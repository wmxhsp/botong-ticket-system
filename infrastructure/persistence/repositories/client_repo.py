"""
博通 (Botong) — 客户仓储 SQLite 实现

支持外部 Connection 注入（conn 参数），用于 UnitOfWork 事务内共享连接。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from infrastructure.persistence.legacy_db import db_query, db_query_one, get_db

logger = logging.getLogger(__name__)


class SqliteClientRepository:
    """客户仓储 - SQLite 实现，支持连接注入"""

    def __init__(self, conn=None):
        self._conn = conn

    @contextmanager
    def _ensure_conn(self):
        if self._conn:
            yield self._conn
        else:
            with get_db() as conn:
                yield conn

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """按名称查询客户"""
        client = db_query_one("SELECT id, name, contact, phone, email, address, payment_terms, notes, created_at, updated_at FROM clients WHERE name = ?", (name,))
        if not client:
            return None
        client["active_tickets"] = db_query_one(
            """SELECT COUNT(*) as cnt FROM tickets
               WHERE client = ? AND status NOT IN ('closed','archived','cancelled')""",
            (name,))["cnt"]
        client["device_count"] = db_query_one(
            "SELECT COUNT(*) as cnt FROM equipment WHERE client = ?", (name,))["cnt"]
        client["unpaid_amount"] = db_query_one(
            """SELECT COALESCE(SUM(COALESCE(total,0)),0) as total FROM tickets
               WHERE client = ? AND billing_status IN ('unpaid','pending')""",
            (name,))["total"]
        client["last_ticket_date"] = db_query_one(
            "SELECT MAX(created_at) as dt FROM tickets WHERE client = ?", (name,))["dt"]
        return client

    def find_list(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """客户列表（含统计）"""
        conditions = []
        params = []
        filters = filters or {}

        keyword = filters.get("q")
        if keyword:
            conditions.append(
                "(c.name LIKE ? OR c.contact LIKE ? OR c.phone LIKE ?)")
            q = f"%{keyword}%"
            params.extend([q, q, q])

        where = " AND ".join(conditions) if conditions else "1=1"

        return db_query(
            f"""
            SELECT c.*,
                (SELECT COUNT(*) FROM tickets t
                 WHERE t.client = c.name AND t.status NOT IN ('closed','archived','cancelled')
                ) as active_tickets,
                (SELECT COUNT(*) FROM equipment e WHERE e.client = c.name) as device_count,
                (SELECT COALESCE(SUM(COALESCE(t.total,0)),0) FROM tickets t
                 WHERE t.client = c.name AND t.billing_status IN ('unpaid','pending')
                ) as unpaid_amount,
                (SELECT MAX(t.created_at) FROM tickets t WHERE t.client = c.name) as last_ticket_date
            FROM clients c
            WHERE {where}
            ORDER BY c.name
            """,
            tuple(params)
        )

    def save(self, data: Dict[str, Any]) -> int:
        """创建客户"""
        with self._ensure_conn() as conn:
            conn.execute(
                """INSERT INTO clients (name, contact, phone, notes, created_at, updated_at)
                   VALUES (?,?,?,?,datetime('now','localtime'),datetime('now','localtime'))""",
                (data["name"], data.get("contact", ""),
                 data.get("phone", ""), data.get("notes", "")))
            if not self._conn:
                conn.commit()
            return 1

    def update(self, name: str, data: Dict[str, Any]) -> bool:
        """更新客户"""
        allowed = ["name", "contact", "phone", "notes",
                    "payment_terms", "billing_address"]
        updates = []
        params = []
        for key, value in data.items():
            if key in allowed and value is not None:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        updates.append("updated_at = datetime('now','localtime')")
        params.append(name)

        with self._ensure_conn() as conn:
            conn.execute(f"UPDATE clients SET {', '.join(updates)} WHERE name = ?",
                         tuple(params))

            # 同步更新关联表
            new_name = data.get("name")
            if new_name and new_name != name:
                conn.execute("UPDATE tickets SET client = ? WHERE client = ?",
                             (new_name, name))
                conn.execute("UPDATE equipment SET client = ? WHERE client = ?",
                             (new_name, name))
                conn.execute("UPDATE income_records SET client = ? WHERE client = ?",
                             (new_name, name))

            if not self._conn:
                conn.commit()
            return True

    def delete(self, name: str) -> bool:
        """删除客户"""
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM clients WHERE name = ?", (name,))
            if not self._conn:
                conn.commit()
            return True

    def check_associations(self, name: str) -> List[Dict[str, Any]]:
        """检查客户关联数据"""
        checks = [
            ("tickets", "工单", "SELECT COUNT(*) as cnt FROM tickets WHERE client = ?"),
            ("income_records", "收入记录", "SELECT COUNT(*) as cnt FROM income_records WHERE client = ?"),
            ("sales_records", "销售记录", "SELECT COUNT(*) as cnt FROM sales_records WHERE client = ?"),
            ("equipment", "设备", "SELECT COUNT(*) as cnt FROM equipment WHERE client = ?"),
            ("service_agreements", "服务协议", "SELECT COUNT(*) as cnt FROM service_agreements WHERE client = ?"),
        ]
        results = []
        for table, label, sql in checks:
            try:
                row = db_query_one(sql, (name,))
                cnt = row["cnt"] if row else 0
                results.append({"table": table, "label": label, "count": cnt})
            except Exception:
                results.append({"table": table, "label": label, "count": 0})
        return results

    def get_profile_stats(self, name: str) -> Dict[str, Any]:
        """获取客户画像统计数据"""
        stats = db_query_one("""
            SELECT
                COUNT(*) as total_orders,
                COALESCE(SUM(COALESCE(total,0)),0) as total_spent,
                SUM(CASE WHEN billing_status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN billing_status IN ('unpaid','pending') THEN 1 ELSE 0 END) as unpaid_count,
                MAX(created_at) as last_order_date
            FROM tickets WHERE client = ?
        """, (name,))

        aging = db_query_one("""
            SELECT COALESCE(SUM(COALESCE(total,0)),0) as overdue_amount
            FROM tickets WHERE client = ? AND billing_status IN ('unpaid','pending')
              AND julianday('now') - julianday(created_at) > 60
        """, (name,))

        payment_history = db_query("""
            SELECT created_at, closed_at, total, billing_status
            FROM tickets WHERE client = ? AND billing_status = 'paid'
              AND closed_at IS NOT NULL
            ORDER BY created_at DESC LIMIT 50
        """, (name,))

        return {"stats": stats, "aging": aging, "payment_history": payment_history}

    def search_clients(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        kw = f"%{keyword}%"
        return db_query(
            "SELECT name, contact, phone FROM clients "
            "WHERE name LIKE ? OR contact LIKE ? OR phone LIKE ? "
            "ORDER BY name LIMIT ?",
            (kw, kw, kw, limit)) or []

    def get_ticket_count(self, client_name: str) -> int:
        result = db_query_one(
            "SELECT COUNT(*) as c FROM tickets WHERE client = ?", (client_name,))
        return result["c"] if result else 0

    def get_equipment_count(self, client_name: str) -> int:
        result = db_query_one(
            "SELECT COUNT(*) as c FROM equipment WHERE client = ?", (client_name,))
        return result["c"] if result else 0

    def count_clients(self) -> int:
        result = db_query_one("SELECT COUNT(*) as c FROM clients")
        return result["c"] if result else 0
