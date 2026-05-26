"""
博通 (Botong) — 数据库迁移 V17
销售记录优惠折扣字段补全
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter, _safe_index, db_execute
    _safe_alter("sales_records", "discount_type", "TEXT DEFAULT ''")
    _safe_alter("sales_records", "discount_value", "REAL DEFAULT 0")
    _safe_alter("ticket_service_items", "name", "TEXT DEFAULT ''")
