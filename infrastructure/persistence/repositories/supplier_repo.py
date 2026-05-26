from datetime import datetime
from typing import List, Dict, Optional

from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one


class SupplierRepo:

    def list_suppliers(self) -> List[Dict]:
        try:
            items = db_query("SELECT * FROM suppliers ORDER BY name")
        except Exception:
            items = []
        return items

    def create_supplier(self, data: Dict) -> Dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        db_execute("INSERT INTO suppliers (name, contact, phone, address, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                   (data["name"], data.get("contact", ""), data.get("phone", ""),
                    data.get("address", ""), data.get("notes", ""), now, now))
        return {"message": f"已创建供应商: {data['name']}"}

    def get_supplier(self, sup_id: int) -> Optional[Dict]:
        sup = db_query_one("SELECT * FROM suppliers WHERE id = ?", (sup_id,))
        return sup

    def update_supplier(self, sup_id: int, **fields) -> Dict:
        updates = []
        params = []
        for f in ["name", "contact", "phone", "address", "notes"]:
            if f in fields:
                updates.append(f"{f} = ?")
                params.append(fields[f])
        if not updates:
            return {"error": "无更新字段"}
        params.append(sup_id)
        db_execute(f"UPDATE suppliers SET {', '.join(updates)}, updated_at=datetime('now','localtime') WHERE id=?", tuple(params))
        return {"message": "已更新"}

    def delete_supplier(self, sup_id: int) -> Dict:
        db_execute("DELETE FROM suppliers WHERE id = ?", (sup_id,))
        return {"message": "已删除"}

    def get_supplier_performance(self) -> List[Dict]:
        return db_query("""
            SELECT
                s.id as supplier_id, s.name as supplier_name, s.contact, s.phone,
                COUNT(DISTINCT po.id) as order_count,
                COALESCE(SUM(COALESCE(pi.total_cost, 0)), 0) as total_spent,
                COALESCE(SUM(COALESCE(pi.quantity, 0)), 0) as total_items,
                CASE WHEN COUNT(DISTINCT po.id) > 0
                     THEN ROUND(COALESCE(SUM(COALESCE(pi.total_cost, 0)), 0) / COUNT(DISTINCT po.id), 2)
                     ELSE 0 END as avg_order_value,
                ROUND(COALESCE(AVG(COALESCE(pi.unit_cost, 0)), 0), 2) as avg_unit_cost,
                COUNT(DISTINCT CASE WHEN po.status = 'completed' THEN po.id END) as completed_orders,
                COUNT(DISTINCT CASE WHEN po.payment_status = 'unpaid' THEN po.id END) as unpaid_orders,
                COALESCE(SUM(CASE WHEN po.payment_status = 'unpaid' THEN COALESCE(pi.total_cost, 0) ELSE 0 END), 0) as unpaid_amount,
                MAX(po.purchase_date) as last_order_date
            FROM suppliers s
            LEFT JOIN purchase_orders po ON s.name = po.vendor
            LEFT JOIN purchase_items pi ON pi.po_id = po.id
            GROUP BY s.id
            ORDER BY total_spent DESC
        """) or []
