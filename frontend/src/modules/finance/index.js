import routes from './routes'
import * as api from './api'

export default {
  name: 'finance',
  routes,
  api,

  nav: {
    title: '财务管理',
    icon: 'bi-cash-coin',
    path: '/finance',
    order: 40,
    group: '财务',
    routeName: 'Finance',
    children: [],
  },

  features: [
    { name: 'getSummary', endpoint: 'GET /finance/summary', status: 'done' },
    { name: 'getExpenses', endpoint: 'GET /finance/expenses', status: 'done' },
    { name: 'getIncome', endpoint: 'GET /finance/', status: 'done' },
    { name: 'recordIncome', endpoint: 'POST /finance/income', status: 'done' },
    { name: 'recordExpense', endpoint: 'POST /expenses/', status: 'done' },
    { name: 'getPendingPayments', endpoint: 'GET /finance/unpaid', status: 'done' },
    { name: 'getDashboard', endpoint: 'GET /finance/dashboard', status: 'done' },
    { name: 'pay', endpoint: 'POST /finance/pay', status: 'done' },
    { name: 'batchPay', endpoint: 'POST /finance/batch-pay', status: 'done' },
    { name: 'quickIncome', endpoint: 'POST /finance/quick-income', status: 'done' },
    { name: 'getReceivables', endpoint: 'GET /finance/receivables', status: 'done' },
    { name: 'getOverdueReceivables', endpoint: 'GET /finance/receivables/overdue', status: 'done' },
    { name: 'getClientStatement', endpoint: 'GET /finance/statement/client/:name', status: 'done' },
    { name: 'getSupplierStatement', endpoint: 'GET /finance/statement/supplier/:id', status: 'done' },
    { name: 'partialPay', endpoint: 'POST /finance/partial-pay', status: 'done' },
    { name: 'getPaymentHistory', endpoint: 'GET /finance/payment-history/:ticketId', status: 'done' },
    { name: 'getSalesReport', endpoint: 'GET /finance/sales-report', status: 'done' },
    { name: 'getTicketProfit', endpoint: 'GET /finance/ticket-profit', status: 'done' },
    { name: 'getAging', endpoint: 'GET /finance/aging/:name', status: 'done' },
    { name: 'updateExpense', endpoint: 'PUT /finance/expenses/:id', status: 'done' },
    { name: 'deleteExpense', endpoint: 'DELETE /finance/expenses/:id', status: 'done' },
  ]
}
