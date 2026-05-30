export default [
  {
    path: '/todos',
    name: 'TodoList',
    component: () => import('./views/Todos.vue'),
    meta: { title: '待办事项' }
  }
]
