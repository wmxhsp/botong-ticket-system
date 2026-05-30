export default [
  {
    path: '/service-fees',
    name: 'ServiceFeeList',
    component: () => import('./views/ServiceFees.vue'),
    meta: { title: '服务费率' }
  }
]
