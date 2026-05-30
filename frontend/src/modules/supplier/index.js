import routes from './routes'
import * as api from './api'

export default {
  name: 'supplier',
  routes,
  api,

  nav: {
    title: '供应商',
    icon: 'bi-truck',
    path: '/suppliers',
    order: 90,
    group: '运营',
    routeName: 'Suppliers',
    children: [],
  },

  features: [
    { name: 'list', endpoint: 'GET /suppliers/', status: 'done' },
    { name: 'getStats', endpoint: 'GET /suppliers/stats', status: 'done' },
    { name: 'create', endpoint: 'POST /suppliers/', status: 'done' },
    { name: 'getById', endpoint: 'GET /suppliers/:id', status: 'done' },
    { name: 'update', endpoint: 'PUT /suppliers/:id', status: 'done' },
    { name: 'delete', endpoint: 'DELETE /suppliers/:id', status: 'done' },
  ]
}
