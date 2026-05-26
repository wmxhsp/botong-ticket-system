# -*- coding: utf-8 -*-
"""
博通 (Botong) — 领域/系统异常定义
从 lib/core/exceptions.py 迁移，保持完全兼容
"""


class TicketSystemError(Exception):
    """系统基础异常"""
    pass


class TicketNotFoundError(TicketSystemError):
    """工单不存在"""
    pass


class TicketValidationError(TicketSystemError):
    """工单数据验证失败"""
    pass


class TicketStatusError(TicketSystemError):
    """工单状态错误（如已完工无法修改）"""
    pass


class TicketAssignmentError(TicketSystemError):
    """工单分配错误（技术员不可用、资质不符等）"""
    pass


class InventoryError(TicketSystemError):
    """库存操作异常"""
    pass


class InventoryNotEnoughError(InventoryError):
    """库存不足"""
    pass


class InventoryLockError(InventoryError):
    """库存锁定错误（并发冲突）"""
    pass


class EquipmentError(TicketSystemError):
    """设备管理异常"""
    pass


class EquipmentMaintenanceError(EquipmentError):
    """设备维保异常（维保过期、维保类型不匹配）"""
    pass


class DatabaseError(TicketSystemError):
    """数据库操作异常"""
    pass


class ConfigError(TicketSystemError):
    """配置错误"""
    pass


class BillingError(TicketSystemError):
    """结算异常"""
    pass


class DuplicateBillingError(BillingError):
    """重复结算错误"""
    pass


class SaleError(TicketSystemError):
    """销售操作异常"""
    pass


class PriceError(TicketSystemError):
    """价格异常（定价不符、折扣超限等）"""
    pass


class PaymentError(TicketSystemError):
    """支付异常（支付失败、金额不匹配等）"""
    pass


class RefundError(TicketSystemError):
    """退款异常"""
    pass


class TechnicianNotFoundError(TicketSystemError):
    """技术人员不存在"""
    pass


class TechnicianRateError(TicketSystemError):
    """技术人员费率异常"""
    pass


class ClientNotFoundError(TicketSystemError):
    """客户不存在"""
    pass


class ClientCreditError(TicketSystemError):
    """客户信用/账期异常"""
    pass


class GoodsNotFoundError(TicketSystemError):
    """商品不存在"""
    pass


class GoodsStockError(TicketSystemError):
    """商品库存异常"""
    pass


class SupplierNotFoundError(TicketSystemError):
    """供应商不存在"""
    pass


class PurchaseOrderError(TicketSystemError):
    """采购订单异常"""
    pass


class PurchaseOrderStatusError(PurchaseOrderError):
    """采购订单状态错误"""
    pass


class WarehouseError(TicketSystemError):
    """仓库异常"""
    pass


class WarehouseStockError(WarehouseError):
    """仓库库存异常"""
    pass


class StockTransferError(TicketSystemError):
    """库存调拨异常"""
    pass


class AuthorizationError(TicketSystemError):
    """权限认证异常"""
    pass


class RateLimitError(TicketSystemError):
    """请求频率超限"""
    pass


class ValidationError(TicketSystemError):
    """通用数据验证错误"""
    pass


class ConcurrencyError(TicketSystemError):
    """并发冲突错误"""
    pass


class IdempotencyError(TicketSystemError):
    """幂等性冲突错误（重复请求）"""
    pass
