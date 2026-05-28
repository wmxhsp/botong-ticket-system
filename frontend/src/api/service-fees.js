import client from './client'

export const serviceFeeApi = {
  list(params = {}) {
    return client.get('/service-fees/', { params })
  },
  getTypes() {
    return client.get('/service-fees/types')
  },
  create(data) {
    return client.post('/service-fees/', data)
  },
  update(id, data) {
    return client.put(`/service-fees/${id}`, data)
  },
  delete(id) {
    return client.delete(`/service-fees/${id}`)
  },
}
