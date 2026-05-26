"""
博通 (Botong) — 数据库迁移 V19
列名对齐：income_records.client + goods.is_bulk/max_stock + sales_records.renew_from + 缺失表补建
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter, _safe_index, db_execute
    _safe_alter("income_records", "client", "TEXT DEFAULT ''")
    _safe_alter("goods", "is_bulk", "INTEGER DEFAULT 0")
    _safe_alter("goods", "max_stock", "INTEGER DEFAULT 0")
    _safe_alter("sales_records", "renew_from", "INTEGER")
    _safe_alter("ticket_equipment", "equipment_name", "TEXT DEFAULT ''")
    _safe_alter("ticket_equipment", "created_at", "TEXT DEFAULT (datetime('now','localtime'))")
    db_execute("""CREATE TABLE IF NOT EXISTS maintenance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL REFERENCES equipment(id),
        type TEXT DEFAULT '',
        description TEXT DEFAULT '',
        cost REAL DEFAULT 0,
        performed_at TEXT,
        performed_by TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS equipment_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL REFERENCES equipment(id),
        url TEXT NOT NULL,
        filename TEXT DEFAULT '',
        is_primary INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        warehouse_id INTEGER REFERENCES warehouses(id),
        description TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS expense_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type TEXT DEFAULT 'business',
        budget REAL DEFAULT 0,
        icon TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS expense_budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER REFERENCES expense_categories(id),
        period TEXT DEFAULT '',
        amount REAL DEFAULT 0,
        spent REAL DEFAULT 0
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        table_name TEXT NOT NULL,
        record_id INTEGER,
        old_data TEXT,
        new_data TEXT,
        operator TEXT DEFAULT 'system',
        ip_address TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
