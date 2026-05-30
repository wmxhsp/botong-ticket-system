export default [
  {
    path: '/tickets',
    name: 'TicketList',
    component: () => import('./views/Tickets.vue'),
    meta: { title: '工单列表' }
  },
  {
    path: '/tickets/new',
    name: 'TicketCreate',
    component: () => import('./views/TicketCreate.vue'),
    meta: { title: '新建工单' }
  },
  {
    path: '/tickets/quick',
    name: 'QuickTicket',
    component: () => import('./views/QuickTicket.vue'),
    meta: { title: '快速创建工单' }
  },
  {
    path: '/tickets/:id',
    name: 'TicketDetail',
    component: () => import('./views/TicketDetail.vue'),
    meta: { title: '工单详情' }
  },
  {
    path: '/tickets/:id/settle',
    name: 'QuickSettle',
    component: () => import('./views/QuickSettle.vue'),
    meta: { title: '一键结算' }
  }
]
