"""
博通 (Botong) — 数据库迁移 V4
待办事项模块
"""



def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_index
    db_execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT DEFAULT '',
            category    TEXT NOT NULL DEFAULT 'work',
            priority    TEXT NOT NULL DEFAULT 'M',
            due_date    TEXT,
            due_time    TEXT,
            done        INTEGER DEFAULT 0,
            done_at     TEXT,
            sort_order  INTEGER DEFAULT 0,
            tags        TEXT DEFAULT '',
            remind      INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            updated_at  TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_todos_category ON todos(category)",
        "CREATE INDEX IF NOT EXISTS idx_todos_done ON todos(done)",
        "CREATE INDEX IF NOT EXISTS idx_todos_due_date ON todos(due_date)",
    ])
