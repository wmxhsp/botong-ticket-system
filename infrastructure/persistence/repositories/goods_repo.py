from datetime import datetime
from typing import List, Dict, Optional

from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one
from domain.exceptions import GoodsNotFoundError


class GoodsRepo:

    def list_goods(self, mode: str = None, q: str = None) -> List[Dict]:
        try:
            sql = """SELECT g.*, gc.name as category_name, gt.name as type_name,
                        (SELECT COUNT(*) FROM inventory_items WHERE product_id = g.id AND status = 'in_stock') as stock
                     FROM goods g
                     LEFT JOIN goods_categories gc ON g.category_id = gc.id
                     LEFT JOIN goods_types gt ON g.type_id = gt.id
                     WHERE 1=1"""
            params = []
            if mode == 'ticket':
                sql += " AND g.sale_mode IN ('ticket_only', 'both')"
            elif mode == 'sales':
                sql += " AND g.sale_mode IN ('sales_only', 'both')"
            if q:
                sql += " AND (g.name LIKE ? OR g.sku LIKE ? OR g.notes LIKE ?)"
                like_q = f"%{q}%"
                params.extend([like_q, like_q, like_q])
            sql += " ORDER BY gc.sort_order, gc.name, gt.sort_order, g.name"
            items = db_query(sql, tuple(params))
        except Exception:
            items = []
        return items

    def get_goods(self, goods_id: int) -> Optional[Dict]:
        goods = db_query_one("""
            SELECT g.*, gc.name as category_name, gt.name as type_name
            FROM goods g
            LEFT JOIN goods_categories gc ON g.category_id = gc.id
            LEFT JOIN goods_types gt ON g.type_id = gt.id
            WHERE g.id = ?
        """, (goods_id,))
        if not goods:
            raise GoodsNotFoundError(f"商品 #{goods_id} 不存在")
        return goods

    def create_goods(self, data: Dict) -> Dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        category_id = data.get("category_id")
        type_id = data.get("type_id")
        db_execute("""INSERT INTO goods
            (name, sku, category_id, type_id, unit,
             selling_price, cost_price, min_stock, supplier, notes,
             is_subscription, billing_cycle, billing_price, sale_mode,
             created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (data["name"], data.get("sku", ""), category_id, type_id,
             data.get("unit", "个"),
             float(data.get("selling_price", 0)), float(data.get("cost_price", 0)),
             int(data.get("min_stock", 1)), data.get("supplier", ""), data.get("notes", ""),
             1 if data.get("is_subscription") else 0, data.get("billing_cycle", ""),
             float(data.get("billing_price", 0)), data.get("sale_mode", "both"), now, now))
        return {"message": f"已创建商品: {data['name']}"}

    def update_goods(self, goods_id: int, **fields) -> Dict:
        allowed = ["name", "sku", "category_id", "type_id",
                   "unit", "selling_price", "cost_price", "min_stock",
                   "supplier", "notes", "is_subscription", "billing_cycle",
                   "billing_price", "sale_mode"]
        updates = []
        params = []
        for field in allowed:
            if field in fields:
                updates.append(f"{field} = ?")
                params.append(fields[field])
        if not updates:
            return {"error": "没有可更新的字段"}
        params.append(goods_id)
        db_execute(f"UPDATE goods SET {', '.join(updates)}, updated_at=datetime('now','localtime') WHERE id=?", tuple(params))
        return {"message": "已更新"}

    def delete_goods(self, goods_id: int) -> Dict:
        db_execute("DELETE FROM inventory_logs WHERE product_id = ?", (goods_id,))
        db_execute("DELETE FROM inventory_items WHERE product_id = ?", (goods_id,))
        db_execute("DELETE FROM goods WHERE id = ?", (goods_id,))
        return {"message": "已删除"}

    def get_inventory_overview(self) -> List[Dict]:
        try:
            items = db_query("""
                SELECT g.id, g.name, gc.name as category, g.min_stock,
                    (SELECT COUNT(*) FROM inventory_items WHERE product_id = g.id AND status = 'in_stock') as stock_count,
                    (SELECT COUNT(*) FROM inventory_items WHERE product_id = g.id AND status = 'used') as in_use_count,
                    (SELECT COUNT(*) FROM inventory_items WHERE product_id = g.id) as total_purchased
                FROM goods g
                LEFT JOIN goods_categories gc ON g.category_id = gc.id
                ORDER BY gc.sort_order, g.name
            """)
        except Exception:
            items = []
        return items

    def list_categories(self) -> List[Dict]:
        try:
            return db_query("""
                SELECT gc.*,
                    COUNT(DISTINCT g.id) as goods_count,
                    COUNT(DISTINCT gt.id) as types_count
                FROM goods_categories gc
                LEFT JOIN goods g ON g.category_id = gc.id
                LEFT JOIN goods_types gt ON gt.category_id = gc.id AND gt.is_active = 1
                GROUP BY gc.id
                ORDER BY gc.sort_order, gc.name
            """)
        except Exception:
            return []

    def get_category(self, category_id: int) -> Optional[Dict]:
        return db_query_one("""
            SELECT gc.*,
                COUNT(DISTINCT g.id) as goods_count
            FROM goods_categories gc
            LEFT JOIN goods g ON g.category_id = gc.id
            WHERE gc.id = ?
            GROUP BY gc.id
        """, (category_id,))

    def create_category(self, name: str, icon: str = "",
                        sort_order: int = 99) -> Dict:
        if not name:
            return {"error": "请提供分类名称"}
        existing = db_query_one("SELECT id FROM goods_categories WHERE name = ?", (name,))
        if existing:
            return {"error": f"分类 '{name}' 已存在"}
        db_execute("INSERT INTO goods_categories (name, icon, sort_order) VALUES (?, ?, ?)",
                  (name, icon, sort_order))
        return {"message": f"已创建分类: {name}"}

    def update_category(self, category_id: int, **fields) -> Dict:
        allowed = ["name", "icon", "sort_order", "is_active"]
        updates = []
        params = []
        for f in allowed:
            if f in fields:
                updates.append(f"{f} = ?")
                params.append(fields[f])
        if not updates:
            return {"error": "没有可更新的字段"}
        params.append(category_id)
        db_execute(f"UPDATE goods_categories SET {', '.join(updates)} WHERE id = ?", tuple(params))
        return {"message": "已更新"}

    def delete_category(self, category_id: int) -> Dict:
        cat = db_query_one("SELECT name FROM goods_categories WHERE id = ?", (category_id,))
        if not cat:
            return {"error": "分类不存在"}
        goods_count = db_query_one("SELECT COUNT(*) as c FROM goods WHERE category_id = ?",
                                  (category_id,))["c"]
        if goods_count > 0:
            return {"error": f"分类 '{cat['name']}' 下有 {goods_count} 个商品，请先迁移后再删除"}
        db_execute("DELETE FROM goods_types WHERE category_id = ?", (category_id,))
        db_execute("DELETE FROM goods_categories WHERE id = ?", (category_id,))
        return {"message": f"已删除分类 '{cat['name']}'"}

    def list_types(self, category_id: int = None) -> List[Dict]:
        try:
            if category_id:
                return db_query("""
                    SELECT gt.*, COUNT(DISTINCT g.id) as goods_count
                    FROM goods_types gt
                    LEFT JOIN goods g ON g.type_id = gt.id
                    WHERE gt.category_id = ? AND gt.is_active = 1
                    GROUP BY gt.id
                    ORDER BY gt.sort_order, gt.name
                """, (category_id,))
            else:
                return db_query("""
                    SELECT gt.*, gc.name as category_name,
                        COUNT(DISTINCT g.id) as goods_count
                    FROM goods_types gt
                    LEFT JOIN goods_categories gc ON gt.category_id = gc.id
                    LEFT JOIN goods g ON g.type_id = gt.id
                    WHERE gt.is_active = 1
                    GROUP BY gt.id
                    ORDER BY gc.sort_order, gt.sort_order, gt.name
                """)
        except Exception:
            return []

    def create_type(self, category_id: int, name: str,
                    sort_order: int = 99) -> Dict:
        if not name:
            return {"error": "请提供类型名称"}
        if not category_id:
            return {"error": "请提供所属分类ID"}
        cat = db_query_one("SELECT id FROM goods_categories WHERE id = ?", (category_id,))
        if not cat:
            return {"error": "分类不存在"}
        existing = db_query_one(
            "SELECT id FROM goods_types WHERE category_id = ? AND name = ?",
            (category_id, name))
        if existing:
            return {"error": f"类型 '{name}' 已存在"}
        db_execute("INSERT INTO goods_types (category_id, name, sort_order) VALUES (?, ?, ?)",
                  (category_id, name, sort_order))
        return {"message": f"已创建类型: {name}"}

    def update_type(self, type_id: int, **fields) -> Dict:
        allowed = ["name", "sort_order", "is_active", "category_id"]
        updates = []
        params = []
        for f in allowed:
            if f in fields:
                updates.append(f"{f} = ?")
                params.append(fields[f])
        if not updates:
            return {"error": "没有可更新的字段"}
        params.append(type_id)
        db_execute(f"UPDATE goods_types SET {', '.join(updates)} WHERE id = ?", tuple(params))
        return {"message": "已更新"}

    def delete_type(self, type_id: int) -> Dict:
        typ = db_query_one("SELECT id, name FROM goods_types WHERE id = ?", (type_id,))
        if not typ:
            return {"error": "类型不存在"}
        goods_count = db_query_one("SELECT COUNT(*) as c FROM goods WHERE type_id = ?",
                                  (type_id,))["c"]
        if goods_count > 0:
            return {"error": f"类型 '{typ['name']}' 下有 {goods_count} 个商品，请先迁移后再删除"}
        db_execute("DELETE FROM goods_types WHERE id = ?", (type_id,))
        return {"message": f"已删除类型 '{typ['name']}'"}
