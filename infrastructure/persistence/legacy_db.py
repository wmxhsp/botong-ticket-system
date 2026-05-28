# -*- coding: utf-8 -*-
"""
博通 (Botong) — 数据库兼容模块
提供与旧 lib.core.database 相同的快捷查询函数 API (db_query/db_query_one/db_execute 等)
所有文件统一从此模块导入，不再依赖 lib/
"""

import sqlite3
import os
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# 项目根目录
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB = str(_BASE_DIR / "tickets.db")
DB_FILE = os.environ.get("TICKETS_DB_PATH", DEFAULT_DB)


from domain.exceptions import DatabaseError


# ===== SQLite 连接池（线程安全） =====
class DatabasePool:
    """
    SQLite 连接池，复用连接以减少 open/close 开销。
    线程安全，自动回收异常连接，支持 WAL 模式。
    """
    def __init__(self, db_file: str, min_size: int = 2, max_size: int = 10):
        self.db_file = db_file
        self.max_size = max_size
        self._pool: list = []
        self._in_use = 0
        self._lock = threading.Lock()
        for _ in range(min_size):
            self._pool.append(self._create_connection())

    def _create_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_file, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    @contextmanager
    def get_connection(self):
        """获取连接，自动归还到池"""
        conn = None
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
            elif self._in_use < self.max_size:
                conn = self._create_connection()
                self._in_use += 1
            else:
                raise DatabaseError("数据库连接池已满，请稍后重试")
        try:
            yield conn
            with self._lock:
                self._pool.append(conn)
        except Exception:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            with self._lock:
                self._in_use = self._in_use - 1
            raise

    def close_all(self):
        """关闭所有连接（应用关闭时调用）"""
        with self._lock:
            while self._pool:
                try:
                    self._pool.pop().close()
                except Exception:
                    pass
            self._in_use = 0


# 全局连接池
_db_pool = DatabasePool(DB_FILE, min_size=2, max_size=10)


@contextmanager
def get_db():
    """
    获取数据库连接（上下文管理器，从连接池获取）
    用法:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM tickets")
            rows = cursor.fetchall()
    """
    with _db_pool.get_connection() as conn:
        try:
            yield conn
        except DatabaseError:
            raise
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise DatabaseError(f"数据库错误: {e}")


def db_execute(sql: str, params: tuple = ()) -> int:
    """
    执行 SQL（INSERT/UPDATE/DELETE）
    返回: 最后插入的行ID（INSERT）或影响的行数（UPDATE/DELETE）

    注意：不再临时关闭外键约束。对于全表删除（测试 teardown），
    应先清理子表再删除主表，或使用 repo.delete() 的级联删除逻辑。
    """
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid or cursor.rowcount


def db_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    查询多条数据
    返回: 字典列表
    """
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def db_query_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """
    查询单条数据
    返回: 字典或 None
    """
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def log_audit(action: str, table_name: str, record_id: int = None,
              old_data: dict = None, new_data: dict = None,
              operator: str = None, ip_address: str = None):
    """
    记录审计日志
    """
    import json
    try:
        db_execute(
            "INSERT INTO audit_log (action, table_name, record_id, old_data, new_data, operator, ip_address) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (action, table_name, record_id,
             json.dumps(old_data, ensure_ascii=False) if old_data else None,
             json.dumps(new_data, ensure_ascii=False) if new_data else None,
             operator or "system", ip_address)
        )
    except Exception:
        pass  # 审计失败不影响主流程


@contextmanager
def db_transaction():
    """
    事务上下文管理器
    用法:
        with db_transaction() as conn:
            conn.execute("INSERT INTO ...")
    """
    with get_db() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# ===== 迁移辅助函数（供 versions/v*_migration.py 调用） =====

def _safe_alter(table, column, ddl):
    """安全 ALTER TABLE，忽略列已存在错误"""
    try:
        db_execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
    except Exception:
        pass


def _safe_index(sql_list):
    """安全创建索引，忽略已存在错误"""
    for sql in sql_list:
        try:
            db_execute(sql)
        except Exception:
            pass


def _raw_alter(table, column, ddl):
    """直接 ALTER TABLE，用于迁移中绕过连接池"""
    import sqlite3 as _sqlite3
    _conn = _sqlite3.connect(DB_FILE)
    try:
        _conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        _conn.commit()
    except Exception:
        pass
    _conn.close()


def _raw_execute(sql, params=()):
    """直接执行 SQL，用于迁移中绕过连接池"""
    import sqlite3 as _sqlite3
    _conn = _sqlite3.connect(DB_FILE)
    try:
        _conn.execute(sql, params)
        _conn.commit()
    except Exception:
        pass
    _conn.close()


def init_indexes():
    """初始化数据库索引和表（容错模式）"""
    # 启用 WAL 模式
    try:
        _conn = sqlite3.connect(DB_FILE)
        _conn.execute("PRAGMA journal_mode = WAL")
        _conn.close()
    except Exception:
        pass

    # 确保基础表存在（全量重建场景）
    _ensure_foundation_tables()

    # 维保报告表
    db_execute("""
        CREATE TABLE IF NOT EXISTS maintenance_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            report_type TEXT NOT NULL,
            title TEXT,
            period TEXT,
            generated_at TEXT,
            cloud_url TEXT,
            cloud_filename TEXT,
            archived_at TEXT,
            notified INTEGER DEFAULT 0,
            signed INTEGER DEFAULT 0,
            signed_at TEXT,
            notes TEXT
        )
    """)
    # 销售记录表
    db_execute("""
        CREATE TABLE IF NOT EXISTS sales_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            product_id INTEGER,
            product_name TEXT,
            product_type TEXT DEFAULT '月卡',
            quantity REAL DEFAULT 1,
            batch_size INTEGER DEFAULT 1,
            unit_price REAL DEFAULT 0,
            cost_price REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            payment_method TEXT DEFAULT '微信',
            status TEXT DEFAULT 'unpaid',
            notes TEXT,
            expires_at TEXT,
            validity_days INTEGER DEFAULT 30,
            discount_type TEXT DEFAULT '',
            discount_value REAL DEFAULT 0,
            ticket_id INTEGER REFERENCES tickets(id),
            created_at TEXT DEFAULT (datetime('now','localtime')),
            paid_at TEXT
        )
    """)
    # 列迁移
    for tbl, col, ddl in [
        ("inventory_items", "purchase_order_id", "INTEGER"),
        ("inventory_items", "unit_cost", "REAL DEFAULT 0"),
        ("inventory_items", "received_at", "TEXT"),
        ("inventory_items", "sale_id", "INTEGER"),
        ("equipment", "maintenance_cycle", "TEXT DEFAULT ''"),
        ("equipment", "last_maintenance", "TEXT DEFAULT ''"),
        ("equipment", "next_maintenance", "TEXT DEFAULT ''"),
        ("equipment", "is_deleted", "INTEGER DEFAULT 0"),
        # tickets 补齐常见迁移列（兼容旧 DB）
        ("tickets", "service_fee_id", "INTEGER"),
        ("tickets", "discount_type", "TEXT DEFAULT ''"),
        ("tickets", "discount_value", "REAL DEFAULT 0"),
        ("tickets", "discount_rate", "REAL DEFAULT 1"),
        ("tickets", "tax_rate", "REAL DEFAULT 0"),
        ("tickets", "tax_amount", "REAL DEFAULT 0"),
        ("tickets", "total_with_tax", "REAL DEFAULT 0"),
        # 收支记录表常见缺失列
        ("expense_records", "created_at", "TEXT DEFAULT (datetime('now','localtime'))"),
        ("income_records", "client", "TEXT DEFAULT ''"),
    ]:
        try:
            db_execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {ddl}")
        except Exception:
            pass

    # 供应商表
    db_execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            bank_name TEXT DEFAULT '',
            bank_account TEXT DEFAULT '',
            payment_terms INTEGER DEFAULT 30,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # 工单多负责人关联表
    db_execute("""
        CREATE TABLE IF NOT EXISTS ticket_technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            technician_name TEXT NOT NULL,
            cost_rate REAL DEFAULT 30,
            hours REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(ticket_id, technician_name)
        )
    """)

    indexes = [
        ("idx_tickets_client", "CREATE INDEX IF NOT EXISTS idx_tickets_client ON tickets(client)"),
        ("idx_tickets_status", "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)"),
        ("idx_tickets_created", "CREATE INDEX IF NOT EXISTS idx_tickets_created ON tickets(created_at)"),
        ("idx_tickets_billing", "CREATE INDEX IF NOT EXISTS idx_tickets_billing ON tickets(billing_status)"),
        ("idx_tickets_closed", "CREATE INDEX IF NOT EXISTS idx_tickets_closed ON tickets(closed_at)"),
        ("idx_tickets_assignee", "CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON tickets(assignee)"),
        ("idx_staff_ticket", "CREATE INDEX IF NOT EXISTS idx_staff_ticket ON staff(ticket_id)"),
        ("idx_materials_ticket", "CREATE INDEX IF NOT EXISTS idx_materials_ticket ON materials(ticket_id)"),
        ("idx_history_ticket", "CREATE INDEX IF NOT EXISTS idx_history_ticket ON history(ticket_id)"),
        ("idx_work_items_ticket", "CREATE INDEX IF NOT EXISTS idx_work_items_ticket ON work_items(ticket_id)"),
        ("idx_ticket_tags_ticket", "CREATE INDEX IF NOT EXISTS idx_ticket_tags_ticket ON ticket_tags(ticket_id)"),
        ("idx_ticket_approvals_ticket", "CREATE INDEX IF NOT EXISTS idx_ticket_approvals_ticket ON ticket_approvals(ticket_id)"),
        ("idx_related_tickets_src", "CREATE INDEX IF NOT EXISTS idx_related_tickets_src ON related_tickets(source_ticket_id)"),
        ("idx_related_tickets_dst", "CREATE INDEX IF NOT EXISTS idx_related_tickets_dst ON related_tickets(target_ticket_id)"),
        ("idx_income_source", "CREATE INDEX IF NOT EXISTS idx_income_source ON income_records(source_type, source_id)"),
        ("idx_income_client", "CREATE INDEX IF NOT EXISTS idx_income_client ON income_records(client)"),
        ("idx_income_received", "CREATE INDEX IF NOT EXISTS idx_income_received ON income_records(received_at)"),
        ("idx_expense_date", "CREATE INDEX IF NOT EXISTS idx_expense_date ON expense_records(paid_at)"),
        ("idx_expense_category", "CREATE INDEX IF NOT EXISTS idx_expense_category ON expense_records(category)"),
        ("idx_inventory_product", "CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory_items(product_id)"),
        ("idx_inventory_status", "CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory_items(status)"),
        ("idx_inventory_ticket", "CREATE INDEX IF NOT EXISTS idx_inventory_ticket ON inventory_items(ticket_id)"),
        ("idx_inspection_plans_agreement", "CREATE INDEX IF NOT EXISTS idx_inspection_plans_agreement ON inspection_plans(agreement_id)"),
        ("idx_inspection_records_plan", "CREATE INDEX IF NOT EXISTS idx_inspection_records_plan ON inspection_records(plan_id)"),
        ("idx_inspection_records_date", "CREATE INDEX IF NOT EXISTS idx_inspection_records_date ON inspection_records(executed_at)"),
        ("idx_equipment_client", "CREATE INDEX IF NOT EXISTS idx_equipment_client ON equipment(client)"),
        ("idx_equipment_components_eq", "CREATE INDEX IF NOT EXISTS idx_equipment_components_eq ON equipment_components(equipment_id)"),
        ("idx_agreement_client", "CREATE INDEX IF NOT EXISTS idx_agreement_client ON service_agreements(client)"),
        ("idx_agreement_status", "CREATE INDEX IF NOT EXISTS idx_agreement_status ON service_agreements(status)"),
        ("idx_audit_action", "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)"),
        ("idx_audit_table", "CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name)"),
        ("idx_audit_created", "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at)"),
        ("idx_po_status", "CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status)"),
        ("idx_po_vendor", "CREATE INDEX IF NOT EXISTS idx_po_vendor ON purchase_orders(vendor)"),
        ("idx_po_date", "CREATE INDEX IF NOT EXISTS idx_po_date ON purchase_orders(purchase_date)"),
        ("idx_ticket_tech", "CREATE INDEX IF NOT EXISTS idx_ticket_tech ON ticket_technicians(ticket_id)"),
    ]
    for name, sql in indexes:
        try:
            db_execute(sql)
        except Exception:
            pass

    _init_schema_version()


def _ensure_foundation_tables():
    """确保基础表存在（全量重建时使用）"""
    # 工单主表
    db_execute("""CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_no TEXT UNIQUE NOT NULL,
        client TEXT NOT NULL DEFAULT '',
        contact TEXT DEFAULT '',
        location TEXT DEFAULT '',
        service_type TEXT DEFAULT '',
        priority TEXT DEFAULT 'M',
        status TEXT DEFAULT 'open',
        description TEXT DEFAULT '',
        title TEXT DEFAULT '',
        assignee TEXT DEFAULT '',
        created_by TEXT DEFAULT '',
        estimated_hours REAL DEFAULT 0,
        time_spent REAL DEFAULT 0,
        total_labor REAL DEFAULT 0,
        total_external REAL DEFAULT 0,
        total_material REAL DEFAULT 0,
        total REAL DEFAULT 0,
        billing_status TEXT DEFAULT 'unpaid',
        billing_model TEXT DEFAULT 'hourly',
        notes TEXT DEFAULT '',
        project TEXT DEFAULT '',
        service_fee_id INTEGER,
        is_renewal INTEGER DEFAULT 0,
        tax_included INTEGER DEFAULT 0,
        tax_rate REAL DEFAULT 0,
        tax_amount REAL DEFAULT 0,
        total_with_tax REAL DEFAULT 0,
        discount_type TEXT DEFAULT '',
        discount_value REAL DEFAULT 0,
        discount_rate REAL DEFAULT 1,
        appointment_at TEXT,
        travel_distance REAL DEFAULT 0,
        travel_rate REAL DEFAULT 0,
        completion_date TEXT,
        service_date TEXT,
        timer_started_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime')),
        closed_at TEXT
    )""")
    # 操作历史
    db_execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER REFERENCES tickets(id),
        action TEXT NOT NULL DEFAULT '',
        note TEXT DEFAULT '',
        operator TEXT DEFAULT 'system',
        changes TEXT DEFAULT '',
        timestamp TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 物料
    db_execute("""CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER REFERENCES tickets(id),
        name TEXT NOT NULL DEFAULT '',
        quantity REAL DEFAULT 1,
        unit_price REAL DEFAULT 0,
        total REAL DEFAULT 0,
        total_cost REAL DEFAULT 0,
        product_name TEXT DEFAULT '',
        product_id INTEGER,
        notes TEXT DEFAULT '',
        inventory_item_ids TEXT DEFAULT '',
        goods_id INTEGER,
        sale_id INTEGER,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 客户表
    db_execute("""CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        address TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        payment_terms INTEGER DEFAULT 30,
        billing_address TEXT DEFAULT '',
        hourly_rate REAL DEFAULT 0,
        annual_rate REAL DEFAULT 0,
        client_type TEXT DEFAULT '',
        scope TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 收入记录
    db_execute("""CREATE TABLE IF NOT EXISTS income_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT DEFAULT '',
        source_id INTEGER,
        amount REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        method TEXT DEFAULT 'pending',
        description TEXT DEFAULT '',
        payment_method TEXT DEFAULT '',
        tax_amount REAL DEFAULT 0,
        received_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 支出记录
    db_execute("""CREATE TABLE IF NOT EXISTS expense_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        related_ticket_id INTEGER,
        category TEXT DEFAULT '',
        description TEXT DEFAULT '',
        vendor TEXT DEFAULT '',
        amount REAL DEFAULT 0,
        paid_at TEXT,
        is_personal INTEGER DEFAULT 0,
        payment_type TEXT DEFAULT '',
        is_recurring INTEGER DEFAULT 0,
        receipt_no TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 设备表
    db_execute("""CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL DEFAULT '',
        client_name TEXT DEFAULT '',
        client TEXT DEFAULT '',
        brand TEXT DEFAULT '',
        model TEXT DEFAULT '',
        type TEXT DEFAULT '',
        serial_no TEXT DEFAULT '',
        location TEXT DEFAULT '',
        status TEXT DEFAULT '正常',
        warranty_expire TEXT,
        install_date TEXT,
        notes TEXT DEFAULT '',
        is_deleted INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 商品表
    db_execute("""CREATE TABLE IF NOT EXISTS goods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        type_id INTEGER,
        unit TEXT DEFAULT '个',
        sku TEXT DEFAULT '',
        retail_price REAL DEFAULT 0,
        selling_price REAL DEFAULT 0,
        cost_price REAL DEFAULT 0,
        supplier TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        min_stock INTEGER DEFAULT 2,
        is_subscription INTEGER DEFAULT 0,
        billing_cycle TEXT DEFAULT 'monthly',
        billing_price REAL DEFAULT 0,
        sale_mode TEXT DEFAULT 'both',
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 设备关联表
    db_execute("""CREATE TABLE IF NOT EXISTS ticket_equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER REFERENCES tickets(id),
        equipment_id INTEGER REFERENCES equipment(id)
    )""")
    # 照片表
    db_execute("""CREATE TABLE IF NOT EXISTS ticket_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER REFERENCES tickets(id),
        filename TEXT DEFAULT '',
        url TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 库存明细表
    db_execute("""CREATE TABLE IF NOT EXISTS inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER REFERENCES goods(id),
        serial_no TEXT DEFAULT '',
        batch_no TEXT DEFAULT '',
        bulk_quantity REAL DEFAULT 1,
        location TEXT DEFAULT '库房',
        status TEXT DEFAULT 'in_stock',
        purchase_order_id INTEGER,
        unit_cost REAL DEFAULT 0,
        received_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        ticket_id INTEGER REFERENCES tickets(id),
        sale_id INTEGER,
        warehouse_id INTEGER REFERENCES warehouses(id),
        notes TEXT DEFAULT ''
    )""")
    # 库存流水表
    db_execute("""CREATE TABLE IF NOT EXISTS inventory_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER REFERENCES goods(id),
        item_id INTEGER,
        type TEXT DEFAULT '',
        quantity REAL DEFAULT 0,
        from_location TEXT DEFAULT '',
        to_location TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 商品分类表
    db_execute("""CREATE TABLE IF NOT EXISTS goods_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT 'bi-tag',
        sort_order INTEGER DEFAULT 99,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS goods_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER REFERENCES goods_categories(id),
        name TEXT NOT NULL,
        sort_order INTEGER DEFAULT 99,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 工单模板表
    db_execute("""CREATE TABLE IF NOT EXISTS ticket_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        content TEXT DEFAULT '',
        client TEXT DEFAULT '',
        category TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 99,
        service_type TEXT DEFAULT '',
        priority TEXT DEFAULT 'M',
        billing_model TEXT DEFAULT 'hourly',
        estimated_hours REAL DEFAULT 0,
        description_template TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 自动化规则表
    db_execute("""CREATE TABLE IF NOT EXISTS automation_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        trigger_event TEXT DEFAULT '',
        conditions TEXT DEFAULT '{}',
        actions TEXT DEFAULT '[]',
        is_active INTEGER DEFAULT 1,
        enabled INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 50,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 技术人员表
    db_execute("""CREATE TABLE IF NOT EXISTS technicians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT DEFAULT '',
        skills TEXT DEFAULT '',
        cost_rate REAL DEFAULT 30,
        status TEXT DEFAULT 'active',
        labor_cost REAL DEFAULT 0,
        labor_revenue REAL DEFAULT 0,
        profit_contribution REAL DEFAULT 0,
        ticket_count INTEGER DEFAULT 0,
        total_hours REAL DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 服务协议表
    db_execute("""CREATE TABLE IF NOT EXISTS service_agreements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agreement_no TEXT UNIQUE,
        client TEXT NOT NULL DEFAULT '',
        amount REAL DEFAULT 0,
        paid_amount REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        paid_at TEXT,
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 巡检计划表
    db_execute("""CREATE TABLE IF NOT EXISTS inspection_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agreement_id INTEGER REFERENCES service_agreements(id),
        client TEXT DEFAULT '',
        plan_name TEXT DEFAULT '',
        plan_type TEXT DEFAULT '巡检',
        frequency TEXT DEFAULT 'monthly',
        status TEXT DEFAULT 'active',
        next_execution TEXT,
        updated_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 巡检记录表
    db_execute("""CREATE TABLE IF NOT EXISTS inspection_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER REFERENCES inspection_plans(id),
        ticket_id INTEGER REFERENCES tickets(id),
        executed_at TEXT DEFAULT '',
        result TEXT DEFAULT '待执行',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 采购订单表
    db_execute("""CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_no TEXT UNIQUE,
        vendor TEXT DEFAULT '',
        supplier_id INTEGER REFERENCES suppliers(id),
        purchase_date TEXT DEFAULT '',
        status TEXT DEFAULT 'pending',
        notes TEXT DEFAULT '',
        total_amount REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'unpaid',
        payment_method TEXT DEFAULT '',
        paid_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 采购明细表
    db_execute("""CREATE TABLE IF NOT EXISTS purchase_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_id INTEGER REFERENCES purchase_orders(id),
        goods_id INTEGER REFERENCES goods(id),
        goods_name TEXT DEFAULT '',
        quantity REAL DEFAULT 0,
        unit_cost REAL DEFAULT 0,
        total_cost REAL DEFAULT 0,
        received_qty REAL DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    # 设备组件表
    db_execute("""CREATE TABLE IF NOT EXISTS equipment_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER REFERENCES equipment(id),
        name TEXT DEFAULT '',
        spec TEXT DEFAULT '',
        count INTEGER DEFAULT 1
    )""")


# ===== 数据库 Schema 版本管理 =====
_SCHEMA_VERSION = 23


def _init_schema_version():
    """初始化 schema_version 表，检查版本"""
    db_execute("""
        CREATE TABLE IF NOT EXISTS _schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT DEFAULT (datetime('now','localtime')),
            description TEXT
        )
    """)
    current = db_query_one("SELECT MAX(version) as v FROM _schema_version")
    ver = current["v"] if current and current["v"] is not None else 0
    if ver < _SCHEMA_VERSION:
        _run_migrations(ver)


def _run_migrations(from_version):
    """执行待处理的迁移 — 委托给独立迁移文件"""
    import importlib
    migrations = {
        2: "预约时间 + 提醒系统",
        3: "仓库管理 + 库存多仓库",
        4: "待办事项模块",
        5: "供应商应付款 + 客户账期 + 对账单",
        6: "待办事项V2：子任务+重复+关联+提醒",
        7: "通知溯源字段",
        8: "旧架构缺失列补齐(project/service_fee_id/收支明细列)",
        9: "V8 补全：materials.total + history.by",
        10: "todos 表补全：category/priority/due_date/sort_order 等 V4 列",
        11: "materials 表补全 inventory_item_ids/goods_id/sale_id",
        12: "统一 income_records 字段(method/amount/total_amount)",
        13: "客户表费率字段 + rates.json 导入",
        14: "内存状态持久化：幂等缓存表 + 工单计时字段",
        15: "工单服务明细行 (ticket_service_items)",
        16: "技术人员计费方式 + 销售销售人员",
        17: "销售记录优惠折扣字段补全",
        18: "推断表补建DDL(purchase_orders/purchase_items/equipment_components)",
        19: "列名对齐：income_records.client + goods.is_bulk/max_stock + sales_records.renew_from + 缺失表补建",
        20: "tickets.parts_fee 配件费字段",
        21: "ticket_no NOT NULL约束 + NULL编号数据修复",
        22: "技术人员天薪/包工成本率字段(daily_rate/package_rate/daily_cost_rate/package_cost)",
        23: "性能优化：复合索引+部分索引+审计归档表+幂等缓存过期索引",
    }
    for v in range(from_version + 1, _SCHEMA_VERSION + 1):
        if v in migrations:
            desc = migrations[v]
            try:
                mod_name = f"infrastructure.persistence.migrations.versions.v{v:03d}_migration"
                mod = importlib.import_module(mod_name)
                mod.upgrade()
                db_execute("INSERT INTO _schema_version (version, description) VALUES (?, ?)", (v, desc))
                print(f"[DB Migration] V{v} ✓ {desc}")
            except Exception as e:
                print(f"[DB Migration] V{v} failed: {e}")
        else:
            try:
                db_execute("INSERT OR IGNORE INTO _schema_version (version, description) VALUES (?, ?)", (v, "初始基准版本"))
            except Exception:
                pass


def maintain_indexes():
    """维护数据库索引性能"""
    with get_db() as conn:
        conn.execute("ANALYZE")
        conn.execute("REINDEX")
    return True


def maintain_vacuum():
    """
    定期执行 VACUUM，收缩 WAL 模式数据库文件体积。
    WAL 模式下 VACUUM 需要无活跃读事务，先执行 checkpoint 再 VACUUM。
    """
    import threading
    import time as _time

    def _vacuum_bg():
        _time.sleep(5)
        try:
            # 先 checkpoint 收缩 WAL 文件
            with get_db() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            # 再 VACUUM 收缩主数据库文件
            with get_db() as conn:
                conn.execute("VACUUM")
            print("[DB] VACUUM 完成，数据库文件已收缩")
        except Exception as e:
            print(f"[DB] VACUUM 失败（可能存在活跃事务）: {e}")

    t = threading.Thread(target=_vacuum_bg, daemon=True)
    t.start()
    return t


def run_maintenance():
    """
    执行定期维护任务（建议每天/每周调用一次）。
    1. 清理过期幂等缓存
    2. 归档90天以上的审计日志
    3. ANALYZE 更新统计信息
    4. WAL checkpoint 收缩日志文件
    """
    import time as _time
    now_ts = _time.time()

    # 1. 清理过期幂等缓存
    try:
        db_execute("DELETE FROM _idempotent_cache WHERE expires_at < ?", (now_ts,))
        print("[DB] 过期幂等缓存已清理")
    except Exception as e:
        print(f"[DB] 清理幂等缓存失败: {e}")

    # 2. 归档审计日志（90天以上）
    try:
        cutoff = "datetime('now', '-90 days')"
        archived = db_execute(
            f"INSERT INTO audit_log_archive (id, action, table_name, record_id, old_data, new_data, operator, ip_address, created_at) "
            f"SELECT id, action, table_name, record_id, old_data, new_data, operator, ip_address, created_at "
            f"FROM audit_log WHERE created_at < {cutoff}"
        )
        db_execute(f"DELETE FROM audit_log WHERE created_at < {cutoff}")
        print(f"[DB] 审计日志归档完成，影响 {archived} 条")
    except Exception as e:
        print(f"[DB] 审计日志归档失败: {e}")

    # 3. ANALYZE 更新统计信息
    try:
        with get_db() as conn:
            conn.execute("ANALYZE")
        print("[DB] ANALYZE 完成")
    except Exception as e:
        print(f"[DB] ANALYZE 失败: {e}")

    # 4. WAL checkpoint
    try:
        with get_db() as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        print("[DB] WAL checkpoint 完成")
    except Exception as e:
        print(f"[DB] WAL checkpoint 失败: {e}")


# 在模块导入时确保基础表与索引存在，便于测试/运行环境自动就绪
try:
    init_indexes()
except Exception:
    pass

# 兼容性补丁：如果旧数据库因迁移未执行导致缺少关键列，尝试补齐
try:
    _safe_alter("tickets", "service_fee_id", "INTEGER")
except Exception:
    pass
try:
    _safe_alter("expense_records", "created_at", "TEXT")
except Exception:
    pass


