"""
pytest 全局配置
"""

import os
import sys
import tempfile

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def _restore_db_module(saved_path):
    """恢复 infrastructure.persistence.legacy_db 内部状态到指定 DB 文件"""
    import sqlite3
    from infrastructure.persistence import legacy_db as dbmod

    try:
        dbmod._db_pool.close_all()
    except Exception:
        pass

    dbmod.DB_FILE = saved_path if saved_path else dbmod.DEFAULT_DB
    dbmod._db_pool = dbmod.DatabasePool(dbmod.DB_FILE, min_size=2, max_size=10)

    os.environ.pop("TICKETS_DB_PATH", None)
    if saved_path:
        os.environ["TICKETS_DB_PATH"] = saved_path


@pytest.fixture
def tmp_db(tmp_path):
    """创建临时 SQLite 数据库并设置环境变量"""
    db_path = str(tmp_path / "test.db")
    os.environ["TICKETS_DB_PATH"] = db_path

    from infrastructure.persistence import legacy_db as dbmod
    dbmod.DB_FILE = db_path
    try:
        dbmod._db_pool.close_all()
    except Exception:
        pass
    dbmod._db_pool = dbmod.DatabasePool(dbmod.DB_FILE, min_size=1, max_size=5)

    try:
        dbmod.init_indexes()
    except Exception:
        pass

    yield db_path

    _restore_db_module(None)


@pytest.fixture
def app(tmp_db):
    """创建 Flask 测试应用"""
    os.environ["BOTO_ACCESS_PASSWORD"] = "test_password"
    os.environ["BOTO_NO_RATE_LIMIT"] = "1"
    from web.app_factory import create_app
    application = create_app(testing=True)
    application.config["TESTING"] = True
    yield application
    os.environ.pop("BOTO_ACCESS_PASSWORD", None)
    os.environ.pop("BOTO_NO_RATE_LIMIT", None)


@pytest.fixture
def client(app):
    """Flask 测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """已认证的测试客户端"""
    import hashlib
    password = "test_password"
    salt = os.environ.get("BOTO_SECRET_KEY", "botong_stable_salt_v1")
    pwd_hash = hashlib.sha256(f"{password}:{salt}:boto_auth_v1".encode()).hexdigest()

    import time
    ts = int(time.time())
    sig = hashlib.sha256(f"{pwd_hash}:{ts}:{salt}".encode()).hexdigest()[:16]
    token = f"{ts}:{sig}"

    client.set_cookie("bt_auth", token)
    return client


def pytest_sessionfinish(session):
    """会话结束时的兜底清理"""
    default_db = os.path.join(BASE_DIR, "tickets.db")
    if os.environ.get("TICKETS_DB_PATH", "").endswith("test_arch.db"):
        _restore_db_module(default_db)
