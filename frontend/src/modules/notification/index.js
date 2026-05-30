import routes from './routes'
import * as api from './api'

export default {
  name: 'notification',
  routes,
  api,

  nav: {
    title: '通知中心',
    icon: 'bi-bell',
    path: '/notifications',
    order: 140,
    group: '工作台',
    routeName: 'Notifications',
    children: [],
  },

  features: [
    { name: 'getAll', endpoint: 'GET /reminders/all', status: 'done' },
    { name: 'getPending', endpoint: 'GET /reminders/pending', status: 'done' },
    { name: 'markRead', endpoint: 'PUT /reminders/read/:id', status: 'done' },
    { name: 'getCount', endpoint: 'GET /reminders/count', status: 'done' },
    { name: 'markAllRead', endpoint: 'PUT /reminders/read-all', status: 'done' },
    { name: 'getTicketReminders', endpoint: 'GET /reminders/ticket/:id', status: 'done' },
    { name: 'createTicketReminder', endpoint: 'POST /reminders/ticket/:id', status: 'done' },
    { name: 'deleteTicketReminder', endpoint: 'DELETE /reminders/ticket/:id', status: 'done' },
    { name: 'getSubscriptionExpiry', endpoint: 'GET /reminders/subscription-expiry', status: 'done' },
  ]
}
