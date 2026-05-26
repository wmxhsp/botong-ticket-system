"""
博通 — 访问认证中间件
Tailscale 外网密码保护：HMAC 签名 Token + Cookie + Header
支持运行时修改密码、Token 自动续期、plist 同步
"""

import os
import json
import hmac
import hashlib
import time
import logging
import secrets
import platform
from pathlib import Path

from flask import request, Response, render_template

logger = logging.getLogger(__name__)

# ── 配置 ──
_AUTH_CONFIG_PATH = None
_PLIST_PATH = None
_ACCESS_COOKIE = "bt_auth"
_COOKIE_SECONDS = 28800  # 8 小时
_COOKIE_REFRESH_SECONDS = 7200  # 剩余不足 2 小时自动续期
_SALT = ""

# ── 暴力破解防护配置 ──
_MAX_LOGIN_ATTEMPTS = 5  # 最大失败次数
_LOCKOUT_DURATION = 900  # 锁定时间（15分钟）
_LOGIN_ATTEMPTS_FILE = None


def init_auth(app, base_dir: str = None):
    """
    初始化认证系统

    在 app.before_request 中注册认证检查。
    必须在 app.secret_key 设置后调用。
    """
    global _AUTH_CONFIG_PATH, _PLIST_PATH, _SALT, _LOGIN_ATTEMPTS_FILE

    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))

    _AUTH_CONFIG_PATH = Path(base_dir) / "config" / "auth_config.json"
    _PLIST_PATH = Path(base_dir) / "com.boto.ticket.plist"
    _LOGIN_ATTEMPTS_FILE = Path(base_dir) / "config" / "login_attempts.json"
    _LOGIN_ATTEMPTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 使用安全的动态盐值生成
    _SALT = _generate_secure_salt()

    # 启动时同步密码
    _sync_password_on_startup()

    # 检查密码是否存在
    pwd = _load_access_pwd()
    if not pwd:
        raise RuntimeError(
            "❌ 必须设置环境变量 BOTO_ACCESS_PASSWORD，"
            "或在 config/auth_config.json 中设置密码！\n"
            "   示例: export BOTO_ACCESS_PASSWORD='your_strong_password'"
        )

    # 注册 before_request 钩子
    app.before_request(_check_auth)
    logger.info("✅ 访问认证中间件已初始化（安全盐值 + 暴力破解防护）")

    return pwd


def _generate_secure_salt() -> str:
    """
    生成安全的动态盐值

    优先使用以下策略：
    1. 环境变量 BOTO_AUTH_SALT（用户指定盐值）
    2. BOTO_SECRET_KEY + 机器指纹（确保不同机器/部署环境使用不同盐值）
    3. secrets.token_hex() 每次启动生成（仅用于开发和测试）
    """
    # 策略1：用户指定盐值
    custom_salt = os.environ.get("BOTO_AUTH_SALT")
    if custom_salt:
        logger.info("使用自定义认证盐值")
        return custom_salt

    # 策略2：基于 secret_key + 机器指纹
    secret_key = os.environ.get("BOTO_SECRET_KEY")
    if secret_key:
        machine_fingerprint = f"{platform.node()}:{platform.system()}:{platform.machine()}"
        combined = f"{secret_key}:{machine_fingerprint}:auth_salt_v1"
        return hashlib.sha256(combined.encode()).hexdigest()

    # 策略3：开发模式使用随机盐值（但给出警告）
    logger.warning(
        "⚠️ 未设置 BOTO_SECRET_KEY 和 BOTO_AUTH_SALT，"
        "使用随机盐值（仅限开发环境）"
    )
    return secrets.token_hex(32)


def _hash_password(password: str) -> str:
    """对密码进行单向哈希（SHA-256 + salt），不可逆"""
    return hashlib.sha256(f"{password}:{_SALT}:boto_auth_v1".encode()).hexdigest()


def _load_access_pwd() -> str:
    """从配置文件读取访问密码（返回哈希值）"""
    try:
        if _AUTH_CONFIG_PATH and _AUTH_CONFIG_PATH.exists():
            data = json.loads(_AUTH_CONFIG_PATH.read_text())
            stored = data.get("password_hash") or data.get("password", "")
            # 兼容旧明文 → 自动迁移为哈希
            if stored and "password_hash" not in data:
                hashed = _hash_password(stored)
                _save_access_pwd(hashed)
                return hashed
            return stored
    except Exception:
        pass
    return ""


def _save_access_pwd(new_pwd: str) -> bool:
    """保存密码（自动哈希化）到配置文件"""
    try:
        hashed = _hash_password(new_pwd) if not new_pwd.startswith("hash:") else new_pwd.replace("hash:", "", 1)
        _AUTH_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _AUTH_CONFIG_PATH.write_text(
            json.dumps({"password_hash": hashed, "hash_algo": "sha256+salt"},
                       ensure_ascii=False, indent=2))
        logger.info("✅ 密码已安全存储（SHA-256 哈希）")
        return True
    except Exception as e:
        logger.error(f"保存密码失败: {e}")
        return False


def _sync_plist_password(new_pwd: str) -> bool:
    """同步密码到 plist 文件"""
    try:
        import plistlib
        if not _PLIST_PATH or not _PLIST_PATH.exists():
            logger.warning("plist 文件不存在，跳过同步")
            return False
        with open(_PLIST_PATH, "rb") as f:
            plist = plistlib.load(f)
        env_dict = plist.get("EnvironmentVariables", {})
        if not env_dict:
            logger.warning("plist 中没有 EnvironmentVariables 字段")
            return False
        env_dict["BOTO_ACCESS_PASSWORD"] = new_pwd
        plist["EnvironmentVariables"] = env_dict
        with open(_PLIST_PATH, "wb") as f:
            plistlib.dump(plist, f)
        logger.info("✅ plist 密码已同步")
        return True
    except Exception as e:
        logger.error(f"同步 plist 失败: {e}")
        return False


def _sync_password_on_startup():
    """启动时密码同步"""
    env_pwd = os.environ.get("BOTO_ACCESS_PASSWORD")
    existing = _load_access_pwd()

    if env_pwd and not existing:
        _save_access_pwd(env_pwd)
        _sync_plist_password(env_pwd)
        logger.info("✅ 环境变量密码已写入 config（首次启动）")
    elif env_pwd and existing:
        _sync_plist_password(existing)
        logger.info("✅ 使用 config 密码，已同步 plist")


def _sign_token(pwd: str) -> str:
    """生成签名 Token"""
    ts = int(time.time())
    raw = f"{pwd}:{ts}:{_SALT}"
    sig = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{ts}:{sig}"


def _verify_token(token: str, pwd: str) -> bool:
    """验证签名 Token"""
    try:
        parts = token.split(":", 2)
        if len(parts) != 2:
            return False
        ts_str, sig = parts
        ts = int(ts_str)
        if time.time() - ts > _COOKIE_SECONDS:
            return False
        expected = hashlib.sha256(
            f"{pwd}:{ts}:{_SALT}".encode()).hexdigest()[:16]
        return hmac.compare_digest(sig, expected)
    except (ValueError, IndexError):
        return False


def _get_login_attempts() -> dict:
    """获取登录尝试记录"""
    try:
        if _LOGIN_ATTEMPTS_FILE and _LOGIN_ATTEMPTS_FILE.exists():
            return json.loads(_LOGIN_ATTEMPTS_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_login_attempts(attempts: dict) -> bool:
    """保存登录尝试记录"""
    try:
        if _LOGIN_ATTEMPTS_FILE:
            _LOGIN_ATTEMPTS_FILE.write_text(
                json.dumps(attempts, ensure_ascii=False, indent=2))
        return True
    except Exception:
        return False


def _check_ip_lockout() -> tuple[bool, int]:
    """
    检查 IP 是否被锁定

    Returns:
        tuple[is_locked, remaining_seconds]: 是否被锁定，剩余锁定时间（秒）
    """
    if not _LOGIN_ATTEMPTS_FILE:
        return False, 0

    client_ip = request.remote_addr
    current_time = int(time.time())
    attempts = _get_login_attempts()

    if client_ip not in attempts:
        return False, 0

    record = attempts[client_ip]
    failed_count = record.get("failed_count", 0)

    if failed_count >= _MAX_LOGIN_ATTEMPTS:
        lockout_time = record.get("lockout_until", 0)
        if current_time < lockout_time:
            remaining = lockout_time - current_time
            return True, remaining
        else:
            attempts[client_ip] = {"failed_count": 0, "lockout_until": 0}
            _save_login_attempts(attempts)
            return False, 0

    return False, 0


def _record_failed_login():
    """记录失败的登录尝试"""
    if not _LOGIN_ATTEMPTS_FILE:
        return

    client_ip = request.remote_addr
    current_time = int(time.time())
    attempts = _get_login_attempts()

    if client_ip not in attempts:
        attempts[client_ip] = {"failed_count": 0, "lockout_until": 0, "history": []}

    record = attempts[client_ip]
    record["failed_count"] = record.get("failed_count", 0) + 1
    record["last_attempt"] = current_time

    if record["failed_count"] >= _MAX_LOGIN_ATTEMPTS:
        record["lockout_until"] = current_time + _LOCKOUT_DURATION
        logger.warning(f"🔒 IP {client_ip} 已锁定，失败次数: {record['failed_count']}")

    _save_login_attempts(attempts)


def _reset_login_attempts():
    """重置登录尝试记录（登录成功时调用）"""
    if not _LOGIN_ATTEMPTS_FILE:
        return

    client_ip = request.remote_addr
    attempts = _get_login_attempts()

    if client_ip in attempts:
        del attempts[client_ip]
        _save_login_attempts(attempts)


def _check_auth():
    """认证检查（注册为 before_request 钩子）"""
    # 本地访问不限制
    if request.remote_addr in ("127.0.0.1", "::1", "localhost"):
        return None
    _PUBLIC_PATHS = ("/docs", "/api/version", "/static/",
                     "/api/v1/auth/", "/api/v1/health",
                     "/app/", "/app2/",
                     "/sw.js", "/manifest.json")
    if request.path.startswith(_PUBLIC_PATHS):
        return None

    # 检查 IP 锁定状态
    is_locked, remaining = _check_ip_lockout()
    if is_locked:
        minutes = remaining // 60
        seconds = remaining % 60
        lock_msg = f"❌ 登录失败次数过多，账户已锁定，请在 {minutes}分{seconds}秒 后重试"
        return _login_page(lock_msg)

    current_pwd = _load_access_pwd()

    # Cookie 验证
    cookie_val = request.cookies.get(_ACCESS_COOKIE)
    if cookie_val and _verify_token(cookie_val, current_pwd):
        return _auto_renew_cookie(cookie_val, current_pwd)

    # Header 验证
    header_val = request.headers.get("X-Access-Token")
    if header_val and _verify_token(header_val, current_pwd):
        return None

    # 表单密码提交
    error = None
    if request.method == "POST":
        form_pwd = request.form.get("pwd")
        form_hash = _hash_password(form_pwd) if form_pwd else ""
        if form_pwd and hmac.compare_digest(form_hash, current_pwd):
            _reset_login_attempts()
            resp = _make_redirect(request)
            secure = (request.is_secure
                      or request.headers.get("X-Forwarded-Proto") == "https")
            resp.set_cookie(
                _ACCESS_COOKIE, _sign_token(current_pwd),
                max_age=_COOKIE_SECONDS, httponly=True,
                samesite="Lax", secure=secure)
            return resp
        _record_failed_login()
        error = "❌ 密码错误，请重试"

    # 获取剩余尝试次数
    attempts = _get_login_attempts()
    client_ip = request.remote_addr
    remaining_attempts = _MAX_LOGIN_ATTEMPTS - attempts.get(client_ip, {}).get("failed_count", 0)

    if remaining_attempts <= 2:
        error = f"{error}（剩余 {remaining_attempts} 次尝试机会）"

    return _login_page(error)


def _auto_renew_cookie(cookie_val: str, pwd: str):
    """Token 自动续期（剩余不足 2 小时时刷新）"""
    try:
        ts_part = cookie_val.split(":")[0]
        elapsed = time.time() - int(ts_part)
        if elapsed > (_COOKIE_SECONDS - _COOKIE_REFRESH_SECONDS):
            resp = Response()
            secure = (request.is_secure
                      or request.headers.get("X-Forwarded-Proto") == "https")
            resp.set_cookie(
                _ACCESS_COOKIE, _sign_token(pwd),
                max_age=_COOKIE_SECONDS, httponly=True,
                samesite="Lax", secure=secure)
            return resp
    except Exception:
        pass
    return None


def _login_page(error=None):
    """登录页面（使用现代化模板）"""
    return render_template("login.html", error=error), 200


def _make_redirect(req):
    """安全重定向"""
    from urllib.parse import urlparse
    from flask import redirect as _rd
    redirect_to = req.args.get("next") or req.form.get("next") or "/"
    parsed = urlparse(redirect_to)
    if parsed.netloc or parsed.scheme:
        redirect_to = "/"
    return _rd(redirect_to)


def get_access_password() -> str:
    """获取当前密码（供修改密码 API 使用）"""
    return _load_access_pwd()


def save_access_password(new_pwd: str) -> bool:
    """保存新密码（供修改密码 API 使用）"""
    result = _save_access_pwd(new_pwd)
    if result:
        _sync_plist_password(new_pwd)
    return result
