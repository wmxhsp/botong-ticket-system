"""
博通 (Botong) — 数据库迁移 V11
materials 表补全 inventory_item_ids/goods_id/sale_id
"""



def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_index, _raw_alter
    for col, ddl in [
        ("inventory_item_ids", "TEXT DEFAULT ''"),
        ("goods_id", "INTEGER"),
        ("sale_id", "INTEGER"),
    ]:
        _raw_alter("materials", col, ddl)
    for col, ddl in [
        ("discount_type", "TEXT DEFAULT ''"),
        ("discount_value", "REAL DEFAULT 0"),
    ]:
        _raw_alter("tickets", col, ddl)
