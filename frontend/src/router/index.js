import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

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
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
      },
      {
        path: 'tickets',
        name: 'Tickets',
        component: () => import('@/views/Tickets.vue'),
      },
      {
        path: 'tickets/new',
        name: 'TicketCreate',
        component: () => import('@/views/TicketCreate.vue'),
      },
      {
        path: 'tickets/:id',
        name: 'TicketDetail',
        component: () => import('@/views/TicketDetail.vue'),
        props: true,
      },
      {
        path: 'clients',
        name: 'Clients',
        component: () => import('@/views/Clients.vue'),
      },
      {
        path: 'clients/:name',
        name: 'ClientDetail',
        component: () => import('@/views/ClientDetail.vue'),
        props: true,
      },
      {
        path: 'equipment',
        name: 'Equipment',
        component: () => import('@/views/Equipment.vue'),
      },
      {
        path: 'equipment/:id',
        name: 'EquipmentDetail',
        component: () => import('@/views/EquipmentDetail.vue'),
        props: true,
      },
      {
        path: 'finance',
        name: 'Finance',
        component: () => import('@/views/Finance.vue'),
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: () => import('@/views/Inventory.vue'),
      },
      {
        path: 'todos',
        name: 'Todos',
        component: () => import('@/views/Todos.vue'),
      },
      {
        path: 'warehouses',
        name: 'Warehouses',
        component: () => import('@/views/Warehouses.vue'),
      },
      {
        path: 'suppliers',
        name: 'Suppliers',
        component: () => import('@/views/Suppliers.vue'),
      },
      {
        path: 'service-fees',
        name: 'ServiceFees',
        component: () => import('@/views/ServiceFees.vue'),
      },
      {
        path: 'staff',
        name: 'Staff',
        component: () => import('@/views/Staff.vue'),
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/Notifications.vue'),
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
      },
      {
        path: 'stats',
        name: 'Stats',
        component: () => import('@/views/Stats.vue'),
      },
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
