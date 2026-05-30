export default [
  {
    path: '/warehouses',
    name: 'WarehouseList',
    component: () => import('./views/Warehouses.vue'),
    meta: { title: '仓库管理' }
  }
]
