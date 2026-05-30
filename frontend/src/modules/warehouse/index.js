import routes from './routes'
import * as api from './api'

export default {
  name: 'warehouse',
  routes,
  api,

  nav: {
    title: '仓库管理',
    icon: 'bi-building',
    path: '/warehouses',
    order: 100,
    group: '运营',
    routeName: 'Warehouses',
    children: [],
  },

  features: [
    { name: 'list', endpoint: 'GET /stock/warehouses', status: 'done' },
    { name: 'create', endpoint: 'POST /stock/warehouses', status: 'done' },
    { name: 'update', endpoint: 'PUT /stock/warehouses/:id', status: 'done' },
    { name: 'delete', endpoint: 'DELETE /stock/warehouses/:id', status: 'done' },
  ]
}
