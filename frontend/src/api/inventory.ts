import client from './client'
import type { ApiResponse } from './schemas'
import type { InventoryItem } from '@/types'

// 库存列表查询参数
export interface InventoryListParams {
  page?: number
  per_page?: number
  keyword?: string
  warehouse_id?: number | string
  goods_id?: number | string
}

// 出入库操作数据
export interface StockAdjustData {
  goods_id: number | string
  warehouse_id: number | string
  quantity: number
  direction: 'in' | 'out'
  reason?: string
}

// 库存调拨数据
export interface StockTransferData {
  goods_id: number | string
  from_warehouse_id: number | string
  to_warehouse_id: number | string
  quantity: number
  reason?: string
}

// 销售出库数据
export interface StockSaleData {
  goods_id: number | string
  warehouse_id: number | string
  quantity: number
  customer_id?: number | string
  price?: number
}

// 库存盘点数据
export interface StockCountData {
  goods_id: number | string
  warehouse_id: number | string
  actual_quantity: number
  notes?: string
}

// 库存流水记录
export interface StockLog {
  id: number
  goods_id: number | string
  goods_name?: string
  warehouse_id: number | string
  warehouse_name?: string
  quantity_change: number
  quantity_after: number
  operation_type: string
  operator?: string
  created_at: string
}

// 库存预警
export interface StockAlert {
  id: number
  goods_id: number | string
  goods_name?: string
  warehouse_id: number | string
  warehouse_name?: string
  current_quantity: number
  min_stock: number
  alert_type: 'low' | 'high'
  created_at: string
}

// 销售记录
export interface SaleRecord {
  id: number
  goods_id: number | string
  goods_name?: string
  quantity: number
  unit_price: number
  total_price: number
  customer_id?: number | string
  customer_name?: string
  sale_date: string
  status?: string
}

/**
 * 库存 API
 */
export const inventoryApi = {
  /** 库存列表 */
  list(params: InventoryListParams = {}): Promise<ApiResponse<InventoryItem[]>> {
    return client.get('/inventory/', { params })
  },

  /** 出入库操作 */
  adjust(data: StockAdjustData): Promise<ApiResponse<void>> {
    return client.post('/stock/adjust', data)
  },

  /** 库存调拨 */
  transfer(data: StockTransferData): Promise<ApiResponse<void>> {
    return client.post('/stock/transfer', data)
  },

  /** 销售出库 */
  sale(data: StockSaleData): Promise<ApiResponse<void>> {
    return client.post('/stock/sale', data)
  },

  /** 库存盘点 */
  count(data: StockCountData): Promise<ApiResponse<void>> {
    return client.post('/stock/count', data)
  },

  /** 库存流水 */
  getLogs(params: { page?: number; per_page?: number; goods_id?: number | string } = {}): Promise<ApiResponse<StockLog[]>> {
    return client.get('/stock/logs', { params })
  },

  /** 库存预警 */
  getAlerts(params: { page?: number; per_page?: number } = {}): Promise<ApiResponse<StockAlert[]>> {
    return client.get('/stock/alerts', { params })
  },

  /** 从预警创建采购 */
  alertPurchase(goodsId: number | string, data: Record<string, any> = {}): Promise<ApiResponse<void>> {
    return client.post(`/stock/alerts/${goodsId}/purchase`, data)
  },

  /** 销售记录 */
  getSales(params: { page?: number; per_page?: number; keyword?: string } = {}): Promise<ApiResponse<SaleRecord[]>> {
    return client.get('/stock/sale', { params })
  },

  /** 销售续约 */
  renewSale(saleId: number | string, data: Record<string, any>): Promise<ApiResponse<void>> {
    return client.post(`/stock/sale/${saleId}/renew`, data)
  },
}
