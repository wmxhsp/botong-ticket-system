---
title: typescript-migration-guide
priority: medium
tags: [typescript, migration, type-safety]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
---

## 简介
JavaScript到TypeScript渐进式迁移指南，通过分阶段迁移策略，提升代码类型安全性和开发效率。

## 适用场景
- 将现有JS文件迁移到TS
- 为新代码建立TypeScript规范
- 配置vue-tsc和ESLint规则
- 解决常见类型错误

## 迁移优先级

### 阶段1: API客户端层（最高优先级）
**原因**: 
- API层是前后端数据交互的边界，类型定义至关重要
- 迁移收益最大，可立即享受IDE智能提示
- 相对独立，不依赖其他模块

**目标文件**:
- `frontend/src/api/client.js` → `.ts`
- `frontend/src/modules/ticket/api.js` → `.ts`
- `frontend/src/modules/client/api.js` → `.ts`

---

### 阶段2: 组合式函数（高优先级）
**原因**:
- Composables被多个组件复用，类型安全影响面广
- 已有部分TS版本，需统一规范

**目标文件**:
- `frontend/src/core/composables/useDebounce.ts`（已是TS，需完善类型）
- `frontend/src/core/composables/useKeyboardShortcuts.ts`
- `frontend/src/core/composables/useCommandPalette.ts`

---

### 阶段3: 状态管理（中优先级）
**原因**:
- Pinia Store涉及全局状态，类型错误影响范围大
- 已有sync.ts等TS文件，需保持一致性

**目标文件**:
- `frontend/src/core/stores/sync.ts`（已是TS，需完善）
- `frontend/src/stores/auth.js` → `.ts`
- `frontend/src/stores/app.js` → `.ts`

---

### 阶段4: 视图组件（低优先级）
**原因**:
- Vue组件数量多，迁移工作量大
- 可保持`.vue`文件使用`<script>`而非`<script lang="ts">`，通过JSDoc提供类型提示

**策略**: 
- 新组件强制使用TS
- 旧组件重构时逐步迁移
- 核心业务组件优先（QuickTicket、QuickSettle、Tickets）

---

## 类型定义规范

### 1. Request/Response Schema定义

**位置**: `frontend/src/core/types/api.ts`

```typescript
// 通用API响应格式
export interface ApiResponse<T = any> {
  code: number
  data: T
  message?: string
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// 工单列表项（精简版）
export interface TicketListItem {
  id: number
  ticket_no: string
  client: string
  status: 'open' | 'in_progress' | 'completed' | 'cancelled'
  total: number
  created_at: string
  priority: 'L' | 'M' | 'H' | 'U'
  billing_status: 'unpaid' | 'paid'
}

// 工单详情（完整版）
export interface TicketDetail extends TicketListItem {
  description: string
  phone?: string
  address?: string
  scheduled_at?: string
  completed_at?: string
  technician_id?: number
  billing_type: 'hourly' | 'daily' | 'package'
  rate?: number
  hours?: number
  materials: MaterialItem[]
  service_items: ServiceItem[]
  photos: PhotoItem[]
}

// 材料项
export interface MaterialItem {
  id: number
  goods_id: number
  goods_name: string
  quantity: number
  unit_price: number
  total: number
}

// 服务项
export interface ServiceItem {
  id: number
  hours: number
  rate: number
  billing_type: string
  technician_id?: number
  technician_name?: string
  total: number
}

// 照片项
export interface PhotoItem {
  id: number
  url: string
  thumbnail_url?: string
  caption?: string
  created_at: string
}

// 创建工单请求
export interface CreateTicketRequest {
  client: string
  phone?: string
  description: string
  priority?: 'L' | 'M' | 'H' | 'U'
  billing_type?: 'hourly' | 'daily' | 'package'
  rate?: number
  scheduled_at?: string
}

// 结算工单请求
export interface SettleTicketRequest {
  hours: number
  rate: number
  billing_type: 'hourly' | 'daily' | 'package'
  technician_id?: number
  materials?: Array<{
    goods_id: number
    quantity: number
    unit_price: number
  }>
  payment_method: 'cash' | 'wechat' | 'alipay' | 'bank_transfer'
  notes?: string
}

// 列表查询参数
export interface ListParams {
  page?: number
  page_size?: number
  keyword?: string
  status?: string
  client?: string
  fields?: string
}
```

---

### 2. API客户端类型化

**位置**: `frontend/src/core/api/client.ts`

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios'
import type { ApiResponse } from '@/core/types/api'

// 创建Axios实例
const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data as ApiResponse,
  (error: AxiosError) => {
    const message = error.response?.data?.message || error.message
    return Promise.reject(new Error(message))
  }
)

export default api
```

---

### 3. 工单API类型化

**位置**: `frontend/src/modules/ticket/api.ts`

```typescript
import api from '@/core/api/client'
import type { 
  TicketListItem, 
  TicketDetail, 
  CreateTicketRequest, 
  SettleTicketRequest,
  PaginatedResponse,
  ListParams 
} from '@/core/types/api'

export const ticketApi = {
  // 列表查询
  list(params: ListParams): Promise<PaginatedResponse<TicketListItem>> {
    return api.get('/tickets', { params })
  },
  
  // 获取详情
  get(id: number): Promise<TicketDetail> {
    return api.get(`/tickets/${id}`)
  },
  
  // 创建工单
  create(data: CreateTicketRequest): Promise<{ id: number }> {
    return api.post('/tickets', data)
  },
  
  // 结算工单
  settle(id: number, data: SettleTicketRequest): Promise<void> {
    return api.post(`/tickets/${id}/settle`, data)
  },
  
  // 删除工单
  delete(id: number): Promise<void> {
    return api.delete(`/tickets/${id}`)
  },
  
  // 更新状态
  updateStatus(id: number, status: string): Promise<void> {
    return api.patch(`/tickets/${id}/status`, { status })
  }
}
```

---

## vue-tsc配置和ESLint规则

### 1. tsconfig.json配置

**位置**: `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    
    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    
    /* Linting - 严格模式 */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    
    /* Path aliases */
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

### 2. ESLint规则配置

**位置**: `frontend/.eslintrc.json`

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:vue/vue3-recommended"
  ],
  "parser": "vue-eslint-parser",
  "parserOptions": {
    "parser": "@typescript-eslint/parser"
  },
  "plugins": ["@typescript-eslint"],
  "rules": {
    // 强制core/目录使用TS
    "@typescript-eslint/no-var-requires": "off",
    
    // 禁止any类型（除非必要）
    "@typescript-eslint/no-explicit-any": "warn",
    
    // 允许未使用的变量（以_开头）
    "@typescript-eslint/no-unused-vars": ["warn", { 
      "argsIgnorePattern": "^_",
      "varsIgnorePattern": "^_"
    }],
    
    // Vue特定规则
    "vue/multi-word-component-names": "off",
    "vue/no-v-html": "off"
  },
  "overrides": [
    {
      "files": ["src/core/**/*.{ts,tsx}"],
      "rules": {
        "@typescript-eslint/no-explicit-any": "error"
      }
    }
  ]
}
```

---

### 3. package.json脚本

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "type-check": "vue-tsc --noEmit",
    "lint": "eslint src --ext .js,.ts,.vue",
    "lint:fix": "eslint src --ext .js,.ts,.vue --fix"
  }
}
```

---

## 常见类型错误及解决方案

### 错误1: Implicit any type

**错误信息**:
```
Parameter 'item' implicitly has an 'any' type.
```

**原因**: 函数参数未声明类型

**修复**:
```typescript
// ❌ 错误
const tickets = data.items.map(item => ({
  ...item,
  formatted_date: formatDate(item.created_at)
}))

// ✅ 正确
const tickets = data.items.map((item: TicketListItem) => ({
  ...item,
  formatted_date: formatDate(item.created_at)
}))
```

---

### 错误2: Property does not exist on type

**错误信息**:
```
Property 'phone' does not exist on type 'TicketListItem'.
```

**原因**: 访问了类型定义中不存在的属性

**修复方案A**: 扩展类型定义
```typescript
export interface TicketListItem {
  // ... 现有字段
  phone?: string  // 添加缺失字段
}
```

**修复方案B**: 使用类型断言（谨慎使用）
```typescript
const phone = (ticket as any).phone
```

**修复方案C**: 使用可选链
```typescript
const phone = (ticket as TicketDetail).phone
```

---

### 错误3: Type is not assignable

**错误信息**:
```
Type 'string' is not assignable to type '"open" | "in_progress" | "completed"'.
```

**原因**: 字符串字面量类型不匹配

**修复**:
```typescript
// ❌ 错误
const status: 'open' | 'in_progress' | 'completed' = someVariable

// ✅ 正确（使用类型守卫）
if (['open', 'in_progress', 'completed'].includes(someVariable)) {
  const status = someVariable as 'open' | 'in_progress' | 'completed'
}
```

---

### 错误4: Module has no default export

**错误信息**:
```
Module 'xxx' has no default export.
```

**原因**: 导入方式与导出方式不匹配

**修复**:
```typescript
// 如果模块使用 named export
export const ticketApi = { ... }

// 则应使用 named import
import { ticketApi } from './api'  // ✅

// 而非 default import
import ticketApi from './api'  // ❌
```

---

### 错误5: Object is possibly null/undefined

**错误信息**:
```
Object is possibly 'null'.
```

**原因**: 未处理可能为null的值

**修复**:
```typescript
// ❌ 错误
const name = ticket.client.name

// ✅ 正确（可选链）
const name = ticket.client?.name

// ✅ 正确（空值合并）
const name = ticket.client?.name ?? '未知客户'

// ✅ 正确（类型守卫）
if (ticket.client) {
  const name = ticket.client.name
}
```

---

## 迁移工作流程

### 1. 单个文件迁移步骤

**Step 1**: 重命名文件
```bash
mv frontend/src/api/client.js frontend/src/api/client.ts
```

**Step 2**: 添加类型注解
```typescript
// 为所有函数参数和返回值添加类型
export function createClient(data: CreateClientRequest): Promise<Client> {
  // ...
}
```

**Step 3**: 运行类型检查
```bash
npm run type-check
```

**Step 4**: 修复类型错误
- 根据错误提示逐个修复
- 必要时扩展类型定义

**Step 5**: 提交代码
```bash
git add frontend/src/api/client.ts
git commit -m "refactor: migrate client.js to TypeScript"
```

---

### 2. 批量迁移策略

**工具**: 使用`jscodeshift`自动化工具

**安装**:
```bash
npm install -g jscodeshift
```

**示例转换**: 自动添加`any`类型占位
```bash
jscodeshift -t transform.js src/**/*.js
```

**transform.js**:
```javascript
module.exports = function transformer(fileInfo, api) {
  const j = api.jscodeshift
  
  return j(fileInfo.source)
    .find(j.FunctionDeclaration)
    .forEach(path => {
      // 为无类型的参数添加any
      path.node.params.forEach(param => {
        if (!param.typeAnnotation) {
          param.typeAnnotation = j.tsTypeAnnotation(j.tsAnyKeyword())
        }
      })
    })
    .toSource()
}
```

---

## 验收标准

### 代码质量
- [ ] core/目录下无.js文件
- [ ] vue-tsc --noEmit无错误
- [ ] ESLint无警告（除允许的any外）
- [ ] 所有API调用都有明确的Request/Response类型

### 开发体验
- [ ] IDE智能提示完整（函数参数、返回值、对象属性）
- [ ] 跳转定义功能正常
- [ ] 重构时类型检查捕获所有引用点

### 编译性能
- [ ] vue-tsc --noEmit耗时 < 10秒
- [ ] npm run build包含类型检查步骤
- [ ] 增量编译耗时 < 3秒

---

## 常见问题

### Q1: 如何处理第三方库缺少类型定义？
**A**: 
```bash
# 安装@types包
npm install --save-dev @types/lodash

# 如果没有@types包，创建声明文件
// src/types/third-party.d.ts
declare module 'some-library' {
  export function doSomething(): void
}
```

### Q2: 是否应该禁止所有any类型？
**A**: 
- core/目录：禁止any（除非绝对必要）
- 业务层：允许any，但需添加注释说明原因
- 使用`unknown`替代any更安全

### Q3: 如何处理动态对象属性？
**A**: 
```typescript
// 使用索引签名
interface DynamicObject {
  [key: string]: any
}

// 或使用Record
type DynamicObject = Record<string, any>
```

### Q4: Vue组件如何迁移到TS？
**A**: 
```vue
<script setup lang="ts">
import { ref } from 'vue'

// 明确声明类型
const count = ref<number>(0)
const name = ref<string>('')

// 定义Props类型
interface Props {
  title: string
  count?: number
}
const props = defineProps<Props>()
</script>
```

---

## 维护人
AI Assistant

## 最后更新
2026-05-31

## 相关技能
- ticket-system-optimization
- frontend-best-practices
- composable-best-practices
