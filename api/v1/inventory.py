"""
博通 — 库存/库存变动 API v1
"""

import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_inventory = Blueprint('api_v1_inventory', __name__, url_prefix='/api/v1/inventory')

# 部分 stock 端点也用此 url_prefix
bp_stock = Blueprint('api_v1_stock', __name__, url_prefix='/api/v1/stock')


# ── 库存概览 ──

@bp_inventory.route("/", strict_slashes=False)
def inventory_list():
    """获取库存概览"""
    try:
        items = inject_service('inventory_service').get_stock_summary()
    except Exception:
        items = []
    try:
        products = inject_service('inventory_service').list_products()
    except Exception:
        products = []
    return jsonify({"items": items, "products": products})


# ── 库存变动 → stock/logs ──

@bp_stock.route("/logs")
def stock_logs():
    """库存变动流水"""
    logs = inject_service('inventory_service').get_logs_with_goods()
    return jsonify({"logs": logs})


@bp_stock.route("/alerts")
def stock_alerts():
    result = inject_service('inventory_service').check_alerts_with_summary()
    return jsonify(result)


@bp_stock.route("/adjust", methods=["POST"])
def stock_adjust():
    """手动调库"""
    data = request.get_json() or {}
    goods_id = data.get("goods_id")
    quantity = int(data.get("quantity", 0))
    notes = data.get("notes", "")
    if not goods_id or quantity == 0:
        return jsonify({"error": "请提供商品ID和数量"}), 400
    try:
        result = inject_service('inventory_service').manual_adjust(goods_id, quantity, notes)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"调库失败: {str(e)}"}), 400


@bp_stock.route("/transfer", methods=["POST"])
def stock_transfer():
    """库存调拨"""
    data = request.get_json() or {}
    goods_id = data.get("goods_id")
    quantity = int(data.get("quantity", 0))
    to_location = data.get("to_location", "")
    if not goods_id or quantity <= 0 or not to_location:
        return jsonify({"error": "请提供商品ID、数量和目标库位"}), 400
    try:
        result = inject_service('inventory_service').transfer(goods_id, quantity, to_location)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"调拨失败: {str(e)}"}), 400


@bp_stock.route("/count", methods=["POST"])
def stock_count():
    """库存盘点"""
    data = request.get_json() or {}
    goods_id = data.get("goods_id")
    actual_qty = int(data.get("actual_qty", 0))
    notes = data.get("notes", "")
    if not goods_id:
        return jsonify({"error": "请提供商品ID"}), 400
    try:
        result = inject_service('inventory_service').stock_count(goods_id, actual_qty, notes)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"盘点失败: {str(e)}"}), 400


# ── 销售 ──

@bp_stock.route("/sale")
def sale_list():
    """获取销售记录"""
    try:
        records = inject_service('inventory_service').list_sales_records()
        return jsonify({"records": records})
    except Exception as e:
        return jsonify({"error": f"获取销售记录失败: {str(e)}"}), 400


@bp_stock.route("/sale", methods=["POST"])
def sale_create():
    data = request.get_json() or {}
    goods_id = data.get("goods_id")
    client = data.get("client", "").strip()
    if not goods_id:
        return jsonify({"error": "请提供商品ID"}), 400
    if not client:
        return jsonify({"error": "请提供客户名称"}), 400

    try:
        result = inject_service('inventory_service').record_sale_with_install(
            goods_id, client,
            quantity=int(data.get("quantity", 1)),
            payment_method=data.get("payment_method", "微信"),
            amount=float(data.get("amount", 0)) if data.get("amount") is not None else None,
            validity_days=int(data.get("validity_days", 0)),
            notes=data.get("notes", ""),
            warehouse_id=data.get("warehouse_id"),
            discount_type=data.get("discount_type", ""),
            discount_value=float(data.get("discount_value", 0)),
            ticket_id=data.get("ticket_id"),
            salesperson=data.get("salesperson", ""),
            create_install_ticket=data.get("create_install_ticket", False),
            install_tech=data.get("install_tech", ""),
            install_date=data.get("install_date", ""),
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": f"销售失败: {str(e)}", "advice": "请检查库存是否充足"}), 400


@bp_stock.route("/sale/<int:sale_id>/renew", methods=["POST"])
def sale_renew(sale_id: int):
    """续费"""
    data = request.get_json() or {}
    try:
        inv_svc = inject_service('inventory_service')
        result = inv_svc.renew_sale(
            sale_id,
            client=data.get("client"),
            quantity=int(data.get("quantity", 1)),
            payment_method=data.get("payment_method", "微信"),
            amount=float(data.get("amount", 0)) if data.get("amount") else None,
            validity_days=int(data.get("validity_days", 0)) or None,
            notes=data.get("notes"),
        )
        return jsonify(result), 201
    except Exception as e:
        error_msg = str(e)
        if "不存在" in error_msg:
            return jsonify({"error": error_msg}), 404
        if "没有关联商品" in error_msg:
            return jsonify({"error": error_msg}), 400
        return jsonify({"error": f"续费失败: {error_msg}"}), 400


@bp_stock.route("/alerts/<int:goods_id>/purchase", methods=["POST"])
def alert_create_purchase(goods_id: int):
    try:
        result = inject_service('inventory_service').create_restock_order(goods_id)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def register_blueprint(app):
    app.register_blueprint(bp_inventory)
    app.register_blueprint(bp_stock)
    logger.info("API v1 库存+库存变动端点已注册")
