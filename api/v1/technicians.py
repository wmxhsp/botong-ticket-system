"""
博通 — 服务人员 API v1
"""

import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_technicians = Blueprint('api_v1_technicians', __name__, url_prefix='/api/v1/technicians')


@bp_technicians.route("/", strict_slashes=False)
def list_technicians():
    """获取服务人员列表"""
    svc = inject_service("technician_service")
    try:
        items = svc.list_technicians()
    except Exception:
        items = []
    return jsonify({"technicians": items})


@bp_technicians.route("/", methods=["POST"], strict_slashes=False)
def create_technician():
    """创建服务人员"""
    svc = inject_service("technician_service")
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "请提供人员名称"}), 400
    result = svc.create_technician(data)
    return jsonify({"message": result["message"]}), 201


@bp_technicians.route("/summary")
def technician_summary():
    """服务人员汇总"""
    svc = inject_service("technician_service")
    return jsonify(svc.get_summary())


@bp_technicians.route("/stats")
def technician_stats():
    """服务人员详细统计"""
    svc = inject_service("technician_service")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    return jsonify(svc.get_stats(date_from, date_to))


@bp_technicians.route("/profit-ranking")
def profit_ranking():
    """技术人员利润贡献排行"""
    svc = inject_service("technician_service")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    return jsonify(svc.get_profit_ranking(date_from, date_to))


@bp_technicians.route("/<int:tech_id>")
def get_technician(tech_id: int):
    """获取服务人员详情"""
    svc = inject_service("technician_service")
    try:
        tech = svc.get_technician(tech_id)
        return jsonify(tech)
    except Exception:
        return jsonify({"error": "服务人员不存在"}), 404


@bp_technicians.route("/<int:tech_id>", methods=["PUT"])
def update_technician(tech_id: int):
    """更新服务人员"""
    svc = inject_service("technician_service")
    data = request.get_json() or {}
    svc.update_technician(tech_id, **data)
    return jsonify({"message": "已更新"})


@bp_technicians.route("/<int:tech_id>", methods=["DELETE"])
def delete_technician(tech_id: int):
    """删除服务人员"""
    svc = inject_service("technician_service")
    svc.delete_technician(tech_id)
    return jsonify({"message": "已删除"})


@bp_technicians.route("/<int:tech_id>/tickets")
def technician_tickets(tech_id: int):
    """获取工程师参与工单"""
    svc = inject_service("technician_service")
    try:
        tech = svc.get_technician(tech_id)
    except Exception:
        return jsonify({"error": "服务人员不存在"}), 404
    name = tech["name"]
    result = svc.get_technician_tickets(name)
    return jsonify({
        "technician_name": name,
        "tickets": result["tickets"],
        "total_tickets": result["total_tickets"],
    })


def register_blueprint(app):
    app.register_blueprint(bp_technicians)
    logger.info("API v1 服务人员端点已注册")
