"""
博通 — 供应商 API v1
"""

import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_suppliers = Blueprint('api_v1_suppliers', __name__, url_prefix='/api/v1/suppliers')


@bp_suppliers.route("/", strict_slashes=False)
def list_suppliers():
    """获取供应商列表"""
    svc = inject_service("supplier_service")
    items = svc.list_suppliers()
    return jsonify({"suppliers": items})


@bp_suppliers.route("/", methods=["POST"], strict_slashes=False)
def create_supplier():
    """创建供应商"""
    svc = inject_service("supplier_service")
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "请提供供应商名称"}), 400
    try:
        result = svc.create_supplier(data)
        return jsonify({"message": result["message"]}), 201
    except Exception as e:
        return jsonify({"error": f"创建供应商失败: {str(e)}"}), 400


@bp_suppliers.route("/<int:sup_id>")
def get_supplier(sup_id: int):
    """获取供应商详情"""
    svc = inject_service("supplier_service")
    sup = svc.get_supplier(sup_id)
    if not sup:
        return jsonify({"error": "供应商不存在"}), 404
    return jsonify(sup)


@bp_suppliers.route("/<int:sup_id>", methods=["PUT"])
def update_supplier(sup_id: int):
    """更新供应商"""
    svc = inject_service("supplier_service")
    data = request.get_json() or {}
    result = svc.update_supplier(sup_id, **data)
    if "error" in result:
        return jsonify({"error": result["error"]}), 400
    return jsonify({"message": result["message"]})


@bp_suppliers.route("/<int:sup_id>", methods=["DELETE"])
def delete_supplier(sup_id: int):
    """删除供应商"""
    svc = inject_service("supplier_service")
    result = svc.delete_supplier(sup_id)
    return jsonify({"message": result["message"]})


@bp_suppliers.route("/stats")
def supplier_stats():
    svc = inject_service("supplier_service")
    return jsonify(svc.get_supplier_performance_summary())


def register_blueprint(app):
    app.register_blueprint(bp_suppliers)
    logger.info("API v1 供应商端点已注册")
