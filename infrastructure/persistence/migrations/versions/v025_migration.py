


def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter

    _safe_alter("clients", "email", "TEXT DEFAULT ''")
    _safe_alter("clients", "address", "TEXT DEFAULT ''")
    _safe_alter("clients", "created_at", "TEXT DEFAULT (datetime('now','localtime'))")
    _safe_alter("clients", "updated_at", "TEXT DEFAULT (datetime('now','localtime'))")
