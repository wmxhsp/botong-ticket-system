import client from './client'

export const reminderApi = {
  getAll() {
    return client.get('/reminders/all').then(r => r.data)
  },
  getPending() {
    return client.get('/reminders/pending').then(r => r.data)
  },
  markRead(id) {
    return client.put(`/reminders/read/${id}`)
  },
  getCount() {
    return client.get('/reminders/count').then(r => r.data)
  },
  markAllRead() {
    return client.put('/reminders/read-all')
  },
}
