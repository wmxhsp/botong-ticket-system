"""
博通 (Botong) — 数据库迁移 V22
技术人员天薪/包工成本率字段
"""


def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_alter, _safe_index

    _safe_alter("technicians", "daily_rate", "REAL DEFAULT 0")
    _safe_alter("technicians", "package_rate", "REAL DEFAULT 0")
    _safe_alter("technicians", "daily_cost_rate", "REAL DEFAULT 0")
    _safe_alter("technicians", "package_cost", "REAL DEFAULT 0")
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_technicians_billing_type ON technicians(billing_type)",
    ])
