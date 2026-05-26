"""
博通 — 请求校验层单元测试

覆盖:
  - 14 个 Pydantic Schema 的正向/反向校验
  - @validate_json / @validate_query 装饰器
"""

import os
import sys
import json
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from pydantic import ValidationError
from api.validators.schemas import (
    TicketCreateSchema, TicketUpdateSchema,
    ClientCreateSchema, ClientUpdateSchema,
    IncomeRecordSchema, ExpenseRecordSchema,
    InventoryAdjustSchema, InventoryCreateSchema,
    EquipmentCreateSchema,
    PaginationQuery, DateRangeQuery, TicketListQuery,
)


class TestClientSchemas:
    """客户 Schema 校验"""

    def test_create_valid(self):
        body = ClientCreateSchema(name="测试客户", phone="13800138000")
        assert body.name == "测试客户"
        assert body.phone == "13800138000"

    def test_create_missing_name(self):
        with pytest.raises(ValidationError) as exc:
            ClientCreateSchema(name="")
        assert "name" in str(exc.value)

    def test_create_empty_body(self):
        with pytest.raises(ValidationError) as exc:
            ClientCreateSchema()
        assert "name" in str(exc.value)

    def test_update_minimal(self):
        body = ClientUpdateSchema(phone="13900139000")
        data = body.model_dump(exclude_none=True)
        assert "phone" in data
        assert "name" not in data
        assert data["phone"] == "13900139000"

    def test_update_empty(self):
        body = ClientUpdateSchema()
        data = body.model_dump(exclude_none=True)
        assert data == {}


class TestTicketSchemas:
    """工单 Schema 校验"""

    def test_create_minimal(self):
        body = TicketCreateSchema(client="测试公司", content="屏幕维修")
        assert body.client == "测试公司"
        assert body.content == "屏幕维修"
        assert body.status == "open"
        assert body.amount == 0

    def test_create_invalid_status(self):
        with pytest.raises(ValidationError) as exc:
            TicketCreateSchema(client="A", content="B", status="invalid")
        assert "无效状态" in str(exc.value)

    def test_create_negative_amount(self):
        with pytest.raises(ValidationError) as exc:
            TicketCreateSchema(client="A", content="B", amount=-100)
        assert "amount" in str(exc.value)

    def test_create_negative_tax_rate(self):
        with pytest.raises(ValidationError) as exc:
            TicketCreateSchema(client="A", content="B", tax_rate=-1)
        assert "tax_rate" in str(exc.value)

    def test_create_tax_rate_over_100(self):
        with pytest.raises(ValidationError) as exc:
            TicketCreateSchema(client="A", content="B", tax_rate=101)
        assert "tax_rate" in str(exc.value)

    def test_update_partial(self):
        body = TicketUpdateSchema(status="closed")
        data = body.model_dump(exclude_none=True)
        assert data == {"status": "closed"}

    def test_update_invalid_status(self):
        with pytest.raises(ValidationError) as exc:
            TicketUpdateSchema(status="deleted")
        assert "无效状态" in str(exc.value)


class TestFinanceSchemas:
    """财务 Schema 校验"""

    def test_income_valid(self):
        body = IncomeRecordSchema(amount=100.5, payment_method="微信")
        assert body.amount == 100.5
        assert body.payment_method == "微信"

    def test_income_amount_zero(self):
        with pytest.raises(ValidationError) as exc:
            IncomeRecordSchema(amount=0)
        assert "amount" in str(exc.value)

    def test_income_amount_negative(self):
        with pytest.raises(ValidationError) as exc:
            IncomeRecordSchema(amount=-10)
        assert "amount" in str(exc.value)

    def test_expense_valid(self):
        body = ExpenseRecordSchema(amount=50, category="维修耗材")
        assert body.amount == 50
        assert body.category == "维修耗材"

    def test_expense_amount_zero(self):
        with pytest.raises(ValidationError) as exc:
            ExpenseRecordSchema(amount=0)
        assert "amount" in str(exc.value)


class TestInventorySchemas:
    """库存 Schema 校验"""

    def test_adjust_in(self):
        body = InventoryAdjustSchema(change_quantity=10, type="in", goods_id=1)
        assert body.change_quantity == 10
        assert body.type == "in"

    def test_adjust_out(self):
        body = InventoryAdjustSchema(change_quantity=-5, type="out", goods_id=2)
        assert body.change_quantity == -5

    def test_create_inventory(self):
        body = InventoryCreateSchema(quantity=100, min_stock=10)
        assert body.quantity == 100
        assert body.min_stock == 10
        assert body.unit == "个"

    def test_create_inventory_negative_quantity(self):
        with pytest.raises(ValidationError) as exc:
            InventoryCreateSchema(quantity=-1)
        assert "quantity" in str(exc.value)


class TestEquipmentSchemas:
    """设备 Schema 校验"""

    def test_create_valid(self):
        body = EquipmentCreateSchema(name="联想笔记本", client="张三")
        assert body.name == "联想笔记本"
        assert body.client == "张三"

    def test_create_missing_client(self):
        with pytest.raises(ValidationError) as exc:
            EquipmentCreateSchema(name="设备A")
        assert "client" in str(exc.value)


class TestQuerySchemas:
    """查询 Schema 校验"""

    def test_pagination_defaults(self):
        body = PaginationQuery()
        assert body.page == 1
        assert body.per_page == 30

    def test_pagination_custom(self):
        body = PaginationQuery(page=3, per_page=50)
        assert body.page == 3
        assert body.per_page == 50

    def test_pagination_page_zero(self):
        with pytest.raises(ValidationError):
            PaginationQuery(page=0)

    def test_pagination_per_page_over_limit(self):
        with pytest.raises(ValidationError):
            PaginationQuery(per_page=500)

    def test_date_range(self):
        body = DateRangeQuery(date_from="2026-01-01", date_to="2026-05-31")
        assert body.date_from == "2026-01-01"

    def test_ticket_list_query(self):
        body = TicketListQuery(status="open", client="张三", page=1)
        assert body.status == "open"
        assert body.client == "张三"
        assert body.page == 1


class TestValidatorDecorators:
    """装饰器集成测试"""

    def test_validate_json_valid(self):
        from api.validators import validate_json
        from flask import Flask, json

        app = Flask(__name__)

        @app.route("/test", methods=["POST"])
        @validate_json(ClientCreateSchema)
        def handler(body: ClientCreateSchema):
            return {"name": body.name, "phone": body.phone}, 201

        with app.test_client() as client:
            resp = client.post("/test", json={"name": "测试", "phone": "138"})
            assert resp.status_code == 201
            data = json.loads(resp.data)
            assert data["name"] == "测试"

    def test_validate_json_invalid(self):
        from api.validators import validate_json
        from flask import Flask, json

        app = Flask(__name__)

        @app.route("/test", methods=["POST"])
        @validate_json(ClientCreateSchema)
        def handler(body: ClientCreateSchema):
            return {"ok": True}

        with app.test_client() as client:
            resp = client.post("/test", json={})
            assert resp.status_code == 400
            data = json.loads(resp.data)
            assert "details" in data
            assert "name" in data["details"]

    def test_validate_query_valid(self):
        from api.validators import validate_query
        from flask import Flask, json

        app = Flask(__name__)

        @app.route("/test")
        @validate_query(PaginationQuery)
        def handler(query: PaginationQuery):
            return {"page": query.page, "per_page": query.per_page}

        with app.test_client() as client:
            resp = client.get("/test?page=2&per_page=10")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert data["page"] == 2
            assert data["per_page"] == 10

    def test_validate_query_defaults(self):
        from api.validators import validate_query
        from flask import Flask, json

        app = Flask(__name__)

        @app.route("/test")
        @validate_query(PaginationQuery)
        def handler(query: PaginationQuery):
            return {"page": query.page}

        with app.test_client() as client:
            resp = client.get("/test")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert data["page"] == 1

    def test_validate_query_invalid(self):
        from api.validators import validate_query
        from flask import Flask, json

        app = Flask(__name__)

        @app.route("/test")
        @validate_query(PaginationQuery)
        def handler(query: PaginationQuery):
            return {"page": query.page}

        with app.test_client() as client:
            resp = client.get("/test?page=0")
            assert resp.status_code == 400
            data = json.loads(resp.data)
            assert "details" in data