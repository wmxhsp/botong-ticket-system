---
title: offline-sync-implementation
priority: medium
tags: [offline, sync, reliability]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
---

## 简介
离线同步机制实现指南，确保在网络不稳定或断网环境下，用户仍可正常使用系统，数据在恢复网络后自动同步到服务器。

## 适用场景
- 移动办公场景（现场服务时网络信号差）
- 长表单填写过程中网络中断
- 批量操作时部分请求失败
- 需要高可靠性的数据录入场景

## 技术方案概览

### 核心组件
1. **本地存储**: IndexedDB（通过localforage封装）
2. **状态管理**: Pinia Store (`frontend/src/core/stores/sync.ts`，已存在)
3. **请求拦截器**: Axios Interceptor（需创建）
4. **同步引擎**: 后台定时同步 + 网络恢复触发

### 工作流程
```
用户操作 → API调用 → 检查网络状态
                    ├─ 在线 → 正常发送请求
                    └─ 离线 → 加入待同步队列 → 保存到IndexedDB
                              ↓
                        显示"已保存到本地"提示
                              ↓
                   监听网络恢复事件 → 自动同步 → 删除已同步项
```

---

## IndexedDB存储策略

### 1. 数据结构设计

**待同步队列表** (`pending_changes`):
```typescript
interface PendingChange {
  id: string              // UUID
  operation: 'create' | 'update' | 'delete'
  endpoint: string        // API端点，如 '/tickets'
  payload: any            // 请求体
  entityType: string      // 实体类型，如 'ticket'
  timestamp: number       // 创建时间戳
  retryCount: number      // 重试次数
  status: 'pending' | 'syncing' | 'failed'
  error?: string          // 最后一次错误信息
}
```

**离线草稿表** (`offline_drafts`):
```typescript
interface OfflineDraft {
  id: string              // UUID
  entityType: string      // 'ticket', 'client', etc.
  data: any               // 表单数据
  createdAt: number       // 创建时间
  updatedAt: number       // 最后更新时间
}
```

---

### 2. 使用localforage封装

**安装**:
```bash
npm install localforage
```

**封装模块** (`frontend/src/core/storage/offlineStorage.ts`):
```typescript
import localforage from 'localforage'

// 创建两个store
const pendingChangesStore = localforage.createInstance({
  name: 'botong-offline',
  storeName: 'pending_changes'
})

const draftsStore = localforage.createInstance({
  name: 'botong-offline',
  storeName: 'offline_drafts'
})

// 待同步队列操作
export async function addPendingChange(change: Omit<PendingChange, 'id' | 'timestamp' | 'retryCount' | 'status'>): Promise<string> {
  const id = crypto.randomUUID()
  const fullChange: PendingChange = {
    ...change,
    id,
    timestamp: Date.now(),
    retryCount: 0,
    status: 'pending'
  }
  
  await pendingChangesStore.setItem(id, fullChange)
  return id
}

export async function getPendingChanges(): Promise<PendingChange[]> {
  const changes: PendingChange[] = []
  await pendingChangesStore.iterate((value: PendingChange) => {
    if (value.status === 'pending') {
      changes.push(value)
    }
  })
  return changes.sort((a, b) => a.timestamp - b.timestamp)
}

export async function updateChangeStatus(id: string, status: PendingChange['status'], error?: string) {
  const change = await pendingChangesStore.getItem<PendingChange>(id)
  if (change) {
    change.status = status
    if (error) change.error = error
    if (status === 'syncing') change.retryCount++
    await pendingChangesStore.setItem(id, change)
  }
}

export async function removePendingChange(id: string) {
  await pendingChangesStore.removeItem(id)
}

// 草稿操作
export async function saveDraft(draft: Omit<OfflineDraft, 'id' | 'createdAt' | 'updatedAt'>): Promise<string> {
  const id = draft.id || crypto.randomUUID()
  const fullDraft: OfflineDraft = {
    ...draft,
    id,
    createdAt: draft.createdAt || Date.now(),
    updatedAt: Date.now()
  }
  
  await draftsStore.setItem(id, fullDraft)
  return id
}

export async function getDraft(entityType: string, id?: string): Promise<OfflineDraft | null> {
  if (id) {
    return await draftsStore.getItem(id)
  }
  
  // 获取该类型的最新草稿
  let latest: OfflineDraft | null = null
  await draftsStore.iterate((value: OfflineDraft) => {
    if (value.entityType === entityType && (!latest || value.updatedAt > latest.updatedAt)) {
      latest = value
    }
  })
  return latest
}

export async function clearDraft(id: string) {
  await draftsStore.removeItem(id)
}
```

---

## 请求拦截器集成

### 1. 创建拦截器

**位置**: `frontend/src/core/api/interceptor.ts`

```typescript
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useSyncStore } from '@/core/stores/sync'
import { addPendingChange } from '@/core/storage/offlineStorage'

export function setupOfflineInterceptor() {
  const api = axios.create({
    baseURL: '/api/v1',
    timeout: 10000
  })
  
  // 请求拦截器
  api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
    const syncStore = useSyncStore()
    
    // 只处理写操作（POST/PUT/DELETE/PATCH）
    if (['post', 'put', 'delete', 'patch'].includes(config.method?.toLowerCase() || '')) {
      // 检查网络状态
      if (!navigator.onLine) {
        // 离线时加入待同步队列
        const entityType = extractEntityType(config.url || '')
        
        await addPendingChange({
          operation: config.method as any,
          endpoint: config.url || '',
          payload: config.data,
          entityType
        })
        
        // 更新离线状态
        syncStore.setOnlineStatus(false)
        syncStore.incrementPendingCount()
        
        // 返回mock响应，避免前端报错
        return Promise.reject({ 
          offline: true, 
          config,
          mockResponse: { success: true, offline: true }
        })
      }
    }
    
    return config
  }, (error) => {
    return Promise.reject(error)
  })
  
  // 响应拦截器
  api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const syncStore = useSyncStore()
      
      // 网络错误时加入队列
      if (!navigator.onLine && error.code === 'ERR_NETWORK') {
        const config = error.config as InternalAxiosRequestConfig
        
        if (config && ['post', 'put', 'delete', 'patch'].includes(config.method?.toLowerCase() || '')) {
          const entityType = extractEntityType(config.url || '')
          
          await addPendingChange({
            operation: config.method as any,
            endpoint: config.url || '',
            payload: config.data,
            entityType
          })
          
          syncStore.incrementPendingCount()
          
          return Promise.reject({ 
            offline: true, 
            config,
            mockResponse: { success: true, offline: true }
          })
        }
      }
      
      return Promise.reject(error)
    }
  )
  
  return api
}

// 从URL提取实体类型
function extractEntityType(url: string): string {
  const match = url.match(/\/api\/v1\/(\w+)/)
  return match ? match[1] : 'unknown'
}
```

---

### 2. 在主API客户端中应用

**位置**: `frontend/src/core/api/client.ts`

```typescript
import { setupOfflineInterceptor } from './interceptor'

// 创建带离线支持的API客户端
export const api = setupOfflineInterceptor()
```

---

## 同步引擎实现

### 1. 扩展现有sync.ts store

**位置**: `frontend/src/core/stores/sync.ts`（已存在，需扩展）

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getPendingChanges, updateChangeStatus, removePendingChange } from '@/core/storage/offlineStorage'
import { api } from '@/core/api/client'

export const useSyncStore = defineStore('sync', () => {
  const isOnline = ref(navigator.onLine)
  const pendingCount = ref(0)
  const isSyncing = ref(false)
  const lastSyncTime = ref<number | null>(null)
  
  // 计算属性
  const hasPendingChanges = computed(() => pendingCount.value > 0)
  
  // 方法
  function setOnlineStatus(status: boolean) {
    isOnline.value = status
  }
  
  function incrementPendingCount() {
    pendingCount.value++
  }
  
  function decrementPendingCount() {
    pendingCount.value = Math.max(0, pendingCount.value - 1)
  }
  
  // 核心同步方法
  async function sync() {
    if (isSyncing.value || !isOnline.value) {
      return
    }
    
    isSyncing.value = true
    
    try {
      const changes = await getPendingChanges()
      
      for (const change of changes) {
        try {
          await updateChangeStatus(change.id, 'syncing')
          
          // 发送请求到服务器
          const response = await api.request({
            method: change.operation,
            url: change.endpoint,
            data: change.payload
          })
          
          // 同步成功，删除队列项
          await removePendingChange(change.id)
          decrementPendingCount()
          
        } catch (error) {
          console.error(`同步失败 [${change.id}]:`, error)
          await updateChangeStatus(change.id, 'failed', String(error))
          
          // 重试次数超过3次，标记为永久失败
          if (change.retryCount >= 3) {
            await removePendingChange(change.id)
            decrementPendingCount()
          }
        }
      }
      
      lastSyncTime.value = Date.now()
      
    } finally {
      isSyncing.value = false
    }
  }
  
  // 监听网络恢复
  function initNetworkListener() {
    window.addEventListener('online', () => {
      setOnlineStatus(true)
      sync()  // 自动同步
    })
    
    window.addEventListener('offline', () => {
      setOnlineStatus(false)
    })
  }
  
  return {
    isOnline,
    pendingCount,
    isSyncing,
    lastSyncTime,
    hasPendingChanges,
    setOnlineStatus,
    incrementPendingCount,
    decrementPendingCount,
    sync,
    initNetworkListener
  }
})
```

---

### 2. 在App.vue中初始化

**位置**: `frontend/src/App.vue`

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useSyncStore } from '@/core/stores/sync'

const syncStore = useSyncStore()

onMounted(() => {
  // 初始化网络监听
  syncStore.initNetworkListener()
  
  // 如果有待同步项，尝试同步
  if (syncStore.hasPendingChanges) {
    syncStore.sync()
  }
})
</script>

<template>
  <div id="app">
    <!-- 离线状态指示器 -->
    <div v-if="!syncStore.isOnline" class="offline-indicator">
      <span>⚠️ 离线模式</span>
      <span v-if="syncStore.hasPendingChanges">
        （{{ syncStore.pendingCount }} 项待同步）
      </span>
    </div>
    
    <router-view />
  </div>
</template>

<style scoped>
.offline-indicator {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: #ff9800;
  color: white;
  text-align: center;
  padding: 8px;
  z-index: 9999;
  font-size: 14px;
}
</style>
```

---

## 冲突解决机制

### 1. 服务器优先策略

**原则**: 
- 同步时比较时间戳
- 如果服务器数据更新，保留服务器数据
- 如果本地数据更新，提示用户手动合并

**实现**:
```typescript
async function resolveConflict(localData: any, serverData: any, entityType: string) {
  const localTime = localData.updated_at || localData.created_at
  const serverTime = serverData.updated_at || serverData.created_at
  
  if (serverTime > localTime) {
    // 服务器数据更新，直接使用
    return { action: 'use_server', data: serverData }
  } else if (localTime > serverTime) {
    // 本地数据更新，提示用户
    return { 
      action: 'manual_merge', 
      local: localData, 
      server: serverData,
      message: `本地${entityType}与服务器版本冲突，请手动选择保留哪个版本`
    }
  } else {
    // 时间相同，视为相同数据
    return { action: 'skip', data: serverData }
  }
}
```

---

### 2. 关键字段保护

**规则**: 
- 金额字段（total、amount）禁止离线修改
- 状态字段（status、billing_status）需要同步前校验
- 库存扣减操作必须在服务器端执行

**实现**:
```typescript
function canModifyOffline(entityType: string, field: string): boolean {
  const protectedFields: Record<string, string[]> = {
    ticket: ['total', 'status', 'billing_status'],
    material: ['quantity', 'unit_price'],
    payment: ['amount', 'method']
  }
  
  return !(protectedFields[entityType]?.includes(field))
}
```

---

## 同步状态指示器设计

### UI组件

**位置**: `frontend/src/components/common/SyncStatusIndicator.vue`

```vue
<script setup lang="ts">
import { useSyncStore } from '@/core/stores/sync'

const syncStore = useSyncStore()

function handleManualSync() {
  syncStore.sync()
}
</script>

<template>
  <div class="sync-status" :class="{ offline: !syncStore.isOnline }">
    <span v-if="!syncStore.isOnline" class="status-icon">📡</span>
    <span v-else-if="syncStore.isSyncing" class="status-icon spinning">🔄</span>
    <span v-else class="status-icon">✅</span>
    
    <span class="status-text">
      <template v-if="!syncStore.isOnline">
        离线模式
      </template>
      <template v-else-if="syncStore.isSyncing">
        同步中...
      </template>
      <template v-else-if="syncStore.hasPendingChanges">
        {{ syncStore.pendingCount }} 项待同步
      </template>
      <template v-else>
        已同步
      </template>
    </span>
    
    <button 
      v-if="syncStore.hasPendingChanges && syncStore.isOnline" 
      @click="handleManualSync"
      class="sync-btn"
    >
      立即同步
    </button>
  </div>
</template>

<style scoped>
.sync-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 14px;
}

.sync-status.offline {
  background: #ff9800;
  color: white;
}

.status-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.sync-btn {
  padding: 4px 8px;
  background: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.sync-btn:hover {
  background: #e0e0e0;
}
</style>
```

---

## 验收标准

### 功能验收
- [ ] 断网时可创建工单，数据保存到IndexedDB
- [ ] 恢复网络后自动同步到服务器
- [ ] 同步失败有明确提示和重试机制
- [ ] 离线状态指示器正确显示当前状态
- [ ] 待同步数量实时更新

### 可靠性验收
- [ ] 同步重试机制工作正常（最多3次）
- [ ] 冲突检测和处理逻辑正确
- [ ] 关键字段离线修改被阻止
- [ ] 刷新页面后待同步队列不丢失

### 性能验收
- [ ] 离线操作响应时间 < 100ms（本地保存）
- [ ] 同步100条记录耗时 < 30秒
- [ ] IndexedDB存储空间不超过50MB

---

## 常见问题

### Q1: IndexedDB存储空间不足怎么办？
**A**: 
- 定期清理已同步的旧数据
- 限制待同步队列大小（最多100条）
- 提供"清除所有离线数据"按钮

### Q2: 如何处理大量数据同时同步？
**A**: 
- 分批同步，每批10条
- 使用Web Worker避免阻塞UI
- 显示进度条和预计剩余时间

### Q3: 同步过程中用户又创建了新的离线数据？
**A**: 
- 新数据加入队列尾部
- 继续同步队列中的旧数据
- 不影响用户当前操作

### Q4: 如何调试离线同步功能？
**A**: 
- Chrome DevTools → Application → IndexedDB查看数据
- Network面板中勾选"Offline"模拟断网
- Console中观察同步日志

---

## 维护人
AI Assistant

## 最后更新
2026-05-31

## 相关技能
- ticket-system-optimization
- pinia-best-practices
- frontend-best-practices
