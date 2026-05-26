"""
博通 — 新架构集成测试
覆盖: Repository → Service → EventBus
"""

import pytest
import json
import os
import sys
from unittest.mock import MagicMock, patch

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# ── 测试数据库（临时文件，避免 :memory: 的连接池问题） ──
# 记录原值，在 teardown 中恢复
_SAVED_DB_PATH = os.environ.pop("TICKETS_DB_PATH", None)
_TEST_DB = os.path.join(BASE_DIR, "test_arch.db")
os.environ["TICKETS_DB_PATH"] = _TEST_DB


def teardown_module():
    """模块级清理：恢复数据库模块状态到生产 DB"""
    _saved = _SAVED_DB_PATH or os.path.join(BASE_DIR, "tickets.db")
    from infrastructure.persistence import legacy_db as dbmod
    try:
        dbmod._db_pool.close_all()
    except Exception:
        pass
    dbmod.DB_FILE = _saved
    dbmod._db_pool = dbmod.DatabasePool(_saved, min_size=2, max_size=10)
    os.environ.pop("TICKETS_DB_PATH", None)
    if _SAVED_DB_PATH is not None:
        os.environ["TICKETS_DB_PATH"] = _SAVED_DB_PATH


class TestSqliteTicketRepository:
    """测试工单仓储"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """每个测试前重建表"""
        from infrastructure.persistence.legacy_db import db_execute
        # 先清理
        for tbl in ["tickets", "history", "materials", "income_records",
                     "expense_records", "ticket_technicians", "ticket_service_items", "equipment",
                     "ticket_equipment", "todos", "_schema_version"]:
            try:
                db_execute(f"DROP TABLE IF EXISTS {tbl}")
            except Exception:
                pass
        # 建所有需要的基础表
        tables = [
            """CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_no TEXT, title TEXT, client TEXT, description TEXT,
                status TEXT DEFAULT 'open', priority TEXT DEFAULT 'M',
                assignee TEXT DEFAULT '', estimated_hours REAL DEFAULT 0,
                time_spent REAL DEFAULT 0, total REAL DEFAULT 0,
                total_labor REAL DEFAULT 0, total_material REAL DEFAULT 0,
                total_external REAL DEFAULT 0,
                billing_status TEXT DEFAULT 'unpaid',
                created_at TEXT, updated_at TEXT, closed_at TEXT,
                appointment_at TEXT, billing_model TEXT DEFAULT 'hourly',
                contact TEXT DEFAULT '', location TEXT DEFAULT '',
                service_type TEXT DEFAULT '', created_by TEXT DEFAULT '',
                travel_distance REAL DEFAULT 0, travel_rate REAL DEFAULT 0,
                discount_rate REAL DEFAULT 1, notes TEXT DEFAULT '',
                completion_date TEXT, service_date TEXT,
                project TEXT DEFAULT '', tax_included INTEGER DEFAULT 0,
                tax_rate REAL DEFAULT 0, tax_amount REAL DEFAULT 0,
                total_with_tax REAL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, action TEXT, note TEXT,
                operator TEXT, timestamp TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, name TEXT, product_name TEXT,
                product_id INTEGER, quantity REAL DEFAULT 1,
                unit_price REAL DEFAULT 0, total_cost REAL DEFAULT 0, total REAL DEFAULT 0,
                notes TEXT DEFAULT '', created_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS income_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT, source_id INTEGER, client TEXT,
                amount REAL, method TEXT, description TEXT, received_at TEXT,
                total_amount REAL DEFAULT 0,
                payment_method TEXT DEFAULT '微信',
                tax_amount REAL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS expense_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                related_ticket_id INTEGER, category TEXT,
                description TEXT, amount REAL, paid_at TEXT,
                vendor TEXT DEFAULT '', is_personal INTEGER DEFAULT 0,
                payment_type TEXT DEFAULT '', is_recurring INTEGER DEFAULT 0,
                receipt_no TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS ticket_technicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, technician_name TEXT,
                cost_rate REAL DEFAULT 30, hours REAL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS ticket_service_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, technician_name TEXT,
                service_fee_id INTEGER,
                hours REAL DEFAULT 0, unit_price REAL DEFAULT 0,
                cost_price REAL DEFAULT 0, line_total REAL DEFAULT 0,
                line_cost REAL DEFAULT 0, name TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS ticket_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, equipment_id INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, type TEXT, client TEXT, model TEXT,
                location TEXT, serial_no TEXT, warranty_expire TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, source_type TEXT, source_id INTEGER,
                done INTEGER DEFAULT 0, created_at TEXT
            )""",
        ]
        for sql in tables:
            db_execute(sql)
        yield
        # 清理
        db_execute("DELETE FROM tickets")
        db_execute("DELETE FROM history")
        db_execute("DELETE FROM materials")
        db_execute("DELETE FROM income_records")
        db_execute("DELETE FROM expense_records")
        db_execute("DELETE FROM ticket_technicians")
        db_execute("DELETE FROM ticket_equipment")

    def test_save_and_find(self):
        """测试创建和查询工单"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository

        repo = SqliteTicketRepository()

        # 创建
        ticket_id = repo.save({
            "ticket_no": "TEST-001",
            "client": "测试客户",
            "description": "测试工单内容",
            "priority": "M",
        })

        assert ticket_id > 0

        # 查询
        ticket = repo.find_by_id(ticket_id)
        assert ticket is not None
        assert ticket["client"] == "测试客户"
        assert ticket["description"] == "测试工单内容"
        assert ticket["status"] == "open"

    def test_update(self):
        """测试更新工单"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository

        repo = SqliteTicketRepository()
        ticket_id = repo.save({
            "ticket_no": "TEST-002",
            "client": "客户A",
            "description": "原始内容",
        })

        # 更新
        result = repo.update(ticket_id, {"description": "更新后的内容", "priority": "H"})
        assert result is True

        ticket = repo.find_by_id(ticket_id)
        assert ticket["description"] == "更新后的内容"
        assert ticket["priority"] == "H"

    def test_delete(self):
        """测试删除工单"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository

        repo = SqliteTicketRepository()
        ticket_id = repo.save({
            "ticket_no": "TEST-003",
            "client": "客户B",
            "description": "将被删除",
        })

        repo.delete(ticket_id)
        ticket = repo.find_by_id(ticket_id)
        assert ticket is None

    def test_find_list_with_filters(self):
        """测试列表查询 + 筛选"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository

        repo = SqliteTicketRepository()
        repo.save({"ticket_no": "T1", "client": "客户X", "status": "open"})
        repo.save({"ticket_no": "T2", "client": "客户Y", "status": "in-progress"})
        repo.save({"ticket_no": "T3", "client": "客户X", "status": "closed"})

        # 按状态筛选
        tickets, total = repo.find_list(filters={"status": "open"})
        assert total == 1
        assert tickets[0]["ticket_no"] == "T1"

        # 按客户筛选
        tickets, total = repo.find_list(filters={"client": "客户X"})
        assert total == 2

        # 多状态筛选
        tickets, total = repo.find_list(filters={"status": "open,closed"})
        assert total == 2

    def test_generate_ticket_no(self):
        """测试工单编号生成"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository

        repo = SqliteTicketRepository()
        # 先创建一条记录，让编号序列递增
        repo.save({"ticket_no": "PRE-001", "client": "C0", "description": "seed"})
        no1 = repo.generate_ticket_no()
        assert no1.startswith("GD-")
        assert len(no1) > 15

        # 再生成一次（两次在不同微秒，编号应不同）
        import time
        time.sleep(0.01)
        no2 = repo.generate_ticket_no()
        assert no2.startswith("GD-")
        # 只验证格式，不强制不同（时间相同时间可能相同）

    def test_status_stats(self):
        """测试状态统计"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository

        repo = SqliteTicketRepository()
        repo.save({"ticket_no": "S1", "client": "C1", "status": "open"})
        repo.save({"ticket_no": "S2", "client": "C2", "status": "open"})
        repo.save({"ticket_no": "S3", "client": "C3", "status": "in-progress"})

        stats = repo.get_status_stats()
        assert stats.get("open") == 2
        assert stats.get("in-progress") == 1


class TestTicketService:
    """测试工单应用服务"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前准备依赖"""
        from infrastructure.persistence.legacy_db import db_execute
        
        # 先清理
        for tbl in ["tickets", "history", "materials", "income_records",
                     "expense_records", "ticket_technicians", "ticket_service_items", "equipment",
                     "ticket_equipment", "_schema_version"]:
            try:
                db_execute(f"DROP TABLE IF EXISTS {tbl}")
            except Exception:
                pass

        tables = [
            """CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_no TEXT, title TEXT, client TEXT, description TEXT,
                status TEXT DEFAULT 'open', priority TEXT DEFAULT 'M',
                assignee TEXT DEFAULT '', estimated_hours REAL DEFAULT 0,
                time_spent REAL DEFAULT 0, total REAL DEFAULT 0,
                total_labor REAL DEFAULT 0, total_material REAL DEFAULT 0,
                total_external REAL DEFAULT 0,
                billing_status TEXT DEFAULT 'unpaid',
                created_at TEXT, updated_at TEXT, closed_at TEXT,
                appointment_at TEXT, billing_model TEXT DEFAULT 'hourly',
                contact TEXT DEFAULT '', location TEXT DEFAULT '',
                service_type TEXT DEFAULT '', created_by TEXT DEFAULT '',
                travel_distance REAL DEFAULT 0, travel_rate REAL DEFAULT 0,
                discount_rate REAL DEFAULT 1, notes TEXT DEFAULT '',
                completion_date TEXT, service_date TEXT,
                project TEXT DEFAULT '', tax_included INTEGER DEFAULT 0,
                tax_rate REAL DEFAULT 0, tax_amount REAL DEFAULT 0,
                total_with_tax REAL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, action TEXT, note TEXT,
                operator TEXT, timestamp TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, name TEXT, product_name TEXT,
                product_id INTEGER, quantity REAL DEFAULT 1,
                unit_price REAL DEFAULT 0, total_cost REAL DEFAULT 0, total REAL DEFAULT 0,
                notes TEXT DEFAULT '', created_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS income_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT, source_id INTEGER, client TEXT,
                amount REAL, method TEXT, description TEXT, received_at TEXT,
                total_amount REAL DEFAULT 0,
                payment_method TEXT DEFAULT '微信',
                tax_amount REAL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS expense_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                related_ticket_id INTEGER, category TEXT,
                description TEXT, amount REAL, paid_at TEXT,
                vendor TEXT DEFAULT '', is_personal INTEGER DEFAULT 0,
                payment_type TEXT DEFAULT '', is_recurring INTEGER DEFAULT 0,
                receipt_no TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS ticket_technicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, technician_name TEXT,
                cost_rate REAL DEFAULT 30, hours REAL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS ticket_service_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, technician_name TEXT,
                service_fee_id INTEGER,
                hours REAL DEFAULT 0, unit_price REAL DEFAULT 0,
                cost_price REAL DEFAULT 0, line_total REAL DEFAULT 0,
                line_cost REAL DEFAULT 0, name TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, type TEXT, client TEXT, model TEXT,
                location TEXT, serial_no TEXT, warranty_expire TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE, contact TEXT DEFAULT '', phone TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS ticket_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER, equipment_id INTEGER
            )""",
        ]
        for sql in tables:
            db_execute(sql)

    def test_create_ticket_with_event(self):
        """测试创建工单（含事件）"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository
        from domain.events import EventBus, TicketCreated
        from application.services.ticket_service import TicketService

        repo = SqliteTicketRepository()
        event_bus = EventBus()
        events = []

        @event_bus.register("ticket.created")
        def on_created(event: TicketCreated):
            events.append(event)

        svc = TicketService(repo=repo, event_bus=event_bus)

        ticket = svc.create_ticket({
            "client": "集宁一中",
            "content": "电脑无法开机",
            "assignee": "苏鹏",
        })

        assert ticket["id"] > 0
        assert ticket["client"] == "集宁一中"
        assert ticket["status"] == "open"
        assert ticket["ticket_no"].startswith("GD-")

        # 验证事件触发
        assert len(events) == 1
        assert events[0].ticket_id == ticket["id"]
        assert events[0].client == "集宁一中"

    def test_create_ticket_validation(self):
        """测试创建工单校验"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository
        from domain.exceptions import TicketValidationError
        from application.services.ticket_service import TicketService

        svc = TicketService(repo=SqliteTicketRepository())

        # 缺少客户
        with pytest.raises(TicketValidationError, match="客户名称不能为空"):
            svc.create_ticket({"content": "test"})

        # 缺少内容
        with pytest.raises(TicketValidationError, match="服务内容不能为空"):
            svc.create_ticket({"client": "C1"})

    def test_transition_status(self):
        """测试状态流转"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository
        from domain.events import EventBus, TicketStatusChanged
        from domain.exceptions import TicketValidationError
        from application.services.ticket_service import TicketService

        repo = SqliteTicketRepository()
        event_bus = EventBus()
        events = []

        @event_bus.register("ticket.status_changed")
        def on_changed(event: TicketStatusChanged):
            events.append(event)

        svc = TicketService(repo=repo, event_bus=event_bus)
        ticket = svc.create_ticket({"client": "C1", "content": "test"})

        # open → in-progress（add_technician 自动推进）
        svc.add_technician(ticket["id"], "测试技术员", cost_rate=50, hours=1)
        updated = svc._repo.find_by_id(ticket["id"])
        assert updated["status"] == "in-progress"

        # in-progress → pending-payment
        updated = svc.transition_status(ticket["id"], "pending-payment")
        assert updated["status"] == "pending-payment"

        # 验证事件（add_technician 自动推进 + transition 触发）
        assert len(events) >= 1

        # 非法流转
        with pytest.raises(TicketValidationError):
            svc.transition_status(ticket["id"], "open")  # 不能回退

    def test_list_tickets(self):
        """测试工单列表"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository
        from application.services.ticket_service import TicketService

        svc = TicketService(repo=SqliteTicketRepository())
        svc.create_ticket({"client": "C1", "content": "任务1"})
        svc.create_ticket({"client": "C2", "content": "任务2"})

        result = svc.list_tickets()
        assert result["total"] == 2
        assert len(result["tickets"]) == 2

        # 按客户筛选
        result = svc.list_tickets(client="C1")
        assert result["total"] == 1

    def test_confirm_payment(self):
        """测试收款"""
        from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository
        from domain.exceptions import TicketValidationError
        from application.services.ticket_service import TicketService

        repo = SqliteTicketRepository()
        svc = TicketService(repo=repo)
        ticket = svc.create_ticket({"client": "C1", "content": "test"})

        # 收款金额为 0 应拒绝
        with pytest.raises(TicketValidationError):
            svc.confirm_payment(ticket["id"], 0)

        # 无金额工单收款应报错（total=0，收款超出剩余应收）
        with pytest.raises(TicketValidationError, match="超出剩余应收"):
            svc.confirm_payment(ticket["id"], 100, method="微信")


class TestEventBus:
    """测试事件总线"""

    def test_register_and_dispatch(self):
        from domain.events import EventBus, TicketCreated

        bus = EventBus()
        received = []

        @bus.register("ticket.created")
        def handler(event: TicketCreated):
            received.append(event)

        bus.dispatch(TicketCreated(ticket_id=1, ticket_no="T1"))

        assert len(received) == 1
        assert received[0].ticket_id == 1

    def test_handler_isolation(self):
        """一个失败不应影响其他"""
        from domain.events import EventBus, TicketCreated

        bus = EventBus()
        results = []

        @bus.register("ticket.created")
        def handler1(event):
            raise ValueError("Handler 1 failed")

        @bus.register("ticket.created")
        def handler2(event):
            results.append("handler2 worked")

        bus.dispatch(TicketCreated(ticket_id=1, ticket_no="T1"))

        assert len(results) == 1
        assert results[0] == "handler2 worked"

    def test_no_handler(self):
        """没有处理器不应报错"""
        from domain.events import EventBus, TicketCreated
        bus = EventBus()
        bus.dispatch(TicketCreated(ticket_id=1, ticket_no="T1"))
        # Should not raise


class TestDI:
    """测试 DI 容器"""

    def test_register_and_resolve(self):
        from infrastructure.di.container import Container
        Container.reset()

        Container.register("greeter", lambda: "Hello")
        result = Container.resolve("greeter")
        assert result == "Hello"

    def test_singleton(self):
        from infrastructure.di.container import Container
        Container.reset()

        class Obj:
            pass

        Container.register("obj", lambda: Obj())
        o1 = Container.resolve("obj")
        o2 = Container.resolve("obj")
        assert o1 is o2

    def test_resolve_raises(self):
        from infrastructure.di.container import Container
        Container.reset()

        with pytest.raises(KeyError):
            Container.resolve("not_exists")

    def test_reset(self):
        from infrastructure.di.container import Container
        Container.reset()

        Container.register("x", lambda: 1)
        assert Container.has("x")

        Container.reset()
        assert not Container.has("x")

    def test_config(self):
        from infrastructure.di.container import Container
        Container.reset()

        Container.set_config("db_path", "/tmp/test.db")
        assert Container.get_config("db_path") == "/tmp/test.db"
        assert Container.get_config("not_set", "default") == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
