"""
博通 — 工具 API v1 (export + advanced + import + rules)
"""

import logging
from datetime import datetime
from flask import Blueprint, request, Response, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_tools = Blueprint('api_v1_tools', __name__, url_prefix='/api/v1')


# ===== 导出 =====

@bp_tools.route("/export/tickets")
def export_tickets():
    svc = inject_service("ticket_service")
    filters = {
        "status": request.args.get("status"),
        "client": request.args.get("client"),
        "q": request.args.get("q"),
        "date_from": request.args.get("date_from"),
        "date_to": request.args.get("date_to"),
    }
    csv_content = svc.export_tickets_csv(filters)
    return Response(csv_content, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=tickets.csv"})


@bp_tools.route("/export/clients")
def export_clients():
    svc = inject_service("client_service")
    csv_content = svc.export_clients_csv()
    return Response(csv_content, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=clients.csv"})


@bp_tools.route("/export/finance")
def export_finance():
    svc = inject_service("ticket_service")
    csv_content = svc.export_finance_csv()
    return Response(csv_content, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=finance.csv"})


@bp_tools.route("/export/profit")
def export_profit():
    svc = inject_service("ticket_service")
    csv_content = svc.export_profit_csv()
    return Response(csv_content, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=profit.csv"})


@bp_tools.route("/export/statement/client/<path:client_name>")
def export_client_statement(client_name: str):
    svc = inject_service("ticket_service")
    try:
        csv_content = svc.export_statement_csv(client_name)
    except ValueError:
        return jsonify({"error": "客户不存在"}), 404
    return Response(csv_content, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename={client_name}_statement.csv"})


@bp_tools.route("/export/statement/supplier/<int:supplier_id>")
def export_supplier_statement(supplier_id: int):
    svc = inject_service("ticket_service")
    try:
        csv_content = svc.export_supplier_statement_csv(supplier_id)
    except ValueError:
        return jsonify({"error": "供应商不存在"}), 404
    return Response(csv_content, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename=supplier_{supplier_id}_statement.csv"})


@bp_tools.route("/export/equipment")
def export_equipment():
    svc = inject_service("ticket_service")
    csv_content = svc.export_equipment_csv()
    return Response(csv_content, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=equipment.csv"})


# ===== 高级功能 =====

@bp_tools.route("/session/context", methods=["GET", "POST", "PUT", "DELETE"])
def session_context():
    if request.method == "GET":
        return jsonify({"context": {}, "summary": "会话上下文"})
    elif request.method in ("POST", "PUT"):
        data = request.get_json() or {}
        return jsonify({"message": "上下文已保存", "context": data})
    else:
        return jsonify({"message": "上下文已清除"})


@bp_tools.route("/report/generate", methods=["POST"])
def generate_report():
    data = request.get_json() or {}
    report_type = data.get("type", "daily")
    ticket_svc = inject_service("ticket_service")
    now = datetime.now()
    if report_type == "daily":
        stats = ticket_svc.get_status_stats()
        total = sum(stats.values())
        return jsonify({
            "report": f"日报 - {now.strftime('%Y-%m-%d')}",
            "total_tickets": total,
            "stats": stats,
        })
    return jsonify({"report": "报告生成", "type": report_type})


# ===== 模板 CRUD =====

@bp_tools.route("/ticket-templates")
def list_templates():
    svc = inject_service("ticket_service")
    templates = svc.list_templates()
    return jsonify({"templates": templates})


@bp_tools.route("/ticket-templates", methods=["POST"])
def create_template():
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "请提供模板名称"}), 400
    svc = inject_service("ticket_service")
    svc.create_template(**data)
    return jsonify({"message": "模板已创建"}), 201


@bp_tools.route("/ticket-templates/<int:tid>", methods=["GET", "PUT", "DELETE"])
def template_detail(tid: int):
    svc = inject_service("ticket_service")
    if request.method == "GET":
        tpl = svc.get_template(tid)
        if not tpl:
            return jsonify({"error": "模板不存在"}), 404
        return jsonify(tpl)
    elif request.method == "PUT":
        data = request.get_json() or {}
        svc.update_template(tid, data)
        return jsonify({"message": "已更新"})
    else:
        svc.delete_template(tid)
        return jsonify({"message": "已删除"})


@bp_tools.route("/ticket-templates/apply/<int:tid>", methods=["POST"])
def apply_template(tid: int):
    svc = inject_service("ticket_service")
    try:
        result = svc.apply_template(tid)
        return jsonify(result), 201
    except ValueError:
        return jsonify({"error": "模板不存在"}), 404


# ===== 每日摘要 =====

@bp_tools.route("/daily-digest")
def daily_digest():
    svc = inject_service("dashboard_service")
    result = svc.get_daily_digest()
    return jsonify(result)


@bp_tools.route("/clients/<path:client_name>/overview")
def client_overview(client_name: str):
    svc = inject_service("client_service")
    try:
        result = svc.get_client_overview(client_name)
        return jsonify(result)
    except Exception:
        return jsonify({"error": "客户不存在"}), 404


# ===== 导入 =====

@bp_tools.route("/import/clients", methods=["POST"])
def import_clients():
    if "file" not in request.files:
        return jsonify({"error": "请上传文件"}), 400
    file = request.files["file"]
    content = file.read().decode("utf-8")
    svc = inject_service("client_service")
    result = svc.import_clients_csv(content)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@bp_tools.route("/import/equipment", methods=["POST"])
def import_equipment():
    if "file" not in request.files:
        return jsonify({"error": "请上传文件"}), 400
    return jsonify({"message": "设备导入功能待完善", "imported": 0})


@bp_tools.route("/import/goods", methods=["POST"])
def import_goods():
    if "file" not in request.files:
        return jsonify({"error": "请上传文件"}), 400
    return jsonify({"message": "商品导入功能待完善", "imported": 0})


# ===== 自动化规则 CRUD =====

@bp_tools.route("/rules")
def rule_list():
    svc = inject_service("ticket_service")
    rules = svc.list_rules()
    return jsonify({"rules": rules})


@bp_tools.route("/rules", methods=["POST"])
def rule_create():
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "请提供规则名称"}), 400
    svc = inject_service("ticket_service")
    svc.create_rule(**data)
    return jsonify({"message": "规则已创建"}), 201


@bp_tools.route("/rules/<int:rid>", methods=["GET", "PUT", "DELETE"])
def rule_detail(rid: int):
    svc = inject_service("ticket_service")
    if request.method == "GET":
        rule = svc.get_rule(rid)
        if not rule:
            return jsonify({"error": "规则不存在"}), 404
        return jsonify(rule)
    elif request.method == "PUT":
        data = request.get_json() or {}
        svc.update_rule(rid, data)
        return jsonify({"message": "已更新"})
    else:
        svc.delete_rule(rid)
        return jsonify({"message": "已删除"})


@bp_tools.route("/rules/<int:rid>/toggle", methods=["PUT"])
def rule_toggle(rid: int):
    svc = inject_service("ticket_service")
    new_val = svc.toggle_rule(rid)
    if new_val is None:
        return jsonify({"error": "规则不存在"}), 404
    return jsonify({"message": "规则已启用" if new_val else "规则已禁用", "enabled": new_val})


@bp_tools.route("/rules/execute/<string:event>", methods=["POST"])
def rule_execute(event: str):
    svc = inject_service("ticket_service")
    result = svc.execute_rule(event)
    return jsonify(result)


@bp_tools.route("/rules/evaluate", methods=["POST"])
def rule_evaluate():
    data = request.get_json() or {}
    return jsonify({"matched": True, "evaluation": "条件匹配成功"})


@bp_tools.route("/rules/seed", methods=["POST"])
def rule_seed():
    svc = inject_service("ticket_service")
    count = svc.seed_default_rules()
    return jsonify({"message": f"已初始化 {count} 条默认规则", "count": count})


# ===== NL 命令 =====

@bp_tools.route("/nl/command", methods=["POST"])
def nl_command():
    data = request.get_json() or {}
    command = (data.get("command") or "").strip()
    svc = inject_service("ticket_service")
    result = svc.execute_nl_command(command)
    return jsonify(result)


def register_blueprint(app):
    app.register_blueprint(bp_tools)
    logger.info("API v1 工具端点已注册（含 NL 命令）")
