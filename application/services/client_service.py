"""
博通 (Botong) — 客户应用服务（新架构版）
支持征信评分、客户级别、画像聚合
"""

import csv
import logging
from io import StringIO
from typing import Optional, List, Dict, Any

from domain.exceptions import ClientNotFoundError

logger = logging.getLogger(__name__)

# 客户级别定义
TIER_NAMES = {0: "普通", 1: "银牌", 2: "金牌", 3: "钻石"}
TIER_DISCOUNT = {0: 1.0, 1: 0.95, 2: 0.90, 3: 0.85}
# (最低分数, 级别)
TIER_THRESHOLDS = [(40, 0), (60, 1), (80, 2), (101, 3)]


class ClientService:
    """
    客户应用服务

    依赖注入:
        repo: SqliteClientRepository
        event_bus: EventBus（可选）
    """

    def __init__(self, repo, event_bus=None, ticket_service=None,
                 finance_service=None, equipment_service=None):
        self._repo = repo
        self._event_bus = event_bus
        self._ticket_service = ticket_service
        self._finance_service = finance_service
        self._equipment_service = equipment_service

    def set_ticket_service(self, svc):
        self._ticket_service = svc

    def set_finance_service(self, svc):
        self._finance_service = svc

    def set_equipment_service(self, svc):
        self._equipment_service = svc

    # ===== 属性代理 =====

    @property
    def repo(self):
        return self._repo

    # ===== 业务方法 =====

    def get_client(self, client_name: str) -> Dict[str, Any]:
        """获取客户详情"""
        client = self._repo.find_by_name(client_name)
        if not client:
            raise ClientNotFoundError(f"客户 '{client_name}' 不存在")
        return client

    def list_clients(self, keyword: str = None,
                     with_profile: bool = False) -> List[Dict[str, Any]]:
        """获取客户列表"""
        filters = {}
        if keyword:
            filters["q"] = keyword
        clients = self._repo.find_list(filters)

        if with_profile:
            for c in clients:
                try:
                    profile = self._get_profile_stats(c["name"])
                    if profile:
                        score = self._calc_credit_score(
                            profile.get("stats"), profile.get("aging"), [])
                        c["credit_score"] = score
                        c["tier"] = self._calc_tier(score)
                        c["tier_name"] = TIER_NAMES.get(c["tier"], "普通")
                except Exception:
                    pass

        return clients

    def list_with_summary(self, keyword: str = None,
                          with_profile: bool = False) -> Dict[str, Any]:
        clients = self.list_clients(keyword=keyword, with_profile=with_profile)
        count = len(clients)
        if clients:
            items = "、".join(f"{c.get('name','?')}({c.get('active_tickets',0)}单)" for c in clients[:10])
            suffix = f"，等{count}位" if count > 10 else ""
            summary = f"共 {count} 位客户：{items}{suffix}"
        else:
            summary = "暂无客户"
        return {"clients": clients, "summary": summary}

    def create_client(self, name: str, contact: str = "",
                      phone: str = "", notes: str = "") -> Dict[str, Any]:
        """创建客户"""
        if not name or not name.strip():
            raise ValueError("客户名称不能为空")

        existing = self._repo.find_by_name(name.strip())
        if existing:
            raise ValueError(f"客户 '{name}' 已存在")

        self._repo.save({
            "name": name.strip(),
            "contact": contact.strip(),
            "phone": phone.strip(),
            "notes": notes.strip(),
        })

        if self._event_bus:
            from domain.events import ClientCreated
            self._event_bus.dispatch(ClientCreated(
                name=name.strip()))

        return {"message": f"客户 {name} 已创建", "name": name.strip()}

    def update_client(self, old_name: str, **fields) -> Dict[str, Any]:
        """更新客户信息"""
        # 验证存在
        self.get_client(old_name)

        data = {k: v for k, v in fields.items() if v is not None}
        if not data:
            return self.get_client(old_name)

        self._repo.update(old_name, data)
        return self.get_client(data.get("name", old_name))

    def delete_client(self, name: str) -> bool:
        """删除客户（完整关联检查）"""
        self.get_client(name)

        associations = self._repo.check_associations(name)
        for assoc in associations:
            if assoc["count"] > 0:
                raise ValueError(
                    f"客户 '{name}' 下有 {assoc['count']} 条关联{assoc['label']}，无法删除")

        self._repo.delete(name)
        return True

    # ===== 客户画像 =====

    def get_client_profile(self, name: str) -> Dict[str, Any]:
        """客户完整画像：基本信息 + 统计 + 征信评分 + 级别"""
        client = self.get_client(name)
        if not client:
            raise ClientNotFoundError(f"客户 '{name}' 不存在")

        stats = self._get_profile_stats(name)
        score = self._calc_credit_score(
            stats.get("stats"), stats.get("aging"), stats.get("payment_history", []))
        tier = self._calc_tier(score)

        return {
            **client,
            "profile": {
                "credit_score": score,
                "tier": tier,
                "tier_name": TIER_NAMES.get(tier, "普通"),
                "discount_rate": TIER_DISCOUNT.get(tier, 1.0),
                "stats": stats.get("stats", {}),
                "aging": stats.get("aging", {}),
            },
        }

    def _get_profile_stats(self, name: str) -> Dict[str, Any]:
        """聚合客户统计数据"""
        return self._repo.get_profile_stats(name)

    def freeze_credit(self, name: str, reason: str = ""):
        """冻结客户信用（由 ClientCreditFrozen 事件触发）"""
        existing = self._repo.find_by_name(name)
        if not existing:
            return
        current_notes = existing.get("notes", "") or ""
        freeze_note = f"[信用冻结] {reason}" if reason else "[信用冻结]"
        new_notes = f"{current_notes}\n{freeze_note}".strip()
        self._repo.update(name, {"notes": new_notes})

    # ===== 征信评分算法 =====

    def _calc_credit_score(self, stats, aging, payment_history) -> int:
        """
        征信评分 0-100

        维度:
        - 交易活跃度 (0-30): 订单数 + 消费总额
        - 付款信用 (0-40): 付款率
        - 逾期扣分 (0~-30): 逾期金额
        - 综合评估 (±10)
        """
        if not stats or not stats.get("total_orders"):
            return 30  # 新客户默认 30 分

        orders = int(stats.get("total_orders", 0) or 0)
        spent = float(stats.get("total_spent", 0) or 0)
        paid = int(stats.get("paid_count", 0) or 0)
        unpaid = int(stats.get("unpaid_count", 0) or 0)
        overdue_amt = float(aging.get("overdue_amount", 0) if aging else 0)

        score = 30  # 基础分

        # 1. 交易活跃度 (0-30分)
        score += min(orders * 3, 20)           # 每单3分, 上限20
        score += min(int(spent / 1000), 10)     # 每千元1分, 上限10

        # 2. 付款信用 (0-40分)
        total = orders or 1
        pay_ratio = paid / max(total, 1)
        score += int(pay_ratio * 30)            # 付款率 × 30

        # 3. 逾期扣分 (0~-30)
        if overdue_amt > 0:
            penalty = min(int(overdue_amt / 500) * 5, 25)
            score -= penalty

        # 4. 综合评估
        if unpaid > orders * 0.5:
            score -= 8
        if paid >= 10 and pay_ratio > 0.9:
            score += 5  # 老客户奖励

        return max(10, min(100, score))

    def _calc_tier(self, score: int) -> int:
        """
        根据评分判定客户级别
        0=普通, 1=银牌, 2=金牌, 3=钻石
        """
        for threshold, tier in TIER_THRESHOLDS:
            if score < threshold:
                return tier
        return 3

    def search_clients(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        return self._repo.search_clients(keyword, limit)

    def get_ticket_count(self, client_name: str) -> int:
        return self._repo.get_ticket_count(client_name)

    def get_equipment_count(self, client_name: str) -> int:
        return self._repo.get_equipment_count(client_name)

    def count_clients(self) -> int:
        return self._repo.count_clients()

    def get_tier_config(self):
        """获取所有级别配置（前端展示用）"""
        return {
            "tiers": [
                {"level": 0, "name": "普通", "discount": 1.0, "min_score": 0,
                 "color": "#6c757d", "icon": "bi-person"},
                {"level": 1, "name": "银牌", "discount": 0.95, "min_score": 40,
                 "color": "#adb5bd", "icon": "bi-award"},
                {"level": 2, "name": "金牌", "discount": 0.90, "min_score": 60,
                 "color": "#ffc107", "icon": "bi-trophy"},
                {"level": 3, "name": "钻石", "discount": 0.85, "min_score": 80,
                 "color": "#0d6efd", "icon": "bi-gem"},
            ]
        }

    def _ensure_svc(self, attr_name, service_name):
        svc = getattr(self, attr_name, None)
        if svc is None:
            raise RuntimeError(f"ClientService: {attr_name} not injected (expected {service_name})")
        return svc

    def export_clients_csv(self):
        clients = self.list_clients(keyword="")
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["客户名称", "联系人", "电话", "活跃工单", "设备数", "未结算", "最近工单"])
        for c in clients:
            writer.writerow([c.get("name", ""), c.get("contact", ""), c.get("phone", ""),
                            c.get("active_tickets", 0), c.get("device_count", 0),
                            c.get("unpaid_amount", 0), c.get("last_ticket_date", "")])
        return output.getvalue()

    def import_clients_csv(self, csv_content):
        lines = csv_content.strip().split("\n")
        if len(lines) < 2:
            return {"error": "文件为空或格式不正确"}
        headers = [h.strip().lower() for h in lines[0].split(",")]
        name_idx = next((i for i, h in enumerate(headers) if h in ("name", "客户名称", "客户名")), 0)
        contact_idx = next((i for i, h in enumerate(headers) if h in ("contact", "联系人")), None)
        phone_idx = next((i for i, h in enumerate(headers) if h in ("phone", "电话", "手机")), None)
        imported = 0
        errors = []
        for line in lines[1:]:
            cols = [c.strip() for c in line.split(",")]
            if len(cols) <= name_idx:
                continue
            name = cols[name_idx]
            if not name:
                continue
            try:
                self.create_client(
                    name=name,
                    contact=cols[contact_idx].strip('"') if contact_idx is not None and len(cols) > contact_idx else "",
                    phone=cols[phone_idx].strip('"') if phone_idx is not None and len(cols) > phone_idx else "",
                )
                imported += 1
            except Exception as e:
                errors.append(f"行 '{name}' 导入失败: {str(e)}")
        return {"imported": imported, "errors": errors, "message": f"导入完成：成功 {imported} 条，失败 {len(errors)} 条"}

    def get_client_overview(self, client_name):
        client = self.get_client(client_name)
        ticket_svc = self._ensure_svc("_ticket_service", "ticket_service")
        finance_svc = self._ensure_svc("_finance_service", "finance_service")
        equip_svc = self._ensure_svc("_equipment_service", "equipment_service")
        tickets_data = ticket_svc.list_tickets(client=client_name)
        tickets = tickets_data["tickets"] if isinstance(tickets_data, dict) else tickets_data
        equipment = equip_svc.list_by_client(client_name) if equip_svc and hasattr(equip_svc, 'list_by_client') else []
        income = finance_svc.get_client_income_records(client_name) if finance_svc and hasattr(finance_svc, 'get_client_income_records') else []
        return {"client": client, "tickets": tickets, "equipment": equipment, "income": income}
