import client from './client'

export const purchaseApi = {
  list() {
    return client.get('/purchase/').then(r => r.data)
  },

  create(data) {
    return client.post('/purchase/', data)
  },

  stats() {
    return client.get('/purchase/stats').then(r => r.data)
  },

  get(poId) {
    return client.get(`/purchase/${poId}`).then(r => r.data)
  },

  update(poId, data) {
    return client.put(`/purchase/${poId}`, data)
  },

  delete(poId) {
    return client.delete(`/purchase/${poId}`)
  },

  receive(poId, data) {
    return client.post(`/purchase/${poId}/receive`, data)
  },

  unpaid() {
    return client.get('/purchase/unpaid').then(r => r.data)
  },

  pay(poId, data) {
    return client.post(`/purchase/${poId}/pay`, data)
  },
}
