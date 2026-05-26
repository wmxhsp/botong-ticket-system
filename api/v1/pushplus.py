"""
捷修 — PushPlus 推送配置 API v1
"""

import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_locator import reg

logger = logging.getLogger(__name__)

bp_pushplus = Blueprint('api_v1_pushplus', __name__, url_prefix='/api/v1/pushplus')


@bp_pushplus.route("/config")
def get_config():
    """获取 PushPlus 配置"""
    return jsonify(reg.pushplus_bot.get_config())


@bp_pushplus.route("/config", methods=["POST"])
def update_config():
    """更新 PushPlus 配置"""
    data = request.get_json(force=True, silent=True) or {}
    if reg.pushplus_bot.update_config(
        token=data.get("token"),
        enabled=data.get("enabled"),
        push_events=data.get("push_events"),
        time_window=data.get("time_window"),
    ):
        return jsonify({"message": "配置已保存", "config": reg.pushplus_bot.get_config()})
    else:
        return jsonify({"error": "保存配置失败"}), 500


@bp_pushplus.route("/test", methods=["POST"])
def send_test():
    """发送测试消息"""
    result = reg.pushplus_bot.send_test()
    if result.get("ok"):
        return jsonify({"message": "测试消息发送成功，请查看 PushPlus 公众号"})
    else:
        return jsonify({"error": result.get("error", "发送失败")}), 400


def register_blueprint(app):
    app.register_blueprint(bp_pushplus)
    logger.info("API v1 PushPlus端点已注册")
