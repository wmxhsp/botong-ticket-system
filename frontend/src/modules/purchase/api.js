import client from '@/api/client'

export const purchaseApi = {
  list() {
    return client.get('/purchase/')
  },

  create(data) {
    return client.post('/purchase/', data)
  },

  stats() {
    return client.get('/purchase/stats')
  },

  get(poId) {
    return client.get(`/purchase/${poId}`)
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
    return client.get('/purchase/unpaid')
  },

  pay(poId, data) {
    return client.post(`/purchase/${poId}/pay`, data)
  },
}
