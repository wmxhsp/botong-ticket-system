"""
博通 (Botong) — 数据库迁移 V6
待办事项V2：子任务+重复+关联+提醒
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter, _safe_index, db_execute
    _safe_alter("todos", "parent_id", "INTEGER REFERENCES todos(id)")
    _safe_alter("todos", "source_type", "TEXT DEFAULT ''")
    _safe_alter("todos", "source_id", "INTEGER")
    _safe_alter("todos", "repeat_rule", "TEXT DEFAULT ''")
    _safe_alter("todos", "repeat_parent_id", "INTEGER REFERENCES todos(id)")
    _safe_alter("todos", "reminder_at", "TEXT")
    _safe_alter("todos", "estimated_minutes", "INTEGER")
    _safe_alter("todos", "completed_count", "INTEGER DEFAULT 0")
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_todos_parent ON todos(parent_id)",
        "CREATE INDEX IF NOT EXISTS idx_todos_source ON todos(source_type, source_id)",
        "CREATE INDEX IF NOT EXISTS idx_todos_reminder_at ON todos(reminder_at)",
    ])
