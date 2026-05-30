"""
博通 (Botong) — 客户 API v1 新版端点
兼容旧 Namespace 返回格式，支持逐步废弃旧路由。
"""

import logging
from flask import Blueprint, request, jsonify

from infrastructure.di.service_injection import inject_service
from domain.exceptions import ClientNotFoundError
from api.validators import validate_json
from api.validators.schemas import ClientCreateSchema, ClientUpdateSchema
from api.v1.responses import ApiResponse

logger = logging.getLogger(__name__)

bp_clients = Blueprint('api_v1_clients', __name__, url_prefix='/api/v1/clients')


def _get_client_service():
    return inject_service("client_service")


@bp_clients.route("/", strict_slashes=False)
def list_clients():
    try:
        svc = _get_client_service()
        if svc is None:
            return ApiResponse.server_error("服务未初始化")

        keyword = request.args.get("q")
        with_profile = request.args.get("with_profile", "0") == "1"
        result = svc.list_with_summary(keyword=keyword, with_profile=with_profile)
        return ApiResponse.success(result)
    except Exception as e:
        logger.error(f"list_clients error: {e}", exc_info=True)
        return ApiResponse.server_error("服务器内部错误")


@bp_clients.route("/<path:client_name>")
def get_client(client_name: str):
    """获取客户详情（兼容旧 Namespace 格式）"""
    try:
        svc = _get_client_service()
        if svc is None:
            return ApiResponse.server_error("服务未初始化")

        client = svc.get_client(client_name)
        return ApiResponse.success(client)
    except ClientNotFoundError as e:
        return ApiResponse.not_found(str(e))
    except Exception as e:
        logger.error(f"get_client error: {e}", exc_info=True)
        return ApiResponse.server_error("服务器内部错误")


@bp_clients.route("/<path:client_name>/profile")
def client_profile(client_name: str):
    """获取客户完整画像（含征信评分、级别、统计）"""
    try:
        svc = _get_client_service()
        if svc is None:
            return ApiResponse.server_error("服务未初始化")

        profile = svc.get_client_profile(client_name)
        return ApiResponse.success(profile)
    except ClientNotFoundError as e:
        return ApiResponse.not_found(str(e))
    except Exception as e:
        logger.error(f"client_profile error: {e}", exc_info=True)
        return ApiResponse.server_error("服务器内部错误")


@bp_clients.route("/<path:client_name>/overview")
def client_overview(client_name: str):
    """获取客户概览（基本信息+最近工单+设备列表+财务汇总）"""
    try:
        svc = _get_client_service()
        if svc is None:
            return ApiResponse.server_error("服务未初始化")

        overview = svc.get_client_overview(client_name)

        client = overview.get("client", {})
        tickets = overview.get("tickets", [])
        equipment = overview.get("equipment", [])
        income = overview.get("income", [])

        total_income = sum(float(r.get("amount", 0) or 0) for r in income)
        unpaid = sum(
            float(r.get("amount", 0) or 0)
            for r in income
            if r.get("status") != "已收款" and r.get("status") != "paid"
        )

        return ApiResponse.success({
            "client": client,
            "recent_tickets": tickets[:5],
            "equipment": equipment,
            "finance_summary": {
                "total_income": round(total_income, 2),
                "unpaid": round(unpaid, 2),
                "income_count": len(income),
            },
        })
    except ClientNotFoundError as e:
        return ApiResponse.not_found(str(e))
    except RuntimeError as e:
        logger.error(f"client_overview error: {e}", exc_info=True)
        return ApiResponse.server_error(str(e))
    except Exception as e:
        logger.error(f"client_overview error: {e}", exc_info=True)
        return ApiResponse.server_error("服务器内部错误")


@bp_clients.route("/tier-config")
def tier_config():
    """获取客户级别配置"""
    try:
        svc = _get_client_service()
        if svc is None:
            return ApiResponse.server_error("服务未初始化")

        config = svc.get_tier_config()
        return ApiResponse.success(config)
    except Exception as e:
        logger.error(f"tier_config error: {e}", exc_info=True)
        return ApiResponse.server_error("服务器内部错误")


@bp_clients.route("/", methods=["POST"], strict_slashes=False)
@validate_json(ClientCreateSchema)
def create_client(body: ClientCreateSchema):
    """创建客户（兼容旧 Namespace 格式）"""
    try:
        svc = _get_client_service()
        if svc is None:
            return ApiResponse.server_error("服务未初始化")

        result = svc.create_client(
            name=body.name,
            contact=body.contact or "",
            phone=body.phone or "",
            notes=body.notes or "",
        )
        summary = f"客户 {body.name} 已创建"
        return ApiResponse.created({"message": result.get("message", summary), "summary": summary})
    except ValueError as e:
        return ApiResponse.bad_request(str(e))
    except Exception as e:
        logger.error(f"create_client error: {e}", exc_info=True)
        return ApiResponse.server_error("服务器内部错误")


@bp_clients.route("/<path:client_name>", methods=["PUT"])
@validate_json(ClientUpdateSchema)
def update_client(client_name: str, body: ClientUpdateSchema):
    """更新客户"""
    try:
        svc = _get_client_service()
        if svc is None:
            return ApiResponse.server_error("服务未初始化")

        svc.update_client(client_name, **body.model_dump(exclude_none=True))
        return ApiResponse.success(message="客户已更新")
    except ClientNotFoundError as e:
        return ApiResponse.not_found(str(e))
    except Exception as e:
        logger.error(f"update_client error: {e}", exc_info=True)
        return ApiResponse.server_error("服务器内部错误")


@bp_clients.route("/<path:client_name>", methods=["DELETE"])
def delete_client(client_name: str):
    """删除客户"""
    try:
        svc = _get_client_service()
        if svc is None:
            return ApiResponse.server_error("服务未初始化")

        svc.delete_client(client_name)
        return ApiResponse.success(message=f"客户 {client_name} 已删除")
    except ClientNotFoundError as e:
        return ApiResponse.not_found(str(e))
    except ValueError as e:
        return ApiResponse.bad_request(str(e))
    except Exception as e:
        logger.error(f"delete_client error: {e}", exc_info=True)
        return ApiResponse.server_error("服务器内部错误")


def register_blueprint(app):
    """注册 Blueprint"""
    app.register_blueprint(bp_clients)
    logger.info("API v1 客户端点已注册")
