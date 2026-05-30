import routes from './routes'
import * as api from './api'

export default {
  name: 'setting',
  routes,
  api,

  nav: {
    title: '系统设置',
    icon: 'bi-gear',
    path: '/settings',
    order: 999,
    group: '工作台',
    routeName: 'Settings',
    children: [],
  },

  features: [
    { name: 'pushplus.getConfig', endpoint: 'GET /pushplus/config', status: 'done' },
    { name: 'pushplus.updateConfig', endpoint: 'POST /pushplus/config', status: 'done' },
    { name: 'pushplus.sendTest', endpoint: 'POST /pushplus/test', status: 'done' },
    { name: 'wecom.getConfig', endpoint: 'GET /wecom/config', status: 'done' },
    { name: 'wecom.updateConfig', endpoint: 'POST /wecom/config', status: 'done' },
    { name: 'wecom.sendTest', endpoint: 'POST /wecom/test', status: 'done' },
  ]
}
