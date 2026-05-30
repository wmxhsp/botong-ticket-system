"""
博通 (Botong) — 数据库迁移 V24
工单服务明细行支持天薪/包工计费模式
- ticket_service_items 添加 days、package_fee 字段
- 兼容已有数据（days 默认 0，package_fee 默认 0）
"""


def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter, _safe_index

    _safe_alter("ticket_service_items", "days", "REAL DEFAULT 0")
    _safe_alter("ticket_service_items", "package_fee", "REAL DEFAULT 0")
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_service_items_days ON ticket_service_items(days)",
    ])
