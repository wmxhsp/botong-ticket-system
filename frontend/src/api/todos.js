import client from './client'

export const todoApi = {
  list(params = {}) {
    return client.get('/todos/', { params }).then(r => r.data)
  },
  getStats() {
    return client.get('/todos/stats').then(r => r.data)
  },
  create(data) {
    return client.post('/todos/', data)
  },
  update(id, data) {
    return client.put(`/todos/${id}`, data)
  },
  delete(id) {
    return client.delete(`/todos/${id}`)
  },
}
