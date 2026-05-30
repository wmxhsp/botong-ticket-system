export default [
  {
    path: '/suppliers',
    name: 'SupplierList',
    component: () => import('./views/Suppliers.vue'),
    meta: { title: '供应商' }
  }
]
