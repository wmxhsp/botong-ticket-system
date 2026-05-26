import client from './client'

export const supplierApi = {
  list(params = {}) {
    return client.get('/suppliers/', { params }).then(r => r.data)
  },
  create(data) {
    return client.post('/suppliers/', data)
  },
  update(id, data) {
    return client.put(`/suppliers/${id}`, data)
  },
  delete(id) {
    return client.delete(`/suppliers/${id}`)
  },
}
