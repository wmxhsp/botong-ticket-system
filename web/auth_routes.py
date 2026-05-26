"""
博通 (Botong) — 认证路由模块

提供:
  - POST /login          — 密码登录
  - GET  /logout         — 退出登录
  - POST /api/v1/auth/change-password — 修改密码
"""

import os
import json
import hashlib
import hmac
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def register_auth_routes(app):
    from flask import jsonify, request, make_response, redirect as _rd

    @app.route("/login", methods=["POST"])
    def _login_spa():
        from web.middleware.auth import _load_access_pwd, _sign_token, _ACCESS_COOKIE

        current_pwd = _load_access_pwd()
        if not current_pwd:
            return jsonify({"error": "系统未初始化密码"}), 500

        data = request.get_json(silent=True) or {}
        input_pwd = data.get("pwd", "")
        input_hash = hashlib.sha256(f"{input_pwd}:{os.environ.get('BOTO_SECRET_KEY', 'botong_stable_salt_v1')}:boto_auth_v1".encode()).hexdigest()

        if hmac.compare_digest(input_hash, current_pwd):
            token = _sign_token(current_pwd)
            resp = make_response(jsonify({"ok": True, "redirect": "/app/"}))
            secure = request.is_secure or request.headers.get("X-Forwarded-Proto") == "https"
            resp.set_cookie(_ACCESS_COOKIE, token,
                            max_age=28800, httponly=True,
                            samesite="Lax", secure=secure)
            return resp
        return jsonify({"error": "密码错误"}), 401

    @app.route("/logout")
    def _logout():
        resp = _rd("/")
        secure = request.is_secure or request.headers.get("X-Forwarded-Proto") == "https"
        resp.set_cookie("bt_auth", "", max_age=0, httponly=True,
                        samesite="Lax", secure=secure)
        logger.info("用户已退出登录")
        return resp

    @app.route("/api/v1/auth/change-password", methods=["POST"])
    def _change_password():
        from web.middleware.auth import get_access_password, save_access_password

        current_pwd = get_access_password()
        data = request.get_json(force=True, silent=True) or {}
        old_pwd = data.get("old_password", "")
        new_pwd = data.get("new_password", "")

        if not hmac.compare_digest(old_pwd, current_pwd):
            return jsonify({"error": "当前密码错误"}), 403
        if len(new_pwd) < 6:
            return jsonify({"error": "新密码至少6位"}), 400
        if hmac.compare_digest(new_pwd, current_pwd):
            return jsonify({"error": "新密码不能与旧密码相同"}), 400
        if not save_access_password(new_pwd):
            return jsonify({"error": "密码保存失败"}), 500

        logger.info("访问密码已更新")
        return jsonify({"message": "密码已更新，请使用新密码重新登录", "need_relogin": True})