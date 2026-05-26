"""
博通 — 设备仓储 SQLite 实现，支持连接注入
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from infrastructure.persistence.legacy_db import db_query, db_query_one, db_execute, get_db

logger = logging.getLogger(__name__)


class SqliteEquipmentRepository:

    def __init__(self, conn=None):
        self._conn = conn

    def _has_column(self, table: str, column: str) -> bool:
        from infrastructure.persistence.legacy_db import get_db
        try:
            with get_db() as conn:
                cur = conn.execute(f"PRAGMA table_info({table})")
                cols = [r[1] if isinstance(r, tuple) else r['name'] for r in cur.fetchall()]
                return column in cols
        except Exception:
            return False

    def _deleted_filter(self, alias: str = "e") -> str:
        # 如果表不存在 is_deleted 列，返回永真条件
        has = self._has_column("equipment", "is_deleted")
        if not has:
            return "1=1"
        return f"({alias}.is_deleted IS NULL OR {alias}.is_deleted = 0)"

    @contextmanager
    def _ensure_conn(self):
        if self._conn:
            yield self._conn
        else:
            with get_db() as conn:
                yield conn

    def find_by_id(self, equip_id: int) -> Optional[Dict[str, Any]]:
        where = self._deleted_filter(alias="")
        return db_query_one(
            f"SELECT id, name FROM equipment WHERE id = ? AND {where}",
            (equip_id,))

    def find_detail(self, equip_id: int) -> Optional[Dict[str, Any]]:
        where = self._deleted_filter(alias="e")
        equip = db_query_one(
            "SELECT e.*, c.name as client_name, c.hourly_rate, c.contact as client_contact, c.phone as client_phone "
            "FROM equipment e LEFT JOIN clients c ON e.client = c.name "
            "WHERE e.id = ? AND " + where,
            (equip_id,))
        return equip

    def find_list(self, page: int = 1, page_size: int = 20,
                  sort_by: str = "client", sort_dir: str = "asc",
                  search: str = "", status: str = "", client: str = "") -> Dict[str, Any]:
        allowed_sort = {"name", "model", "client", "location", "warranty_expire",
                        "status", "type", "brand", "serial_no", "install_date"}
        if sort_by not in allowed_sort:
            sort_by = "client"
        if sort_dir not in ("asc", "desc"):
            sort_dir = "asc"
        sort_col = f"e.{sort_by}" if sort_by in allowed_sort else "e.client"

        where = self._deleted_filter(alias="e")
        params = []
        if search:
            kw = f"%{search}%"
            where += """ AND (e.name LIKE ? OR e.serial_no LIKE ? OR e.model LIKE ?
                OR e.location LIKE ? OR e.client LIKE ? OR e.brand LIKE ?)"""
            params = [kw, kw, kw, kw, kw, kw]

        if status:
            where += " AND e.status = ?"
            params.append(status)

        if client:
            where += " AND e.client = ?"
            params.append(client)

        count_row = db_query_one(f"SELECT COUNT(*) as c FROM equipment e WHERE {where}", params)
        total = count_row["c"] if count_row else 0

        offset = (page - 1) * page_size
        items = db_query(
            f"SELECT e.*, c.name as client_name, c.hourly_rate "
            f"FROM equipment e LEFT JOIN clients c ON e.client = c.name "
            f"WHERE {where} ORDER BY {sort_col} {sort_dir}, e.id LIMIT ? OFFSET ?",
            tuple(params + [page_size, offset]))

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def save(self, data: Dict[str, Any]) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO equipment (name,type,brand,model,serial_no,location,client,"
                "install_date,warranty_expire,status,notes,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (data["name"], data.get("type", ""), data.get("brand", ""),
                 data.get("model", ""), data.get("serial_no", ""),
                 data.get("location", ""), data["client"],
                 data.get("install_date", ""), data.get("warranty_expire", ""),
                 data.get("status", "正常"), data.get("notes", ""), now, now))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def update(self, equip_id: int, data: Dict[str, Any]) -> bool:
        allowed = ["name", "type", "brand", "model", "serial_no", "location", "client",
                   "install_date", "warranty_expire", "status", "notes",
                   "maintenance_cycle", "last_maintenance", "next_maintenance"]
        updates = []
        params = []
        for f in allowed:
            if f in data:
                updates.append(f"{f} = ?")
                params.append(data[f])
        if not updates:
            return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        updates.append("updated_at = ?")
        params.append(now)
        params.append(equip_id)
        with self._ensure_conn() as conn:
            conn.execute(f"UPDATE equipment SET {', '.join(updates)} WHERE id = ?",
                         tuple(params))
            if not self._conn:
                conn.commit()
            return True

    def soft_delete(self, equip_id: int) -> bool:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._ensure_conn() as conn:
            conn.execute("UPDATE equipment SET is_deleted = 1, updated_at = ? WHERE id = ?",
                         (now, equip_id))
            if not self._conn:
                conn.commit()
            return True

    def restore(self, equip_id: int) -> Optional[Dict[str, Any]]:
        where_restored = "(is_deleted = 1)" if self._has_column("equipment", "is_deleted") else "0=1"
        equip = db_query_one(
            "SELECT id, name, client, serial_no FROM equipment WHERE id = ? AND " + where_restored,
            (equip_id,))
        if not equip:
            return None
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._ensure_conn() as conn:
            conn.execute("UPDATE equipment SET is_deleted = 0, updated_at = ? WHERE id = ?",
                         (now, equip_id))
            if not self._conn:
                conn.commit()
            return equip

    def find_by_client(self, client_name: str) -> List[Dict[str, Any]]:
        cols = ("id, name, type, brand, model, serial_no, location, client, "
                "install_date, warranty_expire, status, maintenance_cycle, "
                "last_maintenance, next_maintenance")
        where_client = self._deleted_filter(alias="")
        return db_query(
            f"SELECT {cols} FROM equipment WHERE client = ? AND " + where_client + " ORDER BY name",
            (client_name,))

    def search(self, keyword: str, limit: int = 6) -> List[Dict[str, Any]]:
        kw = f"%{keyword}%"
        where_search = self._deleted_filter(alias="")
        return db_query(
            "SELECT id, name, serial_no, model, client, location FROM equipment "
            "WHERE " + where_search + " "
            "AND (name LIKE ? OR serial_no LIKE ? OR model LIKE ? OR location LIKE ? OR client LIKE ?) "
            "ORDER BY id DESC LIMIT ?",
            (kw, kw, kw, kw, kw, limit)) or []

    def has_tickets(self, equip_id: int) -> bool:
        result = db_query_one(
            "SELECT COUNT(*) as c FROM ticket_equipment WHERE equipment_id = ?", (equip_id,))
        return result["c"] > 0 if result else False

    def get_finance_summary(self, equip_id: int) -> Dict[str, Any]:
        result = db_query_one(
            "SELECT COUNT(t.id) as total_tickets, "
            "COALESCE(SUM(t.total), 0) as total_revenue, "
            "COALESCE(SUM(t.total_material), 0) as total_material_cost, "
            "COALESCE(SUM(t.total_labor), 0) as total_labor_cost, "
            "COALESCE(SUM(t.total_external), 0) as total_external_cost "
            "FROM ticket_equipment te JOIN tickets t ON te.ticket_id = t.id "
            "WHERE te.equipment_id = ?", (equip_id,))
        if not result:
            return {"total_tickets": 0, "total_revenue": 0,
                    "total_material_cost": 0, "total_labor_cost": 0,
                    "total_external_cost": 0, "total_cost": 0, "total_profit": 0}
        data = dict(result)
        data["total_cost"] = (data["total_material_cost"] + data["total_labor_cost"] +
                              data["total_external_cost"])
        data["total_profit"] = data["total_revenue"] - data["total_cost"]
        return data

    def get_equipment_tickets(self, equip_id: int) -> List[Dict[str, Any]]:
        return db_query(
            "SELECT t.id, t.ticket_no, t.client, t.description as content, t.status, "
            "t.created_at, t.total FROM ticket_equipment te "
            "JOIN tickets t ON te.ticket_id = t.id WHERE te.equipment_id = ? "
            "ORDER BY t.created_at DESC", (equip_id,))

    def get_warranty_summary(self) -> Dict[str, Any]:
        where_w = self._deleted_filter(alias="")
        expiring = db_query_one(
            "SELECT COUNT(*) as c FROM equipment WHERE " + where_w +
            " AND warranty_expire != '' AND warranty_expire <= date('now','+30 days') "
            "AND warranty_expire >= date('now')")
        expired = db_query_one(
            "SELECT COUNT(*) as c FROM equipment WHERE " + where_w +
            " AND warranty_expire != '' AND warranty_expire < date('now')")
        return {
            "expiring": expiring["c"] if expiring else 0,
            "expired": expired["c"] if expired else 0,
        }

    def get_maintenance_summary(self) -> Dict[str, Any]:
        where_m = self._deleted_filter(alias="")
        overdue = db_query_one(
            "SELECT COUNT(*) as c FROM equipment WHERE " + where_m +
            " AND next_maintenance IS NOT NULL AND next_maintenance != '' "
            "AND next_maintenance < date('now','localtime')")
        upcoming = db_query_one(
            "SELECT COUNT(*) as c FROM equipment WHERE " + where_m +
            " AND next_maintenance IS NOT NULL AND next_maintenance != '' "
            "AND next_maintenance >= date('now','localtime') "
            "AND next_maintenance <= date('now','localtime','+30 days')")
        return {
            "overdue": overdue["c"] if overdue else 0,
            "upcoming": upcoming["c"] if upcoming else 0,
        }

    def get_overdue_maintenance(self, days: int = 30) -> List[Dict[str, Any]]:
        where_over = self._deleted_filter(alias="e")
        return db_query(
            "SELECT e.id, e.name, e.client, e.model, e.maintenance_cycle, "
            "e.last_maintenance, e.next_maintenance, c.contact, c.phone "
            "FROM equipment e LEFT JOIN clients c ON e.client = c.name "
            "WHERE " + where_over +
            " AND e.next_maintenance IS NOT NULL AND e.next_maintenance != '' "
            "AND e.next_maintenance <= date('now','localtime',?) "
            "AND e.next_maintenance >= date('now','localtime') "
            "ORDER BY e.next_maintenance",
            (f'+{days} days',))

    def record_maintenance(self, equip_id: int, content: str = "",
                           next_maint: str = "") -> Dict[str, Any]:
        equip = db_query_one(
            "SELECT id, name, client, maintenance_cycle, next_maintenance FROM equipment WHERE id = ?",
            (equip_id,))
        if not equip:
            return None
        now_str = datetime.now().strftime("%Y-%m-%d")
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE equipment SET last_maintenance=?, next_maintenance=?, updated_at=? WHERE id=?",
                (now_str, next_maint, now_str + " 00:00", equip_id))
            conn.execute(
                "INSERT INTO maintenance_records (equipment_id, type, date, content, staff, status, next_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (equip_id, equip.get("maintenance_cycle") or "常规", now_str,
                 content or f"{equip['name']} 定期维护", "system", "completed", next_maint))
            if not self._conn:
                conn.commit()
            return {"last_maintenance": now_str, "next_maintenance": next_maint}

    def get_maintenance_history(self, equip_id: int) -> List[Dict[str, Any]]:
        return db_query(
            "SELECT id, equipment_id, type, date, content, staff, cost, next_date, status "
            "FROM maintenance_records WHERE equipment_id = ? ORDER BY date DESC",
            (equip_id,)) or []

    def get_status_timeline(self, equip_id: int) -> List[Dict[str, Any]]:
        timeline = []
        logs = db_query(
            "SELECT action, new_data, created_at FROM audit_log "
            "WHERE table_name = 'equipment' AND record_id = ? "
            "AND action IN ('equipment_delete', 'equipment_restore', 'equipment_status_change') "
            "ORDER BY created_at DESC LIMIT 20", (equip_id,)) or []
        for log in logs:
            action = log.get("action", "")
            ts = log.get("created_at", "")
            info = log.get("new_data", "")
            icon = "bi-trash text-danger"
            label = "删除"
            if action == "equipment_restore":
                icon = "bi-arrow-counterclockwise text-success"
                label = "恢复"
            elif action == "equipment_status_change":
                icon = "bi-arrow-left-right text-primary"
                label = "状态变更"
            timeline.append({
                "type": "status", "icon": icon, "label": label,
                "description": info, "timestamp": str(ts) if ts else "",
            })
        maint = self.get_maintenance_history(equip_id)
        for m in maint:
            timeline.append({
                "type": "maintenance", "icon": "bi-tools text-success", "label": "维护",
                "description": m.get("content", "维护") or "维护",
                "timestamp": m.get("date", ""),
                "detail": f"责任人: {m.get('staff', '-')} | 下次: {m.get('next_date', '-')}",
            })
        timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return timeline

    def list_components(self, equip_id: int) -> List[Dict[str, Any]]:
        return db_query(
            "SELECT * FROM equipment_components WHERE equipment_id = ? ORDER BY name",
            (equip_id,)) or []

    def add_component(self, equip_id: int, name: str, spec: str = "", count: int = 1) -> int:
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO equipment_components (equipment_id, name, spec, count) VALUES (?, ?, ?, ?)",
                (equip_id, name, spec, count))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def update_component(self, comp_id: int, **fields) -> bool:
        updates = []
        params = []
        for f in ["name", "spec", "count"]:
            if f in fields:
                updates.append(f"{f} = ?")
                params.append(fields[f])
        if not updates:
            return False
        params.append(comp_id)
        with self._ensure_conn() as conn:
            conn.execute(f"UPDATE equipment_components SET {', '.join(updates)} WHERE id=?",
                         tuple(params))
            if not self._conn:
                conn.commit()
            return True

    def delete_component(self, comp_id: int) -> bool:
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM equipment_components WHERE id = ?", (comp_id,))
            if not self._conn:
                conn.commit()
            return True

    def batch_soft_delete(self, ids: List[int]) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        placeholders = ",".join("?" for _ in ids)
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                f"UPDATE equipment SET is_deleted=1, updated_at=? WHERE id IN ({placeholders})",
                [now] + ids)
            if not self._conn:
                conn.commit()
            return cursor.rowcount

    def batch_restore(self, ids: List[int]) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        placeholders = ",".join("?" for _ in ids)
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                f"UPDATE equipment SET is_deleted=0, updated_at=? WHERE id IN ({placeholders})",
                [now] + ids)
            if not self._conn:
                conn.commit()
            return cursor.rowcount

    def batch_get_qr_urls(self, ids: List[int], base_url: str) -> List[Dict[str, Any]]:
        placeholders = ",".join("?" for _ in ids)
        items = db_query(
            f"SELECT id, name, client FROM equipment WHERE id IN ({placeholders})", ids) or []
        results = []
        for item in items:
            results.append({
                "id": item["id"],
                "name": item.get("name", ""),
                "client": item.get("client", ""),
                "qr_url": f"{base_url}/api/v1/equipment/{item['id']}/qrcode",
                "detail_url": f"{base_url}/equipment/{item['id']}",
            })
        return results

    def get_photos(self, equip_id: int) -> List[Dict[str, Any]]:
        return db_query(
            "SELECT id, filepath, type, is_cover, created_at FROM equipment_photos "
            "WHERE equip_id = ? ORDER BY is_cover DESC, created_at DESC",
            (equip_id,)) or []

    def add_photo(self, equip_id: int, filepath: str, photo_type: str = 'image') -> int:
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO equipment_photos (equip_id, filepath, type, created_at) "
                "VALUES (?, ?, ?, datetime('now'))",
                (equip_id, filepath, photo_type))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def find_photo(self, photo_id: int, equip_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one(
            "SELECT filepath FROM equipment_photos WHERE id = ? AND equip_id = ?",
            (photo_id, equip_id))

    def delete_photo(self, photo_id: int) -> bool:
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM equipment_photos WHERE id = ?", (photo_id,))
            if not self._conn:
                conn.commit()
            return True

    def delete_photo_by_path(self, filepath: str) -> bool:
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM equipment_photos WHERE filepath = ?", (filepath,))
            if not self._conn:
                conn.commit()
            return True

    def update_photo_cover(self, photo_id: int, equip_id: int, is_cover: int) -> bool:
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE equipment_photos SET is_cover = ? WHERE id = ? AND equip_id = ?",
                (is_cover, photo_id, equip_id))
            if not self._conn:
                conn.commit()
            return True

    def get_stats(self) -> Dict[str, Any]:
        type_dist = db_query(
            "SELECT COALESCE(type,'其他') as type, COUNT(*) as cnt FROM equipment "
            "WHERE (is_deleted IS NULL OR is_deleted = 0) GROUP BY type ORDER BY cnt DESC")
        status_dist = db_query(
            "SELECT status, COUNT(*) as cnt FROM equipment "
            "WHERE (is_deleted IS NULL OR is_deleted = 0) GROUP BY status")
        warranty_stats = db_query_one(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN warranty_expire != '' AND warranty_expire >= date('now') THEN 1 ELSE 0 END) as in_warranty, "
            "SUM(CASE WHEN warranty_expire != '' AND warranty_expire < date('now') THEN 1 ELSE 0 END) as expired, "
            "SUM(CASE WHEN warranty_expire = '' THEN 1 ELSE 0 END) as no_warranty "
            "FROM equipment WHERE (is_deleted IS NULL OR is_deleted = 0)")
        top_clients = db_query(
            "SELECT client, COUNT(*) as cnt FROM equipment "
            "WHERE (is_deleted IS NULL OR is_deleted = 0) GROUP BY client ORDER BY cnt DESC LIMIT 10")
        return {
            "type_distribution": type_dist or [],
            "status_distribution": status_dist or [],
            "warranty": {
                "total": warranty_stats["total"] if warranty_stats else 0,
                "in_warranty": warranty_stats["in_warranty"] if warranty_stats else 0,
                "expired": warranty_stats["expired"] if warranty_stats else 0,
                "no_warranty": warranty_stats["no_warranty"] if warranty_stats else 0,
            },
            "top_clients": top_clients or [],
        }

    def log_audit(self, action: str, equip_id: int, old_data: str = "", new_data: str = ""):
        try:
            db_execute(
                "INSERT INTO audit_log (action, table_name, record_id, old_data, new_data, operator) "
                "VALUES (?, 'equipment', ?, ?, ?, 'system')",
                (action, equip_id, old_data, new_data))
        except Exception:
            pass

    def find_old_status(self, equip_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT status, name FROM equipment WHERE id = ?", (equip_id,))

    def find_for_delete(self, equip_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one(
            "SELECT name, client, serial_no FROM equipment WHERE id = ?", (equip_id,))
