# 博通工单系统 — 前端架构 v5.0 设计文档

> 目标：打造适合1人公司的极致效率工具
> 核心原则：**极简、快速、离线优先**

---

## 一、当前架构分析

### 1.1 现有结构

```
frontend/src/
├── modules/           # 16个业务模块
│   ├── ticket/        # 工单（views/, api/, routes.js, index.js）
│   ├── client/        # 客户
│   ├── finance/       # 财务
│   └── ...
├── views/             # 22个页面（与modules/views重复）
├── components/        # 公共组件
│   ├── common/        # 通用（Modal, Toast, Loading）
│   ├── layout/        # 布局（AppLayout, Sidebar, TopBar）
│   └── tickets/       # 工单专用组件
├── api/               # API封装
│   ├── client.ts      # Axios实例
│   ├── tickets.js     # 工单API
│   └── schemas.js     # Zod验证
├── stores/            # Pinia状态
│   ├── auth.ts        # 认证
│   └── app.ts         # 应用状态
├── composables/       # 组合式函数
├── router/            # 路由
└── main.js            # 入口
```

### 1.2 存在的问题

| 问题 | 影响 | 优先级 |
|------|------|--------|
| **views/ 与 modules/views/ 重复** | 代码分散，维护困难 | 🔴 高 |
| **API 与模块分离** | 修改模块需改两处 | 🔴 高 |
| **缺少类型系统** | JS/TS 混用，类型不一致 | 🟡 中 |
| **组件职责不清** | views/ 和 components/ 边界模糊 | 🟡 中 |
| **缺少移动端适配** | 手机使用体验差 | 🔴 高 |
| **构建产物未优化** | 首屏加载慢 | 🟡 中 |

---

## 二、新架构设计

### 2.1 核心变化

```
frontend/src/
├── core/                    # 核心基础设施（全局唯一）
│   ├── router/              # 路由配置
│   ├── store/               # 全局状态（Pinia）
│   ├── api/                 # API客户端 + 拦截器
│   ├── components/          # 全局公共组件
│   │   ├── layout/          # 布局组件
│   │   ├── ui/              # UI基础组件（Button, Input, Modal）
│   │   └── data/            # 数据展示（Table, Card, Chart）
│   ├── composables/         # 全局组合式函数
│   ├── utils/               # 工具函数
│   └── styles/              # 全局样式 + CSS变量
│
├── modules/                 # 业务模块（自治单元）
│   ├── ticket/
│   │   ├── index.ts         # 模块入口：导出 routes, nav, api, features
│   │   ├── routes.ts        # 路由定义
│   │   ├── api.ts           # 模块API（从core/api扩展）
│   │   ├── stores/          # 模块状态（Pinia）
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 模块专用组件
│   │   └── composables/     # 模块组合式函数
│   ├── client/
│   └── ...
│
├── mobile/                  # 移动端专用页面
│   ├── views/               # 快速创建、一键结算
│   └── composables/         # 移动端专用逻辑
│
└── main.ts                  # 入口（自动注册模块）
```

### 2.2 模块自治规范

每个模块必须是一个**自包含的单元**：

```typescript
// modules/ticket/index.ts
import routes from './routes'
import * as api from './api'

export default {
  name: 'ticket',
  routes,
  api,
  
  nav: {
    title: '工单管理',
    icon: 'bi-ticket-perforated',
    path: '/tickets',
    order: 10,
    group: '业务',
  },
  
  features: [
    { name: 'list', endpoint: 'GET /tickets/', status: 'done' },
    { name: 'create', endpoint: 'POST /tickets/', status: 'done' },
  ]
}
```

**模块内部结构**：
```
modules/ticket/
├── index.ts           # 入口
├── routes.ts          # 路由
├── api.ts             # API（模块级别）
├── stores/
│   └── ticketStore.ts # 模块状态
├── views/
│   ├── TicketList.vue
│   ├── TicketDetail.vue
│   └── TicketCreate.vue
├── components/
│   ├── TicketCard.vue
│   ├── TicketFilter.vue
│   └── TicketTimeline.vue
└── composables/
    ├── useTicketList.ts
    └── useTicketForm.ts
```

### 2.3 核心层设计

#### API 客户端（core/api/）

```typescript
// core/api/client.ts
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 15000,
})

// 请求拦截器
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('bt_auth_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器
client.interceptors.response.use(
  (response) => response.data,  // 直接返回 data
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client
```

#### 全局状态（core/store/）

```typescript
// core/store/auth.ts
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
  }),
  
  actions: {
    async login(credentials) {
      const { token, user } = await api.auth.login(credentials)
      localStorage.setItem('bt_auth_token', token)
      this.user = user
      this.isAuthenticated = true
    },
    
    logout() {
      localStorage.removeItem('bt_auth_token')
      this.user = null
      this.isAuthenticated = false
    }
  }
})
```

### 2.4 移动端优化

#### 快速创建页面

```vue
<!-- mobile/views/QuickTicket.vue -->
<template>
  <div class="mobile-page">
    <!-- 顶部：客户快捷选择 -->
    <section class="recent-clients">
      <h3>最近客户</h3>
      <div class="client-chips">
        <button 
          v-for="client in recentClients" 
          :key="client.id"
          @click="selectClient(client)"
          :class="{ active: form.client === client.name }"
        >
          {{ client.name }}
        </button>
      </div>
    </section>
    
    <!-- 中部：语音输入 -->
    <section class="voice-input" @touchstart="startVoice" @touchend="stopVoice">
      <i class="bi bi-mic"></i>
      <span>{{ isRecording ? '录音中...' : '按住说话' }}</span>
    </section>
    
    <!-- 底部：快速创建 -->
    <button class="btn-primary" @click="createTicket" :disabled="!form.client">
      创建工单
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTicketStore } from '@/modules/ticket/stores/ticketStore'

const router = useRouter()
const ticketStore = useTicketStore()

const recentClients = ref([])
const form = ref({ client: '', content: '' })
const isRecording = ref(false)

async function createTicket() {
  const ticket = await ticketStore.create(form.value)
  router.push(`/tickets/${ticket.id}`)
}
</script>

<style scoped>
.mobile-page {
  padding: 16px;
  max-width: 100vw;
}

.recent-clients {
  margin-bottom: 24px;
}

.client-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.client-chips button {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid #ddd;
  background: white;
}

.client-chips button.active {
  background: #007bff;
  color: white;
}

.voice-input {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  border: 2px dashed #ddd;
  border-radius: 16px;
  margin-bottom: 24px;
}

.voice-input i {
  font-size: 48px;
  color: #007bff;
}
</style>
```

### 2.5 构建优化

```javascript
// vite.config.js
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // 核心框架
          'core': ['vue', 'vue-router', 'pinia'],
          // UI库
          'ui': ['bootstrap'],
          // 图表
          'chart': ['chart.js', 'vue-echarts'],
          // 工具
          'utils': ['axios', 'date-fns', 'lodash-es'],
        },
      },
    },
    // 代码分割
    cssCodeSplit: true,
    sourcemap: 'hidden',
    chunkSizeWarningLimit: 500,
  },
  
  // 预加载关键模块
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios'],
  },
})
```

---

## 三、迁移策略

### 3.1 渐进式迁移

```
Phase 1: 核心层搭建（1周）
  - 创建 core/ 目录
  - 迁移 API 客户端
  - 迁移全局组件
  
Phase 2: 模块迁移（2周）
  - 逐个迁移业务模块
  - 保持旧代码可用
  
Phase 3: 移动端开发（1周）
  - 创建 mobile/ 目录
  - 实现快速创建、一键结算
  
Phase 4: 清理旧代码（1天）
  - 删除 views/ 旧目录
  - 统一入口
```

### 3.2 兼容性处理

```typescript
// main.ts
import { createApp } from 'vue'
import router from './core/router'
import { registerModules } from './core/utils/module-loader'

// 自动注册所有模块
const modules = import.meta.glob('./modules/*/index.ts', { eager: true })
registerModules(modules)

const app = createApp(App)
app.use(router)
app.mount('#app')
```

---

## 四、性能优化

### 4.1 首屏加载

| 优化项 | 当前 | 目标 |
|--------|------|------|
| 首屏 JS | ~500KB | <200KB |
| 首屏 CSS | ~100KB | <50KB |
| 首屏时间 | ~3s | <1.5s |

### 4.2 具体措施

1. **路由懒加载**：已实现
2. **组件按需加载**：大组件拆分为小组件
3. **图片懒加载**：使用 `loading="lazy"`
4. **缓存策略**：API 响应缓存 5 分钟

---

## 五、1人运营场景优化

### 5.1 核心工作流

```
早上 5分钟
  └─ 打开系统 → 查看今日待办（Dashboard）
        └─ 移动端优先

上门服务
  └─ 手机快速创建工单 → 拍照 → 完工 → 一键结算
        └─ 全程手机操作

晚上 10分钟
  └─ 查看今日统计 → 确认收入
        └─ 利润日报推送
```

### 5.2 关键页面

| 页面 | 设备 | 功能 |
|------|------|------|
| Dashboard | 手机/电脑 | 今日待办、收入概览 |
| QuickTicket | 手机 | 3步创建工单 |
| QuickSettle | 手机 | 一键完工结算 |
| TicketList | 电脑 | 完整工单管理 |
| Stats | 电脑 | 统计分析 |

---

## 六、实施计划

| 阶段 | 时间 | 内容 |
|------|------|------|
| 第1周 | 核心层 | 搭建 core/ 目录，迁移基础设施 |
| 第2周 | 模块迁移 | 迁移 ticket, client 模块 |
| 第3周 | 模块迁移 | 迁移 finance, inventory 模块 |
| 第4周 | 移动端 | 实现 QuickTicket, QuickSettle |
| 第5周 | 测试优化 | 性能测试、Bug修复 |

---

## 七、预期收益

| 指标 | 当前 | 目标 |
|------|------|------|
| 代码维护性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 移动端体验 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 首屏加载 | 3s | 1.5s |
| 开发效率 | 中等 | 提升50% |
| 1人运营适配 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

> **决策点**：是否采用此架构？
> 
> 如果确认，我将开始编写详细的实施计划，包括：
> 1. 核心层代码实现
> 2. 模块迁移步骤
> 3. 移动端页面开发
> 4. 测试验证方案
