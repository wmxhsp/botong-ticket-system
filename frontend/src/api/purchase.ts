import client from './client'
import type { ApiResponse } from './schemas'
import type { PurchaseOrder } from '@/types'

export const purchaseApi = {
  list(): Promise<ApiResponse<PurchaseOrder[]>> {
    return client.get('/purchase/')
  },

  create(data: Partial<PurchaseOrder>): Promise<ApiResponse<PurchaseOrder>> {
    return client.post('/purchase/', data)
  },

  stats(): Promise<ApiResponse<any>> {
    return client.get('/purchase/stats')
  },

  get(poId: number | string): Promise<ApiResponse<PurchaseOrder>> {
    return client.get(`/purchase/${poId}`)
  },

  update(poId: number | string, data: Partial<PurchaseOrder>): Promise<ApiResponse<PurchaseOrder>> {
    return client.put(`/purchase/${poId}`, data)
  },

  delete(poId: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/purchase/${poId}`)
  },

  receive(poId: number | string, data: Record<string, any>): Promise<ApiResponse<PurchaseOrder>> {
    return client.post(`/purchase/${poId}/receive`, data)
  },

  unpaid(): Promise<ApiResponse<PurchaseOrder[]>> {
    return client.get('/purchase/unpaid')
  },

  pay(poId: number | string, data: Record<string, any>): Promise<ApiResponse<PurchaseOrder>> {
    return client.post(`/purchase/${poId}/pay`, data)
  },
}
