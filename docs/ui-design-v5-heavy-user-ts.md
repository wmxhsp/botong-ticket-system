# 博通工单系统 — 重度使用者视角 UI/前端设计 v5.0 (TS增强版)

> 设计目标：每天使用 50+ 次，每次操作 < 3 秒
> 核心原则：**键盘优先、零思考、肌肉记忆**
> TS策略：**核心层全面TS化，业务层JS + JSDoc渐进增强**
> 参考：OpenClaw 的 Control UI（Vite + Lit）、Terminal UI、多通道设计哲学

---

## 一、OpenClaw 设计哲学分析

### 1.1 OpenClaw 核心特点

| 特性 | 实现方式 | 对工单系统的启示 |
|------|----------|------------------|
| **自托管网关** | 本地运行，数据自主 | 工单系统完全本地部署，无需云端 |
| **多通道接入** | WebChat/CLI/移动端/IM | 工单可通过 Web/手机/企微机器人操作 |
| **Control UI** | Vite + Lit，轻量SPA | 前端应极致轻量，首屏 < 1s |
| **终端界面(TUI)** | 命令行图形化 | 支持键盘快捷键， power user 友好 |
| **实时通信** | WebSocket 直连 Gateway | 工单状态实时推送，无需刷新 |
| **会话隔离** | per-sender 会话 | 不同客户/工单的上下文隔离 |
| **工具卡片** | 实时工具输出卡片 | 工单操作的可视化反馈 |
| **Activity Tab** | 实时活动观察器 | 今日工单的实时动态面板 |

### 1.2 OpenClaw UI 设计原则

1. **即时反馈**：所有操作都有视觉反馈，无等待焦虑
2. **键盘优先**：CLI/TUI 支持，Web 端支持快捷键
3. **上下文感知**：根据当前状态动态显示相关操作
4. **渐进披露**：复杂功能分层，不一次性暴露
5. **离线优先**：本地存储，网络恢复后同步
6. **多模态**：文字/语音/图片/文件多种输入方式

---

## 二、重度使用者画像

### 2.1 典型使用场景

```
场景1：早上 8:00（5分钟）
  └─ 打开系统 → 查看今日待办 → 确认预约时间
  
场景2：接到客户电话（30秒）
  └─ 快捷键 N → 输入客户名（自动补全）→ 输入问题 → 回车创建
  
场景3：现场服务中（2分钟）
  └─ 手机拍照 → 语音输入服务内容 → 扫码添加配件 → 一键结算
  
场景4：晚上 21:00（10分钟）
  └─ 查看今日统计 → 确认收入 → 查看明日预约
```

### 2.2 核心痛点

| 痛点 | 当前系统 | 理想状态 |
|------|----------|----------|
| 创建工单太慢 | 需点击5次，填写10个字段 | 快捷键 + 自动补全，3秒完成 |
| 查找历史困难 | 翻页浏览，无搜索 | 模糊搜索，即时结果 |
| 结算流程繁琐 | 多页面跳转 | 一键结算，自动计算 |
| 数据分散 | 工单/财务/库存分开查看 | 统一仪表盘，关联展示 |
| 移动端难用 | 桌面端缩小版 | 原生App体验 |
| 重复录入 | 相同客户需重复输入 | 智能记忆，自动填充 |

---

## 三、TypeScript 策略：核心TS + 业务JS

### 3.1 架构分层与语言选择

```
frontend/src/
├── core/                          # 核心基础设施（全面TS）
│   ├── api/                       # API客户端（TS）
│   │   ├── client.ts              # Axios实例 + 拦截器
│   │   ├── types.ts               # API通用类型
│   │   └── errors.ts              # 错误处理类型
│   ├── stores/                    # 全局状态（TS）
│   │   ├── auth.ts                # 认证状态
│   │   ├── app.ts                 # 应用状态
│   │   └── sync.ts                # 离线同步状态
│   ├── composables/               # 通用组合式函数（TS）
│   │   ├── useApi.ts              # API调用封装
│   │   ├── useCommandPalette.ts   # 命令面板逻辑
│   │   ├── useKeyboardShortcuts.ts# 快捷键管理
│   │   └── useOfflineSync.ts      # 离线同步
│   ├── types/                     # 类型定义（TS）
│   │   ├── index.ts               # 实体类型
│   │   ├── api.ts                 # API类型
│   │   └── ui.ts                  # UI组件类型
│   └── utils/                     # 工具函数（TS）
│       ├── format.ts              # 格式化
│       └── constants.ts           # 常量
│
├── modules/                       # 业务模块（JS + JSDoc）
│   ├── ticket/
│   │   ├── api.ts                 # 模块API（TS）
│   │   ├── stores/                # 模块状态（TS）
│   │   ├── views/                 # 页面（Vue + JS + JSDoc）
│   │   ├── components/            # 组件（Vue + JS + JSDoc）
│   │   └── composables/           # 模块组合式函数（TS）
│   └── ...
│
├── mobile/                        # 移动端（Vue + JS + JSDoc）
│   ├── views/                     # 移动页面
│   └── composables/               # 移动专用逻辑
│
└── main.ts                        # 入口（TS）
```

### 3.2 TS配置优化

```json
// tsconfig.json
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
    "allowJs": true,           // 允许JS文件
    "checkJs": false,          // 不强制检查JS（减少干扰）
    "paths": {
      "@/*": ["./src/*"]
    },
    "types": ["vite/client"]
  },
  "include": [
    "src/**/*.ts",
    "src/**/*.tsx",
    "src/**/*.vue",
    "src/**/*.js"              // 包含JS文件以支持混合开发
  ],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 3.3 类型定义示例

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

export type TicketStatus = 
  | 'open' 
  | 'in-progress' 
  | 'pending-parts' 
  | 'pending-client' 
  | 'pending-payment' 
  | 'completed' 
  | 'closed' 
  | 'cancelled'

export type Priority = 'H' | 'L' | ''
export type BillingType = 'hourly' | 'daily' | 'package'
export type PaymentMethod = '微信' | '支付宝' | '现金' | '银行转账'

export interface TicketPhoto {
  id: number
  filepath: string
  url: string
  created_at: string
}

export interface TicketMaterial {
  id: number
  product_id: number
  product_name: string
  quantity: number
  unit_price: number
  total_price: number
}

export interface TicketServiceItem {
  id: number
  service_name: string
  billing_type: BillingType
  hours?: number
  days?: number
  package_fee?: number
  unit_price: number
  cost_price: number
  line_total: number
  line_cost: number
}

export interface Client {
  id: number
  name: string
  contact: string
  phone: string
  address: string
  hourly_rate: number
  notes: string
}

export interface Technician {
  id: number
  name: string
  phone: string
  skills: string
  cost_rate: number
  daily_cost_rate: number
  package_cost: number
  status: 'active' | 'inactive'
}

export interface DashboardStats {
  today_income: number
  pending_tickets: number
  today_appointments: number
  monthly_profit: number
  profit_progress: number
}

export interface ActivityItem {
  id: number
  type: 'ticket_created' | 'ticket_completed' | 'payment_received' | 'material_used'
  title: string
  detail: string
  amount?: number
  time: string
  icon: string
}

export interface CommandItem {
  id: string
  name: string
  shortcut: string
  icon: string
  action: () => void
  description?: string
}
```

### 3.4 API层TS化示例

```typescript
// core/api/client.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import type { ApiResponse, PaginatedResponse } from '@/core/types'

class ApiClient {
  private client: AxiosInstance
  
  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
      timeout: 15000,
    })
    
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('bt_auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
    
    this.client.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response?.status === 401) {
          window.location.href = '/login'
        }
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
  
  async list<T>(url: string, params?: Record<string, unknown>): Promise<PaginatedResponse<T>> {
    const response = await this.get<T[]>(url, { params })
    return {
      items: response.data || [],
      total: response.total || 0,
      page: response.page || 1,
      page_size: response.page_size || 20,
    }
  }
}

export const apiClient = new ApiClient()
```

```typescript
// core/api/tickets.ts
import { apiClient } from './client'
import type { 
  ApiResponse, 
  PaginatedResponse, 
  Ticket, 
  TicketStatus,
  BillingType 
} from '@/core/types'

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

export interface UpdateTicketData extends Partial<CreateTicketData> {
  id: number
}

export interface SettleTicketData {
  labor_fee: number
  material_fee: number
  total_amount: number
  payment_method: string
  paid_amount: number
}

export const ticketApi = {
  async list(params?: TicketListParams): Promise<PaginatedResponse<Ticket>> {
    return apiClient.list<Ticket>('/tickets', params)
  },
  
  async getById(id: number): Promise<ApiResponse<Ticket>> {
    return apiClient.get<Ticket>(`/tickets/${id}`)
  },
  
  async create(data: CreateTicketData): Promise<ApiResponse<Ticket>> {
    return apiClient.post<Ticket>('/tickets', data)
  },
  
  async update(id: number, data: UpdateTicketData): Promise<ApiResponse<Ticket>> {
    return apiClient.put<Ticket>(`/tickets/${id}`, data)
  },
  
  async delete(id: number): Promise<ApiResponse<void>> {
    return apiClient.delete(`/tickets/${id}`)
  },
  
  async settle(id: number, data: SettleTicketData): Promise<ApiResponse<Ticket>> {
    return apiClient.post<Ticket>(`/tickets/${id}/settle`, data)
  },
  
  async addPhoto(id: number, file: File): Promise<ApiResponse<Ticket>> {
    const formData = new FormData()
    formData.append('photo', file)
    return apiClient.post<Ticket>(`/tickets/${id}/photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  async addMaterial(id: number, materialId: number, quantity: number): Promise<ApiResponse<Ticket>> {
    return apiClient.post<Ticket>(`/tickets/${id}/materials`, {
      product_id: materialId,
      quantity
    })
  }
}
```

### 3.5 业务层JS + JSDoc示例

```javascript
// modules/ticket/views/Tickets.vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ticketApi } from '@/core/api/tickets'
import { useAuthStore } from '@/core/stores/auth'

/** @type {import('vue').Ref<import('@/core/types').Ticket[]>} */
const tickets = ref([])

/** @type {import('vue').Ref<import('@/core/types').Ticket | null>} */
const selectedTicket = ref(null)

/** @type {import('vue').Ref<boolean>} */
const loading = ref(false)

/** @type {import('vue').Ref<string>} */
const searchQuery = ref('')

/** @type {import('vue').Ref<string>} */
const activeFilter = ref('all')

/** @type {import('vue').Ref<import('@/core/types').TicketStatus | ''>} */
const statusFilter = ref('')

/** @type {import('vue').Ref<number>} */
const currentPage = ref(1)

/** @type {import('vue').Ref<number>} */
const totalItems = ref(0)

const router = useRouter()
const authStore = useAuthStore()

/** @type {import('vue').ComputedRef<import('@/core/types').Ticket[]>} */
const filteredTickets = computed(() => {
  let result = tickets.value
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(t => 
      t.client_name?.toLowerCase().includes(query) ||
      t.content?.toLowerCase().includes(query) ||
      t.ticket_no?.toLowerCase().includes(query)
    )
  }
  
  if (statusFilter.value) {
    result = result.filter(t => t.status === statusFilter.value)
  }
  
  return result
})

/**
 * 获取工单列表
 * @returns {Promise<void>}
 */
async function fetchTickets() {
  loading.value = true
  try {
    const response = await ticketApi.list({
      page: currentPage.value,
      page_size: 20,
      status: statusFilter.value || undefined,
      search: searchQuery.value || undefined
    })
    tickets.value = response.items
    totalItems.value = response.total
  } catch (error) {
    console.error('获取工单失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 选择工单
 * @param {import('@/core/types').Ticket} ticket
 */
function selectTicket(ticket) {
  selectedTicket.value = ticket
}

/**
 * 查看工单详情
 * @param {import('@/core/types').Ticket} ticket
 */
function viewTicketDetail(ticket) {
  router.push(`/tickets/${ticket.id}`)
}

/**
 * 创建新工单
 */
function createTicket() {
  router.push('/tickets/new')
}

/**
 * 判断工单是否紧急
 * @param {import('@/core/types').Ticket} ticket
 * @returns {boolean}
 */
function isUrgent(ticket) {
  return ticket.priority === 'H' && ticket.status !== 'completed'
}

onMounted(() => {
  fetchTickets()
})
</script>
```

---

## 四、Web 端设计（桌面重度使用）

### 4.1 整体布局：三栏式 + 命令面板

```
+-------------------------------------------------------------+
|  Cmd+K 命令面板  |  标题栏（当前视图 + 快捷操作）            |
+----------+--------------------------------------------------+
|          |                                                  |
|  导航栏   |              主内容区                             |
|  (可折叠) |                                                  |
|          |  +--------------------------------------------+  |
|  · 今日   |  |  今日概览卡片（收入/工单/待办）              |  |
|  · 工单   |  +--------------------------------------------+  |
|  · 客户   |                                                  |
|  · 财务   |  +------------------+------------------------+  |
|  · 库存   |  |   工单列表        |    工单详情/编辑        |  |
|  · 统计   |  |  （可筛选排序）    |   （右侧滑出）          |  |
|          |  +------------------+------------------------+  |
|  · 设置   |                                                  |
|          |                                                  |
+----------+--------------------------------------------------+
|  状态栏：当前用户 · 最后同步时间 · 离线/在线状态              |
+-------------------------------------------------------------+
```

### 4.2 命令面板（Cmd+K）— 核心交互

参考 OpenClaw 的 CLI 和 Control UI 的搜索体验：

```vue
<!-- core/components/CommandPalette.vue -->
<template>
  <div v-if="visible" class="command-palette" @keydown.esc="close">
    <div class="palette-overlay" @click="close"></div>
    <div class="palette-container">
      <div class="palette-input">
        <i class="bi bi-search"></i>
        <input 
          ref="inputRef"
          v-model="query"
          placeholder="输入命令或搜索... (Esc关闭)"
          @keydown.enter="execute"
          @keydown.up="selectPrev"
          @keydown.down="selectNext"
        />
        <span class="shortcut-hint">↵ 执行</span>
      </div>
      
      <div class="palette-results">
        <!-- 最近使用 -->
        <div v-if="!query" class="section">
          <div class="section-title">最近使用</div>
          <div 
            v-for="(item, i) in recentCommands" 
            :key="i"
            class="result-item"
            :class="{ active: selectedIndex === i }"
            @click="executeCommand(item)"
          >
            <i :class="item.icon"></i>
            <span class="name">{{ item.name }}</span>
            <span class="shortcut">{{ item.shortcut }}</span>
          </div>
        </div>
        
        <!-- 搜索结果 -->
        <div v-else class="section">
          <div class="section-title">工单</div>
          <div 
            v-for="ticket in searchResults.tickets" 
            :key="ticket.id"
            class="result-item"
            @click="openTicket(ticket)"
          >
            <span class="ticket-id">#{{ ticket.id }}</span>
            <span class="client">{{ ticket.client_name }}</span>
            <StatusBadge :status="ticket.status" />
          </div>
          
          <div class="section-title">客户</div>
          <div 
            v-for="client in searchResults.clients" 
            :key="client.id"
            class="result-item"
            @click="openClient(client)"
          >
            <i class="bi bi-person"></i>
            <span>{{ client.name }}</span>
            <span class="phone">{{ client.phone }}</span>
          </div>
          
          <div class="section-title">快捷命令</div>
          <div 
            v-for="cmd in filteredCommands" 
            :key="cmd.id"
            class="result-item"
            :class="{ active: selectedIndex === i }"
            @click="executeCommand(cmd)"
          >
            <i :class="cmd.icon"></i>
            <span class="name">{{ cmd.name }}</span>
            <span class="desc">{{ cmd.description }}</span>
            <span class="shortcut">{{ cmd.shortcut }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import type { CommandItem, Ticket, Client } from '@/core/types'

const visible = ref(false)
const query = ref('')
const selectedIndex = ref(0)
const inputRef = ref<HTMLInputElement>()
const router = useRouter()

const commands: CommandItem[] = [
  { id: 'new-ticket', name: '新建工单', shortcut: 'N', icon: 'bi bi-plus', action: () => router.push('/tickets/new') },
  { id: 'quick-settle', name: '快速结算', shortcut: 'S', icon: 'bi bi-check-circle', action: () => openQuickSettle() },
  { id: 'today-view', name: '今日视图', shortcut: 'T', icon: 'bi bi-calendar-day', action: () => router.push('/today') },
  { id: 'search-client', name: '搜索客户', shortcut: 'C', icon: 'bi bi-people', action: () => focusSearch('client') },
  { id: 'voice-input', name: '语音输入', shortcut: 'V', icon: 'bi bi-mic', action: () => startVoiceInput() },
  { id: 'sync-data', name: '同步数据', shortcut: 'R', icon: 'bi bi-arrow-clockwise', action: () => syncData() },
  { id: 'dark-mode', name: '切换主题', shortcut: 'D', icon: 'bi bi-moon', action: () => toggleTheme() },
  { id: 'fullscreen', name: '全屏模式', shortcut: 'F', icon: 'bi bi-fullscreen', action: () => toggleFullscreen() },
]

const recentCommands = ref<CommandItem[]>([])
const searchResults = ref<{ tickets: Ticket[]; clients: Client[] }>({ tickets: [], clients: [] })

const filteredCommands = computed(() => {
  if (!query.value) return commands
  const q = query.value.toLowerCase()
  return commands.filter(c => 
    c.name.toLowerCase().includes(q) || 
    c.description?.toLowerCase().includes(q)
  )
})

function open() {
  visible.value = true
  nextTick(() => inputRef.value?.focus())
}

function close() {
  visible.value = false
  query.value = ''
}

function execute() {
  // 执行选中项
}

function selectPrev() {
  selectedIndex.value = Math.max(0, selectedIndex.value - 1)
}

function selectNext() {
  selectedIndex.value++
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

// 快捷键监听
onMounted(() => {
  window.addEventListener('keydown', (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      open()
    }
    if (e.key === 'Escape') close()
  })
})
</script>

<style scoped>
.command-palette {
  position: fixed;
  inset: 0;
  z-index: 9999;
}

.palette-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
}

.palette-container {
  position: absolute;
  top: 15%;
  left: 50%;
  transform: translateX(-50%);
  width: 640px;
  max-width: 90vw;
  background: var(--bt-card-bg);
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  overflow: hidden;
}

.palette-input {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--bt-gray-200);
}

.palette-input input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 16px;
  outline: none;
}

.shortcut-hint {
  font-size: 12px;
  color: var(--bt-gray-400);
  padding: 4px 8px;
  background: var(--bt-gray-100);
  border-radius: 4px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  cursor: pointer;
  transition: background 0.15s;
}

.result-item:hover,
.result-item.active {
  background: var(--bt-gray-100);
}

.result-item .shortcut {
  margin-left: auto;
  font-size: 12px;
  color: var(--bt-gray-400);
  padding: 2px 6px;
  background: var(--bt-gray-200);
  border-radius: 4px;
}
</style>
```

### 4.3 今日视图（默认首页）

参考 OpenClaw 的 Activity Tab 实时活动观察器：

```vue
<!-- modules/dashboard/views/Dashboard.vue -->
<template>
  <div class="today-view">
    <!-- 顶部快捷数据 -->
    <div class="quick-stats">
      <div class="stat-card" :class="{ pulse: hasNewIncome }">
        <div class="stat-icon">💰</div>
        <div class="stat-value">¥{{ todayIncome }}</div>
        <div class="stat-label">今日收入</div>
        <div class="stat-trend" v-if="incomeTrend">+{{ incomeTrend }}%</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-value">{{ pendingTickets }}</div>
        <div class="stat-label">待处理</div>
        <div class="stat-detail">{{ todayAppointments }}个预约</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⏰</div>
        <div class="stat-value">{{ overdueTodos }}</div>
        <div class="stat-label">待办逾期</div>
      </div>
      <div class="stat-card clickable" @click="showMonthlyDetail">
        <div class="stat-icon">📈</div>
        <div class="stat-value">¥{{ monthlyProfit }}</div>
        <div class="stat-label">本月利润</div>
        <div class="stat-progress">
          <div class="progress-bar" :style="{ width: profitProgress + '%' }"></div>
        </div>
      </div>
    </div>
    
    <!-- 实时活动流（参考 OpenClaw Activity Tab） -->
    <div class="activity-stream">
      <div class="stream-header">
        <h3>今日动态</h3>
        <button class="btn-text" @click="clearStream">清除</button>
      </div>
      <div class="stream-content" ref="streamRef">
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
          <div class="activity-amount" v-if="activity.amount">
            {{ activity.amount > 0 ? '+' : '' }}¥{{ Math.abs(activity.amount) }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 快捷操作区 -->
    <div class="quick-actions">
      <button class="action-btn primary" @click="createTicket">
        <i class="bi bi-plus-lg"></i>
        <span>新建工单 (Ctrl+N)</span>
      </button>
      <button class="action-btn" @click="quickSettle">
        <i class="bi bi-check-circle"></i>
        <span>快速结算 (Ctrl+S)</span>
      </button>
      <button class="action-btn" @click="voiceNote">
        <i class="bi bi-mic"></i>
        <span>语音备忘 (Ctrl+V)</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardApi } from '@/core/api/dashboard'
import type { DashboardStats, ActivityItem } from '@/core/types'

const router = useRouter()

const stats = ref<DashboardStats>({
  today_income: 0,
  pending_tickets: 0,
  today_appointments: 0,
  monthly_profit: 0,
  profit_progress: 0
})

const activities = ref<ActivityItem[]>([])
const hasNewIncome = ref(false)

const todayIncome = computed(() => stats.value.today_income)
const pendingTickets = computed(() => stats.value.pending_tickets)
const todayAppointments = computed(() => stats.value.today_appointments)
const monthlyProfit = computed(() => stats.value.monthly_profit)
const profitProgress = computed(() => stats.value.profit_progress)
const overdueTodos = ref(0)
const incomeTrend = ref(12)

async function fetchDashboard() {
  try {
    const response = await dashboardApi.getTodayStats()
    stats.value = response.data
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
  }
}

function createTicket() {
  router.push('/tickets/new')
}

function quickSettle() {
  router.push('/quick-settle')
}

function voiceNote() {
  // 启动语音输入
}

function showMonthlyDetail() {
  router.push('/finance')
}

function clearStream() {
  activities.value = []
}

function formatTime(time: string): string {
  return new Date(time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchDashboard()
})
</script>

<style scoped>
.today-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.quick-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bt-card-bg);
  border-radius: 12px;
  padding: 20px;
  position: relative;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.stat-card.pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(99, 102, 241, 0); }
}

.stat-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--bt-gray-800);
}

.stat-label {
  font-size: 13px;
  color: var(--bt-gray-400);
  margin-top: 4px;
}

.activity-stream {
  background: var(--bt-card-bg);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  max-height: 400px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--bt-gray-100);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-time {
  font-size: 12px;
  color: var(--bt-gray-400);
  width: 50px;
  flex-shrink: 0;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--bt-gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-weight: 500;
}

.activity-detail {
  font-size: 12px;
  color: var(--bt-gray-400);
}

.activity-amount {
  font-weight: 600;
  color: var(--bt-success);
}

.activity-amount.negative {
  color: var(--bt-danger);
}

.quick-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 8px;
  border: 1px solid var(--bt-gray-200);
  background: var(--bt-card-bg);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--bt-gray-50);
}

.action-btn.primary {
  background: var(--bt-primary);
  color: white;
  border-color: var(--bt-primary);
}

.action-btn.primary:hover {
  background: var(--bt-primary-dark);
}
</style>
```

### 4.4 工单列表：双栏 + 内联编辑

```vue
<!-- modules/ticket/views/Tickets.vue -->
<template>
  <div class="ticket-workspace">
    <!-- 左侧列表 -->
    <div class="ticket-list" :class="{ collapsed: showDetail }">
      <div class="list-header">
        <div class="search-box">
          <i class="bi bi-search"></i>
          <input 
            v-model="searchQuery" 
            placeholder="搜索工单 #编号 客户 内容..."
            @focus="showFilters = true"
          />
          <button class="btn-icon" @click="showFilters = !showFilters">
            <i class="bi bi-funnel"></i>
          </button>
        </div>
        
        <!-- 快速筛选标签 -->
        <div class="filter-tags">
          <button 
            v-for="filter in quickFilters" 
            :key="filter.id"
            class="tag"
            :class="{ active: activeFilter === filter.id }"
            @click="activeFilter = filter.id"
          >
            {{ filter.name }} ({{ filter.count }})
          </button>
        </div>
      </div>
      
      <div class="list-content" ref="listRef">
        <div 
          v-for="ticket in filteredTickets" 
          :key="ticket.id"
          class="ticket-item"
          :class="{ 
            active: selectedTicket?.id === ticket.id,
            urgent: isUrgent(ticket)
          }"
          @click="selectTicket(ticket)"
        >
          <div class="item-header">
            <span class="ticket-id">#{{ ticket.id }}</span>
            <StatusBadge :status="ticket.status" />
            <span class="time">{{ formatTime(ticket.created_at) }}</span>
          </div>
          <div class="client-name">{{ ticket.client_name }}</div>
          <div class="ticket-preview">{{ ticket.content }}</div>
          <div class="item-footer">
            <span class="amount" v-if="ticket.total_amount">¥{{ ticket.total_amount }}</span>
            <span class="technician" v-if="ticket.technician_name">
              <i class="bi bi-person"></i> {{ ticket.technician_name }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧详情（滑出） -->
    <Transition name="slide">
      <div v-if="showDetail" class="ticket-detail">
        <div class="detail-header">
          <button class="btn-icon" @click="showDetail = false">
            <i class="bi bi-x-lg"></i>
          </button>
          <h3>#{{ selectedTicket?.id }} {{ selectedTicket?.client_name }}</h3>
          <div class="header-actions">
            <button class="btn-text" @click="editTicket">编辑</button>
            <button class="btn-primary" @click="quickSettle">结算</button>
          </div>
        </div>
        
        <div class="detail-content">
          <!-- 工单信息 -->
          <div class="info-section">
            <div class="info-row">
              <span class="label">状态</span>
              <StatusBadge :status="selectedTicket?.status" />
            </div>
            <div class="info-row">
              <span class="label">客户</span>
              <span>{{ selectedTicket?.client_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">电话</span>
              <a :href="`tel:${selectedTicket?.phone}`">{{ selectedTicket?.phone }}</a>
            </div>
            <div class="info-row">
              <span class="label">地址</span>
              <span>{{ selectedTicket?.address }}</span>
            </div>
          </div>
          
          <!-- 服务内容 -->
          <div class="content-section">
            <h4>问题描述</h4>
            <p>{{ selectedTicket?.content }}</p>
          </div>
          
          <!-- 服务明细 -->
          <div class="service-section">
            <h4>服务明细</h4>
            <div v-for="item in selectedTicket?.service_items" :key="item.id" class="service-item">
              <span>{{ item.service_name }}</span>
              <span>{{ item.hours }}h × ¥{{ item.unit_price }} = ¥{{ item.line_total }}</span>
            </div>
          </div>
          
          <!-- 材料 -->
          <div class="materials-section">
            <h4>使用材料</h4>
            <div v-for="m in selectedTicket?.materials" :key="m.id" class="material-item">
              <span>{{ m.product_name }} x{{ m.quantity }}</span>
              <span>¥{{ m.total_price }}</span>
            </div>
          </div>
          
          <!-- 金额汇总 -->
          <div class="amount-summary">
            <div class="summary-row">
              <span>劳务费</span>
              <span>¥{{ selectedTicket?.labor_fee }}</span>
            </div>
            <div class="summary-row">
              <span>材料费</span>
              <span>¥{{ selectedTicket?.material_fee }}</span>
            </div>
            <div class="summary-row total">
              <span>合计</span>
              <span>¥{{ selectedTicket?.total_amount }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ticketApi } from '@/core/api/tickets'
import type { Ticket, TicketStatus } from '@/core/types'

const router = useRouter()

const tickets = ref<Ticket[]>([])
const selectedTicket = ref<Ticket | null>(null)
const loading = ref(false)
const searchQuery = ref('')
const activeFilter = ref('all')
const statusFilter = ref<TicketStatus | ''>('')
const currentPage = ref(1)
const totalItems = ref(0)
const showDetail = ref(false)
const showFilters = ref(false)

const quickFilters = [
  { id: 'all', name: '全部', count: 0 },
  { id: 'today', name: '今日', count: 0 },
  { id: 'pending', name: '待处理', count: 0 },
  { id: 'urgent', name: '紧急', count: 0 },
]

const filteredTickets = computed(() => {
  let result = tickets.value
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(t => 
      t.client_name?.toLowerCase().includes(query) ||
      t.content?.toLowerCase().includes(query) ||
      t.ticket_no?.toLowerCase().includes(query)
    )
  }
  
  if (statusFilter.value) {
    result = result.filter(t => t.status === statusFilter.value)
  }
  
  return result
})

async function fetchTickets() {
  loading.value = true
  try {
    const response = await ticketApi.list({
      page: currentPage.value,
      page_size: 20,
      status: statusFilter.value || undefined,
      search: searchQuery.value || undefined
    })
    tickets.value = response.items
    totalItems.value = response.total
  } catch (error) {
    console.error('获取工单失败:', error)
  } finally {
    loading.value = false
  }
}

function selectTicket(ticket: Ticket) {
  selectedTicket.value = ticket
  showDetail.value = true
}

function editTicket() {
  if (selectedTicket.value) {
    router.push(`/tickets/${selectedTicket.value.id}/edit`)
  }
}

function quickSettle() {
  if (selectedTicket.value) {
    router.push(`/tickets/${selectedTicket.value.id}/settle`)
  }
}

function isUrgent(ticket: Ticket): boolean {
  return ticket.priority === 'H' && ticket.status !== 'completed'
}

function formatTime(time: string): string {
  return new Date(time).toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchTickets()
})
</script>

<style scoped>
.ticket-workspace {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.ticket-list {
  flex: 1;
  min-width: 360px;
  max-width: 480px;
  border-right: 1px solid var(--bt-gray-200);
  display: flex;
  flex-direction: column;
}

.ticket-list.collapsed {
  max-width: 360px;
}

.list-header {
  padding: 16px;
  border-bottom: 1px solid var(--bt-gray-200);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bt-gray-100);
  border-radius: 8px;
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
}

.filter-tags {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  overflow-x: auto;
}

.tag {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  border: 1px solid var(--bt-gray-200);
  background: transparent;
  cursor: pointer;
  white-space: nowrap;
}

.tag.active {
  background: var(--bt-primary);
  color: white;
  border-color: var(--bt-primary);
}

.list-content {
  flex: 1;
  overflow-y: auto;
}

.ticket-item {
  padding: 16px;
  border-bottom: 1px solid var(--bt-gray-100);
  cursor: pointer;
  transition: background 0.15s;
}

.ticket-item:hover {
  background: var(--bt-gray-50);
}

.ticket-item.active {
  background: rgba(99, 102, 241, 0.05);
  border-left: 3px solid var(--bt-primary);
}

.ticket-item.urgent {
  border-left: 3px solid var(--bt-danger);
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.ticket-id {
  font-size: 12px;
  color: var(--bt-gray-400);
}

.time {
  margin-left: auto;
  font-size: 12px;
  color: var(--bt-gray-400);
}

.client-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.ticket-preview {
  font-size: 13px;
  color: var(--bt-gray-500);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-footer {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  font-size: 12px;
}

.amount {
  color: var(--bt-success);
  font-weight: 600;
}

.technician {
  color: var(--bt-gray-400);
}

.ticket-detail {
  flex: 1;
  min-width: 480px;
  background: var(--bt-card-bg);
  overflow-y: auto;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--bt-gray-200);
  position: sticky;
  top: 0;
  background: var(--bt-card-bg);
  z-index: 10;
}

.detail-header h3 {
  flex: 1;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.detail-content {
  padding: 20px;
}

.info-section,
.content-section,
.service-section,
.materials-section {
  margin-bottom: 24px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--bt-gray-100);
}

.info-row .label {
  color: var(--bt-gray-400);
}

.amount-summary {
  background: var(--bt-gray-50);
  border-radius: 8px;
  padding: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}

.summary-row.total {
  border-top: 2px solid var(--bt-gray-200);
  margin-top: 8px;
  padding-top: 12px;
  font-size: 18px;
  font-weight: 700;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
```

---

## 五、移动端设计（原生App体验）

### 5.1 整体架构：底部导航 + 浮动按钮

参考 OpenClaw 的移动端 Nodes 设计：

```
+------------------------------------------+
|  Header（时间 + 收入速览）                 |
+------------------------------------------+
|                                          |
|  [今日收入] [待处理] [本月利润]            |
|     ¥1,250     3单      ¥8,600           |
|                                          |
|  ┌────────────────────────────────────┐  |
|  │  🔴 小微公司A  网络故障  10:30     │  |
|  │  🟡 个人散户    系统重装  14:00     │  |
|  │  🟢 家庭用户    已完成    09:00     │  |
|  └────────────────────────────────────┘  |
|                                          |
|  [最近活动]                                |
|  10:30 完成工单 #123 +¥400               |
|  09:15 创建工单 #124                     |
|                                          |
+------------------------------------------+
|  [首页] [工单] [➕] [客户] [我的]        |
+------------------------------------------+

浮动按钮（长按展开）：
- 新建工单
- 语音备忘
- 扫码添加
```

### 5.2 快速创建（3秒完成）

参考 OpenClaw 的语音输入和实时会话：

```vue
<!-- mobile/views/QuickTicket.vue -->
<template>
  <div class="quick-ticket-page">
    <!-- 步骤指示器（进度条） -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: (step / 3 * 100) + '%' }"></div>
    </div>
    
    <!-- 步骤1：客户（语音优先） -->
    <div v-if="step === 1" class="step">
      <h2>客户是谁？</h2>
      
      <!-- 语音输入大按钮 -->
      <button 
        class="voice-btn"
        :class="{ recording: isRecording }"
        @touchstart="startVoice"
        @touchend="stopVoice"
      >
        <i class="bi bi-mic"></i>
        <span>{{ isRecording ? '录音中...' : '按住说话' }}</span>
      </button>
      
      <!-- 最近客户快捷选择 -->
      <div class="recent-clients">
        <div class="section-title">最近</div>
        <div class="client-chips">
          <button 
            v-for="client in recentClients" 
            :key="client.id"
            class="chip"
            @click="selectClient(client)"
          >
            {{ client.name }}
          </button>
        </div>
      </div>
      
      <!-- 搜索 -->
      <div class="search-box">
        <i class="bi bi-search"></i>
        <input 
          v-model="clientSearch"
          placeholder="搜索客户..."
          @input="searchClients"
        />
      </div>
    </div>
    
    <!-- 步骤2：问题描述 -->
    <div v-if="step === 2" class="step">
      <h2>什么问题？</h2>
      
      <button 
        class="voice-btn"
        :class="{ recording: isRecording }"
        @touchstart="startVoice"
        @touchend="stopVoice"
      >
        <i class="bi bi-mic"></i>
        <span>{{ isRecording ? '录音中...' : '描述问题' }}</span>
      </button>
      
      <!-- 快捷标签 -->
      <div class="quick-tags">
        <button 
          v-for="tag in commonIssues" 
          :key="tag"
          class="tag"
          @click="addIssue(tag)"
        >
          {{ tag }}
        </button>
      </div>
      
      <textarea 
        v-model="form.content"
        placeholder="手动输入..."
        rows="3"
      />
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
        <div class="summary-row">
          <span class="label">预约</span>
          <span class="value">{{ form.appointment || '尽快' }}</span>
        </div>
      </div>
      
      <!-- 预计收入（智能计算） -->
      <div class="estimate" v-if="estimatedIncome">
        <span>预计收入</span>
        <span class="amount">¥{{ estimatedIncome }}</span>
      </div>
    </div>
    
    <!-- 底部操作 -->
    <div class="actions">
      <button v-if="step > 1" class="btn-secondary" @click="step--">
        上一步
      </button>
      <button v-if="step < 3" class="btn-primary" @click="step++">
        下一步
      </button>
      <button v-if="step === 3" class="btn-primary" @click="createTicket">
        创建工单
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ticketApi } from '@/core/api/tickets'
import { clientApi } from '@/core/api/clients'
import type { Client, CreateTicketData } from '@/core/types'

const router = useRouter()

const step = ref(1)
const isRecording = ref(false)
const clientSearch = ref('')
const recentClients = ref<Client[]>([])
const selectedClient = ref<Client | null>(null)
const estimatedIncome = ref(0)

const form = ref<Partial<CreateTicketData>>({
  client_id: undefined,
  content: '',
  appointment: ''
})

const commonIssues = [
  '无法开机',
  '网络故障',
  '系统重装',
  '数据恢复',
  '病毒清理',
  '硬件更换'
]

async function searchClients() {
  if (!clientSearch.value) return
  const response = await clientApi.search(clientSearch.value)
  recentClients.value = response.data
}

function selectClient(client: Client) {
  selectedClient.value = client
  form.value.client_id = client.id
  step.value = 2
}

function addIssue(issue: string) {
  form.value.content = issue
}

async function createTicket() {
  if (!form.value.client_id || !form.value.content) return
  
  try {
    const response = await ticketApi.create(form.value as CreateTicketData)
    router.push(`/tickets/${response.data.id}`)
  } catch (error) {
    console.error('创建工单失败:', error)
  }
}

function startVoice() {
  isRecording.value = true
  // 启动语音识别
}

function stopVoice() {
  isRecording.value = false
  // 停止语音识别
}
</script>

<style scoped>
.quick-ticket-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bt-bg);
}

.progress-bar {
  height: 3px;
  background: var(--bt-gray-200);
}

.progress-fill {
  height: 100%;
  background: var(--bt-primary);
  transition: width 0.3s;
}

.step {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.step h2 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
}

.voice-btn {
  width: 100%;
  padding: 40px;
  border-radius: 16px;
  border: 2px dashed var(--bt-gray-300);
  background: var(--bt-card-bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.voice-btn.recording {
  border-color: var(--bt-primary);
  background: rgba(99, 102, 241, 0.05);
}

.voice-btn i {
  font-size: 48px;
  color: var(--bt-primary);
}

.recent-clients {
  margin-bottom: 20px;
}

.section-title {
  font-size: 12px;
  color: var(--bt-gray-400);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 12px;
}

.client-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 8px 16px;
  border-radius: 20px;
  background: var(--bt-card-bg);
  border: 1px solid var(--bt-gray-200);
  font-size: 14px;
}

.chip:active {
  background: var(--bt-primary);
  color: white;
}

.quick-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.tag {
  padding: 8px 16px;
  border-radius: 20px;
  background: var(--bt-gray-100);
  border: none;
  font-size: 13px;
}

.actions {
  padding: 16px;
  display: flex;
  gap: 12px;
  background: var(--bt-card-bg);
  border-top: 1px solid var(--bt-gray-200);
}

.actions button {
  flex: 1;
  padding: 14px;
  border-radius: 8px;
  border: none;
  font-size: 16px;
  font-weight: 500;
}

.btn-primary {
  background: var(--bt-primary);
  color: white;
}

.btn-secondary {
  background: var(--bt-gray-100);
  color: var(--bt-gray-700);
}

.summary-card {
  background: var(--bt-card-bg);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--bt-gray-100);
}

.summary-row:last-child {
  border-bottom: none;
}

.summary-row .label {
  color: var(--bt-gray-400);
}

.estimate {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--bt-gray-50);
  border-radius: 8px;
}

.estimate .amount {
  font-size: 24px;
  font-weight: 700;
  color: var(--bt-success);
}
</style>
```

### 5.3 一键结算（现场快速操作）

```vue
<!-- mobile/views/QuickSettle.vue -->
<template>
  <div class="quick-settle-page">
    <h2>工单结算 #{{ ticket?.id }}</h2>
    
    <!-- 客户信息卡片 -->
    <div class="client-card">
      <div class="name">{{ ticket?.client_name }}</div>
      <div class="phone">{{ ticket?.phone }}</div>
    </div>
    
    <!-- 工时记录（大按钮） -->
    <div class="section">
      <h3>工时</h3>
      <div class="time-input">
        <button class="btn-adjust" @click="hours -= 0.5">-</button>
        <div class="time-value">{{ hours }}h</div>
        <button class="btn-adjust" @click="hours += 0.5">+</button>
      </div>
    </div>
    
    <!-- 材料（扫码添加） -->
    <div class="section">
      <h3>材料</h3>
      <button class="btn-scan" @click="scanBarcode">
        <i class="bi bi-upc-scan"></i>
        扫码添加
      </button>
      <div class="material-list">
        <div v-for="m in materials" :key="m.id" class="material-item">
          <span>{{ m.name }}</span>
          <div class="quantity">
            <button @click="m.quantity--">-</button>
            <span>{{ m.quantity }}</span>
            <button @click="m.quantity++">+</button>
          </div>
          <span>¥{{ m.price * m.quantity }}</span>
        </div>
      </div>
    </div>
    
    <!-- 金额汇总 -->
    <div class="amount-summary">
      <div class="row">
        <span>劳务费</span>
        <span>¥{{ laborFee }}</span>
      </div>
      <div class="row">
        <span>材料费</span>
        <span>¥{{ materialFee }}</span>
      </div>
      <div class="row total">
        <span>合计</span>
        <span>¥{{ total }}</span>
      </div>
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
    
    <!-- 确认按钮 -->
    <button class="btn-confirm" @click="confirmSettle">
      确认收款 ¥{{ total }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ticketApi } from '@/core/api/tickets'
import type { Ticket, SettleTicketData, PaymentMethod } from '@/core/types'

const route = useRoute()
const router = useRouter()

const ticket = ref<Ticket | null>(null)
const hours = ref(1)
const materials = ref<Array<{ id: number; name: string; price: number; quantity: number }>>([])
const selectedMethod = ref<PaymentMethod>('微信')

const paymentMethods = [
  { id: 'wechat' as PaymentMethod, name: '微信', icon: 'bi bi-wechat' },
  { id: 'alipay' as PaymentMethod, name: '支付宝', icon: 'bi bi-alipay' },
  { id: 'cash' as PaymentMethod, name: '现金', icon: 'bi bi-cash' },
]

const laborFee = computed(() => {
  if (!ticket.value) return 0
  return hours.value * (ticket.value.hourly_rate || 80)
})

const materialFee = computed(() => {
  return materials.value.reduce((sum, m) => sum + m.price * m.quantity, 0)
})

const total = computed(() => laborFee.value + materialFee.value)

async function fetchTicket() {
  const id = parseInt(route.params.id as string)
  try {
    const response = await ticketApi.getById(id)
    ticket.value = response.data
  } catch (error) {
    console.error('获取工单失败:', error)
  }
}

function scanBarcode() {
  // 调用摄像头扫码
}

async function confirmSettle() {
  if (!ticket.value) return
  
  const data: SettleTicketData = {
    labor_fee: laborFee.value,
    material_fee: materialFee.value,
    total_amount: total.value,
    payment_method: selectedMethod.value,
    paid_amount: total.value
  }
  
  try {
    await ticketApi.settle(ticket.value.id, data)
    router.push('/tickets')
  } catch (error) {
    console.error('结算失败:', error)
  }
}

fetchTicket()
</script>

<style scoped>
.quick-settle-page {
  padding: 20px;
  padding-bottom: 100px;
}

.client-card {
  background: var(--bt-card-bg);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.client-card .name {
  font-size: 18px;
  font-weight: 600;
}

.client-card .phone {
  color: var(--bt-gray-400);
  margin-top: 4px;
}

.section {
  margin-bottom: 24px;
}

.section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.time-input {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
}

.btn-adjust {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: var(--bt-gray-100);
  font-size: 24px;
}

.time-value {
  font-size: 32px;
  font-weight: 700;
}

.btn-scan {
  width: 100%;
  padding: 16px;
  border-radius: 12px;
  border: 2px dashed var(--bt-primary);
  background: rgba(99, 102, 241, 0.05);
  color: var(--bt-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
}

.material-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--bt-gray-100);
}

.quantity {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quantity button {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--bt-gray-100);
}

.amount-summary {
  background: var(--bt-gray-50);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.amount-summary .row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}

.amount-summary .total {
  border-top: 2px solid var(--bt-gray-200);
  margin-top: 8px;
  padding-top: 12px;
  font-size: 20px;
  font-weight: 700;
}

.payment-methods {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.method-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-radius: 12px;
  border: 2px solid var(--bt-gray-200);
  background: var(--bt-card-bg);
}

.method-btn.active {
  border-color: var(--bt-primary);
  background: rgba(99, 102, 241, 0.05);
}

.method-btn i {
  font-size: 24px;
}

.btn-confirm {
  width: 100%;
  padding: 16px;
  border-radius: 12px;
  border: none;
  background: var(--bt-success);
  color: white;
  font-size: 18px;
  font-weight: 600;
}
</style>
```

---

## 六、前端架构适配

### 6.1 技术栈调整

| 层级 | 当前 | 新方案 | 理由 |
|------|------|--------|------|
| 构建工具 | Vite 4 | Vite 5 + SWC | 更快编译 |
| UI框架 | Bootstrap 5 | Tailwind CSS + 自定义组件 | 更轻量，按需加载 |
| 状态管理 | Pinia | Pinia + 本地存储同步 | 离线可用 |
| 路由 | Vue Router | Vue Router + 路由预加载 | 更快切换 |
| 图表 | Chart.js | 纯CSS图表 | 减少依赖 |
| 通信 | HTTP轮询 | WebSocket + Server-Sent Events | 实时更新 |

### 6.2 核心组件库（TS）

```typescript
// core/components/ui/index.ts
export { default as BtButton } from './BtButton.vue'
export { default as BtCard } from './BtCard.vue'
export { default as BtInput } from './BtInput.vue'
export { default as BtModal } from './BtModal.vue'
export { default as BtToast } from './BtToast.vue'
export { default as BtSkeleton } from './BtSkeleton.vue'
export { default as BtEmpty } from './BtEmpty.vue'
export { default as BtLoading } from './BtLoading.vue'

// 所有组件支持：
// - 键盘导航
// - 触摸反馈
// - 加载状态
// - 错误状态
// - 暗色模式
```

### 6.3 性能优化策略

```javascript
// vite.config.js
export default defineConfig({
  build: {
    // 代码分割
    rollupOptions: {
      output: {
        manualChunks: {
          'core': ['vue', 'vue-router', 'pinia'],
          'ui': ['@headlessui/vue', '@heroicons/vue'],
          'utils': ['date-fns', 'lodash-es'],
        },
      },
    },
    // 预加载
    modulePreload: {
      polyfill: true,
    },
  },
  
  // 开发优化
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia'],
  },
})
```

---

## 七、快捷键体系

### 7.1 全局快捷键

| 快捷键 | 功能 | 场景 |
|--------|------|------|
| `Cmd/Ctrl + K` | 打开命令面板 | 任何页面 |
| `Cmd/Ctrl + N` | 新建工单 | 任何页面 |
| `Cmd/Ctrl + S` | 快速结算 | 任何页面 |
| `Cmd/Ctrl + F` | 搜索 | 任何页面 |
| `Cmd/Ctrl + T` | 今日视图 | 任何页面 |
| `Cmd/Ctrl + R` | 刷新数据 | 任何页面 |
| `Esc` | 关闭面板/取消 | 任何页面 |
| `?` | 显示快捷键帮助 | 任何页面 |

### 7.2 列表快捷键

| 快捷键 | 功能 |
|--------|------|
| `↑/↓` | 选择上下项 |
| `Enter` | 打开选中项 |
| `E` | 编辑选中项 |
| `D` | 删除选中项 |
| `Space` | 标记/取消标记 |

---

## 八、离线优先设计

### 8.1 数据同步策略（TS）

```typescript
// core/stores/sync.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface SyncState {
  isOnline: boolean
  lastSync: Date | null
  pendingChanges: SyncChange[]
}

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
  const pendingCount = computed(() => pendingChanges.value.length)
  
  async function sync() {
    if (!isOnline.value) return
    
    // 上传本地变更
    for (const change of pendingChanges.value) {
      await applyChange(change)
    }
    
    // 下载服务器变更
    const serverChanges = await getServerChanges(lastSync.value)
    await applyServerChanges(serverChanges)
    
    lastSync.value = new Date()
    pendingChanges.value = []
    saveToLocalStorage()
  }
  
  function queueChange(change: Omit<SyncChange, 'id' | 'timestamp'>) {
    const fullChange: SyncChange = {
      ...change,
      id: generateId(),
      timestamp: new Date()
    }
    pendingChanges.value.push(fullChange)
    saveToLocalStorage()
  }
  
  function saveToLocalStorage() {
    localStorage.setItem('pendingChanges', JSON.stringify(pendingChanges.value))
  }
  
  async function applyChange(change: SyncChange) {
    // 应用变更到服务器
  }
  
  async function getServerChanges(since: Date | null): Promise<SyncChange[]> {
    // 获取服务器变更
    return []
  }
  
  async function applyServerChanges(changes: SyncChange[]) {
    // 应用服务器变更到本地
  }
  
  function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }
  
  // 监听网络状态
  window.addEventListener('online', () => {
    isOnline.value = true
    sync()
  })
  
  window.addEventListener('offline', () => {
    isOnline.value = false
  })
  
  return {
    isOnline,
    lastSync,
    pendingChanges,
    hasPendingChanges,
    pendingCount,
    sync,
    queueChange
  }
})
```

### 8.2 本地存储结构（TS）

```typescript
// core/utils/db.ts
import { openDB, DBSchema, IDBPDatabase } from 'idb'

interface BotongDB extends DBSchema {
  tickets: {
    key: number
    value: import('@/core/types').Ticket
    indexes: { 'by-status': string; 'by-client': number }
  }
  clients: {
    key: number
    value: import('@/core/types').Client
    indexes: { 'by-name': string }
  }
  materials: {
    key: number
    value: import('@/core/types').Goods
    indexes: { 'by-category': string }
  }
  syncQueue: {
    key: string
    value: import('@/core/stores/sync').SyncChange
    indexes: { 'by-timestamp': Date }
  }
}

let db: IDBPDatabase<BotongDB> | null = null

export async function initDB(): Promise<IDBPDatabase<BotongDB>> {
  if (db) return db
  
  db = await openDB<BotongDB>('botong-ticket', 1, {
    upgrade(db) {
      // 工单表
      const ticketStore = db.createObjectStore('tickets', { keyPath: 'id' })
      ticketStore.createIndex('by-status', 'status')
      ticketStore.createIndex('by-client', 'client_id')
      
      // 客户表
      const clientStore = db.createObjectStore('clients', { keyPath: 'id' })
      clientStore.createIndex('by-name', 'name')
      
      // 材料表
      const materialStore = db.createObjectStore('materials', { keyPath: 'id' })
      materialStore.createIndex('by-category', 'category')
      
      // 同步队列表
      const syncStore = db.createObjectStore('syncQueue', { keyPath: 'id' })
      syncStore.createIndex('by-timestamp', 'timestamp')
    }
  })
  
  return db
}

export async function getTicketsByStatus(status: string): Promise<import('@/core/types').Ticket[]> {
  const db = await initDB()
  return db.getAllFromIndex('tickets', 'by-status', status)
}

export async function saveTicket(ticket: import('@/core/types').Ticket): Promise<void> {
  const db = await initDB()
  await db.put('tickets', ticket)
}
```

---

## 九、实施路线图

| 阶段 | 时间 | 内容 | 目标 | TS策略 |
|------|------|------|------|--------|
| **P0** | 第1周 | 命令面板 + 快捷键 | 操作效率提升50% | core/api + types TS化 |
| **P0** | 第2周 | 今日视图重构 | 信息获取时间 < 5秒 | stores TS化 |
| **P1** | 第3周 | 工单列表双栏 | 减少页面跳转 | composables TS化 |
| **P1** | 第4周 | 移动端快速创建 | 3秒创建工单 | 移动端 JS + JSDoc |
| **P1** | 第5周 | 移动端一键结算 | 现场结算 < 1分钟 | 移动端 JS + JSDoc |
| **P2** | 第6周 | 离线同步 | 断网可用 | sync store TS化 |
| **P2** | 第7周 | 主题系统 | 自动暗色模式 | utils TS化 |
| **P2** | 第8周 | 性能优化 | 首屏 < 1秒 | 构建优化 |

---

## 十、预期效果

| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 创建工单时间 | 30秒 | 3秒 | **10x** |
| 查找工单时间 | 15秒 | 2秒 | **7.5x** |
| 结算时间 | 3分钟 | 30秒 | **6x** |
| 每日操作次数 | 20次 | 50次 | **2.5x** |
| 首屏加载 | 3秒 | 1秒 | **3x** |
| 类型安全 | 10% | 80% | **8x** |
| IDE智能提示 | 40% | 90% | **2.25x** |
| 离线可用性 | 无 | 完全支持 | **∞** |

---

## 十一、TS迁移策略总结

### 11.1 分层策略

| 层级 | 语言 | 类型覆盖 | 理由 |
|------|------|----------|------|
| **core/api/** | TypeScript | 100% | API类型安全，统一响应格式 |
| **core/stores/** | TypeScript | 100% | 状态管理类型安全 |
| **core/composables/** | TypeScript | 100% | 通用逻辑复用 |
| **core/types/** | TypeScript | 100% | 类型定义核心资产 |
| **core/utils/** | TypeScript | 100% | 工具函数类型安全 |
| **modules/*/api.ts** | TypeScript | 100% | 模块API类型安全 |
| **modules/*/views/** | JavaScript + JSDoc | 60% | 开发快，维护成本低 |
| **modules/*/components/** | JavaScript + JSDoc | 60% | 灵活，不增加负担 |
| **mobile/** | JavaScript + JSDoc | 50% | 快速迭代，移动端优先功能 |

### 11.2 渐进迁移原则

1. **新功能优先TS**：所有新功能、新模块使用TypeScript
2. **核心层先TS**：API、状态、类型定义优先TS化
3. **业务层JS+JSDoc**：views、components保持JS，添加JSDoc类型注释
4. **修改时顺手迁移**：修改旧文件时，顺手添加类型或迁移到TS
5. **不强制全面迁移**：避免大规模重构，保持开发效率

### 11.3 工具配置

```json
// .vscode/settings.json
{
  "typescript.preferences.includePackageJsonAutoImports": "on",
  "javascript.preferences.includePackageJsonAutoImports": "on",
  "jsdoc.enable": true,
  "jsdoc.checkTypes": true,
  "editor.quickSuggestions": {
    "other": true,
    "comments": true,
    "strings": true
  }
}
```

---

> **决策点**：是否采用此融合TS策略的UI设计方案？
> 
> 如果确认，我将开始编写详细的实施计划，包括：
> 1. core/api TS化实现
> 2. 命令面板组件实现
> 3. 今日视图重构
> 4. 移动端快速创建页面
> 5. 快捷键系统
> 6. 离线同步机制
