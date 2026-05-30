import routes from './routes'
import * as api from './api'

export default {
  name: 'stats',
  routes,
  api,

  nav: {
    title: '统计分析',
    icon: 'bi-graph-up',
    path: '/stats',
    order: 130,
    group: '财务',
    routeName: 'Stats',
    children: [],
  },

  features: [
    { name: 'getAll', endpoint: 'GET /stats/', status: 'done' },
    { name: 'getSummary', endpoint: 'GET /dashboard/summary', status: 'done' },
    { name: 'getStockAlerts', endpoint: 'GET /stock/alerts', status: 'done' },
  ]
}
