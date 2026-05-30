import client from './client'
import type { ApiResponse } from './schemas'
import type { Goods } from '@/types'

export const goodsApi = {
  list(params: Record<string, any> = {}) {
    return client.get('/goods/', { params })
  },

  create(data: any) {
    return client.post('/goods/', data)
  },

  get(goodsId) {
    return client.get(`/goods/${goodsId}`)
  },

  update(goodsId: number | string, data: any) {
    return client.put(`/goods/${goodsId}`, data)
  },

  delete(goodsId: number | string) {
    return client.delete(`/goods/${goodsId}`)
  },

  listCategories() {
    return client.get('/goods/categories')
  },

  createCategory(data) {
    return client.post('/goods/categories', data)
  },

  getCategory(catId) {
    return client.get(`/goods/categories/${catId}`)
  },

  updateCategory(catId, data) {
    return client.put(`/goods/categories/${catId}`, data)
  },

  deleteCategory(catId) {
    return client.delete(`/goods/categories/${catId}`)
  },

  listTypesByCategory(catId) {
    return client.get(`/goods/categories/${catId}/types`)
  },

  createTypeInCategory(catId, data) {
    return client.post(`/goods/categories/${catId}/types`, data)
  },

  listAllTypes() {
    return client.get('/goods/types')
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
