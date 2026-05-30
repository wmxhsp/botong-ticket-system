<template>
  <aside class="bt-sidebar-rail">
    <div class="rail-brand">
      <i class="bi bi-cpu"></i>
    </div>

    <nav class="rail-nav">
      <div class="rail-section">
        <router-link
          v-for="item in primaryNav"
          :key="item.name"
          class="rail-item"
          :to="{ name: item.name }"
          :class="{ active: isActive(item) }"
          @click="onNavClick"
        >
          <span class="rail-indicator"></span>
          <i :class="['bi', item.icon]"></i>
          <span class="rail-tooltip">{{ item.label }}</span>
        </router-link>
      </div>

      <div class="rail-divider"></div>

      <div class="rail-section">
        <router-link
          v-for="item in secondaryNav"
          :key="item.name"
          class="rail-item"
          :to="{ name: item.name }"
          :class="{ active: isActive(item) }"
          @click="onNavClick"
        >
          <span class="rail-indicator"></span>
          <i :class="['bi', item.icon]"></i>
          <span class="rail-tooltip">{{ item.label }}</span>
        </router-link>
      </div>
    </nav>

    <div class="rail-bottom">
      <router-link
        v-for="item in bottomNav"
        :key="item.name"
        class="rail-item"
        :to="{ name: item.name }"
        :class="{ active: isActive(item) }"
        @click="onNavClick"
      >
        <span class="rail-indicator"></span>
        <i :class="['bi', item.icon]"></i>
        <span v-if="item.badge" class="rail-badge">{{ item.badge }}</span>
        <span class="rail-tooltip">{{ item.label }}</span>
      </router-link>
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
const mobileOpen = computed(() => app.sidebarMobileOpen)

const primaryNav = [
  { name: 'Dashboard', icon: 'bi-lightning-charge', label: '仪表盘' },
  { name: 'TicketList', icon: 'bi-clipboard-check', label: '工单' },
  { name: 'ClientList', icon: 'bi-people', label: '客户' },
  { name: 'Finance', icon: 'bi-cash-coin', label: '财务' },
  { name: 'Inventory', icon: 'bi-box-seam', label: '库存' },
]

const secondaryNav = [
  { name: 'EquipmentList', icon: 'bi-pc-display', label: '设备' },
  { name: 'Purchase', icon: 'bi-cart3', label: '采购' },
  { name: 'Staff', icon: 'bi-wrench-adjustable', label: '员工' },
  { name: 'Stats', icon: 'bi-bar-chart-line', label: '统计' },
]

const bottomNav = [
  { name: 'Todos', icon: 'bi-check2-square', label: '待办' },
  { name: 'Notifications', icon: 'bi-bell', label: '通知', badge: true },
  { name: 'Settings', icon: 'bi-gear', label: '设置' },
]

function isActive(item) {
  return route.name === item.name
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
.bt-sidebar-rail {
  width: 48px;
  min-height: 100vh;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  align-items: center;
  padding: 0;
}

.rail-brand {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  cursor: default;
}

.rail-brand i {
  font-size: 20px;
  color: #3b82f6;
}

.rail-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  overflow-y: auto;
  min-height: 0;
  width: 100%;
}

.rail-nav::-webkit-scrollbar {
  width: 0;
}

.rail-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.rail-divider {
  width: 24px;
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 6px 0;
  flex-shrink: 0;
}

.rail-item {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  margin: 2px 0;
  color: #64748b;
  text-decoration: none;
  transition: all 0.15s ease;
}

.rail-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
}

.rail-item.active {
  color: #60a5fa;
}

.rail-item.active .rail-indicator {
  position: absolute;
  left: -4px;
  top: 50%;
  transform: translateY(-50%);
  width: 2px;
  height: 16px;
  background: #3b82f6;
  border-radius: 0 2px 2px 0;
}

.rail-item i {
  font-size: 18px;
  flex-shrink: 0;
}

.rail-tooltip {
  position: absolute;
  left: 52px;
  top: 50%;
  transform: translateY(-50%);
  background: #fff;
  color: #1e293b;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
  z-index: 1000;
}

[data-theme="dark"] .rail-tooltip {
  background: #334155;
  color: #f1f5f9;
}

.rail-item:hover .rail-tooltip {
  opacity: 1;
}

.rail-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ef4444;
}

.rail-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  width: 100%;
}

.bt-sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

@media (max-width: 992px) {
  .bt-sidebar-rail {
    display: none;
  }
}
</style>
