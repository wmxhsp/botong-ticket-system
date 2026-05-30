"""
博通 — 访问认证中间件
Tailscale 外网密码保护：HMAC 签名 Token + Cookie + Header
支持运行时修改密码、Token 自动续期、plist 同步
暴力破解防护使用 SQLite 存储（并发安全）
"""

import os
import json
import hmac
import hashlib
import time
import logging
import secrets
import platform
import sqlite3
from pathlib import Path

from flask import request, Response, render_template, g

logger = logging.getLogger(__name__)

_AUTH_CONFIG_PATH = None
_PLIST_PATH = None
_ACCESS_COOKIE = "bt_auth"
_COOKIE_SECONDS = 28800
_COOKIE_REFRESH_SECONDS = 7200
_SALT = ""
_CACHED_PWD_HASH = None

_MAX_LOGIN_ATTEMPTS = 5
_LOCKOUT_DURATION = 900
_LOGIN_DB_PATH = None

_BCRYPT_AVAILABLE = False
try:
    import bcrypt as _bcrypt_mod
    _BCRYPT_AVAILABLE = True
except ImportError:
    pass


def init_auth(app, base_dir: str = None):
    global _AUTH_CONFIG_PATH, _PLIST_PATH, _SALT, _LOGIN_DB_PATH

    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))

    _AUTH_CONFIG_PATH = Path(base_dir) / "config" / "auth_config.json"
    _PLIST_PATH = Path(base_dir) / "com.boto.ticket.plist"
    _LOGIN_DB_PATH = Path(base_dir) / "tickets.db"

    _SALT = _generate_secure_salt()

    _init_login_attempts_db()

    _sync_password_on_startup()

    pwd = _load_access_pwd()
    if not pwd:
        raise RuntimeError(
            "❌ 必须设置环境变量 BOTO_ACCESS_PASSWORD，"
            "或在 config/auth_config.json 中设置密码！\n"
            "   示例: export BOTO_ACCESS_PASSWORD='your_strong_password'"
        )

    app.before_request(_check_auth)
    logger.info("✅ 访问认证中间件已初始化（安全盐值 + SQLite 暴力破解防护）")

    return pwd


def _init_login_attempts_db():
    if not _LOGIN_DB_PATH:
        return
    try:
        conn = sqlite3.connect(str(_LOGIN_DB_PATH), timeout=10)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                ip TEXT PRIMARY KEY,
                failed_count INTEGER DEFAULT 0,
                lockout_until INTEGER DEFAULT 0,
                last_attempt INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"初始化登录尝试数据库失败，回退到内存模式: {e}")


def _generate_secure_salt() -> str:
    custom_salt = os.environ.get("BOTO_AUTH_SALT")
    if custom_salt:
        logger.info("使用自定义认证盐值")
        return custom_salt

    secret_key = os.environ.get("BOTO_SECRET_KEY")
    if secret_key:
        machine_fingerprint = f"{platform.node()}:{platform.system()}:{platform.machine()}"
        combined = f"{secret_key}:{machine_fingerprint}:auth_salt_v1"
        return hashlib.sha256(combined.encode()).hexdigest()

    logger.warning(
        "⚠️ 未设置 BOTO_SECRET_KEY 和 BOTO_AUTH_SALT，"
        "使用随机盐值（仅限开发环境）"
    )
    return secrets.token_hex(32)


def _hash_password(password: str) -> str:
    if _BCRYPT_AVAILABLE:
        return "bcrypt:" + _bcrypt_mod.hashpw(
            password.encode(), _bcrypt_mod.gensalt(rounds=12)
        ).decode()
    return "sha256:" + hashlib.sha256(f"{password}:{_SALT}:boto_auth_v1".encode()).hexdigest()


def _verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith("bcrypt:"):
        if not _BCRYPT_AVAILABLE:
            logger.error("密码使用 bcrypt 哈希但 bcrypt 库不可用")
            return False
        try:
            return _bcrypt_mod.checkpw(password.encode(), stored_hash[7:].encode())
        except Exception:
            return False
    actual_hash = stored_hash
    if stored_hash.startswith("sha256:"):
        actual_hash = stored_hash[7:]
    computed = hashlib.sha256(f"{password}:{_SALT}:boto_auth_v1".encode()).hexdigest()
    return hmac.compare_digest(computed, actual_hash)


def _load_access_pwd() -> str:
    global _CACHED_PWD_HASH
    # 返回缓存的哈希值（避免 bcrypt 每次生成不同随机盐）
    if _CACHED_PWD_HASH is not None:
        return _CACHED_PWD_HASH

    result = ""
    env_pwd = os.environ.get("BOTO_ACCESS_PASSWORD")
    if env_pwd:
        result = _hash_password(env_pwd)
    else:
        try:
            if _AUTH_CONFIG_PATH and _AUTH_CONFIG_PATH.exists():
                data = json.loads(_AUTH_CONFIG_PATH.read_text())
                stored = data.get("password_hash") or data.get("password", "")
                if not stored:
                    result = ""
                elif stored.startswith("bcrypt:") or stored.startswith("sha256:"):
                    result = stored
                elif "password_hash" not in data:
                    hashed = _hash_password(stored)
                    _save_access_pwd(hashed)
                    result = hashed
                else:
                    result = "sha256:" + stored
        except Exception:
            pass

    if result:
        _CACHED_PWD_HASH = result
    return result


def _save_access_pwd(new_pwd: str) -> bool:
    global _CACHED_PWD_HASH
    try:
        if not (new_pwd.startswith("bcrypt:") or new_pwd.startswith("sha256:")):
            new_pwd = _hash_password(new_pwd)
        _AUTH_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        algo = "bcrypt" if new_pwd.startswith("bcrypt:") else "sha256+salt"
        _AUTH_CONFIG_PATH.write_text(
            json.dumps({"password_hash": new_pwd, "hash_algo": algo},
                       ensure_ascii=False, indent=2))
        _CACHED_PWD_HASH = new_pwd  # 更新缓存
        logger.info(f"✅ 密码已安全存储（{algo}）")
        return True
    except Exception as e:
        logger.error(f"保存密码失败: {e}")
        return False


def _sync_plist_password(new_pwd: str) -> bool:
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
    ts = int(time.time())
    raw = f"{pwd}:{ts}:{_SALT}"
    sig = hashlib.sha256(raw.encode()).hexdigest()[:32]
    return f"{ts}:{sig}"


def _verify_token(token: str, pwd: str) -> bool:
    try:
        parts = token.split(":", 2)
        if len(parts) != 2:
            return False
        ts_str, sig = parts
        ts = int(ts_str)
        if time.time() - ts > _COOKIE_SECONDS:
            return False
        expected = hashlib.sha256(
            f"{pwd}:{ts}:{_SALT}".encode()).hexdigest()[:32]
        return hmac.compare_digest(sig, expected)
    except (ValueError, IndexError):
        return False


def _check_ip_lockout() -> tuple:
    if not _LOGIN_DB_PATH:
        return False, 0

    client_ip = request.remote_addr
    current_time = int(time.time())

    try:
        conn = sqlite3.connect(str(_LOGIN_DB_PATH), timeout=10)
        row = conn.execute(
            "SELECT failed_count, lockout_until FROM login_attempts WHERE ip = ?",
            (client_ip,)
        ).fetchone()
        conn.close()

        if not row:
            return False, 0

        failed_count, lockout_until = row
        if failed_count >= _MAX_LOGIN_ATTEMPTS:
            if current_time < lockout_until:
                remaining = lockout_until - current_time
                return True, remaining
            else:
                _reset_login_attempts_for_ip(client_ip)
                return False, 0
    except Exception as e:
        logger.warning(f"检查 IP 锁定失败: {e}")

    return False, 0


def _record_failed_login():
    if not _LOGIN_DB_PATH:
        return

    client_ip = request.remote_addr
    current_time = int(time.time())

    try:
        conn = sqlite3.connect(str(_LOGIN_DB_PATH), timeout=10)
        conn.execute("""
            INSERT INTO login_attempts (ip, failed_count, last_attempt)
            VALUES (?, 1, ?)
            ON CONFLICT(ip) DO UPDATE SET
                failed_count = failed_count + 1,
                last_attempt = ?
        """, (client_ip, current_time, current_time))

        row = conn.execute(
            "SELECT failed_count FROM login_attempts WHERE ip = ?",
            (client_ip,)
        ).fetchone()

        if row and row[0] >= _MAX_LOGIN_ATTEMPTS:
            conn.execute(
                "UPDATE login_attempts SET lockout_until = ? WHERE ip = ?",
                (current_time + _LOCKOUT_DURATION, client_ip)
            )
            logger.warning(f"🔒 IP {client_ip} 已锁定，失败次数: {row[0]}")

        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"记录登录失败失败: {e}")


def _reset_login_attempts():
    if not _LOGIN_DB_PATH:
        return

    client_ip = request.remote_addr
    _reset_login_attempts_for_ip(client_ip)


def _reset_login_attempts_for_ip(ip: str):
    if not _LOGIN_DB_PATH:
        return

    try:
        conn = sqlite3.connect(str(_LOGIN_DB_PATH), timeout=10)
        conn.execute("DELETE FROM login_attempts WHERE ip = ?", (ip,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"重置登录尝试失败: {e}")


def _get_remaining_attempts() -> int:
    if not _LOGIN_DB_PATH:
        return _MAX_LOGIN_ATTEMPTS

    client_ip = request.remote_addr
    try:
        conn = sqlite3.connect(str(_LOGIN_DB_PATH), timeout=10)
        row = conn.execute(
            "SELECT failed_count FROM login_attempts WHERE ip = ?",
            (client_ip,)
        ).fetchone()
        conn.close()
        if row:
            return max(0, _MAX_LOGIN_ATTEMPTS - row[0])
    except Exception:
        pass
    return _MAX_LOGIN_ATTEMPTS


def _is_api_request():
    """判断当前请求是否为 API 请求"""
    if request.is_json:
        return True
    accept = request.headers.get("Accept", "")
    if accept.startswith("application/json"):
        return True
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    if request.path.startswith("/api/"):
        return True
    return False


def _unauthorized_response(message="未登录或登录已过期"):
    """返回统一的 401 JSON 响应"""
    from flask import jsonify
    return jsonify({"ok": False, "error": message}), 401


def _check_auth():
    if request.remote_addr in ("127.0.0.1", "::1", "localhost"):
        if os.environ.get("BOTO_SKIP_LOCAL_AUTH", "").lower() in ("1", "true", "yes"):
            return None
        from flask import current_app
        if current_app.config.get("TESTING"):
            return None
    _PUBLIC_PATHS = ("/docs", "/api/version", "/static/",
                     "/api/v1/auth/", "/api/v1/health", "/api/v1/csrf-token",
                     "/api/v1/login", "/api/v1/logout",
                     "/app/", "/app2/", "/login",
                     "/sw.js", "/manifest.json")
    if request.path.startswith(_PUBLIC_PATHS):
        return None

    is_locked, remaining = _check_ip_lockout()
    if is_locked:
        minutes = remaining // 60
        seconds = remaining % 60
        lock_msg = f"登录失败次数过多，账户已锁定，请在 {minutes}分{seconds}秒 后重试"
        if _is_api_request():
            return _unauthorized_response(lock_msg)
        return _login_page(f"❌ {lock_msg}")

    current_pwd = _load_access_pwd()

    cookie_val = request.cookies.get(_ACCESS_COOKIE)
    if cookie_val and _verify_token(cookie_val, current_pwd):
        return _auto_renew_cookie(cookie_val, current_pwd)

    header_val = request.headers.get("X-Access-Token")
    if header_val and _verify_token(header_val, current_pwd):
        return None

    error = None
    if request.method == "POST":
        form_pwd = request.form.get("pwd")
        if form_pwd and _verify_password(form_pwd, current_pwd):
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
        error = "密码错误，请重试"

    remaining_attempts = _get_remaining_attempts()
    if remaining_attempts <= 2:
        error = f"{error}（剩余 {remaining_attempts} 次尝试机会）" if error else f"剩余 {remaining_attempts} 次尝试机会"

    if _is_api_request():
        return _unauthorized_response(error or "未登录或登录已过期")

    return _login_page(f"❌ {error}" if error else error)


def _auto_renew_cookie(cookie_val: str, pwd: str):
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
    return render_template("login.html", error=error), 200


def _make_redirect(req):
    from urllib.parse import urlparse
    from flask import redirect as _rd
    redirect_to = req.args.get("next") or req.form.get("next") or "/"
    parsed = urlparse(redirect_to)
    if parsed.netloc or parsed.scheme:
        redirect_to = "/"
    return _rd(redirect_to)


def get_access_password() -> str:
    return _load_access_pwd()


def save_access_password(new_pwd: str) -> bool:
    result = _save_access_pwd(new_pwd)
    if result:
        _sync_plist_password(new_pwd)
    return result
