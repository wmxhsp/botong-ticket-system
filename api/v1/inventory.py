"""
博通 — 库存/库存变动 API v1
"""

import logging
import traceback
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
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    try:
        items = inject_service('inventory_service').get_stock_summary()
    except Exception:
        items = []
    try:
        products = inject_service('inventory_service').list_products()
    except Exception:
        products = []
    start = (page - 1) * per_page
    paginated_items = items[start:start + per_page]
    paginated_products = products[start:start + per_page]
    return jsonify({
        "items": paginated_items,
        "products": paginated_products,
        "page": page,
        "per_page": per_page,
        "total_items": len(items),
        "total_products": len(products),
    })


# ── 库存变动 → stock/logs ──

@bp_stock.route("/logs")
def stock_logs():
    """库存变动流水"""
    logs = inject_service('inventory_service').get_logs_with_goods()
    return jsonify({"logs": logs})


@bp_stock.route("/alerts")
def stock_alerts():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    result = inject_service('inventory_service').check_alerts_with_summary()
    alerts = result.get("alerts", [])
    total = len(alerts)
    start = (page - 1) * per_page
    paginated = alerts[start:start + per_page]
    return jsonify({
        "alerts": paginated,
        "summary": result.get("summary", ""),
        "page": page,
        "per_page": per_page,
        "total": total,
    })


@bp_stock.route("/adjust", methods=["POST"])
def stock_adjust():
    """手动调库"""
    data = request.get_json() or {}
    goods_id = data.get("goods_id")
    quantity = int(data.get("quantity", 0))
    notes = data.get("notes", "")
    if abs(quantity) > 100000:
        return jsonify({"error": "调库数量超出合理范围"}), 400
    if not goods_id or quantity == 0:
        return jsonify({"error": "请提供商品ID和数量"}), 400
    try:
        result = inject_service('inventory_service').manual_adjust(goods_id, quantity, notes)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"调库异常: {traceback.format_exc()}")
        return jsonify({"error": "调库失败，请稍后重试"}), 500


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

    qty_raw = data.get("quantity", 1)
    try:
        qty = int(qty_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "数量必须是整数"}), 400
    if qty < 1 or qty > 10000:
        return jsonify({"error": "数量应在 1-10000 之间"}), 400

    try:
        result = inject_service('inventory_service').record_sale_with_install(
            goods_id, client,
            quantity=qty,
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
