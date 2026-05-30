export default [
  {
    path: '/notifications',
    name: 'NotificationList',
    component: () => import('./views/Notifications.vue'),
    meta: { title: '通知中心' }
  }
]
