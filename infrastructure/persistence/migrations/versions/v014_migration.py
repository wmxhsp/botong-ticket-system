"""
博通 (Botong) — 数据库迁移 V14
内存状态持久化：幂等缓存表 + 工单计时字段
"""



def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_index, _raw_alter, _raw_execute
    _raw_execute("CREATE TABLE IF NOT EXISTS _idempotent_cache (key TEXT PRIMARY KEY, data TEXT NOT NULL, created_at REAL NOT NULL, expires_at REAL NOT NULL)")
    _raw_alter("tickets", "timer_started_at", "TEXT")
