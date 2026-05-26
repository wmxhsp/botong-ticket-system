"""
博通 (Botong) — 数据库抽象层
支持 SQLite / PostgreSQL 切换的数据库接口
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Generator
import logging

logger = logging.getLogger(__name__)


class Database(ABC):
    """数据库抽象接口"""
    
    @abstractmethod
    @contextmanager
    def get_connection(self) -> Generator:
        """获取原生连接"""
        ...
    
    @abstractmethod
    def execute(self, sql: str, params: tuple = ()) -> int:
        """执行 SQL（INSERT/UPDATE/DELETE）"""
        ...
    
    @abstractmethod
    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """查询多条"""
        ...
    
    @abstractmethod
    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """查询单条"""
        ...
    
    @abstractmethod
    @contextmanager
    def transaction(self) -> Generator:
        """事务上下文"""
        ...


# ===== 工作单元（UnitOfWork）— 确保事务内共享同一连接 =====

class UnitOfWork:
    """
    工作单元上下文管理器。
    
    保证事务内的所有 Repository 操作共享同一个数据库连接，
    统一提交或回滚。解决 db_execute() 在外层事务内产生独立连接的问题。
    
    用法:
        with UnitOfWork() as uow:
            ticket_repo = SqliteTicketRepository(conn=uow.conn)
            ticket_repo.update(1, {"status": "closed"})
            finance_repo = SqliteFinanceRepository(conn=uow.conn)
            finance_repo.record_income({...})
            # 正常退出自动提交，异常自动回滚
    """
    
    def __init__(self):
        self.conn = None
        self._ctx = None

    def __enter__(self):
        from infrastructure.persistence.legacy_db import _db_pool
        self._ctx = _db_pool.get_connection()
        self.conn = self._ctx.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            try:
                self.conn.commit()
            except Exception:
                pass
        else:
            try:
                self.conn.rollback()
            except Exception:
                pass
        if self._ctx:
            try:
                self._ctx.__exit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass
        self.conn = None
        self._ctx = None
