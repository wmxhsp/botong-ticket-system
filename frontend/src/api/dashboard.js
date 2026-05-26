import client from './client'

export const dashboardApi = {
  getSummary(params = {}) {
    return client.get('/dashboard/summary', { params }).then(r => r.data)
  },
  getStockAlerts(params = {}) {
    return client.get('/stock/alerts', { params }).then(r => r.data)
  },
}
