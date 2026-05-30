import routes from './routes'
import * as api from './api'

export default {
  name: 'client',
  routes,
  api,

  nav: {
    title: '客户管理',
    icon: 'bi-people',
    path: '/clients',
    order: 20,
    group: '业务',
    routeName: 'ClientList',
    children: ['ClientDetail'],
  },

  features: [
    { name: 'list', endpoint: 'GET /clients/', status: 'done' },
    { name: 'getByName', endpoint: 'GET /clients/:name', status: 'done' },
    { name: 'getProfile', endpoint: 'GET /clients/:name/profile', status: 'done' },
    { name: 'getOverview', endpoint: 'GET /clients/:name/overview', status: 'done' },
    { name: 'getTierConfig', endpoint: 'GET /clients/tier-config', status: 'done' },
    { name: 'create', endpoint: 'POST /clients/', status: 'done' },
    { name: 'update', endpoint: 'PUT /clients/:name', status: 'done' },
    { name: 'delete', endpoint: 'DELETE /clients/:name', status: 'done' },
  ]
}
