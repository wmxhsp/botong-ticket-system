import client from '@/api/client'

/**
 * 库存 API
 */
export const inventoryApi = {
  /** 库存列表 */
  list(params = {}) {
    return client.get('/inventory/', { params })
  },

  /** 出入库操作 */
  adjust(data) {
    return client.post('/stock/adjust', data)
  },

  /** 库存调拨 */
  transfer(data) {
    return client.post('/stock/transfer', data)
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
    return client.get('/stock/logs', { params })
  },

  /** 库存预警 */
  getAlerts(params = {}) {
    return client.get('/stock/alerts', { params })
  },

  /** 从预警创建采购 */
  alertPurchase(goodsId, data = {}) {
    return client.post(`/stock/alerts/${goodsId}/purchase`, data)
  },

  /** 销售记录 */
  getSales(params = {}) {
    return client.get('/stock/sale', { params })
  },

  /** 销售续约 */
  renewSale(saleId, data) {
    return client.post(`/stock/sale/${saleId}/renew`, data)
  },
}
