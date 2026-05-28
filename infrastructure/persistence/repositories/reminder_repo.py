"""
博通 — 提醒仓储 SQLite 实现
"""

import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from infrastructure.persistence.legacy_db import db_query, db_query_one, get_db

logger = logging.getLogger(__name__)


class SqliteReminderRepository:

    def __init__(self, conn=None):
        self._conn = conn

    @contextmanager
    def _ensure_conn(self):
        if self._conn:
            yield self._conn
        else:
            with get_db() as conn:
                yield conn

    def create(self, data: Dict[str, Any]) -> int:
        """创建提醒"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO ticket_reminders
                   (ticket_id, reminder_time, content, repeat_daily, active, created_at)
                   VALUES (?, ?, ?, ?, 1, datetime('now','localtime'))""",
                (data.get("ticket_id"), data.get("reminder_time"),
                 data.get("content", ""), 1 if data.get("repeat_type", "once") == "daily" else 0))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def cancel(self, ticket_id: int) -> bool:
        """停用工单的所有提醒"""
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE ticket_reminders SET active=0 WHERE ticket_id=?",
                (ticket_id,))
            if not self._conn:
                conn.commit()
            return True

    def get(self, reminder_id: int) -> Optional[Dict[str, Any]]:
        """按ID查提醒"""
        return db_query_one("SELECT id, ticket_id, remind_at, message, is_sent, created_at FROM ticket_reminders WHERE id=?", (reminder_id,))

    def get_by_ticket(self, ticket_id: int) -> List[Dict[str, Any]]:
        """按工单查提醒列表"""
        return db_query(
            "SELECT id, ticket_id, remind_at, message, is_sent FROM ticket_reminders WHERE ticket_id=? ORDER BY id",
            (ticket_id,))

    def get_active(self) -> List[Dict[str, Any]]:
        """获取活跃提醒（含工单信息）"""
        return db_query(
            """SELECT r.*, t.ticket_no, t.client, t.status as ticket_status,
                      t.appointment_at
               FROM ticket_reminders r
               LEFT JOIN tickets t ON r.ticket_id = t.id
               WHERE r.active = 1
               ORDER BY r.reminder_time""")

    def get_active_with_ticket_status(self) -> List[Dict[str, Any]]:
        """获取活跃提醒（含工单状态，用于检查周期）"""
        return db_query(
            """SELECT r.*, t.ticket_no, t.client, t.status as ticket_status,
                      t.appointment_at
               FROM ticket_reminders r
               LEFT JOIN tickets t ON r.ticket_id = t.id
               WHERE r.active = 1 AND t.status NOT IN ('closed', 'archived')""")
