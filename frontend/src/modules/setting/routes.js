export default [
  {
    path: '/settings',
    name: 'SettingsPage',
    component: () => import('./views/Settings.vue'),
    meta: { title: '系统设置' }
  }
]
