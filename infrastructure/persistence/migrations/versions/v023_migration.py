"""
博通 (Botong) — 数据库迁移 V23
性能优化：补充复合索引、部分索引、审计归档表、幂等缓存过期索引
"""


def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_alter, _safe_index

    # 1. 复合索引：工单列表最常用的组合查询
    _safe_index([
        # 工单列表页：按状态+客户筛选
        "CREATE INDEX IF NOT EXISTS idx_tickets_status_client ON tickets(status, client)",
        # 工单列表页：按状态+创建时间排序
        "CREATE INDEX IF NOT EXISTS idx_tickets_status_created ON tickets(status, created_at)",
        # 工单列表页：按客户+创建时间
        "CREATE INDEX IF NOT EXISTS idx_tickets_client_created ON tickets(client, created_at)",
        # Dashboard统计：按结算状态+创建时间
        "CREATE INDEX IF NOT EXISTS idx_tickets_billing_created ON tickets(billing_status, created_at)",
    ])

    # 2. 部分索引：软删除过滤（只索引未删除的记录，更小更快）
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_inventory_items_active ON inventory_items(product_id, status) WHERE is_deleted = 0",
        "CREATE INDEX IF NOT EXISTS idx_equipment_active ON equipment(client) WHERE is_deleted = 0",
    ])

    # 3. 幂等缓存过期索引
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_idempotent_expires ON _idempotent_cache(expires_at)",
    ])

    # 4. 审计日志归档表
    db_execute("""
        CREATE TABLE IF NOT EXISTS audit_log_archive (
            id INTEGER PRIMARY KEY,
            action TEXT,
            table_name TEXT,
            record_id INTEGER,
            old_data TEXT,
            new_data TEXT,
            operator TEXT,
            ip_address TEXT,
            created_at TEXT,
            archived_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # 5. 审计归档索引
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_audit_archive_table ON audit_log_archive(table_name)",
        "CREATE INDEX IF NOT EXISTS idx_audit_archive_created ON audit_log_archive(created_at)",
    ])

    # 6. expense_records 关联工单查询索引
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_expense_ticket ON expense_records(related_ticket_id)",
    ])

    # 7. sales_records 常用查询索引
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_sales_client ON sales_records(client)",
        "CREATE INDEX IF NOT EXISTS idx_sales_status ON sales_records(status)",
        "CREATE INDEX IF NOT EXISTS idx_sales_created ON sales_records(created_at)",
    ])
