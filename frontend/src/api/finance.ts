import client from './client'

/**
 * 财务 API
 *
 * 封装所有财务相关的后端接口，包括收入、支出、报表、对账等。
 */

export interface FinanceSummaryParams {
  start_date?: string
  end_date?: string
  period?: 'day' | 'week' | 'month' | 'year'
}

export interface ExpenseListParams {
  page?: number
  per_page?: number
  category?: string
  start_date?: string
  end_date?: string
}

export interface IncomeListParams {
  page?: number
  per_page?: number
  client?: string
  start_date?: string
  end_date?: string
}

export interface IncomeRecordData {
  client: string
  amount: number
  payment_method?: string
  description?: string
  source_type?: string
  source_id?: number | string
  received_at?: string
}

export interface ExpenseRecordData {
  category: string
  amount: number
  vendor?: string
  description?: string
  paid_at?: string
  related_ticket_id?: number | string
}

export interface PaymentData {
  ticket_id?: number | string
  amount: number
  method?: string
  note?: string
}

export const financeApi = {
  /** 获取财务汇总 */
  getSummary(params: FinanceSummaryParams = {}) {
    return client.get('/finance/summary', { params })
  },

  /** 获取支出列表 */
  getExpenses(params: ExpenseListParams = {}) {
    return client.get('/finance/expenses', { params })
  },

  /** 获取收入列表 */
  getIncome(params: IncomeListParams = {}) {
    return client.get('/finance/', { params })
  },

  /** 记录收入 */
  recordIncome(data: IncomeRecordData) {
    return client.post('/finance/income', data)
  },

  /** 记录支出 */
  recordExpense(data: ExpenseRecordData) {
    return client.post('/expenses/', data)
  },

  /** 获取待付款项 */
  getPendingPayments(params: { page?: number; per_page?: number } = {}) {
    return client.get('/finance/unpaid', { params })
  },

  /** 获取财务仪表盘 */
  getDashboard(params: FinanceSummaryParams = {}) {
    return client.get('/finance/dashboard', { params })
  },

  /** 付款 */
  pay(data: PaymentData) {
    return client.post('/finance/pay', data)
  },

  /** 批量付款 */
  batchPay(data: { payments: PaymentData[] }) {
    return client.post('/finance/batch-pay', data)
  },

  /** 快速收入 */
  quickIncome(data: IncomeRecordData) {
    return client.post('/finance/quick-income', data)
  },

  /** 获取应收账款 */
  getReceivables(params: { page?: number; per_page?: number; client?: string } = {}) {
    return client.get('/finance/receivables', { params })
  },

  /** 获取逾期应收 */
  getOverdueReceivables(params: { page?: number; per_page?: number } = {}) {
    return client.get('/finance/receivables/overdue', { params })
  },

  /** 获取客户对账单 */
  getClientStatement(clientName: string, params: { start_date?: string; end_date?: string } = {}) {
    return client.get(`/finance/statement/client/${encodeURIComponent(clientName)}`, { params })
  },

  /** 获取供应商对账单 */
  getSupplierStatement(supplierId: number | string, params: { start_date?: string; end_date?: string } = {}) {
    return client.get(`/finance/statement/supplier/${supplierId}`, { params })
  },

  /** 部分付款 */
  partialPay(data: { ticket_id: number | string; amount: number; method?: string }) {
    return client.post('/finance/partial-pay', data)
  },

  /** 获取付款历史 */
  getPaymentHistory(ticketId: number | string) {
    return client.get(`/finance/payment-history/${ticketId}`)
  },

  /** 获取销售报表 */
  getSalesReport(params: { start_date?: string; end_date?: string; group_by?: string } = {}) {
    return client.get('/finance/sales-report', { params })
  },

  /** 获取工单利润 */
  getTicketProfit(params: { ticket_id?: number | string; start_date?: string; end_date?: string } = {}) {
    return client.get('/finance/ticket-profit', { params })
  },

  /** 获取账龄分析 */
  getAging(clientName: string, params: { as_of_date?: string } = {}) {
    return client.get(`/finance/aging/${encodeURIComponent(clientName)}`, { params })
  },

  /** 更新财务支出 */
  updateExpense(expId: number | string, data: Partial<ExpenseRecordData>) {
    return client.put(`/finance/expenses/${expId}`, data)
  },

  /** 删除财务支出 */
  deleteExpense(expId: number | string) {
    return client.delete(`/finance/expenses/${expId}`)
  },
}
