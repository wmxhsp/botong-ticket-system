import logging
from flask import Blueprint, request, jsonify
from infrastructure.di.service_injection import inject_service
from api.v1.responses import ApiResponse

logger = logging.getLogger(__name__)

bp_search = Blueprint('api_v1_search', __name__, url_prefix='/api/v1')


@bp_search.route("/search")
def global_search():
    search_svc = inject_service("search_service")
    q = (request.args.get("q") or "").strip()
    result = search_svc.global_search(q)
    return ApiResponse.success(result)


def register_blueprint(app):
    app.register_blueprint(bp_search)
    logger.info("API v1 搜索端点已注册")
