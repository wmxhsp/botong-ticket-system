import logging
import threading
import importlib
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)


class Container:
    _instances: Dict[str, Any] = {}
    _factories: Dict[str, tuple] = {}
    _config: Dict[str, Any] = {}
    _lazy_map: Dict[str, tuple] = {}
    _lock = threading.RLock()

    @classmethod
    def register(cls, name: str, factory: Callable, singleton: bool = True):
        with cls._lock:
            cls._factories[name] = (factory, singleton)
        logger.debug(f"Container: registered '{name}' (singleton={singleton})")

    @classmethod
    def register_instance(cls, name: str, instance: Any):
        with cls._lock:
            cls._instances[name] = instance
        logger.debug(f"Container: instance registered '{name}'")

    @classmethod
    def register_lazy(cls, name: str, module_path: str, class_name: str):
        with cls._lock:
            cls._lazy_map[name] = (module_path, class_name)
        logger.debug(f"Container: lazy-registered '{name}' ← {module_path}.{class_name}")

    @classmethod
    def resolve(cls, name: str):
        with cls._lock:
            if name in cls._instances:
                return cls._instances[name]

            entry = cls._factories.get(name)
            if entry is not None:
                factory, singleton = entry
                instance = factory()
                if singleton:
                    cls._instances[name] = instance
                return instance

            if name in cls._lazy_map:
                module_path, class_name = cls._lazy_map[name]
                try:
                    mod = importlib.import_module(module_path)
                    klass = getattr(mod, class_name)
                    instance = klass()
                    cls._instances[name] = instance
                    logger.info(f"Container: lazy-loaded '{name}' ← {module_path}.{class_name}")
                    return instance
                except Exception as e:
                    logger.warning(f"Container: lazy-load '{name}' failed: {e}")
                    return None

        raise KeyError(f"Container: 未注册的服务 '{name}'")

    @classmethod
    def has(cls, name: str) -> bool:
        with cls._lock:
            return name in cls._instances or name in cls._factories or name in cls._lazy_map

    @classmethod
    def set_config(cls, key: str, value: Any):
        with cls._lock:
            cls._config[key] = value

    @classmethod
    def get_config(cls, key: str, default: Any = None) -> Any:
        with cls._lock:
            return cls._config.get(key, default)

    @classmethod
    def reset(cls):
        with cls._lock:
            cls._instances.clear()
            cls._factories.clear()
            cls._config.clear()
            cls._lazy_map.clear()
