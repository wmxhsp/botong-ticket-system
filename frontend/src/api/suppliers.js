import client from './client'

export const supplierApi = {
  list(params = {}) {
    return client.get('/suppliers/', { params })
  },
  /** 供应商统计 */
  getStats() {
    return client.get('/suppliers/stats')
  },
  create(data) {
    return client.post('/suppliers/', data)
  },
  getById(id) {
    return client.get(`/suppliers/${id}`)
  },
  update(id, data) {
    return client.put(`/suppliers/${id}`, data)
  },
  delete(id) {
    return client.delete(`/suppliers/${id}`)
  },
}
