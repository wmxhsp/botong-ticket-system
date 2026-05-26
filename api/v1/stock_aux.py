import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_stock_aux = Blueprint('api_v1_stock_aux', __name__, url_prefix='/api/v1/stock')


@bp_stock_aux.route("/locations")
def list_locations():
    try:
        inv_svc = inject_service("inventory_service")
        items = inv_svc.list_locations()
        return jsonify({"locations": items})
    except Exception as e:
        return jsonify({"error": f"获取库位列表失败: {str(e)}"}), 400


@bp_stock_aux.route("/locations", methods=["POST"])
def create_location():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "请提供库位名称"}), 400
    try:
        inv_svc = inject_service("inventory_service")
        inv_svc.create_location(name, description=data.get("description", ""),
                                sort_order=int(data.get("sort_order", 99)))
        return jsonify({"message": f"已添加库位 '{name}'"}), 201
    except Exception as e:
        if "已存在" in str(e):
            return jsonify({"error": str(e)}), 400
        return jsonify({"error": f"添加库位失败: {str(e)}"}), 400


@bp_stock_aux.route("/locations/<int:loc_id>", methods=["PUT"])
def update_location(loc_id: int):
    data = request.get_json() or {}
    inv_svc = inject_service("inventory_service")
    inv_svc.update_location(loc_id, data)
    return jsonify({"message": "已更新"})


@bp_stock_aux.route("/locations/<int:loc_id>", methods=["DELETE"])
def delete_location(loc_id: int):
    try:
        inv_svc = inject_service("inventory_service")
        name = inv_svc.delete_location(loc_id)
        return jsonify({"message": f"已删除库位 '{name}'"})
    except Exception as e:
        if "不存在" in str(e):
            return jsonify({"error": str(e)}), 404
        return jsonify({"error": f"删除库位失败: {str(e)}"}), 400


@bp_stock_aux.route("/warehouses")
def list_warehouses():
    try:
        inv_svc = inject_service("inventory_service")
        items = inv_svc.list_warehouses()
        return jsonify({"warehouses": items})
    except Exception as e:
        return jsonify({"error": f"获取仓库列表失败: {str(e)}"}), 400


@bp_stock_aux.route("/warehouses", methods=["POST"])
def create_warehouse():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "请提供仓库名称"}), 400
    try:
        inv_svc = inject_service("inventory_service")
        inv_svc.create_warehouse(name, address=data.get("address", ""),
                                  contact=data.get("contact", data.get("manager", "")),
                                  sort_order=int(data.get("sort_order", 99)))
        return jsonify({"message": f"已添加仓库 '{name}'"}), 201
    except Exception as e:
        if "已存在" in str(e):
            return jsonify({"error": str(e)}), 400
        return jsonify({"error": f"添加仓库失败: {str(e)}"}), 400


@bp_stock_aux.route("/warehouses/<int:wh_id>", methods=["PUT"])
def update_warehouse(wh_id: int):
    data = request.get_json() or {}
    inv_svc = inject_service("inventory_service")
    inv_svc.update_warehouse(wh_id, data)
    return jsonify({"message": "已更新"})


@bp_stock_aux.route("/warehouses/<int:wh_id>", methods=["DELETE"])
def delete_warehouse(wh_id: int):
    try:
        inv_svc = inject_service("inventory_service")
        name = inv_svc.delete_warehouse(wh_id)
        return jsonify({"message": f"已删除仓库 '{name}'"})
    except Exception as e:
        if "不存在" in str(e):
            return jsonify({"error": str(e)}), 404
        return jsonify({"error": f"删除仓库失败: {str(e)}"}), 400


def register_blueprint(app):
    app.register_blueprint(bp_stock_aux)
    logger.info("API v1 库位/仓库端点已注册")
