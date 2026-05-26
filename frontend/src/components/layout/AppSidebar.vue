<template>
  <aside class="bt-sidebar" :class="{ collapsed: collapsed, open: mobileOpen }">
    <div class="brand" @click="toggleCollapse">
      <i class="bi bi-cpu"></i>
      <span class="brand-name">博通</span>
    </div>

    <nav class="nav flex-column">
      <template v-for="group in navGroups" :key="group.title">
        <div class="nav-group-title">{{ group.title }}</div>
        <router-link
          v-for="item in group.items"
          :key="item.name"
          class="nav-link"
          :to="{name: item.name}"
          :class="{ active: isActive(item) }"
          :title="item.label"
          @click="onNavClick"
        >
          <i :class="['bi', item.icon]"></i>
          <span>{{ item.label }}</span>
        </router-link>
      </template>
    </nav>

    <div class="sidebar-footer">
      <div class="user-info">
        <div class="avatar"><i class="bi bi-user"></i></div>
        <span class="username">管理员</span>
      </div>
    </div>
  </aside>

  <div v-if="mobileOpen" class="bt-sidebar-overlay" @click="closeMobile"></div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const app = useAppStore()

const collapsed = computed(() => app.sidebarCollapsed)
const mobileOpen = computed(() => app.sidebarMobileOpen)

const navGroups = [
  {
    title: '工作台',
    items: [
      { name: 'Dashboard', label: '仪表盘', icon: 'speedometer2' },
      { name: 'Notifications', label: '通知中心', icon: 'bell' },
      { name: 'Todos', label: '待办事项', icon: 'check2-square' },
    ],
  },
  {
    title: '核心业务',
    items: [
      { name: 'Tickets', label: '工单管理', icon: 'ticket-perforated', children: ['TicketDetail', 'TicketCreate'] },
      { name: 'Clients', label: '客户管理', icon: 'people', children: ['ClientDetail'] },
      { name: 'Equipment', label: '设备管理', icon: 'pc-display', children: ['EquipmentDetail'] },
    ],
  },
  {
    title: '销售管理',
    items: [
      { name: 'Inventory', label: '库存管理', icon: 'box-seam' },
      { name: 'Warehouses', label: '仓库管理', icon: 'shop' },
      { name: 'Suppliers', label: '供应商管理', icon: 'truck' },
    ],
  },
  {
    title: '服务规则',
    items: [
      { name: 'ServiceFees', label: '服务规则', icon: 'currency-yen' },
      { name: 'Staff', label: '工程师管理', icon: 'people-fill' },
    ],
  },
  {
    title: '财务',
    items: [
      { name: 'Finance', label: '财务管理', icon: 'cash-coin' },
      { name: 'Stats', label: '统计分析', icon: 'graph-up' },
    ],
  },
  {
    title: '系统',
    items: [
      { name: 'Settings', label: '系统设置', icon: 'sliders' },
    ],
  },
]

function isActive(item) {
  if (route.name === item.name) return true
  if (item.children && item.children.includes(route.name)) return true
  return false
}

function toggleCollapse() {
  app.sidebarCollapsed = !app.sidebarCollapsed
}

function onNavClick() {
  if (window.innerWidth < 993) {
    app.sidebarMobileOpen = false
  }
}

function closeMobile() {
  app.sidebarMobileOpen = false
}
</script>

<style scoped>
.bt-sidebar {
  width: 200px;
  min-height: 100vh;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  transition: width 0.3s ease;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
}

.bt-sidebar.collapsed {
  width: 56px;
}

.bt-sidebar .brand {
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.bt-sidebar .brand:hover {
  background: rgba(255, 255, 255, 0.05);
}

.bt-sidebar .brand i {
  font-size: 24px;
  color: #3b82f6;
  flex-shrink: 0;
}

.bt-sidebar .brand-name {
  font-size: 18px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.bt-sidebar nav {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

.bt-sidebar nav::-webkit-scrollbar {
  width: 4px;
}

.bt-sidebar nav::-webkit-scrollbar-track {
  background: transparent;
}

.bt-sidebar nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

.bt-sidebar .nav-group-title {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: #64748b;
  padding: 12px 16px 4px;
  font-weight: 700;
  transition: opacity 0.3s ease;
}

.bt-sidebar .nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  color: #94a3b8;
  text-decoration: none;
  transition: all 0.2s ease;
  border-radius: 0 8px 8px 0;
  margin: 2px 0;
  position: relative;
}

.bt-sidebar .nav-link:hover {
  background: rgba(59, 130, 246, 0.1);
  color: #e2e8f0;
  padding-left: 20px;
}

.bt-sidebar .nav-link.active {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.25) 0%, transparent 100%);
  color: #3b82f6;
  border-left: 3px solid #3b82f6;
}

.bt-sidebar .nav-link i {
  width: 18px;
  font-size: 16px;
  text-align: center;
  flex-shrink: 0;
}

.bt-sidebar .sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.bt-sidebar .user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bt-sidebar .avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.bt-sidebar .avatar i {
  font-size: 14px;
}

.bt-sidebar .username {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

.bt-sidebar.collapsed .brand-name,
.bt-sidebar.collapsed .nav-group-title,
.bt-sidebar.collapsed .nav-link span,
.bt-sidebar.collapsed .username {
  display: none;
}

.bt-sidebar.collapsed .brand {
  justify-content: center;
}

.bt-sidebar.collapsed .nav-link {
  justify-content: center;
  border-radius: 8px;
  margin: 2px 8px;
  padding: 10px;
}

.bt-sidebar.collapsed .nav-link.active {
  border-left: none;
  background: rgba(59, 130, 246, 0.2);
}

.bt-sidebar.collapsed .sidebar-footer {
  padding: 12px 8px;
  text-align: center;
}

.bt-sidebar.collapsed .user-info {
  justify-content: center;
}

.bt-sidebar.collapsed .nav-link:hover::after {
  content: attr(title);
  position: absolute;
  left: 60px;
  background: #1e293b;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: white;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 1000;
}

.bt-sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

@media (max-width: 992px) {
  .bt-sidebar {
    width: 260px;
    transform: translateX(-100%);
    z-index: 1000;
  }

  .bt-sidebar.open {
    transform: translateX(0);
  }

  .bt-sidebar.collapsed {
    width: 260px;
    transform: translateX(-100%);
  }

  .bt-sidebar.collapsed.open {
    transform: translateX(0);
  }
}
</style>
