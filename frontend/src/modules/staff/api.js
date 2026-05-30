import client from '@/api/client'

export const staffApi = {
  list(params = {}) {
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
  getById(id) {
    return client.get(`/technicians/${id}`)
  },
  /** 技师关联工单 */
  getTickets(id) {
    return client.get(`/technicians/${id}/tickets`)
  },
  create(data) {
    return client.post('/technicians/', data)
  },
  update(id, data) {
    return client.put(`/technicians/${id}`, data)
  },
  delete(id) {
    return client.delete(`/technicians/${id}`)
  },
}
