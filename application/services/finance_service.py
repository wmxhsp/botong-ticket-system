"""
博通 (Botong) — 财务应用服务（新架构版）
使用 FinanceRepository + EventBus
"""

import logging
import calendar as _cal
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from domain.events import EventBus, IncomeRecorded, ExpenseRecorded
from domain.exceptions import BillingError
from config.manager import config

logger = logging.getLogger(__name__)


class FinanceService:

    def __init__(self, repo, event_bus=None, client_service=None, ticket_service=None):
        self._repo = repo
        self._event_bus = event_bus
        self._client_service = client_service
        self._ticket_service = ticket_service

    def _get_client_svc(self):
        return self._client_service

    def _get_ticket_svc(self):
        return self._ticket_service

    @property
    def repo(self):
        return self._repo

    # ===== 收入管理 =====

    def record_income(self, source_type: str, source_id: int,
                      client: str, amount: float, method: str = "微信",
                      description: str = "") -> Dict[str, Any]:
        income_id = self._repo.record_income({
            "source_type": source_type,
            "source_id": source_id,
            "client": client,
            "amount": amount,
            "method": method,
            "description": description,
        })
        if self._event_bus:
            self._event_bus.dispatch(IncomeRecorded(
                amount=amount, client=client,
                source_type=source_type, source_id=source_id))
        return self._repo.get_income(income_id) or {}

    def get_monthly_income(self, month_start: str, month_end: str) -> float:
        return self._repo.get_monthly_income(month_start, month_end + " 23:59:59")

    def get_monthly_expense(self, month_start: str, month_end: str,
                            personal: bool = False) -> float:
        return self._repo.get_monthly_expense(month_start, month_end + " 23:59:59", personal)

    def get_monthly_data(self, months: int = 6) -> List[Dict[str, Any]]:
        monthly_data = []
        today = datetime.now()
        for i in range(months - 1, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            ym = f"{y}-{m:02d}"
            ms = ym + "-01"
            me = f"{ym}-{_cal.monthrange(y, m)[1]}"
            inc = self.get_monthly_income(ms, me)
            exp = self.get_monthly_expense(ms, me)
            monthly_data.append({
                "month": ym,
                "income": inc,
                "expense": exp,
                "profit": inc - exp,
            })
        for i in range(len(monthly_data)):
            if i > 0:
                prev = monthly_data[i - 1]
                curr = monthly_data[i]
                curr["income_growth"] = round((curr["income"] - prev["income"]) / prev["income"] * 100, 1) if prev["income"] > 0 else None
                curr["expense_growth"] = round((curr["expense"] - prev["expense"]) / prev["expense"] * 100, 1) if prev["expense"] > 0 else None
            else:
                monthly_data[i]["income_growth"] = None
                monthly_data[i]["expense_growth"] = None
        return monthly_data

    def get_income_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._repo.get_income_history(limit)

    def has_income_record(self, source_type: str, source_id: int) -> bool:
        return self._repo.has_income_record(source_type, source_id)

    def record_ticket_income(self, client: str, amount: float, method: str,
                              ticket_id: int, received_at: str, description: str):
        record_id = self._repo.record_ticket_income(ticket_id, client, amount, method, description)
        self._repo.audit("pay", "income_records", record_id,
                  new_data={"client": client, "amount": amount, "method": method, "ticket_id": ticket_id},
                  operator=config.get_operator())

    def record_quick_income(self, client: str, amount: float, method: str,
                         description: str, received_at: str = None) -> int:
        record_id = self._repo.record_quick_income(client, amount, method, description)
        self._repo.audit("quick_income", "income_records", record_id,
                  new_data={"client": client, "amount": amount, "method": method, "description": description},
                  operator=config.get_operator())
        return record_id

    def get_client_revenue(self, client: str = None):
        if client:
            return self._repo.get_client_revenue(client)
        return self._repo.get_income_by_client(
            datetime.now().strftime("%Y-01-01"),
            datetime.now().strftime("%Y-12-31"))

    def get_client_profitability(self, client: str = None):
        if client:
            return self._repo.get_client_profitability(client)
        rows = self._repo.get_income_by_client(
            datetime.now().strftime("%Y-01-01"),
            datetime.now().strftime("%Y-12-31"))
        result = []
        for r in rows:
            c = r.get("client", "")
            revenue = float(r.get("total", 0))
            expense = self._repo.get_client_profitability(c)
            result.append({
                "client": c,
                "revenue": revenue,
                "expense": expense,
                "profit": revenue - expense,
            })
        return result

    def get_client_income_records(self, client: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self._repo.get_client_income_records(client, limit)

    def get_income_records_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        return self._repo.get_income_records_range(start_date, end_date)

    def get_batch_ticket_income(self, ids: list) -> dict:
        return self._repo.get_batch_ticket_income(ids)

    def get_ticket_income_total(self, ticket_id: int) -> float:
        return self._repo.get_ticket_income_total(ticket_id)

    def get_ticket_income_records(self, ticket_id: int) -> List[Dict[str, Any]]:
        return self._repo.get_ticket_income_records(ticket_id)

    # ===== 支出管理 =====

    def add_expense(self, category: str, vendor: str, amount: float,
                    description: str = "", paid_at: str = None,
                    related_ticket_id: int = None,
                    is_personal: bool = False,
                    payment_type: str = "") -> Dict[str, Any]:
        if not paid_at:
            paid_at = datetime.now().strftime("%Y-%m-%d")
        exp_id = self._repo.record_expense({
            "category": category,
            "vendor": vendor,
            "description": description,
            "amount": amount,
            "paid_at": paid_at,
            "related_ticket_id": related_ticket_id,
            "is_personal": 1 if is_personal else 0,
            "payment_type": payment_type,
        })

        if related_ticket_id and not is_personal:
            self._sync_ticket_cost(related_ticket_id, category)

        if self._event_bus:
            self._event_bus.dispatch(ExpenseRecorded(
                amount=amount, category=category, description=description))
        return self._repo.get_expense(exp_id) or {}

    def list_expenses(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._repo.list_expenses(limit=limit)

    def update_expense(self, exp_id: int, **fields) -> bool:
        old_exp = self._repo.get_expense_ticket_id(exp_id)
        result = self._repo.update_expense(exp_id, fields)
        if old_exp and old_exp.get("related_ticket_id"):
            self._sync_ticket_cost(old_exp["related_ticket_id"])
        return result

    def delete_expense(self, exp_id: int) -> bool:
        old_exp = self._repo.get_expense_ticket_id(exp_id)
        result = self._repo.delete_expense(exp_id)
        if old_exp and old_exp.get("related_ticket_id"):
            self._sync_ticket_cost(old_exp["related_ticket_id"])
        return result

    def list_expense_categories(self) -> List[Dict[str, Any]]:
        return self._repo.list_expense_categories()

    def create_expense_category(self, name: str) -> int:
        return self._repo.create_expense_category(name)

    def get_expense_category(self, cat_id: int) -> Optional[Dict[str, Any]]:
        return self._repo.get_expense_category(cat_id)

    def delete_expense_category(self, cat_id: int):
        self._repo.delete_expense_category(cat_id)

    def update_expense_category(self, cat_id: int, name: str):
        self._repo.update_expense_category(cat_id, name)

    def count_expenses_by_category(self, category: str) -> int:
        return self._repo.count_expenses_by_category(category)

    def get_expense_records_range(self, start_date: str, end_date: str,
                                   personal: bool = False) -> List[Dict[str, Any]]:
        return self._repo.get_expense_records_range(start_date, end_date, personal)

    def get_batch_ticket_expense(self, ids: list) -> dict:
        return self._repo.get_batch_ticket_expense(ids)

    def get_ticket_expense_total(self, ticket_id: int) -> float:
        return self._repo.get_ticket_expense_total(ticket_id)

    def get_ticket_expense_detail(self, ticket_id: int) -> List[Dict[str, Any]]:
        return self._repo.get_ticket_expense_detail(ticket_id)

    # ===== 个人支出 =====

    def list_personal_expenses(self, month: str = None, category: str = "",
                                limit: int = 100) -> List[Dict[str, Any]]:
        return self._repo.list_personal_expenses(month, category or None, limit)

    def add_personal_expense(self, category: str, amount: float,
                              paid_at: str, payment_type: str = "微信",
                              vendor: str = "", description: str = "",
                              is_recurring: int = 0) -> int:
        record_id = self._repo.add_personal_expense({
            "category": category,
            "amount": amount,
            "paid_at": paid_at,
            "payment_type": payment_type,
            "vendor": vendor,
            "description": description,
            "is_recurring": is_recurring,
        })
        self._repo.audit("personal_expense", "expense_records", record_id,
                  new_data={"category": category, "amount": amount, "payment_type": payment_type,
                            "is_recurring": is_recurring, "description": description},
                  operator=config.get_operator())
        return record_id

    def get_personal_month_summary(self, month: str) -> Dict[str, Any]:
        summary = self._repo.get_personal_month_summary(month)
        total = sum(float(r.get("total", 0) or 0) for r in summary.get("by_category", []))
        total_budget = float(summary.get("budget_total", 0) or 0)
        return {
            "month": month,
            "total": round(total, 2),
            "total_budget": round(total_budget, 2),
            "budget_remaining": round(total_budget - total, 2),
            "by_category": summary.get("by_category", []),
            "by_payment": summary.get("by_payment_type", []),
            "daily_trend": summary.get("daily_trend", []),
            "budgets": [{"category": b.get("category", ""), "budget": b.get("budget_amount", 0)}
                        for b in summary.get("budgets", [])],
        }

    def set_personal_budget(self, category: str, month: str,
                             budget_amount: float) -> Dict[str, Any]:
        self._repo.set_personal_budget(month, category, budget_amount)
        return {"category": category, "month": month, "budget": budget_amount}

    def get_recurring_expenses(self) -> List[Dict[str, Any]]:
        return self._repo.get_recurring_expenses()

    def auto_create_recurring(self) -> List[Dict[str, Any]]:
        recurring = self.get_recurring_expenses()
        if not recurring:
            return []
        now = datetime.now().strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%Y-%m")
        created = []
        for r in recurring:
            if self._repo.check_recurring_exists(r["category"], current_month):
                continue
            self.add_personal_expense(
                category=r["category"],
                amount=float(r["amount"]),
                paid_at=now,
                payment_type=r.get("payment_type", "微信"),
                vendor=r.get("vendor", ""),
                description=f"自动创建: {r.get('description', r['category'])}",
                is_recurring=1,
            )
            created.append(r["category"])
        return created

    # ===== 应收款 =====

    def get_unpaid_tickets(self) -> List[Dict[str, Any]]:
        return self._repo.get_unpaid_tickets()

    def get_overdue_receivables(self) -> List[Dict[str, Any]]:
        results = self._repo.get_overdue_receivables()
        overdue = []
        now = datetime.now()
        for r in results:
            try:
                created = datetime.fromisoformat(r.get("created_at", ""))
            except (ValueError, TypeError):
                created = datetime.now()
            terms = r.get("payment_terms") or 30
            due_date = created + timedelta(days=int(terms))
            days_overdue = (now - due_date).days
            if days_overdue > 0:
                r["due_date"] = due_date.strftime("%Y-%m-%d")
                r["overdue_days"] = days_overdue
                overdue.append(r)
        return sorted(overdue, key=lambda x: x["overdue_days"], reverse=True)

    def get_overdue_receivables_summary(self) -> Dict[str, Any]:
        """获取逾期应收款列表（含汇总）"""
        overdue = self.get_overdue_receivables()
        total = sum(float(r.get("amount", 0) or 0) for r in overdue)
        return {
            "overdue": overdue,
            "total": round(total, 2),
            "summary": f"共 {len(overdue)} 笔逾期应收款，合计 ¥{total:.2f}",
        }

    def get_receivables(self, client: str = None, overdue_only: bool = False,
                        min_amount: float = 0) -> Dict[str, Any]:
        all_receivables = self._repo.get_receivables(client)
        now = datetime.now()
        by_client = {}

        for r in all_receivables:
            c = r["client"]
            if c not in by_client:
                by_client[c] = {"client": c, "items": [], "total": 0, "count": 0}

            amt = float(r.get("amount") or 0)
            try:
                created = datetime.fromisoformat(r["created_at"])
            except (ValueError, TypeError):
                created = now

            days_overdue = 0
            due_date = None
            if overdue_only:
                client_row = self._repo._query_client_payment_terms(c)
                terms = client_row if client_row else 30
                due = created + timedelta(days=terms)
                due_date = due.strftime("%Y-%m-%d")
                days_overdue = (now - due).days
                if days_overdue <= 0:
                    continue

            by_client[c]["items"].append({
                **r,
                "amount": amt,
                "due_date": due_date,
                "days_overdue": days_overdue,
            })
            by_client[c]["total"] += amt
            by_client[c]["count"] += 1

        result = sorted(by_client.values(), key=lambda x: x["total"], reverse=True)
        if min_amount > 0:
            result = [r for r in result if r["total"] >= min_amount]

        grand_total = sum(r["total"] for r in result)
        return {
            "receivables": result,
            "grand_total": round(grand_total, 2),
            "summary": f"共 {len(result)} 位客户 {sum(r['count'] for r in result)} 笔应收款，合计 ¥{grand_total:.2f}",
        }

    def get_client_statement(self, client_name: str, start: str = None,
                             end: str = None) -> Dict[str, Any]:
        now = datetime.now()
        if not start:
            start = now.strftime("%Y-%m-01")
        if not end:
            end = now.strftime("%Y-%m-%d")
        end_full = end + " 23:59:59"

        client_svc = self._get_client_svc()
        client = client_svc.get_client(client_name) if client_svc else None
        if not client:
            raise ValueError(f"客户 {client_name} 不存在")

        opening_balance = self._repo.get_client_opening_balance(client_name, start)
        income_records = self._repo.get_client_income_in_range(client_name, start, end_full)
        expense_records = self._repo.get_client_expense_in_range(client_name, start, end_full)
        unpaid_tickets = self._repo.get_client_unpaid_tickets(client_name)

        period_income = sum(float(r.get("amount", 0) or 0) for r in income_records)
        period_expense = sum(float(r.get("amount", 0) or 0) for r in expense_records)
        unpaid_total = sum(float(r.get("amount", 0) or 0) for r in unpaid_tickets)
        closing_balance = opening_balance + period_income - period_expense

        return {
            "client": client_name,
            "period": {"start": start, "end": end},
            "opening_balance": round(opening_balance, 2),
            "closing_balance": round(closing_balance, 2),
            "period_income": round(period_income, 2),
            "period_expense": round(period_expense, 2),
            "unpaid_total": round(unpaid_total, 2),
            "income_records": income_records,
            "expense_records": expense_records,
            "unpaid_tickets": unpaid_tickets,
            "payment_terms": client.get("payment_terms", 30) if isinstance(client, dict) else 30,
            "summary": f"{client_name} 对账单：期初 ¥{opening_balance:.2f}，期间收入 ¥{period_income:.2f}，支出 ¥{period_expense:.2f}，未收款 ¥{unpaid_total:.2f}，期末 ¥{closing_balance:.2f}",
        }

    def get_supplier_statement(self, supplier_id: int, start: str = None,
                               end: str = None) -> Dict[str, Any]:
        now = datetime.now()
        if not start:
            start = now.strftime("%Y-%m-01")
        if not end:
            end = now.strftime("%Y-%m-%d")
        end_full = end + " 23:59:59"

        supplier = self._repo.get_supplier(supplier_id)
        if not supplier:
            raise ValueError(f"供应商 #{supplier_id} 不存在")

        name = supplier["name"]
        orders = self._repo.get_supplier_orders_in_range(name, supplier_id, start, end_full)

        total_ordered = sum(float(o.get("total_cost", 0) or o.get("total_amount", 0) or 0) for o in orders)
        paid_amount = sum(float(o.get("total_amount", 0) or 0) for o in orders if o.get("payment_status") == "paid")
        unpaid_amount = total_ordered - paid_amount
        paid_orders = [o for o in orders if o.get("payment_status") in ("paid", "partial")]

        return {
            "supplier": name,
            "supplier_id": supplier_id,
            "period": {"start": start, "end": end},
            "total_ordered": round(total_ordered, 2),
            "paid_amount": round(paid_amount, 2),
            "unpaid_amount": round(unpaid_amount, 2),
            "orders": orders,
            "paid_orders": paid_orders,
            "payment_terms": supplier.get("payment_terms", 30),
            "summary": f"{name} 对账单：期间采购 ¥{total_ordered:.2f}，已付 ¥{paid_amount:.2f}，未付 ¥{unpaid_amount:.2f}",
        }

    def get_client_aging(self, client: str) -> Dict[str, Any]:
        rows = self._repo.get_client_aging(client)
        now = datetime.now()
        aging = {"<30天": 0, "30-60天": 0, ">60天": 0, "total": 0, "items": []}
        for r in rows:
            try:
                created = datetime.fromisoformat(r.get("created_at", ""))
            except (ValueError, TypeError):
                created = datetime.now()
            days = (now - created).days
            amount = r.get("amount", 0) or 0
            aging["total"] += amount
            aging["items"].append({
                "id": r["id"], "ticket_no": r.get("ticket_no", ""),
                "amount": amount, "days": days,
            })
            if days < 30:
                aging["<30天"] += amount
            elif days < 60:
                aging["30-60天"] += amount
            else:
                aging[">60天"] += amount
        return aging

    def confirm_payment(self, ticket_id: int, amount: float,
                        method: str = "微信", note: str = "") -> bool:
        logger.warning("FinanceService.confirm_payment 已废弃，请使用 TicketService.confirm_payment")
        try:
            ticket_svc = self._get_ticket_svc()
            ticket_svc.confirm_payment(ticket_id, amount, method, note)
            return True
        except Exception:
            return False

    def record_partial_payment(self, ticket_id: int, amount: float,
                               method: str = "微信", note: str = "") -> Dict[str, Any]:
        ticket = self._get_ticket_svc().get_ticket(ticket_id)
        if not ticket:
            from domain.exceptions import TicketNotFoundError
            raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")

        if amount <= 0:
            raise ValueError("收款金额必须大于 0")

        total_due = float(ticket.get("total_with_tax") or 0)
        if total_due <= 0:
            total_due = float(ticket.get("total") or 0)
        if total_due <= 0:
            total_due = (float(ticket.get("total_labor") or 0)
                         + float(ticket.get("total_material") or 0)
                         + float(ticket.get("total_external") or 0))
        if total_due <= 0:
            raise ValueError("工单总额为 0，无需收款")

        already_paid = self._repo.get_ticket_paid_total(ticket_id)
        remaining = total_due - already_paid

        if amount > remaining + 0.01:
            raise ValueError(
                f"收款额 ¥{amount:.2f} 超出剩余应收 ¥{max(remaining, 0):.2f}")

        self.record_income(
            "ticket", ticket_id, ticket.get("client", ""),
            amount, method,
            note or f"工单收款 #{ticket.get('ticket_no', '')}")

        new_paid = already_paid + amount
        is_settled = abs(new_paid - total_due) < 0.01

        if is_settled:
            if self._event_bus:
                from domain.events import TicketSettled, TicketPaymentConfirmed
                self._event_bus.dispatch(TicketSettled(
                    ticket_id=ticket_id, billing_status="paid",
                    closed_at=datetime.now().isoformat()))
                self._event_bus.dispatch(TicketPaymentConfirmed(
                    ticket_id=ticket_id, amount=amount, method=method))
            else:
                self._get_ticket_svc().update_ticket_billing(
                    ticket_id, billing_status="paid",
                    closed_at=datetime.now().isoformat())

        return {
            "ticket_id": ticket_id,
            "paid_amount": amount,
            "total_paid": round(new_paid, 2),
            "total_due": total_due,
            "remaining": round(total_due - new_paid, 2),
            "is_settled": is_settled,
        }

    def get_payment_history(self, ticket_id: int) -> List[Dict[str, Any]]:
        return self._repo.get_payment_history(ticket_id)

    # ===== 结算单 =====

    def generate_invoice(self, ticket_id: int, tax_rate: float = None) -> Dict[str, Any]:
        billing_cfg = config.get_billing_config()

        ticket = self._get_ticket_svc().get_ticket(ticket_id)
        if not ticket:
            raise BillingError(f"工单 #{ticket_id} 不存在")

        if self._repo.has_income_record('ticket', ticket_id):
            return {}

        total = ticket.get("total", 0) or 0
        if total <= 0:
            raise BillingError("工单金额为0，无法生成结算单")

        if tax_rate is None:
            tax_rate = billing_cfg.default_tax_rate if billing_cfg.auto_tax_calc else 0
        tax_amount = total * tax_rate
        total_with_tax = total + tax_amount

        now = datetime.now()
        invoice_no = f"INV-{now.strftime('%Y%m%d')}-{ticket_id:04d}"

        record_id = self._repo.generate_invoice_record(
            ticket_id, ticket.get("client", ""), total, tax_amount,
            "pending",
            f"工单 {ticket.get('ticket_no', '')} 结算单 {invoice_no}")

        if self._event_bus:
            from domain.events import TicketTaxUpdated
            self._event_bus.dispatch(TicketTaxUpdated(
                ticket_id=ticket_id, tax_rate=tax_rate,
                tax_amount=tax_amount, billing_status="pending"))
        else:
            self._get_ticket_svc().update_ticket_billing(
                ticket_id, billing_status="pending",
                tax_rate=tax_rate, tax_amount=tax_amount,
                total_with_tax=total_with_tax)

        return self._repo.find_income_record(record_id)

    def list_pending_invoices(self, days_overdue: int = None) -> List[Dict[str, Any]]:
        results = self._repo.list_pending_invoices()

        now = datetime.now()
        for r in results:
            try:
                created = datetime.fromisoformat(r.get("created_at", ""))
            except (ValueError, TypeError):
                created = datetime.now()
            terms = r.get("payment_terms") or 30
            due_date = created + timedelta(days=int(terms))
            r["due_date"] = due_date.isoformat()
            r["days_overdue"] = (now - due_date).days if now > due_date else 0

        if days_overdue is not None:
            results = [r for r in results if r.get("days_overdue", 0) >= days_overdue]

        return results

    # ===== 统计 =====

    def get_finance_dashboard(self, month: str = None) -> Dict[str, Any]:
        if not month:
            month = datetime.now().strftime("%Y-%m")

        y, m = month.split("-")
        ms = f"{month}-01"
        last_day = _cal.monthrange(int(y), int(m))[1]
        me = f"{month}-{last_day}"
        me_full = me + " 23:59:59"

        monthly = self._repo.get_dashboard_summary(ms, me_full)
        income = float(monthly.get("income", 0) or 0)
        expense = float(monthly.get("expense", 0) or 0)
        profit = income - expense

        unpaid_tickets = self._repo.get_unpaid_tickets()
        unpaid_count = len(unpaid_tickets)
        unpaid_total = sum(float(t.get("total", 0) or 0) for t in unpaid_tickets)

        unpaid_sales = self._repo.get_unpaid_sales_count()
        unpaid_count += (unpaid_sales and unpaid_sales[0]["c"] or 0)
        unpaid_total += float(unpaid_sales[0]["t"] if unpaid_sales else 0)

        overdue_list = self.get_overdue_receivables()
        overdue_count = len(overdue_list)
        overdue_total = sum(float(r.get("amount", 0) or 0) for r in overdue_list)

        top_expenses = self._repo.get_top_expense_categories(ms, me_full, 5)
        top_clients = self._repo.get_top_income_clients(ms, me_full, 5)

        return {
            "month": month,
            "income": round(income, 2),
            "expense": round(expense, 2),
            "profit": round(profit, 2),
            "expense_rate": round((expense / income * 100), 1) if income > 0 else 0,
            "daily_income": round(income / datetime.now().day, 2),
            "ticket_count": monthly.get("ticket_count", 0) or 0,
            "client_count": monthly.get("client_count", 0) or 0,
            "unpaid": {"count": unpaid_count, "total": round(unpaid_total, 2)},
            "overdue": {"count": overdue_count, "total": round(overdue_total, 2)},
            "top_expenses": top_expenses or [],
            "top_clients": top_clients or [],
            "_ms": ms,
            "_me": me_full,
        }

    def get_ticket_profit(self, month: str = None) -> List[Dict[str, Any]]:
        rows = self._repo.get_ticket_profit(month)
        result = []
        for r in rows:
            income = float(r.get("income", 0) or 0)
            material_cost = float(r.get("material_cost", 0) or 0)
            labor_cost = float(r.get("labor_cost", 0) or 0)
            external_cost = float(r.get("external_cost", 0) or 0)
            profit = income - material_cost - labor_cost - external_cost
            margin = round(profit / income * 100, 1) if income > 0 else 0
            result.append({
                **r,
                "profit": profit,
                "margin": margin,
            })
        return result

    def get_ticket_profit_summary(self, month: str = None) -> Dict[str, Any]:
        """工单利润分析（含汇总）"""
        profit_data = self.get_ticket_profit(month=month)
        total_income = sum(t["income"] for t in profit_data)
        total_cost = sum(
            float(t.get("material_cost", 0) or 0) + float(t.get("labor_cost", 0) or 0) + float(t.get("external_cost", 0) or 0)
            for t in profit_data
        )
        total_profit = sum(t["profit"] for t in profit_data)
        overall_margin = round(total_profit / total_income * 100, 1) if total_income > 0 else 0
        return {
            "profit_data": profit_data,
            "month": month or datetime.now().strftime("%Y-%m"),
            "total_income": round(total_income, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "overall_margin": overall_margin,
            "summary": f"{month or '本月'} 工单利润：收入 ¥{total_income:.2f}，成本 ¥{total_cost:.2f}，利润 ¥{total_profit:.2f}，毛利率 {overall_margin}%",
        }

    def get_batch_profit(self, ticket_ids: List[int]) -> List[Dict[str, Any]]:
        rows = self._repo.get_batch_profit(ticket_ids)
        result = []
        for r in rows:
            total = float(r.get("total", 0) or 0)
            total_expense = float(r.get("total_expense", 0) or 0)
            profit = total - total_expense
            result.append({
                **r,
                "profit": profit,
            })
        return result

    def get_summary(self, month: str = None) -> Dict[str, Any]:
        """获取财务完整汇总（API 层 _get_finance_summary 的服务层实现）"""
        if not month:
            month = datetime.now().strftime("%Y-%m")

        dashboard = self.get_finance_dashboard(month=month)
        monthly_tickets = self.get_monthly_ticket_stats(dashboard["_ms"], dashboard["_me"])
        top_client = self.get_top_client(dashboard["_ms"], dashboard["_me"])
        income_history = self.get_income_history(limit=50)
        expense_history = self.list_expenses(limit=50)
        monthly_data = self.get_monthly_data(months=6)
        client_revenue = self.get_client_revenue()
        client_profitability = self.get_client_profitability()

        unpaid = self.get_unpaid_tickets()
        total_unpaid = sum(float(t.get("total", 0) or 0) for t in unpaid)

        return {
            "unpaid_tickets": unpaid,
            "total_unpaid": total_unpaid,
            "month": month,
            "monthly_income": dashboard["income"],
            "monthly_expense": dashboard["expense"],
            "monthly_profit": dashboard["profit"],
            "summary": f"{month} 财务概况：收入 ¥{dashboard['income']:.2f}，支出 ¥{dashboard['expense']:.2f}，利润 ¥{dashboard['profit']:.2f}，{len(unpaid)} 单未收款共 ¥{total_unpaid:.2f}",
            "monthly_expense_rate": dashboard["expense_rate"],
            "monthly_tickets": monthly_tickets["c"] if monthly_tickets else 0,
            "monthly_clients": monthly_tickets["clients"] if monthly_tickets else 0,
            "top_client": top_client,
            "top_expense_category": dashboard["top_expenses"][0] if dashboard.get("top_expenses") else None,
            "expense_by_category": dashboard["top_expenses"],
            "unpaid_count": len(unpaid),
            "income_history": income_history,
            "expense_history": expense_history,
            "monthly_data": monthly_data,
            "client_revenue": client_revenue,
            "client_profitability": client_profitability,
        }

    def get_ticket_profit_detail(self, ticket_id: int) -> Dict[str, Any]:
        """按工单查询利润明细"""
        ticket_svc = self._get_ticket_svc()
        ticket = ticket_svc.get_ticket(ticket_id)

        total_income = self.get_ticket_income_total(ticket_id)
        total_expense = self.get_ticket_expense_total(ticket_id)
        expense_detail = self.get_ticket_expense_detail(ticket_id)
        income_recs = self.get_ticket_income_records(ticket_id)

        profit = total_income - total_expense
        margin = round(profit / total_income * 100, 1) if total_income > 0 else 0

        return {
            "ticket_id": ticket_id,
            "ticket_no": ticket["ticket_no"],
            "client": ticket["client"],
            "status": ticket["status"],
            "billing_status": ticket["billing_status"],
            "total_bill": ticket["total"] or 0,
            "total_labor": ticket["total_labor"] or 0,
            "total_material": ticket["total_material"] or 0,
            "total_income": total_income,
            "total_expense": total_expense,
            "profit": profit,
            "margin": margin,
            "expenses": expense_detail,
            "income_records": income_recs,
        }

    def get_ticket_profit_list(self) -> Dict[str, Any]:
        """获取全部工单利润列表"""
        ticket_svc = self._get_ticket_svc()
        data = ticket_svc.list_tickets(page=1, per_page=200)
        tickets = data["tickets"] if isinstance(data, dict) else data
        ids = [t["id"] for t in tickets]
        income_map = self.get_batch_ticket_income(ids)
        expense_map = self.get_batch_ticket_expense(ids)
        result = []
        for t in tickets:
            tid = t["id"]
            ti = income_map.get(tid, 0)
            te = expense_map.get(tid, 0)
            result.append({
                "id": t["id"],
                "ticket_no": t["ticket_no"],
                "client": t["client"],
                "total_bill": t["total"] or 0,
                "total_income": ti,
                "total_expense": te,
                "profit": ti - te,
                "billing_status": t.get("billing_status", ""),
            })
        return {"tickets": result}

    def get_revenue_stats(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        if start_date and end_date:
            result = self._repo.get_revenue_stats(start_date, end_date)
            by_client = self._repo.get_revenue_by_client(start_date, end_date)
        else:
            result = {"total": 0, "count": 0, "avg_amount": 0}
            by_client = []
        return {
            "total_count": result.get("count", 0) or 0,
            "total_amount": result.get("total", 0) or 0,
            "total_tax": result.get("total_tax", 0) or 0,
            "total_with_tax": result.get("total_with_tax", 0) or 0,
            "by_client": by_client
        }

    def get_top_client(self, month_start: str, month_end: str) -> Optional[Dict[str, Any]]:
        return self._repo.get_top_client(month_start, month_end + " 23:59:59")

    def get_top_expense_category(self, month_start: str, month_end: str) -> Optional[Dict[str, Any]]:
        return self._repo.get_top_expense_category(month_start, month_end + " 23:59:59")

    def get_expense_by_category(self, month_start: str, month_end: str) -> List[Dict[str, Any]]:
        return self._repo.get_expense_by_category(month_start, month_end + " 23:59:59")

    def get_monthly_ticket_stats(self, month_start: str, month_end: str) -> Dict[str, Any]:
        return self._repo.get_monthly_ticket_stats(month_start, month_end + " 23:59:59")

    def get_sales_report(self, month: str = None) -> Dict[str, Any]:
        if not month:
            month = datetime.now().strftime("%Y-%m")

        y, m = month.split("-")
        month_start = f"{month}-01"
        last_day = _cal.monthrange(int(y), int(m))[1]
        month_end = f"{month}-{last_day}"

        sales = self._repo.get_sales_report(month_start, month_end + " 23:59:59")

        total_qty = sum(float(s.get("quantity", 0) or 0) for s in sales)
        total_revenue = sum(float(s.get("total_amount", 0) or 0) for s in sales)
        total_profit = sum(float(s.get("profit", 0) or 0) for s in sales)

        by_product = {}
        for s in sales:
            pid = s["product_id"] or 0
            if pid not in by_product:
                by_product[pid] = {
                    "name": s.get("goods_name") or s.get("product_name", "未知"),
                    "sku": s.get("goods_sku", ""),
                    "category": s.get("category_name", ""),
                    "qty": 0, "revenue": 0, "profit": 0, "count": 0,
                }
            by_product[pid]["qty"] += float(s.get("quantity", 0) or 0)
            by_product[pid]["revenue"] += float(s.get("total_amount", 0) or 0)
            by_product[pid]["profit"] += float(s.get("profit", 0) or 0)
            by_product[pid]["count"] += 1

        by_client = {}
        for s in sales:
            c = s["client"]
            if c not in by_client:
                by_client[c] = {"name": c, "qty": 0, "revenue": 0, "count": 0}
            by_client[c]["qty"] += float(s.get("quantity", 0) or 0)
            by_client[c]["revenue"] += float(s.get("total_amount", 0) or 0)
            by_client[c]["count"] += 1

        by_category = {}
        for s in sales:
            cat = s.get("category_name") or "未分类"
            if cat not in by_category:
                by_category[cat] = {"name": cat, "qty": 0, "revenue": 0, "count": 0}
            by_category[cat]["qty"] += float(s.get("quantity", 0) or 0)
            by_category[cat]["revenue"] += float(s.get("total_amount", 0) or 0)
            by_category[cat]["count"] += 1

        return {
            "month": month,
            "total_sales": len(sales),
            "total_qty": total_qty,
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "by_product": sorted(by_product.values(), key=lambda x: x["revenue"], reverse=True),
            "by_client": sorted(by_client.values(), key=lambda x: x["revenue"], reverse=True),
            "by_category": sorted(by_category.values(), key=lambda x: x["revenue"], reverse=True),
        }

    # ===== 协议 =====

    def pay_agreement(self, agreement_id: int, amount: float,
                      method: str = "微信", received_at: str = None) -> Dict[str, Any]:
        agreement = self._repo.get_agreement(agreement_id)
        if not agreement:
            raise BillingError(f"协议 #{agreement_id} 不存在")

        now = datetime.now().isoformat()
        received = received_at or now

        self._repo.record_agreement_income(
            agreement_id, agreement["client"], amount, method,
            f"协议 {agreement['agreement_no']} 收款")

        new_paid = (agreement.get("paid_amount", 0) or 0) + amount
        self._repo.update_agreement_payment(agreement_id, new_paid, received)

        return self._repo.get_agreement(agreement_id)

    def get_agreement_payment_summary(self, client: str = None) -> List[Dict[str, Any]]:
        agreements = self._repo.list_active_agreements()
        if client:
            agreements = [a for a in agreements if a.get("client") == client]
        return agreements

    # ===== 工单成本同步 =====

    def update_inspection_plan_next_execution(self, plan_id: int, next_execution: str):
        self._repo.update_inspection_plan_next_execution(plan_id, next_execution)

    def _sync_ticket_cost(self, ticket_id: int, category: str = None):
        ticket = self._get_ticket_svc().get_ticket(ticket_id)
        if not ticket:
            return

        labor_total = self._repo.get_ticket_labor_cost(ticket_id)
        other_total = self._repo.get_ticket_external_cost(ticket_id)

        if self._event_bus:
            from domain.events import TicketCostSyncRequired
            self._event_bus.dispatch(TicketCostSyncRequired(ticket_id=ticket_id))
        else:
            self._get_ticket_svc().update_ticket_billing(
                ticket_id, total_labor=labor_total, total_external=other_total)
