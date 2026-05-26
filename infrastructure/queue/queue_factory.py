"""
博通 (Botong) — 队列工厂

根据 Redis 可用性自动选择实现:
  1. Redis 可用 → RQTaskQueue（生产模式）
  2. Redis 不可用 → LocalTaskQueue（回退模式，零依赖）
"""

import logging
import os

from infrastructure.queue.interfaces import Task, TaskQueue

logger = logging.getLogger(__name__)


def create_queue() -> TaskQueue:
    """
    创建任务队列实例
    
    自动检测 Redis 可用性，不可用时降级到 LocalTaskQueue。
    """
    redis_url = os.environ.get("REDIS_URL", "")

    if redis_url:
        try:
            from infrastructure.queue.rq_queue import RQTaskQueue
            queue = RQTaskQueue(redis_url=redis_url)
            logger.info("✅ 任务队列: RQTaskQueue (Redis: %s)", redis_url)
            return queue
        except Exception as e:
            logger.warning("Redis 不可用，降级到 LocalTaskQueue: %s", e)

    # 回退: 本地线程队列
    from infrastructure.queue.local_queue import LocalTaskQueue
    worker_count = int(os.environ.get("LOCAL_QUEUE_WORKERS", "2"))
    queue = LocalTaskQueue(max_workers=worker_count)
    logger.info("✅ 任务队列: LocalTaskQueue (workers=%d)", worker_count)
    return queue


def register_cron_jobs(queue: TaskQueue):
    """
    注册所有周期性任务到队列
    
    在应用启动时调用一次即可。
    """
    from tasks.reminder_tasks import check_reminders, check_periodic_tasks
    from tasks.maintenance_tasks import vacuum_database, analyze_queries

    # 预约提醒 — 每分钟
    try:
        queue.schedule(
            Task(
                name="tasks.reminder_tasks.check_reminders",
                payload={},
            ),
            cron_expr="* * * * *",
        )
        logger.info("  注册: check_reminders (每分钟)")
    except Exception as e:
        logger.warning("  注册失败 check_reminders: %s", e)

    # 周期性任务（订阅到期/逾期应收/待办/维保）— 每10分钟
    try:
        queue.schedule(
            Task(
                name="tasks.reminder_tasks.check_periodic_tasks",
                payload={},
            ),
            cron_expr="*/10 * * * *",
        )
        logger.info("  注册: check_periodic_tasks (每10分钟)")
    except Exception as e:
        logger.warning("  注册失败 check_periodic_tasks: %s", e)

    # 查询统计 — 每日凌晨 2 点
    try:
        queue.schedule(
            Task(
                name="tasks.maintenance_tasks.analyze_queries",
                payload={},
            ),
            cron_expr="0 2 * * *",
        )
        logger.info("  注册: analyze_queries (每日 2:00)")
    except Exception as e:
        logger.warning("  注册失败 analyze_queries: %s", e)

    # 数据库维护 — 每周日凌晨 3 点
    try:
        queue.schedule(
            Task(
                name="tasks.maintenance_tasks.vacuum_database",
                payload={},
            ),
            cron_expr="0 3 * * 0",
        )
        logger.info("  注册: vacuum_database (每周日 3:00)")
    except Exception as e:
        logger.warning("  注册失败 vacuum_database: %s", e)
