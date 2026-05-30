import client from './client'
import type { ApiResponse } from './schemas'
import type { Warehouse } from '@/types'

export const warehouseApi = {
  list(params: Record<string, any> = {}) {
    return client.get('/stock/warehouses', { params })
  },
  create(data: any) {
    return client.post('/stock/warehouses', data)
  },
  update(id: number | string, data: any) {
    return client.put(`/stock/warehouses/${id}`, data)
  },
  delete(id: number | string) {
    return client.delete(`/stock/warehouses/${id}`)
  },
}
