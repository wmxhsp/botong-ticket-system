import client from './client'

export const staffApi = {
  list(params = {}) {
    return client.get('/technicians/', { params }).then(r => r.data)
  },
  getStats() {
    return client.get('/technicians/stats').then(r => r.data)
  },
  create(data) {
    return client.post('/technicians/', data)
  },
  update(id, data) {
    return client.put(`/technicians/${id}`, data)
  },
  delete(id) {
    return client.delete(`/technicians/${id}`)
  },
}
