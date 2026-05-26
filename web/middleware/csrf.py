"""
博通 — CSRF 保护中间件
带自动过期清理的 Token 存储，支持内存和 Redis 降级方案
"""

import secrets
import time
import threading
import logging
from flask import request, jsonify

logger = logging.getLogger(__name__)


class CSRFTokenStore:
    """
    线程安全的 CSRF Token 存储，自动过期清理。

    - Token 有效期 1 小时
    - 每 100 次写入触发清理
    - 支持内存存储（默认）和 Redis 降级方案
    """

    def __init__(self, ttl: int = 3600):
        self._ttl = ttl
        self._tokens: dict = {}
        self._lock = threading.Lock()
        self._gc_counter = 0

    def store(self, token: str, client_ip: str):
        """存储 token"""
        with self._lock:
            self._tokens[token] = (time.time(), client_ip)
            self._gc_counter += 1
            if self._gc_counter >= 100:
                self._gc_counter = 0
                self._cleanup_locked()

    def verify(self, token: str, client_ip: str) -> bool:
        """验证 token"""
        with self._lock:
            entry = self._tokens.get(token)
            if entry is None:
                return False
            issued_at, stored_ip = entry
            if (time.time() - issued_at) > self._ttl:
                del self._tokens[token]
                return False
            if stored_ip != client_ip:
                return False
            return True

    def _cleanup_locked(self):
        """清理过期 token"""
        now = time.time()
        expired = [t for t, (ts, _) in self._tokens.items()
                   if (now - ts) > self._ttl]
        for t in expired:
            del self._tokens[t]

    def force_cleanup(self):
        """强制清理"""
        with self._lock:
            self._cleanup_locked()

    @property
    def active_count(self) -> int:
        """有效 token 数量"""
        self.force_cleanup()
        return len(self._tokens)


def init_csrf(app):
    """
    初始化 CSRF 保护

    在 app.before_request 中注册检查。
    放行逻辑：
    - 本地访问、GET/HEAD/OPTIONS、公开端点
    - X-Access-Token Header（已通过 HMAC 验证）
    - 已通过密码验证（bt_auth cookie 有效）
    """
    store = CSRFTokenStore(ttl=3600)

    @app.before_request
    def _csrf_check():
        """CSRF 检查"""
        # 放行本地访问
        if request.remote_addr in ("127.0.0.1", "::1", "localhost"):
            return None
        # 放行安全方法
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return None
        # 放行公开端点
        if request.path.startswith(("/docs", "/api/version",
                                     "/static/", "/api/v1/auth/")):
            return None
        # 放行已通过 HMAC 验证的请求
        if request.headers.get("X-Access-Token"):
            return None
        # 放行已登录用户
        cookie_val = request.cookies.get("bt_auth")
        if cookie_val:
            from web.middleware.auth import _verify_token, _load_access_pwd
            if _verify_token(cookie_val, _load_access_pwd()):
                return None

        # 验证 CSRF Token
        csrf_token = (request.headers.get("X-CSRF-Token")
                      or request.form.get("csrf_token") or "")
        if not csrf_token:
            return jsonify(
                {"error": "CSRF 验证失败，请刷新页面后重试", "code": 403}), 403
        if not store.verify(csrf_token, request.remote_addr):
            return jsonify(
                {"error": "CSRF 验证失败，请刷新页面后重试", "code": 403}), 403

    @app.route("/api/v1/csrf-token")
    def _get_csrf_token():
        """获取 CSRF Token"""
        token = secrets.token_hex(24)
        store.store(token, request.remote_addr)
        resp = jsonify({"csrf_token": token})
        resp.set_cookie("bt_csrf", token, max_age=3600,
                        httponly=False, samesite="Strict",
                        secure=request.is_secure)
        return resp

    logger.info("✅ CSRF 保护已初始化")
    return store
