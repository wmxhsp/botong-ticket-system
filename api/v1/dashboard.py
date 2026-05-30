import logging
from flask import Blueprint, request, jsonify

from infrastructure.di.service_injection import inject_service
from api.v1.responses import ApiResponse

logger = logging.getLogger(__name__)

bp_dashboard = Blueprint('api_v1_dashboard', __name__, url_prefix='/api/v1/dashboard')



@bp_dashboard.route("/summary")
def dashboard_summary():
    svc = inject_service("dashboard_service")
    equip_svc = inject_service("equipment_service")
    ticket_svc = inject_service("ticket_service")
    inventory_svc = inject_service("inventory_service")

    try:
        if svc:
            month = request.args.get("month")
            result = svc.get_summary(month=month)

            result["alerts"] = []
            if hasattr(inventory_svc, "check_alerts"):
                result["alerts"] = inventory_svc.check_alerts()[:5]
            result["warranty"] = equip_svc.get_warranty_summary() if hasattr(equip_svc, "get_warranty_summary") else {}
            result["maintenance"] = equip_svc.get_maintenance_summary() if hasattr(equip_svc, "get_maintenance_summary") else {}

            result["equip_stats"] = svc.build_equip_stats()

            result["sales_today"] = {"total": 0}
            result["all_statuses"] = ticket_svc.STATUS_NAMES

            result["recommendations"] = svc.build_recommendations()

            return ApiResponse.success(result)

        return ApiResponse.success(svc.build_legacy_dashboard(
            month=request.args.get("month")))

    except Exception as e:
        logger.warning(f"Dashboard summary failed, falling back to legacy: {e}")
        try:
            return ApiResponse.success(svc.build_legacy_dashboard(
                month=request.args.get("month")))
        except Exception as e2:
            return ApiResponse.server_error(f"仪表盘获取失败: {str(e2)}")


@bp_dashboard.route("/today")
def dashboard_today():
    try:
        svc = inject_service("dashboard_service")
        if svc is None:
            return ApiResponse.error("服务未初始化", 500)
        result = svc.get_today_stats()
        return ApiResponse.success(result)
    except Exception as e:
        logger.error(f"dashboard_today error: {e}", exc_info=True)
        return ApiResponse.server_error(f"获取今日统计失败: {str(e)}")


def register_blueprint(app):
    app.register_blueprint(bp_dashboard)
    logger.info("API v1 仪表盘端点已注册")
