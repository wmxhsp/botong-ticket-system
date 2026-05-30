import client from '@/api/client'

export function getSummary(params = {}) {
  return client.get('/api/v1/dashboard/summary', { params })
}

export function getStockAlerts(params = {}) {
  return client.get('/api/v1/stock/alerts', { params })
}
