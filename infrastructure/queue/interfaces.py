"""
博通 (Botong) — 任务队列抽象层

支持三种实现:
  1. RQTaskQueue      — 基于 Redis + RQ，生产环境（任务持久化、多进程 Worker）
  2. LocalTaskQueue   — 本地线程队列，零依赖（开发/单机回退）
  3. CeleryTaskQueue  — 未来分布式场景扩展

用法:
    from infrastructure.di.container import Container
    Container.register("queue", lambda: RQTaskQueue("redis://localhost:6379/0"))
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Task:
    """统一任务定义"""
    name: str                      # 任务函数名，如 "tasks.reminder_tasks.check_reminders"
    payload: Dict[str, Any] = field(default_factory=dict)  # 参数字典
    task_id: Optional[str] = None  # 可选自定义 ID
    delay: int = 0                 # 延迟执行（秒）
    max_retries: int = 3           # 最大重试次数
    retry_delay: int = 60          # 重试间隔（秒）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TaskStatus:
    """任务状态"""
    task_id: str
    status: str       # queued / running / finished / failed / cancelled
    name: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskQueue(ABC):
    """
    任务队列抽象接口
    
    职责:
        - 异步执行任务（enqueue）
        - 定时执行任务（enqueue_at / schedule）
        - 任务状态查询（get_status）
        - 任务取消（cancel）
    """

    @abstractmethod
    def enqueue(self, task: Task) -> str:
        """异步执行任务，返回 task_id"""
        ...

    @abstractmethod
    def enqueue_at(self, task: Task, run_at: datetime) -> str:
        """在指定时间执行任务"""
        ...

    @abstractmethod
    def schedule(self, task: Task, cron_expr: str) -> str:
        """按 cron 表达式周期性执行"""
        ...

    @abstractmethod
    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """查询任务执行状态"""
        ...

    @abstractmethod
    def cancel(self, task_id: str) -> bool:
        """取消待执行任务"""
        ...

    @abstractmethod
    def get_failed(self, limit: int = 100) -> List[TaskStatus]:
        """获取最近失败的任务列表"""
        ...

    @abstractmethod
    def get_queue_size(self) -> int:
        """当前队列中等待的任务数"""
        ...
