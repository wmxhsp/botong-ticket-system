import routes from './routes'
import * as api from './api'

export default {
  name: 'expense',
  routes,
  api,

  nav: {
    title: '支出管理',
    icon: 'bi-receipt',
    path: '/expenses',
    order: 70,
    group: '财务',
    routeName: 'Expenses',
    children: [],
  },

  features: [
    { name: 'listCategories', endpoint: 'GET /expenses/categories', status: 'done' },
    { name: 'createCategory', endpoint: 'POST /expenses/categories', status: 'done' },
    { name: 'updateCategory', endpoint: 'PUT /expenses/categories', status: 'done' },
    { name: 'deleteCategory', endpoint: 'DELETE /expenses/categories/:id', status: 'done' },
    { name: 'list', endpoint: 'GET /expenses/', status: 'done' },
    { name: 'create', endpoint: 'POST /expenses/', status: 'done' },
    { name: 'update', endpoint: 'PUT /expenses/:id', status: 'done' },
    { name: 'delete', endpoint: 'DELETE /expenses/:id', status: 'done' },
    { name: 'listPersonal', endpoint: 'GET /expenses/personal', status: 'done' },
    { name: 'addPersonal', endpoint: 'POST /expenses/personal', status: 'done' },
    { name: 'personalSummary', endpoint: 'GET /expenses/personal/summary', status: 'done' },
    { name: 'getPersonalBudget', endpoint: 'GET /expenses/personal/budget', status: 'done' },
    { name: 'setPersonalBudget', endpoint: 'POST /expenses/personal/budget', status: 'done' },
    { name: 'listRecurring', endpoint: 'GET /expenses/personal/recurring', status: 'done' },
    { name: 'createRecurring', endpoint: 'POST /expenses/personal/recurring', status: 'done' },
    { name: 'updatePersonalItem', endpoint: 'PUT /expenses/personal/item/:id', status: 'done' },
    { name: 'deletePersonalItem', endpoint: 'DELETE /expenses/personal/item/:id', status: 'done' },
  ]
}
