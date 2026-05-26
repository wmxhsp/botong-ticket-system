"""
博通 — 仪表盘应用服务
使用 DashboardRepository 高效获取聚合数据
"""

import logging
import calendar
from typing import Dict, Any
from datetime import datetime

from domain.events import EventBus

logger = logging.getLogger(__name__)

STATUS_NAMES = {
    "open": "待处理", "in-progress": "进行中",
    "pending-parts": "待配件", "pending-payment": "待结算",
    "closed": "已完成", "archived": "已归档",
}


class DashboardService:
    """
    仪表盘服务

    依赖注入:
        repo: SqliteDashboardRepository
        event_bus: EventBus（可选）
        ticket_service: TicketService（可选）
        finance_service: FinanceService（可选）
        inventory_service: InventoryService（可选）
        equipment_service: EquipmentService（可选）
        todo_service: TodoService（可选）
    """

    def __init__(self, repo, event_bus=None, ticket_service=None,
                 finance_service=None, inventory_service=None,
                 equipment_service=None, todo_service=None,
                 reminder_service=None):
        self._repo = repo
        self._event_bus = event_bus
        self._ticket_service = ticket_service
        self._finance_service = finance_service
        self._inventory_service = inventory_service
        self._equipment_service = equipment_service
        self._todo_service = todo_service
        self._reminder_service = reminder_service

    def _get_ticket_service(self):
        return self._ticket_service

    def _get_finance_service(self):
        return self._finance_service

    def _get_inventory_service(self):
        return self._inventory_service

    def _get_equipment_service(self):
        return self._equipment_service

    def _get_todo_service(self):
        return self._todo_service

    def get_summary(self, month: str = None) -> Dict[str, Any]:
        """获取仪表盘汇总"""
        data = self._repo.get_dashboard(month=month)

        stats = data.get("stats", {})
        open_count = (stats.get("open") or 0) + (stats.get("assigned") or 0)
        in_progress_count = stats.get("in-progress") or 0
        pending_parts = stats.get("pending-parts") or 0
        pending_pay = stats.get("pending-payment") or 0

        recent = data.get("recent_tickets", [])
        for t in recent:
            t["status_name"] = STATUS_NAMES.get(t.get("status"), t.get("status"))

        finance = data.get("finance", {})
        mi = finance.get("monthly_income", 0)
        me = finance.get("monthly_expense", 0)
        overdue_count = len(data.get("overdue", []))
        alert_count = len(data.get("alerts", []))

        parts = [
            f"{open_count} 单待处理",
            f"{in_progress_count} 单进行中",
        ]
        if pending_parts:
            parts.append(f"{pending_parts} 单待配件")
        if pending_pay:
            parts.append(f"{pending_pay} 单待结算")
        parts.append(f"本月收入 ¥{mi:.0f} 支出 ¥{me:.0f}")
        if overdue_count:
            parts.append(f"{overdue_count} 单逾期")
        if alert_count:
            parts.append(f"{alert_count} 条预警")

        return {
            "summary": "仪表盘概况：" + "、".join(parts),
            "stats": stats,
            "todo": {
                "open": open_count,
                "in_progress": in_progress_count,
                "pending_parts": pending_parts,
                "pending_payment": pending_pay,
            },
            "finance": finance,
            "overdue": data.get("overdue", []),
            "recent_tickets": recent[:5],
            "recent_expenses": data.get("recent_expenses", []),
            "month": month or datetime.now().strftime("%Y-%m"),
        }

    def build_equip_stats(self) -> Dict[str, Any]:
        equip_svc = self._get_equipment_service()
        try:
            equip_list = equip_svc.list_equipment(page=1, page_size=1000) if equip_svc else {"items": []}
            items = equip_list.get("items", equip_list) if isinstance(equip_list, dict) else equip_list
            type_dist = {}
            status_dist = {}
            for e in (items or []):
                t = e.get("type", "其他") or "其他"
                s = e.get("status", "未知") or "未知"
                type_dist[t] = type_dist.get(t, 0) + 1
                status_dist[s] = status_dist.get(s, 0) + 1
            return {
                "total": len(items or []),
                "type_distribution": [{"type": k, "cnt": v} for k, v in sorted(type_dist.items(), key=lambda x: -x[1])][:10],
                "status_distribution": [{"status": k, "cnt": v} for k, v in status_dist.items()],
            }
        except Exception:
            return {"total": 0, "type_distribution": [], "status_distribution": []}

    def build_recommendations(self) -> list:
        ticket_svc = self._get_ticket_service()
        finance_svc = self._get_finance_service()
        inventory_svc = self._get_inventory_service()
        equip_svc = self._get_equipment_service()
        todo_svc = self._get_todo_service()

        now_dt = datetime.now()
        recommendations = []

        pending_pay_count = 0
        try:
            stats = ticket_svc.get_status_stats()
            pending_pay_count = stats.get("pending-payment", 0)
        except Exception:
            pass

        if pending_pay_count > 0:
            try:
                old_unpaid = ticket_svc.list_tickets(status="pending-payment", per_page=3).get("tickets", [])
                old_unpaid = [t for t in old_unpaid if t.get("created_at") and
                              (now_dt - datetime.fromisoformat(t["created_at"])).days > 7][:3]
                if old_unpaid:
                    names = ", ".join(f"{u['client']}({u['ticket_no']})" for u in old_unpaid)
                    recommendations.append({
                        "type": "urgent", "action": "催款",
                        "title": "待结算工单超7天",
                        "description": f"{len(old_unpaid)} 单待收款超一周：{names}",
                        "suggestions": [f"确认收款 {u['ticket_no']}" for u in old_unpaid],
                    })
            except Exception:
                pass

        if hasattr(inventory_svc, "check_alerts"):
            try:
                alerts = inventory_svc.check_alerts()[:5]
                if alerts:
                    suggestions = []
                    for a in alerts[:3]:
                        s_name = a.get("product", a.get("name", "?"))
                        s_stock = a.get("stock", 0)
                        s_min = a.get("min_stock", 0)
                        suggestions.append(f"采购 {s_name}（库存 {s_stock}/{s_min}）")
                    recommendations.append({
                        "type": "warning", "action": "采购",
                        "title": "库存不足提醒",
                        "description": f"「{alerts[0].get('product', alerts[0].get('name', '?'))}」库存不足",
                        "suggestions": suggestions,
                    })
            except Exception:
                pass

        try:
            warranty = equip_svc.get_warranty_summary() if hasattr(equip_svc, "get_warranty_summary") else {}
            if isinstance(warranty, dict):
                expiring_count = warranty.get("expiring", 0)
                if expiring_count > 0:
                    recommendations.append({
                        "type": "info", "action": "维保",
                        "title": "设备维保即将到期",
                        "description": f"{expiring_count} 台设备维保将在30天内到期",
                        "suggestions": ["查看维保详情并联系客户续保"],
                    })
        except Exception:
            pass

        try:
            if todo_svc and hasattr(todo_svc, 'stats'):
                todo_stats = todo_svc.stats()
                todo_count = todo_stats.get("pending", 0) if isinstance(todo_stats, dict) else 0
            else:
                todo_count = 0
            if todo_count > 0:
                recommendations.append({
                    "type": "info", "action": "待办",
                    "title": "有待办事项未完成",
                    "description": f"还有 {todo_count} 项待办未完成",
                    "suggestions": ["查看待办并处理"],
                })
        except Exception:
            pass

        try:
            overdue = ticket_svc.get_overdue_tickets(limit=10)
            if overdue:
                recommendations.append({
                    "type": "warning", "action": "逾期",
                    "title": "工单逾期提醒",
                    "description": f"{len(overdue)} 单工单已逾期",
                    "suggestions": [f"处理 {o.get('ticket_no', '?')} {o.get('client', '')}" for o in overdue[:3]],
                })
        except Exception:
            pass

        try:
            today_data = ticket_svc.list_tickets(page=1, per_page=1)
            today_tickets_count = today_data.get("total", 0)
            if today_tickets_count == 0:
                recommendations.append({
                    "type": "tip", "action": "开始工作",
                    "title": "今天还没有新建工单",
                    "description": "是否从待处理或待办开始今天的工作？",
                    "suggestions": ["查看待处理工单", "查看待办事项"],
                })
        except Exception:
            pass

        return recommendations[:5]

    def build_legacy_dashboard(self, month: str = None) -> Dict[str, Any]:
        ticket_svc = self._get_ticket_service()
        finance_svc = self._get_finance_service()
        inventory_svc = self._get_inventory_service()
        equip_svc = self._get_equipment_service()

        stats = ticket_svc.get_status_stats()
        tickets_data = ticket_svc.list_tickets(page=1, per_page=50)
        tickets = tickets_data["tickets"] if isinstance(tickets_data, dict) else tickets_data

        todo = {
            "open": (stats.get("open") or 0) + (stats.get("assigned") or 0),
            "in_progress": stats.get("in-progress") or 0,
            "pending_parts": stats.get("pending-parts") or 0,
            "pending_payment": stats.get("pending-payment") or 0,
        }

        finance = finance_svc.get_summary() if hasattr(finance_svc, "get_summary") else {}
        if not isinstance(finance, dict):
            finance = {}
        month = month or datetime.now().strftime("%Y-%m")
        month_start = month + "-01"
        month_end = datetime.now().strftime("%Y-%m-%d") if month == datetime.now().strftime("%Y-%m") else f"{month}-{calendar.monthrange(int(month[:4]), int(month[5:7]))[1]}"
        monthly_income = finance_svc.get_monthly_income(month_start, month_end)
        monthly_expense = finance_svc.get_monthly_expense(month_start, month_end)
        finance["monthly_income"] = monthly_income
        finance["monthly_expense"] = monthly_expense
        finance["monthly_profit"] = monthly_income - monthly_expense

        alerts = []
        if hasattr(inventory_svc, "check_alerts"):
            alerts = inventory_svc.check_alerts()
        warranty = equip_svc.get_warranty_summary()

        equip_stats = {}
        try:
            equip_list = equip_svc.list_equipment(page=1, page_size=1000) if equip_svc else {"items": []}
            items = equip_list.get("items", equip_list) if isinstance(equip_list, dict) else equip_list
            type_dist = {}
            status_dist = {}
            for e in (items or []):
                t = e.get("type", "其他") or "其他"
                s = e.get("status", "未知") or "未知"
                type_dist[t] = type_dist.get(t, 0) + 1
                status_dist[s] = status_dist.get(s, 0) + 1
            equip_stats = {
                "total": len(items or []),
                "type_distribution": [{"type": k, "cnt": v} for k, v in sorted(type_dist.items(), key=lambda x: -x[1])][:10],
                "status_distribution": [{"status": k, "cnt": v} for k, v in status_dist.items()],
                "maintenance": equip_svc.get_maintenance_summary() if hasattr(equip_svc, "get_maintenance_summary") else {},
            }
        except Exception:
            equip_stats = {"total": 0, "type_distribution": [], "status_distribution": [], "maintenance": {}}

        overdue = ticket_svc.get_overdue_tickets(limit=10)

        open_count = todo.get("open", 0)
        in_progress_count = todo.get("in_progress", 0)
        pending_parts = todo.get("pending_parts", 0)
        pending_pay = todo.get("pending_payment", 0)
        total_alerts = len(alerts)
        alert_str = f"，{total_alerts} 条库存预警" if total_alerts > 0 else ""
        overdue_str = f"，{len(overdue)} 单逾期" if overdue else ""
        summary = (f"仪表盘概况：{open_count} 单待处理、{in_progress_count} 单进行中"
                   f"、{pending_parts} 单待配件、{pending_pay} 单待结算"
                   f"，本月收入 ¥{monthly_income:.0f} 支出 ¥{monthly_expense:.0f}"
                   f"{alert_str}{overdue_str}")

        return {
            "summary": summary,
            "stats": stats or {},
            "todo": todo,
            "finance": finance,
            "alerts": alerts[:5],
            "warranty": warranty,
            "equip_stats": equip_stats,
            "overdue": overdue,
            "sales_today": {"total": 0},
            "recommendations": self.build_recommendations(),
            "recent_tickets": [
                {
                    "id": t.get("id"), "ticket_no": t.get("ticket_no"),
                    "client": t.get("client"),
                    "content": (t.get("description") or "")[:50],
                    "status": t.get("status"),
                    "status_name": STATUS_NAMES.get(t.get("status"), t.get("status")),
                    "amount": t.get("total") or t.get("amount") or 0,
                    "created_at": t.get("created_at"),
                }
                for t in tickets[:5]
            ],
            "all_statuses": STATUS_NAMES,
            "recent_expenses": [
                {"category": e.get("category"), "amount": e.get("amount"),
                 "description": (e.get("description") or "")[:30]}
                for e in (finance_svc.list_expenses(limit=3) or [])
            ],
        }

    def get_daily_digest(self):
        ticket_svc = self._ticket_service
        finance_svc = self._finance_service
        inventory_svc = self._inventory_service
        equip_svc = self._equipment_service
        todo_svc = self._todo_service
        reminder_svc = self._reminder_service
        if reminder_svc is None:
            logger.warning("DashboardService: reminder_service not injected, skipping reminders")

        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        month = now.strftime("%Y-%m")
        month_start = month + "-01"

        stats = ticket_svc.get_status_stats()
        overdue = ticket_svc.get_overdue_tickets(limit=5)

        warranty = equip_svc.get_warranty_summary() if equip_svc and hasattr(equip_svc, 'get_warranty_summary') else {}
        warranty_items = warranty.get("expiring_list", []) if isinstance(warranty, dict) else []

        alerts = inventory_svc.check_alerts()[:5] if inventory_svc and hasattr(inventory_svc, 'check_alerts') else []

        todo_stats = todo_svc.stats() if todo_svc and hasattr(todo_svc, 'stats') else {}
        pending_todos = todo_stats.get("pending", 0) if isinstance(todo_stats, dict) else 0

        unread = reminder_svc.get_unread_count() if reminder_svc and hasattr(reminder_svc, 'get_unread_count') else 0

        monthly_income = finance_svc.get_monthly_income(month_start, today) if finance_svc else 0
        today_income = finance_svc.get_monthly_income(today, today) if finance_svc else 0

        open_count = stats.get("open", 0) + stats.get("assigned", 0)
        in_progress = stats.get("in-progress", 0)
        pending_payment = stats.get("pending-payment", 0)
        pending_parts = stats.get("pending-parts", 0)

        return {
            "date": today,
            "ticket_summary": {
                "open": open_count, "in_progress": in_progress,
                "pending_payment": pending_payment, "pending_parts": pending_parts,
                "overdue_count": len(overdue), "overdue": overdue,
            },
            "todo_summary": {"pending_count": pending_todos},
            "warranty": {"count": len(warranty_items), "items": warranty_items},
            "inventory_alerts": {"count": len(alerts), "items": alerts},
            "unread_notifications": unread,
            "monthly_income": round(monthly_income, 2),
            "today_income": round(today_income, 2),
            "summary": (
                f"📋 {today} 工作摘要\n"
                f"• 工单：待处理 {open_count} 单，进行中 {in_progress} 单，待结算 {pending_payment} 单\n"
                f"• 待办：待完成 {pending_todos} 项\n"
                f"• 逾期：{len(overdue)} 单工单逾期\n"
                f"• 维保：{len(warranty_items)} 台设备即将到期\n"
                f"• 库存：{len(alerts)} 种商品库存不足\n"
                f"• 通知：{unread} 条未读\n"
                f"• 收入：本月 ¥{round(monthly_income, 2)}，今日 ¥{round(today_income, 2)}"
            ),
        }
