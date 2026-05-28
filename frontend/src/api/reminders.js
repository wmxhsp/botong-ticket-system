import client from './client'

export const reminderApi = {
  getAll() {
    return client.get('/reminders/all')
  },
  getPending() {
    return client.get('/reminders/pending')
  },
  markRead(id) {
    return client.put(`/reminders/read/${id}`)
  },
  getCount() {
    return client.get('/reminders/count')
  },
  markAllRead() {
    return client.put('/reminders/read-all')
  },
  /** 工单提醒列表 */
  getTicketReminders(ticketId) {
    return client.get(`/reminders/ticket/${ticketId}`)
  },
  /** 创建工单提醒 */
  createTicketReminder(ticketId, data) {
    return client.post(`/reminders/ticket/${ticketId}`, data)
  },
  /** 删除工单提醒 */
  deleteTicketReminder(ticketId) {
    return client.delete(`/reminders/ticket/${ticketId}`)
  },
  /** 订阅到期提醒 */
  getSubscriptionExpiry() {
    return client.get('/reminders/subscription-expiry')
  },
}
