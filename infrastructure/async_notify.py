"""
博通 (Botong) — 异步通知发送

轻量 fire-and-forget 方案：threading + 重试。
替代 RQ 入队发送通知，无需 Redis。

用法:
    from infrastructure.async_notify import async_notify
    async_notify("wecom", "工单状态已变更")
"""

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


def async_notify(
    channel: str,
    message: str,
    title: str = "",
    retries: int = 3,
    retry_delay: float = 2.0,
):
    """
    异步发送通知（fire-and-forget + 自动重试）

    Args:
        channel: "wecom" | "pushplus"
        message: 通知内容
        title: 通知标题（PushPlus 使用）
        retries: 最大重试次数
        retry_delay: 重试间隔（秒），指数退避
    """
    def _send():
        for attempt in range(1, retries + 1):
            try:
                from infrastructure.di.container import Container

                if channel == "wecom":
                    bot = Container.resolve("wecom_bot")
                    if bot:
                        bot.send_markdown(message)
                elif channel == "pushplus":
                    bot = Container.resolve("pushplus_bot")
                    if bot:
                        if title:
                            bot.send_markdown(title, message)
                        else:
                            bot.send_message(message)
                else:
                    logger.warning("Unknown notify channel: %s", channel)
                    return

                logger.info("Notification sent via %s (attempt %d)", channel, attempt)
                return

            except Exception as e:
                if attempt < retries:
                    wait = retry_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Notification %s failed (attempt %d/%d), retry in %.1fs: %s",
                        channel, attempt, retries, wait, e,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "Notification %s exhausted %d retries: %s",
                        channel, retries, e,
                    )

    t = threading.Thread(target=_send, daemon=True, name=f"notify-{channel}")
    t.start()
    return t
