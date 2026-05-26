"""
博通 (Botong) — 数据库迁移 V10
todos 表补全：category/priority/due_date/sort_order 等 V4 列
"""



def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_index, _raw_alter
    for col, ddl in [
        ("description", "TEXT DEFAULT ''"),
        ("category", "TEXT NOT NULL DEFAULT 'work'"),
        ("priority", "TEXT NOT NULL DEFAULT 'M'"),
        ("due_date", "TEXT"),
        ("due_time", "TEXT"),
        ("done_at", "TEXT"),
        ("sort_order", "INTEGER DEFAULT 0"),
        ("tags", "TEXT DEFAULT ''"),
        ("remind", "INTEGER DEFAULT 0"),
        ("updated_at", "TEXT DEFAULT (datetime('now','localtime'))"),
    ]:
        _raw_alter("todos", col, ddl)
    _raw_alter("expense_records", "created_at", "TEXT")
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_todos_category ON todos(category)",
        "CREATE INDEX IF NOT EXISTS idx_todos_done ON todos(done)",
        "CREATE INDEX IF NOT EXISTS idx_todos_due_date ON todos(due_date)",
    ])
