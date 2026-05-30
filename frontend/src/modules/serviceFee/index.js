import routes from './routes'
import * as api from './api'

export default {
  name: 'serviceFee',
  routes,
  api,

  nav: {
    title: '服务费率',
    icon: 'bi-tags',
    path: '/service-fees',
    order: 110,
    group: '运营',
    routeName: 'ServiceFees',
    children: [],
  },

  features: [
    { name: 'list', endpoint: 'GET /service-fees/', status: 'done' },
    { name: 'getTypes', endpoint: 'GET /service-fees/types', status: 'done' },
    { name: 'create', endpoint: 'POST /service-fees/', status: 'done' },
    { name: 'update', endpoint: 'PUT /service-fees/:id', status: 'done' },
    { name: 'delete', endpoint: 'DELETE /service-fees/:id', status: 'done' },
  ]
}
