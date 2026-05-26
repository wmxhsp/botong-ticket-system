"""
博通 (Botong) — 应用启动引导
使用 DI 容器组装全部依赖，替换 app.py 中的手动初始化
"""

import logging
import importlib
import os
from typing import Optional

from infrastructure.di.container import Container
from domain.events import get_event_bus

logger = logging.getLogger(__name__)


def bootstrap(flask_app=None, use_events: bool = True, use_cache: bool = True):
    from config.manager import config as global_config
    from infrastructure.persistence.repositories.ticket_repo import SqliteTicketRepository
    from infrastructure.persistence.repositories.client_repo import SqliteClientRepository
    from infrastructure.persistence.repositories.finance_repo import SqliteFinanceRepository
    from infrastructure.persistence.repositories.todo_repo import SqliteTodoRepository
    from infrastructure.persistence.repositories.dashboard_repo import SqliteDashboardRepository
    from infrastructure.persistence.repositories.equipment_repo import SqliteEquipmentRepository
    from application.services.ticket_service import TicketService
    from application.services.client_service import ClientService as NewClientService
    from application.services.finance_service import FinanceService as NewFinanceService
    from application.services.todo_service import TodoService as NewTodoService
    from application.services.equipment_service import EquipmentService as NewEquipmentService
    from application.services.dashboard_service import DashboardService
    from application.services.reminder_service import ReminderService
    from application.services.inventory_service import InventoryService
    from application.services.supplier_service import SupplierService as AppSupplierService
    from application.services.goods_service import GoodsService as AppGoodsService
    from application.services.search_service import SearchService

    # 0. 初始化数据库表与索引
    try:
        from infrastructure.persistence.legacy_db import init_indexes
        init_indexes()
        logger.info("✅ 数据库表与索引已初始化")
    except Exception as e:
        logger.warning(f"数据库初始化失败: {e}")

    # 1. 配置
    Container.register_instance("settings", global_config)

    # 2. 事件总线
    if use_events:
        event_bus = get_event_bus()
        Container.register_instance("event_bus", event_bus)
    else:
        Container.register_instance("event_bus", None)

    # 3. 仓储
    Container.register("ticket_repo", lambda: SqliteTicketRepository())
    Container.register("client_repo", lambda: SqliteClientRepository())
    Container.register("finance_repo", lambda: SqliteFinanceRepository())
    Container.register("todo_repo", lambda: SqliteTodoRepository())
    Container.register("dashboard_repo", lambda: SqliteDashboardRepository())
    Container.register("equipment_repo", lambda: SqliteEquipmentRepository())

    from infrastructure.persistence.repositories.notification_repo import SqliteNotificationRepository
    from infrastructure.persistence.repositories.reminder_repo import SqliteReminderRepository
    from infrastructure.persistence.repositories.inventory_repo import SqliteInventoryRepository
    from infrastructure.persistence.repositories.goods_repo import GoodsRepo
    from infrastructure.persistence.repositories.technician_repo import TechnicianRepo
    from infrastructure.persistence.repositories.supplier_repo import SupplierRepo
    from infrastructure.persistence.repositories.service_fee_repo import ServiceFeeRepo
    from infrastructure.persistence.repositories.stats_repo import StatsRepo
    from infrastructure.persistence.repositories.purchase_repo import PurchaseRepo
    Container.register("notification_repo", lambda: SqliteNotificationRepository())
    Container.register("reminder_repo", lambda: SqliteReminderRepository())
    Container.register("inventory_repo", lambda: SqliteInventoryRepository())
    Container.register("goods_repo", lambda: GoodsRepo())
    Container.register("technician_repo", lambda: TechnicianRepo())
    Container.register("supplier_repo", lambda: SupplierRepo())
    Container.register("service_fee_repo", lambda: ServiceFeeRepo())
    Container.register("stats_repo", lambda: StatsRepo())
    Container.register("purchase_repo", lambda: PurchaseRepo())

    # 4. 服务层
    Container.register("technician_service", lambda: Container.resolve("technician_repo"))
    Container.register("goods_service", lambda: AppGoodsService(
        goods_repo=Container.resolve("goods_repo"),
    ))
    Container.register("supplier_service", lambda: AppSupplierService(
        supplier_repo=Container.resolve("supplier_repo"),
    ))
    Container.register("service_fee_service", lambda: Container.resolve("service_fee_repo"))
    Container.register("stats_service", lambda: Container.resolve("stats_repo"))

    Container.register("client_service", lambda: NewClientService(
        repo=Container.resolve("client_repo"),
        event_bus=Container.resolve("event_bus"),
    ))
    Container.register("equipment_service", lambda: NewEquipmentService(
        repo=Container.resolve("equipment_repo"),
        event_bus=Container.resolve("event_bus"),
    ))
    Container.register("ticket_service", lambda: TicketService(
        repo=Container.resolve("ticket_repo"),
        event_bus=Container.resolve("event_bus"),
        config=Container.resolve("settings"),
        client_service=Container.resolve("client_service"),
        finance_service=None,
        goods_service=Container.resolve("goods_service"),
        inventory_service=Container.resolve("inventory_service"),
        equipment_service=Container.resolve("equipment_service"),
        technician_service=Container.resolve("technician_service"),
        technician_repo=Container.resolve("technician_repo"),
        reminder_service=None,
        todo_service=None,
    ))
    Container.register("finance_service", lambda: NewFinanceService(
        repo=Container.resolve("finance_repo"),
        event_bus=Container.resolve("event_bus"),
        client_service=Container.resolve("client_service"),
        ticket_service=Container.resolve("ticket_service"),
    ))
    Container.register("todo_service", lambda: NewTodoService(
        repo=Container.resolve("todo_repo"),
        event_bus=Container.resolve("event_bus"),
    ))
    Container.register("dashboard_service", lambda: DashboardService(
        repo=Container.resolve("dashboard_repo"),
        event_bus=Container.resolve("event_bus"),
        ticket_service=Container.resolve("ticket_service"),
        finance_service=Container.resolve("finance_service"),
        inventory_service=Container.resolve("inventory_service"),
        equipment_service=Container.resolve("equipment_service"),
        todo_service=Container.resolve("todo_service"),
    ))
    Container.register("reminder_service", lambda: ReminderService(
        notification_repo=Container.resolve("notification_repo"),
        reminder_repo=Container.resolve("reminder_repo"),
        inventory_repo=Container.resolve("inventory_repo"),
        finance_repo=Container.resolve("finance_repo"),
        event_bus=Container.resolve("event_bus"),
        todo_service=Container.resolve("todo_service"),
        ticket_service=Container.resolve("ticket_service"),
        finance_service=Container.resolve("finance_service"),
        client_service=Container.resolve("client_service"),
        wecom_bot=_try_resolve("wecom_bot"),
        equipment_service=Container.resolve("equipment_service"),
    ))
    Container.register("inventory_service", lambda: InventoryService(
        repo=Container.resolve("inventory_repo"),
        event_bus=Container.resolve("event_bus"),
        goods_service=Container.resolve("goods_service"),
        ticket_service=None,
        purchase_service=None,
    ))

    from application.services.purchase_service import PurchaseService as NewPurchaseService
    from application.services.ticket_nl_service import TicketNlService
    from application.services.ticket_export_service import TicketExportService
    Container.register("purchase_service", lambda: NewPurchaseService(
        purchase_repo=Container.resolve("purchase_repo"),
        inventory_service=Container.resolve("inventory_service"),
        finance_service=Container.resolve("finance_service"),
    ))

    Container.register("ticket_nl_service", lambda: TicketNlService(
        ticket_service=Container.resolve("ticket_service"),
        client_service=Container.resolve("client_service"),
        finance_service=Container.resolve("finance_service"),
        equipment_service=Container.resolve("equipment_service"),
        reminder_service=Container.resolve("reminder_service"),
    ))
    Container.register("ticket_export_service", lambda: TicketExportService(
        ticket_service=Container.resolve("ticket_service"),
        finance_service=Container.resolve("finance_service"),
        equipment_service=Container.resolve("equipment_service"),
    ))

    _inv_svc = Container.resolve("inventory_service")
    _inv_svc.set_ticket_service(Container.resolve("ticket_service"))
    _inv_svc.set_purchase_service(Container.resolve("purchase_service"))

    _ts = Container.resolve("ticket_service")
    _ts.set_finance_service(Container.resolve("finance_service"))
    _ts.set_reminder_service(Container.resolve("reminder_service"))
    _ts.set_todo_service(Container.resolve("todo_service"))
    _ts.set_nl_service(Container.resolve("ticket_nl_service"))
    _ts.set_export_service(Container.resolve("ticket_export_service"))

    _eq_svc = Container.resolve("equipment_service")
    _eq_svc.set_reminder_service(Container.resolve("reminder_service"))

    _cs = Container.resolve("client_service")
    _cs.set_ticket_service(Container.resolve("ticket_service"))
    _cs.set_finance_service(Container.resolve("finance_service"))
    _cs.set_equipment_service(Container.resolve("equipment_service"))

    Container.register("search_service", lambda: SearchService(
        ticket_service=Container.resolve("ticket_service"),
        equipment_service=Container.resolve("equipment_service"),
        client_service=Container.resolve("client_service"),
        goods_service=Container.resolve("goods_service"),
        supplier_service=Container.resolve("supplier_service"),
        service_fee_service=Container.resolve("service_fee_service"),
        todo_service=Container.resolve("todo_service"),
        reminder_service=Container.resolve("reminder_service"),
    ))

    # 消息推送（惰性加载到服务定位器）
    try:
        from infrastructure.messaging.wecom import WeComBotClient
        Container.register("wecom_bot", lambda: WeComBotClient())
        logger.info("✅ 消息推送客户端已注册")
    except Exception as e:
        logger.warning(f"消息推送客户端注册失败: {e}")

    try:
        from infrastructure.messaging.pushplus import PushPlusClient
        Container.register("pushplus_bot", lambda: PushPlusClient())
        logger.info("✅ PushPlus推送客户端已注册")
    except Exception as e:
        logger.warning(f"PushPlus推送客户端注册失败: {e}")

    # 5. 缓存
    if use_cache:
        _register_cache(flask_app)

    # 5.5 任务队列（自动选择 RQ / LocalQueue）
    try:
        from infrastructure.queue.queue_factory import create_queue, register_cron_jobs
        queue = create_queue()
        Container.register_instance("queue", queue)
        register_cron_jobs(queue)
        logger.info("✅ 任务队列已注册")
    except Exception as e:
        Container.register_instance("queue", None)
        logger.warning(f"任务队列注册失败: {e}")

    # 6. 注册事件订阅
    if use_events:
        _register_event_subscribers()

    # 7. 注册 API 路由（如有 Flask 应用）
    if flask_app:
        _register_routes(flask_app)

    # 8. 启动每日数据库维护
    try:
        from infrastructure.persistence.maintenance import get_maintenance
        maint = get_maintenance()
        maint.schedule_daily()
        logger.info("✅ 每日数据库维护已启动")
    except Exception as e:
        logger.warning(f"数据库维护启动失败: {e}")

    # 9. 将所有已解析的服务注入 Flask app context
    if flask_app:
        _inject_services_to_app(flask_app)

    logger.info("✅ DI 容器初始化完成")
    # MCP 客户端（CodeGeeX 扩展）注册：优先使用官方客户端库，否则回退到简单 HTTP wrapper
    try:
        from codegeex_mcp_client import MCPClient  # 官方客户端（占位）
        mcp_client = MCPClient(base_url=os.environ.get("MCP_API_URL", "http://localhost:8080"),
                               api_key=os.environ.get("MCP_API_KEY", ""))
        Container.register_instance("mcp_client", mcp_client)
        logger.info("✅ MCP 官方客户端已注册")
    except Exception:
        try:
            import requests

            class SimpleMCPClient:
                def __init__(self, base_url, api_key=None):
                    self.base_url = base_url.rstrip("/")
                    self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

                def health(self):
                    resp = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=5)
                    return resp.json() if resp.ok else None

                def register_skill(self, payload):
                    return requests.post(f"{self.base_url}/api/v1/skills/register", json=payload, headers={**self.headers, "Content-Type": "application/json"}, timeout=10)

                def list_skills(self):
                    return requests.get(f"{self.base_url}/api/v1/skills", headers=self.headers, timeout=5)

            mcp_client = SimpleMCPClient(base_url=os.environ.get("MCP_API_URL", "http://localhost:8080"), api_key=os.environ.get("MCP_API_KEY", ""))
            Container.register_instance("mcp_client", mcp_client)
            logger.info("✅ MCP HTTP 客户端已注册（回退实现）")
        except Exception as e:
            Container.register_instance("mcp_client", None)
            logger.warning(f"MCP 客户端注册失败: {e}")
    return Container


def _register_cache(flask_app):
    from config.manager import config as s
    if not s.cache.enabled:
        Container.register_instance("cache", None)
        return

    try:
        from flask_caching import Cache
        if s.cache.redis_url:
            cache = Cache(flask_app, config={
                'CACHE_TYPE': 'RedisCache',
                'CACHE_REDIS_URL': s.cache.redis_url,
                'CACHE_DEFAULT_TIMEOUT': s.cache.default_timeout,
                'CACHE_KEY_PREFIX': s.cache.key_prefix,
            })
        else:
            cache = Cache(flask_app, config={
                'CACHE_TYPE': 'SimpleCache',
                'CACHE_DEFAULT_TIMEOUT': s.cache.default_timeout,
                'CACHE_THRESHOLD': s.cache.threshold,
            })
        Container.register_instance("cache", cache)
        logger.info("✅ 缓存已注册")
    except Exception as e:
        Container.register_instance("cache", None)
        logger.warning(f"缓存注册失败: {e}")


def _register_event_subscribers():
    try:
        from infrastructure.messaging.event_subscribers import register_all_subscribers
        event_bus = Container.resolve("event_bus")

        wecom_bot = _try_resolve("wecom_bot")
        todo_svc = _try_resolve("todo_service")
        reminder_svc = _try_resolve("reminder_service")
        ticket_svc = _try_resolve("ticket_service")
        client_svc = _try_resolve("client_service")

        services = {
            "todo_svc": todo_svc,
            "reminder_svc": reminder_svc,
            "wecom_bot": wecom_bot,
            "pushplus_bot": _try_resolve("pushplus_bot"),
            "ticket_svc": ticket_svc,
            "client_svc": client_svc,
            "equipment_svc": _try_resolve("equipment_service"),
            "finance_repo": _try_resolve("finance_repo"),
        }
        register_all_subscribers(event_bus, services)
        logger.info("✅ 事件订阅已注册")

        active = [k for k, v in services.items() if v]
        logger.info(f"   活跃推送服务: {active}")
    except Exception as e:
        logger.warning(f"事件订阅注册失败: {e}")


def _register_routes(flask_app):

    for module_name in ["api.v1.tickets", "api.v1.clients", "api.v1.finance",
                        "api.v1.todos", "api.v1.dashboard", "api.v1.health",
                        "api.v1.service_fees", "api.v1.suppliers",
                        "api.v1.stats", "api.v1.goods",
                        "api.v1.expenses", "api.v1.stock_aux",
                        "api.v1.wecom", "api.v1.pushplus",
                        "api.v1.search", "api.v1.tools",
                        "api.v1.reminders", "api.v1.inventory",
                        "api.v1.purchase", "api.v1.equipment",
                        "api.v1.technicians"]:
        try:
            mod = importlib.import_module(module_name)
            mod.register_blueprint(flask_app)
        except Exception as e:
            logger.warning(f"路由 {module_name} 注册失败: {e}")


def _try_resolve(name):
    try:
        return Container.resolve(name)
    except KeyError:
        return None


def _inject_services_to_app(flask_app):
    """
    将 Container 中已解析的服务实例批量注入到 Flask app.extensions，
    使 API 层可通过 inject_service() 从 app context 获取服务，
    不再依赖全局 ServiceLocator。
    """
    from infrastructure.di.service_injection import register_app_services

    service_names = [
        # 仓储
        "ticket_repo", "client_repo", "finance_repo", "todo_repo",
        "dashboard_repo", "equipment_repo", "notification_repo",
        "reminder_repo", "inventory_repo", "goods_repo",
        "technician_repo", "supplier_repo", "service_fee_repo",
        "stats_repo", "purchase_repo",
        # 服务
        "ticket_service", "client_service", "finance_service",
        "equipment_service", "dashboard_service", "reminder_service",
        "inventory_service", "goods_service", "supplier_service",
        "todo_service", "purchase_service", "ticket_nl_service",
        "ticket_export_service", "search_service",
        "technician_service", "service_fee_service", "stats_service",
        # 基础设施
        "settings", "event_bus", "cache", "queue",
        "wecom_bot", "pushplus_bot", "mcp_client",
    ]

    services = {}
    for name in service_names:
        try:
            svc = Container.resolve(name)
            if svc is not None:
                services[name] = svc
        except KeyError:
            pass  # 未注册的服务跳过

    register_app_services(flask_app, services)
