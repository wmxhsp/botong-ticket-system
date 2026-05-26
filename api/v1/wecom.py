"""
博通 — 企业微信机器人配置 API v1
"""

import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_wecom = Blueprint('api_v1_wecom', __name__, url_prefix='/api/v1/wecom')


def _bot():
    return inject_service("wecom_bot")


@bp_wecom.route("/config")
def get_config():
    return jsonify(_bot().get_config())


@bp_wecom.route("/config", methods=["POST"])
def update_config():
    data = request.get_json(force=True, silent=True) or {}
    if _bot().update_config(
        webhook_url=data.get("webhook_url"),
        enabled=data.get("enabled"),
        push_events=data.get("push_events"),
        time_window=data.get("time_window"),
    ):
        return jsonify({"message": "配置已保存", "config": _bot().get_config()})
    else:
        validation_error = _bot().last_validation_error
        if validation_error:
            return jsonify({"error": f"保存配置失败: {validation_error}"}), 400
        return jsonify({"error": "保存配置失败"}), 500


@bp_wecom.route("/test", methods=["POST"])
def send_test():
    result = _bot().send_test()
    if result.get("ok"):
        return jsonify({"message": "测试消息发送成功，请查看企业微信群机器人"})
    else:
        return jsonify({"error": result.get("error", "发送失败")}), 400


def register_blueprint(app):
    app.register_blueprint(bp_wecom)
    logger.info("API v1 企业微信端点已注册")
