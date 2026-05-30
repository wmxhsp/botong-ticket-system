import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { moduleRoutes } from '@/modules'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // 动态注入模块路由
      ...moduleRoutes,
      // 功能地图（全局页面，不属于单一模块）
      {
        path: '/feature-map',
        name: 'FeatureMap',
        component: () => import('@/views/FeatureMap.vue'),
        meta: { title: '功能地图' },
      },
      // 404 兜底
      {
        path: ':pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/NotFound.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory('/app/'),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  if (requiresAuth) {
    await auth.checkAuth()
    if (!auth.isAuthenticated) {
      next({ name: 'Login', query: { next: to.fullPath } })
      return
    }
  }

  if (to.name === 'Login' && auth.isAuthenticated) {
    next({ name: 'Dashboard' })
    return
  }

  next()
})

export default router
