"""
博通 — 商品目录 API v1
"""

import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_goods = Blueprint('api_v1_goods', __name__, url_prefix='/api/v1/goods')


@bp_goods.route("/", strict_slashes=False)
def list_goods():
    svc = inject_service("goods_service")
    mode = request.args.get("mode")
    q = request.args.get("q")
    return jsonify(svc.list_with_summary(mode=mode, q=q))


@bp_goods.route("/", methods=["POST"], strict_slashes=False)
def create_goods():
    """创建商品"""
    svc = inject_service("goods_service")
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "请提供商品名称"}), 400
    result = svc.create_goods(data)
    return jsonify({"message": result["message"]}), 201


@bp_goods.route("/<int:goods_id>")
def get_goods(goods_id: int):
    """获取商品详情"""
    svc = inject_service("goods_service")
    try:
        goods = svc.get_goods(goods_id)
        return jsonify({"goods": goods})
    except Exception:
        return jsonify({"error": "商品不存在"}), 404


@bp_goods.route("/<int:goods_id>", methods=["PUT"])
def update_goods(goods_id: int):
    """更新商品"""
    svc = inject_service("goods_service")
    data = request.get_json() or {}
    result = svc.update_goods(goods_id, **data)
    return jsonify({"message": result.get("message", "已更新")})


@bp_goods.route("/<int:goods_id>", methods=["DELETE"])
def delete_goods(goods_id: int):
    """删除商品"""
    svc = inject_service("goods_service")
    result = svc.delete_goods(goods_id)
    return jsonify({"message": result["message"]})


# ── 分类管理 ──

@bp_goods.route("/categories")
def list_categories():
    """获取分类列表"""
    svc = inject_service("goods_service")
    cats = svc.list_categories()
    return jsonify({"categories": cats})


@bp_goods.route("/categories", methods=["POST"])
def create_category():
    """创建分类"""
    svc = inject_service("goods_service")
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "请提供分类名称"}), 400
    result = svc.create_category(
        name=name, icon=data.get("icon", ""),
        sort_order=int(data.get("sort_order", 99)))
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@bp_goods.route("/categories/<int:cat_id>")
def get_category(cat_id: int):
    """获取分类详情"""
    svc = inject_service("goods_service")
    cat = svc.get_category(cat_id)
    if not cat:
        return jsonify({"error": "分类不存在"}), 404
    return jsonify({"category": cat})


@bp_goods.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id: int):
    """更新分类"""
    svc = inject_service("goods_service")
    data = request.get_json() or {}
    result = svc.update_category(cat_id, **data)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@bp_goods.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id: int):
    """删除分类"""
    svc = inject_service("goods_service")
    result = svc.delete_category(cat_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


# ── 类型管理 ──

@bp_goods.route("/categories/<int:cat_id>/types")
def list_types_by_category(cat_id: int):
    """获取分类下的类型列表"""
    svc = inject_service("goods_service")
    types = svc.list_types(category_id=cat_id)
    return jsonify({"types": types})


@bp_goods.route("/categories/<int:cat_id>/types", methods=["POST"])
def create_type_in_category(cat_id: int):
    """在分类下创建类型"""
    svc = inject_service("goods_service")
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "请提供类型名称"}), 400
    result = svc.create_type(
        category_id=cat_id, name=name,
        sort_order=int(data.get("sort_order", 99)))
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@bp_goods.route("/types")
def list_all_types():
    """获取所有类型列表"""
    svc = inject_service("goods_service")
    types = svc.list_types()
    return jsonify({"types": types})


@bp_goods.route("/types", methods=["POST"])
def create_type():
    """创建类型"""
    svc = inject_service("goods_service")
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    category_id = data.get("category_id")
    if not name:
        return jsonify({"error": "请提供类型名称"}), 400
    if not category_id:
        return jsonify({"error": "请提供所属分类ID"}), 400
    result = svc.create_type(
        category_id=int(category_id), name=name,
        sort_order=int(data.get("sort_order", 99)))
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@bp_goods.route("/types/<int:type_id>", methods=["PUT"])
def update_type(type_id: int):
    """更新类型"""
    svc = inject_service("goods_service")
    data = request.get_json() or {}
    result = svc.update_type(type_id, **data)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@bp_goods.route("/types/<int:type_id>", methods=["DELETE"])
def delete_type(type_id: int):
    """删除类型"""
    svc = inject_service("goods_service")
    result = svc.delete_type(type_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


def register_blueprint(app):
    app.register_blueprint(bp_goods)
    logger.info("API v1 商品目录端点已注册")
