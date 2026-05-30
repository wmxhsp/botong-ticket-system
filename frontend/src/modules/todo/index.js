import routes from './routes'
import * as api from './api'

export default {
  name: 'todo',
  routes,
  api,

  nav: {
    title: '待办事项',
    icon: 'bi-check2-square',
    path: '/todos',
    order: 120,
    group: '工作台',
    routeName: 'Todos',
    children: [],
  },

  features: [
    { name: 'list', endpoint: 'GET /todos/', status: 'done' },
    { name: 'getStats', endpoint: 'GET /todos/stats', status: 'done' },
    { name: 'getToday', endpoint: 'GET /todos/today', status: 'done' },
    { name: 'getOverdue', endpoint: 'GET /todos/overdue', status: 'done' },
    { name: 'getUpcoming', endpoint: 'GET /todos/upcoming', status: 'done' },
    { name: 'getByTicket', endpoint: 'GET /todos/by-ticket/:id', status: 'done' },
    { name: 'getBySource', endpoint: 'GET /todos/by-source', status: 'done' },
    { name: 'create', endpoint: 'POST /todos/', status: 'done' },
    { name: 'update', endpoint: 'PUT /todos/:id', status: 'done' },
    { name: 'toggle', endpoint: 'PUT /todos/:id/toggle', status: 'done' },
    { name: 'delete', endpoint: 'DELETE /todos/:id', status: 'done' },
    { name: 'listSubtasks', endpoint: 'GET /todos/:id/subtasks', status: 'done' },
    { name: 'createSubtask', endpoint: 'POST /todos/:id/subtasks', status: 'done' },
    { name: 'toggleSubtask', endpoint: 'PUT /todos/subtasks/:id/toggle', status: 'done' },
    { name: 'batch', endpoint: 'PUT /todos/batch', status: 'done' },
    { name: 'cleanup', endpoint: 'POST /todos/cleanup', status: 'done' },
  ]
}
