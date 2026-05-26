"""
博通 (Botong) — 数据库迁移 V15
工单服务明细行 (ticket_service_items)
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _raw_execute, _safe_alter, _safe_index, db_execute
    _safe_alter("tickets", "total_external", "REAL DEFAULT 0")
    # service_fees 表若不存在则创建（原始schema缺失时的补全）
    _raw_execute("""CREATE TABLE IF NOT EXISTS service_fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        fee_type TEXT NOT NULL DEFAULT 'hourly',
        unit_price REAL DEFAULT 0,
        cost_price REAL DEFAULT 0,
        description TEXT DEFAULT '',
        active INTEGER DEFAULT 1,
        usage_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT
    )""")
    _raw_execute("""CREATE TABLE IF NOT EXISTS ticket_service_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        technician_name TEXT NOT NULL DEFAULT '',
        service_fee_id INTEGER,
        hours REAL DEFAULT 0,
        unit_price REAL DEFAULT 0,
        cost_price REAL DEFAULT 0,
        line_total REAL DEFAULT 0,
        line_cost REAL DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_service_items_ticket ON ticket_service_items(ticket_id)",
    ])
