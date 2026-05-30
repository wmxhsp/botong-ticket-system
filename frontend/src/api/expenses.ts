import client from './client'
import type { ApiResponse } from './schemas'
import type { Expense } from '@/types'

// 支出类别
export interface ExpenseCategory {
  id: number | string
  name: string
  color?: string
  icon?: string
}

// 个人预算
export interface PersonalBudget {
  category: string
  monthly_limit: number
  current_spent: number
  remaining: number
}

// 循环支出
export interface RecurringExpense {
  id: number | string
  description: string
  amount: number
  frequency: 'daily' | 'weekly' | 'monthly' | 'yearly'
  next_due_date: string
  category?: string
}

export const expenseApi = {
  listCategories(): Promise<ApiResponse<ExpenseCategory[]>> {
    return client.get('/expenses/categories')
  },

  createCategory(data: Partial<ExpenseCategory>): Promise<ApiResponse<ExpenseCategory>> {
    return client.post('/expenses/categories', data)
  },

  updateCategory(data: Partial<ExpenseCategory>): Promise<ApiResponse<ExpenseCategory>> {
    return client.put('/expenses/categories', data)
  },

  deleteCategory(catId: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/expenses/categories/${catId}`)
  },

  list(): Promise<ApiResponse<Expense[]>> {
    return client.get('/expenses/')
  },

  create(data: Partial<Expense>): Promise<ApiResponse<Expense>> {
    return client.post('/expenses/', data)
  },

  update(expId: number | string, data: Partial<Expense>): Promise<ApiResponse<Expense>> {
    return client.put(`/expenses/${expId}`, data)
  },

  delete(expId: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/expenses/${expId}`)
  },

  listPersonal(params: { page?: number; per_page?: number } = {}): Promise<ApiResponse<Expense[]>> {
    return client.get('/expenses/personal', { params })
  },

  addPersonal(data: Partial<Expense>): Promise<ApiResponse<Expense>> {
    return client.post('/expenses/personal', data)
  },

  personalSummary(params: { period?: string } = {}): Promise<ApiResponse<any>> {
    return client.get('/expenses/personal/summary', { params })
  },

  getPersonalBudget(params: { category?: string } = {}): Promise<ApiResponse<PersonalBudget>> {
    return client.get('/expenses/personal/budget', { params })
  },

  setPersonalBudget(data: Partial<PersonalBudget>): Promise<ApiResponse<PersonalBudget>> {
    return client.post('/expenses/personal/budget', data)
  },

  listRecurring(): Promise<ApiResponse<RecurringExpense[]>> {
    return client.get('/expenses/personal/recurring')
  },

  createRecurring(data: Partial<RecurringExpense>): Promise<ApiResponse<RecurringExpense>> {
    return client.post('/expenses/personal/recurring', data)
  },

  updatePersonalItem(expId: number | string, data: Partial<Expense>): Promise<ApiResponse<Expense>> {
    return client.put(`/expenses/personal/item/${expId}`, data)
  },

  deletePersonalItem(expId: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/expenses/personal/item/${expId}`)
  },
}
