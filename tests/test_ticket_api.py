"""
博通 (Botong) — 工单模块单元测试 (参考示例)

本文件作为团队测试标准模板，展示了：
  1. 使用 Flask test_client（不需启动服务器）
  2. pytest fixture 管理依赖
  3. Arrange-Act-Assert 模式
  4. 边界条件测试

运行方式:
  cd /Users/supeng/WorkBuddy/Claw/new-ticket-system
  python3 -m pytest tests/test_ticket_api.py -v

安装依赖:
  pip install pytest
"""

import sys
import os
from pathlib import Path

import pytest

# 将项目根目录加入 sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def app():
    """Flask 应用实例（使用测试客户端，不需启动服务器）"""
    os.environ.setdefault("BOTO_SECRET_KEY", "test-secret-key-for-testing-only")
    os.environ.setdefault("BOTO_DEBUG", "1")
    os.environ.setdefault("BOTO_NO_RATE_LIMIT", "1")
    from web.app_factory import create_app
    flask_app = create_app(testing=True)
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    """测试客户端"""
    return app.test_client()


# ============================================================
# 工单 API 测试
# ============================================================

class TestTicketAPI:
    """工单 API 端点测试"""

    # ── 列表查询 ──

    def test_list_tickets_success(self, client):
        """正常获取工单列表返回 200"""
        resp = client.get("/api/v1/tickets/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None

    # ── 详情查询 ──

    def test_get_ticket_success(self, client):
        """存在的工单返回详情（统一响应格式）"""
        resp = client.get("/api/v1/tickets/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None
        assert isinstance(data, dict)
        # 统一响应格式
        assert data.get("code") == 200
        assert data.get("success") is True
        assert "data" in data
        payload = data["data"]
        # 关键字段必须存在
        for field in ["id", "ticket_no", "client", "status", "created_at"]:
            assert field in payload, f"工单详情缺少字段: {field}"

    def test_get_ticket_not_found(self, client):
        """不存在的工单返回 404"""
        resp = client.get("/api/v1/tickets/99999")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data is not None
        assert "error" in data or (data.get("success") is False and "code" in data)

    def test_get_ticket_invalid_id(self, client):
        """非数字 ID 返回 404"""
        resp = client.get("/api/v1/tickets/abc")
        assert resp.status_code == 404

    # ── 时间线 ──

    def test_ticket_timeline(self, client):
        """工单时间线返回 200"""
        resp = client.get("/api/v1/tickets/1/timeline")
        assert resp.status_code == 200
        data = resp.get_json()
        payload = data.get("data", data) if data else {}
        if payload and "timeline" in payload:
            assert isinstance(payload["timeline"], list)

    def test_ticket_timeline_not_found(self, client):
        """不存在的工单时间线返回 404"""
        resp = client.get("/api/v1/tickets/99999/timeline")
        assert resp.status_code == 404

    # ── 变更 Delta ──

    def test_ticket_delta(self, client):
        """工单变更 Delta 返回 200（统一响应格式）"""
        resp = client.get("/api/v1/tickets/1/delta")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None
        payload = data.get("data", data)
        for field in ["ticket_id", "timeline", "change_count"]:
            assert field in payload, f"Delta 缺少字段: {field}"

    # ── 物料管理 ──

    def test_add_material_success(self, client):
        """添加工单物料（统一响应格式）"""
        resp = client.post("/api/v1/tickets/1/materials", json={
            "name": "测试物料",
            "quantity": 1,
            "unit_price": 50,
        })
        assert resp.status_code in (200, 201)
        data = resp.get_json()
        assert data is not None
        payload = data.get("data", data)
        assert "message" in payload or "summary" in payload or data.get("message")

    def test_add_material_missing_name(self, client):
        """缺少物料名称返回 400"""
        resp = client.post("/api/v1/tickets/1/materials", json={
            "quantity": 1,
            "unit_price": 50,
        })
        assert resp.status_code == 400

    # ── 照片 ──

    def test_ticket_photos(self, client):
        """工单照片列表返回 200"""
        resp = client.get("/api/v1/tickets/1/photos")
        assert resp.status_code == 200

    # ── 编辑 ──

    def test_update_ticket_notes(self, client):
        """更新工单备注"""
        resp = client.put("/api/v1/tickets/1", json={
            "notes": f"测试备注 {os.urandom(4).hex()}"
        })
        assert resp.status_code == 200

    # ── 编辑 - 边界条件 ──

    def test_update_ticket_empty_body(self, client):
        """空请求体返回 400"""
        resp = client.put("/api/v1/tickets/1", json={})
        assert resp.status_code == 400


# ============================================================
# 健康检查
# ============================================================

class TestHealth:
    """系统健康检查"""

    def test_health_endpoint(self, client):
        """健康检查返回 200 + 状态信息"""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None
        assert data.get("status") == "healthy"

    def test_version_endpoint(self, client):
        """版本信息返回 200"""
        resp = client.get("/api/version")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None
        assert "version" in data


# ============================================================
# 跨模块关联测试
# ============================================================

class TestCrossModule:
    """模块间关联调用测试"""

    def test_client_ticket_link(self, client):
        resp = client.get("/api/v1/clients/")
        assert resp.status_code == 200
        data = resp.get_json()
        clients = data.get("data", data).get("clients", data.get("clients", []))
        if clients:
            name = clients[0].get("name", clients[0].get("client", ""))
            if name:
                resp2 = client.get(f"/api/v1/clients/{name}")
                assert resp2.status_code in (200, 404)

    def test_expense_ticket_association(self, client):
        """费用创建可关联工单"""
        resp = client.post("/api/v1/expenses/", json={
            "category": "维修",
            "amount": 100,
            "description": "关联测试",
            "related_ticket_id": 1,
        })
        assert resp.status_code == 201

    def test_expense_update_association(self, client):
        """费用编辑可修改关联"""
        # 先获取最新费用
        resp = client.get("/api/v1/expenses/")
        assert resp.status_code == 200
        items = resp.get_json().get("expenses", [])
        if not items:
            pytest.skip("没有费用记录")
        exp_id = items[0]["id"]

        # 更新关联
        resp2 = client.put(f"/api/v1/expenses/{exp_id}", json={
            "related_ticket_id": 1,
            "description": "已验证关联更新",
        })
        assert resp2.status_code == 200

    def test_stock_adjust(self, client):
        """库存调整"""
        # 先创建商品，通过列表获取 ID
        goods_name = f"测试商品_{os.urandom(2).hex()}"
        goods_resp = client.post("/api/v1/goods/", json={
            "name": goods_name,
            "category": "耗材",
            "unit": "个",
            "cost_price": 10,
            "sell_price": 20,
        })
        if goods_resp.status_code not in (200, 201):
            pytest.skip(f"商品创建失败: {goods_resp.get_json()}")

        # 从商品列表获取刚创建的商品 ID
        list_resp = client.get("/api/v1/goods/")
        goods_list = list_resp.get_json() if list_resp.status_code == 200 else {}
        goods_id = None
        for g in (goods_list.get("goods") or goods_list.get("items") or []):
            if g.get("name") == goods_name:
                goods_id = g["id"]
                break
        if not goods_id:
            pytest.skip("无法获取新创建商品ID")

        resp = client.post("/api/v1/stock/adjust", json={
            "goods_id": goods_id,
            "quantity": 5,
            "notes": "测试入库",
        })
        assert resp.status_code == 200

    def test_warehouse_crud(self, client):
        """仓库新建 + 列表"""
        # 新建
        resp = client.post("/api/v1/stock/warehouses", json={
            "name": f"测试仓_{os.urandom(2).hex()}",
        })
        assert resp.status_code == 201

        # 列表
        resp2 = client.get("/api/v1/stock/warehouses")
        assert resp2.status_code == 200
        data = resp2.get_json()
        assert data is not None
        assert "warehouses" in data
