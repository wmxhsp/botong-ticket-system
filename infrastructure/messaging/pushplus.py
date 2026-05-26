"""
博通 (Botong) — PushPlus 推送客户端

支持通过 PushPlus API 推送消息到个人微信
PushPlus 官网: https://www.pushplus.plus
API: POST https://www.pushplus.plus/send
"""

import json
import logging
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
PUSHPLUS_CONFIG_PATH = CONFIG_DIR / "pushplus.json"
PUSHPLUS_API_URL = "https://www.pushplus.plus/send"

_MAX_RETRIES = 3
_RETRY_DELAY = 1
_RATE_LIMIT_INTERVAL = 2


class PushPlusClient:

    def __init__(self, config_file: str = None):
        self._config_file = config_file or str(PUSHPLUS_CONFIG_PATH)
        self._last_send_time = 0
        self._load_config()

    def _load_config(self):
        try:
            if Path(self._config_file).exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._token = data.get("token", "")
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
            logger.warning(f"加载 PushPlus 配置失败: {e}")

        self._token = ""
        self._enabled = False
        self._push_events = {
            "reminder": True,
            "todo": True,
            "subscription": True,
            "overdue": True,
        }
        self._time_window = {"start": "08:00", "end": "22:00"}

    def save_config(self) -> bool:
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "token": self._token,
                "enabled": self._enabled,
                "push_events": self._push_events,
                "time_window": self._time_window,
            }
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("✅ PushPlus 配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存 PushPlus 配置失败: {e}")
            return False

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str):
        self._token = value.strip()

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._token)

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
            "token": self._token,
            "enabled": self._enabled,
            "push_events": self._push_events.copy(),
            "time_window": self._time_window.copy(),
        }

    def update_config(self, token: str = None,
                      enabled: bool = None,
                      push_events: Dict[str, bool] = None,
                      time_window: Dict[str, str] = None) -> bool:
        if token is not None:
            self._token = token.strip()
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
                       extra_lines: List[str] = None) -> Dict[str, str]:
        now = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        lines = [
            f"# {title}",
            f"> {now}",
            "---",
            content,
        ]

        meta_parts = []
        if ticket_no:
            meta_parts.append(f"**工单:** {ticket_no}")
        if client:
            meta_parts.append(f"**客户:** {client}")
        if amount is not None:
            meta_parts.append(f"**金额:** ¥{amount:.2f}")

        if meta_parts:
            lines.append("")
            lines.append(" | ".join(meta_parts))

        if extra_lines:
            lines.append("")
            lines.extend(extra_lines)

        lines.append("")
        lines.append("---")
        lines.append("*博通 · 自动推送*")

        markdown_text = "\n".join(lines)

        return {
            "token": self._token,
            "title": title,
            "content": markdown_text,
            "template": "markdown",
        }

    def build_test_message(self) -> Dict[str, str]:
        return self.build_markdown(
            "✅ PushPlus 推送测试",
            "这是一条来自博通的测试消息\n\n如果看到这条消息，说明 PushPlus 配置正确！",
            extra_lines=[
                "---",
                "- 系统版本: 博通 Botong v4.0",
                f"- 推送时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}",
            ]
        )

    def send_raw(self, payload: Dict) -> Dict:
        if not self.enabled:
            return {"ok": False, "error": "PushPlus 未启用或未配置 Token"}

        window_check = self.in_time_window()
        if not window_check["ok"]:
            logger.info(f"PushPlus 推送跳过（不在推送时间窗口内）: {window_check.get('msg', '')}")
            return {"ok": False, "error": "不在推送时间窗口内", "skip": True, "detail": window_check}

        now = time.time()
        elapsed = now - self._last_send_time
        if elapsed < _RATE_LIMIT_INTERVAL:
            time.sleep(_RATE_LIMIT_INTERVAL - elapsed)

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    PUSHPLUS_API_URL,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = resp.read().decode()
                    result = json.loads(body)
                    code = result.get("code", 0)
                    if code == 200:
                        self._last_send_time = time.time()
                        logger.info("✅ PushPlus 消息推送成功")
                        return {"ok": True}
                    else:
                        errmsg = result.get("msg", result.get("message", "未知错误"))
                        logger.warning(f"PushPlus 推送失败(尝试{attempt}/{_MAX_RETRIES}): code={code} {errmsg}")
                        if attempt < _MAX_RETRIES:
                            time.sleep(_RETRY_DELAY * attempt)
            except urllib.error.HTTPError as e:
                logger.warning(f"PushPlus HTTP错误(尝试{attempt}/{_MAX_RETRIES}): {e.code}")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)
            except urllib.error.URLError as e:
                logger.warning(f"PushPlus 网络错误(尝试{attempt}/{_MAX_RETRIES}): {e.reason}")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)
            except Exception as e:
                logger.error(f"PushPlus 推送异常(尝试{attempt}/{_MAX_RETRIES}): {e}")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)

        return {"ok": False, "error": f"推送失败，已重试{_MAX_RETRIES}次"}

    def send(self, title: str, content: str, template: str = "markdown") -> Dict:
        payload = {
            "token": self._token,
            "title": title,
            "content": content,
            "template": template,
        }
        return self.send_raw(payload)

    def send_message(self, content: str, title: str = "") -> Dict:
        return self.send(title or "博通通知", content)

    def send_markdown(self, title: str, body: str, **kwargs) -> Dict:
        ticket_no = kwargs.get("ticket_no", "")
        client = kwargs.get("client", "")
        amount = kwargs.get("amount")
        extra_lines = kwargs.get("extra_lines")
        payload = self.build_markdown(
            title, body,
            ticket_no=ticket_no,
            client=client,
            amount=amount,
            extra_lines=extra_lines,
        )
        return self.send_raw(payload)

    def send_test(self) -> Dict:
        if not self._token:
            return {"ok": False, "error": "请先配置 PushPlus Token"}
        payload = self.build_test_message()
        return self.send_raw(payload)

    def push_reminder(self, ticket_no: str, client: str,
                      content: str, appointment_at: str = "") -> Dict:
        if not self._push_events.get("reminder", True):
            return {"ok": False, "error": "reminder 事件已关闭"}
        extra = []
        if appointment_at:
            extra.append(f"**预约时间:** {appointment_at}")
        return self.send_markdown(
            "⏰ 工单预约提醒", content,
            ticket_no=ticket_no, client=client,
            extra_lines=extra,
        )

    def push_payment_notice(self, event) -> Dict:
        data = event.data if hasattr(event, 'data') else event
        ticket_no = data.get("ticket_no", "")
        client = data.get("client", "")
        amount = data.get("amount", 0)
        return self.send_markdown(
            "💰 收款通知",
            f"工单 **{ticket_no}** 已确认收款",
            ticket_no=ticket_no,
            client=client,
            amount=amount,
        )

    def push_todo_reminder(self, title: str, description: str = "",
                           estimated_minutes: int = None,
                           source_info: str = "") -> Dict:
        if not self._push_events.get("todo", True):
            return {"ok": False, "error": "todo 事件已关闭"}
        extra = []
        if estimated_minutes:
            extra.append(f"**预估耗时:** {estimated_minutes} 分钟")
        if source_info:
            extra.append(f"**来源:** {source_info}")
        if description:
            extra.append(f"**说明:** {description}")
        return self.send_markdown(
            "📌 待办到期提醒",
            f"待办事项 **「{title}」** 已到期，请及时处理",
            extra_lines=extra,
        )

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

        return self.send_markdown(
            title, content, client=client,
            extra_lines=[f"**到期日期:** {expires_at}", f"**剩余天数:** {days_left} 天"],
        )

    def push_overdue_notice(self, client: str, ref: str,
                            amount: float, days_overdue: int) -> Dict:
        if not self._push_events.get("overdue", True):
            return {"ok": False, "error": "overdue 事件已关闭"}

        urgency = "🔴" if days_overdue >= 60 else ("🟡" if days_overdue >= 30 else "🟢")
        title = f"{urgency} 逾期催收提醒"
        content = f"**{client}** 的 **{ref}** 已逾期 **{days_overdue}** 天"

        return self.send_markdown(
            title, content, client=client, amount=amount,
            extra_lines=[
                f"**逾期天数:** {days_overdue} 天",
                "> 请尽快安排催收" if days_overdue < 60 else "> ⚠️ 严重逾期，建议立即处理",
            ],
        )
