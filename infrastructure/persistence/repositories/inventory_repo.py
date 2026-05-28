"""
博通 — 库存仓储 SQLite 实现
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from infrastructure.persistence.legacy_db import db_query, db_query_one, db_execute, db_transaction, get_db

logger = logging.getLogger(__name__)


class SqliteInventoryRepository:

    def __init__(self, conn=None):
        self._conn = conn

    @contextmanager
    def _ensure_conn(self):
        if self._conn:
            yield self._conn
        else:
            with get_db() as conn:
                yield conn

    # ===== 商品查询 =====

    def get_goods(self, goods_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT id, name, sku, category_id, unit, is_bulk, cost_price, min_stock, max_stock, updated_at FROM goods WHERE id = ?", (goods_id,))

    def count_items_by_product(self, goods_id: int) -> int:
        row = db_query_one(
            "SELECT COUNT(*) as c FROM inventory_items WHERE product_id = ?",
            (goods_id,))
        return row["c"] if row else 0

    def update_goods_cost(self, goods_id: int, cost_price: float) -> bool:
        with self._ensure_conn() as conn:
            conn.execute("UPDATE goods SET cost_price = ? WHERE id = ?",
                         (cost_price, goods_id))
            if not self._conn:
                conn.commit()
            return True

    def update_goods_threshold(self, goods_id: int, updates: dict) -> bool:
        sets = []
        params = []
        for k, v in updates.items():
            if k in ("min_stock", "max_stock"):
                sets.append(f"{k} = ?")
                params.append(v)
        if not sets:
            return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        sets.append("updated_at = ?")
        params.append(now)
        params.append(goods_id)
        with self._ensure_conn() as conn:
            conn.execute(f"UPDATE goods SET {', '.join(sets)} WHERE id = ?",
                         tuple(params))
            if not self._conn:
                conn.commit()
            return True

    # ===== 库存查询 =====

    def get_bulk_stock_total(self, goods_id: int) -> float:
        row = db_query_one(
            "SELECT COALESCE(SUM(bulk_quantity), 0) as total FROM inventory_items "
            "WHERE product_id = ? AND status = 'in_stock'",
            (goods_id,))
        return float(row["total"]) if row else 0.0

    def get_piece_stock_count(self, goods_id: int) -> int:
        row = db_query_one(
            "SELECT COUNT(*) as c FROM inventory_items "
            "WHERE product_id = ? AND status = 'in_stock'",
            (goods_id,))
        return row["c"] if row else 0

    def list_inventory(self, status: str = None, goods_id: int = None) -> List[Dict[str, Any]]:
        sql = """SELECT i.*, g.name as product_name, g.unit, g.is_bulk
                 FROM inventory_items i JOIN goods g ON i.product_id = g.id WHERE 1=1"""
        params = []
        if status:
            sql += " AND i.status = ?"
            params.append(status)
        if goods_id:
            sql += " AND i.product_id = ?"
            params.append(goods_id)
        sql += " ORDER BY i.created_at DESC"
        return db_query(sql, tuple(params))

    def get_sold_count(self, goods_id: int) -> int:
        row = db_query_one(
            "SELECT COUNT(*) as c FROM inventory_items WHERE product_id = ? AND status = 'sold'",
            (goods_id,))
        return row["c"] if row else 0

    def count_in_stock(self, goods_id: int) -> int:
        row = db_query_one(
            "SELECT COUNT(*) as c FROM inventory_items WHERE product_id = ? AND status = 'in_stock'",
            (goods_id,))
        return row["c"] if row else 0

    def get_monthly_sold_quantity(self, goods_id: int) -> float:
        row = db_query_one(
            "SELECT COALESCE(SUM(quantity),0) as qty FROM sales_records "
            "WHERE product_id = ? AND created_at >= datetime('now', '-30 days')",
            (goods_id,))
        return float(row["qty"]) if row else 0.0

    # ===== 库存项 CRUD =====

    def find_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT id, product_id, serial_no, batch_no, bulk_quantity, location, warehouse_id, status, ticket_id, unit_cost, purchase_order_id, sale_id, notes, received_at, created_at FROM inventory_items WHERE id = ?", (item_id,))

    def find_bulk_in_stock(self, goods_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one(
            "SELECT id, product_id, serial_no, batch_no, bulk_quantity, location, warehouse_id, status, unit_cost FROM inventory_items WHERE product_id = ? AND status = 'in_stock'",
            (goods_id,))

    def find_bulk_in_stock_for_update(self, conn, goods_id: int) -> Optional[Dict[str, Any]]:
        cursor = conn.execute(
            "SELECT id, product_id, batch_no, bulk_quantity, status, unit_cost FROM inventory_items WHERE product_id = ? AND status = 'in_stock'",
            (goods_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_pieces_in_stock(self, goods_id: int, limit: int) -> List[Dict[str, Any]]:
        return db_query(
            "SELECT id, product_id, serial_no, batch_no, status, unit_cost FROM inventory_items WHERE product_id = ? AND status = 'in_stock' LIMIT ?",
            (goods_id, limit))

    def find_pieces_in_stock_for_update(self, conn, goods_id: int, limit: int) -> List[Dict[str, Any]]:
        cursor = conn.execute(
            "SELECT id, product_id, serial_no, status, unit_cost FROM inventory_items WHERE product_id = ? AND status = 'in_stock' LIMIT ?",
            (goods_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def update_bulk_item_atomic(self, conn, item_id: int, batch_no: str, bulk_quantity: float,
                                 status: str = None, sale_id: int = None, ticket_id: int = None):
        sets = ["batch_no = ?", "bulk_quantity = ?"]
        params = [batch_no, bulk_quantity]
        if status:
            sets.append("status = ?")
            params.append(status)
        if sale_id is not None:
            sets.append("sale_id = ?")
            params.append(sale_id)
        if ticket_id is not None:
            sets.append("ticket_id = ?")
            params.append(ticket_id)
        params.append(item_id)
        conn.execute(
            f"UPDATE inventory_items SET {', '.join(sets)} WHERE id = ?",
            tuple(params))

    def mark_item_used_atomic(self, conn, item_id: int, ticket_id: int) -> bool:
        cursor = conn.execute(
            "UPDATE inventory_items SET status = 'used', ticket_id = ? "
            "WHERE id = ? AND status = 'in_stock'",
            (ticket_id, item_id))
        return cursor.rowcount > 0

    def add_log_atomic(self, conn, goods_id: int, log_type: str, quantity: float,
                       from_location: str = None, to_location: str = None,
                       notes: str = "", item_id: int = None, created_at: str = None):
        now = created_at or datetime.now().isoformat()
        conn.execute(
            """INSERT INTO inventory_logs
               (product_id, item_id, type, quantity, from_location, to_location, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (goods_id, item_id, log_type, quantity, from_location,
             to_location, notes, now))

    def get_items_by_product(self, goods_id: int, status: str = None,
                             limit: int = None) -> List[Dict[str, Any]]:
        cols = "id, product_id, serial_no, batch_no, location, warehouse_id, status, ticket_id, unit_cost, received_at"
        sql = f"SELECT {cols} FROM inventory_items WHERE product_id = ?"
        params = [goods_id]
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY id"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        return db_query(sql, tuple(params))

    def create_item(self, goods_id: int, serial_no: str = None,
                    batch_no: str = None, bulk_quantity: float = 0,
                    location: str = "库房", status: str = "in_stock",
                    purchase_order_id: int = None, unit_cost: float = 0,
                    received_at: str = None, created_at: str = None,
                    warehouse_id: int = None, sale_id: int = None) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        received_at = received_at or now
        created_at = created_at or now
        if warehouse_id is None:
            default = db_query_one("SELECT id FROM warehouses WHERE name='库房' ORDER BY id LIMIT 1")
            warehouse_id = default["id"] if default else None
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO inventory_items "
                "(product_id, serial_no, batch_no, bulk_quantity, location, status, "
                "purchase_order_id, unit_cost, received_at, created_at, warehouse_id, sale_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (goods_id, serial_no, batch_no, bulk_quantity, location, status,
                 purchase_order_id, unit_cost, received_at, created_at, warehouse_id, sale_id))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def update_item_status(self, item_id: int, status: str, notes: str = None,
                           sale_id: int = None):
        with self._ensure_conn() as conn:
            if notes:
                conn.execute("UPDATE inventory_items SET status = ?, notes = ? WHERE id = ?",
                             (status, notes, item_id))
            else:
                conn.execute("UPDATE inventory_items SET status = ? WHERE id = ?",
                             (status, item_id))
            if sale_id is not None:
                conn.execute("UPDATE inventory_items SET sale_id = ? WHERE id = ?",
                             (sale_id, item_id))
            if not self._conn:
                conn.commit()

    def update_bulk_item(self, item_id: int, batch_no: str, bulk_quantity: float,
                         status: str = None, sale_id: int = None, ticket_id: int = None):
        with self._ensure_conn() as conn:
            sets = ["batch_no = ?", "bulk_quantity = ?"]
            params = [batch_no, bulk_quantity]
            if status:
                sets.append("status = ?")
                params.append(status)
            if sale_id is not None:
                sets.append("sale_id = ?")
                params.append(sale_id)
            if ticket_id is not None:
                sets.append("ticket_id = ?")
                params.append(ticket_id)
            params.append(item_id)
            conn.execute(
                f"UPDATE inventory_items SET {', '.join(sets)} WHERE id = ?",
                tuple(params))
            if not self._conn:
                conn.commit()

    def update_item_location(self, item_id: int, location: str, warehouse_id: int = None):
        with self._ensure_conn() as conn:
            if warehouse_id is not None:
                conn.execute("UPDATE inventory_items SET location=?, warehouse_id=? WHERE id=?",
                             (location, warehouse_id, item_id))
            else:
                conn.execute("UPDATE inventory_items SET location=? WHERE id=?",
                             (location, item_id))
            if not self._conn:
                conn.commit()

    # ===== 库存流水 =====

    def add_log(self, goods_id: int, log_type: str, quantity: float,
                from_location: str = None, to_location: str = None,
                notes: str = "", item_id: int = None, created_at: str = None):
        now = created_at or datetime.now().isoformat()
        with self._ensure_conn() as conn:
            conn.execute(
                """INSERT INTO inventory_logs
                   (product_id, item_id, type, quantity, from_location, to_location, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (goods_id, item_id, log_type, quantity, from_location,
                 to_location, notes, now))
            if not self._conn:
                conn.commit()

    def get_logs_with_goods(self, goods_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        if goods_id:
            return db_query(
                """SELECT l.*, g.name as product_name
                   FROM inventory_logs l LEFT JOIN goods g ON l.product_id = g.id
                   WHERE l.product_id = ? ORDER BY l.created_at DESC LIMIT ?""",
                (goods_id, limit))
        return db_query(
            """SELECT l.*, g.name as product_name
               FROM inventory_logs l LEFT JOIN goods g ON l.product_id = g.id
               ORDER BY l.created_at DESC LIMIT ?""",
            (limit,))

    # ===== 加权成本 =====

    def get_weighted_cost_data(self, goods_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one(
            """SELECT COALESCE(SUM(bulk_quantity), 0) as total_qty,
                      COALESCE(SUM(bulk_quantity * unit_cost), 0) as total_value
               FROM inventory_items WHERE product_id = ? AND status = 'in_stock'""",
            (goods_id,))

    # ===== 仓库 =====

    def get_warehouse(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT id, name FROM warehouses WHERE id = ?", (warehouse_id,))

    def find_warehouse_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT id, name FROM warehouses WHERE name = ?", (name,))

    # ===== 销售记录 =====

    def list_sales_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        return db_query(
            """SELECT s.*, g.name as goods_name, g.sku as goods_sku
               FROM sales_records s LEFT JOIN goods g ON s.product_id = g.id
               ORDER BY s.created_at DESC LIMIT ?""",
            (limit,))

    def get_expiring_subscriptions(self, today: str, week_later: str) -> List[Dict[str, Any]]:
        return db_query("""
            SELECT s.*, g.name as goods_name, g.sku as goods_sku
            FROM sales_records s
            LEFT JOIN goods g ON s.product_id = g.id
            WHERE s.expires_at IS NOT NULL
              AND s.expires_at >= ? AND s.expires_at <= ?
              AND s.status = 'paid'
            ORDER BY s.expires_at
        """, (today, week_later))

    def find_in_stock_items(self, goods_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        return db_query(
            "SELECT id, unit_cost, bulk_quantity, product_id FROM inventory_items "
            "WHERE product_id = ? AND status = 'in_stock' ORDER BY id LIMIT ?",
            (goods_id, limit))

    def mark_item_used(self, item_id: int, ticket_id: int) -> bool:
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                "UPDATE inventory_items SET status = 'used', ticket_id = ? "
                "WHERE id = ? AND status = 'in_stock'",
                (ticket_id, item_id))
            if not self._conn:
                conn.commit()
            return cursor.rowcount > 0

    def deduct_bulk_quantity(self, item_id: int, deduct_qty: float, ticket_id: int) -> bool:
        with self._ensure_conn() as conn:
            row = conn.execute(
                "SELECT bulk_quantity, batch_no FROM inventory_items WHERE id = ? AND status = 'in_stock'",
                (item_id,)).fetchone()
            if not row:
                return False
            remaining = float(row["bulk_quantity"]) - deduct_qty
            if remaining <= 0.001:
                conn.execute(
                    "UPDATE inventory_items SET status = 'used', ticket_id = ?, bulk_quantity = 0, "
                    "batch_no = 'BATCH-0' WHERE id = ?", (ticket_id, item_id))
            else:
                goods_row = conn.execute(
                    "SELECT unit FROM goods g JOIN inventory_items i ON i.product_id = g.id WHERE i.id = ?",
                    (item_id,)).fetchone()
                unit = goods_row["unit"] if goods_row and goods_row["unit"] else "个"
                new_batch = f"BATCH-{remaining}-{unit}"
                conn.execute(
                    "UPDATE inventory_items SET bulk_quantity = ?, ticket_id = ?, batch_no = ? WHERE id = ?",
                    (remaining, ticket_id, new_batch, item_id))
            if not self._conn:
                conn.commit()
            return True

    def get_items_by_ids(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        if not item_ids:
            return []
        placeholders = ",".join("?" for _ in item_ids)
        return db_query(
            f"SELECT id, serial_no, batch_no, unit_cost, purchase_order_id, location "
            f"FROM inventory_items WHERE id IN ({placeholders})",
            tuple(item_ids)) or []

    def get_purchase_orders_by_ids(self, po_ids: List[int]) -> List[Dict[str, Any]]:
        if not po_ids:
            return []
        unique_ids = list(set(po_ids))
        placeholders = ",".join("?" for _ in unique_ids)
        return db_query(
            f"SELECT id, po_no, vendor, purchase_date FROM purchase_orders WHERE id IN ({placeholders})",
            tuple(unique_ids)) or []

    @staticmethod
    def parse_bulk_quantity(item: Dict) -> float:
        if item.get("bulk_quantity"):
            return float(item["bulk_quantity"])
        batch_no = item.get("batch_no", "")
        try:
            if batch_no and batch_no.startswith("BATCH-"):
                parts = batch_no.split("-")
                if len(parts) >= 2:
                    return float(parts[1])
        except (ValueError, IndexError, TypeError):
            pass
        return 0

    def insert_sale_record(self, client: str, goods_id: int, product_name: str,
                           product_type: str, quantity: int, unit_price: float,
                           cost_price: float, final_amount: float, profit: float,
                           payment_method: str, notes: str, validity_days: int,
                           discount_type: str, discount_value: float,
                           ticket_id: int = None, salesperson: str = "") -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._ensure_conn() as conn:
            cur = conn.execute("""
                INSERT INTO sales_records
                (client, product_id, product_name, product_type, quantity, batch_size,
                 unit_price, cost_price, total_amount, profit, payment_method, status,
                 notes, validity_days, created_at, paid_at, discount_type, discount_value,
                 ticket_id, salesperson)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'paid', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client, goods_id, product_name, product_type,
                quantity, 1, unit_price, cost_price, final_amount, profit,
                payment_method, notes, validity_days, now, now,
                discount_type, discount_value,
                ticket_id, salesperson
            ))
            if not self._conn:
                conn.commit()
            return cur.lastrowid

    def insert_sale_income_record(self, client: str, final_amount: float,
                                  payment_method: str, sale_id: int, description: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._ensure_conn() as conn:
            conn.execute("""
                INSERT INTO income_records
                (client, amount, total_amount, payment_method, source_type, source_id, received_at, description)
                VALUES (?, ?, ?, ?, 'sales_record', ?, ?, ?)
            """, (client, final_amount, final_amount, payment_method, sale_id, now, description))
            if not self._conn:
                conn.commit()

    def update_bulk_item_sold(self, item_id: int, sale_id: int, batch_no: str, bulk_quantity: float = 0):
        with self._ensure_conn() as conn:
            conn.execute("""
                UPDATE inventory_items
                SET status = 'sold', sale_id = ?, batch_no = ?, bulk_quantity = ?
                WHERE id = ?
            """, (sale_id, batch_no, bulk_quantity, item_id))
            if not self._conn:
                conn.commit()

    def update_bulk_item_quantity(self, item_id: int, batch_no: str, bulk_quantity: float):
        with self._ensure_conn() as conn:
            conn.execute("""
                UPDATE inventory_items SET batch_no = ?, bulk_quantity = ? WHERE id = ?
            """, (batch_no, bulk_quantity, item_id))
            if not self._conn:
                conn.commit()

    def mark_items_sold_by_ids(self, sale_id: int, item_ids: list):
        if not item_ids:
            return
        placeholders = ",".join("?" * len(item_ids))
        with self._ensure_conn() as conn:
            conn.execute(f"""
                UPDATE inventory_items SET status = 'sold', sale_id = ? WHERE id IN ({placeholders})
            """, (sale_id, *item_ids))
            if not self._conn:
                conn.commit()

    def record_sale_transaction(self, goods_id: int, client: str, quantity: int,
                                unit_price: float, cost_price: float,
                                final_amount: float, profit: float,
                                payment_method: str, product_type: str,
                                sale_label: str, notes: str, validity_days: int,
                                discount_type: str, discount_value: float,
                                ticket_id: int = None, salesperson: str = "",
                                goods: dict = None) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with db_transaction() as conn:
            cur = conn.execute("""
                INSERT INTO sales_records
                (client, product_id, product_name, product_type, quantity, batch_size,
                 unit_price, cost_price, total_amount, profit, payment_method, status,
                 notes, validity_days, created_at, paid_at, discount_type, discount_value,
                 ticket_id, salesperson)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'paid', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client, goods_id, goods["name"], product_type,
                quantity, 1, unit_price, cost_price, final_amount, profit,
                payment_method, notes, validity_days, now, now,
                discount_type, discount_value,
                ticket_id, salesperson
            ))
            sale_id = cur.lastrowid

            conn.execute("""
                INSERT INTO income_records
                (client, amount, total_amount, payment_method, source_type, source_id, received_at, description)
                VALUES (?, ?, ?, ?, 'sales_record', ?, ?, ?)
            """, (client, final_amount, final_amount, payment_method, sale_id, now,
                  f"{sale_label}: {goods['name']} × {quantity} ({client})"))

            if goods.get("is_bulk"):
                existing = conn.execute("""
                    SELECT id, product_id, batch_no, bulk_quantity, status, unit_cost
                    FROM inventory_items
                    WHERE product_id = ? AND status = 'in_stock'
                """, (goods_id,)).fetchone()
                if existing:
                    existing = dict(existing)
                    if existing["batch_no"]:
                        old_qty = self.parse_bulk_quantity(existing)
                        new_qty = old_qty - quantity
                        if new_qty <= 0:
                            conn.execute("""
                                UPDATE inventory_items
                                SET status = 'sold', sale_id = ?, batch_no = ?, bulk_quantity = 0
                                WHERE id = ?
                            """, (sale_id, f"BATCH-0-{goods['unit']}", existing["id"]))
                        else:
                            batch_no = f"BATCH-{new_qty}-{goods['unit']}"
                            conn.execute("""
                                UPDATE inventory_items SET batch_no = ?, bulk_quantity = ? WHERE id = ?
                            """, (batch_no, new_qty, existing["id"]))
            else:
                items = conn.execute("""
                    SELECT id FROM inventory_items
                    WHERE product_id = ? AND status = 'in_stock'
                    LIMIT ?
                """, (goods_id, int(quantity))).fetchall()
                for item in items:
                    conn.execute("""
                        UPDATE inventory_items
                        SET status = 'sold', sale_id = ? WHERE id = ?
                    """, (sale_id, item["id"]))

            conn.execute("""
                INSERT INTO inventory_logs
                (product_id, type, quantity, from_location, to_location, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (goods_id, sale_label, quantity, "库房", client,
                  f"{sale_label}: {goods['name']} × {quantity} · {payment_method}",
                  now))

        return sale_id

    def get_sale_record(self, sale_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT id, client, product_id, product_name, product_type, quantity, unit_price, cost_price, total_amount, profit, payment_method, status, notes, validity_days, ticket_id, salesperson, created_at, paid_at FROM sales_records WHERE id = ?", (sale_id,))

    def renew_sale(self, sale_id: int, client: str, product_id: int,
                   product_name: str, product_type: str, quantity: int,
                   unit_price: float, cost_price: float, total_amount: float,
                   profit: float, payment_method: str, validity_days: int,
                   notes: str) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with db_transaction() as conn:
            cur = conn.execute("""
                INSERT INTO sales_records
                (client, product_id, product_name, product_type, quantity, batch_size,
                 unit_price, cost_price, total_amount, profit, payment_method, status,
                 notes, validity_days, renew_from, created_at, paid_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'paid', ?, ?, ?, ?, ?)
            """, (client, product_id, product_name, product_type,
                  quantity, 1, unit_price, cost_price, total_amount, profit,
                  payment_method, notes, validity_days, sale_id, now, now))
            new_id = cur.lastrowid
            conn.execute("""
                INSERT INTO income_records
                (client, amount, total_amount, payment_method, source_type, source_id, received_at, description)
                VALUES (?, ?, ?, ?, 'sales_record', ?, ?, ?)
            """, (client, total_amount, total_amount, payment_method, new_id, now,
                  f"续费: {product_name} × {quantity} ({client})"))
        return new_id

    def link_sale_ticket(self, sale_id: int, ticket_id: int):
        db_execute("UPDATE sales_records SET ticket_id = ? WHERE id = ?",
                   (ticket_id, sale_id))

    # ===== 库位 CRUD =====

    def list_locations(self) -> list:
        try:
            return db_query("SELECT id, name, description, sort_order FROM locations ORDER BY sort_order, name") or []
        except Exception:
            return []

    def find_location_by_name(self, name: str):
        return db_query_one("SELECT id FROM locations WHERE name = ?", (name,))

    def create_location(self, name: str, description: str = "", sort_order: int = 99):
        db_execute("INSERT INTO locations (name, description, sort_order) VALUES (?, ?, ?)",
                   (name, description, sort_order))

    def update_location(self, loc_id: int, updates: dict):
        _ALLOWED = {"name", "description", "sort_order"}
        sets, params = [], []
        for f in _ALLOWED:
            if f in updates:
                sets.append(f"{f} = ?")
                params.append(updates[f])
        if not sets:
            return
        params.append(loc_id)
        db_execute(f"UPDATE locations SET {', '.join(sets)} WHERE id = ?", tuple(params))

    def delete_location(self, loc_id: int):
        loc = db_query_one("SELECT name FROM locations WHERE id = ?", (loc_id,))
        if not loc:
            return None
        used = db_query_one("SELECT COUNT(*) as c FROM inventory_items WHERE location = ?", (loc["name"],))
        if used and used["c"] > 0:
            db_execute("UPDATE inventory_items SET location = '库房' WHERE location = ?", (loc["name"],))
        db_execute("DELETE FROM locations WHERE id = ?", (loc_id,))
        return loc["name"]

    # ===== 仓库 CRUD =====

    def list_warehouses(self) -> list:
        try:
            return db_query("SELECT id, name, address, manager, sort_order FROM warehouses ORDER BY sort_order, name") or []
        except Exception:
            return []

    def find_warehouse_by_name(self, name: str):
        return db_query_one("SELECT id FROM warehouses WHERE name = ?", (name,))

    def create_warehouse(self, name: str, address: str = "", manager: str = "", sort_order: int = 99):
        db_execute("INSERT INTO warehouses (name, address, manager, sort_order) VALUES (?, ?, ?, ?)",
                   (name, address, manager, sort_order))

    def update_warehouse(self, wh_id: int, updates: dict):
        _ALLOWED = {"name", "address", "manager", "sort_order"}
        sets, params = [], []
        for f in _ALLOWED:
            if f in updates:
                sets.append(f"{f} = ?")
                params.append(updates[f])
        if not sets:
            return
        params.append(wh_id)
        db_execute(f"UPDATE warehouses SET {', '.join(sets)} WHERE id = ?", tuple(params))

    def delete_warehouse(self, wh_id: int):
        wh = db_query_one("SELECT name FROM warehouses WHERE id = ?", (wh_id,))
        if not wh:
            return None
        db_execute("DELETE FROM warehouses WHERE id = ?", (wh_id,))
        return wh["name"]
