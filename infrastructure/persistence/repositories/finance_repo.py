"""
博通 (Botong) — 财务仓储 SQLite 实现

支持外部 Connection 注入（conn 参数），用于 UnitOfWork 事务内共享连接。
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager

from infrastructure.persistence.legacy_db import db_query, db_query_one, get_db, log_audit

logger = logging.getLogger(__name__)


class SqliteFinanceRepository:
    """财务仓储 - SQLite 实现，支持连接注入"""

    def __init__(self, conn=None):
        """conn: 可选外部连接，用于 UnitOfWork 事务内共享"""
        self._conn = conn

    @contextmanager
    def _ensure_conn(self):
        if self._conn:
            yield self._conn
        else:
            with get_db() as conn:
                yield conn

    # ===== 收入 =====

    def record_income(self, data: Dict[str, Any]) -> int:
        """记录收入"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO income_records
                   (source_type, source_id, client, amount, method, description, received_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))""",
                (data.get("source_type", ""), data.get("source_id"),
                 data.get("client", ""), data.get("amount", 0),
                 data.get("method", "微信"), data.get("description", "")))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def get_income(self, income_id: int) -> Optional[Dict[str, Any]]:
        """获取收入记录"""
        return db_query_one("SELECT * FROM income_records WHERE id = ?", (income_id,))

    def list_income(self, source_type: str = None, source_id: int = None,
                    client: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取收入列表"""
        conditions = []
        params = []
        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)
        if source_id is not None:
            conditions.append("source_id = ?")
            params.append(source_id)
        if client:
            conditions.append("client = ?")
            params.append(client)
        where = " AND ".join(conditions) if conditions else "1=1"
        return db_query(
            f"SELECT * FROM income_records WHERE {where} ORDER BY id DESC LIMIT ?",
            params + [limit])

    def get_monthly_income(self, start: str, end: str) -> float:
        """月度收入汇总"""
        result = db_query_one(
            """SELECT COALESCE(SUM(amount), 0) as total FROM income_records
               WHERE received_at >= ? AND received_at <= ?""", (start, end))
        return result["total"] if result else 0.0

    def get_income_by_client(self, start: str, end: str) -> List[Dict[str, Any]]:
        """按客户汇总收入"""
        return db_query(
            """SELECT client, COALESCE(SUM(amount), 0) as total,
                      COUNT(*) as count
               FROM income_records
               WHERE received_at >= ? AND received_at <= ?
               GROUP BY client ORDER BY total DESC""", (start, end))

    def get_income_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """最近收入记录"""
        return db_query(
            "SELECT * FROM income_records ORDER BY id DESC LIMIT ?", (limit,))

    # ===== 支出 =====

    def record_expense(self, data: Dict[str, Any]) -> int:
        """记录支出"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO expense_records
                   (category, vendor, description, amount, paid_at,
                    payment_type, related_ticket_id, is_personal, is_recurring)
                   VALUES (?, ?, ?, ?, ?,
                           ?, ?, ?, ?)""",
                (data.get("category", "其他"), data.get("vendor", ""),
                 data.get("description", ""), data.get("amount", 0),
                 data.get("paid_at", datetime.now().strftime("%Y-%m-%d")),
                 data.get("payment_type", ""),
                 data.get("related_ticket_id"),
                 data.get("is_personal", 0), data.get("is_recurring", 0)))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def get_expense(self, exp_id: int) -> Optional[Dict[str, Any]]:
        """获取支出记录"""
        return db_query_one("SELECT * FROM expense_records WHERE id = ?", (exp_id,))

    def list_expenses(self, category: str = None, limit: int = 100,
                      personal: bool = False) -> List[Dict[str, Any]]:
        """获取支出列表"""
        conditions = ["is_personal = ?"]
        params = [1 if personal else 0]
        if category:
            conditions.append("category = ?")
            params.append(category)
        where = " AND ".join(conditions)
        return db_query(
            f"SELECT * FROM expense_records WHERE {where} ORDER BY id DESC LIMIT ?",
            params + [limit])

    def get_monthly_expense(self, start: str, end: str,
                            personal: bool = False) -> float:
        """月度支出汇总"""
        result = db_query_one(
            """SELECT COALESCE(SUM(amount), 0) as total FROM expense_records
               WHERE paid_at >= ? AND paid_at <= ? AND is_personal = ?""",
            (start, end, 1 if personal else 0))
        return result["total"] if result else 0.0

    def get_expense_by_category(self, start: str, end: str,
                                personal: bool = False) -> List[Dict[str, Any]]:
        """按分类汇总支出"""
        return db_query(
            """SELECT category, COALESCE(SUM(amount), 0) as total,
                      COUNT(*) as count
               FROM expense_records
               WHERE paid_at >= ? AND paid_at <= ? AND is_personal = ?
               GROUP BY category ORDER BY total DESC""",
            (start, end, 1 if personal else 0))

    def update_expense(self, exp_id: int, data: Dict[str, Any]) -> bool:
        """更新支出"""
        allowed = ["category", "vendor", "description", "amount",
                    "paid_at", "payment_type", "related_ticket_id"]
        updates = []
        params = []
        for key, value in data.items():
            if key in allowed:
                updates.append(f"{key} = ?")
                params.append(value)
        if not updates:
            return False
        params.append(exp_id)
        with self._ensure_conn() as conn:
            conn.execute(f"UPDATE expense_records SET {', '.join(updates)} WHERE id = ?",
                         tuple(params))
            if not self._conn:
                conn.commit()
            return True

    def delete_expense(self, exp_id: int) -> bool:
        """删除支出"""
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM expense_records WHERE id = ?", (exp_id,))
            if not self._conn:
                conn.commit()
            return True

    # ===== 应收款 =====

    def get_unpaid_tickets(self) -> List[Dict[str, Any]]:
        """获取未结算工单"""
        return db_query(
            """SELECT id, ticket_no, client, total, billing_status,
                      created_at, completion_date
               FROM tickets
               WHERE billing_status IN ('unpaid', 'pending')
               ORDER BY created_at DESC""")

    def get_overdue_receivables(self) -> List[Dict[str, Any]]:
        """获取逾期应收款原始数据（账龄计算由Service层完成）"""
        return db_query(
            """SELECT i.*, t.ticket_no, t.status,
                      COALESCE(c.payment_terms, 30) as payment_terms
               FROM income_records i
               LEFT JOIN tickets t ON i.source_id = t.id AND i.source_type = 'ticket'
               LEFT JOIN clients c ON i.client = c.name
               WHERE i.method IN ('pending', 'unpaid')
               ORDER BY i.created_at""")

    def get_client_aging(self, client: str) -> List[Dict[str, Any]]:
        """获取客户欠款原始数据（账龄分档由Service层完成）"""
        return db_query(
            """SELECT i.*, t.ticket_no, t.created_at as ticket_created
               FROM income_records i
               LEFT JOIN tickets t ON i.source_id = t.id AND i.source_type = 'ticket'
               WHERE i.client = ? AND i.method IN ('pending', 'unpaid')
               ORDER BY i.created_at""", (client,))

    # ===== 统计 =====

    def get_monthly_data(self, months: int = 6) -> List[Dict[str, Any]]:
        """月度收入/支出趋势"""
        return db_query(f"""
            SELECT substr(received_at, 1, 7) as month,
                   COALESCE(SUM(amount), 0) as income
            FROM income_records
            WHERE received_at >= date('now', 'localtime', '-{months} months')
            GROUP BY month ORDER BY month
        """)

    def get_ticket_profit(self, month: str = None) -> List[Dict[str, Any]]:
        """工单利润原始数据（利润率计算由Service层完成）"""
        condition = ""
        params = []
        if month:
            condition = "WHERE substr(t.closed_at, 1, 7) = ?"
            params.append(month)
        return db_query(f"""
            SELECT t.id, t.ticket_no, t.client,
                   t.total as income,
                   COALESCE(m.material_cost, 0) as material_cost,
                   COALESCE(l.labor_cost, 0) as labor_cost,
                   COALESCE(e.external_cost, 0) as external_cost
            FROM tickets t
            LEFT JOIN (SELECT ticket_id, SUM(total_cost) as material_cost
                       FROM materials GROUP BY ticket_id) m ON t.id = m.ticket_id
            LEFT JOIN (SELECT related_ticket_id, SUM(amount) as labor_cost
                       FROM expense_records WHERE category = '人工'
                       GROUP BY related_ticket_id) l ON t.id = l.related_ticket_id
            LEFT JOIN (SELECT related_ticket_id, SUM(amount) as external_cost
                       FROM expense_records WHERE category NOT IN ('人工', '')
                       GROUP BY related_ticket_id) e ON t.id = e.related_ticket_id
            {condition}
            ORDER BY t.id DESC
        """, params)

    def get_finance_dashboard_data(self, start: str, end: str) -> Dict[str, Any]:
        """获取看板原始数据（聚合由Service层完成）"""
        monthly_income = self.get_monthly_income(start, end)
        monthly_expense = self.get_monthly_expense(start, end, personal=False)
        personal_expense = self.get_monthly_expense(start, end, personal=True)
        return {
            "monthly_income": monthly_income,
            "monthly_expense": monthly_expense,
            "personal_expense": personal_expense,
        }

    # ===== 收入扩展查询 =====

    def has_income_record(self, source_type: str, source_id: int) -> bool:
        """检查是否已有收入记录"""
        row = db_query_one(
            "SELECT COUNT(*) as c FROM income_records WHERE source_type=? AND source_id=?",
            (source_type, source_id))
        return (row["c"] if row else 0) > 0

    def get_client_revenue(self, client: str) -> float:
        """获取客户总收入"""
        row = db_query_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM income_records WHERE client=?",
            (client,))
        return float(row["total"]) if row else 0.0

    def get_client_income_records(self, client: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取客户收入记录"""
        return db_query(
            "SELECT * FROM income_records WHERE client=? ORDER BY id DESC LIMIT ?",
            (client, limit))

    def get_income_records_range(self, start: str, end: str) -> List[Dict[str, Any]]:
        """按日期范围查询收入记录"""
        return db_query(
            "SELECT * FROM income_records WHERE received_at >= ? AND received_at <= ? ORDER BY id DESC",
            (start, end))

    def get_batch_ticket_income(self, ticket_ids: List[int]) -> Dict[int, float]:
        """批量获取工单收入汇总"""
        if not ticket_ids:
            return {}
        placeholders = ",".join("?" * len(ticket_ids))
        rows = db_query(
            f"SELECT source_id, COALESCE(SUM(amount), 0) as total FROM income_records "
            f"WHERE source_type='ticket' AND source_id IN ({placeholders}) GROUP BY source_id",
            tuple(ticket_ids))
        return {r["source_id"]: float(r["total"]) for r in rows}

    def get_ticket_income_total(self, ticket_id: int) -> float:
        """获取工单收入总额"""
        row = db_query_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM income_records "
            "WHERE source_type='ticket' AND source_id=?",
            (ticket_id,))
        return float(row["total"]) if row else 0.0

    def get_ticket_income_records(self, ticket_id: int) -> List[Dict[str, Any]]:
        """获取工单收入记录明细"""
        return db_query(
            "SELECT * FROM income_records WHERE source_type='ticket' AND source_id=? ORDER BY id",
            (ticket_id,))

    def get_payment_history(self, ticket_id: int) -> List[Dict[str, Any]]:
        """获取工单收款历史"""
        return db_query(
            """SELECT ir.*, t.ticket_no FROM income_records ir
               LEFT JOIN tickets t ON ir.source_id = t.id AND ir.source_type='ticket'
               WHERE ir.source_type='ticket' AND ir.source_id=?
               ORDER BY ir.id DESC""",
            (ticket_id,))

    def get_top_client(self, start: str = None, end: str = None) -> Optional[Dict[str, Any]]:
        """获取收入最高的客户"""
        if start and end:
            return db_query_one(
                """SELECT client, COALESCE(SUM(amount), 0) as total FROM income_records
                   WHERE received_at >= ? AND received_at <= ? GROUP BY client
                   ORDER BY total DESC LIMIT 1""",
                (start, end))
        return db_query_one(
            "SELECT client, COALESCE(SUM(amount), 0) as total FROM income_records "
            "GROUP BY client ORDER BY total DESC LIMIT 1")

    def get_revenue_stats(self, start: str, end: str) -> Dict[str, Any]:
        """获取收入统计"""
        row = db_query_one(
            """SELECT COALESCE(SUM(amount), 0) as total,
                      COUNT(*) as count,
                      COALESCE(AVG(amount), 0) as avg_amount
               FROM income_records WHERE received_at >= ? AND received_at <= ?""",
            (start, end))
        return row if row else {"total": 0, "count": 0, "avg_amount": 0}

    def get_revenue_by_client(self, start: str, end: str) -> List[Dict[str, Any]]:
        """按客户汇总收入"""
        return db_query(
            """SELECT client, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
               FROM income_records WHERE received_at >= ? AND received_at <= ?
               GROUP BY client ORDER BY total DESC""",
            (start, end))

    def record_ticket_income(self, ticket_id: int, client: str, amount: float,
                             method: str = "微信", description: str = "") -> int:
        """记录工单收入"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO income_records
                   (source_type, source_id, client, amount, method, description, received_at)
                   VALUES ('ticket', ?, ?, ?, ?, ?, datetime('now','localtime'))""",
                (ticket_id, client, amount, method, description))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def record_quick_income(self, client: str, amount: float, method: str = "微信",
                            description: str = "") -> int:
        """记录快速收入"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO income_records
                   (source_type, source_id, client, amount, method, description, received_at)
                   VALUES ('quick', NULL, ?, ?, ?, ?, datetime('now','localtime'))""",
                (client, amount, method, description))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def record_agreement_income(self, agreement_id: int, client: str, amount: float,
                                method: str = "微信", description: str = "") -> int:
        """记录协议收款"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO income_records
                   (source_type, source_id, client, amount, method, description, received_at)
                   VALUES ('agreement', ?, ?, ?, ?, ?, datetime('now','localtime'))""",
                (agreement_id, client, amount, method, description))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def generate_invoice_record(self, ticket_id: int, client: str, amount: float,
                                tax_amount: float, method: str = "pending",
                                description: str = "") -> int:
        """生成结算单收入记录"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO income_records
                   (source_type, source_id, client, amount, method, description, received_at)
                   VALUES ('ticket', ?, ?, ?, ?, ?, datetime('now','localtime'))""",
                (ticket_id, client, amount, method, description))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def find_income_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """查询收入记录"""
        return db_query_one("SELECT * FROM income_records WHERE id = ?", (record_id,))

    def list_pending_invoices(self) -> List[Dict[str, Any]]:
        """获取待结算发票列表"""
        return db_query(
            """SELECT ir.*, t.ticket_no, t.status, t.total as ticket_total,
                      COALESCE(c.payment_terms, 30) as payment_terms
               FROM income_records ir
               LEFT JOIN tickets t ON ir.source_id = t.id AND ir.source_type = 'ticket'
               LEFT JOIN clients c ON ir.client = c.name
               WHERE ir.method IN ('pending', 'unpaid')
               ORDER BY ir.created_at""")

    # ===== 支出扩展查询 =====

    def get_expense_ticket_id(self, exp_id: int) -> Optional[int]:
        """获取支出记录关联的工单ID"""
        row = db_query_one(
            "SELECT related_ticket_id, category FROM expense_records WHERE id=?",
            (exp_id,))
        return row

    def get_expense_records_range(self, start: str, end: str,
                                  personal: bool = False) -> List[Dict[str, Any]]:
        """按日期范围查询支出记录"""
        return db_query(
            """SELECT * FROM expense_records
               WHERE paid_at >= ? AND paid_at <= ? AND is_personal = ?
               ORDER BY id DESC""",
            (start, end, 1 if personal else 0))

    def get_batch_ticket_expense(self, ticket_ids: List[int]) -> Dict[int, float]:
        """批量获取工单支出汇总"""
        if not ticket_ids:
            return {}
        placeholders = ",".join("?" * len(ticket_ids))
        rows = db_query(
            f"SELECT related_ticket_id, COALESCE(SUM(amount), 0) as total FROM expense_records "
            f"WHERE related_ticket_id IN ({placeholders}) GROUP BY related_ticket_id",
            tuple(ticket_ids))
        return {r["related_ticket_id"]: float(r["total"]) for r in rows}

    def get_ticket_expense_total(self, ticket_id: int) -> float:
        """获取工单支出总额"""
        row = db_query_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expense_records WHERE related_ticket_id=?",
            (ticket_id,))
        return float(row["total"]) if row else 0.0

    def get_ticket_expense_detail(self, ticket_id: int) -> List[Dict[str, Any]]:
        """获取工单支出明细（按分类汇总）"""
        return db_query(
            "SELECT category, COALESCE(SUM(amount), 0) as total FROM expense_records "
            "WHERE related_ticket_id=? GROUP BY category",
            (ticket_id,))

    def get_top_expense_category(self, start: str = None, end: str = None) -> Optional[Dict[str, Any]]:
        """获取支出最高的分类"""
        if start and end:
            return db_query_one(
                """SELECT category, COALESCE(SUM(amount), 0) as total FROM expense_records
                   WHERE paid_at >= ? AND paid_at <= ? AND is_personal=0
                   GROUP BY category ORDER BY total DESC LIMIT 1""",
                (start, end))
        return db_query_one(
            "SELECT category, COALESCE(SUM(amount), 0) as total FROM expense_records "
            "WHERE is_personal=0 GROUP BY category ORDER BY total DESC LIMIT 1")

    def get_ticket_labor_cost(self, ticket_id: int) -> float:
        """获取工单人工成本"""
        row = db_query_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expense_records "
            "WHERE related_ticket_id=? AND category='人工'",
            (ticket_id,))
        return float(row["total"]) if row else 0.0

    def get_ticket_external_cost(self, ticket_id: int) -> float:
        """获取工单外部成本"""
        row = db_query_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expense_records "
            "WHERE related_ticket_id=? AND category NOT IN ('人工', '')",
            (ticket_id,))
        return float(row["total"]) if row else 0.0

    def get_ticket_paid_total(self, ticket_id: int) -> float:
        """获取工单已付金额"""
        row = db_query_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM income_records "
            "WHERE source_type='ticket' AND source_id=? AND method NOT IN ('pending','unpaid')",
            (ticket_id,))
        return float(row["total"]) if row else 0.0

    # ===== 支出分类 =====

    def list_expense_categories(self) -> List[Dict[str, Any]]:
        """获取所有支出分类"""
        return db_query("SELECT * FROM expense_categories ORDER BY name")

    def create_expense_category(self, name: str, budget: float = 0) -> int:
        """创建支出分类"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO expense_categories (name, budget_amount) VALUES (?, ?)",
                (name, budget))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def get_expense_category(self, cat_id: int) -> Optional[Dict[str, Any]]:
        """获取支出分类"""
        return db_query_one("SELECT * FROM expense_categories WHERE id=?", (cat_id,))

    def delete_expense_category(self, cat_id: int) -> bool:
        """删除支出分类"""
        with self._ensure_conn() as conn:
            cursor = conn.execute("DELETE FROM expense_categories WHERE id=?", (cat_id,))
            if not self._conn:
                conn.commit()
            return cursor.rowcount > 0

    def update_expense_category(self, cat_id: int, name: str) -> bool:
        """更新支出分类名称"""
        with self._ensure_conn() as conn:
            conn.execute("UPDATE expense_categories SET name = ? WHERE id = ?", (name, cat_id))
            if not self._conn:
                conn.commit()
            return True

    def count_expenses_by_category(self, category: str) -> int:
        row = db_query_one("SELECT COUNT(*) as cnt FROM expense_records WHERE category=?", [category])
        return row["cnt"] if row else 0

    # ===== 个人支出 =====

    def list_personal_expenses(self, month: str = None, category: str = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """获取个人支出列表"""
        conditions = ["is_personal = 1"]
        params = []
        if month:
            conditions.append("substr(paid_at, 1, 7) = ?")
            params.append(month)
        if category:
            conditions.append("category = ?")
            params.append(category)
        where = " AND ".join(conditions)
        return db_query(
            f"SELECT * FROM expense_records WHERE {where} ORDER BY id DESC LIMIT ?",
            params + [limit])

    def add_personal_expense(self, data: Dict[str, Any]) -> int:
        """添加个人支出"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO expense_records
                   (category, vendor, description, amount, paid_at,
                    payment_type, related_ticket_id, is_personal, is_recurring)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (data.get("category", "其他"), data.get("vendor", ""),
                 data.get("description", ""), data.get("amount", 0),
                 data.get("paid_at", datetime.now().strftime("%Y-%m-%d")),
                 data.get("payment_type", ""), data.get("related_ticket_id"),
                 data.get("is_recurring", 0)))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def get_personal_month_summary(self, month: str) -> Dict[str, Any]:
        """获取个人月度支出汇总"""
        by_category = db_query(
            """SELECT category, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
               FROM expense_records WHERE is_personal=1 AND substr(paid_at,1,7)=?
               GROUP BY category ORDER BY total DESC""",
            (month,))

        budgets = db_query(
            "SELECT category, budget_amount FROM expense_budgets WHERE month=?",
            (month,))

        budget_total_row = db_query_one(
            "SELECT COALESCE(SUM(budget_amount), 0) as total FROM expense_budgets WHERE month=?",
            (month,))
        budget_total = float(budget_total_row["total"]) if budget_total_row else 0.0

        by_payment = db_query(
            """SELECT payment_type, COALESCE(SUM(amount), 0) as total
               FROM expense_records WHERE is_personal=1 AND substr(paid_at,1,7)=?
               GROUP BY payment_type""",
            (month,))

        daily = db_query(
            """SELECT paid_at, COALESCE(SUM(amount), 0) as total
               FROM expense_records WHERE is_personal=1 AND substr(paid_at,1,7)=?
               GROUP BY paid_at ORDER BY paid_at""",
            (month,))

        return {
            "by_category": by_category,
            "budgets": budgets,
            "budget_total": budget_total,
            "by_payment_type": by_payment,
            "daily_trend": daily,
        }

    def set_personal_budget(self, month: str, category: str, amount: float) -> bool:
        """设置个人预算"""
        with self._ensure_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO expense_budgets (month, category, budget_amount) VALUES (?, ?, ?)",
                (month, category, amount))
            if not self._conn:
                conn.commit()
            return True

    def get_recurring_expenses(self) -> List[Dict[str, Any]]:
        """获取循环支出"""
        return db_query(
            "SELECT * FROM expense_records WHERE is_personal=1 AND is_recurring=1 ORDER BY id")

    def check_recurring_exists(self, category: str, month: str) -> bool:
        """检查循环支出是否已存在"""
        row = db_query_one(
            "SELECT COUNT(*) as c FROM expense_records "
            "WHERE is_personal=1 AND is_recurring=1 AND category=? AND substr(paid_at,1,7)=?",
            (category, month))
        return (row["c"] if row else 0) > 0

    # ===== 协议 =====

    def get_agreement(self, agreement_id: int) -> Optional[Dict[str, Any]]:
        """获取服务协议"""
        return db_query_one("SELECT * FROM service_agreements WHERE id=?", (agreement_id,))

    def update_agreement_payment(self, agreement_id: int, paid_amount: float,
                                 paid_at: str) -> bool:
        """更新协议付款信息"""
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE service_agreements SET paid_amount=?, paid_at=? WHERE id=?",
                (paid_amount, paid_at, agreement_id))
            if not self._conn:
                conn.commit()
            return True

    def list_active_agreements(self) -> List[Dict[str, Any]]:
        """获取活跃服务协议"""
        return db_query(
            "SELECT * FROM service_agreements WHERE status='active' ORDER BY id")

    # ===== 看板扩展 =====

    def get_dashboard_summary(self, start: str, end: str) -> Dict[str, Any]:
        """获取看板汇总数据"""
        row = db_query_one(
            """SELECT
                (SELECT COALESCE(SUM(amount), 0) FROM income_records
                 WHERE received_at >= ? AND received_at <= ?) as income,
                (SELECT COALESCE(SUM(amount), 0) FROM expense_records
                 WHERE paid_at >= ? AND paid_at <= ? AND is_personal=0) as expense,
                (SELECT COUNT(*) FROM tickets
                 WHERE created_at >= ? AND created_at <= ?) as ticket_count,
                (SELECT COUNT(DISTINCT client) FROM income_records
                 WHERE received_at >= ? AND received_at <= ?) as client_count""",
            (start, end, start, end, start, end, start, end))
        return row if row else {"income": 0, "expense": 0, "ticket_count": 0, "client_count": 0}

    def get_top_expense_categories(self, start: str, end: str,
                                   limit: int = 5) -> List[Dict[str, Any]]:
        """获取TOP支出分类"""
        return db_query(
            """SELECT category, COALESCE(SUM(amount), 0) as total FROM expense_records
               WHERE paid_at >= ? AND paid_at <= ? AND is_personal=0
               GROUP BY category ORDER BY total DESC LIMIT ?""",
            (start, end, limit))

    def get_top_income_clients(self, start: str, end: str,
                               limit: int = 5) -> List[Dict[str, Any]]:
        """获取TOP收入客户"""
        return db_query(
            """SELECT client, COALESCE(SUM(amount), 0) as total FROM income_records
               WHERE received_at >= ? AND received_at <= ?
               GROUP BY client ORDER BY total DESC LIMIT ?""",
            (start, end, limit))

    def get_client_profitability(self, client: str) -> float:
        """获取客户支出总额（用于利润计算）"""
        row = db_query_one(
            """SELECT COALESCE(SUM(e.amount), 0) as total
               FROM expense_records e
               LEFT JOIN tickets t ON e.related_ticket_id = t.id
               WHERE t.client = ?""",
            (client,))
        return float(row["total"]) if row else 0.0

    def get_unpaid_sales_count(self) -> List[Dict[str, Any]]:
        """获取未结算销售记录统计"""
        return db_query(
            "SELECT COUNT(*) as c, COALESCE(SUM(COALESCE(total_amount,0)),0) as t "
            "FROM sales_records WHERE status = 'unpaid'")

    def get_monthly_ticket_stats(self, start: str, end: str) -> Dict[str, Any]:
        """获取月度工单统计"""
        result = db_query(
            "SELECT COUNT(*) as c, COUNT(DISTINCT client) as clients "
            "FROM tickets WHERE created_at >= ? AND created_at <= ?",
            (start, end))
        return result[0] if result else {"c": 0, "clients": 0}

    def get_sales_report(self, start: str, end: str) -> List[Dict[str, Any]]:
        """获取销售报表"""
        return db_query(
            """SELECT s.*, g.name as goods_name, g.sku as goods_sku,
                      gc.name as category_name
               FROM sales_records s
               LEFT JOIN goods g ON s.product_id = g.id
               LEFT JOIN goods_categories gc ON g.category_id = gc.id
               WHERE s.created_at >= ? AND s.created_at <= ?
                 AND s.status = 'paid'
               ORDER BY s.created_at DESC""",
            (start, end))

    def get_due_maintenance_plans(self, today: str) -> List[Dict[str, Any]]:
        return db_query(
            "SELECT p.*, sa.client as agreement_client "
            "FROM inspection_plans p "
            "LEFT JOIN service_agreements sa ON p.agreement_id = sa.id "
            "WHERE p.status = 'active' AND p.next_execution = ?",
            (today,))

    def record_inspection(self, plan_id: int, ticket_id: int, executed_at: str,
                          result: str = '待执行', notes: str = '') -> int:
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO inspection_records (plan_id, ticket_id, executed_at, result, notes) "
                "VALUES (?, ?, ?, ?, ?)",
                (plan_id, ticket_id, executed_at, result, notes))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def update_inspection_plan_next_execution(self, plan_id: int, next_execution: str) -> bool:
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE inspection_plans SET next_execution = ?, updated_at = ? WHERE id = ?",
                (next_execution, datetime.now().isoformat(), plan_id))
            if not self._conn:
                conn.commit()
            return True

    def _query_client_payment_terms(self, client_name: str) -> Optional[int]:
        row = db_query_one("SELECT payment_terms FROM clients WHERE name = ?", (client_name,))
        return row["payment_terms"] if row else None

    def get_receivables(self, client: str = None) -> List[Dict[str, Any]]:
        ticket_sql = """
            SELECT t.id as source_id, 'ticket' as source_type,
                   t.client, t.ticket_no as ref_no,
                   COALESCE(t.total, 0) as amount,
                   t.created_at, t.billing_status
            FROM tickets t
            WHERE t.billing_status IN ('unpaid', 'pending')
        """
        params = []
        if client:
            ticket_sql += " AND t.client = ?"
            params.append(client)

        sales_sql = """
            SELECT s.id as source_id, 'sale' as source_type,
                   s.client, s.product_name as ref_no,
                   COALESCE(s.total_amount, 0) as amount,
                   s.created_at, s.status as billing_status
            FROM sales_records s
            WHERE s.status = 'unpaid'
        """
        if client:
            sales_sql += " AND s.client = ?"
            params.append(client)

        return db_query(f"{ticket_sql} UNION ALL {sales_sql} ORDER BY created_at", tuple(params))

    def get_client_opening_balance(self, client: str, before: str) -> float:
        row = db_query_one("""
            SELECT
                (SELECT COALESCE(SUM(amount),0) FROM income_records WHERE client=? AND received_at < ?) -
                (SELECT COALESCE(SUM(amount),0) FROM expense_records WHERE related_ticket_id IN
                    (SELECT id FROM tickets WHERE client=?) AND paid_at < ?) as balance
        """, (client, before, client, before))
        return float(row["balance"] or 0) if row else 0.0

    def get_client_income_in_range(self, client: str, start: str, end: str) -> List[Dict[str, Any]]:
        return db_query("""
            SELECT 'income' as type, id, source_type, source_id, amount,
                   payment_method, received_at as date, description
            FROM income_records
            WHERE client = ? AND received_at >= ? AND received_at <= ?
            ORDER BY received_at
        """, (client, start, end))

    def get_client_expense_in_range(self, client: str, start: str, end: str) -> List[Dict[str, Any]]:
        return db_query("""
            SELECT 'expense' as type, e.id, e.category as source_type, e.related_ticket_id as source_id,
                   e.amount, e.category as payment_method, e.paid_at as date, e.description
            FROM expense_records e
            JOIN tickets t ON e.related_ticket_id = t.id
            WHERE t.client = ? AND e.paid_at >= ? AND e.paid_at <= ?
            ORDER BY e.paid_at
        """, (client, start, end))

    def get_client_unpaid_tickets(self, client: str) -> List[Dict[str, Any]]:
        return db_query("""
            SELECT id as source_id, ticket_no as ref_no, COALESCE(total,0) as amount, created_at as date,
                   '待收款' as payment_method, description
            FROM tickets
            WHERE client = ? AND billing_status IN ('unpaid', 'pending')
            ORDER BY created_at
        """, (client,))

    def get_supplier_orders_in_range(self, supplier_name: str, supplier_id: int,
                                     start: str, end: str) -> List[Dict[str, Any]]:
        return db_query("""
            SELECT po.*, s.name as supplier_name,
                   (SELECT COALESCE(SUM(total_cost),0) FROM purchase_items WHERE po_id = po.id) as total_cost
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            WHERE (po.vendor = ? OR po.supplier_id = ?)
              AND po.purchase_date >= ? AND po.purchase_date <= ?
            ORDER BY po.purchase_date
        """, (supplier_name, supplier_id, start, end))

    def audit(self, action: str, table: str, record_id: int,
              old_data: dict = None, new_data: dict = None,
              operator: str = ""):
        log_audit(action, table, record_id,
                  old_data=old_data, new_data=new_data,
                  operator=operator)

    def get_supplier(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))

    def get_batch_profit(self, ticket_ids: List[int]) -> List[Dict[str, Any]]:
        """批量获取工单利润原始数据（利润计算由Service层完成）"""
        if not ticket_ids:
            return []
        placeholders = ",".join("?" * len(ticket_ids))
        return db_query(f"""
            SELECT t.id, t.ticket_no, t.client, t.status,
                   COALESCE(t.total, 0) as total,
                   COALESCE(i.total_income, 0) as total_income,
                   COALESCE(e.total_expense, 0) as total_expense
            FROM tickets t
            LEFT JOIN (SELECT source_id, COALESCE(SUM(amount), 0) as total_income
                       FROM income_records WHERE source_type='ticket'
                       GROUP BY source_id) i ON t.id = i.source_id
            LEFT JOIN (SELECT related_ticket_id, COALESCE(SUM(amount), 0) as total_expense
                       FROM expense_records GROUP BY related_ticket_id) e ON t.id = e.related_ticket_id
            WHERE t.id IN ({placeholders})
        """, tuple(ticket_ids))
