import client from './client'
import type { ApiResponse } from './schemas'
import type { Staff } from '@/types'

export const staffApi = {
  list(params: Record<string, any> = {}) {
    return client.get('/technicians/', { params })
  },
  getStats() {
    return client.get('/technicians/stats')
  },
  /** 技师概览 */
  getSummary() {
    return client.get('/technicians/summary')
  },
  /** 利润排行 */
  getProfitRanking() {
    return client.get('/technicians/profit-ranking')
  },
  /** 技师详情 */
  getById(id: number | string) {
    return client.get(`/technicians/${id}`)
  },
  /** 技师关联工单 */
  getTickets(id) {
    return client.get(`/technicians/${id}/tickets`)
  },
  create(data: any) {
    return client.post('/technicians/', data)
  },
  update(id: number | string, data: any) {
    return client.put(`/technicians/${id}`, data)
  },
  delete(id: number | string) {
    return client.delete(`/technicians/${id}`)
  },
}
