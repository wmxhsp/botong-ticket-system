import client from './client'
import type { ApiResponse, DashboardStats, PaginatedResponse } from '@/types'

/**
 * 仪表盘 API
 *
 * 封装仪表盘数据相关的后端接口，包括汇总统计、库存预警等。
 */

export interface DashboardSummaryParams {
  start_date?: string
  end_date?: string
  period?: 'day' | 'week' | 'month' | 'year'
}

export interface StockAlertParams {
  page?: number
  per_page?: number
  alert_type?: 'low' | 'high' | 'expired'
}

export const dashboardApi = {
  /** 获取仪表盘汇总数据 */
  getSummary(params: DashboardSummaryParams = {}): Promise<ApiResponse<DashboardStats>> {
    return client.get('/dashboard/summary', { params })
  },

  /** 获取库存预警 */
  getStockAlerts(params: StockAlertParams = {}): Promise<ApiResponse<PaginatedResponse<any>>> {
    return client.get('/stock/alerts', { params })
  },
}
