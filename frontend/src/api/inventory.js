import client from './client'

/**
 * 库存 API
 */
export const inventoryApi = {
  /** 库存列表 */
  list(params = {}) {
    return client.get('/inventory/', { params }).then(r => r.data)
  },

  /** 出入库操作 */
  adjust(data) {
    return client.post('/stock/adjust', data)
  },

  /** 销售出库 */
  sale(data) {
    return client.post('/stock/sale', data)
  },

  /** 库存盘点 */
  count(data) {
    return client.post('/stock/count', data)
  },

  /** 库存流水 */
  getLogs(params = {}) {
    return client.get('/stock/logs', { params }).then(r => r.data)
  },

  /** 库存预警 */
  getAlerts(params = {}) {
    return client.get('/stock/alerts', { params }).then(r => r.data)
  },

  /** 销售记录 */
  getSales(params = {}) {
    return client.get('/stock/sale', { params }).then(r => r.data)
  },
}
