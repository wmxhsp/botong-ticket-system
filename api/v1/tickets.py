"""
博通 (Botong) — 工单 API v1 完整 Blueprint
包含旧 Namespace 路由 api/v1/tickets 的全部端点，返回格式兼容前端。
"""

import json
import os
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify

from api.v1.responses import ApiResponse
from domain.exceptions import TicketNotFoundError, TicketValidationError
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_IDEMPOTENT_TTL = 3600

_ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_MAX_UPLOAD_SIZE = 10 * 1024 * 1024

_IMAGE_MAGIC = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "image/webp": [b"RIFF"],
}

def _validate_image_upload(file_storage):
    if file_storage.mimetype not in _ALLOWED_IMAGE_MIMES:
        return False, f"不支持的文件类型: {file_storage.mimetype}"
    file_storage.seek(0, 2)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > _MAX_UPLOAD_SIZE:
        return False, f"文件过大: {size} bytes (最大 {_MAX_UPLOAD_SIZE} bytes)"
    header = file_storage.read(12)
    file_storage.seek(0)
    magics = _IMAGE_MAGIC.get(file_storage.mimetype, [])
    if magics and not any(header.startswith(m) for m in magics):
        return False, "文件内容与声明类型不匹配"
    return True, ""





# ===== 幂等性支持 =====

def _check_idempotent(key):
    if not key:
        return None
    try:
        return inject_service("ticket_service").check_idempotent(key)
    except Exception:
        pass
    return None


def _set_idempotent(key, data):
    if not key:
        return
    try:
        inject_service("ticket_service").set_idempotent(key, data, ttl=_IDEMPOTENT_TTL)
    except Exception:
        pass


def _clean_expired_idempotent():
    try:
        inject_service("ticket_service").clean_expired_idempotent()
    except Exception:
        pass


# ===== 工时计时器支持 =====

def _get_timer_start(ticket_id):
    svc = inject_service("ticket_service")
    val = svc.get_timer(ticket_id) if svc else None
    if val:
        try:
            return datetime.fromisoformat(val)
        except (ValueError, TypeError):
            pass
    return None


def _set_timer_start(ticket_id, dt):
    svc = inject_service("ticket_service")
    if svc:
        svc.set_timer(ticket_id, dt.isoformat())


def _clear_timer(ticket_id):
    svc = inject_service("ticket_service")
    if svc:
        svc.clear_timer(ticket_id)


def _get_parse_suggestions(parsed):
    suggestions = []
    if not parsed.get("_client_matched"):
        suggestions.append(f"客户「{parsed.get('client', '')}」未在系统中找到，将作为新客户创建")
    if parsed.get("estimated_hours", 0) > 0:
        suggestions.append(f"预估工时 {parsed['estimated_hours']} 小时")
    return suggestions


# ===== Blueprint =====
bp_tickets = Blueprint('api_v1_tickets', __name__, url_prefix='/api/v1/tickets')


# ============================================================
# 工单列表 / 创建 / 删除
# ============================================================

@bp_tickets.route("/", methods=["GET"], strict_slashes=False)
def list_tickets():
    """获取工单列表（带分页/排序/筛选/利润）"""
    svc = inject_service("ticket_service")

    try:
        result = svc.list_tickets_paginated(
            page=request.args.get("page", 1, type=int),
            per_page=request.args.get("per_page", 50, type=int),
            status=request.args.get("status") or None,
            client=request.args.get("client") or None,
            keyword=request.args.get("q") or None,
            date_from=request.args.get("date_from") or None,
            date_to=request.args.get("date_to") or None,
            sort_field=request.args.get("sort") or None,
            sort_dir=request.args.get("order", "desc"),
        )
    except Exception as e:
        logger.error(f"工单列表查询失败: {e}")
        return jsonify({"tickets": [], "total": 0, "summary": "查询失败，请稍后重试"}), 500

    tickets = result["tickets"]
    total = result["total"]

    for t in tickets:
        t["status_name"] = svc.STATUS_NAMES.get(t.get("status"), t.get("status"))

    tickets = svc.calc_list_profits(tickets)

    return jsonify({
        "tickets": tickets,
        "total": total,
        "page": result["page"],
        "per_page": result["per_page"],
        "total_pages": result["total_pages"],
    })


@bp_tickets.route("/", methods=["POST"], strict_slashes=False)
def create_ticket():
    """创建工单（含 Schema 验证 + 幂等性保护）"""
    from api.validators import validate_json
    from api.validators.schemas import TicketCreateSchema
    svc = inject_service("ticket_service")
    tech_svc = inject_service("technician_service")

    _clean_expired_idempotent()

    data = request.get_json(force=True, silent=True) or {}
    if not data:
        return jsonify({"error": "请提供工单数据"}), 400

    try:
        validated = TicketCreateSchema(**{k: v for k, v in data.items()
                                          if k in TicketCreateSchema.model_fields})
        data.update(validated.model_dump(exclude_unset=True))
    except Exception as ve:
        return jsonify({"error": f"数据验证失败: {str(ve)}"}), 400

    if "client" not in data:
        return jsonify({"error": "缺少必填字段: client"}), 400
    if "content" not in data and "title" not in data:
        return jsonify({"error": "缺少必填字段: content/title"}), 400

    # 幂等性检查
    idempotent_key = (request.headers.get("X-Idempotency-Key") or
                      data.get("_idempotent_key", ""))
    cached = _check_idempotent(idempotent_key)
    if cached:
        logger.info(f"幂等命中: key={idempotent_key[:16]}...")
        return jsonify({"ticket": cached, "message": "已提交（幂等返回）"}), 200
    if "_idempotent_key" in data:
        del data["_idempotent_key"]

    try:
        create_data = {
            "client": data["client"],
            "content": data.get("content") or data.get("title", ""),
            "contact": data.get("contact", ""),
            "location": data.get("location", ""),
            "service_type": data.get("service_type", ""),
            "priority": data.get("priority", "M"),
            "billing_model": data.get("billing_model", "hourly"),
            "amount": data.get("amount", 0),
            "estimated_hours": float(data.get("estimated_hours", 0)),
            "appointment_at": data.get("appointment_at"),
            "service_fee_id": data.get("service_fee_id"),
            "assignee": data.get("assignee", ""),
            "travel_distance": float(data.get("travel_distance", 0)),
            "travel_rate": float(data.get("travel_rate", 0)),
            "equipment_id": data.get("equipment_id"),
        }
        ticket = svc.create_ticket(create_data)
        result = dict(ticket) if ticket else {}

        equip_id = data.get("equipment_id")
        if equip_id and result.get("id"):
            svc.link_equipment(result["id"], equip_id)

        if result.get("id"):
            result = dict(svc.get_ticket(result["id"]))

        ticket_no = result.get("ticket_no", "") or f"#{result['id']}"
        client_name = data["client"]
        summary = f"工单 {ticket_no} 已创建，客户：{client_name}，内容：{data.get('content') or data.get('title', '')[:30]}"

        if idempotent_key:
            _set_idempotent(idempotent_key, result)

        return jsonify({"message": "工单创建成功", "ticket": result, "summary": summary}), 201
    except Exception as e:
        return jsonify({"error": f"创建失败: {str(e)}"}), 400


@bp_tickets.route("/", methods=["DELETE"], strict_slashes=False)
def delete_ticket_by_id():
    """删除工单（通过查询参数 ?id=）"""
    svc = inject_service("ticket_service")
    ticket_id = request.args.get("id")
    if not ticket_id:
        return jsonify({"error": "请提供工单ID"}), 400
    svc.delete_ticket(int(ticket_id))
    return jsonify({"message": "工单已删除"})


# ============================================================
# 批量操作
# ============================================================

@bp_tickets.route("/batch", methods=["POST"])
def batch_operation():
    """批量操作工单"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    action = data.get("action")
    ids = data.get("ids", [])
    if not action or not ids:
        return jsonify({"error": "请提供操作类型和工单ID列表"}), 400

    results = {"success": 0, "failed": 0}
    for raw_id in ids:
        try:
            tid = int(raw_id)
        except (ValueError, TypeError):
            results["failed"] += 1
            continue
        try:
            if action == "complete":
                svc.transition_status(tid, "pending-payment", note="批量完工")
                results["success"] += 1
            elif action == "delete":
                svc.delete_ticket(tid)
                results["success"] += 1
            elif action == "status":
                new_status = data.get("target_status")
                if new_status and new_status in svc.STATUS_NAMES:
                    try:
                        svc.transition_status(tid, new_status)
                        results["success"] += 1
                    except Exception:
                        results["failed"] += 1
                else:
                    results["failed"] += 1
            else:
                return jsonify({"error": f"不支持的操作类型: {action}"}), 400
        except Exception as e:
            logger.warning(f"Batch action failed for ticket {tid}: {e}")
            results["failed"] += 1

    return jsonify({"message": f"完成 {results['success']} 条，失败 {results['failed']} 条", **results})


# ============================================================
# 工单详情
# ============================================================

@bp_tickets.route("/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id: int):
    """获取工单详情"""
    svc = inject_service("ticket_service")
    try:
        result = svc.enrich_ticket_detail(ticket_id)
    except TicketNotFoundError:
        return jsonify({"error": "工单不存在"}), 404
    return jsonify(result)


@bp_tickets.route("/<int:ticket_id>", methods=["PUT"])
def update_ticket(ticket_id: int):
    """更新工单（含 Schema 验证）"""
    from api.validators.schemas import TicketUpdateSchema
    svc = inject_service("ticket_service")
    data = request.get_json()
    if not data:
        return jsonify({"error": "请提供更新数据"}), 400
    try:
        validated = TicketUpdateSchema(**{k: v for k, v in data.items()
                                          if k in TicketUpdateSchema.model_fields})
        data.update(validated.model_dump(exclude_unset=True))
    except Exception as ve:
        return jsonify({"error": f"数据验证失败: {str(ve)}"}), 400
    data.pop("status", None)
    data.pop("billing_status", None)
    svc.update_ticket(ticket_id, data)
    if "tax_rate" in data or "discount_type" in data or "discount_value" in data:
        inject_service("ticket_service").recalc_ticket_total(ticket_id)
    return jsonify({"message": "工单已更新"})


@bp_tickets.route("/<int:ticket_id>", methods=["DELETE"])
def delete_ticket_by_detail(ticket_id: int):
    """删除单个工单"""
    svc = inject_service("ticket_service")
    svc.delete_ticket(ticket_id)
    return jsonify({"message": "工单已删除"})


# ============================================================
# 状态流转图
# ============================================================

@bp_tickets.route("/status-flow", methods=["GET"])
def status_flow():
    """获取状态流转图"""
    svc = inject_service("ticket_service")
    return jsonify({
        "status_names": svc.STATUS_NAMES,
        "status_flow": svc.STATUS_FLOW,
    })


# ============================================================
# 统计
# ============================================================

@bp_tickets.route("/stats", methods=["GET"])
def ticket_stats():
    """获取工单统计"""
    svc = inject_service("ticket_service")
    stats = svc.get_status_stats()
    return jsonify({"stats": stats or {}})


# ============================================================
# 完工
# ============================================================

@bp_tickets.route("/<int:ticket_id>/complete", methods=["POST"])
def complete_ticket(ticket_id: int):
    """完工（自动结算：多人劳务费+人工成本支出）"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}

    try:
        result = svc.complete_ticket(ticket_id, data)
        return jsonify(result)
    except TicketNotFoundError:
        return jsonify({"error": "工单不存在"}), 404
    except TicketValidationError as e:
        return jsonify({"error": str(e)}), 400


# ============================================================
# 工单利润
# ============================================================

@bp_tickets.route("/<int:ticket_id>/profit", methods=["GET"])
def ticket_profit(ticket_id: int):
    """按工单查询利润明细"""
    finance_svc = inject_service("finance_service")
    try:
        result = finance_svc.get_ticket_profit_detail(ticket_id)
        return jsonify(result)
    except Exception:
        return jsonify({"error": "工单不存在"}), 404


@bp_tickets.route("/profit-list", methods=["GET"])
def ticket_profit_list():
    """获取全部工单利润列表"""
    finance_svc = inject_service("finance_service")
    result = finance_svc.get_ticket_profit_list()
    return jsonify(result)


# ============================================================
# 物料管理
# ============================================================

@bp_tickets.route("/<int:ticket_id>/materials", methods=["GET"])
def list_materials(ticket_id: int):
    """获取工单物料列表"""
    svc = inject_service("ticket_service")
    materials = svc.get_ticket_materials(ticket_id)
    return jsonify({"materials": materials})


@bp_tickets.route("/<int:ticket_id>/materials", methods=["POST"])
def add_material(ticket_id: int):
    """工单领料（自动扣减库存）"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    try:
        result = svc.add_material_with_inventory(ticket_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp_tickets.route("/<int:ticket_id>/materials/<int:mat_id>", methods=["PUT"])
def update_material(ticket_id: int, mat_id: int):
    """修改工单物料数量或价格"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    quantity = data.get("quantity")
    unit_price = data.get("unit_price")
    if quantity is None and unit_price is None:
        return jsonify({"error": "请提供数量或单价"}), 400
    try:
        result = svc.update_material(mat_id, ticket_id, quantity=quantity, unit_price=unit_price)
        inject_service("ticket_service").recalc_ticket_total(ticket_id)
        return jsonify({"message": "物料已更新", **result})
    except Exception as e:
        return jsonify({"error": f"物料更新失败: {str(e)}"}), 404


@bp_tickets.route("/<int:ticket_id>/materials/<int:mat_id>", methods=["DELETE"])
def delete_material(ticket_id: int, mat_id: int):
    """删除工单物料"""
    svc = inject_service("ticket_service")
    svc.delete_material(mat_id, ticket_id)
    inject_service("ticket_service").recalc_ticket_total(ticket_id)
    return jsonify({"message": "物料已删除"})


@bp_tickets.route("/<int:ticket_id>/materials/trace", methods=["GET"])
def material_trace(ticket_id: int):
    """物料追溯链"""
    svc = inject_service("ticket_service")
    result = svc.trace_material(ticket_id)
    return jsonify(result)


# ============================================================
# 照片管理
# ============================================================

@bp_tickets.route("/<int:ticket_id>/photos", methods=["GET"])
def list_photos(ticket_id: int):
    """获取工单照片列表"""
    svc = inject_service("ticket_service")
    try:
        photos = []
        ticket_dir = str(_PROJECT_ROOT / "static" / "uploads" / "tickets" / str(ticket_id))
        for p in svc.get_ticket_photos(ticket_id):
            photos.append(p)
        if os.path.exists(ticket_dir):
            for f in sorted(os.listdir(ticket_dir)):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) and not f.startswith('raw_'):
                    fp = os.path.join(ticket_dir, f)
                    url_path = f"/static/uploads/tickets/{ticket_id}/{f}"
                    if not any(x.get("filepath", "").endswith(f) for x in photos):
                        photos.append({
                            "id": None, "ticket_id": ticket_id, "type": "watermarked",
                            "filepath": url_path,
                            "created_at": datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M") if os.path.exists(fp) else "",
                        })
        for p in photos:
            if p.get("filepath") and not p["filepath"].startswith("/"):
                p["filepath"] = "/" + p["filepath"]
        return jsonify({"photos": photos})
    except Exception as e:
        return jsonify({"photos": [], "error": f"获取照片失败: {str(e)}"})


@bp_tickets.route("/<int:ticket_id>/photos", methods=["POST"])
def upload_photo(ticket_id: int):
    """上传照片（自动打水印）"""
    svc = inject_service("ticket_service")
    if "photo" not in request.files:
        return jsonify({"error": "请选择照片"}), 400
    photo = request.files["photo"]
    ok, err = _validate_image_upload(photo)
    if not ok:
        return jsonify({"error": err}), 400
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    ticket_dir = str(_PROJECT_ROOT / "static" / "uploads" / "tickets" / str(ticket_id))
    os.makedirs(ticket_dir, exist_ok=True)
    raw_path = os.path.join(ticket_dir, f"raw_{ticket_id}_{now_str}.jpg")
    photo.save(raw_path)
    filename = f"wm_{ticket_id}_{now_str}.jpg"
    # 尝试将打水印任务异步入队；若队列不可用回退到同步处理
    try:
        from infrastructure.di.container import Container
        from infrastructure.queue.interfaces import Task

        queue = Container.resolve("queue") if Container.has("queue") else None
        if queue:
                task = Task(
                    name="tasks.photo_tasks.process_watermark",
                    payload={
                        "raw_path": raw_path,
                        "ticket_id": ticket_id,
                        "filename": filename,
                    },
                )
                # 记录任务状态到磁盘状态文件（轻量替代 DB schema 变更）
                try:
                    import json, os
                    os.makedirs(os.path.join(os.getcwd(), '.data'), exist_ok=True)
                    status_path = os.path.join(os.getcwd(), '.data', 'photo_task_status.json')
                    entry = {
                        'task_id': task.task_id or f"local-{task.name}-{int(datetime.now().timestamp())}",
                        'ticket_id': ticket_id,
                        'filename': filename,
                        'status': 'queued',
                        'created_at': datetime.now().isoformat(),
                    }
                    # append to jsonlines file
                    with open(status_path, 'a', encoding='utf-8') as sf:
                        sf.write(json.dumps(entry, ensure_ascii=False) + "\n")
                except Exception:
                    pass
                task_id = queue.enqueue(task)
                logger.info(f"照片处理任务已入队: task_id={task_id}, ticket_id={ticket_id}")
                return jsonify({
                    "message": "照片已上传，正在后台处理",
                    "task_id": task_id,
                    "filepath": f"/static/uploads/tickets/{ticket_id}/{filename}",
                })
        else:
            # 回退到同步处理
            try:
                svc.add_watermark(raw_path, ticket_id)
            except Exception as e:
                logger.warning(f"照片打水印失败 (ticket_id={ticket_id}): {e}")
            filepath = f"static/uploads/tickets/{ticket_id}/{filename}"
            svc.save_photo(ticket_id, filename, filepath)
            return jsonify({
                "message": "照片已上传",
                "filepath": f"/static/uploads/tickets/{ticket_id}/{filename}"
            })
    except Exception as e:
        logger.warning(f"照片处理调度失败 (ticket_id={ticket_id}): {e}")
        # 最后回退到同步保存，避免上传丢失
        try:
            svc.add_watermark(raw_path, ticket_id)
        except Exception:
            pass
        filepath = f"static/uploads/tickets/{ticket_id}/{filename}"
        try:
            svc.save_photo(ticket_id, filename, filepath)
        except Exception:
            pass
        return jsonify({"message": "照片已上传（回退处理）", "filepath": f"/static/uploads/tickets/{ticket_id}/{filename}"})


@bp_tickets.route("/<int:ticket_id>/photos", methods=["DELETE"])
def delete_photo(ticket_id: int):
    """删除工单照片"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    photo_id = data.get("id")
    filepath = data.get("filepath", "")
    if photo_id:
        p = svc.get_photo(photo_id, ticket_id)
        if p:
            svc.delete_photo(photo_id)
            fp = p["filepath"]
            full = str(_PROJECT_ROOT / fp.lstrip("/"))
            if os.path.exists(full):
                os.remove(full)
            return jsonify({"message": "照片已删除"})
    if filepath:
        full = str(_PROJECT_ROOT / filepath.lstrip("/"))
        if os.path.exists(full):
            os.remove(full)
        svc.delete_photo_by_path(filepath, ticket_id)
        return jsonify({"message": "照片已删除"})
    return jsonify({"error": "请提供照片ID或路径"}), 400


# ============================================================
# 技术服务人员管理
# ============================================================

@bp_tickets.route("/<int:ticket_id>/technicians", methods=["GET"])
def list_technicians(ticket_id: int):
    """获取工单负责人列表"""
    svc = inject_service("ticket_service")
    techs = svc.get_technicians(ticket_id)
    return jsonify({"technicians": techs})


@bp_tickets.route("/<int:ticket_id>/technicians", methods=["POST"])
def add_technician(ticket_id: int):
    """添加/更新负责人"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    cost_rate = float(data.get("cost_rate", 30))
    hours = float(data.get("hours", 0))
    if not name:
        return jsonify({"error": "请提供负责人名称"}), 400
    try:
        svc.add_technician(ticket_id, name, cost_rate, hours)
        return jsonify({"message": f"已添加负责人: {name}"})
    except Exception as e:
        return jsonify({"error": f"添加负责人失败: {str(e)}"}), 400


@bp_tickets.route("/<int:ticket_id>/technicians", methods=["DELETE"])
def remove_technician(ticket_id: int):
    """删除负责人"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "请提供负责人名称"}), 400
    svc.remove_technician(ticket_id, name)
    return jsonify({"message": f"已移除负责人: {name}"})


# ============================================================
# 服务明细行 (ticket_service_items)
# ============================================================

@bp_tickets.route("/<int:ticket_id>/service-items", methods=["GET"])
def list_service_items(ticket_id: int):
    """获取工单的服务明细行"""
    svc = inject_service("ticket_service")
    items = svc.get_service_items(ticket_id)
    return jsonify({"service_items": items})


@bp_tickets.route("/<int:ticket_id>/service-items", methods=["POST"])
def add_service_item(ticket_id: int):
    """添加服务明细行"""
    data = request.get_json() or {}
    svc = inject_service("ticket_service")
    name = (data.get("name") or "").strip()
    technician = (data.get("technician_name") or "").strip()
    fee_id = data.get("service_fee_id")
    if not technician and not fee_id:
        return jsonify({"error": "请选择服务人员或服务项目"}), 400
    data = svc.calc_service_item_totals(data)
    item_id = svc.add_service_item_raw(
        ticket_id, technician, fee_id, data["hours"],
        data["unit_price"], data["cost_price"],
        data["line_total"], data["line_cost"], name=name)
    svc.recalc_ticket_total(ticket_id)
    return jsonify({"message": "服务明细已添加", "id": item_id})


@bp_tickets.route("/<int:ticket_id>/service-items/<int:item_id>", methods=["PUT"])
def update_service_item(ticket_id: int, item_id: int):
    """更新服务明细行"""
    data = request.get_json() or {}
    svc = inject_service("ticket_service")
    if data.get("hours") is not None or data.get("unit_price") is not None:
        data = svc.calc_service_item_totals(data)
    svc.update_service_item_raw(item_id, data)
    svc.recalc_ticket_total(ticket_id)
    return jsonify({"message": "已更新"})


@bp_tickets.route("/<int:ticket_id>/service-items/<int:item_id>", methods=["DELETE"])
def delete_service_item(ticket_id: int, item_id: int):
    """删除服务明细行"""
    svc = inject_service("ticket_service")
    svc.delete_service_item_raw(item_id)
    svc.recalc_ticket_total(ticket_id)
    return jsonify({"message": "已删除"})


@bp_tickets.route("/<int:ticket_id>/service-items/batch", methods=["POST"])
def batch_save_service_items(ticket_id: int):
    """批量保存服务明细行（先删后插，全量替换）"""
    data = request.get_json() or {}
    items = data.get("items", [])
    if not isinstance(items, list):
        return jsonify({"error": "items 必须为数组"}), 400
    svc = inject_service("ticket_service")
    result = svc.batch_save_service_items(ticket_id, items)
    return jsonify(result)


def _get_ticket_due_amount(ticket: dict) -> float:
    return inject_service("ticket_service").get_ticket_due_amount(ticket)


# ============================================================
# 关联设备
# ============================================================

@bp_tickets.route("/<int:ticket_id>/link-equipment", methods=["POST"])
def link_equipment(ticket_id: int):
    """关联设备到工单"""
    svc = inject_service("ticket_service")
    data = request.get_json()
    equip_id = (data or {}).get("equipment_id")
    if not equip_id:
        return jsonify({"error": "请提供设备ID"}), 400
    try:
        equip = svc.link_equipment(ticket_id, int(equip_id))
        return jsonify({"message": f"已关联设备: {equip['name']}"})
    except Exception as e:
        return jsonify({"error": f"关联设备失败: {str(e)}"}), 400


# ============================================================
# 折扣管理
# ============================================================

@bp_tickets.route("/<int:ticket_id>/discount", methods=["PUT"])
def set_discount(ticket_id: int):
    """结算时设置工单优惠折扣"""
    data = request.get_json() or {}
    discount_type = data.get("discount_type", "")
    discount_value = float(data.get("discount_value", 0))
    try:
        svc = inject_service("ticket_service")
        result = svc.set_discount(ticket_id, discount_type, discount_value)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp_tickets.route("/<int:ticket_id>/equipment/<int:equip_id>", methods=["DELETE"])
def unlink_equipment(ticket_id: int, equip_id: int):
    """取消关联设备"""
    svc = inject_service("ticket_service")
    svc.unlink_equipment(ticket_id, equip_id)
    return jsonify({"message": "已取消关联"})


# ============================================================
# 工时计时器
# ============================================================

@bp_tickets.route("/<int:ticket_id>/timer/start", methods=["POST"])
def timer_start(ticket_id: int):
    """开始工时计时（DB 持久化）"""
    svc = inject_service("ticket_service")
    ticket = svc.get_ticket(ticket_id)
    if not ticket:
        return jsonify({"error": "工单不存在"}), 404
    now = datetime.now()
    _set_timer_start(ticket_id, now)
    return jsonify({"message": "计时已开始", "started_at": now.isoformat()})


@bp_tickets.route("/<int:ticket_id>/timer/stop", methods=["POST"])
def timer_stop(ticket_id: int):
    """停止工时计时，自动累加实际工时"""
    start_time = _get_timer_start(ticket_id)
    if not start_time:
        return jsonify({"error": "没有正在运行的计时器"}), 400

    _clear_timer(ticket_id)
    try:
        svc = inject_service("ticket_service")
        result = svc.stop_timer(ticket_id, start_time)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@bp_tickets.route("/<int:ticket_id>/timer/status", methods=["GET"])
def timer_status(ticket_id: int):
    """查询计时器状态"""
    start_time = _get_timer_start(ticket_id)
    if not start_time:
        return jsonify({"running": False, "message": "计时器未启动"})
    running_seconds = round((datetime.now() - start_time).total_seconds())
    return jsonify({
        "running": True,
        "started_at": start_time.isoformat(),
        "elapsed_seconds": running_seconds,
        "elapsed_hours": round(running_seconds / 3600, 2),
    })


# ============================================================
# 操作日志
# ============================================================

@bp_tickets.route("/<int:ticket_id>/history", methods=["GET"])
def ticket_history(ticket_id: int):
    """获取工单操作日志"""
    history = inject_service("ticket_service").get_history(ticket_id)
    return jsonify({"history": history})


# ============================================================
# NLP 解析
# ============================================================

@bp_tickets.route("/parse", methods=["POST"])
def parse_ticket():
    """增强自然语言解析"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "请提供自然语言描述"}), 400

    parsed = svc.parse_natural_language(text)
    if "error" in parsed:
        return jsonify(parsed), 400

    client = parsed.get("client", "")
    if client:
        client_svc = inject_service("client_service")
        exist = client_svc.get_client(client) if client_svc and hasattr(client_svc, 'get_client') else None
        if not exist:
            try:
                clients = client_svc.list_clients() if hasattr(client_svc, 'list_clients') else []
                matches = [c for c in clients if client.lower() in (c.get("name", "") or "").lower()]
                if matches:
                    exist = matches[0]
            except Exception:
                pass
        if exist:
            parsed["client"] = exist["name"] if isinstance(exist, dict) else exist
            parsed["_client_matched"] = True
        else:
            parsed["_client_matched"] = False

    return jsonify({
        "parsed": parsed,
        "summary": f"解析结果：客户「{parsed.get('client','?')}」，内容「{parsed.get('content','')}」"
                   f"，优先级「{parsed.get('priority','M')}」",
        "suggestions": _get_parse_suggestions(parsed),
    })


# ============================================================
# 安全删除（确认模式）
# ============================================================

@bp_tickets.route("/<int:ticket_id>/confirm-delete", methods=["GET"])
def confirm_delete_preview(ticket_id: int):
    """预览删除效果（确认模式）"""
    svc = inject_service("ticket_service")
    try:
        result = svc.confirm_delete_preview(ticket_id)
    except TicketNotFoundError:
        return jsonify({"error": "工单不存在"}), 404
    return jsonify(result)


@bp_tickets.route("/<int:ticket_id>/confirm-delete", methods=["POST"])
def confirm_delete_execute(ticket_id: int):
    """确认执行删除"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    confirm_id = data.get("confirm_id", "")

    try:
        result = svc.confirm_delete_execute(ticket_id, confirm_id)
    except TicketValidationError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(result)


# ============================================================
# 批量操作（预览+确认）
# ============================================================

@bp_tickets.route("/batch-preview", methods=["POST"])
def batch_preview():
    """预览批量操作效果"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    action = data.get("action", "")
    ids = data.get("ids", [])
    if not action or not ids:
        return jsonify({"error": "请提供操作类型和工单ID列表"}), 400

    tickets_info = []
    for raw_id in ids:
        try:
            tid = int(raw_id)
            t = svc.get_ticket(tid)
            if t:
                tickets_info.append({
                    "id": tid, "ticket_no": t["ticket_no"],
                    "client": t["client"], "status": t["status"],
                    "status_name": svc.STATUS_NAMES.get(t.get("status"), ""),
                })
        except (ValueError, TypeError):
            pass

    if not tickets_info:
        return jsonify({"error": "未找到有效工单"}), 404

    total_amount = sum(
        float(svc.get_ticket(t["id"]).get("total", 0) or 0)
        for t in tickets_info
    )

    confirm_id = f"batch_{action}_{int(datetime.now().timestamp())}"
    svc.store_confirmation(confirm_id, {
        "action": f"batch_{action}",
        "ids": ids,
        "expires_at": datetime.now().timestamp() + 300,
    })

    return jsonify({
        "confirm_id": confirm_id,
        "action": action,
        "tickets": tickets_info,
        "count": len(tickets_info),
        "total_amount": round(total_amount, 2),
        "summary": f"即将对 {len(tickets_info)} 单工单执行「{action}」操作",
        "confirmation_required": True,
        "confirm_url": "/api/v1/tickets/batch-confirm",
        "expires_in_seconds": 300,
    })


@bp_tickets.route("/batch-confirm", methods=["POST"])
def batch_confirm():
    """确认执行批量操作"""
    svc = inject_service("ticket_service")
    data = request.get_json() or {}
    confirm_id = data.get("confirm_id", "")

    confirmation = svc.pop_confirmation(confirm_id)
    if not confirm_id or not confirmation:
        return jsonify({"error": "确认ID无效或已过期，请重新预览"}), 400

    if confirmation["expires_at"] < datetime.now().timestamp():
        return jsonify({"error": "确认已过期（5分钟），请重新预览"}), 400

    action = confirmation["action"].replace("batch_", "")
    ids = confirmation["ids"]

    target_status = data.get("target_status")
    result = svc.batch_execute_action(ids, action, target_status)

    svc.cleanup_expired_confirmations()
    return jsonify(result)


# ============================================================
# 批量筛选操作
# ============================================================

@bp_tickets.route("/batch-by-filter", methods=["POST"])
def batch_by_filter():
    """按筛选条件批量操作工单"""
    data = request.get_json() or {}
    action = data.get("action", "")
    filters = data.get("filter", {})
    target_status = data.get("target_status")

    try:
        svc = inject_service("ticket_service")
        result = svc.batch_by_filter(action, filters, target_status)
        if "error" in result and "matched_count" in result:
            return jsonify(result), 404
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ============================================================
# 工单变更 Delta + 时间线
# ============================================================

@bp_tickets.route("/<int:ticket_id>/delta", methods=["GET"])
def ticket_delta(ticket_id: int):
    """获取工单变更 Delta 信息"""
    try:
        svc = inject_service("ticket_service")
        result = svc.get_ticket_delta(ticket_id)
        return jsonify(result)
    except ValueError:
        return jsonify({"error": "工单不存在"}), 404


@bp_tickets.route("/<int:ticket_id>/timeline", methods=["GET"])
def ticket_timeline(ticket_id: int):
    """工单时间线（与 delta 同逻辑，兼容 Vue SPA 调用）"""
    return ticket_delta(ticket_id)


# ===== 状态流转（新架构扩展端点） =====

@bp_tickets.route("/<int:ticket_id>/status", methods=["PUT"])
def transition_status(ticket_id: int):
    """状态流转（支持 note 参数）"""
    svc = inject_service("ticket_service")
    try:
        data = request.get_json(force=True, silent=True) or {}
        new_status = data.get("status", "")
        note = data.get("note", "")
        if not new_status:
            return ApiResponse.bad_request("请指定目标状态")
        ticket = svc.transition_status(ticket_id, new_status, note=note)
        return ApiResponse.success(ticket, message="状态已变更")
    except TicketValidationError as e:
        return ApiResponse.bad_request(str(e))
    except TicketNotFoundError as e:
        return ApiResponse.not_found(str(e))
    except Exception as e:
        logger.error(f"transition_status error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_tickets.route("/<int:ticket_id>/pay", methods=["POST"])
def pay_ticket(ticket_id: int):
    """确认收款（使用新架构服务）"""
    svc = inject_service("ticket_service")
    try:
        data = request.get_json(force=True, silent=True) or {}
        amount = float(data.get("amount", 0))
        method = data.get("method", "微信")
        note = data.get("note", "")
        ticket = svc.confirm_payment(ticket_id, amount, method, note)
        return ApiResponse.success(ticket, message="收款成功")
    except TicketValidationError as e:
        return ApiResponse.bad_request(str(e))
    except TicketNotFoundError as e:
        return ApiResponse.not_found(str(e))
    except Exception as e:
        logger.error(f"pay_ticket error: {e}", exc_info=True)
        return ApiResponse.server_error()


# ===== 自动化规则 =====

@bp_tickets.route("/rules", methods=["GET"])
def list_rules():
    svc = inject_service("ticket_service")
    rules = svc.list_rules()
    return ApiResponse.success(rules)


@bp_tickets.route("/rules", methods=["POST"])
def create_rule():
    svc = inject_service("ticket_service")
    data = request.get_json(force=True, silent=True) or {}
    svc.create_rule(**data)
    return ApiResponse.success(message="规则已创建")


@bp_tickets.route("/rules/<int:rid>", methods=["GET"])
def get_rule(rid):
    svc = inject_service("ticket_service")
    rule = svc.get_rule(rid)
    if not rule:
        return ApiResponse.not_found("规则不存在")
    return ApiResponse.success(rule)


@bp_tickets.route("/rules/<int:rid>", methods=["PUT"])
def update_rule(rid):
    svc = inject_service("ticket_service")
    data = request.get_json(force=True, silent=True) or {}
    svc.update_rule(rid, data)
    return ApiResponse.success(message="规则已更新")


@bp_tickets.route("/rules/<int:rid>", methods=["DELETE"])
def delete_rule(rid):
    svc = inject_service("ticket_service")
    svc.delete_rule(rid)
    return ApiResponse.success(message="规则已删除")


@bp_tickets.route("/rules/<int:rid>/toggle", methods=["POST"])
def toggle_rule(rid):
    svc = inject_service("ticket_service")
    new_val = svc.toggle_rule(rid)
    if new_val is None:
        return ApiResponse.not_found("规则不存在")
    return ApiResponse.success({"enabled": new_val})


@bp_tickets.route("/rules/seed", methods=["POST"])
def seed_rules():
    svc = inject_service("ticket_service")
    count = svc.seed_default_rules()
    return ApiResponse.success({"seeded": count}, message=f"已预置 {count} 条默认规则")


@bp_tickets.route("/rules/execute", methods=["POST"])
def execute_rules():
    svc = inject_service("ticket_service")
    data = request.get_json(force=True, silent=True) or {}
    event_name = data.get("event", "")
    context = data.get("context", {})
    if not event_name:
        return ApiResponse.bad_request("缺少 event 参数")
    results = svc.execute_rules_for_event(event_name, context)
    return ApiResponse.success(results)


# ===== 注册到应用 =====

def register_blueprint(app):
    """注册 Blueprint 到 Flask 应用"""
    app.register_blueprint(bp_tickets)
    logger.info("API v1 工单完整端点已注册 (Blueprint)")
