export default [
  {
    path: '/expenses',
    name: 'ExpenseList',
    component: () => import('./views/Expenses.vue'),
    meta: { title: '支出管理' }
  }
]
