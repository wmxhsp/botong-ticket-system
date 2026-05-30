---
title: frontend-best-practices
priority: high
tags: [frontend, vue, vite, router, composition-api]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
last_updated: 2026-05-31
related_skills: [vue-frontend-optimization, state-management-patterns, typescript-migration-guide]
---

## 简介
前端开发完整最佳实践指南：涵盖 Vue 3 Composition API、Vite 构建优化、Vue Router 路由规范、组件设计与性能优化。

## 适用场景
- 新页面/组件开发
- 状态管理与复用逻辑设计
- 路由配置与权限控制
- 构建优化与性能调优
- TypeScript 迁移

## 一、Vue 3 Composition API 规范

### 1.1 组件设计原则

**核心要求**:
- 使用 `<script setup>` 语法糖
- 响应式数据优先使用 `ref()`（简单类型）和 `reactive()`（对象）
- 复杂逻辑抽取为 Composable（存放于 `frontend/src/core/composables/`）
- Props 定义使用 `defineProps`，事件使用 `defineEmits`
- 组件命名采用 PascalCase，文件名采用 PascalCase.vue
- 模板中避免复杂表达式，抽取为 computed 或方法

**示例**:
```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

// Props 定义
interface Props {
  title: string
  count?: number
}
const props = withDefaults(defineProps<Props>(), {
  count: 0
})

// Emits 定义
const emit = defineEmits<{
  update: [value: number]
  close: []
}>()

// 响应式数据
const localCount = ref(props.count)

// 计算属性
const doubled = computed(() => localCount.value * 2)

// 方法
function handleUpdate() {
  emit('update', localCount.value)
}
</script>

<template>
  <div class="component-name">
    <h2>{{ title }}</h2>
    <p>Count: {{ localCount }}, Doubled: {{ doubled }}</p>
    <button @click="handleUpdate">Update</button>
  </div>
</template>
```

### 1.2 Composables 设计规范

**何时抽取 Composable**:
- 逻辑超过 50 行
- 需要在多个组件中复用
- 涉及副作用（API调用、localStorage等）

**命名规范**: `useXxx.ts`，如 `useDebounce.ts`、`useKeyboardShortcuts.ts`

**示例**:
```typescript
// frontend/src/core/composables/useDebounce.ts
import { ref, watch } from 'vue'

export function useDebounce<T>(value: Ref<T>, delay = 300): Ref<T> {
  const debouncedValue = ref(value.value)
  let timer: ReturnType<typeof setTimeout>
  
  watch(value, (newVal) => {
    clearTimeout(timer)
    timer = setTimeout(() => {
      debouncedValue.value = newVal
    }, delay)
  })
  
  return debouncedValue
}
```

---

## 二、Vite 构建优化

### 2.1 Chunk 分割策略

**配置位置**: `frontend/vite.config.js`

**核心原则**:
- 第三方库拆分为独立 chunk（element-plus、chart.js、axios等）
- 路由级代码分割（每个页面一个 chunk）
- 单 chunk 不超过 500KB

**配置示例**:
```javascript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-vue': ['vue', 'vue-router', 'pinia'],
          'vendor-ui': ['element-plus'],
          'vendor-chart': ['chart.js'],
          'vendor-utils': ['axios', 'dayjs', 'lodash-es']
        }
      }
    }
  }
})
```

### 2.2 环境变量管理

**规则**:
- 环境变量使用 `VITE_` 前缀
- 通过 `import.meta.env.VITE_XXX` 访问
- 敏感信息（API密钥）不要提交到版本控制

**示例**:
```javascript
// .env.development
VITE_API_BASE_URL=http://localhost:5053/api/v1
VITE_APP_NAME=Botong Ticket System

// 在代码中使用
const apiBase = import.meta.env.VITE_API_BASE_URL
```

### 2.3 开发代理配置

**解决跨域问题**:
```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5053',
        changeOrigin: true
      }
    }
  }
})
```

---

## 三、Vue Router 路由规范

### 3.1 路由配置原则

**核心要求**:
- 页面组件使用动态 import 实现懒加载
- 路由元信息 `meta` 字段用于权限标记
- 导航守卫 `beforeEach` 统一处理认证逻辑
- 路由命名采用 kebab-case，路径采用 kebab-case
- 嵌套路由使用 `children` 配置

**配置示例**:
```typescript
// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/tickets',
    name: 'tickets-list',
    component: () => import('@/modules/ticket/views/Tickets.vue'),
    meta: { requiresAuth: true, title: '工单列表' }
  },
  {
    path: '/tickets/quick',
    name: 'ticket-quick-create',
    component: () => import('@/modules/ticket/views/QuickTicket.vue'),
    meta: { requiresAuth: true, title: '快速创建工单' }
  },
  {
    path: '/tickets/:id/settle',
    name: 'ticket-settle',
    component: () => import('@/modules/ticket/views/QuickSettle.vue'),
    meta: { requiresAuth: true, title: '工单结算' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局导航守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

### 3.2 路由懒加载最佳实践

**标准写法**:
```typescript
// ✅ 推荐：命名 chunk
component: () => import(/* webpackChunkName: "tickets" */ '@/views/Tickets.vue')

// ✅ 也可接受：匿名 chunk
component: () => import('@/views/Tickets.vue')

// ❌ 不推荐：同步导入
component: TicketsView
```

---

## 四、状态管理（Pinia）

### 4.1 Store 设计规范

**核心原则**:
- 每个业务域一个 Store（`useTicketsStore`, `useAuthStore`）
- Actions 负责副作用（API调用）
- Getters 用于计算派生状态
- 持久化敏感数据时加密或限制为 sessionStorage

**示例**:
```typescript
// frontend/src/stores/tickets.ts
import { defineStore } from 'pinia'
import { ticketApi } from '@/modules/ticket/api'
import type { TicketListItem } from '@/core/types/api'

export const useTicketsStore = defineStore('tickets', {
  state: () => ({
    tickets: [] as TicketListItem[],
    loading: false,
    total: 0
  }),
  
  getters: {
    openTickets: (state) => state.tickets.filter(t => t.status === 'open'),
    hasTickets: (state) => state.tickets.length > 0
  },
  
  actions: {
    async fetchTickets(params: ListParams) {
      this.loading = true
      try {
        const response = await ticketApi.list(params)
        this.tickets = response.items
        this.total = response.total
      } finally {
        this.loading = false
      }
    }
  }
})
```

---

## 五、测试与质量

### 5.1 单元测试

**工具**: Vitest + Testing Library

**测试范围**:
- Composables（纯逻辑）
- Store Actions（API调用Mock）
- 工具函数

**示例**:
```typescript
// tests/unit/useDebounce.test.ts
import { describe, it, expect } from 'vitest'
import { useDebounce } from '@/core/composables/useDebounce'

describe('useDebounce', () => {
  it('should debounce value changes', async () => {
    // 测试逻辑
  })
})
```

### 5.2 代码质量工具

**ESLint + Prettier**: 提交前必跑项

**配置**:
```json
{
  "scripts": {
    "lint": "eslint src --ext .js,.ts,.vue",
    "lint:fix": "eslint src --ext .js,.ts,.vue --fix",
    "type-check": "vue-tsc --noEmit"
  }
}
```

---

## 六、性能优化要点

### 6.1 组件级优化

- **v-if vs v-show**: 频繁切换用 `v-show`，条件渲染用 `v-if`
- **computed 缓存**: 避免模板中复杂表达式
- **key 优化**: `v-for` 使用唯一 key（避免使用 index）
- **图片懒加载**: 使用 `loading="lazy"` 或 IntersectionObserver

### 6.2 路由级优化

- **路由懒加载**: 所有页面组件都使用动态 import
- **预加载**: 用户可能访问的下一个页面使用 `<link rel="prefetch">`

### 6.3 构建级优化

- **按需导入**: Element Plus、Chart.js 等库按需导入
- **Tree Shaking**: 确保使用 ES Module 版本的依赖
- **代码压缩**: 生产环境启用 minify 和 gzip

---

## 验收标准

### 组件开发
- [ ] 新组件使用 `<script setup>` + Composition API
- [ ] 组件 Props 有类型定义和默认值
- [ ] 逻辑超过 50 行已抽取为 Composable
- [ ] 组件文件采用 PascalCase 命名

### 路由配置
- [ ] 新增路由有 `name` 和 `meta` 字段
- [ ] 需认证的页面设置 `meta.requiresAuth = true`
- [ ] 页面组件使用懒加载

### 构建优化
- [ ] `npm run build` 无错误完成
- [ ] 产出 chunk 大小合理（单 chunk < 500KB）
- [ ] 第三方库拆分为独立 chunk
- [ ] 开发环境 API 代理正常工作

### 代码质量
- [ ] ESLint 无警告
- [ ] TypeScript 类型检查通过
- [ ] 单元测试覆盖率 > 70%

---

## 常见问题

### Q1: 何时使用 ref 而非 reactive？
**A**: 
- `ref`: 简单类型（number、string、boolean）或需要替换整个对象
- `reactive`: 复杂对象且不需要替换引用

### Q2: 如何处理大型表单的状态管理？
**A**: 
- 小表单：组件内部 ref + reactive
- 大表单：Pinia Store，支持跨页面共享

### Q3: 路由懒加载导致首屏闪烁怎么办？
**A**: 
- 使用骨架屏占位
- 预加载关键路由：`router.push({ path: '/important', replace: true })`

### Q4: Vite 构建产物过大如何优化？
**A**: 
- 运行 `npm run build -- --report` 分析 bundle
- 检查是否有重复依赖
- 使用 `manualChunks` 拆分大型库

---

## 相关技能
- **vue-frontend-optimization**: 专注性能优化高级主题（虚拟滚动、Bundle分析）
- **state-management-patterns**: Pinia、Composables、事务模式详细指南
- **typescript-migration-guide**: JavaScript 到 TypeScript 迁移步骤

## 维护人
AI Assistant

## 最后更新
2026-05-31
