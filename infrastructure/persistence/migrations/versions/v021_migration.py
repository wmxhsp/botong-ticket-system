"""
博通 (Botong) — 数据库迁移 V21
ticket_no NOT NULL约束 + NULL编号数据修复
"""



def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, db_query
    from datetime import datetime as _dt
    null_rows = db_query("SELECT id, created_at FROM tickets WHERE ticket_no IS NULL")
    for row in null_rows:
        created = row.get("created_at") or _dt.now().strftime("%Y%m%d")
        date_part = created[:8] if len(created) >= 8 else _dt.now().strftime("%Y%m%d")
        ts = int(_dt.now().timestamp() * 1000) % 100000
        generated = f"GD-{date_part}-{ts:05d}"
        db_execute("UPDATE tickets SET ticket_no = ? WHERE id = ?", (generated, row["id"]))
    db_execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tickets_ticket_no ON tickets(ticket_no)")
