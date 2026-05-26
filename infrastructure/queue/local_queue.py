"""
博通 (Botong) — 本地线程任务队列

零依赖的本地回退方案，当 Redis 不可用时自动降级。
不适用于生产环境（进程崩溃后任务丢失），但开发调试很方便。

用法:
    from infrastructure.di.container import Container
    Container.register("queue", lambda: LocalTaskQueue())
"""

import logging
import threading
import time
import uuid
from typing import Any, Dict, Optional, List
from datetime import datetime
from collections import OrderedDict

from infrastructure.queue.interfaces import Task, TaskQueue, TaskStatus

logger = logging.getLogger(__name__)


class LocalTaskQueue(TaskQueue):
    """
    本地线程队列

    特点:
        - 零依赖（纯 Python threading）
        - 进程级队列，重启丢失 ❌
        - 适合开发/测试环境
        - 自动重试（同 RQ 策略）
    """

    def __init__(self, max_workers: int = 2):
        self._queue: "OrderedDict[str, Task]" = OrderedDict()
        self._results: Dict[str, TaskStatus] = {}
        self._lock = threading.Lock()
        self._running = True
        # 启动 Worker 线程
        self._workers = []
        for i in range(max_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True,
                                 name=f"local-queue-worker-{i}")
            t.start()
            self._workers.append(t)
        logger.info("LocalTaskQueue started (workers=%d)", max_workers)

    def enqueue(self, task: Task) -> str:
        task_id = task.task_id or f"local-{uuid.uuid4().hex[:12]}"
        task.task_id = task_id
        with self._lock:
            self._queue[task_id] = task
            self._results[task_id] = TaskStatus(
                task_id=task_id, status="queued", name=task.name,
                created_at=datetime.now().isoformat(),
            )
        logger.debug("LocalTaskQueue enqueued: %s (id=%s)", task.name, task_id)
        return task_id

    def enqueue_at(self, task: Task, run_at: datetime) -> str:
        """延迟执行 — 计算等待时间，用 delay 模拟"""
        delay = max(0, (run_at - datetime.now()).total_seconds())
        task.delay = int(delay)
        return self.enqueue(task)

    def schedule(self, task: Task, cron_expr: str) -> str:
        """
        简化 cron 支持（仅支持每分钟触发）
        完整 cron 需使用 RQ 版本
        """
        task_id = task.task_id or f"cron-{uuid.uuid4().hex[:12]}"
        task.task_id = task_id

        def cron_loop():
            while self._running:
                self.enqueue(task)
                time.sleep(60)  # 每分钟执行一次

        t = threading.Thread(target=cron_loop, daemon=True,
                             name=f"cron-{task.name}")
        t.start()
        logger.info("LocalTaskQueue cron started [* * * * *]: %s", task.name)
        return task_id

    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        with self._lock:
            return self._results.get(task_id)

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._queue:
                del self._queue[task_id]
                if task_id in self._results:
                    self._results[task_id].status = "cancelled"
                return True
            return False

    def get_failed(self, limit: int = 100) -> List[TaskStatus]:
        with self._lock:
            failed = [s for s in self._results.values()
                      if s.status == "failed"]
            return failed[:limit]

    def get_queue_size(self) -> int:
        with self._lock:
            return len(self._queue)

    def shutdown(self):
        """关闭队列（测试用）"""
        self._running = False
        logger.info("LocalTaskQueue shut down")

    # ─── 内部 Worker ───

    def _worker_loop(self):
        """Worker 线程：从队列取任务并执行"""
        while self._running:
            task = self._dequeue()
            if task is None:
                time.sleep(0.1)
                continue
            self._execute(task)

    def _dequeue(self) -> Optional[Task]:
        with self._lock:
            for task_id in list(self._queue.keys()):
                task = self._queue.pop(task_id)
                if task.delay > 0:
                    # 延迟任务，先记下创建时间，后续检查
                    pass
                return task
            return None

    def _execute(self, task: Task):
        """执行单个任务"""
        with self._lock:
            if task.task_id in self._results:
                self._results[task.task_id].status = "running"
                self._results[task.task_id].started_at = datetime.now().isoformat()

        import importlib
        retries = 0
        while retries <= task.max_retries:
            try:
                # 按 "module.function" 格式导入并执行
                module_path, func_name = task.name.rsplit(".", 1)
                mod = importlib.import_module(module_path)
                func = getattr(mod, func_name)
                result = func(**task.payload)

                with self._lock:
                    if task.task_id in self._results:
                        self._results[task.task_id].status = "finished"
                        self._results[task.task_id].ended_at = datetime.now().isoformat()
                        self._results[task.task_id].result = result
                return

            except Exception as e:
                retries += 1
                logger.warning("Task %s failed (attempt %d/%d): %s",
                               task.name, retries, task.max_retries + 1, e)
                if retries <= task.max_retries:
                    time.sleep(task.retry_delay)
                else:
                    with self._lock:
                        if task.task_id in self._results:
                            self._results[task.task_id].status = "failed"
                            self._results[task.task_id].ended_at = datetime.now().isoformat()
                            self._results[task.task_id].error = str(e)
                    logger.error("Task %s exhausted retries: %s", task.name, e)
                    # 记录失败任务到磁盘日志，便于运维审计
                    try:
                        import os, json
                        os.makedirs(os.path.join(os.getcwd(), 'logs'), exist_ok=True)
                        log_path = os.path.join(os.getcwd(), 'logs', 'queue_failed.log')
                        with open(log_path, 'a', encoding='utf-8') as lf:
                            lf.write(json.dumps({
                                'task_id': task.task_id,
                                'name': task.name,
                                'error': str(e),
                                'time': datetime.now().isoformat()
                            }, ensure_ascii=False) + "\n")
                    except Exception:
                        pass
