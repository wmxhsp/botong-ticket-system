export default [
  {
    path: '/stats',
    name: 'StatsOverview',
    component: () => import('./views/Stats.vue'),
    meta: { title: '统计分析' }
  }
]
