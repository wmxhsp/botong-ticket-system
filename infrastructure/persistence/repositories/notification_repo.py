"""
博通 — 通知仓储 SQLite 实现
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from infrastructure.persistence.legacy_db import db_query, db_query_one, get_db

logger = logging.getLogger(__name__)


class SqliteNotificationRepository:

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
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO notifications
                   (title, content, ticket_id, reminder_id, read, created_at)
                   VALUES (?, ?, ?, ?, 0, datetime('now','localtime'))""",
                (data.get("title", ""), data.get("content", ""),
                 data.get("ticket_id"), data.get("reminder_id")))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def get_pending(self) -> List[Dict[str, Any]]:
        """获取未读通知（含工单信息）"""
        return db_query(
            """SELECT n.*, t.ticket_no, t.client, t.status as ticket_status
               FROM notifications n
               LEFT JOIN tickets t ON n.ticket_id = t.id
               WHERE n.read = 0
               ORDER BY n.created_at DESC""")

    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取全部通知（含工单信息）"""
        return db_query(
            """SELECT n.*, t.ticket_no, t.client, t.status as ticket_status
               FROM notifications n
               LEFT JOIN tickets t ON n.ticket_id = t.id
               ORDER BY n.created_at DESC LIMIT ?""",
            (limit,))

    def mark_read(self, notification_id: int) -> bool:
        """标记通知已读"""
        with self._ensure_conn() as conn:
            conn.execute("UPDATE notifications SET read=1 WHERE id=?", (notification_id,))
            if not self._conn:
                conn.commit()
            return True

    def mark_all_read(self) -> int:
        """全部标记已读"""
        with self._ensure_conn() as conn:
            cursor = conn.execute("UPDATE notifications SET read=1 WHERE read=0")
            if not self._conn:
                conn.commit()
            return cursor.rowcount

    def get_unread_count(self) -> int:
        """统计未读数"""
        row = db_query_one("SELECT COUNT(*) as c FROM notifications WHERE read=0")
        return row["c"] if row else 0

    def check_exists_today(self, title: str, reminder_id: int = None) -> bool:
        """检查今日是否已发送过指定通知"""
        today = datetime.now().strftime("%Y-%m-%d")
        if reminder_id:
            row = db_query_one(
                "SELECT COUNT(*) as c FROM notifications WHERE reminder_id=? AND created_at>=?",
                (reminder_id, today))
        else:
            row = db_query_one(
                "SELECT COUNT(*) as c FROM notifications WHERE title=? AND created_at>=?",
                (title, today))
        return (row["c"] if row else 0) > 0
