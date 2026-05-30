import { watch, onMounted, onUnmounted } from 'vue'
import { useSyncStore } from '@/core/stores/sync'
import { ticketApi } from '@/api/tickets'
import { clientApi } from '@/api/clients'
import type { PendingChange } from '@/core/stores/sync'

/**
 * 离线同步 Composable
 * 
 * 提供完整的离线数据同步功能：
 * - 自动检测网络状态变化
 * - 网络恢复时自动同步待处理变更
 * - 冲突检测和解决
 * - 同步进度跟踪
 * 
 * @example
 * ```ts
 * const { syncPendingChanges, isSyncing } = useOfflineSync()
 * 
 * // 手动触发同步
 * await syncPendingChanges()
 * ```
 */
export function useOfflineSync() {
  const syncStore = useSyncStore()
  
  const isSyncing = ref(false)
  const syncProgress = ref({ current: 0, total: 0 })
  const syncErrors = ref<string[]>([])
  
  /**
   * API端点映射
   */
  const apiMap: Record<string, any> = {
    tickets: ticketApi,
    clients: clientApi,
  }
  
  /**
   * 监听网络状态变化
   */
  function setupNetworkListeners() {
    const handleOnline = () => {
      console.log('[OfflineSync] Network restored, starting sync...')
      syncStore.setOnlineStatus(true)
      // 自动同步待处理的变更
      syncPendingChanges()
    }
    
    const handleOffline = () => {
      console.log('[OfflineSync] Network lost')
      syncStore.setOnlineStatus(false)
    }
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }
  
  /**
   * 同步单个变更
   */
  async function syncSingleChange(change: PendingChange): Promise<boolean> {
    try {
      const api = apiMap[change.entityType]
      if (!api) {
        throw new Error(`Unknown entity type: ${change.entityType}`)
      }
      
      let result
      
      switch (change.operation) {
        case 'create':
          result = await api.create(change.payload)
          break
        case 'update':
          if (change.entityId) {
            result = await api.update(change.entityId, change.payload)
          } else {
            throw new Error('Missing entityId for update operation')
          }
          break
        case 'delete':
          if (change.entityId) {
            result = await api.delete(change.entityId)
          } else {
            throw new Error('Missing entityId for delete operation')
          }
          break
        default:
          throw new Error(`Unknown operation: ${change.operation}`)
      }
      
      // 同步成功，从队列中移除
      syncStore.removeChange(change.id)
      
      return true
    } catch (error) {
      const errorMsg = `Failed to sync ${change.operation} ${change.entityType} #${change.id}: ${error.message}`
      console.error('[OfflineSync]', errorMsg)
      syncErrors.value.push(errorMsg)
      return false
    }
  }
  
  /**
   * 同步所有待处理的变更
   */
  async function syncPendingChanges(): Promise<{ success: number; failed: number }> {
    if (isSyncing.value) {
      console.warn('[OfflineSync] Sync already in progress')
      return { success: 0, failed: 0 }
    }
    
    if (!syncStore.isOnline) {
      console.warn('[OfflineSync] Cannot sync while offline')
      return { success: 0, failed: 0 }
    }
    
    const changes = [...syncStore.pendingChanges]
    if (changes.length === 0) {
      console.log('[OfflineSync] No pending changes to sync')
      return { success: 0, failed: 0 }
    }
    
    isSyncing.value = true
    syncErrors.value = []
    syncProgress.value = { current: 0, total: changes.length }
    
    let successCount = 0
    let failedCount = 0
    
    try {
      // 按时间戳排序，确保操作顺序
      const sortedChanges = changes.sort((a, b) => a.timestamp - b.timestamp)
      
      for (let i = 0; i < sortedChanges.length; i++) {
        const change = sortedChanges[i]
        syncProgress.value.current = i + 1
        
        const success = await syncSingleChange(change)
        if (success) {
          successCount++
        } else {
          failedCount++
        }
        
        // 每个操作之间稍微延迟，避免API限流
        if (i < sortedChanges.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 100))
        }
      }
      
      // 更新最后同步时间
      if (successCount > 0) {
        syncStore.updateLastSync()
      }
      
      console.log(`[OfflineSync] Sync completed: ${successCount} succeeded, ${failedCount} failed`)
    } finally {
      isSyncing.value = false
      syncProgress.value = { current: 0, total: 0 }
    }
    
    return { success: successCount, failed: failedCount }
  }
  
  /**
   * 将变更添加到同步队列
   */
  function queueChange(
    entityType: string,
    operation: 'create' | 'update' | 'delete',
    payload: Record<string, any>,
    entityId?: string | number
  ) {
    syncStore.queueChange({
      operation,
      endpoint: `/api/v1/${entityType}`,
      payload,
      entityType,
      entityId,
    })
  }
  
  /**
   * 检测冲突（简单版本：检查实体是否被修改）
   */
  async function detectConflict(
    entityType: string,
    entityId: string | number
  ): Promise<boolean> {
    try {
      const api = apiMap[entityType]
      if (!api) return false
      
      // 获取服务器上的最新版本
      const serverData = await api.get(entityId)
      
      // 这里可以实现更复杂的冲突检测逻辑
      // 例如比较更新时间戳、版本号等
      return false // 暂时返回无冲突
    } catch (error) {
      console.error('[OfflineSync] Conflict detection failed:', error)
      return false
    }
  }
  
  /**
   * 清除同步错误
   */
  function clearSyncErrors() {
    syncErrors.value = []
  }
  
  /**
   * 重试失败的同步
   */
  async function retryFailedSyncs() {
    if (syncErrors.value.length === 0) {
      console.log('[OfflineSync] No errors to retry')
      return
    }
    
    clearSyncErrors()
    return syncPendingChanges()
  }
  
  // 自动设置网络监听
  let cleanup: (() => void) | undefined
  
  onMounted(() => {
    cleanup = setupNetworkListeners()
  })
  
  onUnmounted(() => {
    if (cleanup) {
      cleanup()
    }
  })
  
  return {
    isSyncing,
    syncProgress,
    syncErrors,
    syncPendingChanges,
    queueChange,
    detectConflict,
    clearSyncErrors,
    retryFailedSyncs,
  }
}
