"""
博通 (Botong) — 统一金额计算器

明确区分:
  - labor_fee (劳务收入): 对客户收取的费用 = 工时 × 服务单价
  - labor_cost (人工成本): 内部支出 = 工时 × 技术员成本率
  - material_fee (材料收费): 对客户收取的材料费
  - material_cost (材料成本): 实际采购成本
  - travel_fee (交通收费): = distance × rate

所有金额计算集中于此，消除多处独立计算的重复和不一致。
"""

import logging
from typing import Optional, Dict, Any, List, Callable

logger = logging.getLogger(__name__)


class AmountCalculator:

    @staticmethod
    def _default_cost_rate() -> float:
        try:
            from config.manager import BillingConfig
            return float(BillingConfig().default_cost_rate)
        except Exception:
            return 30.0

    @staticmethod
    def _default_fee_rate() -> float:
        try:
            from config.manager import BillingConfig
            return float(BillingConfig().default_fee_rate)
        except Exception:
            return 60.0

    # ===== 劳务收费 =====

    @staticmethod
    def calc_labor_fee(techs_data: List[Dict[str, Any]],
                       fee_rate: float = 60.0) -> float:
        """
        计算劳务总收入（对客户收取的费用）。

        支持三种计费模式：
          - hourly (时薪): hours × fee_rate
          - daily  (天薪): days × daily_fee_rate
          - package (包工): package_fee (固定金额)

        techs_data 中每项可包含:
          - billing_type: "hourly"|"daily"|"package"
          - hours / days / package_fee: 对应的量
          - daily_fee_rate: 天薪费率（可选，缺省走 fee_rate × 8）
        """
        if fee_rate <= 0 or fee_rate > 1000:
            raise ValueError(f"无效的服务费率: {fee_rate}（应在 0-1000 之间）")

        total = 0.0
        for td in techs_data:
            if not td.get("name"):
                continue
            billing_type = td.get("billing_type", "hourly")

            if billing_type == "package":
                total += float(td.get("package_fee", 0) or 0)
            elif billing_type == "daily":
                days = float(td.get("days", 0) or 0)
                if days <= 0:
                    continue
                daily_rate = float(td.get("daily_fee_rate", 0) or 0)
                if daily_rate <= 0:
                    daily_rate = fee_rate * 8  # 默认按8小时折算
                total += days * daily_rate
            else:  # hourly
                hours = float(td.get("hours", 0) or 0)
                if hours <= 0:
                    continue
                total += hours * fee_rate

        return round(max(total, 0), 2)

    # ===== 人工成本 =====

    @staticmethod
    def calc_labor_cost(techs_data: List[Dict[str, Any]],
                        cost_rate_lookup: Callable[[str], Optional[float]] = None,
                        daily_cost_lookup: Callable[[str], Optional[float]] = None,
                        package_cost_lookup: Callable[[str], Optional[float]] = None) -> float:
        """
        计算人工总成本（内部支出）。

        支持三种计费模式：
          - hourly: hours × cost_rate
          - daily:  days × daily_cost_rate
          - package: package_cost (固定金额)

        Args:
            techs_data: 技术员列表
            cost_rate_lookup: 时薪成本率回调
            daily_cost_lookup: 天薪成本率回调
            package_cost_lookup: 包工成本回调
        """
        total = 0.0
        for td in techs_data:
            if not td.get("name"):
                continue
            billing_type = td.get("billing_type", "hourly")

            if billing_type == "package":
                cost = float(td.get("package_cost", 0) or 0)
                if cost <= 0 and package_cost_lookup:
                    try:
                        looked = package_cost_lookup(td["name"])
                        cost = float(looked) if looked else 0
                    except Exception:
                        pass
                total += max(cost, 0)

            elif billing_type == "daily":
                days = float(td.get("days", 0) or 0)
                if days <= 0:
                    continue
                daily_cost = float(td.get("daily_cost_rate", 0) or 0)
                if daily_cost <= 0 and daily_cost_lookup:
                    try:
                        looked = daily_cost_lookup(td["name"])
                        daily_cost = float(looked) if looked else 0
                    except Exception:
                        pass
                if daily_cost <= 0:
                    # 回退：按小时成本率 × 8 折算
                    hourly = AmountCalculator._resolve_hourly_cost(td, cost_rate_lookup)
                    daily_cost = hourly * 8
                if daily_cost <= 0 or daily_cost > 5000:
                    raise ValueError(f"无效的天薪成本率: {daily_cost}（应在 0-5000 之间）")
                total += days * daily_cost

            else:  # hourly
                hours = float(td.get("hours", 0) or 0)
                if hours <= 0:
                    continue
                cost_rate = AmountCalculator._resolve_hourly_cost(td, cost_rate_lookup)
                if cost_rate <= 0 or cost_rate > 500:
                    raise ValueError(f"无效的成本率: {cost_rate}（应在 0-500 之间）")
                total += hours * cost_rate

        return round(max(total, 0), 2)

    @staticmethod
    def _resolve_hourly_cost(td: Dict[str, Any],
                            cost_rate_lookup: Callable[[str], Optional[float]] = None) -> float:
        """解析时薪成本率，优先用 techs_data 中的值，其次 lookup，最后默认值"""
        cost_rate = float(td.get("cost_rate", 0) or 0)
        if cost_rate <= 0 and cost_rate_lookup:
            try:
                looked_up = cost_rate_lookup(td["name"])
                cost_rate = float(looked_up) if looked_up else 0
            except Exception:
                pass
        if cost_rate <= 0:
            cost_rate = AmountCalculator._default_cost_rate()
        return cost_rate

    # ===== 材料费 =====

    @staticmethod
    def calc_material_fee(materials: List[Dict[str, Any]]) -> float:
        total = sum(
            float(m.get("total", m.get("total_cost", 0) or 0))
            for m in (materials or [])
        )
        return round(total, 2)

    # ===== 交通费 =====

    @staticmethod
    def calc_travel_fee(distance: float, rate: float) -> float:
        return round(distance * rate, 2) if distance > 0 and rate > 0 else 0.0

    # ===== 折扣计算 =====

    @staticmethod
    def calc_discount(total: float, discount_type: str = "",
                      discount_value: float = 0) -> tuple:
        discount_amount = 0.0
        if discount_type == "percent" and discount_value > 0:
            discount_amount = round(total * discount_value / 100, 2)
        elif discount_type == "fixed" and discount_value > 0:
            discount_amount = min(discount_value, total)
        final_total = round(total - discount_amount, 2)
        return discount_amount, final_total

    # ===== 总金额 =====

    @staticmethod
    def calc_total(labor_fee: float, material_fee: float,
                   travel_fee: float = 0.0,
                   discount_type: str = "",
                   discount_value: float = 0) -> float:
        if labor_fee < 0 or material_fee < 0 or travel_fee < 0:
            raise ValueError("金额不能为负数")
        
        gross = labor_fee + material_fee + travel_fee
        _, total = AmountCalculator.calc_discount(
            gross, discount_type, discount_value)
        return round(max(total, 0), 2)

    # ===== 含税总金额 =====

    @staticmethod
    def calc_total_with_tax(total: float, tax_rate: float = 0) -> tuple:
        """
        计算含税总额。

        Returns:
            (tax_amount, total_with_tax) — tax_rate 为 0 时 total_with_tax 返回 0
            （遵循业务约定：无税率时不填含税总额）
        """
        if tax_rate <= 0:
            return 0.0, 0.0
        tax_amount = round(total * tax_rate, 2)
        total_with_tax = round(total + tax_amount, 2)
        return tax_amount, total_with_tax

    # ===== 客户级别折扣 =====

    @staticmethod
    def apply_tier_discount(client_name: str,
                            discount_override: Optional[Dict] = None,
                            client_profile_lookup: Callable[[str], Optional[Dict]] = None) -> Optional[Dict]:
        """
        根据客户级别自动应用折扣，可被手动折扣覆盖。

        Args:
            client_name: 客户名称
            discount_override: 手动输入的折扣（优先级高于自动折扣）
            client_profile_lookup: 可选回调函数，传入客户名称返回客户画像 dict
        """
        if discount_override:
            discount_type = discount_override.get("type", "")
            discount_value = float(discount_override.get("value", 0) or 0)
            if discount_type not in ("percent", "fixed"):
                raise ValueError(f"无效的折扣类型: {discount_type}")
            if discount_value < 0 or (discount_type == "percent" and discount_value > 100):
                raise ValueError(f"无效的折扣值: {discount_value}")
            return discount_override

        if not client_name:
            return None

        if client_profile_lookup:
            try:
                profile = client_profile_lookup(client_name)
                if profile and isinstance(profile, dict):
                    tier_discount = float(profile.get("profile", {}).get("discount_rate", 1.0) or 1.0)
                    if tier_discount < 0 or tier_discount > 1.0:
                        logger.warning(f"客户 {client_name} 的折扣率 {tier_discount} 超出范围，忽略")
                        return None
                    if tier_discount < 1.0:
                        pct = round((1 - tier_discount) * 100, 1)
                        logger.info(f"客户 {client_name} 级别折扣: {pct}%")
                        return {"type": "percent", "value": pct}
            except Exception as e:
                logger.warning(f"获取客户 {client_name} 画像失败: {e}")
        return None

    # ===== 有效服务费率 =====

    @staticmethod
    def get_effective_fee_rate(ticket: Dict[str, Any],
                               client_rate_lookup: Callable[[str], Optional[float]] = None,
                               service_fee_lookup: Callable[[int], Optional[Dict]] = None) -> float:
        """
        获取有效服务费率。

        优先级:
          1. 客户专属费率
          2. 服务项目费率
          3. 默认值 60

        Args:
            ticket: 工单数据
            client_rate_lookup: 可选回调，传入客户名称返回 hourly_rate
            service_fee_lookup: 可选回调，传入 service_fee_id 返回 {fee_type, unit_price}
        """
        client_name = ticket.get("client", "")
        if client_name and client_rate_lookup:
            try:
                rate = client_rate_lookup(client_name)
                if rate and float(rate) > 0:
                    return float(rate)
            except Exception:
                pass

        service_fee_id = ticket.get("service_fee_id")
        if service_fee_id and service_fee_lookup:
            try:
                fee = service_fee_lookup(service_fee_id)
                if fee:
                    if fee.get("fee_type") == "hourly":
                        return float(fee.get("unit_price", 0)) or 60
                    elif fee.get("fee_type") in ("fixed", "free"):
                        return 0
            except Exception:
                pass

        return 60.0
