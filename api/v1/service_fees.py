"""
博通 — 服务项目 API v1
"""

import logging
from flask import Blueprint, request, jsonify

from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_service_fees = Blueprint('api_v1_service_fees', __name__, url_prefix='/api/v1/service-fees')


@bp_service_fees.route("/", strict_slashes=False)
def list_fees():
    """获取服务项目列表"""
    svc = inject_service("service_fee_service")
    fees = svc.list_fees()
    return jsonify({"fees": fees})


@bp_service_fees.route("/", methods=["POST"], strict_slashes=False)
def create_fee():
    """创建服务项目"""
    svc = inject_service("service_fee_service")
    data = request.get_json() or {}
    if not data.get("name") or data.get("unit_price") is None:
        return jsonify({"error": "请提供名称和价格"}), 400
    try:
        result = svc.create_fee(data)
        return jsonify({"message": result["message"]}), 201
    except Exception as e:
        return jsonify({"error": f"创建服务项目失败: {str(e)}"}), 400


@bp_service_fees.route("/<int:fee_id>", methods=["PUT"])
def update_fee(fee_id: int):
    """更新服务项目"""
    svc = inject_service("service_fee_service")
    data = request.get_json() or {}
    result = svc.update_fee(fee_id, **data)
    if "error" in result:
        return jsonify({"error": result["error"]}), 400
    return jsonify({"message": result["message"]})


@bp_service_fees.route("/<int:fee_id>", methods=["DELETE"])
def delete_fee(fee_id: int):
    """删除服务项目"""
    svc = inject_service("service_fee_service")
    result = svc.delete_fee(fee_id)
    return jsonify({"message": result["message"]})


@bp_service_fees.route("/types")
def fee_types():
    """获取计价类型列表"""
    return jsonify({"types": [
        {"key": "hourly", "name": "按小时", "unit": "元/h"},
        {"key": "monthly", "name": "按月", "unit": "元/月"},
        {"key": "yearly", "name": "按年", "unit": "元/年"},
        {"key": "fixed", "name": "按次", "unit": "元/次"},
        {"key": "free", "name": "保修免费", "unit": "免费"},
    ]})


def register_blueprint(app):
    app.register_blueprint(bp_service_fees)
    logger.info("API v1 服务项目端点已注册")
