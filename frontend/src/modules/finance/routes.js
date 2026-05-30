export default [
  {
    path: '/finance',
    name: 'FinanceOverview',
    component: () => import('./views/Finance.vue'),
    meta: { title: '财务管理' }
  }
]
