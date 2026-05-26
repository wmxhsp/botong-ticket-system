"""
博通 (Botong) — 数据库迁移 V20
tickets.parts_fee 配件费字段
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter, _safe_index, db_execute
    _safe_alter("tickets", "parts_fee", "REAL DEFAULT 0")
