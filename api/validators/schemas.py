"""
博通 (Botong) — Pydantic Schema 定义

按资源分组:
  - Ticket schemas
  - Client schemas
  - Finance schemas
  - Inventory schemas
  - 通用 Query schemas
"""

from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

# ============================================================
#  工单 Ticket
# ============================================================

class TicketCreateSchema(BaseModel):
    """创建工单"""
    client: str = Field(..., min_length=1, max_length=200, description="客户名称")
    content: str = Field(..., min_length=1, description="服务内容")
    status: Optional[str] = Field(default="open", description="初始状态")
    estimated_hours: Optional[float] = Field(default=0, ge=0, description="预估工时")
    amount: Optional[float] = Field(default=0, ge=0, description="工单金额")
    tax_rate: Optional[float] = Field(default=0, ge=0, le=100, description="税率(%)")
    discount: Optional[float] = Field(default=0, ge=0, description="折扣金额")
    ticket_no: Optional[str] = Field(default=None, max_length=50, description="自定义编号")
    appointment_at: Optional[str] = Field(default=None, description="预约时间")
    service_type: Optional[str] = Field(default=None, description="服务类型")
    technician_ids: Optional[List[int]] = Field(default=None, description="负责人ID列表")
    equipment_ids: Optional[List[int]] = Field(default=None, description="关联设备ID列表")
    notes: Optional[str] = Field(default=None, description="备注")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"open", "in-progress", "pending-parts", "pending-client",
                 "pending-payment", "completed", "closed", "cancelled", "archived"}
        if v not in valid:
            raise ValueError(f"无效状态: {v}，有效值: {', '.join(sorted(valid))}")
        return v


class TicketUpdateSchema(BaseModel):
    """更新工单"""
    client: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)
    status: Optional[str] = Field(default=None)
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    amount: Optional[float] = Field(default=None, ge=0)
    tax_rate: Optional[float] = Field(default=None, ge=0, le=100)
    discount: Optional[float] = Field(default=None, ge=0)
    ticket_no: Optional[str] = Field(default=None, max_length=50)
    appointment_at: Optional[str] = Field(default=None)
    service_type: Optional[str] = Field(default=None)
    technician_ids: Optional[List[int]] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"open", "in-progress", "pending-parts", "pending-client",
                 "pending-payment", "completed", "closed", "cancelled", "archived"}
        if v not in valid:
            raise ValueError(f"无效状态: {v}，有效值: {', '.join(sorted(valid))}")
        return v


# ============================================================
#  客户 Client
# ============================================================

class ClientCreateSchema(BaseModel):
    """创建客户"""
    name: str = Field(..., min_length=1, max_length=200, description="客户名称")
    contact: Optional[str] = Field(default=None, max_length=100, description="联系人")
    phone: Optional[str] = Field(default=None, max_length=50, description="电话")
    notes: Optional[str] = Field(default=None, description="备注")


class ClientUpdateSchema(BaseModel):
    """更新客户"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    contact: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None)


# ============================================================
#  财务 Finance
# ============================================================

class IncomeRecordSchema(BaseModel):
    """收入记录"""
    ticket_id: Optional[int] = Field(default=None, ge=1, description="关联工单ID")
    amount: float = Field(..., gt=0, description="收入金额")
    payment_method: Optional[str] = Field(default="现金", description="收款方式")
    received_at: Optional[str] = Field(default=None, description="收款日期")
    notes: Optional[str] = Field(default=None, description="备注")


class ExpenseRecordSchema(BaseModel):
    """支出记录"""
    amount: float = Field(..., gt=0, description="支出金额")
    category: Optional[str] = Field(default="其他", description="支出类别")
    description: Optional[str] = Field(default=None, min_length=1, description="支出描述")
    related_ticket_id: Optional[int] = Field(default=None, description="关联工单ID")
    incurred_at: Optional[str] = Field(default=None, description="发生日期")
    supplier: Optional[str] = Field(default=None, description="供应商")


# ============================================================
#  库存 Inventory
# ============================================================

class InventoryAdjustSchema(BaseModel):
    """出入库操作"""
    goods_id: Optional[int] = Field(default=None, ge=1, description="商品ID")
    change_quantity: float = Field(..., description="数量变更(正=入库,负=出库)")
    type: str = Field(default="adjust", description="操作类型: in/out/adjust")
    warehouse_id: Optional[int] = Field(default=None, ge=1, description="仓库ID")
    remark: Optional[str] = Field(default=None, description="备注")


class InventoryCreateSchema(BaseModel):
    """创建库存记录"""
    goods_id: Optional[int] = Field(default=None, ge=1)
    quantity: float = Field(default=0, ge=0)
    cost_price: Optional[float] = Field(default=None, ge=0)
    price: Optional[float] = Field(default=None, ge=0)
    min_stock: int = Field(default=5, ge=0)
    unit: str = Field(default="个")
    location: Optional[str] = Field(default=None)
    barcode: Optional[str] = Field(default=None)
    warehouse_id: Optional[int] = Field(default=None)


# ============================================================
#  设备 Equipment
# ============================================================

class EquipmentCreateSchema(BaseModel):
    """创建设备"""
    name: str = Field(..., min_length=1, max_length=200, description="设备名称")
    client: str = Field(..., min_length=1, max_length=200, description="所属客户")
    brand: Optional[str] = Field(default=None, description="品牌")
    model: Optional[str] = Field(default=None, description="型号")
    serial_no: Optional[str] = Field(default=None, description="序列号")
    location: Optional[str] = Field(default=None, description="位置")
    install_date: Optional[str] = Field(default=None, description="安装日期")
    warranty_expire: Optional[str] = Field(default=None, description="保修到期")
    notes: Optional[str] = Field(default=None, description="备注")


# ============================================================
#  通用查询 Query Schemas
# ============================================================

class PaginationQuery(BaseModel):
    """通用分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=30, ge=1, le=200, description="每页条数")


class DateRangeQuery(BaseModel):
    """日期范围查询"""
    date_from: Optional[str] = Field(default=None, description="开始日期 YYYY-MM-DD")
    date_to: Optional[str] = Field(default=None, description="结束日期 YYYY-MM-DD")


class KeywordQuery(BaseModel):
    """关键词搜索"""
    q: Optional[str] = Field(default=None, max_length=100, description="搜索关键词")


class TicketListQuery(KeywordQuery, PaginationQuery):
    """工单列表查询"""
    status: Optional[str] = Field(default=None, description="按状态筛选")
    client: Optional[str] = Field(default=None, description="按客户筛选")
    sort: Optional[str] = Field(default="created_at_desc", description="排序方式")


class FinanceMonthQuery(BaseModel):
    """财务月度查询"""
    month: Optional[str] = Field(default=None, description="月份 YYYY-MM")