export default [
  {
    path: '/inventory',
    name: 'InventoryList',
    component: () => import('./views/Inventory.vue'),
    meta: { title: '库存管理' }
  }
]
