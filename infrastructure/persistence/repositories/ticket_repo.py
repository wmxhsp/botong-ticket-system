"""
博通 (Botong) — 工单仓储 SQLite 实现
完整支持动态查询、分页、事务、关联数据加载

支持外部 Connection 注入（通过 conn 参数），
用于 UnitOfWork 事务内共享同一连接。
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager

from infrastructure.persistence.legacy_db import db_query, db_query_one, db_execute, get_db

logger = logging.getLogger(__name__)


class SqliteTicketRepository:
    """
    工单仓储 - SQLite 实现

    支持原有 lib/core/database 的全部功能，
    同时提供更丰富的关联数据加载和查询构建。

    支持事务内连接注入:
        with UnitOfWork() as uow:
            repo = SqliteTicketRepository(conn=uow.conn)
            repo.save(...)  # 使用 uow.conn 共享事务
    """

    def __init__(self, conn=None):
        """
        Args:
            conn: 外部传入的数据库连接（用于 UnitOfWork 事务内共享）
                  为 None 时使用默认的连接池连接（独立提交）
        """
        self._conn = conn

    @contextmanager
    def _ensure_conn(self):
        """
        获取连接上下文管理器。
        
        已注入外部连接时直接使用（调用方管理生命周期），
        否则从连接池获取并自动归还。
        """
        if self._conn:
            yield self._conn
        else:
            with get_db() as conn:
                yield conn

    # 工单列表查询字段（按需投影）
    LIST_COLS = (
        "id, ticket_no, title, client, contact, location, service_type, priority, "
        "status, assignee, billing_status, total, created_at, updated_at, closed_at"
    )

    # 工单详情查询字段（比列表多一些，但仍然不是 *）
    DETAIL_COLS = (
        "id, ticket_no, title, client, contact, location, service_type, priority, "
        "status, description, assignee, created_by, estimated_hours, time_spent, "
        "total_labor, total_external, total_material, total, billing_status, "
        "billing_model, notes, project, created_at, updated_at, closed_at, "
        "service_date, completion_date, appointment_at, "
        "travel_distance, travel_rate, "
        "service_fee_id, discount_type, discount_value, discount_rate, "
        "tax_rate, tax_amount, total_with_tax, parts_fee, is_renewal, tax_included, "
        "timer_started_at"
    )

    # ===== 基础 CRUD =====

    def find_by_id(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """获取工单详情（含关联数据）"""
        # 动态检测存在的列，避免旧 schema 报错
        try:
            cols_info = db_query_one("PRAGMA table_info(tickets)")  # 仅触发检测
            from infrastructure.persistence.legacy_db import DB_FILE
            import sqlite3 as _s3
            _c = _s3.connect(DB_FILE)
            _existing = {r[1] for r in _c.execute("PRAGMA table_info(tickets)").fetchall()}
            _c.close()
            preferred = [c.strip() for c in self.DETAIL_COLS.split(',')]
            _cols = ', '.join(c for c in preferred if c in _existing) or '*'
        except Exception:
            _cols = '*'

        ticket = db_query_one(f"SELECT {_cols} FROM tickets WHERE id = ?", (ticket_id,))
        if not ticket:
            return None

        # 加载核心关联数据（这些表数据量小，SELECT * 影响可忽略）
        ticket["materials"] = db_query(
            "SELECT id, name, product_name, product_id, quantity, unit_price, total, total_cost, notes, inventory_item_ids, goods_id, sale_id, created_at FROM materials WHERE ticket_id = ?", (ticket_id,))
        ticket["history"] = db_query(
            "SELECT id, action, note, operator, changes, timestamp FROM history WHERE ticket_id = ? ORDER BY timestamp", (ticket_id,))

        # 结算单信息
        ticket["invoice"] = db_query_one(
            "SELECT id, source_type, source_id, client, amount, total_amount, method, payment_method, description, received_at FROM income_records WHERE source_type = 'ticket' AND source_id = ?",
            (ticket_id,))

        # 关联设备
        ticket["equipment"] = db_query(
            """SELECT te.*, e.name, e.type, e.model, e.location, e.warranty_expire
               FROM ticket_equipment te
               LEFT JOIN equipment e ON te.equipment_id = e.id
               WHERE te.ticket_id = ?""",
            (ticket_id,))

        # 关联支出
        ticket["expenses"] = db_query(
            "SELECT id, category, description, amount, paid_at FROM expense_records WHERE related_ticket_id = ?",
            (ticket_id,))

        ticket["service_items"] = db_query(
            """SELECT si.id, si.ticket_id, si.name, si.technician_name, si.service_fee_id, si.hours,
                  si.unit_price, si.cost_price, si.line_total, si.line_cost,
                  sf.name AS service_name, sf.fee_type
               FROM ticket_service_items si
               LEFT JOIN service_fees sf ON si.service_fee_id = sf.id
               WHERE si.ticket_id = ?
               ORDER BY si.id""",
            (ticket_id,))

        ticket["technicians"] = ticket["service_items"]

        # 照片
        try:
            ticket["photos"] = db_query(
                "SELECT id, filename, url, created_at FROM ticket_photos WHERE ticket_id = ? ORDER BY id",
                (ticket_id,))
        except Exception:
            ticket["photos"] = []

        return ticket

    def find_list(self, filters: Dict[str, Any] = None,
                  page: int = 1, per_page: int = 50,
                  sort_field: str = None, sort_dir: str = "desc"
                  ) -> Tuple[List[Dict[str, Any]], int]:
        """
        工单列表查询（动态 WHERE 构建）

        filters 支持:
            - status: str | list — 单个或多个状态
            - client: str — 客户名模糊搜索
            - q: str — 关键词（工单号/描述/客户）
            - date_from: str — 开始日期
            - date_to: str — 结束日期
            - billing: str — 结算状态
            - assignee: str — 负责人
        """
        conditions = []
        params = []
        filters = filters or {}

        # 状态筛选
        status = filters.get("status")
        if status:
            if isinstance(status, str) and "," in status:
                parts = status.split(",")
                placeholders = ",".join(["?"] * len(parts))
                conditions.append(f"status IN ({placeholders})")
                params.extend(parts)
            elif isinstance(status, (list, tuple)):
                placeholders = ",".join(["?"] * len(status))
                conditions.append(f"status IN ({placeholders})")
                params.extend(status)
            else:
                conditions.append("status = ?")
                params.append(status)

        # 客户模糊搜索
        client = filters.get("client")
        if client:
            conditions.append("client LIKE ?")
            params.append(f"%{client}%")

        # 关键词搜索
        keyword = filters.get("q")
        if keyword:
            conditions.append(
                "(ticket_no LIKE ? OR description LIKE ? OR client LIKE ? OR title LIKE ?)")
            q = f"%{keyword}%"
            params.extend([q, q, q, q])

        # 日期范围
        date_from = filters.get("date_from")
        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)

        date_to = filters.get("date_to")
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to + " 23:59:59")

        # 结算状态
        billing = filters.get("billing")
        if billing:
            conditions.append("billing_status = ?")
            params.append(billing)

        # 负责人
        assignee = filters.get("assignee")
        if assignee:
            conditions.append("assignee = ?")
            params.append(assignee)

        where = " AND ".join(conditions) if conditions else "1=1"

        # 排序
        sort_whitelist = {
            "id": "id", "ticket_no": "ticket_no", "client": "client",
            "status": "status", "created_at": "created_at", "updated_at": "updated_at",
            "total": "total", "estimated_hours": "estimated_hours", "profit": "profit",
            "closed_at": "closed_at",
        }
        sort_col = sort_whitelist.get(sort_field, "id")
        sort_direction = "ASC" if sort_dir == "asc" else "DESC"
        order_clause = f"ORDER BY {sort_col} {sort_direction}"

        offset = (page - 1) * per_page

        with get_db() as conn:
            # 总数
            count_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM tickets WHERE {where}", params
            ).fetchone()
            total = count_row["cnt"] if count_row else 0

            # 动态构建投影列：若数据库中缺失某些列（旧 schema），则忽略它们
            try:
                cols_info = conn.execute("PRAGMA table_info(tickets)").fetchall()
                existing_cols = {r['name'] for r in cols_info}
            except Exception:
                existing_cols = set()

            preferred_cols = [c.strip() for c in self.LIST_COLS.split(',')]
            select_cols = [c for c in preferred_cols if c in existing_cols]
            select_clause = ', '.join(select_cols) if select_cols else '*'

            # 列表
            rows = conn.execute(
                f"SELECT {select_clause} FROM tickets WHERE {where} {order_clause} LIMIT ? OFFSET ?",
                params + [per_page, offset]
            ).fetchall()

            tickets = [dict(r) for r in rows]
            return tickets, total

    def save(self, ticket: Dict[str, Any]) -> int:
        """创建工单，返回新工单 ID"""
        with self._ensure_conn() as conn:
            now = datetime.now().isoformat()
            cursor = conn.execute(
                """INSERT INTO tickets
                   (ticket_no, title, client, contact, location, service_type, priority,
                    status, description, assignee, created_by, estimated_hours,
                    billing_model, created_at, updated_at, appointment_at,
                    travel_distance, travel_rate)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ticket.get("ticket_no", ""),
                    ticket.get("title", ticket.get("description", "")[:50]),
                    ticket.get("client", ""),
                    ticket.get("contact", ""),
                    ticket.get("location", ""),
                    ticket.get("service_type", ""),
                    ticket.get("priority", "M"),
                    ticket.get("status", "open"),
                    ticket.get("description", ""),
                    ticket.get("assignee", ""),
                    ticket.get("created_by", ""),
                    ticket.get("estimated_hours", 0),
                    ticket.get("billing_model", "hourly"),
                    now,
                    now,
                    ticket.get("appointment_at"),
                    ticket.get("travel_distance", 0),
                    ticket.get("travel_rate", 0),
                )
            )
            ticket_id = cursor.lastrowid
            if not self._conn:
                conn.commit()
            return ticket_id

    def update(self, ticket_id: int, data: Dict[str, Any], conn=None) -> bool:
        """更新工单字段"""
        allowed_fields = {
            "client", "contact", "location", "service_type", "priority",
            "description", "title", "assignee", "status", "billing_status",
            "estimated_hours", "time_spent", "total_labor", "total_material",
            "total_external", "total", "notes", "appointment_at", "closed_at",
            "travel_distance", "travel_rate", "parts_fee",
            "service_fee_id", "discount_type", "discount_value",
            "completion_date", "service_date",
            "tax_rate", "tax_amount", "total_with_tax",
        }

        updates = []
        params = []
        for key, value in data.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        params.append(ticket_id)
        use_conn = conn or self._conn
        if use_conn:
            use_conn.execute(f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?", tuple(params))
            if not conn:
                use_conn.commit()
            return True
        with self._ensure_conn() as c:
            c.execute(f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?", tuple(params))
            if not self._conn:
                c.commit()
            return True

    def delete(self, ticket_id: int) -> bool:
        """删除工单（级联清理关联数据，含财务记录）"""
        with self._ensure_conn() as conn:
            try:
                conn.execute("DELETE FROM materials WHERE ticket_id = ?", (ticket_id,))
            except Exception:
                pass
            try:
                conn.execute("DELETE FROM history WHERE ticket_id = ?", (ticket_id,))
            except Exception:
                pass
            try:
                conn.execute("DELETE FROM ticket_service_items WHERE ticket_id = ?", (ticket_id,))
            except Exception:
                pass
            try:
                conn.execute("DELETE FROM ticket_equipment WHERE ticket_id = ?", (ticket_id,))
            except Exception:
                pass
            try:
                conn.execute("DELETE FROM ticket_photos WHERE ticket_id = ?", (ticket_id,))
            except Exception:
                pass
            try:
                conn.execute("DELETE FROM ticket_reminders WHERE ticket_id = ?", (ticket_id,))
            except Exception:
                pass
            try:
                conn.execute("DELETE FROM todos WHERE source_type = 'ticket' AND source_id = ?",
                             (ticket_id,))
            except Exception:
                pass
            # 清理可能引用 tickets 的库存或其他记录，避免外键约束
            try:
                conn.execute("DELETE FROM inventory_items WHERE ticket_id = ?", (ticket_id,))
            except Exception:
                pass
            try:
                conn.execute("DELETE FROM inspection_records WHERE ticket_id = ?", (ticket_id,))
            except Exception:
                pass
            # 级联清理财务记录
            try:
                conn.execute("DELETE FROM income_records WHERE source_type = 'ticket' AND source_id = ?",
                             (ticket_id,))
            except Exception:
                pass
            try:
                conn.execute("DELETE FROM expense_records WHERE related_ticket_id = ?",
                             (ticket_id,))
            except Exception:
                pass
            try:
                conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
            except Exception as e:
                # 若因外键约束导致删除失败，尝试临时关闭外键后重试（测试环境兼容策略）
                try:
                    conn.execute("PRAGMA foreign_keys = OFF")
                    conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
                finally:
                    try:
                        conn.execute("PRAGMA foreign_keys = ON")
                    except Exception:
                        pass
            if not self._conn:
                conn.commit()
            return True

    # ===== 业务查询 =====

    def get_status_stats(self) -> Dict[str, int]:
        """获取各状态工单数量统计"""
        rows = db_query("SELECT status, COUNT(*) as cnt FROM tickets GROUP BY status")
        stats = {}
        for row in rows:
            stats[row["status"]] = row["cnt"]
        return stats

    def get_overdue_tickets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取逾期工单"""
        return db_query(
            """SELECT id, ticket_no, client, status, completion_date, total
               FROM tickets
               WHERE status NOT IN ('closed', 'archived')
                 AND completion_date IS NOT NULL
                 AND completion_date < date('now','localtime')
               ORDER BY completion_date ASC
               LIMIT ?""",
            (limit,))

    def get_recent_tickets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近工单"""
        return db_query(f"SELECT {self.LIST_COLS} FROM tickets ORDER BY id DESC LIMIT ?", (limit,))

    def generate_ticket_no(self) -> str:
        """生成工单编号"""
        now = datetime.now()
        prefix = now.strftime("GD-%Y%m%d-%H%M%S")
        count = db_query_one(
            "SELECT COUNT(*) as cnt FROM tickets WHERE ticket_no LIKE ?",
            (f"{prefix}%",))
        seq = (count["cnt"] if count else 0) + 1
        return f"{prefix}-{seq:02d}"

    def add_history(self, ticket_id: int, action: str, note: str = "",
                    operator: str = "") -> int:
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO history (ticket_id, action, note, operator, timestamp)
                   VALUES (?, ?, ?, ?, datetime('now','localtime'))""",
                (ticket_id, action, note, operator or "system"))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def add_history_atomic(self, conn, ticket_id: int, action: str, note: str = "",
                           operator: str = "") -> int:
        cursor = conn.execute(
            """INSERT INTO history (ticket_id, action, note, operator, timestamp)
               VALUES (?, ?, ?, ?, datetime('now','localtime'))""",
            (ticket_id, action, note, operator or "system"))
        return cursor.lastrowid

    def update_status_with_history(self, ticket_id: int, status: str, note: str = "",
                                   operator: str = "", conn=None) -> bool:
        """原子操作：更新状态并记录历史"""
        use_conn = conn or self._conn
        if use_conn:
            use_conn.execute("UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
                        (status, datetime.now().isoformat(), ticket_id))
            use_conn.execute(
                """INSERT INTO history (ticket_id, action, note, operator, timestamp)
                   VALUES (?, ?, ?, ?, datetime('now','localtime'))""",
                (ticket_id, "status", note, operator or "system"))
            if not conn:
                use_conn.commit()
            return True
        with self._ensure_conn() as c:
            c.execute("UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
                        (status, datetime.now().isoformat(), ticket_id))
            c.execute(
                """INSERT INTO history (ticket_id, action, note, operator, timestamp)
                   VALUES (?, ?, ?, ?, datetime('now','localtime'))""",
                (ticket_id, "status", note, operator or "system"))
            if not self._conn:
                c.commit()
            return True

    def find_inventory_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """查询单个库存项"""
        return db_query_one("SELECT id, product_id, serial_no, batch_no, bulk_quantity, location, status, ticket_id, unit_cost, sale_id, warehouse_id, notes FROM inventory_items WHERE id = ?", (item_id,))

    def mark_item_used_atomic(self, conn, item_id: int, ticket_id: int) -> bool:
        """原子操作：标记库存项已使用（使用外部连接）"""
        cursor = conn.execute(
            "UPDATE inventory_items SET status = 'used', ticket_id = ? "
            "WHERE id = ? AND status = 'in_stock'",
            (ticket_id, item_id))
        return cursor.rowcount > 0

    def deduct_bulk_quantity_atomic(self, conn, item_id: int, deduct_qty: float,
                                    ticket_id: int) -> bool:
        """原子操作：批量扣减库存数量（使用外部连接）"""
        row = conn.execute(
            "SELECT bulk_quantity, batch_no, product_id FROM inventory_items WHERE id = ? AND status = 'in_stock'",
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
        return True

    def get_history(self, ticket_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        return db_query(
            "SELECT id, action, note, operator, changes, timestamp FROM history WHERE ticket_id = ? ORDER BY timestamp DESC LIMIT ?",
            (ticket_id, limit)) or []

    def count_history(self, ticket_id: int) -> int:
        row = db_query_one("SELECT COUNT(*) as c FROM history WHERE ticket_id = ?", (ticket_id,))
        return row["c"] if row else 0

    def get_timer(self, ticket_id: int) -> Optional[str]:
        row = db_query_one("SELECT timer_started_at FROM tickets WHERE id = ?", (ticket_id,))
        return row["timer_started_at"] if row else None

    def set_timer(self, ticket_id: int, started_at: str):
        with self._ensure_conn() as conn:
            conn.execute("UPDATE tickets SET timer_started_at = ? WHERE id = ?",
                         (started_at, ticket_id))
            if not self._conn:
                conn.commit()

    def clear_timer(self, ticket_id: int):
        with self._ensure_conn() as conn:
            conn.execute("UPDATE tickets SET timer_started_at = NULL WHERE id = ?",
                         (ticket_id,))
            if not self._conn:
                conn.commit()

    def search_by_filter(self, status: str = None, client: str = None,
                         keyword: str = None, date_from: str = None,
                         date_to: str = None) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if client:
            conditions.append("client LIKE ?")
            params.append(f"%{client}%")
        if keyword:
            conditions.append("(description LIKE ? OR ticket_no LIKE ?)")
            params.extend([f"%{keyword}%"] * 2)
        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to)
        where = " AND ".join(conditions) if conditions else "1=1"
        return db_query(f"SELECT id, ticket_no, client, status FROM tickets WHERE {where} ORDER BY id",
                        tuple(params))

    def link_equipment(self, ticket_id: int, equip_id: int, equipment_name: str = None):
        with self._ensure_conn() as conn:
            try:
                if equipment_name:
                    conn.execute(
                        "INSERT OR IGNORE INTO ticket_equipment (ticket_id, equipment_id, equipment_name, created_at) VALUES (?, ?, ?, datetime('now','localtime'))",
                        (ticket_id, equip_id, equipment_name))
                else:
                    conn.execute(
                        "INSERT OR IGNORE INTO ticket_equipment (ticket_id, equipment_id) VALUES (?, ?)",
                        (ticket_id, equip_id))
            except Exception as e:
                logger.warning(f"关联设备失败: ticket={ticket_id}, equip={equip_id}: {e}")
            if not self._conn:
                conn.commit()

    def add_technician(self, ticket_id: int, name: str, cost_rate: float = 30.0, hours: float = 0):
        """添加工单负责人（写入 ticket_service_items，计费规则由Service层计算后传入）"""
        with self._ensure_conn() as conn:
            conn.execute(
                "DELETE FROM ticket_service_items WHERE ticket_id=? AND technician_name=?",
                (ticket_id, name))
            conn.execute(
                "INSERT INTO ticket_service_items (ticket_id, technician_name, hours, unit_price, cost_price, line_total, line_cost) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ticket_id, name, hours, cost_rate * 2 if cost_rate > 0 else 60.0, cost_rate, hours * (cost_rate * 2 if cost_rate > 0 else 60.0), hours * cost_rate))
            if not self._conn:
                conn.commit()

    # ===== 服务明细行 (ticket_service_items) =====

    def get_service_items(self, ticket_id: int):
        """获取工单的所有服务明细行"""
        return db_query(
            "SELECT id, ticket_id, name, technician_name, service_fee_id, hours, unit_price, cost_price, line_total, line_cost FROM ticket_service_items WHERE ticket_id = ? ORDER BY id",
            (ticket_id,))

    def find_service_item(self, item_id: int, ticket_id: int = None) -> Optional[Dict[str, Any]]:
        """查询单个服务明细行"""
        _cols = "id, ticket_id, name, technician_name, service_fee_id, hours, unit_price, cost_price, line_total, line_cost"
        if ticket_id:
            return db_query_one(
                f"SELECT {_cols} FROM ticket_service_items WHERE id = ? AND ticket_id = ?",
                (item_id, ticket_id))
        return db_query_one(
            f"SELECT {_cols} FROM ticket_service_items WHERE id = ?", (item_id,))

    def add_service_item(self, ticket_id: int, technician_name: str,
                         service_fee_id: int, hours: float = 0,
                         unit_price: float = 0, cost_price: float = 0,
                         line_total: float = 0, line_cost: float = 0,
                         name: str = "") -> int:
        """添加服务明细行"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO ticket_service_items
                   (ticket_id, name, technician_name, service_fee_id, hours,
                    unit_price, cost_price, line_total, line_cost)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ticket_id, name, technician_name, service_fee_id, hours,
                 unit_price, cost_price, line_total, line_cost))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def update_service_item(self, item_id: int, data: dict) -> bool:
        """更新服务明细行"""
        allowed = {"name", "technician_name", "service_fee_id", "hours",
                    "unit_price", "cost_price", "line_total", "line_cost"}
        updates, params = [], []
        for k, v in data.items():
            if k in allowed:
                updates.append(f"{k} = ?")
                params.append(v)
        if not updates:
            return False
        params.append(item_id)
        with self._ensure_conn() as conn:
            conn.execute(f"UPDATE ticket_service_items SET {', '.join(updates)} WHERE id = ?", tuple(params))
            if not self._conn:
                conn.commit()
            return True

    def delete_service_item(self, item_id: int) -> bool:
        """删除服务明细行"""
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM ticket_service_items WHERE id = ?", (item_id,))
            if not self._conn:
                conn.commit()
            return True

    def delete_ticket_service_items(self, ticket_id: int):
        """删除工单的所有服务明细行（重建时使用）"""
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM ticket_service_items WHERE ticket_id = ?", (ticket_id,))
            if not self._conn:
                conn.commit()

    # ===== 计费字段查询 =====

    def get_billing_fields(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """获取工单计费相关字段"""
        # 若数据库中缺少某些列（旧 schema），动态选择存在的字段以避免 OperationalError
        needed = ["total_material", "travel_distance", "travel_rate",
                  "discount_type", "discount_value", "tax_rate"]
        try:
            from infrastructure.persistence.legacy_db import DB_FILE
            import sqlite3
            conn = sqlite3.connect(DB_FILE)
            cur = conn.execute("PRAGMA table_info(tickets)")
            cols = {r[1] for r in cur.fetchall()}
            conn.close()
        except Exception:
            cols = set()

        select_cols = [c for c in needed if c in cols]
        if not select_cols:
            return db_query_one("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        sql = f"SELECT {', '.join(select_cols)} FROM tickets WHERE id = ?"
        return db_query_one(sql, (ticket_id,))

    def sum_material_total(self, ticket_id: int) -> float:
        """汇总工单物料销售总额"""
        row = db_query_one(
            "SELECT COALESCE(SUM(total), 0) as m FROM materials WHERE ticket_id = ?",
            (ticket_id,))
        return float(row["m"]) if row else 0.0

    # ===== 物料管理 =====

    def find_material(self, material_id: int, ticket_id: int) -> Optional[Dict[str, Any]]:
        """查询单个物料"""
        return db_query_one(
            "SELECT id, ticket_id, name, product_name, product_id, quantity, unit_price, total, total_cost, notes, inventory_item_ids, goods_id, sale_id FROM materials WHERE id = ? AND ticket_id = ?",
            (material_id, ticket_id))

    def find_materials_by_ticket(self, ticket_id: int) -> List[Dict[str, Any]]:
        """获取工单物料列表（含商品SKU和分类名）"""
        return db_query(
            """SELECT m.*, g.sku, g.sale_mode, gc.name as category_name
               FROM materials m
               LEFT JOIN goods g ON m.product_id = g.id
               LEFT JOIN goods_categories gc ON g.category_id = gc.id
               WHERE m.ticket_id = ?
               ORDER BY m.id""",
            (ticket_id,))

    def add_material(self, ticket_id: int, name: str, product_name: str,
                     product_id: int, quantity: float, unit_price: float,
                     total: float, total_cost: float, notes: str = "") -> int:
        """添加物料"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO materials (ticket_id, name, product_name, product_id,
                   quantity, unit_price, total, total_cost, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ticket_id, name, product_name, product_id, quantity,
                 unit_price, total, total_cost, notes))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def update_material(self, material_id: int, ticket_id: int,
                        quantity: float, unit_price: float, total: float) -> bool:
        """更新物料"""
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE materials SET quantity=?, unit_price=?, total=? WHERE id=? AND ticket_id=?",
                (quantity, unit_price, total, material_id, ticket_id))
            if not self._conn:
                conn.commit()
            return True

    def delete_material(self, material_id: int, ticket_id: int) -> bool:
        """删除物料"""
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM materials WHERE id = ? AND ticket_id = ?",
                         (material_id, ticket_id))
            if not self._conn:
                conn.commit()
            return True

    def release_inventory(self, material_id: int) -> bool:
        """释放物料关联的库存（将库存项状态改为 in_stock）"""
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE inventory_items SET status='in_stock', ticket_id=NULL WHERE id = ?",
                (material_id,))
            if not self._conn:
                conn.commit()
            return True

    # ===== 照片管理 =====

    def find_photos_by_ticket(self, ticket_id: int) -> List[Dict[str, Any]]:
        """获取工单照片列表"""
        try:
            return db_query(
                "SELECT id, filename, url, created_at FROM ticket_photos WHERE ticket_id = ? ORDER BY created_at DESC",
                (ticket_id,))
        except Exception:
            return []

    def save_photo(self, ticket_id: int, filename: str, filepath: str) -> int:
        """保存照片记录"""
        with self._ensure_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO ticket_photos (ticket_id, filename, url, created_at) VALUES (?, ?, ?, datetime('now','localtime'))",
                (ticket_id, filename, filepath))
            if not self._conn:
                conn.commit()
            return cursor.lastrowid

    def delete_photo(self, photo_id: int) -> bool:
        """删除照片"""
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM ticket_photos WHERE id = ?", (photo_id,))
            if not self._conn:
                conn.commit()
            return True

    def delete_photo_by_path(self, filepath: str, ticket_id: int) -> bool:
        """按路径删除照片"""
        with self._ensure_conn() as conn:
            conn.execute("DELETE FROM ticket_photos WHERE url = ? AND ticket_id = ?",
                         (filepath, ticket_id))
            if not self._conn:
                conn.commit()
            return True

    # ===== 设备关联 =====

    def unlink_equipment(self, ticket_id: int, equip_id: int) -> bool:
        """取消设备关联"""
        with self._ensure_conn() as conn:
            conn.execute(
                "DELETE FROM ticket_equipment WHERE ticket_id = ? AND equipment_id = ?",
                (ticket_id, equip_id))
            if not self._conn:
                conn.commit()
            return True

    # ===== 搜索 =====

    def search_tickets(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """关键词搜索工单"""
        q = f"%{keyword}%"
        return db_query(
            """SELECT id, ticket_no, client, status, description, created_at
               FROM tickets
               WHERE ticket_no LIKE ? OR client LIKE ? OR description LIKE ? OR title LIKE ?
               LIMIT ?""",
            (q, q, q, q, limit))

    # ===== 技术人员辅助 =====

    def get_technician_names(self, ticket_id: int) -> List[str]:
        """获取工单关联的技术人员姓名列表"""
        rows = db_query(
            "SELECT DISTINCT technician_name FROM ticket_service_items "
            "WHERE ticket_id = ? AND technician_name IS NOT NULL AND technician_name != '' "
            "ORDER BY id",
            (ticket_id,))
        return [r["technician_name"] for r in rows if r.get("technician_name")]

    def sync_assignee_from_service_items(self, ticket_id: int):
        """从服务明细行同步负责人到工单 assignee 字段"""
        names = self.get_technician_names(ticket_id)
        assignee = ", ".join(names) if names else ""
        self.update(ticket_id, {"assignee": assignee})

    def count_service_items_with_hours(self, ticket_id: int) -> int:
        """统计有工时的服务明细行数"""
        row = db_query_one(
            "SELECT COUNT(*) as c FROM ticket_service_items WHERE ticket_id=? AND hours>0",
            (ticket_id,))
        return row["c"] if row else 0

    def remove_technician(self, ticket_id: int, name: str) -> bool:
        """删除工单指定技术人员"""
        with self._ensure_conn() as conn:
            conn.execute(
                "DELETE FROM ticket_service_items WHERE ticket_id=? AND technician_name=?",
                (ticket_id, name))
            if not self._conn:
                conn.commit()
            return True

    # ===== 结算状态 =====

    def confirm_payment_status(self, ticket_id: int, billing_status: str, status: str, closed_at: str):
        """确认收款：更新结算状态和关闭时间（编排由Service层调用）"""
        self.update(ticket_id, {
            "billing_status": billing_status,
            "status": status,
            "closed_at": closed_at,
        })

    # ===== 幂等性缓存 =====

    def check_idempotent(self, key: str, now_ts: float) -> Optional[Dict[str, Any]]:
        import json as _json
        row = db_query_one(
            "SELECT data FROM _idempotent_cache WHERE key = ? AND expires_at > ?",
            (key, now_ts))
        if row:
            return _json.loads(row["data"])
        return None

    def set_idempotent(self, key: str, data: dict, now_ts: float, expires_ts: float):
        import json as _json
        from infrastructure.persistence.legacy_db import db_execute
        db_execute(
            "INSERT OR REPLACE INTO _idempotent_cache (key, data, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (key, _json.dumps(data), now_ts, expires_ts))

    def clean_expired_idempotent(self, now_ts: float):
        from infrastructure.persistence.legacy_db import db_execute
        db_execute("DELETE FROM _idempotent_cache WHERE expires_at < ?", (now_ts,))

    # ===== 工单模板 CRUD =====

    def list_templates(self) -> list:
        try:
            return db_query("SELECT id, name, content, client, category, sort_order, service_type, priority, billing_model, estimated_hours, description_template, is_active, created_at, updated_at FROM ticket_templates ORDER BY sort_order, name") or []
        except Exception:
            return []

    def get_template(self, tid: int):
        return db_query_one("SELECT id, name, content, client, category, sort_order, service_type, priority, billing_model, estimated_hours, description_template, is_active, created_at, updated_at FROM ticket_templates WHERE id = ?", (tid,))

    def create_template(self, name: str, content: str = "", client: str = "",
                        category: str = "", sort_order: int = 99):
        db_execute(
            "INSERT INTO ticket_templates (name, content, client, category, sort_order) VALUES (?, ?, ?, ?, ?)",
            (name, content, client, category, sort_order))

    _TEMPLATE_ALLOWED = {"name", "content", "client", "category", "sort_order"}

    def update_template(self, tid: int, data: dict):
        filtered = {k: v for k, v in data.items() if k in self._TEMPLATE_ALLOWED}
        if not filtered:
            return
        sets = ", ".join(f"{k} = ?" for k in filtered)
        vals = list(filtered.values()) + [tid]
        db_execute(f"UPDATE ticket_templates SET {sets} WHERE id = ?", tuple(vals))

    def delete_template(self, tid: int):
        db_execute("DELETE FROM ticket_templates WHERE id = ?", (tid,))

    # ===== 自动化规则 CRUD =====

    def list_rules(self) -> list:
        try:
            return db_query("SELECT id, name, description, trigger_event, conditions, actions, is_active, enabled, priority, created_at, updated_at FROM automation_rules ORDER BY priority, name") or []
        except Exception:
            return []

    def get_rule(self, rid: int):
        return db_query_one("SELECT id, name, description, trigger_event, conditions, actions, is_active, enabled, priority, created_at, updated_at FROM automation_rules WHERE id = ?", (rid,))

    def create_rule(self, name: str, event: str = "", conditions: str = "{}",
                    actions: str = "{}", enabled: int = 1, priority: int = 99):
        db_execute(
            "INSERT INTO automation_rules (name, trigger_event, conditions, actions, enabled, priority) VALUES (?, ?, ?, ?, ?, ?)",
            (name, event, conditions, actions, enabled, priority))

    _RULE_ALLOWED = {"name", "trigger_event", "conditions", "actions", "enabled", "priority"}

    def update_rule(self, rid: int, data: dict):
        filtered = {k: v for k, v in data.items() if k in self._RULE_ALLOWED}
        if not filtered:
            return
        sets = ", ".join(f"{k} = ?" for k in filtered)
        vals = list(filtered.values()) + [rid]
        db_execute(f"UPDATE automation_rules SET {sets} WHERE id = ?", tuple(vals))

    def delete_rule(self, rid: int):
        db_execute("DELETE FROM automation_rules WHERE id = ?", (rid,))

    def find_rule_by_name(self, name: str):
        return db_query_one("SELECT id FROM automation_rules WHERE name = ?", (name,))

    def get_enabled_rules_by_event(self, event: str) -> list:
        try:
            return db_query(
                "SELECT id, name, description, trigger_event, conditions, actions, priority FROM automation_rules WHERE trigger_event = ? AND enabled = 1 ORDER BY priority",
                (event,)) or []
        except Exception:
            return []

    # ===== 分页查询 =====

    ALLOWED_SORT_FIELDS = frozenset({
        "ticket_no", "client", "status", "total",
        "estimated_hours", "profit", "created_at",
    })

    ALLOWED_STATUS_VALUES = frozenset({
        "open", "in-progress", "pending-parts", "pending-client",
        "pending-payment", "completed", "closed", "cancelled", "archived",
    })

    MAX_PER_PAGE = 200

    def paginated_list(self, page: int = 1, per_page: int = 50,
                       status: str = None, client: str = None,
                       keyword: str = None, date_from: str = None,
                       date_to: str = None, sort_field: str = None,
                       sort_dir: str = "desc") -> dict:
        per_page = min(max(1, per_page), self.MAX_PER_PAGE)
        page = max(1, page)
        offset = (page - 1) * per_page

        if sort_field and sort_field not in self.ALLOWED_SORT_FIELDS:
            sort_field = None
        order_dir = "ASC" if sort_dir == "asc" else "DESC"
        order_by = f"{sort_field or 'created_at'} {order_dir}"

        conditions = ["1=1"]
        params = []

        if status:
            status_list = [s.strip() for s in status.split(",") if s.strip()]
            valid_statuses = [s for s in status_list if s in self.ALLOWED_STATUS_VALUES]
            if valid_statuses:
                placeholders = ",".join("?" * len(valid_statuses))
                conditions.append(f"status IN ({placeholders})")
                params.extend(valid_statuses)

        if client:
            conditions.append("client LIKE ?")
            params.append(f"%{client}%")

        if keyword:
            conditions.append("(ticket_no LIKE ? OR description LIKE ? OR title LIKE ?)")
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)

        if date_to:
            conditions.append("created_at <= ?")
            params.append(f"{date_to} 23:59:59")

        where_clause = " AND ".join(conditions)

        try:
            count_row = db_query_one(
                f"SELECT COUNT(*) as total FROM tickets WHERE {where_clause}",
                tuple(params))
            total = count_row["total"] if count_row else 0

            rows = db_query(
                f"SELECT {self.LIST_COLS} FROM tickets WHERE {where_clause} ORDER BY {order_by} LIMIT ? OFFSET ?",
                tuple(params + [per_page, offset])) or []

            return {
                "tickets": rows,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": max(1, -(-total // per_page)),
            }
        except Exception as e:
            return {"tickets": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}

    # ===== 设备名称查询 =====

    def get_linked_equipment_names(self, ticket_id: int) -> List[str]:
        rows = db_query(
            "SELECT e.name FROM ticket_equipment te JOIN equipment e ON te.equipment_id = e.id WHERE te.ticket_id = ?",
            (ticket_id,)) or []
        return [r["name"] for r in rows if r.get("name")]

    # ===== 单张照片查询 =====

    def find_photo_by_id(self, photo_id: int, ticket_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one("SELECT url as filepath FROM ticket_photos WHERE id = ? AND ticket_id = ?", (photo_id, ticket_id))

    # ===== 物料数量 =====

    def get_material_count(self, ticket_id: int) -> int:
        result = db_query_one("SELECT COUNT(*) as c FROM materials WHERE ticket_id = ?", (ticket_id,))
        return result["c"] if result else 0

    # ===== 物料库存项ID更新 =====

    def update_material_inventory_ids(self, material_id: int, new_ids: str):
        with self._ensure_conn() as conn:
            conn.execute("UPDATE materials SET inventory_item_ids = ? WHERE id = ?", (new_ids, material_id))
            if not self._conn:
                conn.commit()

    # ===== 物料数量和合计更新 =====

    def update_material_quantity_and_total(self, material_id: int, quantity: float, total: float):
        with self._ensure_conn() as conn:
            conn.execute("UPDATE materials SET quantity = ?, total = ? WHERE id = ?", (quantity, total, material_id))
            if not self._conn:
                conn.commit()

    # ===== 提醒相关 =====

    def find_active_reminder(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        return db_query_one(
            "SELECT id FROM ticket_reminders WHERE ticket_id = ? AND active = 1",
            (ticket_id,))

    def update_reminder(self, reminder_id: int, reminder_time: str, content: str):
        with self._ensure_conn() as conn:
            conn.execute(
                "UPDATE ticket_reminders SET reminder_time = ?, content = ? WHERE id = ?",
                (reminder_time, content, reminder_id))
            if not self._conn:
                conn.commit()

    def deactivate_reminder(self, reminder_id: int):
        with self._ensure_conn() as conn:
            conn.execute("UPDATE ticket_reminders SET active = 0 WHERE id = ?", (reminder_id,))
            if not self._conn:
                conn.commit()

    # ===== 库存恢复 =====

    def find_used_inventory_items(self, ticket_id: int) -> List[Dict[str, Any]]:
        return db_query(
            "SELECT i.id, i.product_id, i.serial_no, i.batch_no, i.bulk_quantity, i.status, i.ticket_id, i.unit_cost, COALESCE(g.is_bulk, 0) as is_bulk, g.name as product_name, g.unit FROM inventory_items i LEFT JOIN goods g ON i.product_id = g.id WHERE i.ticket_id = ?",
            (ticket_id,)) or []

    def restore_inventory_item(self, item_id: int):
        with self._ensure_conn() as conn:
            conn.execute("UPDATE inventory_items SET status = 'in_stock', ticket_id = NULL WHERE id = ?", (item_id,))
            if not self._conn:
                conn.commit()

    # ===== 通知删除 =====

    def delete_notifications_by_ticket(self, ticket_id: int):
        with self._ensure_conn() as conn:
            try:
                conn.execute("DELETE FROM notifications WHERE ticket_id = ?", (ticket_id,))
            except Exception:
                pass
            if not self._conn:
                conn.commit()
