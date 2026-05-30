import client from './client'
import type { ApiResponse } from './schemas'
import type { Supplier } from '@/types'

export const supplierApi = {
  list(params: Record<string, any> = {}) {
    return client.get('/suppliers/', { params })
  },
  /** 供应商统计 */
  getStats() {
    return client.get('/suppliers/stats')
  },
  create(data: any) {
    return client.post('/suppliers/', data)
  },
  getById(id: number | string) {
    return client.get(`/suppliers/${id}`)
  },
  update(id: number | string, data: any) {
    return client.put(`/suppliers/${id}`, data)
  },
  delete(id: number | string) {
    return client.delete(`/suppliers/${id}`)
  },
}
