export default [
  {
    path: '',
    name: 'Dashboard',
    component: () => import('./views/Dashboard.vue'),
    meta: { title: '仪表盘', keepAlive: true },
  },
]
