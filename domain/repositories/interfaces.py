"""
博通 (Botong) — 仓储接口定义
所有仓储的抽象基类，支持 SQLite / PostgreSQL 切换
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple


class TicketRepository(ABC):
    """工单仓储接口"""
    
    @abstractmethod
    def find_by_id(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        ...
    
    @abstractmethod
    def find_list(self, filters: Dict[str, Any], page: int, per_page: int) -> Tuple[List[Dict[str, Any]], int]:
        ...
    
    @abstractmethod
    def save(self, ticket: Dict[str, Any]) -> int:
        ...
    
    @abstractmethod
    def update(self, ticket_id: int, data: Dict[str, Any]) -> bool:
        ...
    
    @abstractmethod
    def delete(self, ticket_id: int) -> bool:
        ...

    @abstractmethod
    def add_history(self, ticket_id: int, action: str, note: str = "",
                    operator: str = "") -> bool:
        ...

    @abstractmethod
    def link_equipment(self, ticket_id: int, equip_id: int):
        ...

    @abstractmethod
    def add_technician(self, ticket_id: int, name: str, cost_rate: float = 30.0,
                       hours: float = 0):
        ...


class ClientRepository(ABC):
    """客户仓储接口"""
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        ...
    
    @abstractmethod
    def find_list(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        ...
    
    @abstractmethod
    def save(self, client: Dict[str, Any]) -> int:
        ...
    
    @abstractmethod
    def update(self, name: str, data: Dict[str, Any]) -> bool:
        ...
    
    @abstractmethod
    def delete(self, name: str) -> bool:
        ...


class FinanceRepository(ABC):
    """财务仓储接口"""
    
    @abstractmethod
    def record_income(self, data: Dict[str, Any]) -> int:
        ...
    
    @abstractmethod
    def record_expense(self, data: Dict[str, Any]) -> int:
        ...
    
    @abstractmethod
    def get_monthly_income(self, start: str, end: str) -> float:
        ...
    
    @abstractmethod
    def get_monthly_expense(self, start: str, end: str) -> float:
        ...


class TodoRepository(ABC):
    """待办仓储接口"""
    
    @abstractmethod
    def find_by_id(self, todo_id: int) -> Optional[Dict[str, Any]]:
        ...
    
    @abstractmethod
    def find_list(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        ...
    
    @abstractmethod
    def save(self, todo: Dict[str, Any]) -> int:
        ...
    
    @abstractmethod
    def update(self, todo_id: int, data: Dict[str, Any]) -> bool:
        ...
    
    @abstractmethod
    def delete(self, todo_id: int) -> bool:
        ...
