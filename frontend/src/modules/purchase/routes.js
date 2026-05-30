export default [
  {
    path: '/purchase',
    name: 'PurchaseList',
    component: () => import('./views/Purchase.vue'),
    meta: { title: '采购管理' }
  }
]
