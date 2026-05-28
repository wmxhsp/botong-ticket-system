import client from './client'

export const financeApi = {
  getSummary(params = {}) {
    return client.get('/finance/summary', { params })
  },
  getExpenses(params = {}) {
    return client.get('/finance/expenses', { params })
  },
  getIncome(params = {}) {
    return client.get('/finance/', { params })
  },
  recordIncome(data) {
    return client.post('/finance/income', data)
  },
  recordExpense(data) {
    return client.post('/expenses/', data)
  },
  getPendingPayments(params = {}) {
    return client.get('/finance/unpaid', { params })
  },
  getDashboard(params = {}) {
    return client.get('/finance/dashboard', { params })
  },
  pay(data) {
    return client.post('/finance/pay', data)
  },
  batchPay(data) {
    return client.post('/finance/batch-pay', data)
  },
  quickIncome(data) {
    return client.post('/finance/quick-income', data)
  },
  getReceivables(params = {}) {
    return client.get('/finance/receivables', { params })
  },
  getOverdueReceivables(params = {}) {
    return client.get('/finance/receivables/overdue', { params })
  },
  getClientStatement(clientName, params = {}) {
    return client.get(`/finance/statement/client/${encodeURIComponent(clientName)}`, { params })
  },
  getSupplierStatement(supplierId, params = {}) {
    return client.get(`/finance/statement/supplier/${supplierId}`, { params })
  },
  partialPay(data) {
    return client.post('/finance/partial-pay', data)
  },
  getPaymentHistory(ticketId) {
    return client.get(`/finance/payment-history/${ticketId}`)
  },
  getSalesReport(params = {}) {
    return client.get('/finance/sales-report', { params })
  },
  getTicketProfit(params = {}) {
    return client.get('/finance/ticket-profit', { params })
  },
  getAging(clientName, params = {}) {
    return client.get(`/finance/aging/${encodeURIComponent(clientName)}`, { params })
  },
  /** 更新财务支出 */
  updateExpense(expId, data) {
    return client.put(`/finance/expenses/${expId}`, data)
  },
  /** 删除财务支出 */
  deleteExpense(expId) {
    return client.delete(`/finance/expenses/${expId}`)
  },
}
