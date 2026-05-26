"""
博通 (Botong) — 统一服务注入

替代 ServiceLocator 反模式，通过 Flask app context 注入服务。
API 层使用 inject_service() 获取服务实例，无需全局可变状态。

迁移路径：
  旧: resolve_service("ticket_service")
  新: inject_service("ticket_service")
  
  两者当前行为一致，但 inject_service() 未来将只从 app.extensions 读取，
  不再依赖全局 Container。
"""

import logging
import warnings
from typing import Any, Optional

from flask import current_app

logger = logging.getLogger(__name__)


def inject_service(name: str) -> Any:
    """
    从 Flask app context 获取服务实例（推荐方式）。
    
    优先从 app.extensions 读取（bootstrap 阶段注入），
    回退到 Container.resolve（兼容旧路径）。
    """
    try:
        services = current_app.extensions.get("bt_services", {})
        if name in services:
            return services[name]
    except RuntimeError:
        # 非 Flask 请求上下文
        pass

    # 回退到 Container
    from infrastructure.di.container import Container
    try:
        return Container.resolve(name)
    except KeyError:
        logger.warning(f"inject_service: 未知服务 '{name}'")
        return None


def register_app_services(app, services: dict):
    """
    将服务实例注册到 Flask app.extensions。
    由 bootstrap() 调用，一次性注入所有已解析的服务。
    """
    app.extensions["bt_services"] = services
    logger.info(f"✅ 已注入 {len(services)} 个服务到 app context")


def get_all_registered_services(app) -> dict:
    """获取当前 app 注册的所有服务名称和类型"""
    services = app.extensions.get("bt_services", {})
    return {name: type(svc).__name__ for name, svc in services.items() if svc is not None}
