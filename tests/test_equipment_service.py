"""
博通工单系统 — 设备服务单元测试
使用 Mock Repository 测试业务逻辑，不依赖真实数据库
"""

import pytest
from unittest.mock import MagicMock

from application.services.equipment_service import EquipmentService
from domain.exceptions import EquipmentError


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_event_bus():
    return MagicMock()


@pytest.fixture
def equipment_service(mock_repo, mock_event_bus):
    return EquipmentService(repo=mock_repo, event_bus=mock_event_bus)


class TestCreateEquipment:

    def test_create_equipment_with_valid_data(self, equipment_service, mock_repo):
        mock_repo.save.return_value = None
        data = {"name": "投影仪", "client": "集宁一中", "model": "EPSON-X01"}

        result = equipment_service.create_equipment(data)

        assert "message" in result
        assert "投影仪" in result["message"]
        mock_repo.save.assert_called_once_with(data)

    def test_create_equipment_calls_repo_save(self, equipment_service, mock_repo):
        mock_repo.save.return_value = None
        data = {"name": "打印机", "client": "测试学校"}

        equipment_service.create_equipment(data)

        mock_repo.save.assert_called_once_with(data)


class TestUpdateEquipment:

    def test_update_equipment_with_valid_data(self, equipment_service, mock_repo):
        mock_repo.find_old_status.return_value = None
        mock_repo.update.return_value = None

        result = equipment_service.update_equipment(
            equip_id=1, model="EPSON-X02", location="教学楼",
        )

        assert "message" in result
        assert "已更新" in result["message"]
        mock_repo.update.assert_called_once_with(1, {"model": "EPSON-X02", "location": "教学楼"})

    def test_update_equipment_status_change_logs_audit(self, equipment_service, mock_repo):
        mock_repo.find_old_status.return_value = {
            "status": "正常", "name": "投影仪",
        }
        mock_repo.update.return_value = None
        mock_repo.log_audit.return_value = None

        result = equipment_service.update_equipment(equip_id=1, status="维修中")

        assert "已更新" in result["message"]
        mock_repo.log_audit.assert_called_once()
        call_args = mock_repo.log_audit.call_args
        assert call_args[0][0] == "equipment_status_change"
        assert call_args[0][1] == 1

    def test_update_equipment_same_status_no_audit(self, equipment_service, mock_repo):
        mock_repo.find_old_status.return_value = {
            "status": "正常", "name": "投影仪",
        }
        mock_repo.update.return_value = None

        equipment_service.update_equipment(equip_id=1, status="正常")

        mock_repo.log_audit.assert_not_called()


class TestDeleteEquipment:

    def test_delete_equipment_soft_delete(self, equipment_service, mock_repo):
        mock_repo.find_for_delete.return_value = {
            "name": "投影仪", "client": "集宁一中",
        }
        mock_repo.soft_delete.return_value = None
        mock_repo.log_audit.return_value = None

        result = equipment_service.delete_equipment(equip_id=1)

        assert "已删除" in result["message"]
        assert "可恢复" in result["message"]
        assert "投影仪" in result["message"]
        mock_repo.soft_delete.assert_called_once_with(1)
        mock_repo.log_audit.assert_called_once()
        call_args = mock_repo.log_audit.call_args
        assert call_args[0][0] == "equipment_delete"
        assert call_args[0][1] == 1

    def test_delete_equipment_logs_audit_with_old_info(self, equipment_service, mock_repo):
        mock_repo.find_for_delete.return_value = {
            "name": "打印机", "client": "测试学校",
        }
        mock_repo.soft_delete.return_value = None
        mock_repo.log_audit.return_value = None

        result = equipment_service.delete_equipment(equip_id=5)

        audit_call = mock_repo.log_audit.call_args
        assert "打印机(测试学校)" in audit_call[1].get("new_data", audit_call[0][2] if len(audit_call[0]) > 2 else "")


class TestGetEquipmentDetail:

    def test_get_equipment_detail_not_found_raises_error(self, equipment_service, mock_repo):
        mock_repo.find_detail.return_value = None
        mock_repo.get_finance_summary.return_value = {}

        with pytest.raises(EquipmentError, match="设备 #999 不存在"):
            equipment_service.get_equipment_detail(equip_id=999)

    def test_get_equipment_detail_includes_finance_summary(self, equipment_service, mock_repo):
        mock_repo.find_detail.return_value = {
            "id": 1, "name": "投影仪", "client": "集宁一中",
        }
        mock_repo.get_finance_summary.return_value = {
            "total_cost": 5000, "total_income": 8000,
        }

        result = equipment_service.get_equipment_detail(equip_id=1)

        assert "finance_summary" in result
        assert result["finance_summary"]["total_cost"] == 5000


class TestRestoreEquipment:

    def test_restore_equipment_success(self, equipment_service, mock_repo):
        mock_repo.restore.return_value = {
            "name": "投影仪", "client": "集宁一中",
        }
        mock_repo.log_audit.return_value = None

        result = equipment_service.restore_equipment(equip_id=1)

        assert "已恢复" in result["message"]
        mock_repo.restore.assert_called_once_with(1)

    def test_restore_equipment_not_deleted_raises_error(self, equipment_service, mock_repo):
        mock_repo.restore.return_value = None

        with pytest.raises(EquipmentError, match="不存在或未被删除"):
            equipment_service.restore_equipment(equip_id=999)
