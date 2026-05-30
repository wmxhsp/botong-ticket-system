import routes from './routes'
import * as api from './api'

export default {
  name: 'dashboard',

  nav: {
    title: '仪表盘',
    icon: 'bi-speedometer2',
    path: '/',
    order: 0,
    group: '工作台',
    routeName: 'Dashboard',
    children: [],
  },

  routes,
  api,

  features: [
    {
      id: 'dashboard.summary',
      name: '仪表盘汇总',
      endpoint: 'GET /api/v1/dashboard/summary',
      view: 'Dashboard.vue',
      status: 'done',
      description: '展示工单、设备、财务等核心指标',
    },
    {
      id: 'dashboard.stockAlerts',
      name: '库存预警',
      endpoint: 'GET /api/v1/stock/alerts',
      view: 'Dashboard.vue',
      status: 'done',
      description: '展示库存不足商品',
    },
  ],
}
