import client from './client'
import type { ApiResponse } from './schemas'
import type { Todo } from '@/types'

export const todoApi = {
  list(params: Record<string, any> = {}) {
    return client.get('/todos/', { params })
  },
  getStats() {
    return client.get('/todos/stats')
  },
  /** 今日待办 */
  getToday() {
    return client.get('/todos/today')
  },
  /** 逾期待办 */
  getOverdue() {
    return client.get('/todos/overdue')
  },
  /** 即将到期 */
  getUpcoming() {
    return client.get('/todos/upcoming')
  },
  /** 按工单查看 */
  getByTicket(ticketId) {
    return client.get(`/todos/by-ticket/${ticketId}`)
  },
  /** 按来源查看 */
  getBySource(params = {}) {
    return client.get('/todos/by-source', { params })
  },
  create(data: any) {
    return client.post('/todos/', data)
  },
  update(id: number | string, data: any) {
    return client.put(`/todos/${id}`, data)
  },
  /** 切换完成状态 */
  toggle(id) {
    return client.put(`/todos/${id}/toggle`)
  },
  delete(id: number | string) {
    return client.delete(`/todos/${id}`)
  },
  /** 子任务列表 */
  listSubtasks(parentId) {
    return client.get(`/todos/${parentId}/subtasks`)
  },
  /** 创建子任务 */
  createSubtask(parentId, data) {
    return client.post(`/todos/${parentId}/subtasks`, data)
  },
  /** 切换子任务状态 */
  toggleSubtask(subtaskId) {
    return client.put(`/todos/subtasks/${subtaskId}/toggle`)
  },
  /** 批量操作 */
  batch(data) {
    return client.put('/todos/batch', data)
  },
  /** 清理已完成 */
  cleanup() {
    return client.post('/todos/cleanup')
  },
}
