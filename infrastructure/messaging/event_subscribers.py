"""
博通 (Botong) — 领域事件订阅注册
将事件处理器注册到事件总线，连接现有 service 层
"""

import logging
from domain.events import (
    EventBus, TicketCreated, TicketStatusChanged, TicketCompleted,
    TicketPaymentConfirmed, TicketDeleted, TodoDue, IncomeRecorded,
    TicketCostSyncRequired, TicketSettled, TicketTaxUpdated,
    ClientCreditFrozen, EquipmentMaintenanceDue, InspectionPlanExecuted,
)

logger = logging.getLogger(__name__)


def register_all_subscribers(event_bus: EventBus, services: dict):
    """
    注册所有事件订阅

    Args:
        event_bus: 事件总线实例
        services: 服务字典（从 DI 容器获取）
            - todo_svc: TodoService
            - reminder_svc: ReminderService
            - wecom_bot: WeComBotClient (可选)
            - pushplus_bot: PushPlusClient (可选)
            - ticket_svc: TicketService (可选)
            - client_svc: ClientService (可选)
            - equipment_svc: EquipmentService (可选)
            - finance_repo: SqliteFinanceRepository (可选)
    """
    todo_svc = services.get("todo_svc")
    reminder_svc = services.get("reminder_svc")
    wecom_bot = services.get("wecom_bot")
    pushplus_bot = services.get("pushplus_bot")
    ticket_svc = services.get("ticket_svc")
    client_svc = services.get("client_svc")
    equipment_svc = services.get("equipment_svc")
    finance_repo = services.get("finance_repo")

    # ─── 工单创建 → 创建待办 + 通知 ───
    if todo_svc:
        @event_bus.register("ticket.created")
        def _on_ticket_created(event: TicketCreated):
            try:
                todo_svc.create_from_ticket(
                    ticket_id=event.ticket_id,
                    todo_type="process",
                    title=f"处理工单 - {event.ticket_no} ({event.client})",
                )
                logger.info(f"Event: ticket.created → todo created for #{event.ticket_id}")
            except Exception as e:
                logger.error(f"Failed to create todo for ticket #{event.ticket_id}: {e}")

    # ─── 工单状态变更 → 对应待办 + 推送 ───
    if todo_svc:
        @event_bus.register("ticket.status_changed")
        def _on_ticket_status_changed(event: TicketStatusChanged):
            todo_map = {
                "in-progress": ("follow_up", "跟进工单"),
                "pending-parts": ("purchase_parts", "采购配件"),
                "pending-payment": ("confirm_payment", "确认收款"),
                "closed": ("follow_up_visit", "工单回访"),
            }
            entry = todo_map.get(event.new_status)
            if entry:
                todo_type, title_prefix = entry
                try:
                    todo_svc.create_from_ticket(
                        ticket_id=event.ticket_id,
                        todo_type=todo_type,
                        title=f"{title_prefix} - {event.ticket_no} ({event.client})",
                    )
                except Exception as e:
                    logger.error(f"Failed to create {todo_type} todo: {e}")

    if wecom_bot:
        @event_bus.register("ticket.status_changed")
        def _on_ticket_status_changed_wecom(event: TicketStatusChanged):
            try:
                wecom_bot.push_status_change(event)
            except Exception as e:
                logger.error(f"WeCom status change push failed: {e}")

    if pushplus_bot:
        @event_bus.register("ticket.status_changed")
        def _on_ticket_status_changed_pushplus(event: TicketStatusChanged):
            try:
                pushplus_bot.send_markdown(
                    "🔄 工单状态变更",
                    f"工单 **{event.ticket_no}** 状态从 **{event.old_status}** 变更为 **{event.new_status}**",
                    ticket_no=event.ticket_no,
                    client=event.client,
                )
            except Exception as e:
                logger.error(f"PushPlus status change push failed: {e}")

    # ─── 工单收款确认 → 推送通知 ───
    if wecom_bot:
        @event_bus.register("ticket.payment_confirmed")
        def _on_payment_confirmed_wecom(event: TicketPaymentConfirmed):
            try:
                msg = f"工单收款 #{event.ticket_id}: ¥{event.amount:.2f} ({event.method})"
                wecom_bot.send_markdown(f"### 收款通知\n{msg}")
            except Exception as e:
                logger.error(f"WeCom push failed: {e}")

    if pushplus_bot:
        @event_bus.register("ticket.payment_confirmed")
        def _on_payment_confirmed_pushplus(event: TicketPaymentConfirmed):
            try:
                msg = f"工单收款 #{event.ticket_id}: ¥{event.amount:.2f} ({event.method})"
                pushplus_bot.send_message(msg, title="💰 收款通知")
            except Exception as e:
                logger.error(f"PushPlus push failed: {e}")

    # ─── 工单完成 → 推送通知 + 自动结算 ───
    if wecom_bot:
        @event_bus.register("ticket.completed")
        def _on_ticket_completed_wecom(event: TicketCompleted):
            try:
                wecom_bot.send_markdown(
                    f"### ✅ 工单完成\n"
                    f"工单 **{event.ticket_no}** 已完成\n"
                    f"客户: {event.client}\n"
                    f"总金额: ¥{event.total:.2f}"
                )
            except Exception as e:
                logger.error(f"WeCom completed push failed: {e}")

    if pushplus_bot:
        @event_bus.register("ticket.completed")
        def _on_ticket_completed_pushplus(event: TicketCompleted):
            try:
                pushplus_bot.send_markdown(
                    "✅ 工单完成",
                    f"工单 **{event.ticket_no}** 已完成",
                    ticket_no=event.ticket_no,
                    client=event.client,
                    amount=event.total,
                )
            except Exception as e:
                logger.error(f"PushPlus completed push failed: {e}")

    if ticket_svc:
        @event_bus.register("ticket.completed")
        def _on_ticket_completed_settle(event: TicketCompleted):
            try:
                ticket_svc.update_ticket_billing(
                    event.ticket_id,
                    billing_status="completed",
                )
                logger.info(f"Event: ticket.completed → billing set to completed for #{event.ticket_id}")
            except Exception as e:
                logger.error(f"Failed to set billing completed for #{event.ticket_id}: {e}")

    # ─── 工单成本同步 → TicketService 处理 ───
    if ticket_svc:
        @event_bus.register("ticket.cost_sync_required")
        def _on_ticket_cost_sync(event: TicketCostSyncRequired):
            try:
                ticket_svc.sync_ticket_cost(event.ticket_id)
                logger.info(f"Event: ticket.cost_sync_required → synced for #{event.ticket_id}")
            except Exception as e:
                logger.error(f"Failed to sync ticket cost for #{event.ticket_id}: {e}")

    # ─── 工单结算 → 更新 billing_status ───
    if ticket_svc:
        @event_bus.register("ticket.settled")
        def _on_ticket_settled(event: TicketSettled):
            try:
                ticket_svc.update_ticket_billing(
                    event.ticket_id,
                    billing_status=event.billing_status,
                    closed_at=event.closed_at,
                )
                logger.info(f"Event: ticket.settled → billing updated for #{event.ticket_id}")
            except Exception as e:
                logger.error(f"Failed to settle ticket #{event.ticket_id}: {e}")

    # ─── 工单税务更新 → 更新 tax 字段 ───
    if ticket_svc:
        @event_bus.register("ticket.tax_updated")
        def _on_ticket_tax_updated(event: TicketTaxUpdated):
            try:
                ticket_svc.update_ticket_billing(
                    event.ticket_id,
                    tax_rate=event.tax_rate,
                    tax_amount=event.tax_amount,
                    billing_status=event.billing_status,
                )
                logger.info(f"Event: ticket.tax_updated → tax updated for #{event.ticket_id}")
            except Exception as e:
                logger.error(f"Failed to update ticket tax for #{event.ticket_id}: {e}")

    # ─── 客户信用冻结 → 更新客户备注 ───
    if client_svc:
        @event_bus.register("client.credit_frozen")
        def _on_client_credit_frozen(event: ClientCreditFrozen):
            try:
                client_svc.freeze_credit(event.client_name, event.reason)
                logger.info(f"Event: client.credit_frozen → {event.client_name}")
            except Exception as e:
                logger.error(f"Failed to freeze client credit: {e}")

    # ─── 设备维保到期 → 更新下次维护日期 ───
    if equipment_svc:
        @event_bus.register("equipment.maintenance_due")
        def _on_equipment_maintenance_due(event: EquipmentMaintenanceDue):
            try:
                equipment_svc.update_equipment(event.equipment_id, next_maintenance=event.next_maintenance)
                logger.info(f"Event: equipment.maintenance_due → equip#{event.equipment_id}")
            except Exception as e:
                logger.error(f"Failed to update equipment maintenance: {e}")

    # ─── 巡检计划执行 → 更新下次执行日期 ───
    if finance_repo:
        @event_bus.register("inspection_plan.executed")
        def _on_inspection_plan_executed(event: InspectionPlanExecuted):
            try:
                finance_repo.update_inspection_plan_next_execution(event.plan_id, event.next_execution)
                logger.info(f"Event: inspection_plan.executed → plan#{event.plan_id}")
            except Exception as e:
                logger.error(f"Failed to update inspection plan: {e}")

    logger.info(f"Event subscribers registered: {len(event_bus._handlers)} event types")
