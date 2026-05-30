import { ref, onMounted, onUnmounted } from 'vue'
import client from '@/api/client'
import {
  useSyncStore,
  type PendingChange,
  type SyncOperationType,
} from '@/core/stores/sync'

export interface UseOfflineSyncReturn {
  isOnline: boolean
  isSyncing: boolean
  lastSyncText: string
  pendingCount: number
  hasPendingChanges: boolean
  syncNow: () => Promise<void>
  queueChange: (
    operation: SyncOperationType,
    endpoint: string,
    payload: Record<string, any>,
    entityType: string,
    entityId?: string | number
  ) => void
}

function formatLastSync(ts: number | null): string {
  if (!ts) return '未同步'
  const date = new Date(ts)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleString('zh-CN')
}

async function executeChange(change: PendingChange): Promise<void> {
  const methodMap: Record<SyncOperationType, string> = {
    create: 'post',
    update: 'put',
    delete: 'delete',
  }
  const method = methodMap[change.operation]
  if (!method) {
    throw new Error(`Unknown operation: ${change.operation}`)
  }

  const url = change.endpoint
  const payload = change.payload

  if (method === 'delete') {
    await client.delete(url, { data: payload })
  } else if (method === 'put') {
    await client.put(url, payload)
  } else {
    await client.post(url, payload)
  }
}

export function useOfflineSync(): UseOfflineSyncReturn {
  const syncStore = useSyncStore()
  const isSyncing = ref(false)
  const lastSyncText = ref(formatLastSync(syncStore.lastSync))

  let intervalId: ReturnType<typeof setInterval> | null = null
  let abortController: AbortController | null = null

  async function syncNow(): Promise<void> {
    if (isSyncing.value) return
    if (!syncStore.isOnline) return
    if (!syncStore.hasPendingChanges) return

    isSyncing.value = true
    abortController = new AbortController()

    const queue = [...syncStore.pendingChanges]
    const failed: PendingChange[] = []

    for (const change of queue) {
      if (abortController.signal.aborted) {
        failed.push(change)
        continue
      }

      try {
        await executeChange(change)
        syncStore.removeChange(change.id)
      } catch (e: any) {
        const status = e.response?.status
        if (status === 401 || status === 403) {
          failed.push(change)
          break
        }
        if (status >= 400 && status < 500 && status !== 429) {
          console.error(
            `[OfflineSync] Client error ${status}, dropping change:`,
            change.id
          )
          syncStore.removeChange(change.id)
          continue
        }
        failed.push(change)
      }
    }

    if (failed.length === 0) {
      syncStore.updateLastSync()
      lastSyncText.value = formatLastSync(syncStore.lastSync)
    }

    isSyncing.value = false
    abortController = null
  }

  function queueChange(
    operation: SyncOperationType,
    endpoint: string,
    payload: Record<string, any>,
    entityType: string,
    entityId?: string | number
  ): void {
    syncStore.queueChange({
      operation,
      endpoint,
      payload,
      entityType,
      entityId,
    })
  }

  function handleOnline(): void {
    syncStore.setOnlineStatus(true)
    syncNow()
  }

  function handleOffline(): void {
    syncStore.setOnlineStatus(false)
    if (abortController) {
      abortController.abort()
      abortController = null
      isSyncing.value = false
    }
  }

  function updateLastSyncText(): void {
    lastSyncText.value = formatLastSync(syncStore.lastSync)
  }

  onMounted(() => {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    intervalId = setInterval(updateLastSyncText, 60000)

    if (syncStore.isOnline && syncStore.hasPendingChanges) {
      syncNow()
    }
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
    if (abortController) {
      abortController.abort()
      abortController = null
    }
  })

  return {
    isOnline: syncStore.isOnline,
    isSyncing,
    lastSyncText,
    pendingCount: syncStore.pendingCount,
    hasPendingChanges: syncStore.hasPendingChanges,
    syncNow,
    queueChange,
  } as unknown as UseOfflineSyncReturn
}
