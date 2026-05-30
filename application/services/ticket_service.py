"""
博通 (Botong) — 工单应用服务（新架构版）
使用 Repository + EventBus + DI 容器，取代旧版 lib/modules/ticket.py
"""

import csv
import json
import logging
import os
import re
from io import StringIO
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from calendar import monthrange

from domain.events import (
    EventBus, TicketCreated, TicketStatusChanged, TicketCompleted,
    TicketPaymentConfirmed, TicketDeleted
)
from domain.exceptions import TicketNotFoundError, TicketValidationError
from domain.amount_calculator import AmountCalculator

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TicketService:
    """
    工单应用服务

    职责:
        - 工单 CRUD 完整业务流程
        - 状态流转校验（含领域事件）
        - 金额计算
        - 工单编号生成

    依赖注入:
        repo: SqliteTicketRepository（或任意实现）
        event_bus: EventBus（可选，为 None 时不发事件）
        config: Settings 或 dict
    """

    # 状态流转定义（与旧前端 STATUS_FLOW 对齐）
    STATUS_FLOW = {
        "open": ["in-progress", "cancelled"],
        "in-progress": ["pending-parts", "pending-client", "pending-payment", "cancelled"],
        "pending-parts": ["in-progress", "cancelled"],
        "pending-client": ["in-progress", "cancelled"],
        "pending-payment": ["completed", "in-progress"],
        "completed": ["closed"],
        "closed": ["archived"],
        "cancelled": ["open"],
        "archived": [],
    }

    # 状态显示名
    STATUS_NAMES = {
        "open": "待处理",
        "in-progress": "进行中",
        "pending-parts": "待配件",
        "pending-client": "待确认",
        "pending-payment": "待结算",
        "completed": "已完成",
        "closed": "已关闭",
        "cancelled": "已取消",
        "archived": "已归档",
    }

    _pending_confirmations = {}  # NOTE: 类级别字典，单进程部署安全；多 worker 部署需迁移到 Redis/DB

    def __init__(self, repo, event_bus: EventBus = None, config: Any = None,
                 client_service=None, finance_service=None, goods_service=None,
                 inventory_service=None, equipment_service=None, technician_service=None,
                 technician_repo=None, reminder_service=None, todo_service=None):
        self._repo = repo
        self._event_bus = event_bus
        self._config = config or {}
        self._client_service = client_service
        self._finance_service = finance_service
        self._goods_service = goods_service
        self._inventory_service = inventory_service
        self._equipment_service = equipment_service
        self._technician_service = technician_service
        self._technician_repo = technician_repo
        self._reminder_service = reminder_service
        self._todo_service = todo_service

    def _ensure_svc(self, attr_name, service_name):
        svc = getattr(self, attr_name, None)
        if svc is None:
            raise RuntimeError(f"TicketService: {attr_name} not injected (expected {service_name})")
        return svc

    def set_finance_service(self, svc):
        self._finance_service = svc

    def set_inventory_service(self, svc):
        self._inventory_service = svc

    def set_reminder_service(self, svc):
        self._reminder_service = svc

    def set_todo_service(self, svc):
        self._todo_service = svc

    def set_nl_service(self, svc):
        self._nl_service = svc

    def set_export_service(self, svc):
        self._export_service = svc

    # ===== 属性暴露 =====
    @property
    def repo(self):
        """暴露仓储实例（兼容旧代码）"""
        return self._repo

    # ===== 幂等性缓存 =====

    def check_idempotent(self, key: str):
        import time
        if not key:
            return None
        try:
            return self._repo.check_idempotent(key, time.time())
        except Exception:
            return None

    def set_idempotent(self, key: str, data: dict, ttl: int = 300):
        import time
        if not key:
            return
        now = time.time()
        try:
            self._repo.set_idempotent(key, data, now, now + ttl)
        except Exception:
            pass

    def clean_expired_idempotent(self):
        import time
        try:
            self._repo.clean_expired_idempotent(time.time())
        except Exception:
            pass

    # ===== 金额计算 =====

    @staticmethod
    def get_ticket_due_amount(ticket: dict) -> float:
        total_due = float(ticket.get("total_with_tax") or 0)
        if total_due > 0:
            return total_due
        total_due = float(ticket.get("total") or 0)
        if total_due > 0:
            return total_due
        return (float(ticket.get("total_labor") or 0)
                + float(ticket.get("total_material") or 0)
                + float(ticket.get("total_external") or 0))

    # ===== 工单 CRUD =====

    def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """获取工单详情"""
        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")
        ticket["status_name"] = self.STATUS_NAMES.get(
            ticket.get("status"), ticket.get("status"))
        return ticket

    def create_ticket(self, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """创建工单（完整业务流程）

        支持两种调用方式：
          - create_ticket({"client": ..., "content": ...})
          - create_ticket(client="...", content="...", title="...")
        """
        if data is None and kwargs:
            data = kwargs
        data = data or {}
        from datetime import datetime

        # 1. 参数校验
        client = (data.get("client") or "").strip()
        content = (data.get("content") or data.get("description") or "").strip()
        if not client:
            raise TicketValidationError("客户名称不能为空")
        if not content:
            raise TicketValidationError("服务内容不能为空")

        # 1.5 客户存在性校验/自动创建
        client_svc = self._client_service
        client_id = None
        if client_svc:
            try:
                existing_client = client_svc.get_client(client)
                client_id = existing_client.get("id") if existing_client else None
            except Exception:
                client_id = None
            if not client_id:
                try:
                    contact = (data.get("contact") or "").strip()
                    new_client = client_svc.create_client(name=client, contact=contact or "", phone=data.get("phone", ""))
                    client_id = new_client.get("id") if isinstance(new_client, dict) else None
                    logger.info(f"自动创建客户: {client}")
                except Exception:
                    client_id = None
        else:
            try:
                client_repo = self._client_repo if hasattr(self, '_client_repo') else None
                if not client_repo:
                    from infrastructure.di.service_injection import inject_service
                    try:
                        client_repo = inject_service('client_service')._repo
                    except Exception:
                        client_repo = None
                if client_repo:
                    existing = client_repo.find_by_name(client)
                    if existing:
                        client_id = existing.get("id")
                    else:
                        client_id = client_repo.save({
                            "name": client,
                            "contact": (data.get("contact") or "").strip(),
                            "phone": data.get("phone", ""),
                            "created_at": datetime.now().isoformat(),
                        })
                        logger.info(f"(Repo Fallback) 自动创建客户: {client}")
                else:
                    client_id = None
            except Exception:
                client_id = None

        # 2. 构建工单数据
        ticket_no = self._repo.generate_ticket_no()
        if not ticket_no:
            raise TicketValidationError("工单编号生成失败，请重试")
        now = datetime.now().isoformat()

        ticket = {
            "ticket_no": ticket_no,
            "client": client,
            "description": content,
            "title": data.get("title", content[:50]),
            "contact": (data.get("contact") or "").strip(),
            "location": (data.get("location") or "").strip(),
            "service_type": data.get("service_type", data.get("billing_model", "")),
            "priority": data.get("priority", "M"),
            "assignee": data.get("assignee", ""),
            "estimated_hours": float(data.get("estimated_hours", 0)),
            "billing_model": data.get("billing_model", "hourly"),
            "status": "open",
            "created_by": data.get("created_by", ""),
            "appointment_at": data.get("appointment_at"),
            "travel_distance": float(data.get("travel_distance", 0)),
            "travel_rate": float(data.get("travel_rate", 0)),
        }

        # 3. 持久化
        ticket_id = self._repo.save(ticket)
        ticket["id"] = ticket_id

        # 3.5 关联设备
        equip_id = data.get("equipment_id")
        if equip_id:
            self._repo.link_equipment(ticket_id, int(equip_id))
            self._repo.add_history(
                ticket_id, "link",
                f"关联设备 #{equip_id}",
                data.get("created_by", ""))

        # 4. 添加操作历史
        self._repo.add_history(
            ticket_id, "create",
            f"创建工单 - {client}",
            data.get("created_by", ""))

        # 5. 设置工单负责人（写 tickets.assignee + ticket_technicians）
        assignee = data.get("assignee", "").strip()
        if assignee and ticket_id:
            try:
                self._repo.update(ticket_id, {"assignee": assignee})
                tech_list = self._repo.get_technicians(ticket_id)
                if not any(t.get("name") == assignee for t in tech_list):
                    cost_rate = 30
                    try:
                        techs = self._repo.search_technicians(assignee)
                        if techs:
                            cost_rate = techs[0].get("cost_rate", 30)
                    except Exception:
                        pass
                    self._repo.add_technician(ticket_id, assignee, cost_rate, 0)
            except Exception as e:
                logger.warning(f"设置工单负责人失败: {e}")

        # 6. 记录交通费
        travel_dist = float(data.get("travel_distance", 0))
        travel_rate = float(data.get("travel_rate", 2.0))
        if travel_dist > 0 and ticket_id:
            travel_fee = travel_dist * travel_rate
            try:
                self._repo.update(ticket_id, {
                    "travel_distance": travel_dist,
                    "travel_rate": travel_rate,
                    "total_external": travel_fee,
                })
            except Exception as e:
                logger.warning(f"记录交通费失败: {e}")

        # 7. 发布领域事件（人工成本在完工时由 TicketComplete 统一记录）
        if self._event_bus:
            self._event_bus.dispatch(TicketCreated(
                ticket_id=ticket_id,
                ticket_no=ticket_no,
                client=client,
                assignee=ticket.get("assignee", ""),
            ))

        # 8. 自动创建预约提醒
        appointment_at = data.get("appointment_at", "").strip()
        if appointment_at and ticket_id:
            try:
                self._sync_reminder_on_appointment_change(ticket_id, appointment_at, client, data.get("description", ""))
            except Exception as e:
                logger.warning(f"创建预约提醒失败: {e}")

        # 9. 自动关联服务项目
        service_fee_id = data.get("service_fee_id")
        if service_fee_id and ticket_id:
            try:
                assignee_name = assignee or ""
                hours = float(data.get("estimated_hours", 0))
                self._repo.add_service_item(ticket_id, assignee_name, int(service_fee_id), hours)
            except Exception as e:
                logger.warning(f"关联服务项目失败: {e}")

        # 10. 记录配件费
        parts_fee = data.get("parts_fee")
        if parts_fee and ticket_id:
            try:
                self._repo.update(ticket_id, {"parts_fee": float(parts_fee)})
            except Exception as e:
                logger.warning(f"记录配件费失败: {e}")

        # 6. 返回完整数据
        return self.get_ticket(ticket_id)

    def update_ticket(self, ticket_id: int, data=None, **kwargs) -> Dict[str, Any]:
        """更新工单字段

        兼容两种调用方式:
            新版: update_ticket(id, {"client": "...", ...})
            旧版: update_ticket(id, client="...", notes="...")
        """
        # 兼容旧版 **kwargs 调用
        if data is None and kwargs:
            data = kwargs
        elif isinstance(data, dict):
            # 新版 dict 调用，合并 kwargs 中可能的额外字段
            if kwargs:
                data = {**data, **kwargs}
        else:
            data = data or {}
        if not isinstance(data, dict):
            data = {}

        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")

        # 记录变更历史
        changes = []
        for key in ["client", "description", "priority", "assignee",
                     "appointment_at", "travel_distance", "travel_rate"]:
            if key in data and str(data[key]) != str(ticket.get(key, "")):
                changes.append(f"{key}: {ticket.get(key, '')} → {data[key]}")

        self._repo.update(ticket_id, data)

        if changes:
            self._repo.add_history(
                ticket_id, "update",
                "; ".join(changes),
                data.get("operator", ""))

        if "appointment_at" in data:
            self._sync_reminder_on_appointment_change(
                ticket_id, data.get("appointment_at"),
                ticket.get("client", ""), ticket.get("title", ""))

        return self.get_ticket(ticket_id)

    def delete_ticket(self, ticket_id: int) -> bool:
        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")

        ticket_no = ticket.get("ticket_no", "")

        used_items = self._repo.find_used_inventory_items(ticket_id)
        for item in used_items:
            if not item.get("is_bulk"):
                self._repo.restore_inventory_item(item["id"])

        self._repo.delete_notifications_by_ticket(ticket_id)
        self._repo.delete(ticket_id)

        if self._event_bus:
            self._event_bus.dispatch(TicketDeleted(
                ticket_id=ticket_id,
                ticket_no=ticket_no,
            ))

        return True

    # ===== 状态流转 =====

    def transition_status(self, ticket_id: int, new_status: str,
                          note: str = "", operator: str = "") -> Dict[str, Any]:
        """状态流转（含校验 + 领域事件）"""
        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")

        old_status = ticket["status"]
        allowed = self.STATUS_FLOW.get(old_status, [])

        if new_status not in allowed:
            raise TicketValidationError(
                f"不允许从「{self.STATUS_NAMES.get(old_status, old_status)}」"
                f"流转到「{self.STATUS_NAMES.get(new_status, new_status)}」")

        self._validate_status_transition(ticket, old_status, new_status)

        # 更新状态
        update_data = {"status": new_status}

        # 特殊处理：流转到 closed 时记录关闭时间
        if new_status == "closed":
            update_data["closed_at"] = datetime.now().isoformat()

        # 特殊处理：流转到 pending-payment 时自动计算总额
        if new_status == "pending-payment":
            self._calc_total(ticket, update_data)

        self._repo.update(ticket_id, update_data)

        # 添加历史
        history_note = (f"状态变更: "
                        f"{self.STATUS_NAMES.get(old_status, old_status)} → "
                        f"{self.STATUS_NAMES.get(new_status, new_status)}")
        if note:
            history_note += f" ({note})"
        self._repo.add_history(ticket_id, "status", history_note, operator)

        # 发布领域事件
        if self._event_bus:
            self._event_bus.dispatch(TicketStatusChanged(
                ticket_id=ticket_id,
                old_status=old_status,
                new_status=new_status,
                ticket_no=ticket.get("ticket_no", ""),
                client=ticket.get("client", ""),
            ))

            if new_status == "completed":
                self._event_bus.dispatch(TicketCompleted(
                    ticket_id=ticket_id,
                    ticket_no=ticket.get("ticket_no", ""),
                    total=update_data.get("total", ticket.get("total", 0)),
                    client=ticket.get("client", ""),
                ))

        return self.get_ticket(ticket_id)

    def _validate_status_transition(self, ticket: Dict[str, Any], 
                                    old_status: str, new_status: str):
        """校验状态流转的业务规则"""
        
        if new_status == "in-progress":
            assignee = ticket.get("assignee", "").strip()
            if not assignee:
                raise TicketValidationError("开始处理前必须先分派技术员")
        
        if new_status == "pending-payment":
            total = float(ticket.get("total", 0) or 0)
            if total <= 0:
                raise TicketValidationError("流转到待结算状态前必须先计算工单总额")
        
        if new_status == "completed":
            current_status = ticket.get("status", "")
            if current_status != "pending-payment":
                raise TicketValidationError("只有待结算状态的工单才能完成")
        
        if new_status == "closed":
            billing_status = ticket.get("billing_status", "")
            if billing_status not in ("paid", "free"):
                raise TicketValidationError("未收款的工单不能直接关闭")

    def _calc_total(self, ticket: Dict[str, Any], update_data: Dict[str, Any]):
        """计算工单总额 — 委托到 recalc_ticket_total（唯一计算入口）"""
        ticket_id = ticket.get("id") or ticket.get("ticket_id")
        if ticket_id:
            self.recalc_ticket_total(ticket_id)

    # ===== 列表查询 =====

    def list_tickets(self, status: str = None, client: str = None,
                     keyword: str = None, billing: str = None,
                     date_from: str = None, date_to: str = None,
                     assignee: str = None,
                     page: int = 1, per_page: int = 50,
                     sort_field: str = None, sort_dir: str = "desc"
                     ) -> dict:
        """工单列表查询"""
        filters = {}
        if status:
            filters["status"] = status
        if client:
            filters["client"] = client
        if keyword:
            filters["q"] = keyword
        if billing:
            filters["billing"] = billing
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if assignee:
            filters["assignee"] = assignee

        tickets, total = self._repo.find_list(
            filters=filters,
            page=page,
            per_page=per_page,
            sort_field=sort_field,
            sort_dir=sort_dir,
        )

        # 添加状态中文名
        for t in tickets:
            t["status_name"] = self.STATUS_NAMES.get(
                t.get("status"), t.get("status"))

        # 批量查询利润
        if tickets:
            ids = [t["id"] for t in tickets]
            placeholders = ",".join(["?"] * len(ids))
            profits = self._batch_get_profit(ids, placeholders)
            profit_map = {p["ticket_id"]: p for p in profits}
            for t in tickets:
                p = profit_map.get(t["id"], {})
                t["profit"] = p.get("profit", 0)
                t["profit_income"] = p.get("income", 0)
                t["profit_expense"] = p.get("expense", 0)

        return {"tickets": tickets, "total": total}

    def _batch_get_profit(self, ids: List[int], placeholders: str) -> list:
        finance_svc = self._finance_service
        if finance_svc and hasattr(finance_svc, 'get_batch_profit'):
            return finance_svc.get_batch_profit(ids)
        return []

    # ===== 统计 =====

    def get_status_stats(self) -> Dict[str, int]:
        """获取各状态工单数量统计"""
        return self._repo.get_status_stats()

    # ===== 物料管理 =====

    def add_material(self, ticket_id: int, data=None, quantity=1, unit_price=0, total=0, item_ids="", **kwargs):
        """
        添加物料

        兼容两种调用方式:
            新版: add_material(ticket_id, {"name": "...", "quantity": 1, ...})
            旧版: add_material(ticket_id, name, quantity, unit_price, total, item_ids, goods_id=...)
        """
        cost_price = None
        if isinstance(data, dict):
            name = data.get("name") or data.get("product_name") or ""
            product_id = data.get("product_id") or kwargs.get("product_id")
            quantity = float(data.get("quantity", 1))
            unit_price = float(data.get("unit_price", 0))
            cost_price = data.get("cost_price")
            notes = data.get("notes", "")
        else:
            name = data or ""
            product_id = kwargs.get("goods_id") or kwargs.get("product_id")
            notes = ""

        if not name and not product_id:
            raise TicketValidationError("物料名称或商品 ID 不能为空")

        if product_id and not name:
            goods_svc = self._goods_service
            try:
                product = goods_svc.get_goods(product_id) if goods_svc else None
            except Exception:
                product = None
            if product:
                name = product["name"]
                if unit_price == 0:
                    unit_price = float(product.get("selling_price") or product.get("retail_price") or 0)
                if cost_price is None:
                    cost_price = float(product.get("cost_price") or 0) or None

        if cost_price is None:
            cost_price = unit_price
        selling_total = round(quantity * unit_price, 2)
        total_cost = round(quantity * cost_price, 2)

        material_id = self._repo.add_material(ticket_id, name, name, product_id,
                                               quantity, unit_price, selling_total,
                                               total_cost, notes)

        self.recalc_ticket_total(ticket_id)

        self._repo.add_history(ticket_id, "material",
                               f"添加物料: {name} × {quantity} = ¥{selling_total:.2f}")

        return {"id": material_id, "ticket_id": ticket_id, "name": name,
                "product_name": name, "product_id": product_id,
                "quantity": quantity, "unit_price": unit_price,
                "total": selling_total, "total_cost": total_cost, "notes": notes}

    def add_material_with_inventory(self, ticket_id: int, data: dict) -> Dict[str, Any]:
        """添加物料（含库存扣减，API 层统一入口）"""
        product_id = data.get("product_id")
        material_name = data.get("name", "")
        quantity = float(data.get("quantity", 1))
        unit_price = float(data.get("unit_price", 0) or 0)

        if not material_name and not product_id:
            raise ValueError("请选择商品或输入物料名称")

        item_ids = ""
        if product_id:
            goods_svc = self._goods_service
            if goods_svc:
                prod = goods_svc.get_goods(product_id)
                if not prod:
                    raise ValueError("商品不存在")
                material_name = prod["name"]
                if unit_price <= 0:
                    unit_price = float(prod.get("selling_price") or prod.get("cost_price") or 0)
            try:
                inv_svc = self._inventory_service
                if inv_svc:
                    used = inv_svc.use_inventory(product_id, quantity, ticket_id, f"工单{ticket_id}领用")
                    if used:
                        item_ids = ",".join(str(u["id"]) for u in used if u.get("id"))
            except Exception as e:
                raise ValueError(f"库存扣减失败: {str(e)}")

        total = unit_price * quantity
        result = self.add_material(ticket_id, material_name, quantity=quantity,
                                    unit_price=unit_price, total=total,
                                    item_ids=item_ids, goods_id=product_id)
        self.auto_progress_status(ticket_id, trigger_field="add_material")

        ticket = self._repo.find_by_id(ticket_id)
        ticket_no = ticket.get("ticket_no", "") if ticket else ""
        return {
            "message": f"已添加物料: {material_name} × {quantity}",
            "summary": f"已为工单 {ticket_no} 添加物料：{material_name} × {quantity}，¥{unit_price}×{quantity}=¥{total:.2f}",
            "name": material_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total": total,
            **result,
        }

    # ===== 完工结算 =====

    def complete_ticket(self, ticket_id: int, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        工单完工结算 — 统一入口

        包含:
          - 服务明细行费用汇总
          - 物料费汇总 + 库存扣减（事务保护）
          - 折扣计算
          - 交通费
          - 状态流转（先改状态防止重复提交）
          - 自动记录支出（物料成本 + 交通费）
        """
        data = data or {}
        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")

        if ticket.get("status") in ("completed", "archived"):
            raise TicketValidationError(f"工单 #{ticket_id} 已完工，不可重复结算")

        # 1. 服务明细行费用汇总
        items = self._repo.get_service_items(ticket_id) or []
        labor_total = sum(float(i.get("line_total", 0) or 0) for i in items)
        labor_cost = sum(float(i.get("line_cost", 0) or 0) for i in items)

        # 2. 物料费汇总 + 库存扣减
        materials = self._repo.find_materials_by_ticket(ticket_id) or []
        material_total = sum(float(m.get("total", 0) or 0) for m in materials)
        material_cost = sum(float(m.get("total_cost", 0) or 0) for m in materials)

        # 3. 交通费
        travel_dist = float(data.get("travel_distance", ticket.get("travel_distance", 0)) or 0)
        travel_rate = float(data.get("travel_rate", ticket.get("travel_rate", 0)) or 0)
        travel_fee = round(travel_dist * travel_rate, 2) if travel_dist > 0 else 0.0

        # 4. 折扣 + 总额（统一委托 AmountCalculator）
        discount_type = data.get("discount_type", ticket.get("discount_type", "")) or ""
        discount_value = float(data.get("discount_value", ticket.get("discount_value", 0)) or 0)
        total = AmountCalculator.calc_total(
            labor_total, material_total, travel_fee,
            discount_type, discount_value)
        discount_amount, _ = AmountCalculator.calc_discount(
            labor_total + material_total + travel_fee,
            discount_type, discount_value)

        # 5. 税费（统一委托 AmountCalculator）
        tax_rate = float(data.get("tax_rate", ticket.get("tax_rate", 0)) or 0)
        tax_amount, total_with_tax = AmountCalculator.calc_total_with_tax(total, tax_rate)

        # 6. 使用事务保护所有数据库操作
        from infrastructure.persistence.database import UnitOfWork

        with UnitOfWork() as uow:
            # 6.1 更新工单字段
            update_data = {
                "total_labor": labor_total,
                "total_material": material_total,
                "total_external": travel_fee,
                "discount_type": discount_type,
                "discount_value": discount_value,
                "total": total,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total_with_tax": total_with_tax,
                "travel_distance": travel_dist,
                "travel_rate": travel_rate,
            }
            if data.get("notes"):
                update_data["notes"] = data["notes"]
            if data.get("closed_at"):
                update_data["closed_at"] = data["closed_at"]
            self._repo.update(ticket_id, update_data, conn=uow.conn)

            # 6.2 库存扣减（在事务内执行）
            if material_cost > 0 or materials:
                try:
                    inv_svc = self._inventory_service
                    if inv_svc:
                        deducted_item_ids = set()
                        for mat in materials:
                            item_ids_str = mat.get("inventory_item_ids", "")
                            goods_id = mat.get("goods_id") or mat.get("product_id")
                            qty = float(mat.get("quantity", 1) or 1)
                            if not item_ids_str or not goods_id:
                                continue
                            
                            deducted_qty = 0
                            for iid_str in item_ids_str.split(","):
                                iid_str = iid_str.strip()
                                if not iid_str.isdigit():
                                    continue
                                item_id = int(iid_str)
                                
                                if item_id in deducted_item_ids:
                                    continue
                                
                                inv_item = self._repo.find_inventory_item(item_id)
                                if not inv_item:
                                    continue
                                
                                if inv_item.get("status") not in ("in_stock", "available"):
                                    continue
                                
                                if inv_item.get("bulk_quantity") and float(inv_item["bulk_quantity"]) > 0:
                                    bulk_qty = self._inventory_service._parse_bulk_quantity(inv_item)
                                    if bulk_qty > 0 and qty < bulk_qty:
                                        self._repo.deduct_bulk_quantity_atomic(
                                            uow.conn, item_id, qty, ticket_id)
                                    else:
                                        self._repo.mark_item_used_atomic(uow.conn, item_id, ticket_id)
                                else:
                                    self._repo.mark_item_used_atomic(uow.conn, item_id, ticket_id)
                                
                                deducted_item_ids.add(item_id)
                                deducted_qty += float(mat.get("quantity", 1) or 1)
                            
                            if deducted_qty > 0:
                                self._repo.add_log_atomic(
                                    uow.conn, goods_id, "工单出库", deducted_qty,
                                    "库房", f"工单#{ticket_id}",
                                    f"工单领料: {mat.get('goods_name', '')} × {deducted_qty}")
                except Exception as e:
                    logger.warning(f"库存扣减失败 (ticket#{ticket_id}): {e}")

            # 6.3 状态流转
            current_status = ticket.get("status", "")
            target_status = data.get("status", "pending-payment")
            if current_status not in ("completed", "archived"):
                try:
                    self._repo.update_status_with_history(
                        ticket_id, target_status, "完工结算", data.get("operator", ""), conn=uow.conn)
                except TicketValidationError:
                    try:
                        self._repo.update_status_with_history(
                            ticket_id, "pending-payment", "完工结算", data.get("operator", ""), conn=uow.conn)
                    except Exception:
                        pass

            # 6.4 操作历史（在事务内记录）
            self._repo.add_history_atomic(
                uow.conn, ticket_id, "complete",
                f"完工结算: 人工¥{labor_total:.2f} + 材料¥{material_total:.2f} + 交通¥{travel_fee:.2f}"
                f" = ¥{total:.2f}" +
                (f"（折扣-¥{discount_amount:.2f}）" if discount_amount > 0 else ""),
                data.get("operator", ""))

            # 6.5 自动记录支出（在事务内，确保数据一致性）
            try:
                finance_svc = self._finance_service
            except Exception:
                finance_svc = None

            if finance_svc:
                try:
                    existing_expenses = finance_svc.list_expenses(
                        filters={"related_ticket_id": ticket_id}) if hasattr(finance_svc, 'list_expenses') else []
                except Exception:
                    existing_expenses = []
                existing_categories = {e.get("category", "") for e in existing_expenses}

                if material_cost > 0 and "物料成本" not in existing_categories:
                    try:
                        finance_svc.add_expense(
                            category="物料成本",
                            vendor=ticket.get("client", ""),
                            description=f"工单 #{ticket.get('ticket_no', '')} 物料成本",
                            amount=material_cost,
                            payment_type="material",
                            related_ticket_id=ticket_id,
                        )
                    except Exception as e:
                        logger.warning(f"自动记录物料成本支出失败: {e}")

                if travel_fee > 0 and "交通费" not in existing_categories:
                    try:
                        finance_svc.add_expense(
                            category="交通费",
                            vendor=ticket.get("client", ""),
                            description=f"工单 #{ticket.get('ticket_no', '')} 交通费",
                            amount=travel_fee,
                            payment_type="travel",
                            related_ticket_id=ticket_id,
                        )
                    except Exception as e:
                        logger.warning(f"自动记录交通费支出失败: {e}")

        # 7. 事务外的操作（通知，不影响主流程）

        return self.get_ticket(ticket_id)

    # ===== 确认收款 =====

    def process_payment(self, ticket_id: int, method: str = "微信",
                        note: str = "") -> Dict[str, Any]:
        """
        处理工单收款（API 层统一入口）。
        包含金额计算、重复检测、状态更新等完整业务逻辑。
        """
        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("工单不存在")

        total = self.get_ticket_due_amount(ticket)
        if total <= 0:
            raise ValueError("工单金额为 ¥0.00，请先通过完工结算后再确认收款")

        finance_svc = self._finance_service
        ticket_no = ticket.get("ticket_no", "")

        if finance_svc and finance_svc.has_income_record("ticket", ticket_id):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            ticket_status = ticket.get("status", "")
            if ticket_status not in ("closed", "archived"):
                self._repo.update(ticket_id, {"billing_status": "paid", "closed_at": now})
            return {
                "message": "工单已标记为已结算（重复收款）",
                "summary": f"工单 {ticket_no} 已标记为已结算（重复收款）",
                "duplicate": True,
            }

        result = self.confirm_payment(ticket_id, total, method, note)
        return {
            "message": f"已确认收款 ¥{total:.2f}（{method}）",
            "summary": f"工单 {ticket_no} 已收款 ¥{total:.2f}（{method}）",
            "total": total,
            "ticket": result,
        }

    def batch_confirm_payment(self, ticket_ids: list,
                              method: str = "微信") -> Dict[str, Any]:
        """批量确认收款"""
        succeeded = []
        failed = []

        for tid in ticket_ids:
            try:
                ticket = self._repo.find_by_id(tid)
                if not ticket:
                    failed.append({"id": tid, "error": "工单不存在"})
                    continue

                total = self.get_ticket_due_amount(ticket)
                ticket_no = ticket.get("ticket_no", "")

                if total <= 0:
                    failed.append({"id": tid, "ticket_no": ticket_no, "error": "工单金额为0"})
                    continue

                finance_svc = self._finance_service
                if finance_svc and finance_svc.has_income_record("ticket", tid):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    self._repo.update(tid, {"billing_status": "paid", "closed_at": now})
                    succeeded.append({"id": tid, "ticket_no": ticket_no, "status": "duplicate"})
                    continue

                self.confirm_payment(tid, total, method, note="批量收款")
                succeeded.append({"id": tid, "ticket_no": ticket_no, "amount": total})
            except Exception as e:
                failed.append({"id": tid, "error": str(e)})

        total_amount = sum(s.get("amount", 0) for s in succeeded if "amount" in s)
        return {
            "succeeded": succeeded,
            "failed": failed,
            "total_amount": total_amount,
            "summary": f"批量收款完成：成功 {len(succeeded)} 单，失败 {len(failed)} 单，合计 ¥{total_amount:.2f}",
        }

    def confirm_payment(self, ticket_id: int, amount: float,
                        method: str = "微信", note: str = "",
                        idempotency_key: str = None) -> Dict[str, Any]:
        """
        确认收款（统一入口）。
        
        仅此方法为收款操作的唯一实现，废弃 FinanceService.confirm_payment 
        和 routes/api/finance.py FinancePay 中的独立事务逻辑。
        
        Args:
            ticket_id: 工单ID
            amount: 收款金额
            method: 收款方式
            note: 备注
            idempotency_key: 幂等键，用于防止重复收款
        """
        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")

        if amount <= 0:
            raise TicketValidationError("收款金额必须大于 0")

        if idempotency_key:
            already_processed = self._repo.get_idempotent_record(idempotency_key)
            if already_processed:
                logger.info(f"幂等键 {idempotency_key} 已处理，跳过重复请求")
                return self.get_ticket(ticket_id)

        total_due = float(ticket.get("total_with_tax") or ticket.get("total") or 0)
        if total_due <= 0:
            total_due = (float(ticket.get("total_labor") or 0)
                         + float(ticket.get("total_material") or 0)
                         + float(ticket.get("total_external") or 0))
        
        finance_svc = self._finance_service
        already_paid = finance_svc.get_ticket_paid_total(ticket_id) if finance_svc else 0
        remaining = total_due - already_paid
        
        if amount > remaining + 0.01:
            raise TicketValidationError(
                f"收款额 ¥{amount:.2f} 超出剩余应收 ¥{max(remaining, 0):.2f}")

        finance_svc.record_income(
            source_type="ticket",
            source_id=ticket_id,
            client=ticket.get("client", ""),
            amount=amount,
            method=method,
            description=note or f"工单收款 #{ticket.get('ticket_no', '')}",
        )

        from infrastructure.persistence.database import UnitOfWork
        with UnitOfWork() as uow:
            self._repo.update(ticket_id, {
                "billing_status": "paid",
                "status": "completed",
                "closed_at": datetime.now().isoformat(),
            }, conn=uow.conn)
            self._repo.add_history_atomic(uow.conn, ticket_id, "payment",
                                   f"确认收款: ¥{amount:.2f} ({method})", "system")

        if idempotency_key:
            self._repo.save_idempotent_record(idempotency_key, {"ticket_id": ticket_id, "amount": amount})

        # 发布事件
        if self._event_bus:
            self._event_bus.dispatch(TicketPaymentConfirmed(
                ticket_id=ticket_id,
                amount=amount,
                method=method,
            ))

        return self.get_ticket(ticket_id)

    # ===== 照片管理 =====

    def get_ticket_photos(self, ticket_id: int) -> list:
        return self._repo.find_photos_by_ticket(ticket_id) or []

    def get_photo(self, photo_id: int, ticket_id: int):
        return self._repo.find_photo_by_id(photo_id, ticket_id)

    def save_photo(self, ticket_id: int, filename: str, filepath: str):
        self._repo.save_photo(ticket_id, filename, filepath)

    def delete_photo(self, photo_id: int):
        self._repo.delete_photo(photo_id)

    def delete_photo_by_path(self, filepath: str, ticket_id: int):
        self._repo.delete_photo_by_path(filepath, ticket_id)

    # ===== 设备关联 =====

    def link_equipment(self, ticket_id: int, equip_id: int) -> dict:
        equip_svc = self._equipment_service
        equip = equip_svc.get_equipment(equip_id) if equip_svc else None
        if not equip:
            raise TicketValidationError(f"设备 #{equip_id} 不存在")
        self._repo.link_equipment(ticket_id, equip_id, equipment_name=equip.get("name", ""))
        return equip

    def unlink_equipment(self, ticket_id: int, equip_id: int):
        self._repo.unlink_equipment(ticket_id, equip_id)

    def get_linked_equipment_names(self, ticket_id: int) -> list:
        return self._repo.get_linked_equipment_names(ticket_id)

    # ===== 搜索 =====

    def search_tickets(self, keyword: str, limit: int = 8) -> list:
        return self._repo.search_tickets(keyword, limit) or []

    # ===== 逾期工单 =====

    def get_overdue_tickets(self, limit: int = 10) -> list:
        return self._repo.get_overdue_tickets(limit)

    # ===== 技术人员查询 =====

    def get_technicians(self, ticket_id: int) -> list:
        return self._repo.get_service_items(ticket_id) or []

    def get_technician_names(self, ticket_id: int) -> list:
        return self._repo.get_technician_names(ticket_id)

    # ===== 物料管理 =====

    def get_ticket_materials(self, ticket_id: int) -> list:
        return self._repo.find_materials_by_ticket(ticket_id) or []

    def get_material_count(self, ticket_id: int) -> int:
        return self._repo.get_material_count(ticket_id)

    def update_material(self, mat_id: int, ticket_id: int, quantity: float = None, unit_price: float = None) -> dict:
        mat = self._repo.find_material(mat_id, ticket_id)
        if not mat:
            raise TicketValidationError(f"物料 #{mat_id} 不存在")
        if quantity is not None:
            quantity = float(quantity)
        else:
            quantity = float(mat.get("quantity", 0))
        if unit_price is not None:
            unit_price = float(unit_price)
        else:
            unit_price = float(mat.get("unit_price", 0))
        total = unit_price * quantity
        self._repo.update_material(mat_id, ticket_id, quantity, unit_price, total)
        return {"quantity": quantity, "unit_price": unit_price, "total": total}

    def update_material_quantity(self, mat_id: int, ticket_id: int, quantity: float) -> dict:
        mat = self._repo.find_material(mat_id, ticket_id)
        if not mat:
            raise TicketValidationError(f"物料 #{mat_id} 不存在")
        old_qty = float(mat.get("quantity", 0))
        diff = quantity - old_qty
        unit_price = float(mat.get("unit_price", 0))
        total = unit_price * quantity

        item_ids_str = mat.get("inventory_item_ids", "") or ""
        if diff < 0 and item_ids_str:
            ids = [int(x) for x in item_ids_str.split(",") if x.strip().isdigit()]
            to_release = abs(int(diff))
            released = 0
            kept_ids = []
            for item_id in ids:
                if released < to_release:
                    self._repo.release_inventory(item_id)
                    released += 1
                else:
                    kept_ids.append(str(item_id))
            self._repo.update_material_inventory_ids(mat_id, ",".join(kept_ids))

        self._repo.update_material_quantity_and_total(mat_id, quantity, total)
        return {"quantity": quantity, "total": total}

    def delete_material(self, mat_id: int, ticket_id: int):
        mat = self._repo.find_material(mat_id, ticket_id)
        if mat and mat.get("inventory_item_ids"):
            ids = [int(x) for x in mat["inventory_item_ids"].split(",") if x.strip().isdigit()]
            for item_id in ids:
                self._repo.release_inventory(item_id)
        self._repo.delete_material(mat_id, ticket_id)

    # ===== 费用重算（唯一计算入口） =====

    def recalc_ticket_total(self, ticket_id: int):
        from domain.amount_calculator import AmountCalculator
        ticket = self._repo.get_billing_fields(ticket_id)
        if not ticket:
            return
        items = self._repo.get_service_items(ticket_id)
        labor_total = sum(float(i.get("line_total", 0) or 0) for i in items)
        material = self._repo.sum_material_total(ticket_id)
        travel_dist = float(ticket.get("travel_distance", 0) or 0)
        travel_rate = float(ticket.get("travel_rate", 0) or 0)
        external = travel_dist * travel_rate
        discount_type = ticket.get("discount_type") or ""
        discount_value = float(ticket.get("discount_value", 0) or 0)
        total = AmountCalculator.calc_total(
            labor_total, material, external,
            discount_type, discount_value)
        discount_amount, _ = AmountCalculator.calc_discount(
            labor_total + material + external,
            discount_type, discount_value)
        tax_rate = float(ticket.get("tax_rate", 0) or 0)
        tax_amount, total_with_tax = AmountCalculator.calc_total_with_tax(total, tax_rate)
        self._repo.update(ticket_id, {
            "total_labor": labor_total,
            "total_material": material,
            "total_external": external,
            "total": total,
            "discount_amount": discount_amount,
            "tax_amount": tax_amount,
            "total_with_tax": total_with_tax,
        })
        tech_names = list(dict.fromkeys(
            i.get("technician_name", "") for i in items if i.get("technician_name")
        ))
        if tech_names:
            self._repo.update(ticket_id, {"assignee": ",".join(tech_names)})
        tax_info = f"，税¥{tax_amount:.2f}→含税¥{total_with_tax:.2f}" if tax_rate > 0 else ""
        self._repo.add_history(ticket_id, "update",
                               f"服务明细重算: 人工¥{labor_total:.2f} + 材料¥{material:.2f} + 交通¥{external:.2f} = ¥{total:.2f}{tax_info}")

    # ===== 服务明细行 =====

    def get_service_items(self, ticket_id: int) -> list:
        return self._repo.get_service_items(ticket_id)

    def add_service_item(self, ticket_id: int, data: dict) -> dict:
        tech_name = data.get("technician_name", "")
        service_fee_id = data.get("service_fee_id")
        hours = float(data.get("hours", 0))
        days = float(data.get("days", 0))
        package_fee = float(data.get("package_fee", 0))
        unit_price = float(data.get("unit_price", 0))
        cost_price = float(data.get("cost_price", 0))
        name = data.get("name", "")
        billing_type = data.get("billing_type", "hourly")
        if billing_type == "daily":
            line_total = round(days * unit_price, 2)
            line_cost = round(days * cost_price, 2)
        elif billing_type == "package":
            line_total = round(package_fee, 2)
            line_cost = round(cost_price, 2)
        else:
            line_total = round(hours * unit_price, 2)
            line_cost = round(hours * cost_price, 2)
        item_id = self._repo.add_service_item(ticket_id, tech_name, service_fee_id,
                                               hours, unit_price, cost_price,
                                               line_total, line_cost, name,
                                               days, package_fee)
        self._update_ticket_assignee(ticket_id)
        self.recalc_ticket_total(ticket_id)
        return {"id": item_id, "ticket_id": ticket_id,
                "technician_name": tech_name, "service_fee_id": service_fee_id,
                "hours": hours, "days": days, "package_fee": package_fee,
                "unit_price": unit_price, "cost_price": cost_price,
                "name": name, "line_total": line_total, "line_cost": line_cost,
                "billing_type": billing_type}

    def update_service_item(self, ticket_id: int, item_id: int, data: dict) -> dict:
        item = self._repo.find_service_item(item_id, ticket_id)
        if not item:
            raise TicketValidationError(f"服务明细 #{item_id} 不存在")
        update_data = {}
        for col in ["technician_name", "service_fee_id", "hours", "days", "package_fee",
                    "unit_price", "cost_price", "name"]:
            if col in data:
                update_data[col] = data[col]
        billing_type = data.get("billing_type", item.get("billing_type", "hourly"))
        hours = float(data.get("hours", item.get("hours", 0)))
        days = float(data.get("days", item.get("days", 0)))
        package_fee = float(data.get("package_fee", item.get("package_fee", 0)))
        unit_price = float(data.get("unit_price", item.get("unit_price", 0)))
        cost_price = float(data.get("cost_price", item.get("cost_price", 0)))
        if billing_type == "daily":
            update_data["line_total"] = round(days * unit_price, 2)
            update_data["line_cost"] = round(days * cost_price, 2)
        elif billing_type == "package":
            update_data["line_total"] = round(package_fee, 2)
            update_data["line_cost"] = round(cost_price, 2)
        else:
            update_data["line_total"] = round(hours * unit_price, 2)
            update_data["line_cost"] = round(hours * cost_price, 2)
        self._repo.update_service_item(item_id, update_data)
        self._update_ticket_assignee(ticket_id)
        self.recalc_ticket_total(ticket_id)
        return self._repo.find_service_item(item_id) or {}

    def delete_service_item(self, ticket_id: int, item_id: int):
        self._repo.delete_service_item(item_id)
        self._update_ticket_assignee(ticket_id)
        self.recalc_ticket_total(ticket_id)

    def batch_update_service_items(self, ticket_id: int, items: list) -> list:
        self._repo.delete_ticket_service_items(ticket_id)
        results = []
        for item in items:
            tech_name = item.get("technician_name", "")
            service_fee_id = item.get("service_fee_id")
            hours = float(item.get("hours", 0))
            days = float(item.get("days", 0))
            package_fee = float(item.get("package_fee", 0))
            unit_price = float(item.get("unit_price", 0))
            cost_price = float(item.get("cost_price", 0))
            name = item.get("name", "")
            billing_type = item.get("billing_type", "hourly")
            if billing_type == "daily":
                line_total = round(days * unit_price, 2)
                line_cost = round(days * cost_price, 2)
            elif billing_type == "package":
                line_total = round(package_fee, 2)
                line_cost = round(cost_price, 2)
            else:
                line_total = round(hours * unit_price, 2)
                line_cost = round(hours * cost_price, 2)
            self._repo.add_service_item(ticket_id, tech_name, service_fee_id,
                                         hours, unit_price, cost_price,
                                         line_total, line_cost, name,
                                         days, package_fee)
            results.append(item)
        self._update_ticket_assignee(ticket_id)
        self.recalc_ticket_total(ticket_id)
        return results

    def _update_ticket_assignee(self, ticket_id: int):
        self._repo.sync_assignee_from_service_items(ticket_id)

    # ===== 计时器 =====

    def get_timer(self, ticket_id: int):
        return self._repo.get_timer(ticket_id)

    def set_timer(self, ticket_id: int, started_at: str):
        self._repo.set_timer(ticket_id, started_at)

    def clear_timer(self, ticket_id: int):
        self._repo.clear_timer(ticket_id)

    # ===== 操作历史 =====

    def get_history(self, ticket_id: int, limit: int = 50) -> list:
        return self._repo.get_history(ticket_id, limit=limit) or []

    def get_ticket_delta(self, ticket_id: int) -> Dict[str, Any]:
        """获取工单变更 Delta 信息（含时间线+时长计算）"""
        import json as _json
        from datetime import datetime

        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("工单不存在")

        changes = self._repo.get_history(ticket_id, limit=1000) or []

        timeline = []
        for h in changes:
            entry = {
                "timestamp": h.get("timestamp", ""),
                "action": h.get("action", ""),
                "by": h.get("by", ""),
            }
            try:
                changes_data = _json.loads(h.get("changes", "{}"))
                if isinstance(changes_data, dict):
                    entry["changes"] = changes_data
            except (_json.JSONDecodeError, TypeError):
                pass
            timeline.append(entry)

        created_at = ticket.get("created_at", "")
        closed_at = ticket.get("closed_at", "")
        duration_info = {}
        if created_at and closed_at:
            try:
                created = datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at
                closed = datetime.fromisoformat(closed_at) if isinstance(closed_at, str) else closed_at
                delta = closed - created
                duration_info = {
                    "created_at": str(created),
                    "closed_at": str(closed),
                    "duration_days": delta.days,
                    "duration_hours": round(delta.total_seconds() / 3600, 1),
                    "duration_text": f"{delta.days}天{delta.seconds // 3600}小时",
                }
            except (ValueError, TypeError):
                pass

        return {
            "ticket_id": ticket_id,
            "ticket_no": ticket["ticket_no"],
            "current_status": ticket.get("status", ""),
            "current_status_name": self.STATUS_NAMES.get(ticket.get("status"), ""),
            "billing_status": ticket.get("billing_status", ""),
            "timeline": timeline,
            "change_count": len(changes),
            "duration": duration_info if duration_info else None,
        }

    def count_history(self, ticket_id: int) -> int:
        return self._repo.count_history(ticket_id) if hasattr(self._repo, 'count_history') else 0

    # ===== 搜索 =====

    def search_by_filter(self, status: str = None, client: str = None,
                         keyword: str = None, date_from: str = None,
                         date_to: str = None) -> list:
        return self._repo.search_by_filter(status, client, keyword, date_from, date_to)

    def count_tickets(self, status: str = None) -> int:
        if status:
            rows = self._repo.search_by_filter(status=status)
            return len(rows) if rows else 0
        return len(self._repo.list_all()) if hasattr(self._repo, 'list_all') else 0

    # ===== 服务明细（低层代理） =====

    def batch_execute_action(self, ids: list, action: str,
                              target_status: str = None) -> Dict[str, Any]:
        """批量执行工单操作（complete/delete/status）"""
        results = {"success": 0, "failed": 0, "confirmed": True}
        for raw_id in ids:
            try:
                tid = int(raw_id)
            except (ValueError, TypeError):
                results["failed"] += 1
                continue
            try:
                if action == "complete":
                    self.transition_status(tid, "pending-payment", note="批量完工")
                    results["success"] += 1
                elif action == "delete":
                    self.delete_ticket(tid)
                    results["success"] += 1
                elif action == "status":
                    if target_status and target_status in self.STATUS_NAMES:
                        self.transition_status(tid, target_status)
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                else:
                    return {"error": f"不支持的操作类型: {action}"}
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Batch action failed for ticket {tid}: {e}")
                results["failed"] += 1

        results["message"] = f"完成 {results['success']} 条，失败 {results['failed']} 条"
        return results

    def batch_by_filter(self, action: str, filters: dict,
                         target_status: str = None) -> Dict[str, Any]:
        """按筛选条件批量操作工单"""
        if not action:
            raise ValueError("请提供操作类型")

        matched = self.search_by_filter(
            status=filters.get("status", ""),
            client=filters.get("client", ""),
            keyword=filters.get("q", ""),
            date_from=filters.get("date_from", ""),
            date_to=filters.get("date_to", ""),
        ) if hasattr(self, 'search_by_filter') else []

        if not matched:
            return {"error": "没有匹配筛选条件的工单", "matched_count": 0}

        ids = [m["id"] for m in matched]
        results = self.batch_execute_action(ids, action, target_status)

        filter_desc = "、".join(f"{k}={v}" for k, v in filters.items() if v)
        results.update({
            "filter": filters,
            "action": action,
            "total": len(ids),
            "affected_tickets": [
                {"id": m["id"], "ticket_no": m["ticket_no"], "client": m["client"]}
                for m in matched
            ],
            "summary": f"对 {len(matched)} 单符合条件的工单（{filter_desc}）执行「{action}」操作",
        })
        return results

    def set_discount(self, ticket_id: int, discount_type: str,
                     discount_value: float) -> Dict[str, Any]:
        """设置工单优惠折扣"""
        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("工单不存在")
        if not discount_type or discount_value <= 0:
            raise ValueError("请提供有效的优惠信息")
        self._repo.update(ticket_id, {"discount_type": discount_type,
                                       "discount_value": discount_value})
        self.recalc_ticket_total(ticket_id)
        ticket = self._repo.find_by_id(ticket_id)
        total = float(ticket.get("total", 0) or 0)
        return {"message": "优惠已设置", "total": total}

    def batch_save_service_items(self, ticket_id: int, items: list) -> Dict[str, Any]:
        """批量保存服务明细行（先删后插，全量替换）"""
        self._repo.delete_ticket_service_items(ticket_id)
        for item in items:
            name = (item.get("name") or "").strip()
            technician = (item.get("technician_name") or "").strip()
            fee_id = item.get("service_fee_id")
            hours = float(item.get("hours", 0))
            days = float(item.get("days", 0))
            package_fee = float(item.get("package_fee", 0))
            unit_price = float(item.get("unit_price", 0))
            cost_price = float(item.get("cost_price", 0))
            billing_type = item.get("billing_type", "hourly")
            if billing_type == "daily":
                line_total = float(item.get("line_total", 0)) or (unit_price * days)
                line_cost = float(item.get("line_cost", 0)) or (cost_price * days)
            elif billing_type == "package":
                line_total = float(item.get("line_total", 0)) or package_fee
                line_cost = float(item.get("line_cost", 0)) or cost_price
            else:
                line_total = float(item.get("line_total", 0)) or (unit_price * hours)
                line_cost = float(item.get("line_cost", 0)) or (cost_price * hours)
            self._repo.add_service_item(ticket_id, technician, fee_id, hours,
                                         unit_price, cost_price, line_total,
                                         line_cost, name=name, days=days,
                                         package_fee=package_fee)
        self.recalc_ticket_total(ticket_id)
        return {"message": f"已保存 {len(items)} 条服务明细"}

    def delete_ticket_service_items(self, ticket_id: int):
        self._repo.delete_ticket_service_items(ticket_id)

    def add_service_item_raw(self, ticket_id: int, technician: str, fee_id,
                              hours, unit_price, cost_price, line_total, line_cost,
                              name: str = "", days: float = 0, package_fee: float = 0):
        return self._repo.add_service_item(ticket_id, technician, fee_id, hours,
                                            unit_price, cost_price, line_total,
                                            line_cost, name=name, days=days,
                                            package_fee=package_fee)

    def update_service_item_raw(self, item_id: int, data: dict):
        self._repo.update_service_item(item_id, data)

    def delete_service_item_raw(self, item_id: int):
        self._repo.delete_service_item(item_id)

    # ===== 工单模板 =====

    def list_templates(self) -> list:
        return self._repo.list_templates()

    def get_template(self, tid: int):
        return self._repo.get_template(tid)

    def create_template(self, **kwargs):
        self._repo.create_template(
            name=kwargs.get("name", ""),
            content=kwargs.get("content", ""),
            client=kwargs.get("client", ""),
            category=kwargs.get("category", ""),
            sort_order=int(kwargs.get("sort_order", 99)))

    def update_template(self, tid: int, data: dict):
        self._repo.update_template(tid, data)

    def delete_template(self, tid: int):
        self._repo.delete_template(tid)

    # ===== 自动化规则 =====

    def list_rules(self) -> list:
        return self._repo.list_rules()

    def get_rule(self, rid: int):
        return self._repo.get_rule(rid)

    def create_rule(self, **kwargs):
        self._repo.create_rule(
            name=kwargs.get("name", ""),
            event=kwargs.get("event", ""),
            conditions=kwargs.get("conditions", "{}"),
            actions=kwargs.get("actions", "{}"),
            enabled=int(kwargs.get("enabled", 1)),
            priority=int(kwargs.get("priority", 99)))

    def update_rule(self, rid: int, data: dict):
        self._repo.update_rule(rid, data)

    def delete_rule(self, rid: int):
        self._repo.delete_rule(rid)

    def toggle_rule(self, rid: int):
        rule = self._repo.get_rule(rid)
        if not rule:
            return None
        new_val = 0 if rule.get("enabled") else 1
        self._repo.update_rule(rid, {"enabled": new_val})
        return new_val

    def seed_default_rules(self) -> int:
        defaults = [
            ("工单超时提醒", "ticket_overdue", "{}", '{"notify":"wecom"}', 1, 10),
            ("库存预警通知", "stock_alert", "{}", '{"notify":"wecom"}', 1, 20),
            ("维保到期提醒", "maintenance_due", "{}", '{"notify":"wecom"}', 1, 30),
        ]
        count = 0
        for name, event, cond, actions, enabled, priority in defaults:
            existing = self._repo.find_rule_by_name(name)
            if not existing:
                self._repo.create_rule(name=name, event=event, conditions=cond,
                                       actions=actions, enabled=enabled, priority=priority)
                count += 1
        return count

    def get_enabled_rules_by_event(self, event: str) -> list:
        return self._repo.get_enabled_rules_by_event(event)

    def execute_rules_for_event(self, event_name: str, context: dict = None):
        """
        执行指定事件的所有已启用自动化规则

        Args:
            event_name: 事件名称 (ticket_overdue, stock_alert, maintenance_due, etc.)
            context: 事件上下文数据 (ticket_id, client, etc.)

        Returns:
            list: 执行结果列表
        """
        import json as _json
        rules = self.get_enabled_rules_by_event(event_name)
        results = []
        ctx = context or {}

        for rule in rules:
            try:
                actions_raw = rule.get("actions", "{}")
                if isinstance(actions_raw, str):
                    actions = _json.loads(actions_raw)
                else:
                    actions = actions_raw or {}

                conditions_raw = rule.get("conditions", "{}")
                if isinstance(conditions_raw, str):
                    conditions = _json.loads(conditions_raw)
                else:
                    conditions = conditions_raw or {}

                if not self._check_conditions(conditions, ctx):
                    results.append({"rule_id": rule["id"], "name": rule["name"], "status": "skipped", "reason": "条件不满足"})
                    continue

                action_results = self._execute_actions(actions, ctx)
                results.append({"rule_id": rule["id"], "name": rule["name"], "status": "executed", "actions": action_results})
            except Exception as e:
                results.append({"rule_id": rule.get("id"), "name": rule.get("name"), "status": "error", "error": str(e)})

        return results

    def _check_conditions(self, conditions: dict, context: dict) -> bool:
        if not conditions or conditions == "{}":
            return True
        for key, expected in conditions.items():
            actual = context.get(key)
            if actual is None:
                continue
            if isinstance(expected, (list, tuple)):
                if actual not in expected:
                    return False
            elif isinstance(expected, str) and expected.startswith((">", "<", ">=", "<=", "!=")):
                try:
                    val = float(actual)
                    threshold = float(expected[1:] if expected[:2] not in (">=", "<=") else expected[2:])
                    op = expected[:2] if expected[:2] in (">=", "<=") else expected[0]
                    if op == ">" and not (val > threshold):
                        return False
                    elif op == "<" and not (val < threshold):
                        return False
                    elif op == ">=" and not (val >= threshold):
                        return False
                    elif op == "<=" and not (val <= threshold):
                        return False
                    elif op == "!=" and not (val != threshold):
                        return False
                except (ValueError, TypeError):
                    return False
            elif str(actual) != str(expected):
                return False
        return True

    def _execute_actions(self, actions: dict, context: dict) -> list:
        results = []
        notify = actions.get("notify", "")
        if notify:
            try:
                from infrastructure.di.container import Container
                if "wecom" in notify:
                    wecom = Container.resolve("wecom_bot")
                    if wecom:
                        title = context.get("title", "自动化通知")
                        content = context.get("content", context.get("message", ""))
                        wecom.send_message(content, title=title)
                        results.append({"action": "wecom_notify", "status": "sent"})
                if "pushplus" in notify:
                    pp = Container.resolve("pushplus_bot")
                    if pp:
                        title = context.get("title", "自动化通知")
                        content = context.get("content", context.get("message", ""))
                        pp.send_message(content, title=title)
                        results.append({"action": "pushplus_notify", "status": "sent"})
            except Exception as e:
                results.append({"action": "notify", "status": "error", "error": str(e)})

        auto_status = actions.get("auto_status", "")
        if auto_status:
            ticket_id = context.get("ticket_id")
            if ticket_id:
                try:
                    self._repo.update(ticket_id, {"status": auto_status})
                    results.append({"action": "auto_status", "status": auto_status, "ticket_id": ticket_id})
                except Exception as e:
                    results.append({"action": "auto_status", "status": "error", "error": str(e)})

        auto_assign = actions.get("auto_assign", "")
        if auto_assign:
            ticket_id = context.get("ticket_id")
            if ticket_id:
                try:
                    self._repo.update(ticket_id, {"assignee": auto_assign})
                    results.append({"action": "auto_assign", "assignee": auto_assign, "ticket_id": ticket_id})
                except Exception as e:
                    results.append({"action": "auto_assign", "status": "error", "error": str(e)})

        create_todo = actions.get("create_todo", False)
        if create_todo:
            try:
                from infrastructure.di.container import Container
                todo_svc = Container.resolve("todo_service")
                if todo_svc:
                    title = context.get("todo_title", context.get("title", "自动待办"))
                    todo_svc.create_from_ticket(
                        ticket_id=context.get("ticket_id", 0),
                        todo_type="auto_rule",
                        title=title,
                    )
                    results.append({"action": "create_todo", "status": "created"})
            except Exception as e:
                results.append({"action": "create_todo", "status": "error", "error": str(e)})

        return results

    def list_tickets_paginated(self, page: int = 1, per_page: int = 50,
                                status: str = None, client: str = None,
                                keyword: str = None, date_from: str = None,
                                date_to: str = None, sort_field: str = None,
                                sort_dir: str = "desc") -> dict:
        return self._repo.paginated_list(
            page=page, per_page=per_page, status=status, client=client,
            keyword=keyword, date_from=date_from, date_to=date_to,
            sort_field=sort_field, sort_dir=sort_dir)

    # ===== 技术人员管理 =====

    def stop_timer(self, ticket_id: int, start_time) -> Dict[str, Any]:
        """停止工时计时，自动累加实际工时并分摊到技师"""
        from datetime import datetime, timedelta
        elapsed = round((datetime.now() - start_time).total_seconds() / 3600, 2)
        if elapsed < 0.02:
            elapsed = 0.02

        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("工单不存在")

        current_hours = float(ticket.get("time_spent", 0) or 0)
        new_hours = current_hours + elapsed
        self._repo.update(ticket_id, {"time_spent": round(new_hours, 2)})

        techs = self._repo.get_technicians(ticket_id)
        if techs:
            first = techs[0]["technician_name"]
            current_tech_hours = float(techs[0].get("hours", 0) or 0)
            self._repo.add_technician(ticket_id, first,
                                       float(techs[0].get("cost_rate", 0) or 0),
                                       round(current_tech_hours + elapsed, 2))
            if len(techs) > 1:
                total_new = current_hours + elapsed
                per_person = round(total_new / len(techs), 2)
                for t in techs:
                    self._repo.add_technician(ticket_id, t["technician_name"],
                                               float(t.get("cost_rate", 0) or 0),
                                               per_person)

        self.recalc_ticket_total(ticket_id)

        return {
            "message": f"计时结束，本次 {elapsed:.2f} 小时，累计 {new_hours:.2f} 小时",
            "elapsed_hours": elapsed,
            "total_hours": new_hours,
        }

    def add_technician(self, ticket_id: int, name: str, cost_rate: float = None, hours: float = 0) -> dict:
        if cost_rate is None:
            tech_svc = self._technician_repo or self._technician_service
            tech = tech_svc.get_technician_by_name(name) if tech_svc else None
            if tech and tech.get("cost_rate"):
                cost_rate = float(tech["cost_rate"])
            else:
                cost_rate = self._default_cost_rate()
        self._repo.add_technician(ticket_id, name, cost_rate, hours)
        self._update_ticket_assignee(ticket_id)
        self.auto_progress_status(ticket_id, trigger_field="assign_technician")
        self.recalc_ticket_total(ticket_id)
        return {"name": name, "cost_rate": cost_rate, "hours": hours}

    def remove_technician(self, ticket_id: int, name: str) -> bool:
        self._repo.remove_technician(ticket_id, name)
        self._update_ticket_assignee(ticket_id)
        self.recalc_ticket_total(ticket_id)
        return True

    def _default_cost_rate(self) -> float:
        try:
            from config.manager import BillingConfig
            return float(BillingConfig().default_cost_rate)
        except Exception:
            return 30.0

    def _default_unit_price(self) -> float:
        try:
            from config.manager import BillingConfig
            return float(BillingConfig().default_fee_rate)
        except Exception:
            return 60.0

    # ===== 自动状态推进 =====

    def auto_progress_status(self, ticket_id: int, trigger_field: str = ""):
        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            return None
        current = ticket.get("status", "")
        target = None

        if current == "open":
            tech_count = self._repo.count_service_items_with_hours(ticket_id)
            if tech_count > 0:
                target = "in-progress"
        elif current == "in-progress":
            if trigger_field in ("add_material", "material_added"):
                target = "pending-parts"
        elif current == "pending-parts":
            if trigger_field == "parts_arrived":
                target = "in-progress"

        if target and target in self.STATUS_FLOW.get(current, []):
            try:
                result = self.transition_status(ticket_id, target, note=f"自动流转(触发:{trigger_field})")
                logger.info(f"工单 #{ticket_id} 自动流转: {current} → {target} (触发:{trigger_field})")
                return result
            except Exception:
                pass
        return None

    def _recalculate_total(self, ticket_id: int):
        self.recalc_ticket_total(ticket_id)

    # ===== 自然语言解析 =====

    def parse_natural_language(self, text: str) -> dict:
        result = {"service_type": "维修", "priority": "M", "estimated_hours": 0}

        for prefix in ["客户是", "客户", "给", "为"]:
            if prefix in text:
                idx = text.index(prefix) + len(prefix)
                end = len(text)
                for sep in ["的", "建", "创", "修", "做", "安", "换", "，", "。", " "]:
                    if sep in text[idx:]:
                        end = idx + text[idx:].index(sep)
                        break
                client = text[idx:end].strip()
                if client:
                    result["client"] = client
                    break

        for prefix in ["修", "安装", "保养", "换", "做", "处理"]:
            if prefix in text:
                idx = text.index(prefix)
                end = len(text)
                for sep in ["，", "。", "！", "？", " ", "给", "为"]:
                    rest = text[idx + len(prefix):]
                    if sep in rest:
                        end = idx + len(prefix) + rest.index(sep)
                        break
                content = text[idx:end].strip()
                if len(content) > 1:
                    result["content"] = content
                    break

        if "content" not in result:
            result["content"] = text

        svc_map = {
            "维修": ["修", "坏", "故障", "换"], "安装": ["装", "安", "部署"],
            "保养": ["保", "养", "清洁"], "培训": ["培", "训", "教学"],
        }
        for svc_type, keywords in svc_map.items():
            if any(kw in text for kw in keywords):
                result["service_type"] = svc_type
                break

        high_kw = ["紧急", "加急", "重要", "紧急", "快", "急"]
        low_kw = ["不急", "普通", "一般", "低"]
        if any(kw in text for kw in high_kw):
            result["priority"] = "H"
        elif any(kw in text for kw in low_kw):
            result["priority"] = "L"

        hours_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:小?时|h)', text)
        if hours_match:
            result["estimated_hours"] = float(hours_match.group(1))

        amount_match = re.search(r'(?:¥|￥|价格|报价)\s*(\d+(?:\.\d{1,2})?)', text)
        if amount_match:
            result["amount"] = float(amount_match.group(1))

        date_match = re.search(r'(?:明天|今天|后天|(\d{1,2})月(\d{1,2})日?)\s*(?:上午|下午|)?\s*(\d{1,2})[：:点](\d{1,2})?', text)
        if date_match:
            now = datetime.now()
            if "明天" in text:
                day = now.day + 1
            elif "后天" in text:
                day = now.day + 2
            else:
                day = now.day
            max_day = monthrange(now.year, now.month)[1]
            if day > max_day:
                day = day - max_day
            result["appointment_at"] = f"{now.year}-{now.month:02d}-{day:02d}"

        if "client" not in result:
            return {"error": "无法识别客户名称，请明确指定客户"}

        return result

    # ===== 事件处理器（跨聚合根写操作入口） =====

    def sync_ticket_cost(self, ticket_id: int):
        ticket = self._repo.find_by_id(ticket_id)
        if not ticket:
            return
        labor = self._repo.get_ticket_labor_cost(ticket_id) if hasattr(self._repo, 'get_ticket_labor_cost') else 0
        external = self._repo.get_ticket_external_cost(ticket_id) if hasattr(self._repo, 'get_ticket_external_cost') else 0
        self._repo.update(ticket_id, {
            "total_labor": labor,
            "total_external": external,
        })

    def update_ticket_billing(self, ticket_id: int, **kwargs):
        data = {k: v for k, v in kwargs.items() if v is not None}
        if data:
            self._repo.update(ticket_id, data)

    def update_equipment_maintenance(self, equipment_id: int, next_maintenance: str):
        equip_svc = self._equipment_service
        if equip_svc and hasattr(equip_svc, 'update_equipment'):
            try:
                equip_svc.update_equipment(equipment_id, next_maintenance=next_maintenance)
            except Exception as e:
                logger.warning(f"更新设备维护日期失败 (equip#{equipment_id}): {e}")

    def update_inspection_plan(self, plan_id: int, next_execution: str):
        finance_svc = self._finance_service
        if finance_svc:
            try:
                finance_svc.update_inspection_plan_next_execution(plan_id, next_execution)
            except Exception as e:
                logger.warning(f"更新巡检计划下次执行日期失败 (plan#{plan_id}): {e}")

    def _sync_reminder_on_appointment_change(self, ticket_id: int, new_appointment: str, client: str, title: str):
        try:
            existing = self._repo.find_active_reminder(ticket_id)

            if new_appointment:
                if existing:
                    try:
                        dt = datetime.fromisoformat(new_appointment)
                        new_reminder_time = dt.strftime("%H:%M")
                    except Exception:
                        new_reminder_time = datetime.now().strftime("%H:%M")
                    self._repo.update_reminder(
                        existing["id"], new_reminder_time,
                        f"{client} - {title}" if title else client)
                else:
                    if self._reminder_service:
                        self._reminder_service.create_reminder(
                            ticket_id=ticket_id,
                            appointment_at=new_appointment,
                            client_name=client,
                            service_content=title,
                        )
            else:
                if existing:
                    self._repo.deactivate_reminder(existing["id"])
        except Exception as e:
            logger.warning(f"同步预约提醒失败: {e}")

    # ===== DDD 重构：业务逻辑下沉方法 =====

    def enrich_ticket_detail(self, ticket_id: int) -> Dict[str, Any]:
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")
        result = dict(ticket)
        result["status_name"] = self.STATUS_NAMES.get(ticket.get("status"), ticket.get("status"))
        try:
            result["material_count"] = len(result.get("materials", []))
        except Exception:
            result["material_count"] = 0
        status_name = result.get("status_name", "")
        total_amt = result.get("total", 0) or 0
        summary = f"工单 {result.get('ticket_no','')} 详情：客户 {result.get('client','')}，状态 {status_name}，金额 ¥{float(total_amt):.2f}"
        if result.get("material_count", 0) > 0:
            summary += f"，物料 {result['material_count']} 项"
        result["summary"] = summary
        try:
            equip = result.get("equipment", [])
            result["linked_equipment"] = [{"id": e.get("equipment_id"), "name": e.get("name", "")} for e in equip if e.get("equipment_id")]
        except Exception:
            result["linked_equipment"] = []
        if "service_items" not in result:
            result["service_items"] = self.get_service_items(ticket_id)
        return result

    def add_watermark(self, image_path: str, ticket_id: int) -> str:
        from PIL import Image, ImageDraw, ImageFont

        ticket = self.get_ticket(ticket_id)
        equip_names = self.get_linked_equipment_names(ticket_id)
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        w, h = img.size

        max_w = 1200
        if w > max_w:
            ratio = max_w / w
            new_h = int(h * ratio)
            img = img.resize((max_w, new_h), Image.LANCZOS)
            w, h = img.size
            draw = ImageDraw.Draw(img)

        lines = [f"工单号: {ticket['ticket_no']}"]
        lines.append(f"客户: {ticket['client']}")
        if equip_names:
            lines.append(f"设备: {'、'.join(equip_names)}")
        lines.append(datetime.now().strftime('%Y-%m-%d %H:%M'))
        text = '\n'.join(lines)

        font_size = max(11, int(w * 0.018))
        font = None
        font_paths = [
            str(_PROJECT_ROOT / "static/fonts/SimHei.ttf"),
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ]
        for fp in font_paths:
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()

        max_text_width = w - 40
        wrapped_lines = []
        for line in text.split('\n'):
            current = ''
            for ch in line:
                test = current + ch
                tw = draw.textbbox((0, 0), test, font=font)[2]
                if tw <= max_text_width:
                    current = test
                else:
                    wrapped_lines.append(current)
                    current = ch
            if current:
                wrapped_lines.append(current)

        line_height = draw.textbbox((0, 0), '测', font=font)[3] + 4
        total_h = line_height * len(wrapped_lines)
        y = h - total_h - 15

        for line in wrapped_lines:
            draw.text((15, y), line, fill=(255, 255, 255), font=font,
                     stroke_width=1, stroke_fill=(0, 0, 0))
            y += line_height

        wm_path = image_path.replace("raw_", "wm_")
        img.save(wm_path, "JPEG", quality=92)
        os.remove(image_path)
        return wm_path

    def confirm_delete_preview(self, ticket_id: int) -> Dict[str, Any]:
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")
        materials = self.get_ticket_materials(ticket_id) or []
        techs = self.get_technicians(ticket_id) or []
        photos = self.get_ticket_photos(ticket_id) or []
        history_count = self.count_history(ticket_id)
        linked_equip = self.get_linked_equipment_names(ticket_id) or []

        confirm_id = f"del_ticket_{ticket_id}_{int(datetime.now().timestamp())}"
        self._pending_confirmations[confirm_id] = {
            "action": "delete_ticket",
            "ticket_id": ticket_id,
            "ticket_no": ticket["ticket_no"],
            "expires_at": datetime.now().timestamp() + 300,
        }

        return {
            "confirm_id": confirm_id,
            "preview": {
                "ticket_no": ticket["ticket_no"],
                "client": ticket["client"],
                "status": ticket["status"],
                "status_name": self.STATUS_NAMES.get(ticket.get("status"), ""),
            },
            "related_data": {
                "materials": len(materials),
                "technicians": len(techs),
                "photos": len(photos),
                "history_entries": history_count if isinstance(history_count, int) else (history_count[0]["c"] if history_count else 0),
                "linked_equipment": linked_equip,
            },
            "summary": f"即将删除工单 {ticket['ticket_no']}（{ticket['client']}），"
                       f"关联 {len(materials)} 项物料、{len(techs)} 位技术人员、{len(linked_equip)} 台设备",
            "confirmation_required": True,
            "confirm_url": f"/api/v1/tickets/{ticket_id}/confirm-delete",
            "expires_in_seconds": 300,
        }

    def confirm_delete_execute(self, ticket_id: int, confirm_id: str) -> Dict[str, Any]:
        if not confirm_id or confirm_id not in self._pending_confirmations:
            raise TicketValidationError("确认ID无效或已过期，请重新预览")
        confirmation = self._pending_confirmations.pop(confirm_id)
        if confirmation["ticket_id"] != ticket_id:
            raise TicketValidationError("确认ID与工单不匹配")
        if confirmation["expires_at"] < datetime.now().timestamp():
            raise TicketValidationError("确认已过期（5分钟），请重新预览")
        ticket_no = confirmation["ticket_no"]
        self.delete_ticket(ticket_id)
        self.cleanup_expired_confirmations()
        return {"message": f"工单 {ticket_no} 已删除", "deleted": True}

    def store_confirmation(self, confirm_id: str, data: dict):
        self._pending_confirmations[confirm_id] = data

    def pop_confirmation(self, confirm_id: str):
        return self._pending_confirmations.pop(confirm_id, None)

    def cleanup_expired_confirmations(self):
        now = datetime.now().timestamp()
        expired = [k for k, v in self._pending_confirmations.items()
                   if v.get("expires_at", 0) < now]
        for k in expired:
            self._pending_confirmations.pop(k, None)

    def calc_list_profits(self, tickets: list) -> list:
        if not tickets:
            return tickets
        ids = [t["id"] for t in tickets]
        finance_svc = self._finance_service
        if finance_svc and hasattr(finance_svc, 'get_batch_ticket_income'):
            try:
                profit_income = finance_svc.get_batch_ticket_income(ids)
                profit_expense = finance_svc.get_batch_ticket_expense(ids)
                for r in tickets:
                    tid = r["id"]
                    inc = profit_income.get(tid, 0)
                    exp = profit_expense.get(tid, 0)
                    r["profit_income"] = inc
                    r["profit_expense"] = exp
                    r["profit"] = inc - exp
            except Exception:
                pass
        return tickets

    def trace_material(self, ticket_id: int) -> Dict[str, Any]:
        mats = self.get_ticket_materials(ticket_id)
        trace = []
        inv_svc = self._inventory_service
        for mat in mats:
            entry = {
                "material_id": mat["id"],
                "name": mat["name"],
                "quantity": mat.get("quantity", 0),
                "selling_price": mat.get("unit_price", 0),
                "total": mat.get("total", 0),
            }
            ids_str = (mat.get("inventory_item_ids", "") or "").strip()
            if ids_str:
                item_ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
                items = inv_svc.get_items_by_ids(item_ids) if inv_svc else []
                entry["inventory_items"] = items
                po_ids = [i["purchase_order_id"] for i in items if i.get("purchase_order_id")]
                if po_ids:
                    orders = inv_svc.get_purchase_orders_by_ids(po_ids) if inv_svc else []
                    entry["purchase_orders"] = orders
                else:
                    entry["purchase_orders"] = []
            else:
                entry["inventory_items"] = []
                entry["purchase_orders"] = []
            trace.append(entry)
        return {"trace": trace}

    def calc_service_item_totals(self, data: dict) -> dict:
        hours = float(data.get("hours", 0))
        days = float(data.get("days", 0))
        package_fee = float(data.get("package_fee", 0))
        unit_price = float(data.get("unit_price", 0))
        cost_price = float(data.get("cost_price", 0))
        billing_type = data.get("billing_type", "hourly")
        if billing_type == "daily":
            data["line_total"] = round(days * unit_price, 2)
            data["line_cost"] = round(days * cost_price, 2)
        elif billing_type == "package":
            data["line_total"] = round(package_fee, 2)
            data["line_cost"] = round(cost_price, 2)
        else:
            data["line_total"] = round(hours * unit_price, 2)
            data["line_cost"] = round(hours * cost_price, 2)
        return data

    # ===== CSV 导出 =====

    def export_tickets_csv(self, filters=None):
        filters = filters or {}
        data = self.list_tickets(
            status=filters.get("status"), client=filters.get("client"),
            keyword=filters.get("q"), date_from=filters.get("date_from"),
            date_to=filters.get("date_to"), page=1, per_page=99999)
        tickets = data["tickets"] if isinstance(data, dict) else data
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["工单编号", "客户", "内容", "状态", "金额", "创建时间"])
        for t in tickets:
            writer.writerow([t.get("ticket_no", ""), t.get("client", ""),
                            (t.get("description") or t.get("content") or "")[:50],
                            self.STATUS_NAMES.get(t.get("status"), t.get("status")),
                            t.get("total", 0), t.get("created_at", "")])
        return output.getvalue()

    def export_finance_csv(self):
        finance_svc = self._ensure_svc("_finance_service", "finance_service")
        income = finance_svc.get_income_history(limit=99999)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "客户", "金额", "方式", "描述"])
        for r in income:
            writer.writerow([r.get("received_at", ""), r.get("client", ""),
                            r.get("amount", 0), r.get("payment_method", ""), r.get("description", "")])
        return output.getvalue()

    def export_profit_csv(self, filters=None):
        data = self.list_tickets(page=1, per_page=99999)
        tickets = data["tickets"] if isinstance(data, dict) else data
        ids = [t["id"] for t in tickets]
        finance_svc = self._ensure_svc("_finance_service", "finance_service")
        income_map = finance_svc.get_batch_ticket_income(ids)
        expense_map = finance_svc.get_batch_ticket_expense(ids)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["工单编号", "客户", "应收", "已收", "成本", "利润"])
        for t in tickets:
            tid = t["id"]
            inc = income_map.get(tid, 0)
            exp = expense_map.get(tid, 0)
            writer.writerow([t.get("ticket_no", ""), t.get("client", ""),
                            t.get("total", 0), inc, exp, inc - exp])
        return output.getvalue()

    def export_statement_csv(self, client_name):
        finance_svc = self._ensure_svc("_finance_service", "finance_service")
        result = finance_svc.get_client_statement(client_name)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "类型", "工单号", "金额", "备注"])
        for r in result.get("income_records", []):
            writer.writerow([r.get("date", ""), "收入", r.get("source_id", ""), r.get("amount", 0), ""])
        for r in result.get("expense_records", []):
            writer.writerow([r.get("date", ""), "支出", r.get("source_id", ""), r.get("amount", 0), ""])
        return output.getvalue()

    def export_supplier_statement_csv(self, supplier_id):
        finance_svc = self._ensure_svc("_finance_service", "finance_service")
        result = finance_svc.get_supplier_statement(supplier_id)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "采购单号", "金额", "状态"])
        for o in result.get("orders", []):
            writer.writerow([o.get("purchase_date", ""), o.get("po_no", ""),
                            o.get("total_cost", o.get("total_amount", 0)), o.get("payment_status", "")])
        return output.getvalue()

    def export_equipment_csv(self):
        equip_svc = self._ensure_svc("_equipment_service", "equipment_service")
        equipment = equip_svc.list_equipment(page=1, page_size=99999)
        items = equipment.get("items", equipment.get("equipment", equipment if isinstance(equipment, list) else []))
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["名称", "序列号", "型号", "客户", "状态", "位置"])
        for e in (items or []):
            writer.writerow([e.get("name", ""), e.get("serial_no", ""), e.get("model", ""),
                            e.get("client", ""), e.get("status", ""), e.get("location", "")])
        return output.getvalue()

    # ===== 自然语言命令 =====

    def execute_nl_command(self, text):
        nl_svc = getattr(self, '_nl_service', None)
        if nl_svc:
            return nl_svc.execute_nl_command(text)
        return {"error": "NL服务未初始化"}

    def export_tickets_csv(self, filters=None):
        export_svc = getattr(self, '_export_service', None)
        if export_svc:
            return export_svc.export_tickets_csv(filters)
        raise RuntimeError("ExportService not injected")

    def export_finance_csv(self):
        export_svc = getattr(self, '_export_service', None)
        if export_svc:
            return export_svc.export_finance_csv()
        raise RuntimeError("ExportService not injected")

    def export_profit_csv(self, filters=None):
        export_svc = getattr(self, '_export_service', None)
        if export_svc:
            return export_svc.export_profit_csv(filters)
        raise RuntimeError("ExportService not injected")

    def export_statement_csv(self, client_name):
        export_svc = getattr(self, '_export_service', None)
        if export_svc:
            return export_svc.export_statement_csv(client_name)
        raise RuntimeError("ExportService not injected")

    def export_supplier_statement_csv(self, supplier_id):
        export_svc = getattr(self, '_export_service', None)
        if export_svc:
            return export_svc.export_supplier_statement_csv(supplier_id)
        raise RuntimeError("ExportService not injected")

    def export_equipment_csv(self):
        export_svc = getattr(self, '_export_service', None)
        if export_svc:
            return export_svc.export_equipment_csv()
        raise RuntimeError("ExportService not injected")


