"""
博通工单系统 — 库存服务单元测试
使用 Mock Repository 测试业务逻辑，不依赖真实数据库
"""

import pytest
from unittest.mock import MagicMock

from application.services.inventory_service import InventoryService
from domain.exceptions import InventoryError, InventoryNotEnoughError


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_goods_service():
    return MagicMock()


@pytest.fixture
def mock_event_bus():
    return MagicMock()


@pytest.fixture
def inventory_service(mock_repo, mock_event_bus, mock_goods_service):
    return InventoryService(
        repo=mock_repo,
        event_bus=mock_event_bus,
        goods_service=mock_goods_service,
    )


class TestRecordSale:

    def test_record_sale_with_valid_data(self, inventory_service, mock_repo):
        mock_repo.get_goods.return_value = {
            "id": 1, "name": "测试商品", "selling_price": 100.0,
            "cost_price": 60.0, "is_subscription": False, "category": "配件",
            "is_bulk": False,
        }
        mock_repo.insert_sale_record.return_value = 42
        mock_repo.insert_sale_income_record.return_value = None
        mock_repo.find_pieces_in_stock.return_value = [{"id": 10}, {"id": 11}]
        mock_repo.mark_items_sold_by_ids.return_value = None
        mock_repo.add_log.return_value = None

        result = inventory_service.record_sale(
            goods_id=1, client="集宁一中", quantity=2,
            payment_method="微信", amount=100.0,
        )

        assert result["sale_id"] == 42
        assert result["client"] == "集宁一中"
        assert result["product_name"] == "测试商品"
        assert result["quantity"] == 2
        assert result["total_amount"] == 200.0
        assert result["payment_method"] == "微信"
        mock_repo.insert_sale_record.assert_called_once()
        mock_repo.insert_sale_income_record.assert_called_once()

    def test_record_sale_with_nonexistent_goods_raises_error(self, inventory_service, mock_repo):
        mock_repo.get_goods.return_value = None

        with pytest.raises(InventoryError, match="商品 #999 不存在"):
            inventory_service.record_sale(goods_id=999, client="测试客户")

    def test_record_sale_with_percent_discount(self, inventory_service, mock_repo):
        mock_repo.get_goods.return_value = {
            "id": 2, "name": "折扣商品", "selling_price": 200.0,
            "cost_price": 100.0, "is_subscription": False, "category": "配件",
            "is_bulk": False,
        }
        mock_repo.insert_sale_record.return_value = 43
        mock_repo.insert_sale_income_record.return_value = None
        mock_repo.find_pieces_in_stock.return_value = [{"id": 20}]
        mock_repo.mark_items_sold_by_ids.return_value = None
        mock_repo.add_log.return_value = None

        result = inventory_service.record_sale(
            goods_id=2, client="测试客户", quantity=1,
            discount_type="percent", discount_value=10,
        )

        assert result["total_amount"] == 180.0
        assert result["discount_type"] == "percent"
        assert result["discount_value"] == 10

    def test_record_sale_with_fixed_discount(self, inventory_service, mock_repo):
        mock_repo.get_goods.return_value = {
            "id": 3, "name": "固定折扣商品", "selling_price": 200.0,
            "cost_price": 100.0, "is_subscription": False, "category": "配件",
            "is_bulk": False,
        }
        mock_repo.insert_sale_record.return_value = 44
        mock_repo.insert_sale_income_record.return_value = None
        mock_repo.find_pieces_in_stock.return_value = [{"id": 30}]
        mock_repo.mark_items_sold_by_ids.return_value = None
        mock_repo.add_log.return_value = None

        result = inventory_service.record_sale(
            goods_id=3, client="测试客户", quantity=1,
            discount_type="fixed", discount_value=50,
        )

        assert result["total_amount"] == 150.0

    def test_record_sale_subscription_goods_auto_validity(self, inventory_service, mock_repo):
        mock_repo.get_goods.return_value = {
            "id": 4, "name": "月卡服务", "selling_price": 300.0,
            "cost_price": 0, "is_subscription": True,
            "billing_cycle": "monthly", "is_bulk": False,
        }
        mock_repo.insert_sale_record.return_value = 45
        mock_repo.insert_sale_income_record.return_value = None
        mock_repo.find_pieces_in_stock.return_value = []
        mock_repo.add_log.return_value = None

        result = inventory_service.record_sale(
            goods_id=4, client="测试客户", quantity=1,
        )

        assert result["sale_id"] == 45
        call_args = mock_repo.insert_sale_record.call_args
        assert call_args[0][11] == 30

    def test_record_sale_bulk_goods(self, inventory_service, mock_repo):
        mock_repo.get_goods.return_value = {
            "id": 5, "name": "散装耗材", "selling_price": 10.0,
            "cost_price": 5.0, "is_subscription": False, "category": "耗材",
            "is_bulk": True, "unit": "kg",
        }
        mock_repo.insert_sale_record.return_value = 46
        mock_repo.insert_sale_income_record.return_value = None
        mock_repo.find_bulk_in_stock.return_value = {
            "id": 50, "batch_no": "BATCH-100-kg",
        }
        mock_repo.parse_bulk_quantity.return_value = 100.0
        mock_repo.update_bulk_item_quantity.return_value = None
        mock_repo.add_log.return_value = None

        result = inventory_service.record_sale(
            goods_id=5, client="测试客户", quantity=30,
        )

        assert result["total_amount"] == 300.0
        mock_repo.update_bulk_item_quantity.assert_called_once()


class TestUseInventoryInsufficientStock:

    def test_use_inventory_insufficient_stock_raises_error(self, inventory_service, mock_repo):
        mock_repo.get_goods.return_value = {
            "id": 1, "name": "测试商品", "unit": "个",
            "is_bulk": False,
        }
        mock_repo.get_piece_stock_count.return_value = 2

        with pytest.raises(InventoryNotEnoughError, match="库存不足"):
            inventory_service.use_inventory(goods_id=1, quantity=5)


class TestRenewSale:

    def test_renew_sale_with_valid_data(self, inventory_service, mock_repo):
        mock_repo.get_sale_record.return_value = {
            "id": 10, "product_id": 1, "client": "集宁一中",
            "unit_price": 100.0, "validity_days": 30,
        }
        mock_repo.get_goods.return_value = {
            "id": 1, "name": "月卡服务", "selling_price": 100.0,
            "cost_price": 0, "is_subscription": True,
            "billing_cycle": "monthly",
        }
        mock_repo.insert_sale_record.return_value = 99
        mock_repo.insert_sale_income_record.return_value = None

        result = inventory_service.renew_sale(sale_id=10)

        assert result["sale_id"] == 99
        assert result["renew_from"] == 10
        assert result["client"] == "集宁一中"
        assert result["product_name"] == "月卡服务"
        assert result["total_amount"] == 100.0
        mock_repo.insert_sale_record.assert_called_once()
        mock_repo.insert_sale_income_record.assert_called_once()

    def test_renew_sale_nonexistent_record_raises_error(self, inventory_service, mock_repo):
        mock_repo.get_sale_record.return_value = None

        with pytest.raises(InventoryError, match="销售记录 #999 不存在"):
            inventory_service.renew_sale(sale_id=999)

    def test_renew_sale_no_product_id_raises_error(self, inventory_service, mock_repo):
        mock_repo.get_sale_record.return_value = {
            "id": 10, "product_id": None, "client": "测试客户",
        }

        with pytest.raises(InventoryError, match="没有关联商品"):
            inventory_service.renew_sale(sale_id=10)

    def test_renew_sale_original_goods_missing_raises_error(self, inventory_service, mock_repo):
        mock_repo.get_sale_record.return_value = {
            "id": 10, "product_id": 1, "client": "测试客户",
            "unit_price": 100.0, "validity_days": 30,
        }
        mock_repo.get_goods.return_value = None

        with pytest.raises(InventoryError, match="原商品已不存在"):
            inventory_service.renew_sale(sale_id=10)

    def test_renew_sale_with_override_params(self, inventory_service, mock_repo):
        mock_repo.get_sale_record.return_value = {
            "id": 10, "product_id": 1, "client": "原客户",
            "unit_price": 100.0, "validity_days": 30,
        }
        mock_repo.get_goods.return_value = {
            "id": 1, "name": "年卡服务", "selling_price": 100.0,
            "cost_price": 0, "is_subscription": True,
            "billing_cycle": "yearly",
        }
        mock_repo.insert_sale_record.return_value = 100
        mock_repo.insert_sale_income_record.return_value = None

        result = inventory_service.renew_sale(
            sale_id=10, client="新客户", quantity=2,
            payment_method="支付宝", amount=200.0,
        )

        assert result["client"] == "新客户"
        assert result["quantity"] == 2
        assert result["total_amount"] == 400.0
        assert result["payment_method"] == "支付宝"
