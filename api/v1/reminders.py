"""
博通 — 提醒通知 API v1
"""

import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_reminders = Blueprint('api_v1_reminders', __name__, url_prefix='/api/v1/reminders')




@bp_reminders.route("/pending")
def pending_notifications():
    """未读通知"""
    svc = inject_service("reminder_service")
    notes = svc.get_pending_notifications(limit=int(request.args.get("limit", 20)))
    return jsonify({"notifications": notes})


@bp_reminders.route("/all")
def all_notifications():
    """所有通知"""
    svc = inject_service("reminder_service")
    notes = svc.get_all_notifications(limit=int(request.args.get("limit", 50)))
    return jsonify({"notifications": notes})


@bp_reminders.route("/read/<int:note_id>", methods=["PUT"])
def mark_read(note_id: int):
    """标记已读"""
    svc = inject_service("reminder_service")
    svc.mark_notification_read(note_id)
    return jsonify({"message": "已标记为已读"})


@bp_reminders.route("/read-all", methods=["PUT"])
def mark_all_read():
    """全部标记已读"""
    svc = inject_service("reminder_service")
    svc.mark_all_read()
    return jsonify({"message": "全部已读"})


@bp_reminders.route("/ticket/<int:ticket_id>")
def ticket_reminders(ticket_id: int):
    """获取工单提醒"""
    svc = inject_service("reminder_service")
    reminders = svc.get_ticket_reminders(ticket_id)
    return jsonify({"reminders": reminders})


@bp_reminders.route("/ticket/<int:ticket_id>", methods=["POST"])
def create_ticket_reminder(ticket_id: int):
    """创建工单提醒"""
    svc = inject_service("reminder_service")
    data = request.get_json() or {}
    svc.create_reminder(
        ticket_id=ticket_id,
        appointment_at=data.get("appointment_at"),
        content=data.get("content", ""),
    )
    return jsonify({"message": "提醒已创建"}), 201


@bp_reminders.route("/ticket/<int:ticket_id>", methods=["DELETE"])
def delete_ticket_reminder(ticket_id: int):
    """取消工单提醒"""
    svc = inject_service("reminder_service")
    svc.cancel_reminder(ticket_id)
    return jsonify({"message": "提醒已取消"})


@bp_reminders.route("/count")
def unread_count():
    """未读通知数"""
    svc = inject_service("reminder_service")
    count = svc.get_unread_count()
    return jsonify({"count": count})


@bp_reminders.route("/subscription-expiry")
def subscription_expiry():
    """获取订阅到期提醒"""
    svc = inject_service("reminder_service")
    days = int(request.args.get("days", 30))
    items = svc.get_expiring_subscriptions(days)
    return jsonify({"items": items})


@bp_reminders.route("/subscription-expiry", methods=["POST"])
def trigger_subscription_check():
    """触发订阅到期检查"""
    svc = inject_service("reminder_service")
    result = svc.check_subscription_expiry()
    return jsonify({"message": "检查完成", "result": result})


def register_blueprint(app):
    app.register_blueprint(bp_reminders)
    logger.info("API v1 提醒端点已注册")
