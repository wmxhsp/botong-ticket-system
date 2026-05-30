export default [
  {
    path: '/staff',
    name: 'StaffList',
    component: () => import('./views/Staff.vue'),
    meta: { title: '员工管理' }
  }
]
