"""
博通 — 统计分析 API v1
"""

import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_stats = Blueprint('api_v1_stats', __name__, url_prefix='/api/v1/stats')


@bp_stats.route("/")
def stats_summary():
    """获取统计数据"""
    svc = inject_service("stats_service")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    overview = svc.get_overview(date_from, date_to)
    monthly_income = svc.get_monthly_income_trend()
    client_ranking = svc.get_client_ranking(date_from, date_to)

    # 设备统计
    equip_stats = {}
    try:
        equip_svc = inject_service("equipment_service")
        if equip_svc and hasattr(equip_svc, 'get_equipment_stats'):
            equip_stats = equip_svc.get_equipment_stats()
    except Exception:
        equip_stats = {}

    return jsonify({
        "overview": overview,
        "status_distribution": overview["status_distribution"],
        "monthly_tickets": overview["monthly_tickets"],
        "monthly_income": monthly_income,
        "client_ranking": client_ranking,
        "equipment": equip_stats,
    })


def register_blueprint(app):
    app.register_blueprint(bp_stats)
    logger.info("API v1 统计端点已注册")
