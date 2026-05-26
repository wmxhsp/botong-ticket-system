import client from './client'

export const financeApi = {
  getSummary(params = {}) {
    return client.get('/finance/summary', { params }).then(r => r.data)
  },
  getExpenses(params = {}) {
    return client.get('/finance/expenses', { params }).then(r => r.data)
  },
  getIncome(params = {}) {
    return client.get('/finance/', { params }).then(r => r.data)
  },
  recordIncome(data) {
    return client.post('/finance/income', data)
  },
  recordExpense(data) {
    return client.post('/expenses/', data)
  },
  getPendingPayments(params = {}) {
    return client.get('/finance/unpaid', { params }).then(r => r.data)
  },
  getDashboard(params = {}) {
    return client.get('/finance/dashboard', { params }).then(r => r.data)
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
    return client.get('/finance/receivables', { params }).then(r => r.data)
  },
  getOverdueReceivables(params = {}) {
    return client.get('/finance/receivables/overdue', { params }).then(r => r.data)
  },
  getClientStatement(clientName, params = {}) {
    return client.get(`/finance/statement/client/${encodeURIComponent(clientName)}`, { params }).then(r => r.data)
  },
  getSupplierStatement(supplierId, params = {}) {
    return client.get(`/finance/statement/supplier/${supplierId}`, { params }).then(r => r.data)
  },
  partialPay(data) {
    return client.post('/finance/partial-pay', data)
  },
  getPaymentHistory(ticketId) {
    return client.get(`/finance/payment-history/${ticketId}`).then(r => r.data)
  },
  getSalesReport(params = {}) {
    return client.get('/finance/sales-report', { params }).then(r => r.data)
  },
  getTicketProfit(params = {}) {
    return client.get('/finance/ticket-profit', { params }).then(r => r.data)
  },
  getAging(clientName, params = {}) {
    return client.get(`/finance/aging/${encodeURIComponent(clientName)}`, { params }).then(r => r.data)
  },
}
