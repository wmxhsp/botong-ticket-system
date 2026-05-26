"""
博通 (Botong) — 领域事件系统
解耦跨模块调用：工单流转→待办/通知/财务
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any
from enum import Enum, auto

logger = logging.getLogger(__name__)


# ===== 事件定义 =====

class DomainEvent:
    """领域事件基类"""
    event_name: str = ""


@dataclass
class TicketCreated(DomainEvent):
    ticket_id: int
    ticket_no: str
    client: str = ""
    assignee: str = ""
    event_name: str = "ticket.created"


@dataclass
class TicketStatusChanged(DomainEvent):
    ticket_id: int
    old_status: str
    new_status: str
    ticket_no: str = ""
    client: str = ""
    event_name: str = "ticket.status_changed"


@dataclass
class TicketCompleted(DomainEvent):
    ticket_id: int
    ticket_no: str
    total: float = 0
    client: str = ""
    event_name: str = "ticket.completed"


@dataclass
class TicketPaymentConfirmed(DomainEvent):
    ticket_id: int
    amount: float
    method: str = ""
    event_name: str = "ticket.payment_confirmed"


@dataclass
class TicketDeleted(DomainEvent):
    ticket_id: int
    ticket_no: str = ""
    event_name: str = "ticket.deleted"


@dataclass
class ClientCreated(DomainEvent):
    client_id: int = 0
    name: str = ""
    event_name: str = "client.created"


@dataclass
class IncomeRecorded(DomainEvent):
    amount: float
    client: str = ""
    source_type: str = ""
    source_id: int = 0
    event_name: str = "finance.income_recorded"


@dataclass
class ExpenseRecorded(DomainEvent):
    amount: float
    category: str = ""
    description: str = ""
    event_name: str = "finance.expense_recorded"


@dataclass
class TodoDue(DomainEvent):
    todo_id: int
    title: str = ""
    event_name: str = "todo.due"


@dataclass
class TicketCostSyncRequired(DomainEvent):
    ticket_id: int
    event_name: str = "ticket.cost_sync_required"


@dataclass
class TicketSettled(DomainEvent):
    ticket_id: int
    billing_status: str = "paid"
    closed_at: str = ""
    event_name: str = "ticket.settled"


@dataclass
class TicketTaxUpdated(DomainEvent):
    ticket_id: int
    tax_rate: float = 0
    tax_amount: float = 0
    billing_status: str = "pending"
    event_name: str = "ticket.tax_updated"


@dataclass
class ClientCreditFrozen(DomainEvent):
    client_name: str
    reason: str = ""
    event_name: str = "client.credit_frozen"


@dataclass
class EquipmentMaintenanceDue(DomainEvent):
    equipment_id: int
    next_maintenance: str = ""
    event_name: str = "equipment.maintenance_due"


@dataclass
class InspectionPlanExecuted(DomainEvent):
    plan_id: int
    next_execution: str = ""
    event_name: str = "inspection_plan.executed"


# ===== 事件总线 =====

class EventBus:
    """
    同步事件总线
    
    - 支持按事件名称注册处理器
    - 处理器之间相互隔离（一个失败不影响其他）
    - 支持异步模式（通过任务队列代理）
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def register(self, event_name: str, handler: Callable = None):
        """
        注册事件处理器
        
        支持两种用法:
            # 装饰器模式
            @event_bus.register("ticket.created")
            def handler(event):
                ...
            
            # 直接注册
            event_bus.register("ticket.created", my_handler)
        """
        if handler is None:
            # 作为装饰器使用
            def decorator(fn):
                self._register(event_name, fn)
                return fn
            return decorator
        
        self._register(event_name, handler)
    
    def _register(self, event_name: str, handler: Callable):
        """实际注册逻辑"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        logger.debug(f"EventBus: handler '{handler.__name__}' registered for '{event_name}'")
    
    def unregister(self, event_name: str, handler: Callable):
        """取消注册"""
        handlers = self._handlers.get(event_name, [])
        if handler in handlers:
            handlers.remove(handler)
    
    def dispatch(self, event: DomainEvent):
        """
        分发事件
        
        同步调用所有处理器，每个处理器有独立的 try/except，
        确保一个失败不影响其他处理器。
        """
        handlers = self._handlers.get(event.event_name, [])
        if not handlers:
            return
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"EventBus: handler '{handler.__name__}' "
                    f"failed for event '{event.event_name}': {e}",
                    exc_info=True
                )
    
    def clear(self):
        """清理所有处理器（测试用）"""
        self._handlers.clear()


# ===== 全局单例 =====
_event_bus_instance = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


def reset_event_bus():
    """重置事件总线（测试用）"""
    global _event_bus_instance
    _event_bus_instance = None
