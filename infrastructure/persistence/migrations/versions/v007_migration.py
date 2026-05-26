"""
博通 (Botong) — 数据库迁移 V7
通知溯源字段
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter, _safe_index, db_execute
    _safe_alter("notifications", "source_type", "TEXT DEFAULT ''")
    _safe_alter("notifications", "source_id", "INTEGER")
    _safe_index(["CREATE INDEX IF NOT EXISTS idx_notifications_source ON notifications(source_type, source_id)"])
