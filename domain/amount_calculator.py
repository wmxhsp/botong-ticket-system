"""
博通 (Botong) — 统一金额计算器

明确区分:
  - labor_fee (劳务收入): 对客户收取的费用 = 工时 × 服务单价
  - labor_cost (人工成本): 内部支出 = 工时 × 技术员成本率
  - material_fee (材料收费): 对客户收取的材料费
  - material_cost (材料成本): 实际采购成本
  - travel_fee (交通收费): = distance × rate

所有金额计算集中于此，消除多处独立计算的重复和不一致。
所有内部计算使用 Decimal，仅在最终输出时转回 float。
"""

import logging
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Optional, Dict, Any, List, Callable

getcontext().prec = 14

logger = logging.getLogger(__name__)

ZERO = Decimal('0')
HUNDRED = Decimal('100')


def _d(value) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return ZERO


def _f(value) -> float:
    if isinstance(value, Decimal):
        return float(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    return round(float(value), 2)


class AmountCalculator:

    @staticmethod
    def _default_cost_rate() -> Decimal:
        try:
            from config.manager import BillingConfig
            return _d(BillingConfig().default_cost_rate)
        except Exception:
            return Decimal('30')

    @staticmethod
    def _default_fee_rate() -> Decimal:
        try:
            from config.manager import BillingConfig
            return _d(BillingConfig().default_fee_rate)
        except Exception:
            return Decimal('60')

    # ===== 劳务收费 =====

    @staticmethod
    def calc_labor_fee(techs_data: List[Dict[str, Any]],
                       fee_rate: float = 60.0) -> float:
        if fee_rate <= 0 or fee_rate > 1000:
            raise ValueError(f"无效的服务费率: {fee_rate}（应在 0-1000 之间）")

        rate = _d(fee_rate)
        total = ZERO
        for td in techs_data:
            if not td.get("name"):
                continue
            billing_type = td.get("billing_type", "hourly")

            if billing_type == "package":
                total += _d(td.get("package_fee", 0))
            elif billing_type == "daily":
                days = _d(td.get("days", 0))
                if days <= 0:
                    continue
                daily_rate = _d(td.get("daily_fee_rate", 0))
                if daily_rate <= 0:
                    daily_rate = rate * 8
                total += days * daily_rate
            else:
                hours = _d(td.get("hours", 0))
                if hours <= 0:
                    continue
                total += hours * rate

        return _f(max(total, ZERO))

    # ===== 人工成本 =====

    @staticmethod
    def calc_labor_cost(techs_data: List[Dict[str, Any]],
                        cost_rate_lookup: Callable[[str], Optional[float]] = None,
                        daily_cost_lookup: Callable[[str], Optional[float]] = None,
                        package_cost_lookup: Callable[[str], Optional[float]] = None) -> float:
        total = ZERO
        for td in techs_data:
            if not td.get("name"):
                continue
            billing_type = td.get("billing_type", "hourly")

            if billing_type == "package":
                cost = _d(td.get("package_cost", 0))
                if cost <= 0 and package_cost_lookup:
                    try:
                        looked = package_cost_lookup(td["name"])
                        cost = _d(looked) if looked else ZERO
                    except Exception:
                        pass
                total += max(cost, ZERO)

            elif billing_type == "daily":
                days = _d(td.get("days", 0))
                if days <= 0:
                    continue
                daily_cost = _d(td.get("daily_cost_rate", 0))
                if daily_cost <= 0 and daily_cost_lookup:
                    try:
                        looked = daily_cost_lookup(td["name"])
                        daily_cost = _d(looked) if looked else ZERO
                    except Exception:
                        pass
                if daily_cost <= 0:
                    hourly = AmountCalculator._resolve_hourly_cost(td, cost_rate_lookup)
                    daily_cost = hourly * 8
                if daily_cost <= 0 or daily_cost > 5000:
                    raise ValueError(f"无效的天薪成本率: {daily_cost}（应在 0-5000 之间）")
                total += days * daily_cost

            else:
                hours = _d(td.get("hours", 0))
                if hours <= 0:
                    continue
                cost_rate = AmountCalculator._resolve_hourly_cost(td, cost_rate_lookup)
                if cost_rate <= 0 or cost_rate > 500:
                    raise ValueError(f"无效的成本率: {cost_rate}（应在 0-500 之间）")
                total += hours * cost_rate

        return _f(max(total, ZERO))

    @staticmethod
    def _resolve_hourly_cost(td: Dict[str, Any],
                            cost_rate_lookup: Callable[[str], Optional[float]] = None) -> Decimal:
        cost_rate = _d(td.get("cost_rate", 0))
        if cost_rate <= 0 and cost_rate_lookup:
            try:
                looked_up = cost_rate_lookup(td["name"])
                cost_rate = _d(looked_up) if looked_up else ZERO
            except Exception:
                pass
        if cost_rate <= 0:
            cost_rate = AmountCalculator._default_cost_rate()
        return cost_rate

    # ===== 材料费 =====

    @staticmethod
    def calc_material_fee(materials: List[Dict[str, Any]]) -> float:
        total = ZERO
        for m in (materials or []):
            val = m.get("total", 0)
            if not val:
                continue
            total += _d(val)
        return _f(total)

    # ===== 交通费 =====

    @staticmethod
    def calc_travel_fee(distance: float, rate: float) -> float:
        d = _d(distance)
        r = _d(rate)
        if d < 0 or r < 0:
            raise ValueError("交通距离和费率不能为负数")
        if d <= 0 or r <= 0:
            return 0.0
        return _f(d * r)

    # ===== 折扣计算 =====

    @staticmethod
    def calc_discount(total: float, discount_type: str = "",
                      discount_value: float = 0) -> tuple:
        t = _d(total)
        dv = _d(discount_value)
        discount_amount = ZERO
        if discount_type == "percent" and dv > 0:
            if dv > HUNDRED:
                raise ValueError("百分比折扣不能超过100%")
            discount_amount = (t * dv / HUNDRED).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif discount_type == "fixed" and dv > 0:
            discount_amount = min(dv, t)
        final_total = (t - discount_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return _f(discount_amount), _f(final_total)

    # ===== 总金额 =====

    @staticmethod
    def calc_total(labor_fee: float, material_fee: float,
                   travel_fee: float = 0.0,
                   discount_type: str = "",
                   discount_value: float = 0) -> float:
        if labor_fee < 0 or material_fee < 0 or travel_fee < 0:
            raise ValueError("金额不能为负数")

        gross = _d(labor_fee) + _d(material_fee) + _d(travel_fee)
        _, total = AmountCalculator.calc_discount(
            _f(gross), discount_type, discount_value)
        return _f(max(_d(total), ZERO))

    # ===== 含税总金额 =====

    @staticmethod
    def calc_total_with_tax(total: float, tax_rate: float = 0) -> tuple:
        if tax_rate <= 0:
            return 0.0, 0.0
        t = _d(total)
        tr = _d(tax_rate)
        tax_amount = (t * tr).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_with_tax = (t + tax_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return _f(tax_amount), _f(total_with_tax)

    # ===== 客户级别折扣 =====

    @staticmethod
    def apply_tier_discount(client_name: str,
                            discount_override: Optional[Dict] = None,
                            client_profile_lookup: Callable[[str], Optional[Dict]] = None) -> Optional[Dict]:
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
