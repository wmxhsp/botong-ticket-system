"""
博通 (Botong) — 数据库迁移 V8
旧架构缺失列补齐(project/service_fee_id/收支明细列)
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter, _safe_index, db_execute
    for col, ddl in [
        ("project", "TEXT DEFAULT ''"),
        ("service_fee_id", "INTEGER"),
        ("is_renewal", "INTEGER DEFAULT 0"),
        ("tax_included", "INTEGER DEFAULT 0"),
        ("tax_rate", "REAL DEFAULT 0"),
        ("tax_amount", "REAL DEFAULT 0"),
        ("total_with_tax", "REAL DEFAULT 0"),
    ]:
        _safe_alter("tickets", col, ddl)
    for col, ddl in [
        ("total_amount", "REAL DEFAULT 0"),
        ("payment_method", "TEXT DEFAULT '微信'"),
        ("tax_amount", "REAL DEFAULT 0"),
    ]:
        _safe_alter("income_records", col, ddl)
    for col, ddl in [
        ("vendor", "TEXT DEFAULT ''"),
        ("is_personal", "INTEGER DEFAULT 0"),
        ("payment_type", "TEXT DEFAULT ''"),
        ("is_recurring", "INTEGER DEFAULT 0"),
        ("receipt_no", "TEXT DEFAULT ''"),
    ]:
        _safe_alter("expense_records", col, ddl)
