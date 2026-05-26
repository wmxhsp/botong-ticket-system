import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service
from config.manager import config

logger = logging.getLogger(__name__)

bp_purchase = Blueprint('api_v1_purchase', __name__, url_prefix='/api/v1/purchase')



@bp_purchase.route("/", strict_slashes=False)
def list_purchase_orders():
    svc = inject_service("purchase_service")
    result = svc.list_with_summary()
    return jsonify(result)


@bp_purchase.route("/", methods=["POST"], strict_slashes=False)
def create_purchase_order():
    svc = inject_service("purchase_service")
    data = request.get_json() or {}
    vendor = data.get("vendor", "")
    if not vendor:
        return jsonify({"error": "请提供供应商"}), 400
    items = data.get("items", [])
    if not items or not isinstance(items, list):
        return jsonify({"error": "请提供至少一种商品"}), 400
    auto_receive = data.get("auto_receive") or request.args.get("auto_receive")
    result = svc.create_with_summary(vendor=vendor, items=items, notes=data.get("notes", ""), auto_receive=bool(auto_receive))
    return jsonify(result), 201


@bp_purchase.route("/stats")
def purchase_stats():
    try:
        svc = inject_service("purchase_service")
        result = svc.get_purchase_stats()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取采购统计失败: {str(e)}"}), 400


@bp_purchase.route("/<int:po_id>")
def get_purchase_order(po_id: int):
    svc = inject_service("purchase_service")
    po = svc.get_purchase_order(po_id)
    if not po:
        return jsonify({"error": "采购单不存在"}), 404
    items = svc.get_purchase_items(po_id)
    return jsonify({"purchase": po, "items": items})


@bp_purchase.route("/<int:po_id>", methods=["PUT"])
def update_purchase_order(po_id: int):
    svc = inject_service("purchase_service")
    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status not in ("ordered", "partial", "completed", "cancelled"):
        return jsonify({"error": "无效状态"}), 400

    po = svc.get_purchase_order(po_id)
    if not po:
        return jsonify({"error": "采购单不存在"}), 404

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if new_status == "completed":
        svc.complete_purchase_order(po_id, now=now)

    return jsonify({"message": f"采购单状态已更新为 {new_status}"})


@bp_purchase.route("/<int:po_id>", methods=["DELETE"])
def delete_purchase_order(po_id: int):
    svc = inject_service("purchase_service")
    po = svc.get_purchase_order(po_id)
    if not po:
        return jsonify({"error": "采购单不存在"}), 404
    if po["status"] != "draft":
        return jsonify({"error": "只有草稿状态可删除"}), 400
    svc.delete_purchase_order(po_id)
    return jsonify({"message": "已删除"})


@bp_purchase.route("/<int:po_id>/receive", methods=["POST"])
def receive_purchase(po_id: int):
    svc = inject_service("purchase_service")
    data = request.get_json() or {}
    item_id = data.get("item_id")
    receive_qty = int(data.get("quantity", 0))
    if not item_id or receive_qty <= 0:
        return jsonify({"error": "请提供商品明细ID和收货数量"}), 400
    result = svc.receive_and_stock(item_id, receive_qty)
    if result is None:
        return jsonify({"error": "商品明细不存在"}), 404
    return jsonify(result)


@bp_purchase.route("/unpaid")
def unpaid_purchase_orders():
    try:
        svc = inject_service("purchase_service")
        result = svc.get_unpaid_orders()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取未付款采购单失败: {str(e)}"}), 400


@bp_purchase.route("/<int:po_id>/pay", methods=["POST"])
def pay_purchase_order(po_id: int):
    svc = inject_service("purchase_service")
    data = request.get_json() or {}
    amount = float(data.get("amount", 0))
    method = data.get("method", "银行转账")
    result = svc.process_payment(po_id, amount, method)
    if result is None:
        return jsonify({"error": "采购单不存在"}), 404
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


def register_blueprint(app):
    app.register_blueprint(bp_purchase)
    logger.info("API v1 采购端点已注册")
