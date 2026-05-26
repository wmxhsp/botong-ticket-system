"""
博通 (Botong) — 数据库迁移 V16
技术人员计费方式 + 销售销售人员
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter, _safe_index, db_execute
    _safe_alter("technicians", "billing_type", "TEXT DEFAULT 'hourly'")
    _safe_alter("sales_records", "salesperson", "TEXT DEFAULT ''")
