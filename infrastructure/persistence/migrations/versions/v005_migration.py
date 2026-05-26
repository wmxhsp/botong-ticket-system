"""
博通 (Botong) — 数据库迁移 V5
供应商应付款 + 客户账期 + 对账单
"""



def upgrade():
    from infrastructure.persistence.legacy_db import _safe_alter, _safe_index, db_execute
    _safe_alter("purchase_orders", "payment_status", "TEXT DEFAULT 'unpaid'")
    _safe_alter("purchase_orders", "payment_method", "TEXT DEFAULT ''")
    _safe_alter("purchase_orders", "paid_at", "TEXT")
    _safe_alter("purchase_orders", "total_amount", "REAL DEFAULT 0")
    db_execute("UPDATE purchase_orders SET total_amount = (SELECT COALESCE(SUM(total_cost),0) FROM purchase_items WHERE po_id = purchase_orders.id) WHERE total_amount = 0")
    _safe_alter("purchase_orders", "supplier_id", "INTEGER REFERENCES suppliers(id)")
    _safe_alter("clients", "payment_terms", "INTEGER DEFAULT 30")
    _safe_alter("clients", "billing_address", "TEXT DEFAULT ''")
    _safe_alter("suppliers", "bank_name", "TEXT DEFAULT ''")
    _safe_alter("suppliers", "bank_account", "TEXT DEFAULT ''")
    _safe_alter("suppliers", "payment_terms", "INTEGER DEFAULT 30")
    _safe_index([
        "CREATE INDEX IF NOT EXISTS idx_po_payment ON purchase_orders(payment_status)",
        "CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id)",
        "CREATE INDEX IF NOT EXISTS idx_clients_payment_terms ON clients(payment_terms)",
    ])
