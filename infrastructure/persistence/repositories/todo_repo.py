"""
博通 — 待办仓储 SQLite 实现，支持连接注入
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import date, timedelta, datetime
from contextlib import contextmanager

from infrastructure.persistence.legacy_db import db_query, db_query_one, get_db

logger = logging.getLogger(__name__)


class SqliteTodoRepository:
    """待办仓储 - SQLite 实现，支持连接注入"""

    def __init__(self, conn=None):
        self._conn = conn

    @contextmanager
    def _ensure_conn(self):
        if self._conn:
            yield self._conn
        else:
            with get_db() as conn:
                yield conn

    def find_by_id(self, todo_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT id, title, done, priority, parent_id, sort_order, remind, remind_at, repeat_rule FROM todos WHERE id = ?", (todo_id,))

    def find_list(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """动态查询待办列表"""
        conditions = []
        params = []
        filters = filters or {}

        if filters.get("parent_only"):
            conditions.append("parent_id IS NULL")

        category = filters.get("category")
        if category in ("work", "life"):
            conditions.append("category = ?")
            params.append(category)

        done = filters.get("done")
        if done is not None:
            conditions.append("done = ?")
            params.append(1 if done else 0)

        date_filter = filters.get("date_filter", "")
        today = date.today().isoformat()
        if date_filter == "today":
            conditions.append("due_date = ?")
            params.append(today)
        elif date_filter == "overdue":
            conditions.append("due_date < ? AND done = 0")
            params.append(today)
        elif date_filter == "upcoming":
            week_later = (date.today() + timedelta(days=7)).isoformat()
            conditions.append("due_date >= ? AND due_date <= ? AND done = 0")
            params.extend([today, week_later])
        elif date_filter == "this_week":
            today_dt = date.today()
            week_start = (today_dt - timedelta(days=today_dt.weekday())).isoformat()
            week_end = (today_dt + timedelta(days=6 - today_dt.weekday())).isoformat()
            conditions.append("due_date >= ? AND due_date <= ? AND done = 0")
            params.extend([week_start, week_end])

        keyword = filters.get("keyword")
        if keyword:
            conditions.append("(title LIKE ? OR description LIKE ? OR tags LIKE ?)")
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        source_type = filters.get("source_type")
        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)

        source_id = filters.get("source_id")
        if source_id is not None:
            conditions.append("source_id = ?")
            params.append(source_id)

        where = " AND ".join(conditions) if conditions else "1=1"
        page = filters.get("page", 1)
        per_page = filters.get("per_page", 50)
        offset = (page - 1) * per_page

        return db_query(
            f"SELECT id, title, done, priority, parent_id, sort_order, remind, remind_at, repeat_rule, created_at FROM todos WHERE {where} ORDER BY sort_order, id DESC LIMIT ? OFFSET ?",
            params + [per_page, offset])

    def save(self, data: Dict[str, Any]) -> int:
        """创建待办"""
        now = data.get("created_at", "")
        if not now:
            now = datetime.now().isoformat()

        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO todos
                   (title, description, category, priority, due_date, due_time,
                    tags, remind, sort_order, source_type, source_id,
                    parent_id, repeat_rule, reminder_at, estimated_minutes,
                    created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (data.get("title", ""), data.get("description", ""),
                 data.get("category", "work"), data.get("priority", "M"),
                 data.get("due_date"), data.get("due_time"),
                 data.get("tags", ""),
                 1 if data.get("remind") else 0,
                 data.get("sort_order", 0),
                 data.get("source_type", ""), data.get("source_id"),
                 data.get("parent_id"),
                 data.get("repeat_rule", ""),
                 data.get("reminder_at"),
                 data.get("estimated_minutes"),
                 now, now))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def update(self, todo_id: int, data: Dict[str, Any]) -> bool:
        """更新待办"""
        allowed = ["title", "description", "category", "priority",
                    "due_date", "due_time", "tags", "remind", "sort_order",
                    "done", "done_at", "source_type", "source_id",
                    "repeat_rule", "reminder_at", "estimated_minutes",
                    "completed_count"]
        updates = []
        params = []
        for key, value in data.items():
            if key in allowed:
                updates.append(f"{key} = ?")
                params.append(value)
        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(todo_id)

        with self._ensure_conn() as conn:
            conn.execute(f"UPDATE todos SET {', '.join(updates)} WHERE id = ?",
                         tuple(params))
            if not self._conn:
                conn.commit()
            return True

    def delete(self, todo_id: int) -> bool:
        """删除待办（含子任务）"""
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
            conn.execute("DELETE FROM todos WHERE parent_id = ?", (todo_id,))
            if not self._conn:
                conn.commit()
            return True

    def get_subtasks(self, parent_id: int) -> List[Dict[str, Any]]:
        """获取子任务"""
        return db_query(
            "SELECT id, title, done, priority, sort_order FROM todos WHERE parent_id = ? ORDER BY sort_order, id",
            (parent_id,))

    def stats(self) -> Dict[str, Any]:
        """待办统计"""
        result = {"total": 0, "done": 0, "pending": 0, "overdue": 0,
                   "today": 0, "upcoming": 0, "high_priority": 0}
        rows = db_query("SELECT done, priority, due_date FROM todos WHERE parent_id IS NULL")
        today = date.today().isoformat()
        week_end = (date.today() + timedelta(days=7)).isoformat()

        for r in rows:
            result["total"] += 1
            if r["done"]:
                result["done"] += 1
            else:
                result["pending"] += 1
                if r.get("priority") == "H":
                    result["high_priority"] += 1
                due = r.get("due_date", "")
                if due and due < today:
                    result["overdue"] += 1
                elif due == today:
                    result["today"] += 1
                elif due and due <= week_end:
                    result["upcoming"] += 1
        return result

    def count_linked_tickets(self) -> int:
        """统计关联工单的未完成待办数"""
        row = db_query_one(
            "SELECT COUNT(*) as c FROM todos WHERE source_type='ticket' AND done=0")
        return row["c"] if row else 0

    def batch_toggle(self, todo_ids: list, done: bool) -> int:
        """批量更新完成状态"""
        now = datetime.now().isoformat()
        placeholders = ",".join("?" * len(todo_ids))
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                f"UPDATE todos SET done=?, done_at=?, updated_at=? WHERE id IN ({placeholders})",
                [1 if done else 0, now if done else None, now] + list(todo_ids))
            if not self._conn:
                conn.commit()
            return cursor.rowcount

    def batch_delete(self, todo_ids: list) -> int:
        """批量删除待办"""
        placeholders = ",".join("?" * len(todo_ids))
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                f"DELETE FROM todos WHERE id IN ({placeholders})",
                list(todo_ids))
            if not self._conn:
                conn.commit()
            return cursor.rowcount

    def cleanup_done(self, days: int = 30) -> int:
        """清理已完成的旧待办"""
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM todos WHERE done=1 AND done_at<? AND repeat_rule='' AND parent_id IS NULL",
                (cutoff,))
            if not self._conn:
                conn.commit()
            return cursor.rowcount

    def find_reminders(self, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """查询需提醒的待办"""
        return db_query(
            "SELECT id, title, remind_at, repeat_rule FROM todos WHERE remind=1 AND done=0 "
            "AND due_date IS NOT NULL AND due_date <= ? AND due_date >= ?",
            (date_from, date_to))

    def find_overdue_repeats(self, today: str) -> List[Dict[str, Any]]:
        """查询逾期重复待办"""
        return db_query(
            "SELECT id, title, repeat_rule FROM todos WHERE repeat_rule!='' AND done=0 "
            "AND due_date<? AND parent_id IS NULL",
            (today,))

    def mark_repeat_done(self, todo_id: int) -> bool:
        """标记重复待办完成并递增计数"""
        now = datetime.now().isoformat()
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE todos SET done=1, done_at=?, updated_at=?, completed_count=completed_count+1 WHERE id=?",
                (now, now, todo_id))
            if not self._conn:
                conn.commit()
            return True

    def save_repeat(self, data: Dict[str, Any]) -> int:
        return self.save(data)

    def find_list_total(self, filters: Dict[str, Any] = None) -> int:
        conditions = []
        params = []
        filters = filters or {}

        if filters.get("parent_only"):
            conditions.append("parent_id IS NULL")

        category = filters.get("category")
        if category in ("work", "life"):
            conditions.append("category = ?")
            params.append(category)

        done = filters.get("done")
        if done is not None:
            conditions.append("done = ?")
            params.append(1 if done else 0)

        date_filter = filters.get("date_filter", "")
        today = date.today().isoformat()
        if date_filter == "today":
            conditions.append("due_date = ?")
            params.append(today)
        elif date_filter == "overdue":
            conditions.append("due_date < ? AND done = 0")
            params.append(today)
        elif date_filter == "upcoming":
            week_later = (date.today() + timedelta(days=7)).isoformat()
            conditions.append("due_date >= ? AND due_date <= ? AND done = 0")
            params.extend([today, week_later])
        elif date_filter == "this_week":
            today_dt = date.today()
            week_start = (today_dt - timedelta(days=today_dt.weekday())).isoformat()
            week_end = (today_dt + timedelta(days=6 - today_dt.weekday())).isoformat()
            conditions.append("due_date >= ? AND due_date <= ? AND done = 0")
            params.extend([week_start, week_end])

        keyword = filters.get("keyword")
        if keyword:
            conditions.append("(title LIKE ? OR description LIKE ? OR tags LIKE ?)")
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        source_type = filters.get("source_type")
        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)

        source_id = filters.get("source_id")
        if source_id is not None:
            conditions.append("source_id = ?")
            params.append(source_id)

        where = " AND ".join(conditions) if conditions else "1=1"
        row = db_query_one(f"SELECT COUNT(*) as c FROM todos WHERE {where}", tuple(params))
        return row["c"] if row else 0

    def toggle_with_subtasks(self, todo_id: int, new_done: int, done_at: str) -> bool:
        new_count_expr = "completed_count + 1" if new_done else "completed_count"
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE todos SET done=?, done_at=?, completed_count=?, "
                "updated_at=datetime('now','localtime') WHERE id=?",
                (new_done, done_at, new_count_expr, todo_id))
            if new_done:
                conn.execute(
                    "UPDATE todos SET done=1, done_at=?, updated_at=datetime('now','localtime') "
                    "WHERE parent_id=? AND done=0",
                    (done_at, todo_id))
            if not self._conn:
                conn.commit()
            return True

    def calc_reminder_at(self, due_date: str, remind: int) -> Optional[str]:
        if not remind or not due_date:
            return None
        try:
            d = datetime.strptime(due_date, "%Y-%m-%d")
            reminder_dt = d - timedelta(days=1)
            return reminder_dt.strftime("%Y-%m-%d 09:00")
        except ValueError:
            return None
