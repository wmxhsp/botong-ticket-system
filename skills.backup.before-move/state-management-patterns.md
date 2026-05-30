---
title: state-management-patterns
priority: high
tags: [pinia, composables, state-management, transaction]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
last_updated: 2026-05-31
related_skills: [frontend-best-practices, typescript-migration-guide]
---

## 简介
状态管理完整模式指南：整合 Pinia Store、Composables 组合式函数、事务和工作单元模式，提供前端和后端状态管理的统一最佳实践。

## 适用场景
- 创建新的 Pinia Store 或 Composable
- 跨组件状态共享与同步
- 后端事务边界定义和UnitOfWork使用
- 重构重复逻辑为可复用模块

---

## 一、Pinia 状态管理规范

### 1.1 Store 设计原则

**核心要求**:
- 使用 Composition API 风格定义 Store（`defineStore` + setup 函数）
- Store 按业务域拆分（auth、tickets、app等），避免单一巨型 Store
- 异步操作放在 Actions 中，Getters 保持纯函数
- 敏感状态考虑持久化到 localStorage 或 sessionStorage
- Store 之间可通过 `useXxxStore()` 互相引用，但避免循环依赖

**示例**:
```typescript
// frontend/src/stores/tickets.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ticketApi } from '@/modules/ticket/api'
import type { TicketListItem, ListParams } from '@/core/types/api'

export const useTicketsStore = defineStore('tickets', () => {
  // State
  const tickets = ref<TicketListItem[]>([])
  const loading = ref(false)
  const total = ref(0)
  const filters = ref<ListParams>({})
  
  // Getters
  const openTickets = computed(() => 
    tickets.value.filter(t => t.status === 'open')
  )
  
  const hasTickets = computed(() => tickets.value.length > 0)
  
  // Actions
  async function fetchTickets(params: ListParams) {
    loading.value = true
    try {
      const response = await ticketApi.list(params)
      tickets.value = response.items
      total.value = response.total
      filters.value = params
    } catch (error) {
      console.error('Failed to fetch tickets:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  async function createTicket(data: any) {
    const newTicket = await ticketApi.create(data)
    tickets.value.unshift(newTicket)
    total.value++
  }
  
  function updateTicket(id: number, updates: Partial<TicketListItem>) {
    const index = tickets.value.findIndex(t => t.id === id)
    if (index !== -1) {
      tickets.value[index] = { ...tickets.value[index], ...updates }
    }
  }
  
  return {
    tickets,
    loading,
    total,
    filters,
    openTickets,
    hasTickets,
    fetchTickets,
    createTicket,
    updateTicket
  }
})
```

### 1.2 Store 持久化策略

**规则**:
- 认证信息（token、user）：localStorage（长期保存）
- UI状态（主题、语言）：localStorage
- 临时数据（表单草稿）：sessionStorage
- 业务数据（工单列表）：不持久化，每次刷新重新获取

**实现**:
```typescript
// 在 Store 中使用
import { useStorage } from '@vueuse/core'

const theme = useStorage('theme', 'light')
const authToken = useStorage('auth_token', '')
```

---

## 二、Composables 组合式函数规范

### 2.1 设计原则

**命名规范**: `useXxx.ts`，如 `useDebounce`、`useKeyboardShortcuts`

**何时抽取 Composable**:
- 逻辑超过 50 行
- 需要在多个组件中复用
- 涉及副作用（API调用、localStorage、事件监听等）

**参数设计**:
- 参数使用 `ref()` 或 `reactive()` 包裹，支持响应式传入
- 返回值为 `ref` 或 `computed`
- 解构时保持响应性（使用 `const` 而非 `let`）

**错误处理**:
- 内部 catch + 返回 `error` ref
- 不吞异常，让调用者决定如何处理

**清理副作用**:
- `onUnmounted` 中清理定时器、事件监听、AbortController

### 2.2 标准模板

```typescript
// frontend/src/core/composables/useDebounce.ts
import { ref, watch, onUnmounted } from 'vue'
import type { Ref } from 'vue'

export function useDebounce<T>(value: Ref<T>, delay = 300): Ref<T> {
  const debouncedValue = ref(value.value)
  let timer: ReturnType<typeof setTimeout>
  
  function cleanup() {
    clearTimeout(timer)
  }
  
  watch(value, (newVal) => {
    cleanup()
    timer = setTimeout(() => {
      debouncedValue.value = newVal
    }, delay)
  })
  
  onUnmounted(() => {
    cleanup()
  })
  
  return debouncedValue
}
```

### 2.3 Composable 组合

Composable 之间可以互相调用：

```typescript
// frontend/src/core/composables/useTicketList.ts
import { useApi } from './useApi'
import { useDebounce } from './useDebounce'

export function useTicketList() {
  const { data, loading, error, execute } = useApi()
  const keyword = ref('')
  const debouncedKeyword = useDebounce(keyword, 300)
  
  watch(debouncedKeyword, (newVal) => {
    execute(() => ticketApi.list({ keyword: newVal }))
  })
  
  return {
    tickets: data,
    loading,
    error,
    keyword,
    search: (kw: string) => { keyword.value = kw }
  }
}
```

---

## 三、事务与工作单元模式（后端）

### 3.1 UnitOfWork 模式

**用途**: 确保跨仓储/跨表操作的原子性，避免半提交或不一致状态

**实现位置**: `infrastructure/persistence/database.py::UnitOfWork`

**使用场景**:
- 完工流程：库存扣减 + 财务记录 + 状态变更
- 收款流程：支付记录 + 工单状态更新
- 批量操作：批量删除、批量完工

### 3.2 事务边界定义

**核心原则**:
- 事务应在 Service 层开启，而非 Repository 层
- 一个业务操作对应一个事务边界
- 异常时自动回滚

**示例**:
```python
# application/services/ticket_service.py
from infrastructure.persistence.database import UnitOfWork

class TicketService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    def complete_ticket(self, ticket_id: int, materials: list):
        """
        完工工单：扣减库存 + 更新状态 + 记录财务
        所有操作在一个事务内，要么全部成功，要么全部回滚
        """
        with self.uow:
            # 1. 扣减库存
            for material in materials:
                self.uow.goods.decrease_stock(
                    material['goods_id'], 
                    material['quantity']
                )
            
            # 2. 更新工单状态
            self.uow.tickets.update(ticket_id, {
                'status': 'completed',
                'completed_at': datetime.now()
            })
            
            # 3. 记录财务
            self.uow.payments.create({
                'ticket_id': ticket_id,
                'amount': calculate_total(materials),
                'type': 'revenue'
            })
            
            # 4. 提交事务（with 块结束时自动提交）
            self.uow.commit()
        
        # 如果任何步骤抛出异常，事务会自动回滚
```

### 3.3 异常处理与幂等性

**规则**:
- 捕获具体异常类型，而非通用 Exception
- 记录详细错误日志，便于排查
- 对外部系统调用（如支付网关）实现幂等性

**示例**:
```python
from sqlalchemy.exc import IntegrityError

def create_payment(self, payment_data: dict):
    try:
        with self.uow:
            self.uow.payments.create(payment_data)
            self.uow.commit()
    except IntegrityError as e:
        # 检查是否是重复支付
        if 'UNIQUE constraint failed' in str(e):
            logger.warning(f"Duplicate payment attempt: {payment_data}")
            raise PaymentDuplicateError("支付记录已存在")
        raise
    except Exception as e:
        logger.error(f"Payment creation failed: {e}")
        raise PaymentCreationError("支付创建失败")
```

### 3.4 SQLite 与 Postgres 的锁行为差异

**SQLite**:
- 写操作锁定整个数据库文件
- 并发写入性能较差
- 适合读多写少场景

**Postgres**:
- 行级锁，支持高并发写入
- MVCC（多版本并发控制）
- 适合高并发场景

**建议**:
- 开发环境使用 SQLite（简单、零配置）
- 生产环境考虑迁移到 Postgres（如果需要高并发）

---

## 四、前后端状态同步

### 4.1 乐观更新策略

**场景**: 用户操作后立即更新UI，后台异步同步到服务器

**实现**:
```typescript
// 前端
async function updateTicketStatus(id: number, newStatus: string) {
  // 1. 乐观更新本地状态
  const oldStatus = store.tickets.find(t => t.id === id)?.status
  store.updateTicket(id, { status: newStatus })
  
  try {
    // 2. 后台同步到服务器
    await ticketApi.updateStatus(id, newStatus)
  } catch (error) {
    // 3. 失败时回滚
    store.updateTicket(id, { status: oldStatus })
    showToast('更新失败，请重试', 'error')
  }
}
```

### 4.2 离线同步机制

参考技能：**offline-sync-implementation**

**核心思路**:
- 离线时操作加入待同步队列（IndexedDB）
- 网络恢复后自动同步
- 冲突时使用"服务器优先"策略

---

## 验收标准

### Pinia Store
- [ ] Store 使用 Composition API 风格定义
- [ ] 按业务域拆分，无巨型 Store
- [ ] 异步操作在 Actions 中完成
- [ ] Getters 保持纯函数，无副作用

### Composables
- [ ] 文件名以 `use` 开头
- [ ] 返回的 ref 在组件中可直接在模板使用
- [ ] 组件卸载后无内存泄漏（定时器/监听器已清理）
- [ ] 错误处理完善，不吞异常

### 事务管理
- [ ] 跨表操作使用 UnitOfWork 保证原子性
- [ ] 异常时自动回滚
- [ ] 对外部系统调用实现幂等性
- [ ] 事务边界清晰，在 Service 层开启

---

## 常见问题

### Q1: Store 和 Composable 如何选择？
**A**: 
- **Store**: 全局状态，跨页面共享（如用户信息、工单列表）
- **Composable**: 可复用逻辑，不涉及全局状态（如防抖、快捷键）

### Q2: 如何避免 Store 循环依赖？
**A**: 
- 设计时画出 Store 依赖图，确保无环
- 必要时合并相关 Store
- 使用事件总线解耦

### Q3: Composable 中如何处理异步错误？
**A**: 
```typescript
const error = ref<Error | null>(null)

async function fetchData() {
  try {
    loading.value = true
    data.value = await api.get()
  } catch (e) {
    error.value = e as Error
  } finally {
    loading.value = false
  }
}

return { data, loading, error, fetchData }
```

### Q4: UnitOfWork 是否影响性能？
**A**: 
- 轻微影响（事务开销）
- 但换来数据一致性保障，值得
- 对于单表操作可不用 UnitOfWork

### Q5: 如何测试使用 UnitOfWork 的代码？
**A**: 
- 使用内存数据库（SQLite :memory:）
- Mock Repository 接口
- 验证事务提交/回滚行为

---

## 相关技能
- **frontend-best-practices**: Vue 3、Vite、Router 综合指南
- **typescript-migration-guide**: TypeScript 迁移步骤
- **offline-sync-implementation**: 离线同步机制详解
- **task-orchestration**: 任务编排和异步作业处理

## 维护人
AI Assistant

## 最后更新
2026-05-31
