import client from './client'

export const searchApi = {
  search(params = {}) {
    return client.get('/search', { params })
  },
}
