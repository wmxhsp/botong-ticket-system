"""
博通 — 设备应用服务（新架构版）
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import os

from domain.exceptions import EquipmentError

logger = logging.getLogger(__name__)


class EquipmentService:

    def __init__(self, repo, event_bus=None, reminder_service=None):
        self._repo = repo
        self._event_bus = event_bus
        self._reminder_service = reminder_service

    def set_reminder_service(self, svc):
        self._reminder_service = svc

    def get_equipment_detail(self, equip_id: int) -> Dict[str, Any]:
        equip = self._repo.find_detail(equip_id)
        if not equip:
            raise EquipmentError(f"设备 #{equip_id} 不存在")
        equip["finance_summary"] = self.get_equipment_finance_summary(equip_id)
        return equip

    def get_equipment_finance_summary(self, equip_id: int) -> Dict[str, Any]:
        return self._repo.get_finance_summary(equip_id)

    def get_equipment_tickets(self, equip_id: int) -> List[Dict]:
        return self._repo.get_equipment_tickets(equip_id)

    def get_equipment(self, equip_id: int) -> Optional[Dict]:
        return self._repo.find_by_id(equip_id)

    def list_equipment(self, page: int = 1, page_size: int = 20,
                       sort_by: str = "client", sort_dir: str = "asc",
                       search: str = "", status: str = "", client: str = "") -> Dict:
        return self._repo.find_list(page=page, page_size=page_size,
                                    sort_by=sort_by, sort_dir=sort_dir,
                                    search=search, status=status, client=client)

    def create_equipment(self, data: Dict) -> Dict:
        self._repo.save(data)
        return {"message": f"设备已创建: {data['name']}"}

    def update_equipment(self, equip_id: int, **fields) -> Dict:
        if "status" in fields:
            old = self._repo.find_old_status(equip_id)
            if old and old.get("status") != fields["status"]:
                old_info = f"状态:{old['status']}"
                new_info = f"{old['name']} 状态: {old['status']} → {fields['status']}"
                self._repo.log_audit("equipment_status_change", equip_id, old_data=old_info, new_data=new_info)
        self._repo.update(equip_id, fields)
        return {"message": "设备信息已更新"}

    def has_tickets(self, equip_id: int) -> bool:
        return self._repo.has_tickets(equip_id)

    def delete_equipment(self, equip_id: int) -> Dict:
        old = self._repo.find_for_delete(equip_id)
        old_info = f"{old['name']}({old['client']})" if old else f"#{equip_id}"
        self._repo.soft_delete(equip_id)
        self._repo.log_audit("equipment_delete", equip_id, new_data=old_info)
        return {"message": f"设备已删除（可恢复）: {old_info}"}

    def restore_equipment(self, equip_id: int) -> Dict:
        equip = self._repo.restore(equip_id)
        if not equip:
            raise EquipmentError(f"设备 #{equip_id} 不存在或未被删除")
        info = f"{equip['name']}({equip['client']})"
        self._repo.log_audit("equipment_restore", equip_id, new_data=info)
        return {"message": f"设备已恢复: {info}"}

    def list_by_client(self, client_name: str) -> List[Dict]:
        return self._repo.find_by_client(client_name)

    def search_equipment(self, keyword: str, limit: int = 6) -> List[Dict]:
        return self._repo.search(keyword, limit)

    def get_warranty_summary(self) -> Dict:
        return self._repo.get_warranty_summary()

    def get_maintenance_summary(self) -> Dict:
        return self._repo.get_maintenance_summary()

    def get_overdue_maintenance(self, days: int = 30) -> List[Dict]:
        return self._repo.get_overdue_maintenance(days)

    def record_maintenance(self, equip_id: int, content: str = "") -> Dict:
        equip = self._repo.find_detail(equip_id)
        if not equip:
            raise EquipmentError(f"设备 #{equip_id} 不存在")

        now_str = datetime.now().strftime("%Y-%m-%d")
        cycle = equip.get("maintenance_cycle", "")

        next_maint = ""
        if cycle:
            try:
                rs = self._reminder_service
                if rs and hasattr(rs, '_calc_next_maintenance'):
                    next_maint = rs._calc_next_maintenance(cycle, now_str)
            except Exception:
                pass

        result = self._repo.record_maintenance(equip_id, content, next_maint)
        if not result:
            raise EquipmentError(f"设备 #{equip_id} 不存在")
        return {"message": "维护记录已更新", "last_maintenance": result["last_maintenance"],
                "next_maintenance": result["next_maintenance"]}

    def get_maintenance_history(self, equip_id: int) -> List[Dict]:
        return self._repo.get_maintenance_history(equip_id)

    def get_status_timeline(self, equip_id: int) -> List[Dict]:
        return self._repo.get_status_timeline(equip_id)

    def list_components(self, equip_id: int) -> List[Dict]:
        return self._repo.list_components(equip_id)

    def add_component(self, equip_id: int, name: str, spec: str = "", count: int = 1) -> Dict:
        if not name:
            raise EquipmentError("组件名称不能为空")
        self._repo.add_component(equip_id, name, spec, count)
        return {"message": f"组件已添加: {name}"}

    def update_component(self, comp_id: int, **fields) -> Dict:
        self._repo.update_component(comp_id, **fields)
        return {"message": "组件已更新"}

    def delete_component(self, comp_id: int) -> Dict:
        self._repo.delete_component(comp_id)
        return {"message": "组件已删除"}

    def batch_delete(self, ids: List[int]) -> Dict:
        self._repo.batch_soft_delete(ids)
        for eid in ids:
            self._repo.log_audit("equipment_batch_delete", eid, new_data="batch_delete")
        return {"message": f"已删除 {len(ids)} 台设备"}

    def batch_restore(self, ids: List[int]) -> Dict:
        self._repo.batch_restore(ids)
        for eid in ids:
            self._repo.log_audit("equipment_batch_restore", eid, new_data="batch_restore")
        return {"message": f"已恢复 {len(ids)} 台设备"}

    def batch_get_qr_urls(self, ids: List[int], base_url: str) -> List[Dict]:
        return self._repo.batch_get_qr_urls(ids, base_url)

    def get_equipment_photos(self, equip_id: int) -> list:
        return self._repo.get_photos(equip_id)

    def add_equipment_photo(self, equip_id: int, filepath: str, photo_type: str = 'image'):
        self._repo.add_photo(equip_id, filepath, photo_type)

    def delete_equipment_photo(self, photo_id: int, equip_id: int):
        base = Path(__file__).resolve().parent.parent.parent
        p = self._repo.find_photo(photo_id, equip_id)
        if p:
            fp = str(base / p["filepath"].lstrip("/"))
            if os.path.exists(fp):
                os.remove(fp)
        self._repo.delete_photo(photo_id)

    def delete_equipment_photo_by_path(self, filepath: str, equip_id: int):
        base = Path(__file__).resolve().parent.parent.parent
        fp = str(base / filepath.lstrip("/"))
        if os.path.exists(fp):
            os.remove(fp)
        self._repo.delete_photo_by_path(filepath)

    def update_equipment_photo_cover(self, photo_id: int, equip_id: int, is_cover: int):
        self._repo.update_photo_cover(photo_id, equip_id, is_cover)

    def get_equipment_stats(self) -> Dict[str, Any]:
        return self._repo.get_stats()
