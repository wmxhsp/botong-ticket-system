import routes from './routes'
import * as api from './api'

export default {
  name: 'inventory',
  routes,
  api,

  nav: {
    title: '库存管理',
    icon: 'bi-box-seam',
    path: '/inventory',
    order: 50,
    group: '运营',
    routeName: 'Inventory',
    children: [],
  },

  features: [
    { name: 'list', endpoint: 'GET /inventory/', status: 'done' },
    { name: 'adjust', endpoint: 'POST /stock/adjust', status: 'done' },
    { name: 'transfer', endpoint: 'POST /stock/transfer', status: 'done' },
    { name: 'sale', endpoint: 'POST /stock/sale', status: 'done' },
    { name: 'count', endpoint: 'POST /stock/count', status: 'done' },
    { name: 'getLogs', endpoint: 'GET /stock/logs', status: 'done' },
    { name: 'getAlerts', endpoint: 'GET /stock/alerts', status: 'done' },
    { name: 'alertPurchase', endpoint: 'POST /stock/alerts/:goodsId/purchase', status: 'done' },
    { name: 'getSales', endpoint: 'GET /stock/sale', status: 'done' },
    { name: 'renewSale', endpoint: 'POST /stock/sale/:saleId/renew', status: 'done' },
  ]
}
