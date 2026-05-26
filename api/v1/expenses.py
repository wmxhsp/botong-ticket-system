"""
博通 — 支出管理 API v1
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_expenses = Blueprint('api_v1_expenses', __name__, url_prefix='/api/v1/expenses')



# ── 支出分类 ──

@bp_expenses.route("/categories")
def list_categories():
    """获取支出分类列表"""
    svc = inject_service("finance_service")
    cats = svc.list_expense_categories()
    return jsonify({"categories": cats})


@bp_expenses.route("/categories", methods=["POST"])
def create_category():
    """新增支出分类"""
    svc = inject_service("finance_service")
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "请提供分类名称"}), 400
    try:
        svc.create_expense_category(name)
        return jsonify({"message": f"分类已创建: {name}"}), 201
    except Exception as e:
        return jsonify({"error": f"创建失败: {str(e)}"}), 400


@bp_expenses.route("/categories", methods=["PUT"])
def update_category():
    """更新分类名称"""
    svc = inject_service("finance_service")
    data = request.get_json() or {}
    cat_id = data.get("id")
    name = data.get("name", "").strip()
    if not cat_id or not name:
        return jsonify({"error": "请提供分类ID和名称"}), 400
    try:
        svc.update_expense_category(cat_id, name)
        return jsonify({"message": "分类已更新"})
    except Exception as e:
        return jsonify({"error": f"更新分类失败: {str(e)}"}), 400


@bp_expenses.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id: int):
    """删除支出分类"""
    svc = inject_service("finance_service")
    cat = svc.get_expense_category(cat_id)
    if cat:
        ref_count = svc.count_expenses_by_category(cat["name"])
        if ref_count > 0:
            return jsonify({"error": f"分类「{cat['name']}」已被 {ref_count} 条记录引用，无法删除"}), 400
    svc.delete_expense_category(cat_id)
    return jsonify({"message": "分类已删除"})


# ── 支出 ──

@bp_expenses.route("/", strict_slashes=False)
def list_expenses():
    """获取支出列表"""
    svc = inject_service("finance_service")
    items = svc.list_expenses()
    return jsonify({"expenses": items})


@bp_expenses.route("/", methods=["POST"], strict_slashes=False)
def add_expense():
    """新增支出"""
    svc = inject_service("finance_service")
    data = request.get_json() or {}
    if not data.get("amount"):
        return jsonify({"error": "请提供金额"}), 400
    try:
        svc.add_expense(
            category=data.get("category", "其他"),
            vendor=data.get("vendor", ""),
            amount=float(data["amount"]),
            description=data.get("description", ""),
            paid_at=data.get("paid_at"),
            related_ticket_id=data.get("related_ticket_id"),
        )
        return jsonify({"message": f"支出已记录 ¥{float(data['amount']):.2f}"}), 201
    except Exception as e:
        return jsonify({"error": f"记录支出失败: {str(e)}"}), 400


@bp_expenses.route("/<int:exp_id>", methods=["PUT"])
def update_expense(exp_id: int):
    """更新支出"""
    svc = inject_service("finance_service")
    data = request.get_json() or {}
    svc.update_expense(exp_id, **data)
    return jsonify({"message": "已更新"})


@bp_expenses.route("/<int:exp_id>", methods=["DELETE"])
def delete_expense(exp_id: int):
    """删除支出"""
    svc = inject_service("finance_service")
    svc.delete_expense(exp_id)
    return jsonify({"message": "已删除"})


# ── 个人费用 ──

@bp_expenses.route("/personal")
def list_personal_expenses():
    """获取个人费用列表"""
    svc = inject_service("finance_service")
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    category = request.args.get("category", "")
    items = svc.list_personal_expenses(month=month, category=category)
    summary = svc.get_personal_month_summary(month)
    return jsonify({"expenses": items, "summary": summary})


@bp_expenses.route("/personal", methods=["POST"])
def add_personal_expense():
    """记录个人费用支出"""
    svc = inject_service("finance_service")
    data = request.get_json() or {}
    amount = float(data.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "请提供有效金额"}), 400
    category = data.get("category", "其他").strip()
    if not category:
        return jsonify({"error": "请提供支出分类"}), 400
    try:
        paid_at = data.get("paid_at", datetime.now().strftime("%Y-%m-%d"))
        record_id = svc.add_personal_expense(
            category=category, amount=amount, paid_at=paid_at,
            vendor=data.get("vendor", ""), payment_type=data.get("payment_type", "微信"),
            description=data.get("description", ""),
            is_recurring=int(data.get("is_recurring", 0)),
        )
        return jsonify({"message": f"个人支出已记录 ¥{amount:.2f}", "id": record_id}), 201
    except Exception as e:
        return jsonify({"error": f"记录失败: {str(e)}"}), 400


@bp_expenses.route("/personal/summary")
def personal_summary():
    """个人月度支出汇总"""
    svc = inject_service("finance_service")
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    summary = svc.get_personal_month_summary(month)
    return jsonify(summary)


@bp_expenses.route("/personal/budget", methods=["GET", "POST"])
def personal_budget():
    """获取/设置个人预算"""
    svc = inject_service("finance_service")
    from flask import request as _req
    if _req.method == "GET":
        month = _req.args.get("month", datetime.now().strftime("%Y-%m"))
        budget = svc.get_personal_budget(month)
        return jsonify({"budget": budget})
    else:
        data = _req.get_json() or {}
        month = data.get("month", datetime.now().strftime("%Y-%m"))
        amount = float(data.get("amount", 0))
        svc.set_personal_budget(month, amount)
        return jsonify({"message": "预算已设置"})


@bp_expenses.route("/personal/recurring")
def list_recurring():
    """获取循环支出"""
    svc = inject_service("finance_service")
    items = svc.list_recurring_expenses()
    return jsonify({"recurring": items})


@bp_expenses.route("/personal/recurring", methods=["POST"])
def create_recurring():
    """创建循环支出"""
    svc = inject_service("finance_service")
    data = request.get_json() or {}
    result = svc.create_recurring_expense(data)
    return jsonify({"message": result.get("message", "已创建")}), 201


@bp_expenses.route("/personal/item/<int:exp_id>", methods=["PUT"])
def update_personal_item(exp_id: int):
    """更新个人支出"""
    svc = inject_service("finance_service")
    data = request.get_json() or {}
    svc.update_personal_expense(exp_id, **data)
    return jsonify({"message": "已更新"})


@bp_expenses.route("/personal/item/<int:exp_id>", methods=["DELETE"])
def delete_personal_item(exp_id: int):
    """删除个人支出"""
    svc = inject_service("finance_service")
    svc.delete_personal_expense(exp_id)
    return jsonify({"message": "已删除"})


def register_blueprint(app):
    app.register_blueprint(bp_expenses)
    logger.info("API v1 支出管理端点已注册")
