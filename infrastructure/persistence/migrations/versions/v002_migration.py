"""
博通 (Botong) — 数据库迁移 V2
预约时间 + 提醒系统
"""



def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_index
    try:
        db_execute("ALTER TABLE tickets ADD COLUMN appointment_at TEXT")
    except Exception:
        pass
    db_execute("""
        CREATE TABLE IF NOT EXISTS ticket_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            reminder_time TEXT NOT NULL,
            content TEXT NOT NULL,
            repeat_daily INTEGER DEFAULT 1,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        )
    """)
    db_execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            reminder_id INTEGER,
            title TEXT NOT NULL,
            content TEXT,
            read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        )
    """)
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_reminders_active ON ticket_reminders(active)",
        "CREATE INDEX IF NOT EXISTS idx_reminders_ticket ON ticket_reminders(ticket_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
    ])
