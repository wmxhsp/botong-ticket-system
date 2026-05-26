"""
博通 (Botong) — 数据库迁移 V9
V8 补全：materials.total + history.by
"""



def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_index, _raw_alter
    _raw_alter("materials", "total", "REAL DEFAULT 0")
    _raw_alter("history", "by", "TEXT DEFAULT ''")
    _raw_alter("history", "changes", "TEXT DEFAULT ''")
    _raw_alter("income_records", "created_at", "TEXT")
    _raw_alter("expense_records", "created_at", "TEXT")
