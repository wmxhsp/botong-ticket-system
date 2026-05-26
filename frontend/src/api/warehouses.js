import client from './client'

export const warehouseApi = {
  list(params = {}) {
    return client.get('/stock/warehouses', { params }).then(r => r.data)
  },
  create(data) {
    return client.post('/stock/warehouses', data)
  },
  update(id, data) {
    return client.put(`/stock/warehouses/${id}`, data)
  },
  delete(id) {
    return client.delete(`/stock/warehouses/${id}`)
  },
}
