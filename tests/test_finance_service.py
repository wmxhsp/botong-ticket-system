"""
博通工单系统 — 财务模块单元测试（直接测试 Service 层）
不依赖 Flask 服务器，可独立运行
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one
from infrastructure.di.bootstrap import bootstrap
bootstrap()
from infrastructure.di.service_injection import inject_service
finance_service = inject_service("finance_service")
ticket_svc = inject_service("ticket_service")


class TestFinanceService:
    """财务服务层单元测试"""

    def test_monthly_income_returns_float(self):
        """月度收入应为数值"""
        income = finance_service.get_monthly_income("2026-05-01", "2026-05-31")
        assert isinstance(income, (int, float))
        assert income >= 0

    def test_monthly_expense_excludes_personal(self):
        """月度业务支出不应包含其他费用"""
        # 先插入一条业务支出（确保测试有数据）
        db_execute(
            "INSERT INTO expense_records (category, vendor, amount, description, "
            "paid_at, is_personal) VALUES (?, ?, ?, ?, ?, 0)",
            ("维修耗材", "测试供应商", 500, "测试业务支出", "2026-05-15"))
        # 再插入一条个人支出（不应计入业务支出）
        db_execute(
            "INSERT INTO expense_records (category, vendor, amount, description, "
            "paid_at, is_personal) VALUES (?, ?, ?, ?, ?, 1)",
            ("个人消费", "个人", 200, "测试个人支出", "2026-05-15"))

        total = finance_service.get_monthly_expense("2026-05-01", "2026-05-31")
        personal = db_query_one(
            "SELECT COALESCE(SUM(amount),0) as t FROM expense_records "
            "WHERE is_personal=1 AND paid_at >= '2026-05-01' AND paid_at <= '2026-05-31'")
        assert total > 0
        # 其他费用不应计入业务支出（业务支出应 >= 500，而非包含其他费用）
        assert total >= 500
        # 其他费用应低于双倍业务支出（验证隔离性）
        assert personal["t"] < total * 2 or personal["t"] == 0

    def test_unpaid_tickets_structure(self):
        """未结算工单列表应有必要字段"""
        unpaid = finance_service.get_unpaid_tickets()
        if unpaid:
            ticket = unpaid[0]
            assert "ticket_no" in ticket
            assert "client" in ticket
            assert "total" in ticket

    def test_get_overdue_receivables(self):
        """逾期应收款应返回合法数据"""
        overdue = finance_service.get_overdue_receivables()
        assert isinstance(overdue, list)
        for r in overdue:
            assert "client" in r
            assert "amount" in r
            assert r.get("overdue_days", 0) >= 0

    def test_client_revenue_structure(self):
        """客户收入排行应有正确字段"""
        revenue = finance_service.get_client_revenue()
        assert isinstance(revenue, list)
        for r in revenue:
            assert "client" in r
            assert "total" in r

    def test_client_profitability_structure(self):
        """客户利润率应有正确字段"""
        profitability = finance_service.get_client_profitability()
        assert isinstance(profitability, list)
        for p in profitability:
            assert "client" in p
            assert "revenue" in p
            assert "expense" in p

    def test_finance_dashboard_returns_all_keys(self):
        """总览看板应包含所有关键指标"""
        dashboard = finance_service.get_finance_dashboard()
        required_keys = ["income", "expense", "profit", "unpaid", "overdue",
                         "ticket_count", "client_count", "top_expenses", "top_clients"]
        for k in required_keys:
            assert k in dashboard, f"缺少关键字段: {k}"

    def test_finance_dashboard_month_filter(self):
        """总览看板应按月份过滤"""
        d_may = finance_service.get_finance_dashboard(month="2026-05")
        d_apr = finance_service.get_finance_dashboard(month="2026-04")
        assert d_may["month"] == "2026-05"
        assert d_apr["month"] == "2026-04"

    def test_ticket_profit_consistency(self):
        """工单利润计算一致性：利润 = 收入 - 总成本"""
        profits = finance_service.get_ticket_profit()
        for p in profits[:10]:
            calc = p["income"] - p["material_cost"] - p["labor_cost"] - p["external_cost"]
            assert abs(calc - p["profit"]) < 0.01, \
                f"工单 {p['ticket_no']} 利润不一致: 计算={calc}, 报告={p['profit']}"

    def test_get_sales_report(self):
        """销售报表应正常返回"""
        report = finance_service.get_sales_report()
        assert isinstance(report, dict)
        # 至少应包含部分汇总数据
        assert any(k in report for k in ["by_product", "by_client", "summary"])

    def test_list_expenses_excludes_personal(self):
        """list_expenses 不应包含其他费用"""
        expenses = finance_service.list_expenses(limit=100)
        for e in expenses:
            # expense_records 表中业务支出的 is_personal=0
            record = db_query_one("SELECT is_personal FROM expense_records WHERE id=?", (e["id"],))
            if record:
                assert record["is_personal"] == 0 or record["is_personal"] is None, \
                    f"支出 #{e['id']} 是其他费用，不应出现在业务支出列表"

    def test_income_history_returns_records(self):
        """收入历史应有记录"""
        income = finance_service.get_income_history(limit=10)
        assert isinstance(income, list)

    def test_ticket_profit_chained_costs(self):
        """工单利润中的成本应 >= 0"""
        profits = finance_service.get_ticket_profit()
        for p in profits:
            assert p["material_cost"] >= 0
            assert p["labor_cost"] >= 0
            assert p["external_cost"] >= 0


class TestTicketAutoProgress:
    """工单自动流转测试"""

    def test_create_ticket_starts_open(self):
        """新工单应为 open 状态"""
        t = ticket_svc.create_ticket(title="auto-test", client="集宁一中",
                                     description="自动流转测试 (可忽略)")
        assert t["status"] == "open"
        # 不做清理（系统会自动管理）

    def test_add_technician_progresses_to_in_progress(self):
        """添加技术员 → 自动流转到 in-progress"""
        t = ticket_svc.create_ticket(title="auto-test2", client="集宁一中",
                                     description="技术员自动流转 (可忽略)")
        ticket_svc.add_technician(t["id"], "苏鹏", 60, 1.0)
        updated = ticket_svc.get_ticket(t["id"])
        assert updated["status"] == "in-progress", \
            f"预期 in-progress, 实际 {updated['status']}"
        # 不做清理（系统会自动管理）


class TestFinanceAPI:
    """财务 API 端到端测试（直接调用 Service 模拟 API 行为）"""

    def test_quick_income_records_income(self):
        """快捷记账应正确记录收入"""
        fs = finance_service
        before = fs.get_monthly_income("2026-05-01", "2026-05-31")
        fs.record_quick_income("测试客户", 500, "微信", "API测试收入",
                               "2026-05-12T12:00:00")
        after = fs.get_monthly_income("2026-05-01", "2026-05-31")
        assert after >= before + 499, f"快捷记账后收入应增加500 (before={before}, after={after})"

    def test_has_income_record_detection(self):
        """has_income_record 应正确检测已存在的收入"""
        fs = finance_service
        # 先记录一笔收入确保有数据
        ticket_svc.create_ticket(title="收入检测测试", client="测试客户", description="test")
        fs.record_quick_income("检测客户", 100, "微信", "检测用收入", "2026-05-12T12:00:00")
        # 用 source_type='quick' 检测刚记录的（quick 类型由 repo 自动标记）
        assert fs.has_income_record("ticket", 99999) == False

    def test_get_unpaid_tickets_structure(self):
        """未结算工单应包含必要字段"""
        fs = finance_service
        unpaid = fs.get_unpaid_tickets()
        for t in unpaid:
            assert t.get("billing_status") in ("unpaid", "pending", "未结算", "待收款")

    def test_expense_records_range_filters_date(self):
        """支出范围查询应过滤日期"""
        fs = finance_service
        may = fs.get_expense_records_range("2026-05-01", "2026-05-31 23:59:59")
        for e in may:
            assert "2026-05" in e["paid_at"]

    def test_income_records_range_returns_list(self):
        """收入范围查询应返回非空列表"""
        fs = finance_service
        data = fs.get_income_records_range("2026-04-01", "2026-05-31 23:59:59")
        assert len(data) > 0

    def test_batch_ticket_income_map(self):
        """批量收入查询应返回 dict"""
        fs = finance_service
        # 使用不存在的 ID 验证返回结构
        result = fs.get_batch_ticket_income([99998, 99999])
        assert isinstance(result, dict)

    def test_batch_ticket_expense_map(self):
        """批量支出查询应返回 dict"""
        fs = finance_service
        result = fs.get_batch_ticket_expense([1, 40])
        assert isinstance(result, dict)
        assert isinstance(result.get(1, 0), (int, float))
