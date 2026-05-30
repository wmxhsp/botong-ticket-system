import client from './client'
import type { ApiResponse } from './schemas'
import type { PurchaseOrder } from '@/types'

export const purchaseApi = {
  list() {
    return client.get('/purchase/')
  },

  create(data: any) {
    return client.post('/purchase/', data)
  },

  stats() {
    return client.get('/purchase/stats')
  },

  get(poId) {
    return client.get(`/purchase/${poId}`)
  },

  update(poId: number | string, data: any) {
    return client.put(`/purchase/${poId}`, data)
  },

  delete(poId: number | string) {
    return client.delete(`/purchase/${poId}`)
  },

  receive(poId, data) {
    return client.post(`/purchase/${poId}/receive`, data)
  },

  unpaid() {
    return client.get('/purchase/unpaid')
  },

  pay(poId, data) {
    return client.post(`/purchase/${poId}/pay`, data)
  },
}
