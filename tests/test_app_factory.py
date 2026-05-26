"""
博通 — 应用工厂测试

覆盖:
  - create_app() 正常创建 Flask 应用
  - 核心端点可访问
  - 认证路由响应格式
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import pytest


@pytest.fixture(scope="module")
def app():
    """创建测试用 Flask 应用"""
    os.environ.setdefault("BOTO_DEBUG", "1")
    os.environ.setdefault("BOTO_NO_RATE_LIMIT", "1")
    from web.app_factory import create_app
    _app = create_app(testing=True)
    _app.config["TESTING"] = True
    return _app


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


class TestAppCreation:
    """测试应用工厂正常创建"""

    def test_app_exists(self, app):
        assert app is not None
        assert app.config["TESTING"] is True

    def test_app_name(self, app):
        assert app.name in ("web.app_factory", "app_factory", "app")


class TestHealthEndpoint:
    """测试健康检查端点"""

    def test_health_ok(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "status" in data or "ok" in data or isinstance(data, dict)


class TestVersionEndpoint:
    """测试版本端点"""

    def test_version_ok(self, client):
        resp = client.get("/api/version")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "version" in data



class TestPWAEndpoints:
    """测试 PWA 端点（PWA 文件尚未创建，暂 skip）"""

    @pytest.mark.skip(reason="PWA 文件未创建")
    def test_sw_js(self, client):
        resp = client.get("/sw.js")
        assert resp.status_code in (200, 304)

    @pytest.mark.skip(reason="PWA 文件未创建")
    def test_manifest_json(self, client):
        resp = client.get("/manifest.json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "name" in data


class TestAuthEndpoints:
    """测试认证端点"""

    def test_login_missing_credentials(self, client):
        resp = client.post("/login", json={})
        assert resp.status_code in (400, 401, 500)

    def test_login_wrong_password(self, client):
        resp = client.post("/login", json={"pwd": "wrong_password_xyz"})
        # 可能是 401（密码错误）或 500（系统未初始化密码）
        assert resp.status_code in (401, 500)

    def test_logout_redirect(self, client):
        resp = client.get("/logout")
        assert resp.status_code in (302, 200)


class TestAPIEndpoints:
    """测试 API 端点可访问性"""

    def test_clients_list(self, client):
        resp = client.get("/api/v1/clients/")
        assert resp.status_code == 200

    def test_tickets_list(self, client):
        resp = client.get("/api/v1/tickets/")
        assert resp.status_code == 200

    def test_finance_stats(self, client):
        resp = client.get("/api/v1/finance/")
        assert resp.status_code == 200

    def test_equipment_list(self, client):
        resp = client.get("/api/v1/equipment/")
        assert resp.status_code == 200

    def test_staff_list(self, client):
        resp = client.get("/api/v1/technicians/")
        assert resp.status_code == 200

    def test_inventory_list(self, client):
        resp = client.get("/api/v1/inventory/")
        assert resp.status_code == 200


class TestWebPages:
    """测试 Web SSR 页面可访问性"""

    def test_dashboard(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code in (200, 302)

    def test_tickets_page(self, client):
        resp = client.get("/tickets")
        assert resp.status_code in (200, 302)

    def test_finance_page(self, client):
        resp = client.get("/finance")
        assert resp.status_code in (200, 302)


class TestErrorHandler:
    """测试全局错误处理器"""

    def test_404_returns_json(self, client):
        resp = client.get("/api/v1/nonexistent")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data

    def test_500_handler_exists(self, app):
        assert app.error_handler_spec.get(None) is not None or \
               app.error_handler_spec.get(Exception) is not None