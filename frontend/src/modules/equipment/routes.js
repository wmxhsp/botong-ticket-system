export default [
  {
    path: '/equipment',
    name: 'EquipmentList',
    component: () => import('./views/Equipment.vue'),
    meta: { title: '设备列表' }
  },
  {
    path: '/equipment/:id',
    name: 'EquipmentDetail',
    component: () => import('./views/EquipmentDetail.vue'),
    meta: { title: '设备详情' }
  }
]
