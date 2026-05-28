from datetime import datetime
from typing import List, Dict, Optional, Any

from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one, db_transaction


class PurchaseRepo:

    def list_purchase_orders(self) -> List[Dict]:
        try:
            orders = db_query("""
                SELECT p.*,
                    (SELECT COUNT(*) FROM purchase_items pi WHERE pi.po_id = p.id) as item_count,
                    (SELECT SUM(pi.quantity) FROM purchase_items pi WHERE pi.po_id = p.id) as total_qty,
                    (SELECT SUM(pi.total_cost) FROM purchase_items pi WHERE pi.po_id = p.id) as total_amount
                FROM purchase_orders p
                ORDER BY p.created_at DESC
            """)
        except Exception:
            orders = []
        return orders

    def count_purchase_orders(self) -> int:
        try:
            result = db_query_one("SELECT COUNT(*) as c FROM purchase_orders")
            return result["c"] if result else 0
        except Exception:
            return 0

    def get_purchase_order(self, po_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT id, po_no, vendor, supplier_id, purchase_date, status, notes, created_at FROM purchase_orders WHERE id = ?", (po_id,))

    def get_purchase_items(self, po_id: int) -> List[Dict]:
        return db_query(
            "SELECT pi.*, g.selling_price, g.name FROM purchase_items pi LEFT JOIN goods g ON pi.goods_id = g.id WHERE pi.po_id = ?",
            (po_id,))

    def get_purchase_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT id, po_id, product_name, quantity, unit_price, total_cost, notes FROM purchase_items WHERE id = ?", (item_id,))

    def get_po_no(self, po_id: int) -> Optional[str]:
        po = db_query_one("SELECT po_no FROM purchase_orders WHERE id = ?", (po_id,))
        return po["po_no"] if po else None

    def update_received_qty(self, item_id: int, qty: int) -> None:
        db_execute("UPDATE purchase_items SET received_qty=? WHERE id=?", (qty, item_id))

    def get_po_summary(self, po_id: int) -> Dict:
        result = db_query_one("SELECT SUM(quantity) as total_qty, SUM(received_qty) as total_recv FROM purchase_items WHERE po_id=?", (po_id,))
        return {
            "total_qty": result["total_qty"] if result and result["total_qty"] else 0,
            "total_recv": result["total_recv"] if result and result["total_recv"] else 0,
        }

    def update_purchase_status(self, po_id: int, status: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        db_execute("UPDATE purchase_orders SET status=?, updated_at=? WHERE id=?", (status, now, po_id))

    def delete_purchase_order(self, po_id: int) -> None:
        db_execute("DELETE FROM purchase_items WHERE po_id = ?", (po_id,))
        db_execute("DELETE FROM purchase_orders WHERE id = ?", (po_id,))

    def create_purchase_order(self, po_no: str, vendor: str, purchase_date: str,
                              notes: str, items: List[Dict]) -> Dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        db_execute("""
            INSERT INTO purchase_orders (po_no, vendor, purchase_date, status, notes, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?)
        """, (po_no, vendor, purchase_date, "draft", notes, now, now))
        po = db_query_one("SELECT id FROM purchase_orders WHERE po_no = ?", (po_no,))
        po_id = po["id"]

        for item in items:
            goods_id = item.get("goods_id")
            qty = int(item.get("quantity", 1))
            cost = float(item.get("unit_cost", 0))
            goods = db_query_one("SELECT id, name FROM goods WHERE id = ?", (goods_id,))
            if goods:
                db_execute("INSERT INTO purchase_items (po_id, goods_id, goods_name, quantity, unit_cost, total_cost, received_qty, created_at) VALUES (?,?,?,?,?,?,0,?)",
                          (po_id, goods_id, goods["name"], qty, cost, cost * qty, now))

        return {"po_no": po_no, "id": po_id}

    def confirm_payment(self, po_id: int, amount: float = 0, method: str = "银行转账",
                        status: str = "paid", now: str = None):
        now = now or datetime.now().strftime("%Y-%m-%d %H:%M")
        po = self.get_purchase_order(po_id)
        total = float(po.get("total_amount", 0) or 0)
        if total <= 0:
            items = self.get_purchase_items(po_id)
            total = sum(float(i.get("total_cost", 0) or 0) for i in items)
        db_execute(
            "UPDATE purchase_orders SET payment_status=?, payment_method=?, paid_at=?, total_amount=?, updated_at=? WHERE id=?",
            (status, method, now, total, now, po_id))

    def get_purchase_stats(self) -> Dict[str, Any]:
        stats = db_query("""
            SELECT po.vendor, COUNT(DISTINCT po.id) as order_count,
                ROUND(SUM(pi.total_cost), 2) as total_spent,
                SUM(pi.quantity) as total_items,
                ROUND(AVG(pi.total_cost), 2) as avg_order_value,
                ROUND(AVG(pi.unit_cost), 2) as avg_unit_cost
            FROM purchase_orders po JOIN purchase_items pi ON pi.po_id = po.id
            WHERE po.status IN ('ordered', 'partial', 'completed')
            GROUP BY po.vendor ORDER BY total_spent DESC""")
        trends = db_query("""
            SELECT strftime('%Y-%m', po.purchase_date) as month,
                COUNT(DISTINCT po.id) as order_count,
                ROUND(SUM(pi.total_cost), 2) as total_spent,
                ROUND(AVG(pi.unit_cost), 2) as avg_unit_price
            FROM purchase_orders po JOIN purchase_items pi ON pi.po_id = po.id
            WHERE po.purchase_date >= date('now', '-6 months')
            GROUP BY month ORDER BY month""")
        return {"stats": stats or [], "trends": trends or []}

    def get_unpaid_orders(self) -> Dict[str, Any]:
        orders = db_query("""
            SELECT po.*, s.name as supplier_name, s.phone as supplier_phone,
                   (SELECT COALESCE(SUM(total_cost),0) FROM purchase_items WHERE po_id = po.id) as total_cost
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.payment_status IN ('unpaid', 'partial')
              AND po.status IN ('ordered', 'partial', 'completed')
            ORDER BY po.purchase_date""")
        total_amount = sum(float(o.get("total_amount", 0) or o.get("total_cost", 0) or 0) for o in (orders or []))
        by_vendor = {}
        for o in (orders or []):
            v = o.get("supplier_name") or o.get("vendor", "未知供应商")
            if v not in by_vendor:
                by_vendor[v] = {"vendor": v, "count": 0, "amount": 0}
            by_vendor[v]["count"] += 1
            by_vendor[v]["amount"] += float(o.get("total_amount", 0) or o.get("total_cost", 0) or 0)
        summary = f"共 {len(orders or [])} 单未付款，合计 ¥{total_amount:.2f}"
        return {
            "orders": orders or [], "total_amount": round(total_amount, 2),
            "by_vendor": sorted(by_vendor.values(), key=lambda x: x["amount"], reverse=True),
            "summary": summary}

    def update_item_received_qty(self, item_id: int, qty: int) -> None:
        db_execute("UPDATE purchase_items SET received_qty=? WHERE id=?", (qty, item_id))

    def create_and_complete_order(self, po_no: str, vendor: str, now: str, notes: str, items: list) -> dict:
        with db_transaction() as conn:
            conn.execute("""
                INSERT INTO purchase_orders (po_no, vendor, purchase_date, status, notes, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?)
            """, (po_no, vendor, now, "draft", notes, now, now))
            po_id = conn.execute("SELECT id FROM purchase_orders WHERE po_no = ?", (po_no,)).fetchone()["id"]

            for item in items:
                goods_id = item.get("goods_id")
                qty = int(item.get("quantity", 1))
                cost = float(item.get("unit_cost", 0))
                goods = conn.execute("SELECT id, name FROM goods WHERE id = ?", (goods_id,)).fetchone()
                if goods:
                    goods = dict(goods)
                    conn.execute("INSERT INTO purchase_items (po_id, goods_id, goods_name, quantity, unit_cost, total_cost, received_qty, created_at) VALUES (?,?,?,?,?,?,0,?)",
                                (po_id, goods_id, goods["name"], qty, cost, cost * qty, now))

            po_items = conn.execute("SELECT id, po_id, product_name, quantity, unit_price, total_cost FROM purchase_items WHERE po_id = ?", (po_id,)).fetchall()
            for item in po_items:
                item = dict(item)
                remaining = item["quantity"] - item["received_qty"]
                if remaining > 0:
                    conn.execute("UPDATE purchase_items SET received_qty=? WHERE id=?", (item["quantity"], item["id"]))
                    total = remaining * item["unit_cost"]
                    conn.execute(
                        "INSERT INTO expense_records (category, vendor, amount, description, paid_at, created_at, related_ticket_id) VALUES (?,?,?,?,?,?,NULL)",
                        ("采购", vendor, total, f"采购 {item['goods_name']} x{remaining} (单号{po_no})", now, now)
                    )
            conn.execute("UPDATE purchase_orders SET status='completed', updated_at=? WHERE id=?", (now, po_id))

        return {"po_no": po_no, "id": po_id}
