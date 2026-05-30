import routes from './routes'
import * as api from './api'

export default {
  name: 'purchase',
  routes,
  api,

  nav: {
    title: '采购管理',
    icon: 'bi-cart',
    path: '/purchase',
    order: 60,
    group: '运营',
    routeName: 'Purchase',
    children: [],
  },

  features: [
    { name: 'list', endpoint: 'GET /purchase/', status: 'done' },
    { name: 'create', endpoint: 'POST /purchase/', status: 'done' },
    { name: 'stats', endpoint: 'GET /purchase/stats', status: 'done' },
    { name: 'get', endpoint: 'GET /purchase/:poId', status: 'done' },
    { name: 'update', endpoint: 'PUT /purchase/:poId', status: 'done' },
    { name: 'delete', endpoint: 'DELETE /purchase/:poId', status: 'done' },
    { name: 'receive', endpoint: 'POST /purchase/:poId/receive', status: 'done' },
    { name: 'unpaid', endpoint: 'GET /purchase/unpaid', status: 'done' },
    { name: 'pay', endpoint: 'POST /purchase/:poId/pay', status: 'done' },
  ]
}
