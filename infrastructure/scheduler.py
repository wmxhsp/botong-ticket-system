"""
博通 (Botong) — 定时任务调度器

基于 APScheduler 替代原 RQ/LocalQueue 方案：
  - 纯 Python，零外部依赖（不需要 Redis）
  - 真正的 cron 表达式支持
  - SQLite 持久化（进程重启不丢任务）
  - 进程内线程调度，无需独立 Worker 进程

用法:
    from infrastructure.scheduler import get_scheduler
    scheduler = get_scheduler()
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_scheduler: Optional["BackgroundScheduler"] = None


def get_scheduler():
    """获取全局调度器实例（懒初始化）"""
    global _scheduler
    if _scheduler is None:
        _scheduler = _create_scheduler()
    return _scheduler


def _create_scheduler():
    """创建并启动 APScheduler 实例"""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.jobstores.memory import MemoryJobStore

    # 单机系统用 MemoryJobStore 即可（任务定义在代码中，重启后重新注册）
    # 如果需要持久化 cron 任务状态，可换 SQLAlchemyJobStore
    scheduler = BackgroundScheduler(
        jobstores={"default": MemoryJobStore()},
        job_defaults={
            "coalesce": True,       # 同一任务堆积时只执行一次
            "max_instances": 1,     # 同一任务不并发
            "misfire_grace_time": 60,  # 错过执行时间 60s 内仍执行
        },
        timezone="Asia/Shanghai",
    )
    return scheduler


def register_cron_jobs(scheduler):
    """
    注册所有周期性定时任务

    在应用启动时调用一次。
    """
    # 预约提醒 — 每分钟
    try:
        scheduler.add_job(
            _wrap_task("tasks.reminder_tasks.check_reminders"),
            "cron",
            minute="*",
            id="check_reminders",
            replace_existing=True,
        )
        logger.info("  注册: check_reminders (每分钟)")
    except Exception as e:
        logger.warning("  注册失败 check_reminders: %s", e)

    # 周期性任务（订阅到期/逾期应收/待办/维保）— 每10分钟
    try:
        scheduler.add_job(
            _wrap_task("tasks.reminder_tasks.check_periodic_tasks"),
            "cron",
            minute="*/10",
            id="check_periodic_tasks",
            replace_existing=True,
        )
        logger.info("  注册: check_periodic_tasks (每10分钟)")
    except Exception as e:
        logger.warning("  注册失败 check_periodic_tasks: %s", e)

    # 查询统计 — 每日凌晨 2 点
    try:
        scheduler.add_job(
            _wrap_task("tasks.maintenance_tasks.analyze_queries"),
            "cron",
            hour="2",
            id="analyze_queries",
            replace_existing=True,
        )
        logger.info("  注册: analyze_queries (每日 2:00)")
    except Exception as e:
        logger.warning("  注册失败 analyze_queries: %s", e)

    # 数据库维护 — 每周日凌晨 3 点
    try:
        scheduler.add_job(
            _wrap_task("tasks.maintenance_tasks.vacuum_database"),
            "cron",
            day_of_week="sun",
            hour="3",
            id="vacuum_database",
            replace_existing=True,
        )
        logger.info("  注册: vacuum_database (每周日 3:00)")
    except Exception as e:
        logger.warning("  注册失败 vacuum_database: %s", e)


def _wrap_task(task_path: str):
    """
    将 "tasks.xxx.func_name" 包装为可直接调度的函数。

    APScheduler 直接调用 Python 函数，不需要 RQ 的 "module.func" 字符串解析。
    包装层做延迟导入 + 异常兜底，防止单个任务失败影响调度器。
    """
    def _run():
        try:
            import importlib
            module_path, func_name = task_path.rsplit(".", 1)
            mod = importlib.import_module(module_path)
            func = getattr(mod, func_name)
            result = func()
            logger.debug("Task %s completed: %s", task_path, result)
        except Exception as e:
            logger.error("Task %s failed: %s", task_path, e)

    _run.__name__ = task_path  # 方便 APScheduler 日志识别
    return _run
