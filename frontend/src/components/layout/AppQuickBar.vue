<template>
  <div class="bt-quick-bar d-flex align-items-center gap-1 flex-grow-1 overflow-hidden">
    <div class="bt-recent-pages d-flex align-items-center gap-1 overflow-hidden flex-nowrap" v-if="recentPages.length">
      <router-link v-for="page in displayPages" :key="page.path + page.timestamp"
                   :to="page.path" class="bt-recent-tag" :title="page.label">
        <span class="bt-recent-tag-text">{{ page.label }}</span>
        <span class="bt-recent-tag-close" @click.prevent.stop="removePage(page.path)">&times;</span>
      </router-link>
    </div>

    <div class="bt-quick-divider" v-if="recentPages.length"></div>

    <button class="bt-quick-action" @click="$router.push({ name: 'QuickTicket' })" title="新建工单">
      <i class="bi bi-plus-lg"></i>
    </button>

    <div class="bt-quick-divider"></div>

    <div class="bt-smart-recs d-flex align-items-center gap-1 flex-nowrap">
      <router-link v-for="rec in smartRecs" :key="rec.path" :to="rec.path" class="bt-smart-tag" :title="rec.label">
        {{ rec.label }}
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const STORAGE_KEY = 'bt_recent_pages'
const MAX_STORE = 10
const MAX_DISPLAY = 5

const router = useRouter()
const route = useRoute()
const recentPages = ref([])

const routeLabelMap = {
  Dashboard: '首页',
  TicketList: '工单',
  TicketCreate: '新建工单',
  QuickTicket: '快速创建',
  ClientList: '客户',
  ClientDetail: null,
  TodoList: '待办',
  FinanceOverview: '财务',
  InventoryList: '库存',
  StatsOverview: '统计',
  EquipmentList: '设备',
}

function loadPages() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) recentPages.value = JSON.parse(raw)
  } catch {
    recentPages.value = []
  }
}

function savePages() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(recentPages.value))
}

function addPage(r) {
  if (!r.name || r.name === 'Dashboard' || r.name === 'Login' || r.name === 'NotFound') return
  const label = buildLabel(r)
  if (!label) return
  const entry = { name: r.name, label, path: r.fullPath, timestamp: Date.now() }
  const filtered = recentPages.value.filter(p => p.path !== entry.path)
  filtered.unshift(entry)
  recentPages.value = filtered.slice(0, MAX_STORE)
  savePages()
}

function removePage(path) {
  recentPages.value = recentPages.value.filter(p => p.path !== path)
  savePages()
}

function buildLabel(r) {
  if (r.name === 'TicketDetail' && r.params.id) return `工单#${r.params.id}`
  if (r.name === 'QuickSettle' && r.params.id) return `结算#${r.params.id}`
  if (r.name === 'ClientDetail' && r.params.name) return `客户:${r.params.name}`
  return routeLabelMap[r.name] || r.meta?.title || null
}

const displayPages = computed(() => recentPages.value.slice(0, MAX_DISPLAY))

const smartRecs = computed(() => {
  const h = new Date().getHours()
  if (h >= 6 && h < 12) {
    return [
      { label: '📋 今日待办', path: '/todos' },
      { label: '🔧 预约工单', path: '/tickets?status=scheduled' },
    ]
  } else if (h >= 12 && h < 18) {
    return [
      { label: '💰 待结算', path: '/tickets?status=completed' },
      { label: '📦 库存预警', path: '/inventory' },
    ]
  } else {
    return [
      { label: '📊 今日统计', path: '/stats' },
      { label: '✅ 完工确认', path: '/tickets?status=completed' },
    ]
  }
})

let unwatch = null

onMounted(() => {
  loadPages()
  addPage(route)
  unwatch = watch(() => route.fullPath, () => {
    addPage(route)
  })
})

onUnmounted(() => {
  if (unwatch) unwatch()
})
</script>

<style scoped>
.bt-quick-bar {
  min-width: 0;
  padding: 0 4px;
}

.bt-recent-pages {
  min-width: 0;
}

.bt-recent-tag {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--bt-gray-100, #f1f5f9);
  color: var(--bt-gray-700, #374151);
  font-size: 11px;
  line-height: 1.4;
  text-decoration: none;
  white-space: nowrap;
  max-width: 120px;
  transition: background 0.15s ease;
  flex-shrink: 0;
}

[data-theme="dark"] .bt-recent-tag {
  background: var(--bt-gray-700, #374151);
  color: var(--bt-gray-300, #d1d5db);
}

.bt-recent-tag:hover {
  background: var(--bt-gray-200, #e2e8f0);
}

[data-theme="dark"] .bt-recent-tag:hover {
  background: var(--bt-gray-600, #4b5563);
}

.bt-recent-tag-text {
  overflow: hidden;
  text-overflow: ellipsis;
}

.bt-recent-tag-close {
  display: none;
  font-size: 13px;
  line-height: 1;
  cursor: pointer;
  margin-left: 1px;
  opacity: 0.6;
  flex-shrink: 0;
}

.bt-recent-tag:hover .bt-recent-tag-close {
  display: inline;
}

.bt-recent-tag-close:hover {
  opacity: 1;
}

.bt-quick-divider {
  width: 1px;
  height: 16px;
  background: var(--bt-gray-200, #e2e8f0);
  flex-shrink: 0;
}

[data-theme="dark"] .bt-quick-divider {
  background: var(--bt-gray-600, #4b5563);
}

.bt-quick-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: 1px solid var(--bt-gray-200, #e2e8f0);
  background: transparent;
  color: var(--bt-gray-600, #4b5563);
  font-size: 12px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s ease;
  padding: 0;
}

[data-theme="dark"] .bt-quick-action {
  border-color: var(--bt-gray-600, #4b5563);
  color: var(--bt-gray-300, #d1d5db);
}

.bt-quick-action:hover {
  background: #6366f1;
  border-color: #6366f1;
  color: #fff;
}

.bt-smart-recs {
  min-width: 0;
}

.bt-smart-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eff6ff;
  color: #3b82f6;
  font-size: 11px;
  line-height: 1.4;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.15s ease;
  flex-shrink: 0;
}

[data-theme="dark"] .bt-smart-tag {
  background: #1e3a5f;
  color: #60a5fa;
}

.bt-smart-tag:hover {
  background: #dbeafe;
}

[data-theme="dark"] .bt-smart-tag:hover {
  background: #1e4a7f;
}

@media (max-width: 768px) {
  .bt-smart-recs {
    display: none;
  }
  .bt-recent-tag {
    max-width: 80px;
  }
}

@media (max-width: 576px) {
  .bt-recent-pages {
    display: none;
  }
  .bt-quick-divider:first-of-type {
    display: none;
  }
}
</style>
