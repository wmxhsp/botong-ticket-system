"""
博通 (Botong) — Flask 应用工厂

create_app() 按顺序执行:
  1. Flask 实例 + 配置
  2. 日志系统
  3. 中间件（认证/CSRF/限流）
  4. Flask-Caching
  5. Flask-RESTx API（Swagger）
  6. DI 容器 + 事件总线 + 任务队列
  7. 路由注册（Web / Auth / PWA / SPA / API）
  8. 全局错误处理器
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_app(testing=False):
    from flask import Flask, jsonify, request, send_from_directory
    from flask_restx import Api, fields, Resource

    # ===== 加载 .env（仅限开发环境，不影响已设置的环境变量）=====
    if not testing:
        try:
            from dotenv import load_dotenv
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_path = os.path.join(base_dir, ".env")
            if os.path.isfile(env_path):
                load_dotenv(env_path, override=False)
                logger.debug("已加载 .env: %s", env_path)
        except ImportError:
            pass

    # ===== Flask 实例 =====
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__, template_folder=os.path.join(base_dir, "templates"),
                static_folder=os.path.join(base_dir, "static"))
    _secret_key = os.environ.get("BOTO_SECRET_KEY")
    if not _secret_key:
        if testing:
            _secret_key = "test-secret-key-for-testing-only"
            logger.warning("⚠️ 使用测试密钥（仅限测试环境）")
        else:
            raise RuntimeError(
                "❌ BOTO_SECRET_KEY 环境变量未设置！\n"
                "必须设置密钥（无论开发还是生产环境）。\n"
                "示例: export BOTO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
            )
    app.secret_key = _secret_key

    # ===== 配置 =====
    app.config["BOTO_BASE_DIR"] = base_dir
    app.config.setdefault("BOTO_PORT", 5053)
    app.config.setdefault("BOTO_DEBUG", os.environ.get("BOTO_DEBUG", "0") == "1")
    app.config.setdefault("BOTO_NO_RATE_LIMIT", bool(os.environ.get("BOTO_NO_RATE_LIMIT")))
    app.config.setdefault("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)

    # ===== 日志 =====
    _setup_logging(app)

    # ===== 速率限制 =====
    limiter = None
    if not app.config["BOTO_NO_RATE_LIMIT"]:
        limiter = _setup_rate_limit(app)

    # ===== 中间件 =====
    _setup_middleware(app, base_dir)

    # ===== Flask-Caching =====
    _setup_cache(app)

    # ===== Flask-RESTx API =====
    api = Api(app, version="3.0", title="博通 API",
              description="博通售后管理系统 - Botong",
              doc="/docs/", prefix="/api")

    # ===== Swagger 模型 =====
    _register_swagger_models(api)

    # ===== 服务注入 =====
    from infrastructure.di.service_locator import reg
    reg.init(app=app, api=api)
    reg.limiter = limiter

    # ===== 新架构引导（DI 容器 + EventBus + 任务队列） =====
    _setup_di_bootstrap(app)

    # ===== 路由注册 =====
    _register_routes(app, api, base_dir)

    # ===== 错误处理器 =====
    _setup_error_handlers(app)

    # ===== Jinja2 全局 =====
    app.jinja_env.globals["app_js"] = lambda: ""

    return app


# ── 内部函数 ──

def _setup_logging(app):
    try:
        from logging.handlers import TimedRotatingFileHandler
        handler = TimedRotatingFileHandler(
            "/tmp/boto-app.log", when="midnight", backupCount=7, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
        ))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
    except Exception:
        pass


def _setup_rate_limit(app):
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        limiter = Limiter(
            app=app, key_func=get_remote_address,
            default_limits=["200000 per day", "30000 per hour"],
            storage_uri="memory://",
        )
        return limiter
    except Exception as e:
        logger.warning("速率限制不可用: %s", e)
        return None


def _setup_middleware(app, base_dir):
    try:
        from web.middleware.auth import init_auth
        init_auth(app, base_dir=base_dir)
    except Exception as e:
        logger.error("认证初始化失败: %s", e)
        raise

    try:
        from web.middleware.csrf import init_csrf
        init_csrf(app)
    except Exception as e:
        logger.warning("CSRF 初始化失败: %s", e)


def _setup_cache(app):
    try:
        from flask_caching import Cache
        from infrastructure.di.container import Container
        cache_config = {
            "CACHE_TYPE": os.environ.get("BOTO_CACHE_TYPE", "SimpleCache"),
            "CACHE_DEFAULT_TIMEOUT": 300,
        }
        if "Redis" in cache_config["CACHE_TYPE"]:
            cache_config["CACHE_REDIS_URL"] = os.environ.get("BOTO_REDIS_URL", "redis://localhost:6379/1")
        cache = Cache(app, config=cache_config)
        app.extensions["cache"] = cache
        Container.register_instance("cache", cache)
        logging.getLogger(__name__).info("✅ 缓存已注册")
    except Exception as e:
        logging.getLogger(__name__).warning("缓存初始化跳过: %s", e)


def _setup_di_bootstrap(app):
    try:
        from infrastructure.di.bootstrap import bootstrap as di_bootstrap
        di_bootstrap(flask_app=app, use_cache=False)
        logger.info("新架构（DI + 事件 + 任务队列）已启动")
    except Exception as e:
        logger.warning("新架构启动跳过: %s", e)


def _register_swagger_models(api):
    from flask_restx import fields, Resource

    ticket_model = api.model("Ticket", {
        "id": fields.Integer(readonly=True, description="工单 ID"),
        "ticket_no": fields.String(description="工单编号"),
        "client": fields.String(required=True, description="客户名称"),
        "content": fields.String(required=True, description="服务内容"),
        "status": fields.String(description="工单状态"),
        "status_name": fields.String(readonly=True, description="状态中文名"),
        "estimated_hours": fields.Float(description="预估工时"),
        "amount": fields.Float(description="工单金额"),
        "total": fields.Float(readonly=True, description="总金额"),
        "billing_status": fields.String(description="结算状态"),
        "created_at": fields.String(description="创建时间"),
        "closed_at": fields.String(description="完工时间"),
        "appointment_at": fields.String(description="预约时间"),
    })

    # 版本信息
    version_path = Path(__file__).parent.parent / "VERSION.json"
    try:
        version_info = json.loads(version_path.read_text())
    except Exception:
        version_info = {"version": "0.0.0", "name": "博通售后管理系统"}

    @api.route("/version")
    class VersionInfo(Resource):
        def get(self):
            return version_info


def _register_routes(app, api, base_dir):
    from flask import jsonify

        # ── Vue 3 SPA ──
    frontend_dist = os.path.join(base_dir, "frontend", "dist")

    # 提供 PWA 相关静态文件（sw.js / manifest.json）
    @app.route('/sw.js')
    def _sw_js():
        from flask import send_from_directory as _sfd
        filepath = os.path.join(frontend_dist, 'sw.js')
        if os.path.exists(filepath):
            resp = _sfd(frontend_dist, 'sw.js')
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return resp
        return jsonify({'error': 'not found'}), 404

    @app.route('/manifest.json')
    def _manifest():
        from flask import send_from_directory as _sfd
        filepath = os.path.join(frontend_dist, 'manifest.json')
        if os.path.exists(filepath):
            resp = _sfd(frontend_dist, 'manifest.json')
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return resp
        return jsonify({'error': 'not found'}), 404

    @app.route("/assets/<path:filename>")
    def _assets(filename):
        from flask import send_from_directory as _sfd
        assets_dir = os.path.join(frontend_dist, "assets")
        filepath = os.path.join(assets_dir, filename)
        if os.path.exists(filepath):
            resp = _sfd(assets_dir, filename)
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return resp
        return jsonify({'error': 'not found'}), 404

    @app.route("/app/")
    @app.route("/app/<path:subpath>")
    def _spa_index(subpath=None):
        from flask import send_from_directory as _sfd
        if subpath and subpath.startswith("assets/"):
            filepath = os.path.join(frontend_dist, subpath)
            if os.path.exists(filepath):
                resp = _sfd(frontend_dist, subpath)
                resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
                return resp
        resp = _sfd(frontend_dist, "index.html")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return resp

    # ── 认证路由 ──
    from web.auth_routes import register_auth_routes
    register_auth_routes(app)

    # ── Web 页面路由 ──
    from web.pages import register_routes as register_web_routes
    register_web_routes(app)


def _setup_error_handlers(app):
    from flask import jsonify
    from werkzeug.exceptions import HTTPException
    from domain.exceptions import (
        TicketNotFoundError, TicketValidationError, TicketStatusError, TicketAssignmentError,
        InventoryError, InventoryNotEnoughError, InventoryLockError,
        EquipmentError, EquipmentMaintenanceError,
        DatabaseError, ConfigError,
        BillingError, DuplicateBillingError,
        SaleError, PriceError, PaymentError, RefundError,
        TechnicianNotFoundError, TechnicianRateError,
        ClientNotFoundError, ClientCreditError,
        GoodsNotFoundError, GoodsStockError,
        SupplierNotFoundError,
        PurchaseOrderError, PurchaseOrderStatusError,
        WarehouseError, WarehouseStockError, StockTransferError,
        AuthorizationError, RateLimitError,
        ValidationError, ConcurrencyError, IdempotencyError,
    )

    @app.errorhandler(TicketNotFoundError)
    @app.errorhandler(ClientNotFoundError)
    @app.errorhandler(GoodsNotFoundError)
    @app.errorhandler(SupplierNotFoundError)
    @app.errorhandler(TechnicianNotFoundError)
    def handle_not_found(e):
        return jsonify({"code": 404, "success": False, "error": str(e)}), 404

    @app.errorhandler(TicketValidationError)
    @app.errorhandler(TicketStatusError)
    @app.errorhandler(TicketAssignmentError)
    @app.errorhandler(InventoryError)
    @app.errorhandler(InventoryNotEnoughError)
    @app.errorhandler(InventoryLockError)
    @app.errorhandler(EquipmentError)
    @app.errorhandler(EquipmentMaintenanceError)
    @app.errorhandler(BillingError)
    @app.errorhandler(DuplicateBillingError)
    @app.errorhandler(SaleError)
    @app.errorhandler(PriceError)
    @app.errorhandler(PaymentError)
    @app.errorhandler(RefundError)
    @app.errorhandler(TechnicianRateError)
    @app.errorhandler(ClientCreditError)
    @app.errorhandler(GoodsStockError)
    @app.errorhandler(PurchaseOrderError)
    @app.errorhandler(PurchaseOrderStatusError)
    @app.errorhandler(WarehouseError)
    @app.errorhandler(WarehouseStockError)
    @app.errorhandler(StockTransferError)
    @app.errorhandler(ValidationError)
    def handle_bad_request(e):
        return jsonify({"code": 400, "success": False, "error": str(e)}), 400

    @app.errorhandler(AuthorizationError)
    @app.errorhandler(RateLimitError)
    def handle_forbidden(e):
        return jsonify({"code": 403, "success": False, "error": str(e)}), 403

    @app.errorhandler(DatabaseError)
    @app.errorhandler(ConfigError)
    @app.errorhandler(ConcurrencyError)
    @app.errorhandler(IdempotencyError)
    def handle_server_error(e):
        app.logger.error("Domain error: %s", e, exc_info=True)
        return jsonify({"code": 500, "success": False, "error": "服务器内部错误"}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({"error": getattr(e, "description", "请求错误"), "code": e.code}), e.code
        app.logger.error("Unhandled exception: %s", e, exc_info=True)
        return jsonify({"error": "服务器内部错误，请稍后重试", "code": 500}), 500
