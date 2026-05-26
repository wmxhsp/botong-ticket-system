"""
博通 (Botong) — RQ (Redis Queue) 任务队列实现

生产环境推荐方案：
  - 任务持久化到 Redis，进程崩溃不丢失
  - Worker 多进程并行处理（默认 2 个进程）
  - 自动重试（最多 3 次，间隔 60 秒）
  - 支持 cron 定时任务

安装依赖:
    pip install redis rq rq-scheduler

启动 Worker:
    rq worker botong-tasks --url redis://localhost:6379/0
    rqscheduler --host localhost --port 6379 --db 0
"""

import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

from infrastructure.queue.interfaces import Task, TaskQueue, TaskStatus

logger = logging.getLogger(__name__)


class RQTaskQueue(TaskQueue):
    """
    RQ 任务队列

    在 DI 容器中注册:
        Container.register("queue", lambda: RQTaskQueue("redis://localhost:6379/0"))
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        from redis import Redis
        from rq import Queue as RQQueue
        from rq.scheduler import RQScheduler

        self._redis = Redis.from_url(redis_url)
        self._queue = RQQueue("botong-tasks", connection=self._redis)
        self._scheduler = RQScheduler(queue=self._queue, connection=self._redis)
        self._scheduler.start()
        logger.info("RQTaskQueue initialized (redis=%s)", redis_url)

    def enqueue(self, task: Task) -> str:
        """异步执行任务"""
        from rq import Retry

        job = self._queue.enqueue(
            task.name,
            kwargs=task.payload,
            job_id=task.task_id,
            retry=Retry(max=task.max_retries, interval=[task.retry_delay]),
            meta={"created_at": task.created_at},
        )
        logger.info("Task enqueued: %s (id=%s, retries=%d)",
                    task.name, job.id, task.max_retries)
        return job.id

    def enqueue_at(self, task: Task, run_at: datetime) -> str:
        """定时执行"""
        from rq import Retry

        job = self._queue.enqueue_at(
            run_at,
            task.name,
            kwargs=task.payload,
            job_id=task.task_id,
            retry=Retry(max=task.max_retries, interval=[task.retry_delay]),
        )
        logger.info("Task scheduled at %s: %s (id=%s)", run_at, task.name, job.id)
        return job.id

    def schedule(self, task: Task, cron_expr: str) -> str:
        """按 cron 周期性执行"""
        job = self._scheduler.cron(
            cron_expr,
            func=task.name,
            kwargs=task.payload,
            job_id=task.task_id,
        )
        logger.info("Cron scheduled [%s]: %s (id=%s)", cron_expr, task.name, job.id)
        return job.id

    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """查询任务状态"""
        from rq.job import Job

        try:
            job = Job.fetch(task_id, connection=self._redis)
            return TaskStatus(
                task_id=job.id,
                status=job.get_status(),
                name=job.func_name,
                created_at=job.created_at.isoformat() if job.created_at else None,
                started_at=job.started_at.isoformat() if job.started_at else None,
                ended_at=job.ended_at.isoformat() if job.ended_at else None,
                result=job.result,
                error=str(job.exc_info) if job.exc_info else None,
            )
        except Exception:
            return None

    def cancel(self, task_id: str) -> bool:
        """取消任务"""
        from rq.job import Job

        try:
            job = Job.fetch(task_id, connection=self._redis)
            job.cancel()
            return True
        except Exception:
            return False

    def get_failed(self, limit: int = 100) -> List[TaskStatus]:
        """获取失败任务列表"""
        from rq import Queue as RQQueue

        failed_queue = RQQueue("failed", connection=self._redis)
        result = []
        for j in failed_queue.get_jobs(limit):
            result.append(TaskStatus(
                task_id=j.id,
                status="failed",
                name=j.func_name,
                created_at=j.created_at.isoformat() if j.created_at else None,
                error=str(j.exc_info) if j.exc_info else None,
            ))
        return result

    def get_queue_size(self) -> int:
        return len(self._queue)
