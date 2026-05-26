"""
博通 (Botong) — 后台任务定义

这些函数被 RQ Worker / LocalTaskQueue 调用。
替代旧版 reminder_svc.start_scheduler() 的 raw threading 方案。

手动触发测试:
    python -c "from tasks.reminder_tasks import check_reminders; check_reminders()"

cron 调度计划（已在 queue_factory.py 中注册）:
    * * * * *      check_reminders         — 每分钟检查预约提醒
    */10 * * * *   check_periodic_tasks    — 每10分钟检查订阅/逾期/待办/维保
    0 3 * * *      vacuum_database         — 每天凌晨3点数据库维护
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def check_reminders(**kwargs) -> Dict[str, Any]:
    """
    检查预约提醒（每分钟执行）
    
    替代旧版 scheduling loop 中的 _check_and_fire()。
    通过 RQ 持久化，崩溃不丢失。
    """
    from infrastructure.di.container import Container

    try:
        reminder_svc = Container.resolve("reminder_service")
    except KeyError as e:
        logger.error("DI container not ready: missing %s", e)
        return {"status": "error", "message": "DI not ready"}

    try:
        result = reminder_svc.check_reminders_cycle()
        return {"status": "ok", **result}
    except Exception as e:
        logger.error("check_reminders failed: %s", e)
        return {"status": "error", "message": str(e)}


def check_periodic_tasks(**kwargs) -> Dict[str, Any]:
    """
    周期性检查任务（每10分钟执行）
    
    替代旧版 scheduling loop 中的:
        - check_subscription_expiry()
        - _check_overdue_receivables()
        - _check_todo_reminders()
        - _check_maintenance_plans()
        - _check_equipment_maintenance()
    """
    from infrastructure.di.container import Container

    try:
        reminder_svc = Container.resolve("reminder_service")
    except KeyError as e:
        logger.error("DI container not ready: missing %s", e)
        return {"status": "error", "message": "DI not ready"}

    results = {}

    # 订阅到期检查
    try:
        subscriptions = reminder_svc.check_subscription_expiry_cycle()
        results["subscriptions"] = len(subscriptions) if subscriptions else 0
    except Exception as e:
        logger.warning("check_subscription_expiry failed: %s", e)
        results["subscriptions"] = -1

    # 逾期应收检查
    try:
        overdue = reminder_svc.check_overdue_receivables_cycle()
        results["overdue"] = len(overdue) if overdue else 0
    except Exception as e:
        logger.warning("check_overdue_receivables failed: %s", e)
        results["overdue"] = -1

    # 待办提醒检查
    try:
        todos = reminder_svc.check_todo_reminders_cycle()
        results["todos"] = len(todos) if todos else 0
    except Exception as e:
        logger.warning("check_todo_reminders failed: %s", e)
        results["todos"] = -1

    # 维保计划/设备维护检查
    try:
        maintenance = reminder_svc.check_maintenance_plans_cycle()
        results["maintenance"] = (len(maintenance.get("plans", []))
                                  + len(maintenance.get("equipment", [])))
    except Exception as e:
        logger.warning("check_maintenance failed: %s", e)
        results["maintenance"] = -1

    logger.info("Periodic tasks result: %s", results)
    return {"status": "ok", **results}


def send_async_notification(**kwargs) -> Dict[str, Any]:
    """
    异步发送推送通知

    用法:
        queue.enqueue(Task(
            name="tasks.reminder_tasks.send_async_notification",
            payload={"channel": "wecom", "message": "..."}
        ))
    """
    from infrastructure.di.container import Container

    channel = kwargs.get("channel", "wecom")
    message = kwargs.get("message", "")

    if not message:
        return {"status": "error", "message": "message is required"}

    try:
        if channel == "wecom":
            bot = Container.resolve("wecom_bot")
            bot.send_markdown(message)
        else:
            return {"status": "error", "message": f"unknown channel: {channel}"}

        logger.info("Async notification sent via %s", channel)
        return {"status": "ok", "channel": channel}
    except Exception as e:
        logger.error("Failed to send %s notification: %s", channel, e)
        return {"status": "error", "message": str(e)}
