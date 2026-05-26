"""
博通 (Botong) — 数据库迁移 V3
仓库管理 + 库存多仓库
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _safe_index, db_execute, db_query, db_query_one
    db_execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            address TEXT DEFAULT '',
            manager TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 99,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    locations = db_query("SELECT DISTINCT location FROM inventory_items WHERE location != ''")
    existing_names = [r['name'] for r in db_query("SELECT name FROM warehouses")]
    for row in locations:
        if row['location'] not in existing_names:
            db_execute("INSERT OR IGNORE INTO warehouses (name) VALUES (?)", (row['location'],))
    if '库房' not in existing_names and '库房' not in [r['location'] for r in locations]:
        db_execute("INSERT OR IGNORE INTO warehouses (name) VALUES ('库房')")
    try:
        db_execute("ALTER TABLE inventory_items ADD COLUMN warehouse_id INTEGER REFERENCES warehouses(id)")
    except Exception:
        pass
    for row in db_query("SELECT id, location FROM inventory_items WHERE warehouse_id IS NULL AND location != ''"):
        w = db_query_one("SELECT id FROM warehouses WHERE name = ?", (row['location'],))
        if w:
            db_execute("UPDATE inventory_items SET warehouse_id = ? WHERE id = ?", (w['id'], row['id']))
    default_w = db_query_one("SELECT id FROM warehouses WHERE name = '库房'")
    if default_w:
        db_execute("UPDATE inventory_items SET warehouse_id = ? WHERE warehouse_id IS NULL", (default_w['id'],))
    _safe_index(["CREATE INDEX IF NOT EXISTS idx_inv_warehouse ON inventory_items(warehouse_id)"])
