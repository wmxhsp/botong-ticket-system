import logging
import re
import calendar
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from domain.events import EventBus, TodoDue

logger = logging.getLogger(__name__)


class ReminderService:

    def __init__(self, event_bus: EventBus = None, todo_service=None, config=None,
                 notification_repo=None, reminder_repo=None,
                 inventory_repo=None, finance_repo=None,
                 ticket_service=None, wecom_bot=None,
                 finance_service=None, client_service=None,
                 equipment_service=None):
        self._event_bus = event_bus
        self._todo_service = todo_service
        self._config = config
        self._notification_repo = notification_repo
        self._reminder_repo = reminder_repo
        self._inventory_repo = inventory_repo
        self._finance_repo = finance_repo
        self._ticket_service = ticket_service
        self._wecom_bot = wecom_bot
        self._finance_service = finance_service
        self._client_service = client_service
        self._equipment_service = equipment_service

    def _get_ticket_svc(self):
        return self._ticket_service

    def _get_wecom_bot(self):
        return self._wecom_bot

    def _get_finance_svc(self):
        return self._finance_service

    def _get_todo_svc(self):
        return self._todo_service

    def _get_client_svc(self):
        return self._client_service

    def _get_equipment_svc(self):
        return self._equipment_service

    def create_reminder(self, ticket_id: int, appointment_at: str,
                        client_name: str = "", service_content: str = "") -> Dict:
        try:
            dt = datetime.fromisoformat(appointment_at)
            reminder_time = dt.strftime("%H:%M")
        except Exception:
            reminder_time = datetime.now().strftime("%H:%M")

        content = f"{client_name} - {service_content}" if service_content else client_name

        data = {
            "ticket_id": ticket_id,
            "reminder_time": reminder_time,
            "content": content,
            "repeat_daily": 1,
            "active": 1,
        }
        reminder_id = self._reminder_repo.create(data)

        return {
            "id": reminder_id,
            "ticket_id": ticket_id,
            "reminder_time": reminder_time,
            "content": content,
            "repeat_daily": 1,
            "active": 1,
        }

    def cancel_reminder(self, ticket_id: int) -> bool:
        self._reminder_repo.cancel(ticket_id)
        return True

    def get_reminder(self, reminder_id: int) -> Optional[Dict]:
        return self._reminder_repo.get(reminder_id)

    def get_ticket_reminders(self, ticket_id: int) -> List[Dict]:
        return self._reminder_repo.get_by_ticket(ticket_id) or []

    def get_active_reminders(self) -> List[Dict]:
        return self._reminder_repo.get_active() or []

    def fire_reminder(self, reminder_id: int, ticket_id: int,
                      content: str) -> Dict:
        ticket = self._get_ticket_svc().get_ticket(ticket_id)
        ticket_no = ticket.get("ticket_no", "") if ticket else ""
        client = ticket.get("client", "") if ticket else ""
        appointment_at = ticket.get("appointment_at", "") if ticket else ""
        title = f"⏰ 预约提醒 - {ticket_no}"
        note_id = self._notification_repo.create({
            "ticket_id": ticket_id,
            "reminder_id": reminder_id,
            "title": title,
            "content": content,
            "read": 0,
            "source_type": "reminder",
            "source_id": reminder_id,
        })
        result = {
            "id": note_id,
            "ticket_id": ticket_id,
            "reminder_id": reminder_id,
            "title": title,
            "content": content,
        }

        try:
            if ticket_no or client:
                push_result = self._get_wecom_bot().push_reminder(
                    ticket_no=ticket_no,
                    client=client,
                    content=content,
                    appointment_at=appointment_at,
                )
                result["wecom_push"] = push_result.get("ok", False)
        except Exception as e:
            logger.warning(f"企业微信推送提醒失败: {e}")
            result["wecom_push"] = False

        if self._event_bus and result.get("id"):
            self._event_bus.dispatch(TodoDue(
                todo_id=result["id"],
                title=result.get("title", ""),
            ))

        return result

    def get_pending_notifications(self, limit: int = 20) -> List[Dict]:
        return self._notification_repo.get_pending() or []

    def get_all_notifications(self, limit: int = 50) -> List[Dict]:
        return self._notification_repo.get_all() or []

    def mark_notification_read(self, note_id: int) -> bool:
        self._notification_repo.mark_read(note_id)
        return True

    def mark_all_read(self) -> bool:
        self._notification_repo.mark_all_read()
        return True

    def get_unread_count(self) -> int:
        return self._notification_repo.get_unread_count()

    def check_reminders_cycle(self) -> Dict[str, Any]:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        active = self._reminder_repo.get_active_with_ticket_status()

        fired = 0
        skipped = 0
        for r in active:
            if r.get("reminder_time", "") != current_time:
                skipped += 1
                continue

            if self._notification_repo.check_exists_today(title=None, reminder_id=r["id"]):
                skipped += 1
                continue

            self.fire_reminder(r["id"], r["ticket_id"], r.get("content", ""))
            fired += 1

        if fired > 0:
            logger.info("Reminder cycle: %d fired, %d skipped", fired, skipped)
        return {"fired": fired, "skipped": skipped}

    def check_subscription_expiry_cycle(self) -> List[Dict]:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        week_later = (now + timedelta(days=7)).strftime("%Y-%m-%d")

        expiring = self._inventory_repo.get_expiring_subscriptions(today, week_later) if self._inventory_repo else []

        fired_notes = []
        for sale in expiring:
            days_left = (datetime.strptime(sale["expires_at"][:10], "%Y-%m-%d") - now).days
            if days_left < 0:
                days_left = 0

            product = sale.get("goods_name") or sale.get("product_name", "未知商品")
            title = f"订阅到期提醒 - {sale['client']}"
            content = (f"{sale['client']} 的 {product} 将于 "
                      f"{sale['expires_at'][:10]} 到期"
                      f"{'（今天到期！）' if days_left == 0 else f'（剩余{days_left}天）'}")

            if self._notification_repo.check_exists_today(title=title):
                continue

            note_id = self._notification_repo.create({
                "ticket_id": None,
                "reminder_id": None,
                "title": title,
                "content": content,
                "read": 0,
                "source_type": "subscription",
                "source_id": sale["id"],
            })
            fired_notes.append({
                "id": note_id,
                "sale_id": sale["id"],
                "client": sale["client"],
                "product": product,
                "expires_at": sale["expires_at"],
                "days_left": days_left,
            })

            try:
                self._get_wecom_bot().push_subscription_expiry(
                    client=sale["client"],
                    product=product,
                    expires_at=sale["expires_at"],
                    days_left=days_left,
                )
            except Exception as e:
                logger.warning(f"企业微信推送订阅到期提醒失败: {e}")

        return fired_notes

    def check_overdue_receivables_cycle(self) -> List[Dict]:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        overdue = self._get_finance_svc().get_overdue_receivables()
        if not overdue:
            return []

        for item in overdue:
            client = item.get("client", "")
            amount = float(item.get("amount", 0) or 0)
            days_overdue = item.get("overdue_days", 0)

            title = f"逾期催收提醒 - {client}"
            ref = item.get("ticket_no", f"#{item.get('source_id', '?')}")
            content = f"{client} 的 {ref} 逾期 {days_overdue} 天，应收 ¥{amount:.2f}（账期{item.get('payment_terms', 30)}天）"

            if self._notification_repo.check_exists_today(title=title):
                continue

            self._notification_repo.create({
                "ticket_id": None,
                "reminder_id": None,
                "title": title,
                "content": content,
                "read": 0,
                "source_type": "overdue",
                "source_id": item["id"],
            })

            try:
                self._get_wecom_bot().push_overdue_notice(
                    client=client,
                    ref=ref,
                    amount=amount,
                    days_overdue=days_overdue,
                )
            except Exception as e:
                logger.warning(f"企业微信推送逾期提醒失败: {e}")

            if days_overdue >= 60:
                freeze_title = f"紧急催收 - {client}（逾期{days_overdue}天）"
                freeze_content = f"{client} 的 {ref} 已逾期 {days_overdue} 天（¥{amount:.2f}），建议立即催收并考虑信用冻结"
                self._notification_repo.create({
                    "ticket_id": None,
                    "reminder_id": None,
                    "title": freeze_title,
                    "content": freeze_content,
                    "read": 0,
                    "source_type": "overdue",
                    "source_id": item["id"],
                })
                try:
                    self._get_todo_svc().create_from_finance(
                        client=client, amount=amount,
                        title=f"紧急催收 - {client}（逾期{days_overdue}天，¥{amount:.0f}）",
                        priority="H",
                        due_date=(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                        source_id=item["id"],
                    )
                except Exception:
                    pass
                if self._event_bus:
                    from domain.events import ClientCreditFrozen
                    self._event_bus.dispatch(ClientCreditFrozen(
                        client_name=client, reason="逾期60天+"))
                else:
                    self._get_client_svc().freeze_credit(client, "逾期60天+")
            elif days_overdue >= 30:
                try:
                    self._get_todo_svc().create_from_finance(
                        client=client, amount=amount,
                        title=f"催收跟进 - {client}（逾期{days_overdue}天）",
                        priority="M",
                        due_date=today,
                        source_id=item["id"],
                    )
                except Exception:
                    pass

        return []

    def check_todo_reminders_cycle(self) -> List[Dict]:
        try:
            reminders = self._get_todo_svc().check_reminders()
            if not reminders:
                return []

            for t in reminders:
                title = f"待办提醒 - {t['title']}"
                content = f"待办事项 <{t['title']}> 今天到期"
                if t.get("estimated_minutes"):
                    content += f"（预估 {t['estimated_minutes']} 分钟）"
                if t.get("source_type"):
                    content += f" | 关联: {t['source_type']}#{t.get('source_id', '')}"

                if self._notification_repo.check_exists_today(title=title):
                    continue

                self._notification_repo.create({
                    "ticket_id": None,
                    "reminder_id": None,
                    "title": title,
                    "content": content,
                    "read": 0,
                    "source_type": "todo",
                    "source_id": t["id"],
                })

                try:
                    source_info = ""
                    if t.get("source_type"):
                        source_info = f"{t['source_type']}#{t.get('source_id', '')}"
                    self._get_wecom_bot().push_todo_reminder(
                        title=t["title"],
                        description=t.get("description", ""),
                        estimated_minutes=t.get("estimated_minutes"),
                        source_info=source_info,
                    )
                except Exception as e:
                    logger.warning(f"企业微信推送待办提醒失败: {e}")

            return reminders
        except Exception as e:
            logger.warning(f"待办提醒检查失败: {e}")
            return []

    def check_maintenance_plans_cycle(self) -> Dict:
        plans = self._check_maintenance_plans() or []
        equipment = self._check_equipment_maintenance() or []
        return {"plans": plans, "equipment": equipment}

    def _check_maintenance_plans(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            plans = self._finance_repo.get_due_maintenance_plans(today) if self._finance_repo else []
            if not plans:
                return

            ts = self._get_ticket_svc()

            for plan in plans:
                client = plan.get("client") or plan.get("agreement_client", "")
                if not client:
                    continue

                try:
                    title = f"定期维保 - {plan.get('plan_name', plan.get('plan_type', '巡检'))}"
                    ticket = ts.create_ticket(
                        title=title,
                        client=client,
                        service_type="保养",
                        description=f"自动生成的定期维保工单（计划ID: {plan['id']}）",
                        priority="M",
                    )
                    ticket_id = ticket.get("id") if isinstance(ticket, dict) else None

                    if ticket_id and self._finance_repo:
                        self._finance_repo.record_inspection(
                            plan["id"], ticket_id, today, '待执行',
                            f"自动创建工单 {ticket.get('ticket_no', '')}")

                    next_date = self._calc_next_maintenance(plan.get("frequency", ""), today)
                    if next_date:
                        if self._event_bus:
                            from domain.events import InspectionPlanExecuted
                            self._event_bus.dispatch(InspectionPlanExecuted(
                                plan_id=plan["id"], next_execution=next_date))
                        elif self._finance_repo:
                            self._finance_repo.update_inspection_plan_next_execution(
                                plan["id"], next_date)

                    logger.info(f"自动生成维保工单: {title} for {client}")

                    try:
                        ticket_no = ticket.get("ticket_no", "") if isinstance(ticket, dict) else ""
                        plan_name = plan.get("plan_name") or plan.get("plan_type", "维保")
                        msg = (f"**{client}** 的定期维保计划 **「{plan_name}」** 今日到期，"
                               f"已自动生成工单 **{ticket_no}**")
                        self._get_wecom_bot().send_markdown(
                            self._get_wecom_bot().build_markdown(
                                "🔧 维保工单自动生成",
                                msg,
                                ticket_no=ticket_no,
                                client=client,
                                extra_lines=[f"维保计划: **{plan_name}**",
                                            f"下次执行: **{next_date or '待计算'}**"],
                            )
                        )
                    except Exception as e:
                        logger.warning(f"企业微信推送维保工单失败: {e}")

                except Exception as e:
                    logger.warning(f"维保工单生成失败 (plan_id={plan['id']}): {e}")
        except Exception as e:
            logger.warning(f"维保计划检查异常: {e}")

    def _check_equipment_maintenance(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            equip_svc = self._get_equipment_svc()
            due = equip_svc.get_overdue_maintenance(0) if equip_svc else []
            if not due:
                return

            ts = self._get_ticket_svc()

            for e in due:
                client = e.get("client", "")
                equip_name = e.get("name", "")
                model = e.get("model", "")
                contact = e.get("contact", "")

                title = f"设备维护到期 - {client}"
                content = (f"{client} 的 {equip_name}（{model or ''}）"
                          f"今日维护到期，请安排维护。")

                if self._notification_repo.check_exists_today(title=title):
                    continue

                self._notification_repo.create({
                    "ticket_id": None,
                    "title": title,
                    "content": content,
                    "read": 0,
                    "source_type": "equipment_maintenance",
                    "source_id": e["id"],
                })

                try:
                    ticket = ts.create_ticket(
                        title=f"定期维护 - {equip_name}",
                        client=client,
                        contact=contact or "",
                        service_type="保养",
                        description=f"设备 {equip_name}（{model or ''}）定期维护到期，请安排维护。",
                        priority="M",
                    )
                    ticket_id = ticket.get("id") if isinstance(ticket, dict) else None
                    if ticket_id:
                        ts.link_equipment(ticket_id, e["id"])
                        logger.info(f"自动生成设备维保工单: {equip_name} for {client}")

                        try:
                            msg = (f"**{client}** 的设备 **{equip_name}** 维保今日到期，"
                                   f"已自动生成工单 **{ticket.get('ticket_no','')}**")
                            self._get_wecom_bot().send_markdown(
                                self._get_wecom_bot().build_markdown("🔧 设备维保到期", msg,
                                    extra_lines=[f"设备型号: **{model or '-'}**"]),
                            )
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(f"自动生成维保工单失败 ({equip_name}): {e}")

                cycle = e.get("maintenance_cycle", "")
                next_date = self._calc_next_maintenance(cycle, today) if cycle else ""
                if next_date:
                    if self._event_bus:
                        from domain.events import EquipmentMaintenanceDue
                        self._event_bus.dispatch(EquipmentMaintenanceDue(
                            equipment_id=e["id"], next_maintenance=next_date))
                    else:
                        try:
                            equip_svc.update_equipment(e["id"], next_maintenance=next_date)
                        except Exception:
                            pass

        except Exception as ex:
            logger.warning(f"设备维保到期检查异常: {ex}")

    def _calc_next_maintenance(self, frequency: str, from_date: str) -> str:
        from datetime import datetime as _dt, timedelta as _td
        try:
            d = _dt.strptime(from_date, "%Y-%m-%d")
            freq = (frequency or "").lower()
            if "月" in freq or "month" in freq:
                match = re.search(r"(\d+)", freq)
                months = int(match.group(1)) if match else 1
                month = d.month + months
                year = d.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                try:
                    next_d = d.replace(year=year, month=month)
                except ValueError:
                    last = calendar.monthrange(year, month)[1]
                    next_d = d.replace(year=year, month=month, day=last)
                return next_d.strftime("%Y-%m-%d")
            elif "周" in freq or "week" in freq:
                match = re.search(r"(\d+)", freq)
                weeks = int(match.group(1)) if match else 1
                return (d + _td(weeks=weeks)).strftime("%Y-%m-%d")
            elif "季" in freq or "quarter" in freq:
                return (d + _td(days=90)).strftime("%Y-%m-%d")
            else:
                return (d + _td(days=30)).strftime("%Y-%m-%d")
        except Exception:
            return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    @property
    def scheduler_running(self) -> bool:
        return False

    def start_scheduler(self):
        logger.warning(
            "ReminderService.start_scheduler() 是旧版方法。"
            "新版通过 RQ 任务队列管理调度，请使用 tasks/reminder_tasks.py"
        )

    def stop_scheduler(self):
        pass
