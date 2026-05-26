"""
博通 (Botong) — 企业微信机器人推送客户端

支持向企业微信群机器人发送 Markdown 消息，
含配置管理、URL 验证、速率控制、推送时间窗口、重试机制。
"""

import json
import logging
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
WECOM_CONFIG_PATH = CONFIG_DIR / "wecom.json"

_MAX_RETRIES = 3
_RETRY_DELAY = 1
_RATE_LIMIT_INTERVAL = 3

_WEBHOOK_URL_PATTERN = re.compile(
    r"^https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[a-zA-Z0-9\-]+$"
)

_COMMON_WRONG_PATTERNS = [
    ("work.weixin.qq.com/wework_admin", "这是企业微信后台管理页面链接，不是 API Webhook 地址"),
    ("work.weixin.qq.com", "这是企业微信的页面地址，正确地址应以 qyapi.weixin.qq.com 开头"),
]


class WeComBotClient:

    def __init__(self, config_file: str = None):
        self._config_file = config_file or str(WECOM_CONFIG_PATH)
        self._last_send_time = 0
        self._load_config()

    def _load_config(self):
        try:
            if Path(self._config_file).exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._webhook_url = data.get("webhook_url", "")
                    self._enabled = data.get("enabled", False)
                    self._push_events = data.get("push_events", {
                        "reminder": True,
                        "todo": True,
                        "subscription": True,
                        "overdue": True,
                    })
                    self._time_window = data.get("time_window", {
                        "start": "08:00",
                        "end": "22:00",
                    })
                    return
        except Exception as e:
            logger.warning(f"加载企业微信配置失败: {e}")

        self._webhook_url = ""
        self._enabled = False
        self._push_events = {
            "reminder": True,
            "todo": True,
            "subscription": True,
            "overdue": True,
        }
        self._time_window = {"start": "08:00", "end": "22:00"}

    def validate_webhook_url(self, url: str) -> Optional[str]:
        url = url.strip()
        if not url:
            return "Webhook URL 不能为空"

        for pattern, hint in _COMMON_WRONG_PATTERNS:
            if pattern in url:
                return f"URL 格式错误：{hint}。\n正确格式：https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

        if not url.startswith("https://"):
            return "Webhook URL 必须以 https:// 开头"

        if "qyapi.weixin.qq.com" not in url:
            return "Webhook URL 域名必须是 qyapi.weixin.qq.com"

        if "/webhook/send" not in url:
            return "URL 路径中缺少 /webhook/send，请确认是正确的机器人 Webhook 地址"

        if "key=" not in url:
            return "URL 缺少 key 参数，请确认复制了完整的 Webhook 地址"

        return None

    def save_config(self) -> bool:
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "webhook_url": self._webhook_url,
                "enabled": self._enabled,
                "push_events": self._push_events,
                "time_window": self._time_window,
            }
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("✅ 企业微信配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存企业微信配置失败: {e}")
            return False

    @property
    def webhook_url(self) -> str:
        return self._webhook_url

    @webhook_url.setter
    def webhook_url(self, url: str):
        self._webhook_url = url.strip()

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._webhook_url)

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @property
    def push_events(self) -> Dict[str, bool]:
        return self._push_events

    @push_events.setter
    def push_events(self, events: Dict[str, bool]):
        self._push_events.update(events)

    def get_config(self) -> Dict:
        return {
            "webhook_url": self._webhook_url,
            "enabled": self._enabled,
            "push_events": self._push_events.copy(),
            "time_window": self._time_window.copy(),
        }

    def update_config(self, webhook_url: str = None,
                      enabled: bool = None,
                      push_events: Dict[str, bool] = None,
                      time_window: Dict[str, str] = None) -> bool:
        if webhook_url is not None:
            url = webhook_url.strip()
            if url:
                validation_error = self.validate_webhook_url(url)
                if validation_error:
                    logger.error(f"Webhook URL 验证失败: {validation_error}")
                    self._last_validation_error = validation_error
                    return False
            self._last_validation_error = None
            self._webhook_url = url
        if enabled is not None:
            self._enabled = enabled
        if push_events is not None:
            self._push_events.update(push_events)
        if time_window is not None:
            self._time_window.update(time_window)
        return self.save_config()

    @property
    def time_window(self) -> Dict[str, str]:
        return self._time_window

    @time_window.setter
    def time_window(self, value: Dict[str, str]):
        if "start" in value and "end" in value:
            self._time_window = value
        else:
            self._time_window.update(value)

    @property
    def last_validation_error(self) -> Optional[str]:
        return getattr(self, '_last_validation_error', None)

    def in_time_window(self) -> Dict:
        from datetime import datetime as _dt
        now = _dt.now()
        current = now.strftime("%H:%M")
        w_start = self._time_window.get("start", "08:00")
        w_end = self._time_window.get("end", "22:00")

        if w_end < w_start:
            if current >= w_start or current < w_end:
                return {"ok": True}
        else:
            if w_start <= current <= w_end:
                return {"ok": True}

        return {"ok": False, "msg": f"推送窗口为 {w_start}-{w_end}，当前 {current} 不在窗口内"}

    def build_markdown(self, title: str, content: str,
                       ticket_no: str = "",
                       client: str = "",
                       amount: float = None,
                       extra_lines: List[str] = None) -> str:
        now = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        lines = [
            f"## 📋 {title}",
            f"> {now}",
            "---",
            content,
        ]

        meta_parts = []
        if ticket_no:
            meta_parts.append(f"工单: **{ticket_no}**")
        if client:
            meta_parts.append(f"客户: **{client}**")
        if amount is not None:
            meta_parts.append(f"金额: **¥{amount:.2f}**")

        if meta_parts:
            lines.append("")
            lines.append(" | ".join(meta_parts))

        if extra_lines:
            lines.append("")
            lines.extend(extra_lines)

        lines.append("")
        lines.append("<font color=\"comment\">博通 · 自动推送</font>")

        return "\n".join(lines)

    def build_test_message(self) -> str:
        return self.build_markdown(
            "✅ 企业微信推送测试",
            "这是一条来自博通的测试消息\n\n如果看到这条消息，说明企业微信机器人配置正确！",
            extra_lines=[
                "---",
                "- 系统版本: 博通 Botong v3.0",
                f"- 推送时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}",
            ]
        )

    def send_markdown(self, markdown_text: str) -> Dict:
        if not self._webhook_url:
            return {"ok": False, "error": "企业微信机器人未配置 Webhook URL"}

        if not self._enabled:
            return {"ok": False, "error": "企业微信机器人推送功能未启用"}

        window_check = self.in_time_window()
        if not window_check["ok"]:
            logger.info(f"企业微信推送跳过（不在推送时间窗口内）: {window_check.get('msg','')}")
            return {"ok": False, "error": f"不在推送时间窗口内", "skip": True, "detail": window_check}

        validation_error = self.validate_webhook_url(self._webhook_url)
        if validation_error:
            logger.error(f"发送消息前检测到 Webhook URL 格式错误: {validation_error}")
            return {"ok": False, "error": f"Webhook URL 格式错误: {validation_error}"}

        now = time.time()
        elapsed = now - self._last_send_time
        if elapsed < _RATE_LIMIT_INTERVAL:
            time.sleep(_RATE_LIMIT_INTERVAL - elapsed)

        payload = {
            "msgtype": "markdown",
            "markdown": {"content": markdown_text},
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        safe_url = self._safe_webhook_url()

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    self._webhook_url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = resp.read().decode()
                    result = json.loads(body)
                    if result.get("errcode") == 0:
                        self._last_send_time = time.time()
                        logger.info("✅ 企业微信消息推送成功")
                        return {"ok": True}
                    else:
                        errcode = result.get("errcode")
                        errmsg = result.get("errmsg", "未知错误")
                        logger.warning(
                            f"企业微信推送失败(尝试{attempt}/{_MAX_RETRIES}): "
                            f"errcode={errcode}, errmsg={errmsg}, "
                            f"url={safe_url}"
                        )
                        if attempt < _MAX_RETRIES:
                            time.sleep(_RETRY_DELAY * attempt)
            except urllib.error.HTTPError as e:
                logger.warning(
                    f"企业微信推送HTTP错误(尝试{attempt}/{_MAX_RETRIES}): "
                    f"HTTP {e.code} {e.reason}, url={safe_url}"
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)
            except urllib.error.URLError as e:
                logger.warning(
                    f"企业微信推送网络错误(尝试{attempt}/{_MAX_RETRIES}): "
                    f"{e.reason}, url={safe_url}"
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)
            except Exception as e:
                logger.error(
                    f"企业微信推送异常(尝试{attempt}/{_MAX_RETRIES}): {e}, "
                    f"url={safe_url}"
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)

        return {"ok": False, "error": f"推送失败，已重试{_MAX_RETRIES}次"}

    def _safe_webhook_url(self) -> str:
        u = self._webhook_url or ''
        if 'key=' in u:
            u = u.split('key=')[0] + 'key=***'
        return u

    @staticmethod
    def _mask_url(url: str) -> str:
        if 'key=' in url:
            return url.split('key=')[0] + 'key=***'
        return url

    def send_test(self) -> Dict:
        if not self._webhook_url:
            return {"ok": False, "error": "请先配置企业微信机器人 Webhook URL"}
        validation_error = self.validate_webhook_url(self._webhook_url)
        if validation_error:
            return {"ok": False, "error": f"Webhook URL 格式错误: {validation_error}"}
        msg = self.build_test_message()
        return self.send_markdown(msg)

    def push_reminder(self, ticket_no: str, client: str,
                      content: str, appointment_at: str = "") -> Dict:
        if not self._push_events.get("reminder", True):
            return {"ok": False, "error": "reminder 事件已关闭"}
        extra = []
        if appointment_at:
            extra.append(f"预约时间: **{appointment_at}**")
        msg = self.build_markdown(
            "⏰ 工单预约提醒",
            content,
            ticket_no=ticket_no,
            client=client,
            extra_lines=extra,
        )
        return self.send_markdown(msg)

    def push_todo_reminder(self, title: str, description: str = "",
                           estimated_minutes: int = None,
                           source_info: str = "") -> Dict:
        if not self._push_events.get("todo", True):
            return {"ok": False, "error": "todo 事件已关闭"}
        extra = []
        if estimated_minutes:
            extra.append(f"预估耗时: **{estimated_minutes} 分钟**")
        if source_info:
            extra.append(f"来源: {source_info}")
        if description:
            extra.append(f"说明: {description}")
        msg = self.build_markdown(
            "📌 待办到期提醒",
            f"待办事项 **「{title}」** 已到期，请及时处理",
            extra_lines=extra,
        )
        return self.send_markdown(msg)

    def push_subscription_expiry(self, client: str, product: str,
                                  expires_at: str, days_left: int) -> Dict:
        if not self._push_events.get("subscription", True):
            return {"ok": False, "error": "subscription 事件已关闭"}

        urgency = "🔴" if days_left <= 0 else ("🟡" if days_left <= 3 else "🟢")
        title = f"{urgency} 订阅到期提醒"
        if days_left == 0:
            content = f"**{client}** 的 **{product}** 今天到期！请及时续费"
        else:
            content = f"**{client}** 的 **{product}** 将于 **{expires_at}** 到期（剩余 **{days_left}** 天）"

        msg = self.build_markdown(
            title, content,
            client=client,
            extra_lines=[f"到期日期: **{expires_at}**", f"剩余天数: **{days_left} 天**"],
        )
        return self.send_markdown(msg)

    def push_overdue_notice(self, client: str, ref: str,
                            amount: float, days_overdue: int) -> Dict:
        if not self._push_events.get("overdue", True):
            return {"ok": False, "error": "overdue 事件已关闭"}

        urgency = "🔴" if days_overdue >= 60 else ("🟡" if days_overdue >= 30 else "🟢")
        title = f"{urgency} 逾期催收提醒"
        content = f"**{client}** 的 **{ref}** 已逾期 **{days_overdue}** 天"

        msg = self.build_markdown(
            title, content,
            client=client,
            amount=amount,
            extra_lines=[f"逾期天数: **{days_overdue} 天**",
                        "> 请尽快安排催收" if days_overdue < 60 else "> ⚠️ 严重逾期，建议立即处理"],
        )
        return self.send_markdown(msg)

    def push_status_change(self, event) -> Dict:
        data = event.data if hasattr(event, 'data') else event
        ticket_no = data.get("ticket_no", "")
        client = data.get("client", "")
        old_status = data.get("old_status", "")
        new_status = data.get("new_status", "")
        msg = self.build_markdown(
            "🔄 工单状态变更",
            f"工单 **{ticket_no}** 状态从 **{old_status}** 变更为 **{new_status}**",
            ticket_no=ticket_no,
            client=client,
        )
        return self.send_markdown(msg)

    def push_payment_notice(self, event) -> Dict:
        data = event.data if hasattr(event, 'data') else event
        ticket_no = data.get("ticket_no", "")
        client = data.get("client", "")
        amount = data.get("amount", 0)
        msg = self.build_markdown(
            "💰 收款通知",
            f"工单 **{ticket_no}** 已确认收款",
            ticket_no=ticket_no,
            client=client,
            amount=amount,
        )
        return self.send_markdown(msg)

    def send_text(self, content: str, mentioned_list: List[str] = None) -> Dict:
        if not self._webhook_url or not self._enabled:
            return {"ok": False, "error": "企业微信机器人未配置或未启用"}

        payload = {
            "msgtype": "text",
            "text": {"content": content},
        }
        if mentioned_list:
            payload["text"]["mentioned_list"] = mentioned_list

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            req = urllib.request.Request(
                self._webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                if result.get("errcode") == 0:
                    return {"ok": True}
                return {"ok": False, "error": result.get("errmsg", "未知错误")}
        except Exception as e:
            return {"ok": False, "error": str(e)}
