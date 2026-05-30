import { defineStore } from 'pinia'
import { ref, computed, type Ref, type ComputedRef } from 'vue'

export type SyncOperationType = 'create' | 'update' | 'delete'

export interface PendingChange {
  id: string
  timestamp: number
  operation: SyncOperationType
  endpoint: string
  payload: Record<string, any>
  entityType: string
  entityId?: string | number
}

export interface SyncState {
  isOnline: Ref<boolean>
  lastSync: Ref<number | null>
  pendingChanges: Ref<PendingChange[]>
  hasPendingChanges: ComputedRef<boolean>
  pendingCount: ComputedRef<number>
  queueChange: (change: Omit<PendingChange, 'id' | 'timestamp'>) => void
  removeChange: (id: string) => void
  clearQueue: () => void
  setOnlineStatus: (status: boolean) => void
  updateLastSync: (timestamp?: number) => void
  restoreQueue: () => void
  persistQueue: () => void
}

const STORAGE_KEY = 'bt_sync_queue'
const LAST_SYNC_KEY = 'bt_last_sync'

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export const useSyncStore = defineStore('sync', (): SyncState => {
  const isOnline = ref<boolean>(navigator.onLine)
  const lastSync = ref<number | null>(
    (() => {
      const stored = localStorage.getItem(LAST_SYNC_KEY)
      return stored ? parseInt(stored, 10) : null
    })()
  )
  const pendingChanges = ref<PendingChange[]>([])

  const hasPendingChanges = computed(() => pendingChanges.value.length > 0)
  const pendingCount = computed(() => pendingChanges.value.length)

  function queueChange(
    change: Omit<PendingChange, 'id' | 'timestamp'>
  ): void {
    const item: PendingChange = {
      ...change,
      id: generateId(),
      timestamp: Date.now(),
    }
    pendingChanges.value.push(item)
    persistQueue()
  }

  function removeChange(id: string): void {
    const idx = pendingChanges.value.findIndex((c) => c.id === id)
    if (idx !== -1) {
      pendingChanges.value.splice(idx, 1)
      persistQueue()
    }
  }

  function clearQueue(): void {
    pendingChanges.value = []
    persistQueue()
  }

  function setOnlineStatus(status: boolean): void {
    isOnline.value = status
  }

  function updateLastSync(timestamp?: number): void {
    const ts = timestamp ?? Date.now()
    lastSync.value = ts
    localStorage.setItem(LAST_SYNC_KEY, String(ts))
  }

  function persistQueue(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(pendingChanges.value))
    } catch (e) {
      console.error('[SyncStore] Failed to persist queue:', e)
    }
  }

  function restoreQueue(): void {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as PendingChange[]
        if (Array.isArray(parsed)) {
          pendingChanges.value = parsed
        }
      }
    } catch (e) {
      console.error('[SyncStore] Failed to restore queue:', e)
      pendingChanges.value = []
    }
  }

  restoreQueue()

  return {
    isOnline,
    lastSync,
    pendingChanges,
    hasPendingChanges,
    pendingCount,
    queueChange,
    removeChange,
    clearQueue,
    setOnlineStatus,
    updateLastSync,
    restoreQueue,
    persistQueue,
  }
})
