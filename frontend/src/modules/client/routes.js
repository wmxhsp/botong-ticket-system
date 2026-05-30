export default [
  {
    path: '/clients',
    name: 'ClientList',
    component: () => import('./views/Clients.vue'),
    meta: { title: '客户列表' }
  },
  {
    path: '/clients/:name',
    name: 'ClientDetail',
    component: () => import('./views/ClientDetail.vue'),
    meta: { title: '客户详情' }
  }
]
