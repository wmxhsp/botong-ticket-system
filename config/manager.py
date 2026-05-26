# -*- coding: utf-8 -*-
"""
博通 (Botong) — 统一配置管理模块
合并原 config/settings.py 和 config/manager.py，提供单一配置入口
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

CONFIG_DIR = Path(__file__).resolve().parent
BASE_DIR = CONFIG_DIR.parent


@dataclass
class DatabaseConfig:
    path: str = field(default_factory=lambda: os.environ.get(
        "TICKETS_DB_PATH", str(BASE_DIR / "tickets.db")))
    pool_min: int = 2
    pool_max: int = 10
    timeout: int = 30
    wal_mode: bool = True


@dataclass
class AuthConfig:
    password: str = field(default_factory=lambda: os.environ.get("BOTO_ACCESS_PASSWORD", ""))
    cookie_name: str = "bt_auth"
    cookie_ttl: int = 28800
    cookie_refresh: int = 7200
    csrf_ttl: int = 3600


@dataclass
class CacheConfig:
    enabled: bool = True
    default_timeout: int = 300
    redis_url: str = field(default_factory=lambda: os.environ.get("REDIS_URL", ""))
    key_prefix: str = "jx:cache:"
    threshold: int = 1000


@dataclass
class RateConfig:
    hourly: float = 0
    annual: float = 0
    contact: str = ""
    type: str = ""
    scope: list = field(default_factory=list)


@dataclass
class CompanyConfig:
    name: str = "集宁区博通科技"
    contact: str = "苏鹏"
    phone: str = ""
    bank: str = ""
    account: str = ""
    credit_code: str = ""
    address: str = ""
    email: str = ""
    default_operator: str = "苏鹏"


@dataclass
class AlertConfig:
    critical_threshold: int = 0
    warning_threshold: int = 2
    info_threshold_percent: float = 0.2
    check_interval_hours: int = 24
    notify_methods: list = field(default_factory=lambda: ["console"])


@dataclass
class BillingConfig:
    auto_generate_invoice: bool = True
    auto_tax_calc: bool = True
    default_tax_rate: float = 0.06
    default_fee_rate: float = 60.0
    default_cost_rate: float = 30.0
    payment_terms_days: int = 30
    auto_remind_before_days: int = 7


@dataclass
class AppConfig:
    debug: bool = field(default_factory=lambda: os.environ.get("BOTO_DEBUG", "0") == "1")
    secret_key: str = field(default_factory=lambda: os.environ.get("BOTO_SECRET_KEY", ""))
    host: str = "0.0.0.0"
    port: int = 5052
    log_level: str = "INFO"
    json_log: bool = False


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._db = DatabaseConfig()
        self._auth = AuthConfig()
        self._cache = CacheConfig()
        self._app = AppConfig()
        self._rates: Dict[str, RateConfig] = {}
        self._company = CompanyConfig()
        self._clients: list = []
        self._service_types: Dict[str, Dict] = {}
        self._alert = AlertConfig()
        self._billing = BillingConfig()
        self._env = os.environ.get("BWT_ENV", "prod")
        self._load_all()

    def _load_all(self):
        self._load_rates()
        self._load_company()
        self._load_service_types()
        self._load_alert()
        self._load_billing()
        self._apply_env_overrides()
        if not self._app.secret_key:
            self._app.secret_key = os.urandom(24).hex()

    def _load_rates(self):
        rates_file = CONFIG_DIR / "rates.json"
        if rates_file.exists():
            with open(rates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for name, cfg in data.get("rates", {}).items():
                    if isinstance(cfg, (int, float)):
                        self._rates[name] = RateConfig(hourly=float(cfg))
                    else:
                        self._rates[name] = RateConfig(**cfg)
        else:
            self._rates = {
                "蒙古族中学": RateConfig(hourly=60, contact="崔主任"),
                "集宁京能电力": RateConfig(hourly=100, contact="李官胜", type="国企"),
                "网吧": RateConfig(annual=2000, scope=["服务器维护", "网络设备维护", "软件维护"]),
                "电竞": RateConfig(annual=2000, scope=["服务器维护", "网络设备维护", "软件维护"]),
            }
            self._save_rates()

    def _load_company(self):
        clients_file = CONFIG_DIR / "clients.json"
        if clients_file.exists():
            with open(clients_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                company_data = data.get("company", {})
                self._company = CompanyConfig(**company_data)
                self._clients = data.get("clients", [])

    def _load_service_types(self):
        service_file = CONFIG_DIR / "service_types.json"
        if service_file.exists():
            with open(service_file, 'r', encoding='utf-8') as f:
                self._service_types = json.load(f)
        else:
            self._service_types = {
                "监控故障": {"keywords": ["监控", "摄像头", "黑屏", "没画面"]},
                "电话故障": {"keywords": ["电话", "移机", "线路"]},
                "网络故障": {"keywords": ["网络", "网线", "交换机"]},
                "包年维保": {"keywords": ["包年", "维保", "年费", "续费"]},
            }
            self._save_service_types()

    def _load_alert(self):
        alert_file = CONFIG_DIR / "alert.json"
        if alert_file.exists():
            with open(alert_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._alert = AlertConfig(**data)

    def _load_billing(self):
        billing_file = CONFIG_DIR / "billing.json"
        if billing_file.exists():
            with open(billing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._billing = BillingConfig(**data)

    def _apply_env_overrides(self):
        if env_name := os.environ.get("BWT_COMPANY_NAME"):
            self._company.name = env_name
        if env_tax := os.environ.get("BWT_TAX_RATE"):
            self._billing.default_tax_rate = float(env_tax)
        if env_notify := os.environ.get("BWT_NOTIFY"):
            self._alert.notify_methods = env_notify.split(",")
        if env_op := os.environ.get("BOTO_OPERATOR"):
            self._company.default_operator = env_op

    def _save_rates(self):
        rates_file = CONFIG_DIR / "rates.json"
        rates_file.parent.mkdir(parents=True, exist_ok=True)
        data = {"rates": {name: {"hourly": cfg.hourly, "annual": cfg.annual,
                                  "contact": cfg.contact, "type": cfg.type,
                                  "scope": cfg.scope}
                          for name, cfg in self._rates.items()}}
        with open(rates_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_service_types(self):
        service_file = CONFIG_DIR / "service_types.json"
        service_file.parent.mkdir(parents=True, exist_ok=True)
        with open(service_file, 'w', encoding='utf-8') as f:
            json.dump(self._service_types, f, ensure_ascii=False, indent=2)

    def _save_alert(self):
        alert_file = CONFIG_DIR / "alert.json"
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        from dataclasses import asdict
        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self._alert), f, ensure_ascii=False, indent=2)

    def _save_billing(self):
        billing_file = CONFIG_DIR / "billing.json"
        billing_file.parent.mkdir(parents=True, exist_ok=True)
        from dataclasses import asdict
        with open(billing_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self._billing), f, ensure_ascii=False, indent=2)

    # ========== Settings 兼容属性 ==========
    @property
    def db(self) -> DatabaseConfig:
        return self._db

    @property
    def auth(self) -> AuthConfig:
        return self._auth

    @property
    def cache(self) -> CacheConfig:
        return self._cache

    @property
    def app(self) -> AppConfig:
        return self._app

    # ========== 业务配置接口 ==========
    def get_rate(self, client: str) -> Optional[RateConfig]:
        return self._rates.get(client)

    def get_hourly_rate(self, client: str) -> float:
        cfg = self._rates.get(client)
        return cfg.hourly if cfg else 60

    def get_annual_rate(self, client: str) -> float:
        cfg = self._rates.get(client)
        return cfg.annual if cfg else 2000

    def get_contact(self, client: str) -> str:
        cfg = self._rates.get(client)
        return cfg.contact if cfg else ""

    def get_company(self) -> CompanyConfig:
        return self._company

    def get_operator(self) -> str:
        return self._company.default_operator

    def get_clients(self) -> list:
        return self._clients

    def get_service_types(self) -> Dict[str, Dict]:
        return self._service_types

    def get_alert_config(self) -> AlertConfig:
        return self._alert

    def get_billing_config(self) -> BillingConfig:
        return self._billing

    def get_wecom_config(self) -> Dict[str, Any]:
        path = CONFIG_DIR / "wecom.json"
        try:
            return json.loads(path.read_text())
        except Exception:
            return {"enabled": False, "webhook_url": "", "push_events": {}}

    def get_service_fees(self) -> list:
        path = CONFIG_DIR / "service_types.json"
        try:
            return json.loads(path.read_text())
        except Exception:
            return []

    def match_service_type(self, text: str) -> str:
        for service_type, cfg in self._service_types.items():
            for keyword in cfg.get("keywords", []):
                if keyword in text:
                    return service_type
        return "维修"

    def load_from_json(self, path: str):
        config_file = Path(path)
        if not config_file.exists():
            return
        try:
            data = json.loads(config_file.read_text())
            for section, values in data.items():
                config_obj = getattr(self, f"_{section}", None)
                if config_obj and isinstance(values, dict):
                    for key, value in values.items():
                        if hasattr(config_obj, key):
                            setattr(config_obj, key, value)
        except Exception:
            pass

    def reload(self):
        self._load_all()

    def save_all(self):
        self._save_rates()
        self._save_alert()
        self._save_billing()


config = ConfigManager()
