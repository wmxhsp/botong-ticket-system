"""
博通 (Botong) — 财务 API v1 完整 Blueprint
包含旧 Namespace 路由的全部端点，返回格式兼容前端。
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

from api.v1.responses import ApiResponse
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_finance = Blueprint('api_v1_finance', __name__, url_prefix='/api/v1/finance')



# ===== 公用函数 =====

def _get_finance_summary():
    """获取财务汇总数据"""
    svc = inject_service("finance_service")
    month = request.args.get("month")
    return svc.get_summary(month=month)


# ============================================================
# 根路径 / 简明汇总
# ============================================================

@bp_finance.route("/", methods=["GET"], strict_slashes=False)
def finance_root():
    """财务页入口（返回汇总数据）"""
    return jsonify(_get_finance_summary())


@bp_finance.route("/", methods=["POST"], strict_slashes=False)
def finance_root_post():
    """POST 方法交给 /pay 处理"""
    return jsonify({"error": "请使用 /api/v1/finance/pay 确认收款"}), 404


# ============================================================
# 汇总
# ============================================================

@bp_finance.route("/summary")
def finance_summary():
    """获取财务汇总"""
    return jsonify(_get_finance_summary())


# ============================================================
# 仪表盘
# ============================================================

@bp_finance.route("/dashboard")
def finance_dashboard():
    """财务总览看板"""
    svc = inject_service("finance_service")
    month = request.args.get("month")
    return jsonify(svc.get_finance_dashboard(month=month))


# ============================================================
# 确认收款
# ============================================================

@bp_finance.route("/pay", methods=["POST"])
def finance_pay():
    """确认收款（统一入口）"""
    data = request.get_json()
    ticket_id = (data or {}).get("ticket_id")
    method = (data or {}).get("method", "微信")
    note = (data or {}).get("note", "")
    if not ticket_id:
        return jsonify({"error": "请提供工单ID"}), 400

    valid_methods = {"微信", "支付宝", "现金", "银行转账", "支票", "其他"}
    if method not in valid_methods:
        return jsonify({"error": f"不支持的收款方式: {method}"}), 400

    try:
        ticket_svc = inject_service("ticket_service")
        result = ticket_svc.process_payment(ticket_id, method, note)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"收款失败 (ticket_id={ticket_id}): {e}", exc_info=True)
        return jsonify({"error": f"收款处理失败: {str(e)}"}), 500


# ============================================================
# 批量收款
# ============================================================

@bp_finance.route("/batch-pay", methods=["POST"])
def finance_batch_pay():
    """批量确认收款"""
    data = request.get_json()
    ticket_ids = (data or {}).get("ticket_ids", [])
    method = (data or {}).get("method", "微信")
    if not ticket_ids or not isinstance(ticket_ids, list):
        return jsonify({"error": "请提供工单ID列表"}), 400

    try:
        ticket_svc = inject_service("ticket_service")
        result = ticket_svc.batch_confirm_payment(ticket_ids, method)
        return jsonify(result)
    except Exception as e:
        logger.error(f"批量收款失败: {e}", exc_info=True)
        return jsonify({"error": f"批量收款处理失败: {str(e)}"}), 500


# ============================================================
# 快捷记账
# ============================================================

@bp_finance.route("/quick-income", methods=["POST"])
def quick_income():
    """快捷记账（无工单），支持可选 product_id 参数自动创建销售记录"""
    svc = inject_service("finance_service")
    data = request.get_json()
    raw_amount = data.get("amount")
    client = data.get("client", "杂项")
    method = data.get("method", "微信")
    description = data.get("description", "")
    product_id = data.get("product_id")

    if not raw_amount or float(raw_amount) <= 0:
        return jsonify({"error": "请提供有效金额"}), 400

    try:
        amount = float(raw_amount)
    except ValueError:
        return jsonify({"error": "金额格式错误"}), 400

    if amount > 99999999:
        return jsonify({"error": "金额超出合理范围"}), 400

    valid_methods = {"微信", "支付宝", "现金", "银行转账", "支票", "其他"}
    if method not in valid_methods:
        return jsonify({"error": f"不支持的收款方式: {method}"}), 400

    now = datetime.now().isoformat()

    if product_id:
        inv_svc = inject_service("inventory_service")
        product = inv_svc.get_product(int(product_id))
        if not product:
            return jsonify({"error": f"商品 #{product_id} 不存在"}), 400

        try:
            result = inv_svc.record_sale(
                goods_id=int(product_id),
                client=client,
                quantity=int(data.get("quantity", 1)),
                payment_method=method,
                amount=amount,
                notes=description,
            )
            return jsonify({"message": result["message"], "sale": result}), 201
        except Exception as e:
            svc.record_quick_income(client, amount, method,
                f"{description} (商品#{product_id}自动记录失败: {e})", now)
            return jsonify({
                "message": f"已记录收入 ¥{amount:.2f}（但库存扣减失败，请手动处理）",
                "amount": amount,
                "sale_error": str(e),
                "advice": f"商品#{product_id}库存扣减失败: {str(e)}，可手动调库",
            })

    svc.record_quick_income(client, amount, method, description, now)
    return jsonify({"message": f"已记录收入 ¥{amount:.2f}", "amount": amount})


# ============================================================
# 销售报表
# ============================================================

@bp_finance.route("/sales-report")
def sales_report():
    """获取销售报表（按商品/客户/分类汇总）"""
    svc = inject_service("finance_service")
    month = request.args.get("month")
    report = svc.get_sales_report(month=month)
    return jsonify(report)


# ============================================================
# 工单利润分析
# ============================================================

@bp_finance.route("/ticket-profit")
def ticket_profit():
    """工单利润分析（按工单维度展示收入/成本/利润/毛利率）"""
    svc = inject_service("finance_service")
    month = request.args.get("month")
    result = svc.get_ticket_profit_summary(month=month)
    return jsonify(result)


# ============================================================
# 应收款查询
# ============================================================

@bp_finance.route("/receivables")
def receivables_list():
    """统一应收款查询（按客户合并工单+销售未收款）"""
    svc = inject_service("finance_service")
    client = request.args.get("client")
    overdue_only = request.args.get("overdue") == "1"
    try:
        min_amount = float(request.args.get("min_amount", 0))
        if min_amount < 0:
            return jsonify({"error": "最小金额不能为负数"}), 400
    except ValueError:
        return jsonify({"error": "最小金额格式错误"}), 400

    if client and len(client) > 200:
        return jsonify({"error": "客户名称过长"}), 400

    def _is_safe_client_name(c):
        if c.isalnum() or c in (' ', '-', '_'):
            return True
        if '\u4e00' <= c <= '\u9fff':
            return True
        return False
    if client and not all(_is_safe_client_name(c) for c in client):
        return jsonify({"error": "客户名称包含非法字符"}), 400

    result = svc.get_receivables(client=client, overdue_only=overdue_only, min_amount=min_amount)
    return jsonify(result)


@bp_finance.route("/receivables/overdue")
def receivables_overdue():
    """获取逾期应收款列表"""
    svc = inject_service("finance_service")
    return jsonify(svc.get_overdue_receivables_summary())


# ============================================================
# 对账单
# ============================================================

@bp_finance.route("/statement/client/<path:client_name>")
def client_statement(client_name: str):
    """客户对账单（含期间内所有交易明细）"""
    svc = inject_service("finance_service")
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        result = svc.get_client_statement(client_name, start=start, end=end)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@bp_finance.route("/statement/supplier/<int:supplier_id>")
def supplier_statement(supplier_id: int):
    """供应商对账单（采购应付账款）"""
    svc = inject_service("finance_service")
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        result = svc.get_supplier_statement(supplier_id, start=start, end=end)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ============================================================
# 已有扩展端点（从原 Blueprint 保留）
# ============================================================

@bp_finance.route("/income", methods=["POST"])
def record_income():
    """记录收入"""
    try:
        svc = inject_service("finance_service")
        data = request.get_json(force=True, silent=True) or {}
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return ApiResponse.bad_request("金额必须大于 0")
        result = svc.record_income(
            source_type=data.get("source_type", "manual"),
            source_id=data.get("source_id"),
            client=data.get("client", "杂项"),
            amount=amount,
            method=data.get("method", "微信"),
            description=data.get("description", ""),
        )
        return ApiResponse.created(result, message="收入已记录")
    except Exception as e:
        logger.error(f"record_income error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_finance.route("/expenses", methods=["GET"])
def list_expenses():
    """支出列表"""
    try:
        svc = inject_service("finance_service")
        limit = int(request.args.get("limit", 100))
        expenses = svc.list_expenses(limit=limit)
        return ApiResponse.list_response(items=expenses, total=len(expenses))
    except Exception as e:
        logger.error(f"list_expenses error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_finance.route("/expenses/<int:exp_id>", methods=["PUT"])
def update_expense(exp_id: int):
    """更新支出"""
    try:
        svc = inject_service("finance_service")
        data = request.get_json(force=True, silent=True) or {}
        svc.update_expense(exp_id, **data)
        return ApiResponse.success(message="已更新")
    except Exception as e:
        logger.error(f"update_expense error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_finance.route("/expenses/<int:exp_id>", methods=["DELETE"])
def delete_expense(exp_id: int):
    """删除支出"""
    try:
        svc = inject_service("finance_service")
        svc.delete_expense(exp_id)
        return ApiResponse.success(message="已删除")
    except Exception as e:
        logger.error(f"delete_expense error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_finance.route("/unpaid")
def unpaid_tickets():
    """未结算工单"""
    try:
        svc = inject_service("finance_service")
        tickets = svc.get_unpaid_tickets()
        return ApiResponse.list_response(items=tickets, total=len(tickets))
    except Exception as e:
        logger.error(f"unpaid_tickets error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_finance.route("/overdue")
def overdue_receivables():
    """逾期应收款"""
    try:
        svc = inject_service("finance_service")
        items = svc.get_overdue_receivables()
        return ApiResponse.list_response(items=items, total=len(items))
    except Exception as e:
        logger.error(f"overdue_receivables error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_finance.route("/aging/<path:client>")
def client_aging(client: str):
    """客户账龄"""
    try:
        svc = inject_service("finance_service")
        aging = svc.get_client_aging(client)
        return ApiResponse.success(aging)
    except Exception as e:
        logger.error(f"client_aging error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_finance.route("/partial-pay", methods=["POST"])
def partial_pay():
    """分期/部分收款"""
    try:
        svc = inject_service("finance_service")
        data = request.get_json(force=True, silent=True) or {}
        ticket_id = data.get("ticket_id")
        amount = float(data.get("amount", 0))
        if not ticket_id:
            return ApiResponse.bad_request("请指定工单 ID")
        try:
            ticket_id = int(ticket_id)
        except (ValueError, TypeError):
            return ApiResponse.bad_request("工单 ID 必须是整数")

        if amount <= 0:
            return ApiResponse.bad_request("收款金额必须大于 0")
        if amount > 99999999:
            return ApiResponse.bad_request("收款金额超出合理范围")

        ticket_svc = inject_service("ticket_service")
        ticket = ticket_svc.get_ticket(ticket_id)
        if not ticket:
            return ApiResponse.bad_request(f"工单 #{ticket_id} 不存在")

        result = svc.record_partial_payment(
            ticket_id=ticket_id,
            amount=amount,
            method=data.get("method", "微信"),
            note=data.get("note", ""),
        )
        msg = "已结清" if result.get("is_settled") else f"已收款 ¥{amount:.2f}，剩余 ¥{result['remaining']:.2f}"
        return ApiResponse.success(result, message=msg)
    except ValueError as e:
        return ApiResponse.bad_request(str(e))
    except Exception as e:
        logger.error(f"partial_pay error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_finance.route("/payment-history/<int:ticket_id>")
def payment_history(ticket_id: int):
    """工单收款历史"""
    try:
        svc = inject_service("finance_service")
        records = svc.get_payment_history(ticket_id)
        return ApiResponse.list_response(items=records, total=len(records))
    except Exception as e:
        logger.error(f"payment_history error: {e}", exc_info=True)
        return ApiResponse.server_error()


# ===== 注册 =====

def register_blueprint(app):
    """注册 Blueprint"""
    app.register_blueprint(bp_finance)
    logger.info("API v1 财务完整端点已注册")
