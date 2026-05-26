"""
博通 — 设备 API v1
"""

import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service
from api.validators import validate_json
from api.validators.schemas import EquipmentCreateSchema

logger = logging.getLogger(__name__)

bp_equipment = Blueprint('api_v1_equipment', __name__, url_prefix='/api/v1/equipment')

_ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_MAX_UPLOAD_SIZE = 10 * 1024 * 1024

def _validate_image_upload(file_storage):
    if file_storage.mimetype not in _ALLOWED_IMAGE_MIMES:
        return False, f"不支持的文件类型: {file_storage.mimetype}"
    file_storage.seek(0, 2)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > _MAX_UPLOAD_SIZE:
        return False, f"文件过大: {size} bytes"
    return True, ""



@bp_equipment.route("/", strict_slashes=False)
def list_equipment():
    """设备列表（支持 search/status/client 筛选）"""
    svc = inject_service("equipment_service")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 50))
    search = request.args.get("search", request.args.get("q", ""))
    status = request.args.get("status", "")
    result = svc.list_equipment(page=page, page_size=page_size, search=search, status=status)
    items = result.get("items", result.get("equipment", result if isinstance(result, list) else []))
    total = result.get("total", len(items)) if isinstance(result, dict) else len(items)
    return jsonify({"equipment": items, "total": total, "page": page})


@bp_equipment.route("/", methods=["POST"], strict_slashes=False)
@validate_json(EquipmentCreateSchema)
def create_equipment(body: EquipmentCreateSchema):
    """创建设备"""
    svc = inject_service("equipment_service")
    equip = svc.create_equipment(body.model_dump())
    return jsonify({"message": "设备已创建", "equipment": equip}), 201


@bp_equipment.route("/<int:equip_id>")
def get_equipment(equip_id: int):
    """设备详情"""
    svc = inject_service("equipment_service")
    equip = svc.get_equipment_detail(equip_id)
    if not equip:
        return jsonify({"error": "设备不存在"}), 404
    return jsonify(equip)


@bp_equipment.route("/<int:equip_id>", methods=["PUT"])
def update_equipment(equip_id: int):
    """更新设备"""
    svc = inject_service("equipment_service")
    data = request.get_json() or {}
    result = svc.update_equipment(equip_id, **data)
    return jsonify(result if isinstance(result, dict) else {"message": "已更新"})


@bp_equipment.route("/<int:equip_id>", methods=["DELETE"])
def delete_equipment(equip_id: int):
    """删除设备"""
    svc = inject_service("equipment_service")
    result = svc.delete_equipment(equip_id)
    return jsonify(result if isinstance(result, dict) else {"message": "已删除"})


# ── 批量操作 ──

@bp_equipment.route("/batch/delete", methods=["POST"])
def batch_delete_equipment():
    """批量删除"""
    svc = inject_service("equipment_service")
    data = request.get_json() or {}
    ids = data.get("ids", [])
    if not ids:
        return jsonify({"error": "请提供设备ID列表"}), 400
    result = svc.batch_delete(ids)
    return jsonify(result if isinstance(result, dict) else {"message": f"已删除 {len(ids)} 台设备"})


@bp_equipment.route("/batch/restore", methods=["POST"])
def batch_restore_equipment():
    """批量恢复"""
    svc = inject_service("equipment_service")
    data = request.get_json() or {}
    ids = data.get("ids", [])
    if not ids:
        return jsonify({"error": "请提供设备ID列表"}), 400
    result = svc.batch_restore(ids)
    return jsonify(result if isinstance(result, dict) else {"message": f"已恢复 {len(ids)} 台设备"})


@bp_equipment.route("/batch/qr-urls", methods=["POST"])
def batch_qr_urls():
    """批量获取QR码"""
    svc = inject_service("equipment_service")
    data = request.get_json() or {}
    ids = data.get("ids", [])
    if not ids:
        return jsonify({"error": "请提供设备ID列表"}), 400
    base_url = request.host_url.rstrip("/")
    result = svc.batch_get_qr_urls(ids, base_url)
    return jsonify({"urls": result})


@bp_equipment.route("/<int:equip_id>/restore", methods=["POST"])
def restore_equipment(equip_id: int):
    """恢复已删除设备"""
    svc = inject_service("equipment_service")
    result = svc.restore_equipment(equip_id)
    return jsonify(result if isinstance(result, dict) else {"message": "已恢复"})


# ── 照片 ──

@bp_equipment.route("/<int:equip_id>/photos")
def list_equipment_photos(equip_id: int):
    """获取设备照片"""
    svc = inject_service("equipment_service")
    photos = svc.get_equipment_photos(equip_id) if hasattr(svc, 'get_equipment_photos') else []
    return jsonify({"photos": photos})


@bp_equipment.route("/<int:equip_id>/photos", methods=["POST"])
def upload_equipment_photo(equip_id: int):
    """上传设备照片"""
    if "photo" not in request.files:
        return jsonify({"error": "请选择照片"}), 400
    photo = request.files["photo"]
    ok, err = _validate_image_upload(photo)
    if not ok:
        return jsonify({"error": err}), 400
    from pathlib import Path
    from datetime import datetime
    import os
    base = Path(__file__).resolve().parent.parent.parent
    upload_dir = base / "static" / "uploads" / "equipment" / str(equip_id)
    os.makedirs(str(upload_dir), exist_ok=True)
    filename = f"eq_{equip_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = f"static/uploads/equipment/{equip_id}/{filename}"
    photo.save(str(upload_dir / filename))
    svc = inject_service("equipment_service")
    if hasattr(svc, 'add_equipment_photo'):
        svc.add_equipment_photo(equip_id, filepath, 'image')
    return jsonify({"message": "照片已上传", "filepath": f"/{filepath}"})


@bp_equipment.route("/<int:equip_id>/photos", methods=["DELETE"])
def delete_equipment_photo(equip_id: int):
    """删除设备照片"""
    from pathlib import Path
    import os
    base = Path(__file__).resolve().parent.parent.parent
    svc = inject_service("equipment_service")
    data = request.get_json() or {}
    photo_id = data.get("id")
    filepath = data.get("filepath", "")
    if photo_id and hasattr(svc, 'delete_equipment_photo'):
        svc.delete_equipment_photo(photo_id, equip_id)
        return jsonify({"message": "照片已删除"})
    if filepath and hasattr(svc, 'delete_equipment_photo_by_path'):
        svc.delete_equipment_photo_by_path(filepath, equip_id)
        return jsonify({"message": "照片已删除"})
    return jsonify({"error": "请提供照片ID"}), 400


@bp_equipment.route("/<int:equip_id>/photos/settings", methods=["PUT"])
def update_equipment_photo_settings(equip_id: int):
    """更新照片设置"""
    data = request.get_json() or {}
    photo_id = data.get("id")
    if not photo_id:
        return jsonify({"error": "请提供照片ID"}), 400
    is_cover = data.get("is_cover", 0)
    svc = inject_service("equipment_service")
    if hasattr(svc, 'update_equipment_photo_cover'):
        svc.update_equipment_photo_cover(photo_id, equip_id, int(is_cover))
    return jsonify({"message": "已更新"})


@bp_equipment.route("/<int:equip_id>/photos/batch", methods=["POST"])
def batch_upload_equipment_photos(equip_id: int):
    """批量上传照片"""
    photos = request.files.getlist("photos")
    if not photos:
        return jsonify({"error": "请选择照片"}), 400
    uploaded = []
    for photo in photos:
        data = request.get_json() or {}
        r = upload_equipment_photo(equip_id)
        if r.status_code == 200:
            uploaded.append(r.get_json().get("filepath", ""))
    return jsonify({"message": f"已上传 {len(uploaded)} 张照片", "files": uploaded})


# ── 关联工单 ──

@bp_equipment.route("/<int:equip_id>/tickets")
def equipment_tickets(equip_id: int):
    """获取关联工单"""
    svc = inject_service("equipment_service")
    tickets = svc.get_equipment_tickets(equip_id)
    return jsonify({"tickets": tickets})


# ── 维保 ──

@bp_equipment.route("/maintenance/summary")
def maintenance_summary():
    """维保统计"""
    svc = inject_service("equipment_service")
    return jsonify(svc.get_maintenance_summary())


@bp_equipment.route("/maintenance/overdue")
def maintenance_overdue():
    """逾期待维保"""
    svc = inject_service("equipment_service")
    days = int(request.args.get("days", 30))
    items = svc.get_overdue_maintenance(days)
    return jsonify({"items": items})


@bp_equipment.route("/<int:equip_id>/maintenance/record", methods=["POST"])
def record_maintenance(equip_id: int):
    """记录维保"""
    svc = inject_service("equipment_service")
    data = request.get_json() or {}
    svc.record_maintenance(equip_id, data.get("content", ""))
    return jsonify({"message": "维保记录已保存"})


@bp_equipment.route("/<int:equip_id>/maintenance/history")
def maintenance_history(equip_id: int):
    """维保历史"""
    svc = inject_service("equipment_service")
    history = svc.get_maintenance_history(equip_id)
    return jsonify({"history": history})


@bp_equipment.route("/<int:equip_id>/timeline")
def equipment_timeline(equip_id: int):
    """设备时间线"""
    svc = inject_service("equipment_service")
    timeline = svc.get_status_timeline(equip_id)
    return jsonify({"timeline": timeline})


@bp_equipment.route("/maintenance/report")
def maintenance_report():
    """维保报告"""
    svc = inject_service("equipment_service")
    summary = svc.get_maintenance_summary()
    overdue = svc.get_overdue_maintenance(30)
    return jsonify({"summary": summary, "overdue": overdue})


# ── 组件 ──

@bp_equipment.route("/<int:equip_id>/components")
def list_components(equip_id: int):
    """获取组件列表"""
    svc = inject_service("equipment_service")
    components = svc.list_components(equip_id)
    return jsonify({"components": components})


@bp_equipment.route("/<int:equip_id>/components", methods=["POST"])
def add_component(equip_id: int):
    """添加组件"""
    svc = inject_service("equipment_service")
    data = request.get_json() or {}
    comp = svc.add_component(equip_id, data.get("name", ""), data.get("spec", ""), int(data.get("count", 1)))
    return jsonify({"message": "组件已添加", "component": comp}), 201


@bp_equipment.route("/<int:equip_id>/components/<int:comp_id>", methods=["PUT"])
def update_component(equip_id: int, comp_id: int):
    """更新组件"""
    svc = inject_service("equipment_service")
    data = request.get_json() or {}
    result = svc.update_component(comp_id, **data)
    return jsonify(result if isinstance(result, dict) else {"message": "已更新"})


@bp_equipment.route("/<int:equip_id>/components/<int:comp_id>", methods=["DELETE"])
def delete_component(equip_id: int, comp_id: int):
    """删除组件"""
    svc = inject_service("equipment_service")
    svc.delete_component(comp_id)
    return jsonify({"message": "已删除"})


# ── QR码 ──

@bp_equipment.route("/<int:equip_id>/qrcode")
def equipment_qrcode(equip_id: int):
    """生成QR码图片"""
    import qrcode as _qr
    from io import BytesIO
    import base64
    url = f"{request.host_url.rstrip('/')}/equipment/{equip_id}"
    img = _qr.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return jsonify({"qr_png_base64": b64, "url": url})


# ── 导入模板 ──

@bp_equipment.route("/import-template")
def import_template():
    """下载CSV导入模板"""
    import csv
    from io import StringIO
    from flask import Response
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["名称", "序列号", "型号", "客户", "位置", "状态"])
    writer.writerow(["示例电脑", "SN001", "ThinkPad X1", "客户A", "三楼办公室", "正常"])
    return Response(output.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=equipment_template.csv"})


def register_blueprint(app):
    app.register_blueprint(bp_equipment)
    logger.info("API v1 设备端点已注册")
