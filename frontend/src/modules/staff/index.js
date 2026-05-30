import routes from './routes'
import * as api from './api'

export default {
  name: 'staff',
  routes,
  api,

  nav: {
    title: '员工管理',
    icon: 'bi-person-gear',
    path: '/staff',
    order: 80,
    group: '运营',
    routeName: 'Staff',
    children: [],
  },

  features: [
    { name: 'list', endpoint: 'GET /technicians/', status: 'done' },
    { name: 'getStats', endpoint: 'GET /technicians/stats', status: 'done' },
    { name: 'getSummary', endpoint: 'GET /technicians/summary', status: 'done' },
    { name: 'getProfitRanking', endpoint: 'GET /technicians/profit-ranking', status: 'done' },
    { name: 'getById', endpoint: 'GET /technicians/:id', status: 'done' },
    { name: 'getTickets', endpoint: 'GET /technicians/:id/tickets', status: 'done' },
    { name: 'create', endpoint: 'POST /technicians/', status: 'done' },
    { name: 'update', endpoint: 'PUT /technicians/:id', status: 'done' },
    { name: 'delete', endpoint: 'DELETE /technicians/:id', status: 'done' },
  ]
}
