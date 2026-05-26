import client from './client'

/**
 * 统计/仪表盘 API
 */
export const statsApi = {
  /** 全局统计 */
  getAll(params = {}) {
    return client.get('/stats/', { params }).then(r => r.data)
  },

  /** 仪表盘摘要 */
  getSummary(params = {}) {
    return client.get('/dashboard/summary', { params }).then(r => r.data)
  },

  /** 库存预警（仪表盘用） */
  getStockAlerts(params = {}) {
    return client.get('/stock/alerts', { params }).then(r => r.data)
  },
}
