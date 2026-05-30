import client from './client'
import type { ApiResponse } from './schemas'
import type { Goods, PaginationParams } from '@/types'
import type { GoodsCategory, GoodsType } from '@/types/api'

// 商品列表查询参数
export interface GoodsListParams extends PaginationParams {
  keyword?: string
  category_id?: number | string
}

export const goodsApi = {
  list(params: GoodsListParams = {}): Promise<ApiResponse<{ items: Goods[]; total: number }>> {
    return client.get('/goods/', { params })
  },

  create(data: Partial<Goods>): Promise<ApiResponse<Goods>> {
    return client.post('/goods/', data)
  },

  get(goodsId: number | string): Promise<ApiResponse<Goods>> {
    return client.get(`/goods/${goodsId}`)
  },

  update(goodsId: number | string, data: Partial<Goods>): Promise<ApiResponse<Goods>> {
    return client.put(`/goods/${goodsId}`, data)
  },

  delete(goodsId: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/goods/${goodsId}`)
  },

  listCategories(): Promise<ApiResponse<GoodsCategory[]>> {
    return client.get('/goods/categories')
  },

  createCategory(data: Partial<GoodsCategory>): Promise<ApiResponse<GoodsCategory>> {
    return client.post('/goods/categories', data)
  },

  getCategory(catId: number | string): Promise<ApiResponse<GoodsCategory>> {
    return client.get(`/goods/categories/${catId}`)
  },

  updateCategory(catId: number | string, data: Partial<GoodsCategory>): Promise<ApiResponse<GoodsCategory>> {
    return client.put(`/goods/categories/${catId}`, data)
  },

  deleteCategory(catId: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/goods/categories/${catId}`)
  },

  listTypesByCategory(catId: number | string): Promise<ApiResponse<GoodsType[]>> {
    return client.get(`/goods/categories/${catId}/types`)
  },

  createTypeInCategory(catId: number | string, data: Partial<GoodsType>): Promise<ApiResponse<GoodsType>> {
    return client.post(`/goods/categories/${catId}/types`, data)
  },

  listAllTypes(): Promise<ApiResponse<GoodsType[]>> {
    return client.get('/goods/types')
  },

  createType(data: Partial<GoodsType>): Promise<ApiResponse<GoodsType>> {
    return client.post('/goods/types', data)
  },

  updateType(typeId: number | string, data: Partial<GoodsType>): Promise<ApiResponse<GoodsType>> {
    return client.put(`/goods/types/${typeId}`, data)
  },

  deleteType(typeId: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/goods/types/${typeId}`)
  },
}
