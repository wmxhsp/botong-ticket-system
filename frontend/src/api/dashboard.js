import client from './client'

export const dashboardApi = {
  getSummary(params = {}) {
    return client.get('/dashboard/summary', { params })
  },
  getStockAlerts(params = {}) {
    return client.get('/stock/alerts', { params })
  },
}
