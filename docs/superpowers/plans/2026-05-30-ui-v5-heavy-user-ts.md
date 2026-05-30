# UI v5 重度使用者视角 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构博通工单系统前端，从重度使用者视角（每天50+次操作，每次<3秒）提升效率，同时采用核心TS+业务JS的渐进迁移策略。

**Architecture:** 基于现有 Vue 3 + Vite + Pinia + Bootstrap 5 架构，新增 core/ 目录存放TS化的基础设施（API、类型、状态、组合式函数），保持 modules/ 业务层为JS+JSDoc，新增 mobile/ 目录存放移动端专用页面。不替换Bootstrap为Tailwind（成本过高），而是在现有基础上优化。

**Tech Stack:** Vue 3, Vite 5, TypeScript（核心层）, JavaScript+JSDoc（业务层）, Pinia, Bootstrap 5, Axios, Chart.js

---

## 文件结构总览

### 新增/重构文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `frontend/src/core/api/client.ts` | 重构 | API客户端，统一响应格式，增强类型 |
| `frontend/src/core/api/tickets.ts` | 重构 | 工单API，完整类型覆盖 |
| `frontend/src/core/api/clients.ts` | 重构 | 客户API，完整类型覆盖 |
| `frontend/src/core/api/dashboard.ts` | 重构 | 仪表盘API，完整类型覆盖 |
| `frontend/src/core/types/index.ts` | 重构 | 统一类型定义，消除字段冗余 |
| `frontend/src/core/stores/app.ts` | 迁移 | 应用状态（已有TS版本） |
| `frontend/src/core/stores/auth.ts` | 迁移 | 认证状态（已有TS版本） |
| `frontend/src/core/stores/sync.ts` | 新增 | 离线同步状态 |
| `frontend/src/core/composables/useCommandPalette.ts` | 新增 | 命令面板逻辑 |
| `frontend/src/core/composables/useKeyboardShortcuts.ts` | 新增 | 快捷键管理 |
| `frontend/src/core/composables/useOfflineSync.ts` | 新增 | 离线同步逻辑 |
| `frontend/src/core/utils/constants.ts` | 迁移 | 常量定义（已有TS版本） |
| `frontend/src/core/utils/format.ts` | 迁移 | 格式化工具（已有TS版本） |
| `frontend/src/components/common/CommandPalette.vue` | 新增 | 命令面板组件 |
| `frontend/src/components/common/ActivityStream.vue` | 新增 | 实时活动流 |
| `frontend/src/components/common/QuickStats.vue` | 新增 | 快捷统计卡片 |
| `frontend/src/modules/dashboard/views/Dashboard.vue` | 重构 | 今日视图 |
| `frontend/src/modules/ticket/views/Tickets.vue` | 重构 | 双栏工单列表 |
| `frontend/src/modules/ticket/views/QuickTicket.vue` | 新增 | 移动端快速创建 |
| `frontend/src/modules/ticket/views/QuickSettle.vue` | 新增 | 移动端一键结算 |
| `frontend/src/modules/ticket/routes.js` | 修改 | 添加新路由 |
| `frontend/src/App.vue` | 修改 | 集成命令面板 |
| `frontend/src/main.js` | 修改 | 入口调整 |
| `frontend/tsconfig.json` | 修改 | 允许JS文件 |
| `frontend/vite.config.js` | 修改 | 路径别名优化 |

---

## Task 1: 类型系统统一（TS核心层基础）

**Files:**
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/core/types/index.ts`

- [ ] **Step 1: 统一ApiResponse类型**

当前 `types/index.ts` 中 `ApiResponse` 的字段都是 optional 的，导致使用时需要大量 `?.` 操作。统一为必填字段，并增加泛型支持。

```typescript
// core/types/index.ts
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
```

- [ ] **Step 2: 统一Ticket类型**

消除字段冗余（如 `client`/`client_name`, `description`/`content`, `total`/`amount`），使用确定性的字段名。

```typescript
export interface Ticket {
  id: number
  ticket_no: string
  client_id: number
  client_name: string
  contact: string
  phone: string
  address: string
  content: string
  status: TicketStatus
  priority: Priority
  billing_type: BillingType
  appointment_at?: string
  closed_at?: string
  created_at: string
  updated_at: string
  labor_fee: number
  material_fee: number
  total_amount: number
  paid_amount: number
  technician_id?: number
  technician_name?: string
  photos: TicketPhoto[]
  materials: TicketMaterial[]
  service_items: TicketServiceItem[]
}
```

- [ ] **Step 3: 统一其他核心类型**

Client, Technician, DashboardStats, ActivityItem 等类型统一整理到 `core/types/index.ts`。

- [ ] **Step 4: 导出聚合**

```typescript
// core/types/index.ts
export * from './index'  // 所有类型
export type { TicketStatus, Priority, BillingType, PaymentMethod }
```

---

## Task 2: API层TS化（统一响应格式）

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/tickets.ts`
- Modify: `frontend/src/api/clients.ts`
- Modify: `frontend/src/api/dashboard.ts`

- [ ] **Step 1: 重构API客户端**

当前 `client.ts` 返回的是 `AxiosResponse.data`，类型为 `any`。需要包装为统一的 `ApiResponse<T>` 类型。

```typescript
// api/client.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import type { ApiResponse } from '@/core/types'

class ApiClient {
  private client: AxiosInstance
  
  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
      timeout: 15000,
    })
    
    // Request interceptor
    this.client.interceptors.request.use((config) => {
      const csrfToken = localStorage.getItem('bt_csrf_token')
      if (csrfToken && config.method !== 'get') {
        config.headers['X-CSRF-Token'] = csrfToken
      }
      return config
    })
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        if (response.config?.responseType === 'blob') {
          return response
        }
        return response.data
      },
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('bt_csrf_token')
          const path = window.location.pathname
          if (!path.includes('/login')) {
            window.location.href = '/login'
          }
        }
        const msg = error.response?.data?.error || error.message || '请求失败'
        window.dispatchEvent(new CustomEvent('api-error', { detail: { message: msg } }))
        return Promise.reject(error)
      }
    )
  }
  
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.client.get(url, config)
  }
  
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.client.post(url, data, config)
  }
  
  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.client.put(url, data, config)
  }
  
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.client.delete(url, config)
  }
}

export const apiClient = new ApiClient()
```

- [ ] **Step 2: 重构tickets API**

```typescript
// api/tickets.ts
import { apiClient } from './client'
import type { ApiResponse, PaginatedResponse, Ticket, TicketStatus, BillingType } from '@/core/types'

export interface TicketListParams {
  page?: number
  page_size?: number
  status?: TicketStatus
  client_id?: number
  search?: string
  start_date?: string
  end_date?: string
}

export interface CreateTicketData {
  client_id: number
  content: string
  status?: TicketStatus
  priority?: string
  billing_type?: BillingType
  appointment_at?: string
  technician_id?: number
}

export const ticketApi = {
  async list(params?: TicketListParams): Promise<PaginatedResponse<Ticket>> {
    const response = await apiClient.get<Ticket[]>('/tickets', { params })
    return {
      items: response.data || [],
      total: response.total || 0,
      page: response.page || 1,
      page_size: response.page_size || 20,
    }
  },
  
  async getById(id: number): Promise<ApiResponse<Ticket>> {
    return apiClient.get<Ticket>(`/tickets/${id}`)
  },
  
  async create(data: CreateTicketData): Promise<ApiResponse<Ticket>> {
    return apiClient.post<Ticket>('/tickets', data)
  },
  
  // ... 其他方法
}
```

- [ ] **Step 3: 重构clients API**

```typescript
// api/clients.ts
import { apiClient } from './client'
import type { ApiResponse, PaginatedResponse, Client } from '@/core/types'

export interface ClientListParams {
  page?: number
  page_size?: number
  search?: string
}

export interface CreateClientData {
  name: string
  phone?: string
  address?: string
  hourly_rate?: number
}

export const clientApi = {
  async list(params?: ClientListParams): Promise<PaginatedResponse<Client>> {
    const response = await apiClient.get<Client[]>('/clients', { params })
    return {
      items: response.data || [],
      total: response.total || 0,
      page: response.page || 1,
      page_size: response.page_size || 20,
    }
  },
  
  async search(query: string): Promise<ApiResponse<Client[]>> {
    return apiClient.get<Client[]>('/clients/search', { params: { q: query } })
  },
  
  async create(data: CreateClientData): Promise<ApiResponse<Client>> {
    return apiClient.post<Client>('/clients', data)
  },
  
  // ... 其他方法
}
```

- [ ] **Step 4: 重构dashboard API**

```typescript
// api/dashboard.ts
import { apiClient } from './client'
import type { ApiResponse, DashboardStats } from '@/core/types'

export const dashboardApi = {
  async getTodayStats(): Promise<ApiResponse<DashboardStats>> {
    return apiClient.get<DashboardStats>('/dashboard/today')
  },
  
  async getSummary(): Promise<ApiResponse<DashboardStats>> {
    return apiClient.get<DashboardStats>('/dashboard/summary')
  }
}
```

---

## Task 3: 命令面板组件（Cmd+K）

**Files:**
- Create: `frontend/src/core/composables/useCommandPalette.ts`
- Create: `frontend/src/components/common/CommandPalette.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 创建命令面板组合式函数**

```typescript
// core/composables/useCommandPalette.ts
import { ref, computed } from 'vue'
import type { CommandItem } from '@/core/types'

const visible = ref(false)
const query = ref('')
const selectedIndex = ref(0)

export function useCommandPalette() {
  const open = () => {
    visible.value = true
    query.value = ''
    selectedIndex.value = 0
  }
  
  const close = () => {
    visible.value = false
    query.value = ''
  }
  
  const toggle = () => {
    visible.value ? close() : open()
  }
  
  return {
    visible: computed(() => visible.value),
    query: computed(() => query.value),
    selectedIndex: computed(() => selectedIndex.value),
    open,
    close,
    toggle,
  }
}
```

- [ ] **Step 2: 创建命令面板组件**

```vue
<!-- components/common/CommandPalette.vue -->
<template>
  <Teleport to="body">
    <Transition name="palette">
      <div v-if="visible" class="command-palette" @keydown.esc="close">
        <div class="palette-overlay" @click="close"></div>
        <div class="palette-container">
          <div class="palette-input">
            <i class="bi bi-search"></i>
            <input
              ref="inputRef"
              v-model="query"
              placeholder="搜索工单、客户、命令... (Esc关闭)"
              @keydown.enter="execute"
              @keydown.up.prevent="selectPrev"
              @keydown.down.prevent="selectNext"
            />
            <kbd>ESC</kbd>
          </div>
          
          <div class="palette-results">
            <!-- 搜索结果 -->
            <div v-if="query" class="results-content">
              <div v-if="searchResults.tickets.length" class="result-group">
                <div class="group-title">工单</div>
                <div
                  v-for="(ticket, i) in searchResults.tickets"
                  :key="ticket.id"
                  class="result-item"
                  :class="{ active: selectedIndex === i }"
                  @click="openTicket(ticket)"
                >
                  <span class="ticket-id">#{{ ticket.id }}</span>
                  <span class="name">{{ ticket.client_name }}</span>
                  <StatusBadge :status="ticket.status" />
                </div>
              </div>
              
              <div v-if="searchResults.clients.length" class="result-group">
                <div class="group-title">客户</div>
                <div
                  v-for="(client, i) in searchResults.clients"
                  :key="client.id"
                  class="result-item"
                  :class="{ active: selectedIndex === searchResults.tickets.length + i }"
                  @click="openClient(client)"
                >
                  <i class="bi bi-person"></i>
                  <span class="name">{{ client.name }}</span>
                  <span class="phone">{{ client.phone }}</span>
                </div>
              </div>
              
              <div v-if="filteredCommands.length" class="result-group">
                <div class="group-title">命令</div>
                <div
                  v-for="(cmd, i) in filteredCommands"
                  :key="cmd.id"
                  class="result-item"
                  :class="{ active: selectedIndex === searchResults.tickets.length + searchResults.clients.length + i }"
                  @click="executeCommand(cmd)"
                >
                  <i :class="cmd.icon"></i>
                  <span class="name">{{ cmd.name }}</span>
                  <span class="shortcut">{{ cmd.shortcut }}</span>
                </div>
              </div>
            </div>
            
            <!-- 默认显示最近使用 -->
            <div v-else class="results-content">
              <div class="result-group">
                <div class="group-title">快捷命令</div>
                <div
                  v-for="(cmd, i) in commands"
                  :key="cmd.id"
                  class="result-item"
                  :class="{ active: selectedIndex === i }"
                  @click="executeCommand(cmd)"
                >
                  <i :class="cmd.icon"></i>
                  <span class="name">{{ cmd.name }}</span>
                  <span class="shortcut">{{ cmd.shortcut }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="palette-footer">
            <span><kbd>↑↓</kbd> 导航</span>
            <span><kbd>Enter</kbd> 选择</span>
            <span><kbd>Esc</kbd> 关闭</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import type { CommandItem, Ticket, Client } from '@/core/types'
import { ticketApi } from '@/core/api/tickets'
import { clientApi } from '@/core/api/clients'
import StatusBadge from './StatusBadge.vue'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits(['close'])

const router = useRouter()
const query = ref('')
const selectedIndex = ref(0)
const inputRef = ref<HTMLInputElement>()
const searchResults = ref<{ tickets: Ticket[]; clients: Client[] }>({ tickets: [], clients: [] })

const commands: CommandItem[] = [
  { id: 'new-ticket', name: '新建工单', shortcut: 'Ctrl+N', icon: 'bi bi-plus', action: () => router.push('/tickets/new') },
  { id: 'today-view', name: '今日视图', shortcut: 'Ctrl+T', icon: 'bi bi-calendar-day', action: () => router.push('/') },
  { id: 'quick-settle', name: '快速结算', shortcut: 'Ctrl+S', icon: 'bi bi-check-circle', action: () => router.push('/tickets?filter=pending-payment') },
  { id: 'search-client', name: '搜索客户', shortcut: 'Ctrl+C', icon: 'bi bi-people', action: () => { query.value = '客户 ' } },
]

const filteredCommands = computed(() => {
  if (!query.value) return commands
  const q = query.value.toLowerCase()
  return commands.filter(c => c.name.toLowerCase().includes(q))
})

const totalItems = computed(() => 
  searchResults.value.tickets.length + searchResults.value.clients.length + filteredCommands.value.length
)

watch(() => props.visible, (v) => {
  if (v) nextTick(() => inputRef.value?.focus())
})

watch(query, async (val) => {
  selectedIndex.value = 0
  if (!val || val.length < 1) {
    searchResults.value = { tickets: [], clients: [] }
    return
  }
  try {
    const [ticketsRes, clientsRes] = await Promise.all([
      ticketApi.list({ search: val, page_size: 5 }),
      clientApi.search(val),
    ])
    searchResults.value = {
      tickets: ticketsRes.items || [],
      clients: clientsRes.data || [],
    }
  } catch {
    searchResults.value = { tickets: [], clients: [] }
  }
})

function selectPrev() {
  selectedIndex.value = Math.max(0, selectedIndex.value - 1)
}

function selectNext() {
  selectedIndex.value = Math.min(totalItems.value - 1, selectedIndex.value + 1)
}

function execute() {
  // 根据selectedIndex判断执行哪个操作
}

function executeCommand(cmd: CommandItem) {
  cmd.action()
  close()
}

function openTicket(ticket: Ticket) {
  router.push(`/tickets/${ticket.id}`)
  close()
}

function openClient(client: Client) {
  router.push(`/clients/${client.id}`)
  close()
}

function close() {
  emit('close')
}
</script>

<style scoped>
.command-palette {
  position: fixed; inset: 0; z-index: 10000;
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: min(20vh, 120px);
}
.palette-overlay {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.5); backdrop-filter: blur(4px);
}
.palette-container {
  position: relative; width: 100%; max-width: 600px; margin: 0 16px;
  background: var(--card-bg); border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  overflow: hidden; display: flex; flex-direction: column;
}
.palette-input {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-bottom: 1px solid var(--card-border);
}
.palette-input input {
  flex: 1; border: none; outline: none; font-size: 16px;
  background: transparent; color: var(--bt-text-body);
}
.palette-input kbd {
  font-size: 11px; padding: 2px 6px; border-radius: 4px;
  background: var(--bt-gray-100); color: var(--bt-gray-500);
  border: 1px solid var(--bt-gray-200);
}
.palette-results {
  max-height: 400px; overflow-y: auto;
}
.result-group {
  padding: 4px 0;
}
.group-title {
  padding: 8px 16px 4px; font-size: 12px; font-weight: 600;
  color: var(--bt-gray-500); text-transform: uppercase; letter-spacing: 0.5px;
}
.result-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; cursor: pointer; transition: background 0.1s;
}
.result-item:hover, .result-item.active {
  background: var(--bt-gray-50);
}
.result-item .name {
  flex: 1; font-size: 14px; font-weight: 500;
}
.result-item .shortcut {
  font-size: 12px; color: var(--bt-gray-400);
  padding: 2px 6px; background: var(--bt-gray-100); border-radius: 4px;
}
.palette-footer {
  display: flex; gap: 16px; padding: 8px 16px;
  border-top: 1px solid var(--card-border);
  font-size: 11px; color: var(--bt-gray-400);
}
.palette-footer kbd {
  font-size: 10px; padding: 1px 4px; border-radius: 3px;
  background: var(--bt-gray-100); border: 1px solid var(--bt-gray-200);
}

.palette-enter-active { transition: opacity 0.15s ease; }
.palette-leave-active { transition: opacity 0.1s ease; }
.palette-enter-from, .palette-leave-to { opacity: 0; }
.palette-enter-active .palette-container { animation: paletteIn 0.2s ease; }
@keyframes paletteIn {
  from { transform: scale(0.96) translateY(-8px); opacity: 0; }
  to { transform: scale(1) translateY(0); opacity: 1; }
}
</style>
```

- [ ] **Step 3: 集成到App.vue**

在 `App.vue` 中添加命令面板组件，并注册全局快捷键。

```vue
<!-- App.vue 修改 -->
<template>
  <router-view v-slot="{ Component, route }">
    <transition name="page-fade" mode="out-in">
      <KeepAlive :include="KEEP_ALIVE_NAMES">
        <component :is="Component" :key="route.path" />
      </KeepAlive>
    </transition>
  </router-view>
  
  <!-- 命令面板 -->
  <CommandPalette :visible="paletteVisible" @close="closePalette" />
  
  <ToastContainer />
  <ConfirmDialog ... />
</template>

<script setup>
// ... 现有导入 ...
import CommandPalette from '@/components/common/CommandPalette.vue'
import { useCommandPalette } from '@/core/composables/useCommandPalette'

const { visible: paletteVisible, open: openPalette, close: closePalette } = useCommandPalette()

// 在keydown handler中添加
const keydownHandler = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    openPalette()
  }
  // ... 其他快捷键 ...
}
</script>
```

---

## Task 4: 快捷键系统

**Files:**
- Create: `frontend/src/core/composables/useKeyboardShortcuts.ts`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 创建快捷键管理组合式函数**

```typescript
// core/composables/useKeyboardShortcuts.ts
import { onMounted, onUnmounted } from 'vue'

export interface ShortcutConfig {
  key: string
  ctrl?: boolean
  meta?: boolean
  shift?: boolean
  alt?: boolean
  handler: (e: KeyboardEvent) => void
  description: string
}

export function useKeyboardShortcuts(shortcuts: ShortcutConfig[]) {
  const handler = (e: KeyboardEvent) => {
    for (const shortcut of shortcuts) {
      const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase()
      const ctrlMatch = !!shortcut.ctrl === (e.ctrlKey || e.metaKey)
      const shiftMatch = !!shortcut.shift === e.shiftKey
      const altMatch = !!shortcut.alt === e.altKey
      
      if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
        e.preventDefault()
        shortcut.handler(e)
        break
      }
    }
  }
  
  onMounted(() => document.addEventListener('keydown', handler))
  onUnmounted(() => document.removeEventListener('keydown', handler))
}
```

- [ ] **Step 2: 在App.vue中使用**

```typescript
// App.vue
import { useKeyboardShortcuts } from '@/core/composables/useKeyboardShortcuts'
import { useRouter } from 'vue-router'

const router = useRouter()

useKeyboardShortcuts([
  { key: 'k', ctrl: true, handler: () => openPalette(), description: '打开命令面板' },
  { key: 'n', ctrl: true, handler: () => router.push('/tickets/new'), description: '新建工单' },
  { key: 's', ctrl: true, handler: () => router.push('/tickets?filter=pending-payment'), description: '快速结算' },
  { key: 't', ctrl: true, handler: () => router.push('/'), description: '今日视图' },
  { key: 'f', ctrl: true, handler: () => openPalette(), description: '搜索' },
  { key: '?', shift: true, handler: () => showShortcutsHelp(), description: '快捷键帮助' },
])
```

---

## Task 5: 今日视图重构（Dashboard）

**Files:**
- Modify: `frontend/src/modules/dashboard/views/Dashboard.vue`
- Create: `frontend/src/components/common/QuickStats.vue`
- Create: `frontend/src/components/common/ActivityStream.vue`

- [ ] **Step 1: 创建QuickStats组件**

```vue
<!-- components/common/QuickStats.vue -->
<template>
  <div class="quick-stats">
    <div 
      v-for="stat in stats" 
      :key="stat.key"
      class="stat-card"
      :class="{ pulse: stat.pulse, clickable: stat.clickable }"
      @click="stat.onClick"
    >
      <div class="stat-icon">{{ stat.icon }}</div>
      <div class="stat-value" :class="stat.valueClass">{{ stat.value }}</div>
      <div class="stat-label">{{ stat.label }}</div>
      <div v-if="stat.detail" class="stat-detail">{{ stat.detail }}</div>
      <div v-if="stat.progress !== undefined" class="stat-progress">
        <div class="progress-bar" :style="{ width: stat.progress + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface StatItem {
  key: string
  icon: string
  value: string | number
  valueClass?: string
  label: string
  detail?: string
  progress?: number
  pulse?: boolean
  clickable?: boolean
  onClick?: () => void
}

defineProps<{ stats: StatItem[] }>()
</script>

<style scoped>
.quick-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  background: var(--card-bg);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid var(--card-border);
}
.stat-card.clickable { cursor: pointer; }
.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.stat-card.pulse {
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.3); }
  50% { box-shadow: 0 0 0 6px rgba(99, 102, 241, 0); }
}
.stat-icon { font-size: 22px; margin-bottom: 6px; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--bt-text-body); }
.stat-label { font-size: 12px; color: var(--bt-gray-500); margin-top: 4px; }
.stat-detail { font-size: 11px; color: var(--bt-gray-400); margin-top: 2px; }
.stat-progress {
  height: 4px; background: var(--bt-gray-200);
  border-radius: 2px; margin-top: 8px; overflow: hidden;
}
.progress-bar {
  height: 100%; background: var(--bt-primary);
  border-radius: 2px; transition: width 0.5s ease;
}
</style>
```

- [ ] **Step 2: 创建ActivityStream组件**

```vue
<!-- components/common/ActivityStream.vue -->
<template>
  <div class="activity-stream">
    <div class="stream-header">
      <h5><i class="bi bi-activity me-2"></i>今日动态</h5>
      <button class="btn btn-sm btn-link text-muted" @click="clear">清除</button>
    </div>
    <div class="stream-content">
      <div 
        v-for="activity in activities" 
        :key="activity.id"
        class="activity-item"
        :class="activity.type"
      >
        <div class="activity-time">{{ formatTime(activity.time) }}</div>
        <div class="activity-icon">
          <i :class="activity.icon"></i>
        </div>
        <div class="activity-content">
          <div class="activity-title">{{ activity.title }}</div>
          <div class="activity-detail">{{ activity.detail }}</div>
        </div>
        <div v-if="activity.amount" class="activity-amount" :class="{ negative: activity.amount < 0 }">
          {{ activity.amount > 0 ? '+' : '' }}¥{{ Math.abs(activity.amount) }}
        </div>
      </div>
      <div v-if="!activities.length" class="text-muted text-center py-4">暂无动态</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ActivityItem } from '@/core/types'

defineProps<{ activities: ActivityItem[] }>()
const emit = defineEmits(['clear'])

function formatTime(time: string): string {
  return new Date(time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function clear() {
  emit('clear')
}
</script>

<style scoped>
.activity-stream {
  background: var(--card-bg);
  border-radius: 10px;
  border: 1px solid var(--card-border);
  overflow: hidden;
}
.stream-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-bottom: 1px solid var(--card-border);
}
.stream-header h5 { margin: 0; font-size: 14px; font-weight: 600; }
.stream-content { max-height: 320px; overflow-y: auto; padding: 8px 0; }
.activity-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; transition: background 0.15s;
}
.activity-item:hover { background: var(--bt-gray-50); }
.activity-time {
  font-size: 11px; color: var(--bt-gray-400); width: 40px; flex-shrink: 0;
}
.activity-icon {
  width: 28px; height: 28px; border-radius: 6px;
  background: var(--bt-gray-100); display: flex;
  align-items: center; justify-content: center; flex-shrink: 0;
  font-size: 12px; color: var(--bt-gray-500);
}
.activity-content { flex: 1; min-width: 0; }
.activity-title { font-size: 13px; font-weight: 500; }
.activity-detail { font-size: 11px; color: var(--bt-gray-400); margin-top: 2px; }
.activity-amount {
  font-size: 13px; font-weight: 600; color: var(--bt-success); flex-shrink: 0;
}
.activity-amount.negative { color: var(--bt-danger); }
</style>
```

- [ ] **Step 3: 重构Dashboard.vue**

使用新的 QuickStats 和 ActivityStream 组件重构仪表盘，保留现有数据获取逻辑。

---

## Task 6: 双栏工单列表

**Files:**
- Modify: `frontend/src/modules/ticket/views/Tickets.vue`

- [ ] **Step 1: 重构为双栏布局**

左侧工单列表（可筛选、搜索），右侧详情滑出面板。

```vue
<!-- Tickets.vue 核心结构 -->
<template>
  <div class="ticket-workspace">
    <!-- 左侧列表 -->
    <div class="ticket-list" :class="{ collapsed: selectedTicket }">
      <div class="list-header">
        <div class="search-box">
          <i class="bi bi-search"></i>
          <input v-model="searchQuery" placeholder="搜索工单..." />
        </div>
        <div class="filter-tags">
          <button 
            v-for="filter in filters" 
            :key="filter.id"
            class="tag"
            :class="{ active: activeFilter === filter.id }"
            @click="activeFilter = filter.id"
          >
            {{ filter.name }}
          </button>
        </div>
      </div>
      
      <div class="list-content">
        <div 
          v-for="ticket in filteredTickets" 
          :key="ticket.id"
          class="ticket-item"
          :class="{ active: selectedTicket?.id === ticket.id, urgent: isUrgent(ticket) }"
          @click="selectTicket(ticket)"
        >
          <div class="item-header">
            <span class="ticket-id">#{{ ticket.id }}</span>
            <StatusBadge :status="ticket.status" />
            <span class="time">{{ formatDate(ticket.created_at) }}</span>
          </div>
          <div class="client-name">{{ ticket.client_name }}</div>
          <div class="ticket-preview">{{ ticket.content }}</div>
        </div>
      </div>
    </div>
    
    <!-- 右侧详情 -->
    <Transition name="slide">
      <div v-if="selectedTicket" class="ticket-detail">
        <!-- 详情内容 -->
      </div>
    </Transition>
  </div>
</template>
```

---

## Task 7: 移动端快速创建（3秒创建）

**Files:**
- Create: `frontend/src/modules/ticket/views/QuickTicket.vue`
- Modify: `frontend/src/modules/ticket/routes.js`

- [ ] **Step 1: 创建快速创建页面**

3步流程：选择客户 → 描述问题 → 确认创建。每步都有语音输入大按钮。

```vue
<!-- QuickTicket.vue -->
<template>
  <div class="quick-ticket-page">
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: (step / 3 * 100) + '%' }"></div>
    </div>
    
    <!-- 步骤1：客户 -->
    <div v-if="step === 1" class="step">
      <h2>客户是谁？</h2>
      <button class="voice-btn" :class="{ recording: isRecording }" @touchstart="startVoice" @touchend="stopVoice">
        <i class="bi bi-mic"></i>
        <span>{{ isRecording ? '录音中...' : '按住说话' }}</span>
      </button>
      <div class="recent-clients">
        <div class="section-title">最近</div>
        <div class="client-chips">
          <button v-for="client in recentClients" :key="client.id" class="chip" @click="selectClient(client)">
            {{ client.name }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 步骤2：问题 -->
    <div v-if="step === 2" class="step">
      <h2>什么问题？</h2>
      <button class="voice-btn" :class="{ recording: isRecording }" @touchstart="startVoice" @touchend="stopVoice">
        <i class="bi bi-mic"></i>
        <span>{{ isRecording ? '录音中...' : '描述问题' }}</span>
      </button>
      <div class="quick-tags">
        <button v-for="tag in commonIssues" :key="tag" class="tag" @click="addIssue(tag)">
          {{ tag }}
        </button>
      </div>
      <textarea v-model="form.content" placeholder="手动输入..." rows="3" />
    </div>
    
    <!-- 步骤3：确认 -->
    <div v-if="step === 3" class="step">
      <h2>确认创建</h2>
      <div class="summary-card">
        <div class="summary-row">
          <span class="label">客户</span>
          <span class="value">{{ selectedClient?.name }}</span>
        </div>
        <div class="summary-row">
          <span class="label">问题</span>
          <span class="value">{{ form.content }}</span>
        </div>
      </div>
    </div>
    
    <div class="actions">
      <button v-if="step > 1" class="btn btn-secondary" @click="step--">上一步</button>
      <button v-if="step < 3" class="btn btn-primary" @click="step++">下一步</button>
      <button v-if="step === 3" class="btn btn-primary" @click="createTicket">创建工单</button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 添加路由**

```javascript
// routes.js
export default [
  // ... 现有路由 ...
  {
    path: '/tickets/quick',
    name: 'QuickTicket',
    component: () => import('./views/QuickTicket.vue'),
    meta: { title: '快速创建' }
  }
]
```

---

## Task 8: 移动端一键结算

**Files:**
- Create: `frontend/src/modules/ticket/views/QuickSettle.vue`
- Modify: `frontend/src/modules/ticket/routes.js`

- [ ] **Step 1: 创建一键结算页面**

大按钮调整工时，扫码添加材料，选择收款方式，一键确认。

```vue
<!-- QuickSettle.vue -->
<template>
  <div class="quick-settle-page">
    <h2>工单结算 #{{ ticket?.id }}</h2>
    
    <div class="client-card">
      <div class="name">{{ ticket?.client_name }}</div>
      <div class="phone">{{ ticket?.phone }}</div>
    </div>
    
    <!-- 工时 -->
    <div class="section">
      <h3>工时</h3>
      <div class="time-input">
        <button class="btn-adjust" @click="hours -= 0.5">-</button>
        <div class="time-value">{{ hours }}h</div>
        <button class="btn-adjust" @click="hours += 0.5">+</button>
      </div>
    </div>
    
    <!-- 材料 -->
    <div class="section">
      <h3>材料</h3>
      <button class="btn-scan" @click="scanBarcode">
        <i class="bi bi-upc-scan"></i> 扫码添加
      </button>
    </div>
    
    <!-- 金额汇总 -->
    <div class="amount-summary">
      <div class="row"><span>劳务费</span><span>¥{{ laborFee }}</span></div>
      <div class="row"><span>材料费</span><span>¥{{ materialFee }}</span></div>
      <div class="row total"><span>合计</span><span>¥{{ total }}</span></div>
    </div>
    
    <!-- 收款方式 -->
    <div class="payment-methods">
      <button 
        v-for="method in paymentMethods" 
        :key="method.id"
        class="method-btn"
        :class="{ active: selectedMethod === method.id }"
        @click="selectedMethod = method.id"
      >
        <i :class="method.icon"></i>
        <span>{{ method.name }}</span>
      </button>
    </div>
    
    <button class="btn-confirm" @click="confirmSettle">
      确认收款 ¥{{ total }}
    </button>
  </div>
</template>
```

---

## Task 9: 移动端首页适配

**Files:**
- Modify: `frontend/src/modules/dashboard/views/Dashboard.vue`
- Modify: `frontend/src/components/layout/AppLayout.vue`

- [ ] **Step 1: 移动端首页优化**

在移动端显示更紧凑的统计卡片，添加快捷操作按钮（新建、结算、拍照）。

- [ ] **Step 2: 底部导航优化**

在 `AppLayout.vue` 中，移动端底部导航添加更多快捷入口。

---

## Task 10: 离线同步（P2）

**Files:**
- Create: `frontend/src/core/stores/sync.ts`
- Create: `frontend/src/core/composables/useOfflineSync.ts`

- [ ] **Step 1: 创建同步状态Store**

```typescript
// core/stores/sync.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface SyncChange {
  id: string
  type: 'create' | 'update' | 'delete'
  entity: string
  data: Record<string, unknown>
  timestamp: Date
}

export const useSyncStore = defineStore('sync', () => {
  const isOnline = ref(navigator.onLine)
  const lastSync = ref<Date | null>(null)
  const pendingChanges = ref<SyncChange[]>([])
  
  const hasPendingChanges = computed(() => pendingChanges.value.length > 0)
  
  function queueChange(change: Omit<SyncChange, 'id' | 'timestamp'>) {
    pendingChanges.value.push({
      ...change,
      id: Date.now().toString(36) + Math.random().toString(36).substr(2),
      timestamp: new Date()
    })
    localStorage.setItem('pendingChanges', JSON.stringify(pendingChanges.value))
  }
  
  // 监听网络状态
  window.addEventListener('online', () => { isOnline.value = true })
  window.addEventListener('offline', () => { isOnline.value = false })
  
  return { isOnline, lastSync, pendingChanges, hasPendingChanges, queueChange }
})
```

---

## Task 11: TS配置优化

**Files:**
- Modify: `frontend/tsconfig.json`
- Modify: `frontend/vite.config.js`

- [ ] **Step 1: 修改tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "allowJs": true,
    "checkJs": false,
    "paths": {
      "@/*": ["./src/*"]
    },
    "types": ["vite/client"]
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue", "src/**/*.js"]
}
```

- [ ] **Step 2: 修改vite.config.js**

确保路径别名正确配置，支持TS和JS混合开发。

---

## Task 12: 构建验证

**Files:**
- 所有修改的文件

- [ ] **Step 1: 运行类型检查**

```bash
cd frontend
npm run typecheck
```

- [ ] **Step 2: 运行构建**

```bash
cd frontend
npm run build
```

- [ ] **Step 3: 运行测试**

```bash
cd frontend
npm test
```

---

## 移动端重度使用视角补充设计

### 核心场景

| 场景 | 当前痛点 | 优化方案 |
|------|----------|----------|
| 接到电话创建工单 | 需打开浏览器→登录→点击新建→填写10个字段 | 手机桌面快捷方式→3步流程→语音输入 |
| 现场拍照记录 | 需打开相机→拍照→返回系统→上传→选择工单 | 一键拍照→自动关联当前工单 |
| 现场结算收款 | 需打开详情→点击结算→填写金额→选择方式→确认 | 大按钮调整→扫码添加材料→一键确认 |
| 查看今日待办 | 需打开浏览器→登录→查看仪表盘 | 手机桌面小组件→实时显示 |

### 移动端设计原则

1. **拇指友好**：所有可点击区域 >= 48px
2. **单手操作**：核心操作在屏幕下半部分
3. **即时反馈**：按钮按下有视觉反馈（缩放+颜色变化）
4. **离线优先**：断网时数据保存本地，恢复后同步
5. **语音优先**：长按即可语音输入，减少打字

### 移动端页面清单

| 页面 | 路径 | 功能 |
|------|------|------|
| 移动端首页 | `/m` | 今日概览+快捷操作 |
| 快速创建 | `/m/tickets/quick` | 3步创建工单 |
| 一键结算 | `/m/tickets/:id/settle` | 现场结算 |
| 今日工单 | `/m/tickets/today` | 今日工单列表 |
| 客户速查 | `/m/clients` | 客户搜索+拨打 |

---

## 实施路线图

| 阶段 | 时间 | 任务 | 目标 |
|------|------|------|------|
| **P0** | 第1天 | Task 1-2: 类型系统+API TS化 | 核心层类型安全 |
| **P0** | 第2天 | Task 3-4: 命令面板+快捷键 | 操作效率提升50% |
| **P0** | 第3天 | Task 5: 今日视图重构 | 信息获取<5秒 |
| **P1** | 第4天 | Task 6: 双栏工单列表 | 减少页面跳转 |
| **P1** | 第5天 | Task 7-8: 移动端快速创建/结算 | 3秒创建，1分钟结算 |
| **P1** | 第6天 | Task 9: 移动端首页适配 | 移动端体验优化 |
| **P2** | 第7天 | Task 10: 离线同步 | 断网可用 |
| **P2** | 第8天 | Task 11-12: 配置优化+验证 | 构建通过 |

---

## 预期效果

| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 创建工单时间 | 30秒 | 3秒 | **10x** |
| 查找工单时间 | 15秒 | 2秒 | **7.5x** |
| 结算时间 | 3分钟 | 30秒 | **6x** |
| 首屏加载 | 3秒 | 1.5秒 | **2x** |
| 类型安全 | 10% | 70% | **7x** |
| 离线可用性 | 无 | 基本支持 | **∞** |
