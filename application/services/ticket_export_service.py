import csv
import logging
from io import StringIO
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TicketExportService:
    STATUS_NAMES = {
        "open": "待处理", "in-progress": "进行中", "pending-payment": "待结算",
        "closed": "已完成", "cancelled": "已取消",
    }

    def __init__(self, ticket_service=None, finance_service=None, equipment_service=None):
        self._ticket_service = ticket_service
        self._finance_service = finance_service
        self._equipment_service = equipment_service

    def export_tickets_csv(self, filters=None):
        filters = filters or {}
        data = self._ticket_service.list_tickets(
            status=filters.get("status"), client=filters.get("client"),
            keyword=filters.get("q"), date_from=filters.get("date_from"),
            date_to=filters.get("date_to"), page=1, per_page=99999)
        tickets = data["tickets"] if isinstance(data, dict) else data
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["工单编号", "客户", "内容", "状态", "金额", "创建时间"])
        for t in tickets:
            writer.writerow([t.get("ticket_no", ""), t.get("client", ""),
                            (t.get("description") or t.get("content") or "")[:50],
                            self.STATUS_NAMES.get(t.get("status"), t.get("status")),
                            t.get("total", 0), t.get("created_at", "")])
        return output.getvalue()

    def export_finance_csv(self):
        income = self._finance_service.get_income_history(limit=99999)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "客户", "金额", "方式", "描述"])
        for r in income:
            writer.writerow([r.get("received_at", ""), r.get("client", ""),
                            r.get("amount", 0), r.get("payment_method", ""), r.get("description", "")])
        return output.getvalue()

    def export_profit_csv(self, filters=None):
        data = self._ticket_service.list_tickets(page=1, per_page=99999)
        tickets = data["tickets"] if isinstance(data, dict) else data
        ids = [t["id"] for t in tickets]
        income_map = self._finance_service.get_batch_ticket_income(ids)
        expense_map = self._finance_service.get_batch_ticket_expense(ids)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["工单编号", "客户", "应收", "已收", "成本", "利润"])
        for t in tickets:
            tid = t["id"]
            inc = income_map.get(tid, 0)
            exp = expense_map.get(tid, 0)
            writer.writerow([t.get("ticket_no", ""), t.get("client", ""),
                            t.get("total", 0), inc, exp, inc - exp])
        return output.getvalue()

    def export_statement_csv(self, client_name):
        result = self._finance_service.get_client_statement(client_name)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "类型", "工单号", "金额", "备注"])
        for r in result.get("income_records", []):
            writer.writerow([r.get("date", ""), "收入", r.get("source_id", ""), r.get("amount", 0), ""])
        for r in result.get("expense_records", []):
            writer.writerow([r.get("date", ""), "支出", r.get("source_id", ""), r.get("amount", 0), ""])
        return output.getvalue()

    def export_supplier_statement_csv(self, supplier_id):
        result = self._finance_service.get_supplier_statement(supplier_id)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "采购单号", "金额", "状态"])
        for o in result.get("orders", []):
            writer.writerow([o.get("purchase_date", ""), o.get("po_no", ""),
                            o.get("total_cost", o.get("total_amount", 0)), o.get("payment_status", "")])
        return output.getvalue()

    def export_equipment_csv(self):
        equipment = self._equipment_service.list_equipment(page=1, page_size=99999)
        items = equipment.get("items", equipment.get("equipment", equipment if isinstance(equipment, list) else []))
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["名称", "序列号", "型号", "客户", "状态", "位置"])
        for e in (items or []):
            writer.writerow([e.get("name", ""), e.get("serial_no", ""), e.get("model", ""),
                            e.get("client", ""), e.get("status", ""), e.get("location", "")])
        return output.getvalue()
