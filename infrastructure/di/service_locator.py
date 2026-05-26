"""
博通 (Botong) — 服务定位器（已废弃）

⚠️ 此模块已废弃，请使用 infrastructure.di.service_injection.inject_service()
  
迁移路径：
  旧: from infrastructure.di.service_locator import resolve_service
      svc = resolve_service("ticket_service")
      
  新: from infrastructure.di.service_injection import inject_service
      svc = inject_service("ticket_service")
"""

import logging
import warnings
from typing import Optional, Any

from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)


def resolve_service(name: str) -> Any:
    """
    [DEPRECATED] 请使用 inject_service(name)
    
    此函数保留向后兼容，内部委托给 inject_service()。
    """
    warnings.warn(
        "resolve_service() is deprecated, use inject_service() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return inject_service(name)


class ServiceLocator:
    """
    [DEPRECATED] 全局服务定位器反模式，保留向后兼容。
    新代码请使用 inject_service() 或直接注入依赖。
    """
    cache = None
    limiter = None
    _initialized = False

    def init(self, app=None, api=None):
        if self._initialized:
            return
        self.app = app
        self.api = api
        self._initialized = True

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return inject_service(name)

    def set_service(self, name: str, instance):
        from infrastructure.di.container import Container
        Container.register_instance(name, instance)

    def get_service(self, name: str) -> Optional[object]:
        return inject_service(name)

    def get_all_services(self) -> dict:
        from infrastructure.di.service_injection import get_all_registered_services
        try:
            from flask import current_app
            return get_all_registered_services(current_app)
        except RuntimeError:
            from infrastructure.di.container import Container
            result = {}
            for name in list(Container._factories.keys()) + list(Container._instances.keys()):
                try:
                    val = Container.resolve(name)
                    if val is not None:
                        result[name] = type(val).__name__
                except Exception:
                    pass
            return result

    def reset(self):
        from infrastructure.di.container import Container
        Container.reset()
        self._initialized = False


reg = ServiceLocator()
