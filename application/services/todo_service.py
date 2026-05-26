"""
博通 — 待办应用服务（新架构版）
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

from domain.events import EventBus

logger = logging.getLogger(__name__)

REPEAT_DAILY = "daily"
REPEAT_WEEKLY = "weekly"
REPEAT_MONTHLY = "monthly"
REPEAT_WEEKDAYS = "weekdays"
VALID_REPEAT_RULES = {"", REPEAT_DAILY, REPEAT_WEEKLY, REPEAT_MONTHLY, REPEAT_WEEKDAYS}


class TodoService:

    def __init__(self, repo, event_bus=None):
        self._repo = repo
        self._event_bus = event_bus

    # ===== CRUD =====

    def get(self, todo_id: int) -> Optional[Dict[str, Any]]:
        todo = self._repo.find_by_id(todo_id)
        if todo:
            todo["subtasks"] = self._repo.get_subtasks(todo_id)
            todo["progress"] = self._calc_progress(todo_id, todo.get("done", 0))
        return todo

    def list(self, category: str = "", done: Optional[int] = None,
             date_filter: str = "", keyword: str = "",
             page: int = 1, per_page: int = 50,
             source_type: str = "", source_id: int = None,
             parent_only: bool = False) -> Dict[str, Any]:
        filters = {
            "category": category,
            "done": done,
            "date_filter": date_filter,
            "keyword": keyword,
            "page": page,
            "per_page": per_page,
            "source_type": source_type,
            "source_id": source_id,
            "parent_only": parent_only,
        }
        total = self._repo.find_list_total(filters)
        items = self._repo.find_list(filters)

        if parent_only or not source_type:
            result_rows = []
            for row in items:
                row = dict(row)
                row["subtasks"] = self._repo.get_subtasks(row["id"])
                row["progress"] = self._calc_progress(row["id"], row.get("done", 0))
                result_rows.append(row)
            items = result_rows

        return {"todos": items, "total": total}

    def create(self, title: str, category: str = "work", priority: str = "M",
               due_date: str = "", due_time: str = "",
               description: str = "", tags: str = "",
               remind: bool = False, source_type: str = "",
               source_id: int = None, parent_id: int = None,
               repeat_rule: str = "", reminder_at: str = "",
               estimated_minutes: int = None) -> Optional[Dict[str, Any]]:
        if not title or not title.strip():
            return None

        if repeat_rule and repeat_rule not in VALID_REPEAT_RULES:
            repeat_rule = ""

        if not reminder_at and remind and due_date:
            reminder_at = self._repo.calc_reminder_at(due_date, 1) or ""

        todo_id = self._repo.save({
            "title": title.strip(),
            "category": category,
            "priority": priority,
            "due_date": due_date or None,
            "due_time": due_time or None,
            "description": description,
            "tags": tags,
            "remind": 1 if remind else 0,
            "source_type": source_type or None,
            "source_id": source_id or None,
            "parent_id": parent_id or None,
            "repeat_rule": repeat_rule,
            "reminder_at": reminder_at or None,
            "estimated_minutes": estimated_minutes,
        })
        return self.get(todo_id)

    def update(self, todo_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        allowed = {"title", "category", "priority", "due_date", "due_time",
                   "description", "tags", "remind", "sort_order",
                   "source_type", "source_id", "repeat_rule",
                   "estimated_minutes", "reminder_at"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return self.get(todo_id)

        if "remind" in updates or "due_date" in updates:
            todo = self._repo.find_by_id(todo_id)
            if todo:
                remind_val = kwargs.get("remind", todo.get("remind", 0))
                due_val = kwargs.get("due_date", todo.get("due_date", ""))
                if remind_val and due_val:
                    ra = self._repo.calc_reminder_at(str(due_val)[:10], 1)
                    if ra:
                        updates["reminder_at"] = ra

        self._repo.update(todo_id, updates)
        return self.get(todo_id)

    def toggle(self, todo_id: int) -> Optional[Dict[str, Any]]:
        todo = self._repo.find_by_id(todo_id)
        if not todo:
            return None
        new_done = 0 if todo.get("done") else 1
        done_at = datetime.now().strftime("%Y-%m-%d %H:%M") if new_done else None

        self._repo.toggle_with_subtasks(todo_id, new_done, done_at)

        if new_done and todo.get("repeat_rule"):
            self._generate_next_repeat(todo)

        return self.get(todo_id)

    def delete(self, todo_id: int) -> bool:
        return self._repo.delete(todo_id)

    def stats(self) -> Dict[str, Any]:
        stats = self._repo.stats()
        stats["linked_tickets"] = self._repo.count_linked_tickets()
        return stats

    # ===== 子任务 =====

    def _calc_progress(self, todo_id: int, parent_done: int) -> Dict:
        subtasks = self._repo.get_subtasks(todo_id)
        if not subtasks:
            return {"total": 0, "done": 0, "percent": 100 if parent_done else 0}
        total = len(subtasks)
        done = sum(1 for s in subtasks if s.get("done"))
        return {"total": total, "done": done, "percent": round(done / total * 100) if total else 0}

    def create_subtask(self, parent_id: int, title: str,
                       **kwargs) -> Optional[Dict[str, Any]]:
        parent = self.get(parent_id)
        if not parent:
            return None
        return self.create(
            title=title,
            category=parent.get("category", "work"),
            parent_id=parent_id,
            source_type=parent.get("source_type", ""),
            source_id=parent.get("source_id"),
            priority=kwargs.get("priority", "M"),
            due_date=kwargs.get("due_date", parent.get("due_date", "")),
            **{k: v for k, v in kwargs.items() if k in ("description", "tags")}
        )

    def toggle_subtask(self, subtask_id: int) -> Optional[Dict[str, Any]]:
        result = self.toggle(subtask_id)
        if result and result.get("parent_id"):
            parent = self.get(result["parent_id"])
            if parent:
                subtasks = self._repo.get_subtasks(result["parent_id"])
                if subtasks:
                    all_done = all(s.get("done") for s in subtasks)
                    if all_done and not parent["done"]:
                        self.toggle(result["parent_id"])
        return result

    # ===== 工单关联待办 =====

    _TICKET_TODO_DEFAULTS = {
        "process": {
            "priority": "M",
            "tags": "工单,自动生成,处理",
            "remind": 1,
            "description_template": "请处理工单，完成服务任务",
        },
        "follow_up": {
            "priority": "M",
            "tags": "工单,自动生成,跟进",
            "remind": 1,
            "description_template": "工单已开始处理，请跟进服务进度",
        },
        "purchase_parts": {
            "priority": "H",
            "tags": "工单,自动生成,采购配件",
            "remind": 1,
            "description_template": "工单需要采购配件，请尽快处理",
        },
        "confirm_payment": {
            "priority": "H",
            "tags": "工单,自动生成,收款",
            "remind": 1,
            "description_template": "工单已完成，等待确认收款",
        },
        "follow_up_visit": {
            "priority": "M",
            "tags": "工单,自动生成,回访",
            "remind": 1,
            "description_template": "工单已关闭，请安排客户回访",
        },
    }

    def create_from_ticket(self, ticket_id: int, todo_type: str,
                           title: str, **kwargs) -> Optional[Dict[str, Any]]:
        defaults = self._TICKET_TODO_DEFAULTS.get(todo_type, {})
        return self.create(
            title=title,
            category="work",
            priority=kwargs.get("priority", defaults.get("priority", "M")),
            due_date=kwargs.get("due_date", ""),
            description=kwargs.get("description", defaults.get("description_template", "")),
            source_type="ticket",
            source_id=ticket_id,
            tags=kwargs.get("tags", defaults.get("tags", "工单,自动生成")),
            remind=kwargs.get("remind", defaults.get("remind", 1)),
            estimated_minutes=kwargs.get("estimated_minutes"),
        )

    def create_from_finance(self, client: str, amount: float,
                            title: str, source_id: int = None, **kwargs) -> Optional[Dict[str, Any]]:
        return self.create(
            title=title,
            category="work",
            priority=kwargs.get("priority", "H"),
            due_date=kwargs.get("due_date", ""),
            description=f"客户: {client}, 金额: ¥{amount:.2f}",
            source_type="finance",
            source_id=source_id,
            tags="财务,自动生成,催收",
            remind=1,
        )

    # ===== 批量操作 =====

    def batch_toggle(self, todo_ids: list, done: int = 1) -> dict:
        count = self._repo.batch_toggle(todo_ids, done)
        return {"updated": count}

    def batch_delete(self, todo_ids: list) -> dict:
        if not todo_ids:
            return {"deleted": 0}
        count = self._repo.batch_delete(todo_ids)
        return {"deleted": count}

    def cleanup_done(self, days: int = 30) -> int:
        return self._repo.cleanup_done(days)

    # ===== 提醒检查 =====

    def check_reminders(self) -> list:
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d")
        yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        reminders = self._repo.find_reminders(now_str, yesterday_str)
        self._generate_overdue_repeats()
        return reminders or []

    def _generate_overdue_repeats(self):
        today = date.today().isoformat()
        overdue_repeat = self._repo.find_overdue_repeats(today)
        for todo in overdue_repeat:
            self._repo.mark_repeat_done(todo["id"])
            self._generate_next_repeat(dict(todo))

    def _generate_next_repeat(self, todo: dict):
        rule = todo.get("repeat_rule", "")
        if not rule:
            return
        due = todo.get("due_date", "")
        if not due:
            return
        try:
            d = datetime.strptime(str(due)[:10], "%Y-%m-%d")
        except ValueError:
            return

        if rule == REPEAT_DAILY:
            next_date = (d + timedelta(days=1)).strftime("%Y-%m-%d")
        elif rule == REPEAT_WEEKLY:
            next_date = (d + timedelta(weeks=1)).strftime("%Y-%m-%d")
        elif rule == REPEAT_MONTHLY:
            month = d.month + 1
            year = d.year
            if month > 12:
                month = 1
                year += 1
            try:
                next_date = d.replace(year=year, month=month).strftime("%Y-%m-%d")
            except ValueError:
                from calendar import monthrange
                last_day = monthrange(year, month)[1]
                next_date = d.replace(year=year, month=month, day=last_day).strftime("%Y-%m-%d")
        elif rule == REPEAT_WEEKDAYS:
            next_d = d + timedelta(days=1)
            while next_d.weekday() >= 5:
                next_d += timedelta(days=1)
            next_date = next_d.strftime("%Y-%m-%d")
        else:
            return

        self._repo.save_repeat({
            "title": todo.get("title"),
            "category": todo.get("category", "work"),
            "priority": todo.get("priority", "M"),
            "due_date": next_date,
            "due_time": todo.get("due_time", ""),
            "description": todo.get("description", ""),
            "tags": todo.get("tags", ""),
            "remind": todo.get("remind", 0),
            "source_type": todo.get("source_type", ""),
            "source_id": todo.get("source_id"),
            "repeat_rule": rule,
            "estimated_minutes": todo.get("estimated_minutes"),
        })
