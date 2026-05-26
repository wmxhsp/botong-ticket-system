"""
博通 (Botong) — 数据库迁移 V13
客户表费率字段 + rates.json 导入
"""

from pathlib import Path


def upgrade():
    from infrastructure.persistence.legacy_db import db_execute, _safe_index, _raw_alter, _raw_execute
    for col, ddl in [
        ("hourly_rate", "REAL DEFAULT 0"),
        ("annual_rate", "REAL DEFAULT 0"),
        ("client_type", "TEXT DEFAULT ''"),
        ("scope", "TEXT DEFAULT ''"),
    ]:
        _raw_alter("clients", col, ddl)
    import json as _json
    rates_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "rates.json"
    if rates_path.exists():
        try:
            data = _json.loads(rates_path.read_text())
            for name, cfg in data.get("rates", {}).items():
                if name == "default":
                    continue
                _raw_execute(
                    "INSERT OR IGNORE INTO clients (name, contact, hourly_rate, annual_rate, client_type, scope, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))",
                    (name, cfg.get("contact", ""), cfg.get("hourly", 0), cfg.get("annual", 0),
                     cfg.get("type", ""), _json.dumps(cfg.get("scope", []), ensure_ascii=False))
                )
        except Exception:
            pass
