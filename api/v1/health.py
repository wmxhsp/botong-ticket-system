"""
博通 (Botong) — 健康检查和系统诊断端点
"""

import time
import logging
import os
from pathlib import Path
from flask import Blueprint, jsonify, request

from api.v1.responses import ApiResponse

logger = logging.getLogger(__name__)

bp_health = Blueprint('api_v1_health', __name__, url_prefix='/api/v1')

# 启动时间
_START_TIME = time.time()


@bp_health.route("/health")
def health_check():
    """系统健康检查"""
    checks = {
        "status": "healthy",
        "uptime": round(time.time() - _START_TIME, 1),
        "version": "3.0.0",
        "system": "博通 (Botong) 售后管理系统",
        "checks": {},
    }

    try:
        import psutil
        mem = psutil.virtual_memory()
        checks["checks"]["memory"] = {
            "healthy": mem.percent < 90,
            "used_percent": mem.percent,
            "used_mb": round(mem.used / 1024 / 1024),
            "total_mb": round(mem.total / 1024 / 1024),
        }
        if mem.percent >= 90:
            checks["status"] = "degraded"
    except ImportError:
        pass

    # 数据库检查
    try:
        from infrastructure.di.service_injection import inject_service
        ts = inject_service("ticket_service")
        if ts:
            ticket_count = ts.count_tickets()
            checks["checks"]["database"] = {
                "healthy": True,
                "ticket_count": ticket_count,
            }
        else:
            checks["checks"]["database"] = {
                "healthy": True,
                "ticket_count": 0,
            }
    except Exception as e:
        checks["checks"]["database"] = {"healthy": False, "error": str(e)}
        checks["status"] = "degraded"

    # 缓存检查
    try:
        from infrastructure.di.service_injection import inject_service
        if inject_service("cache"):
            checks["checks"]["cache"] = {"healthy": True, "type": "enabled"}
        else:
            checks["checks"]["cache"] = {"healthy": True, "type": "disabled"}
    except Exception as e:
        checks["checks"]["cache"] = {"healthy": False, "error": str(e)}
        checks["status"] = "degraded"

    # DI 容器检查
    try:
        from infrastructure.di.container import Container
        di_services = []
        for name in ["ticket_service", "ticket_repo"]:
            if Container.has(name):
                di_services.append(name)
        checks["checks"]["di_container"] = {
            "healthy": True,
            "services": di_services,
        }
    except Exception:
        checks["checks"]["di_container"] = {"healthy": True, "type": "not_initialized"}

    status_code = 200 if checks["status"] == "healthy" else 503
    return jsonify(checks), status_code


@bp_health.route("/system/maintenance", methods=["GET", "POST"])
def run_maintenance():
    """执行数据库维护（VACUUM + REINDEX + ANALYZE）"""
    try:
        from infrastructure.persistence.maintenance import get_maintenance
        maint = get_maintenance()
        action = request.args.get("action", "full")
        
        actions = {
            "vacuum": maint.vacuum,
            "reindex": maint.reindex,
            "analyze": maint.analyze,
            "wal": maint.wal_checkpoint,
            "full": maint.full_maintenance,
        }
        
        func = actions.get(action)
        if not func:
            return ApiResponse.bad_request(f"未知操作: {action}")
        
        result = func()
        return ApiResponse.success(result, message=f"维护操作 '{action}' 完成")
    except Exception as e:
        logger.error(f"maintenance error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_health.route("/system/maintenance/status")
def maintenance_status():
    """数据库维护状态"""
    try:
        from infrastructure.persistence.maintenance import get_maintenance
        maint = get_maintenance()
        size = maint.get_db_size()
        pragma = maint.get_pragma_info()

        return ApiResponse.success({
            "db_size_mb": size.get("total_mb", 0),
            "db_size_kb": size.get("total_kb", 0),
            "wal_size_kb": size.get(f"{Path(__file__).stem}-wal", 0),
            "page_count": pragma["page_count"],
            "page_size": pragma["page_size"],
            "journal_mode": pragma["journal_mode"],
            "last_maintenance": None,
        })
    except Exception as e:
        return ApiResponse.server_error(str(e))

@bp_health.route("/system/status")
def system_status():
    """系统运行状态"""
    info = {
        "system": "博通 (Botong) 售后管理系统",
        "version": "3.0.0",
        "uptime": round(time.time() - _START_TIME),
        "architecture": {
            "di_container": _check_di(),
            "event_bus": _check_event_bus(),
            "new_services": _check_new_services(),
        },
    }

    try:
        from infrastructure.di.service_injection import inject_service
        ts = inject_service("ticket_service")
        if ts:
            all_tickets = ts.count_tickets()
            info["total_tickets"] = all_tickets
            by_status = {}
            for st in ["open", "in_progress", "waiting", "closed"]:
                cnt = ts.count_tickets(status=st)
                if cnt > 0:
                    by_status[st] = cnt
            info["ticket_stats"] = by_status

        cs = inject_service("client_service")
        if cs and hasattr(cs, 'count_clients'):
            info["total_clients"] = cs.count_clients()
        elif cs and hasattr(cs, 'list_clients'):
            info["total_clients"] = len(cs.list_clients(limit=999999).get("clients", []))

        import os
        db_path = os.environ.get(
            "TICKETS_DB_PATH",
            os.path.join(os.path.dirname(__file__), "../../tickets.db"))
        if os.path.exists(db_path):
            info["db_size_mb"] = round(os.path.getsize(db_path) / 1024 / 1024, 2)
    except Exception as e:
        info["db_error"] = str(e)

    return jsonify(info)


def _check_di() -> dict:
    try:
        from infrastructure.di.container import Container
        return {
            "initialized": Container.has("ticket_service"),
            "registered": list(Container._factories.keys()) if hasattr(Container, '_factories') else [],
        }
    except Exception:
        return {"initialized": False}


def _check_event_bus() -> dict:
    try:
        from domain.events import get_event_bus
        bus = get_event_bus()
        handlers = sum(len(v) for v in bus._handlers.values()) if hasattr(bus, '_handlers') else 0
        return {"initialized": True, "event_types": len(bus._handlers) if hasattr(bus, '_handlers') else 0}
    except Exception:
        return {"initialized": False}


def _check_new_services() -> list:
    services = []
    try:
        from infrastructure.di.container import Container
        if Container.has("ticket_service"):
            services.append("tickets")
        if Container.has("client_service"):
            services.append("clients")
    except Exception:
        pass
    return services


def register_blueprint(app):
    """注册 Blueprint"""
    app.register_blueprint(bp_health)
    logger.info("API v1 健康检查端点已注册")
