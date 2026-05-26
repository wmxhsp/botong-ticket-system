"""
博通 — 仪表盘仓储（聚合查询）
用最少的 SQL 获取仪表盘所需全部数据
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, List
from infrastructure.persistence.legacy_db import db_query, db_query_one

logger = logging.getLogger(__name__)


class SqliteDashboardRepository:
    """
    仪表盘仓储 — 聚合查询

    原 dashboard API 做 9+ 次独立 SQL 查询。
    本仓储通过 3 次 SQL 获取全部数据：
      1. 工单聚合统计
      2. 财务聚合统计
      3. 最近工单 + 最近支出
    """

    def get_dashboard(self, month: str = None) -> Dict[str, Any]:
        """
        获取仪表盘全部数据（3 次 SQL）
        
        Returns:
            {
                "stats": { "open": N, "in-progress": N, ... },
                "finance": { "monthly_income": N, "monthly_expense": N, "monthly_profit": N },
                "overdue": [...],
                "alerts": [...],
                "recent_tickets": [...],
                "recent_expenses": [...],
            }
        """
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        month_start = month + "-01"
        # 计算月末
        import calendar
        year, mon = int(month[:4]), int(month[5:7])
        month_end = f"{month}-{calendar.monthrange(year, mon)[1]}"

        # ── SQL 1: 工单统计数据（一次聚合） ──
        stats = self._get_ticket_stats(month_start, month_end)

        # ── SQL 2: 财务数据（一次聚合） ──
        finance = self._get_finance_summary(month_start, month_end)

        # ── SQL 3: 最近工单 ──
        recent_tickets = self._get_recent_tickets(limit=5)

        # ── 逾期工单 ──
        overdue = self._get_overdue(limit=10)

        # ── 最近支出 ──
        recent_expenses = self._get_recent_expenses(limit=3)

        return {
            "stats": stats,
            "finance": finance,
            "overdue": overdue,
            "recent_tickets": recent_tickets,
            "recent_expenses": recent_expenses,
            "month": month,
        }

    def _get_ticket_stats(self, month_start: str, month_end: str) -> Dict[str, Any]:
        """工单聚合统计"""
        rows = db_query(
            "SELECT status, COUNT(*) as cnt FROM tickets GROUP BY status")
        stats = {r["status"]: r["cnt"] for r in rows}

        # 本月新增工单数
        new_this_month = db_query_one(
            "SELECT COUNT(*) as cnt FROM tickets WHERE created_at >= ? AND created_at <= ?",
            (month_start, month_end + " 23:59:59"))
        stats["new_this_month"] = new_this_month["cnt"] if new_this_month else 0

        return stats

    def _get_finance_summary(self, month_start: str, month_end: str) -> Dict[str, Any]:
        """财务聚合统计"""
        # 月度收入
        income = db_query_one(
            """SELECT COALESCE(SUM(amount), 0) as total FROM income_records
               WHERE received_at >= ? AND received_at <= ?""",
            (month_start, month_end + " 23:59:59"))

        # 月度支出（仅业务）
        expense = db_query_one(
            """SELECT COALESCE(SUM(amount), 0) as total FROM expense_records
               WHERE paid_at >= ? AND paid_at <= ? AND (is_personal IS NULL OR is_personal = 0)""",
            (month_start, month_end))

        # 月度个人支出
        personal = db_query_one(
            """SELECT COALESCE(SUM(amount), 0) as total FROM expense_records
               WHERE paid_at >= ? AND paid_at <= ? AND is_personal = 1""",
            (month_start, month_end))

        monthly_income = income["total"] if income else 0
        monthly_expense = expense["total"] if expense else 0
        personal_expense = personal["total"] if personal else 0

        # 未结算统计
        unpaid = db_query_one(
            """SELECT COUNT(*) as cnt, COALESCE(SUM(COALESCE(total,0)),0) as total
               FROM tickets WHERE billing_status IN ('unpaid','pending')""")

        return {
            "monthly_income": monthly_income,
            "monthly_expense": monthly_expense,
            "personal_expense": personal_expense,
            "monthly_profit": monthly_income - monthly_expense,
            "unpaid_count": unpaid["cnt"] if unpaid else 0,
            "unpaid_total": unpaid["total"] if unpaid else 0,
        }

    def _get_recent_tickets(self, limit: int = 5) -> List[Dict[str, Any]]:
        """最近工单"""
        return db_query(
            """SELECT id, ticket_no, client, description, status,
                      COALESCE(total, 0) as amount, created_at
               FROM tickets ORDER BY id DESC LIMIT ?""", (limit,))

    def _get_overdue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """逾期工单"""
        return db_query(
            """SELECT id, ticket_no, client, status, completion_date,
                      COALESCE(total, 0) as total
               FROM tickets
               WHERE status NOT IN ('closed', 'archived')
                 AND completion_date IS NOT NULL
                 AND completion_date < date('now','localtime')
               ORDER BY completion_date ASC LIMIT ?""", (limit,))

    def _get_recent_expenses(self, limit: int = 3) -> List[Dict[str, Any]]:
        """最近支出"""
        return db_query(
            """SELECT category, amount, description
               FROM expense_records
               WHERE is_personal IS NULL OR is_personal = 0
               ORDER BY id DESC LIMIT ?""", (limit,))
