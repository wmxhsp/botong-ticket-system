"""
博通 (Botong) — 数据库迁移 V18
推断表补建DDL(purchase_orders/purchase_items/equipment_components)
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _ensure_foundation_tables
