import client from './client'

export const goodsApi = {
  list(params = {}) {
    return client.get('/goods/', { params }).then(r => r.data)
  },

  create(data) {
    return client.post('/goods/', data)
  },

  get(goodsId) {
    return client.get(`/goods/${goodsId}`).then(r => r.data)
  },

  update(goodsId, data) {
    return client.put(`/goods/${goodsId}`, data)
  },

  delete(goodsId) {
    return client.delete(`/goods/${goodsId}`)
  },

  listCategories() {
    return client.get('/goods/categories').then(r => r.data)
  },

  createCategory(data) {
    return client.post('/goods/categories', data)
  },

  getCategory(catId) {
    return client.get(`/goods/categories/${catId}`).then(r => r.data)
  },

  updateCategory(catId, data) {
    return client.put(`/goods/categories/${catId}`, data)
  },

  deleteCategory(catId) {
    return client.delete(`/goods/categories/${catId}`)
  },

  listTypesByCategory(catId) {
    return client.get(`/goods/categories/${catId}/types`).then(r => r.data)
  },

  createTypeInCategory(catId, data) {
    return client.post(`/goods/categories/${catId}/types`, data)
  },

  listAllTypes() {
    return client.get('/goods/types').then(r => r.data)
  },

  createType(data) {
    return client.post('/goods/types', data)
  },

  updateType(typeId, data) {
    return client.put(`/goods/types/${typeId}`, data)
  },

  deleteType(typeId) {
    return client.delete(`/goods/types/${typeId}`)
  },
}
