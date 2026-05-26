import client from './client'

export const expenseApi = {
  listCategories() {
    return client.get('/expenses/categories').then(r => r.data)
  },

  createCategory(data) {
    return client.post('/expenses/categories', data)
  },

  updateCategory(data) {
    return client.put('/expenses/categories', data)
  },

  deleteCategory(catId) {
    return client.delete(`/expenses/categories/${catId}`)
  },

  list() {
    return client.get('/expenses/').then(r => r.data)
  },

  create(data) {
    return client.post('/expenses/', data)
  },

  update(expId, data) {
    return client.put(`/expenses/${expId}`, data)
  },

  delete(expId) {
    return client.delete(`/expenses/${expId}`)
  },

  listPersonal(params = {}) {
    return client.get('/expenses/personal', { params }).then(r => r.data)
  },

  addPersonal(data) {
    return client.post('/expenses/personal', data)
  },

  personalSummary(params = {}) {
    return client.get('/expenses/personal/summary', { params }).then(r => r.data)
  },

  getPersonalBudget(params = {}) {
    return client.get('/expenses/personal/budget', { params }).then(r => r.data)
  },

  setPersonalBudget(data) {
    return client.post('/expenses/personal/budget', data)
  },

  listRecurring() {
    return client.get('/expenses/personal/recurring').then(r => r.data)
  },

  createRecurring(data) {
    return client.post('/expenses/personal/recurring', data)
  },

  updatePersonalItem(expId, data) {
    return client.put(`/expenses/personal/item/${expId}`, data)
  },

  deletePersonalItem(expId) {
    return client.delete(`/expenses/personal/item/${expId}`)
  },
}
