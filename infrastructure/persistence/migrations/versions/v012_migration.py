"""
博通 (Botong) — 数据库迁移 V12
统一 income_records 字段(method/amount/total_amount)
"""



def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_index, _raw_execute
    _raw_execute("UPDATE income_records SET method = payment_method WHERE (method IS NULL OR method = '') AND (payment_method IS NOT NULL AND payment_method != '')")
    _raw_execute("UPDATE income_records SET method = 'pending' WHERE method = '待收款'")
    _raw_execute("UPDATE income_records SET amount = total_amount WHERE (amount IS NULL OR amount = 0) AND (total_amount IS NOT NULL AND total_amount > 0)")
