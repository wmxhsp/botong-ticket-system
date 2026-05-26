"""
博通工单系统 — 采购服务单元测试
使用 Mock Repository 测试业务逻辑，不依赖真实数据库
"""

import pytest
from unittest.mock import MagicMock, call

from application.services.purchase_service import PurchaseService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_inventory_service():
    return MagicMock()


@pytest.fixture
def mock_finance_service():
    return MagicMock()


@pytest.fixture
def purchase_service(mock_repo, mock_inventory_service, mock_finance_service):
    return PurchaseService(
        purchase_repo=mock_repo,
        inventory_service=mock_inventory_service,
        finance_service=mock_finance_service,
    )


class TestCreateOrder:

    def test_create_with_summary_draft_order(self, purchase_service, mock_repo):
        mock_repo.count_purchase_orders.return_value = 5
        mock_repo.create_purchase_order.return_value = {"id": 10}

        result = purchase_service.create_with_summary(
            vendor="测试供应商",
            items=[{"goods_id": 1, "goods_name": "灯泡", "quantity": 10, "unit_cost": 5.0}],
            notes="测试采购",
        )

        assert "草稿" in result["message"]
        assert result["po_no"].startswith("PO-")
        assert result["id"] == 10
        mock_repo.create_purchase_order.assert_called_once()

    def test_create_with_summary_auto_receive(self, purchase_service, mock_repo, mock_inventory_service):
        mock_repo.count_purchase_orders.return_value = 3
        mock_repo.create_and_complete_order.return_value = {"id": 20}
        mock_repo.get_purchase_items.return_value = [
            {"id": 1, "goods_id": 1, "goods_name": "灯泡", "quantity": 3,
             "unit_cost": 5.0, "received_qty": 0},
        ]

        result = purchase_service.create_with_summary(
            vendor="自动入库供应商",
            items=[{"goods_id": 1, "goods_name": "灯泡", "quantity": 3, "unit_cost": 5.0}],
            auto_receive=True,
        )

        assert "入库" in result["message"]
        mock_repo.create_and_complete_order.assert_called_once()
        assert mock_inventory_service.create_inventory_item.call_count == 3
        mock_inventory_service.update_weighted_cost.assert_called_once_with(1)

    def test_create_with_summary_generates_po_no(self, purchase_service, mock_repo):
        mock_repo.count_purchase_orders.return_value = 0
        mock_repo.create_purchase_order.return_value = {"id": 1}

        result = purchase_service.create_with_summary(
            vendor="供应商A",
            items=[{"goods_id": 1, "goods_name": "测试", "quantity": 1, "unit_cost": 10.0}],
        )

        assert "PO-" in result["po_no"]


class TestReceiveAndStock:

    def test_receive_and_stock_partial_receive(self, purchase_service, mock_repo, mock_inventory_service, mock_finance_service):
        mock_repo.get_purchase_item.return_value = {
            "id": 1, "po_id": 10, "goods_id": 5, "goods_name": "灯泡",
            "quantity": 10, "received_qty": 0, "unit_cost": 5.0,
        }
        mock_repo.get_po_no.return_value = "PO-20260524-001"
        mock_repo.get_po_summary.return_value = {"total_recv": 5, "total_qty": 10}

        result = purchase_service.receive_and_stock(item_id=1, receive_qty=5)

        assert "已收货" in result["message"]
        assert "灯泡" in result["message"]
        assert mock_inventory_service.create_inventory_item.call_count == 5
        mock_inventory_service.update_weighted_cost.assert_called_once_with(5)
        mock_repo.update_received_qty.assert_called_once_with(1, 5)
        mock_repo.update_purchase_status.assert_called_once_with(10, "partial")
        mock_finance_service.add_expense.assert_called_once()
        expense_call = mock_finance_service.add_expense.call_args
        assert expense_call[1]["category"] == "采购"
        assert expense_call[1]["amount"] == 25.0

    def test_receive_and_stock_full_receive(self, purchase_service, mock_repo, mock_inventory_service, mock_finance_service):
        mock_repo.get_purchase_item.return_value = {
            "id": 2, "po_id": 20, "goods_id": 8, "goods_name": "墨盒",
            "quantity": 5, "received_qty": 0, "unit_cost": 100.0,
        }
        mock_repo.get_po_no.return_value = "PO-20260524-002"
        mock_repo.get_po_summary.return_value = {"total_recv": 5, "total_qty": 5}

        result = purchase_service.receive_and_stock(item_id=2, receive_qty=5)

        assert "已收货" in result["message"]
        mock_repo.update_purchase_status.assert_called_once_with(20, "completed")
        mock_finance_service.add_expense.assert_called_once()
        expense_call = mock_finance_service.add_expense.call_args
        assert expense_call[1]["amount"] == 500.0

    def test_receive_and_stock_item_not_found(self, purchase_service, mock_repo):
        mock_repo.get_purchase_item.return_value = None

        result = purchase_service.receive_and_stock(item_id=999, receive_qty=1)

        assert result is None

    def test_receive_and_stock_caps_at_remaining(self, purchase_service, mock_repo, mock_inventory_service, mock_finance_service):
        mock_repo.get_purchase_item.return_value = {
            "id": 3, "po_id": 30, "goods_id": 9, "goods_name": "色带",
            "quantity": 5, "received_qty": 3, "unit_cost": 20.0,
        }
        mock_repo.get_po_no.return_value = "PO-20260524-003"
        mock_repo.get_po_summary.return_value = {"total_recv": 5, "total_qty": 5}

        result = purchase_service.receive_and_stock(item_id=3, receive_qty=10)

        assert mock_inventory_service.create_inventory_item.call_count == 2
        mock_repo.update_received_qty.assert_called_once_with(3, 5)


class TestCompletePurchaseOrder:

    def test_complete_purchase_order(self, purchase_service, mock_repo, mock_inventory_service, mock_finance_service):
        mock_repo.get_purchase_items.return_value = [
            {"id": 1, "goods_id": 1, "goods_name": "灯泡", "quantity": 3,
             "unit_cost": 5.0, "received_qty": 0},
        ]
        mock_repo.get_po_no.return_value = "PO-20260524-010"

        purchase_service.complete_purchase_order(po_id=10)

        mock_repo.update_purchase_status.assert_called_once_with(10, "completed")
        assert mock_inventory_service.create_inventory_item.call_count == 3
        mock_inventory_service.update_weighted_cost.assert_called_once_with(1)
        mock_finance_service.add_expense.assert_called_once()


class TestProcessPayment:

    def test_process_payment_full(self, purchase_service, mock_repo):
        mock_repo.get_purchase_order.return_value = {
            "po_no": "PO-001", "total_amount": 1000, "payment_status": "unpaid",
        }
        mock_repo.confirm_payment.return_value = None

        result = purchase_service.process_payment(po_id=1, amount=1000)

        assert result["payment_status"] == "paid"
        assert result["amount_paid"] == 1000
        mock_repo.confirm_payment.assert_called_once()

    def test_process_payment_already_paid(self, purchase_service, mock_repo):
        mock_repo.get_purchase_order.return_value = {
            "po_no": "PO-002", "total_amount": 1000, "payment_status": "paid",
        }

        result = purchase_service.process_payment(po_id=2, amount=500)

        assert "error" in result

    def test_process_payment_order_not_found(self, purchase_service, mock_repo):
        mock_repo.get_purchase_order.return_value = None

        result = purchase_service.process_payment(po_id=999, amount=100)

        assert result is None
