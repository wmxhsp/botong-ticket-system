import { ref, computed, onScopeDispose } from 'vue'
import { useRouter } from 'vue-router'
import { searchApi } from '@/api/search'
import type { Ticket, Client } from '@/types'

export interface CommandItem {
  id: string
  type: 'ticket' | 'client' | 'command' | 'recent'
  title: string
  subtitle?: string
  icon?: string
  action?: () => void
  route?: string
  meta?: Record<string, any>
}

const STATIC_COMMANDS: CommandItem[] = [
  { id: 'cmd-new-ticket', type: 'command', title: '新建工单', subtitle: '创建一个新的工单', icon: 'bi-plus-circle', route: '/tickets/create' },
  { id: 'cmd-new-client', type: 'command', title: '新建客户', subtitle: '添加新客户信息', icon: 'bi-person-plus', route: '/clients/create' },
  { id: 'cmd-dashboard', type: 'command', title: '仪表盘', subtitle: '查看数据概览', icon: 'bi-speedometer2', route: '/' },
  { id: 'cmd-tickets', type: 'command', title: '工单列表', subtitle: '查看所有工单', icon: 'bi-ticket-perforated', route: '/tickets' },
  { id: 'cmd-clients', type: 'command', title: '客户列表', subtitle: '查看所有客户', icon: 'bi-people', route: '/clients' },
  { id: 'cmd-equipment', type: 'command', title: '设备管理', subtitle: '查看设备列表', icon: 'bi-pc-display', route: '/equipment' },
  { id: 'cmd-finance', type: 'command', title: '财务管理', subtitle: '查看收支明细', icon: 'bi-cash-stack', route: '/finance' },
  { id: 'cmd-settings', type: 'command', title: '系统设置', subtitle: '配置系统参数', icon: 'bi-gear', route: '/settings' },
  { id: 'cmd-stats', type: 'command', title: '统计分析', subtitle: '查看业务统计', icon: 'bi-bar-chart', route: '/stats' },
]

function loadRecentCommands(): CommandItem[] {
  try {
    const saved = localStorage.getItem('bt_recent_commands')
    if (saved) {
      const parsed = JSON.parse(saved)
      return parsed.slice(0, 5)
    }
  } catch {
    // ignore
  }
  return []
}

function saveRecentCommand(item: CommandItem, recentCommands: CommandItem[]) {
  const existing = recentCommands.findIndex(r => r.id === item.id)
  let updated = [...recentCommands]
  if (existing >= 0) {
    updated.splice(existing, 1)
  }
  updated = [item, ...updated].slice(0, 5)
  try {
    localStorage.setItem('bt_recent_commands', JSON.stringify(updated))
  } catch {}
  return updated
}

export function useCommandPalette() {
  const router = useRouter()

  const isOpen = ref(false)
  const query = ref('')
  const loading = ref(false)
  const activeIndex = ref(0)
  const recentCommands = ref<CommandItem[]>(loadRecentCommands())
  const searchResults = ref<CommandItem[]>([])

  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  onScopeDispose(() => {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
  })

  const filteredItems = computed<CommandItem[]>(() => {
    const q = query.value.trim().toLowerCase()
    if (!q) {
      if (recentCommands.value.length > 0) {
        return recentCommands.value.map(r => ({ ...r, type: 'recent' as const }))
      }
      return STATIC_COMMANDS.slice(0, 6)
    }

    const staticMatches = STATIC_COMMANDS.filter(cmd =>
      cmd.title.toLowerCase().includes(q) ||
      (cmd.subtitle && cmd.subtitle.toLowerCase().includes(q))
    )

    return [...searchResults.value, ...staticMatches]
  })

  function open() {
    isOpen.value = true
    query.value = ''
    activeIndex.value = 0
    searchResults.value = []
    recentCommands.value = loadRecentCommands()
  }

  function close() {
    isOpen.value = false
    query.value = ''
    searchResults.value = []
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
  }

  function toggle() {
    if (isOpen.value) close()
    else open()
  }

  function moveDown() {
    const total = filteredItems.value.length
    if (total === 0) return
    activeIndex.value = (activeIndex.value + 1) % total
  }

  function moveUp() {
    const total = filteredItems.value.length
    if (total === 0) return
    activeIndex.value = (activeIndex.value - 1 + total) % total
  }

  function moveToFirst() {
    const total = filteredItems.value.length
    if (total === 0) return
    activeIndex.value = 0
  }

  function moveToLast() {
    const total = filteredItems.value.length
    if (total === 0) return
    activeIndex.value = total - 1
  }

  function selectCurrent() {
    const items = filteredItems.value
    const item = items[activeIndex.value]
    if (!item) return
    executeItem(item)
  }

  function executeItem(item: CommandItem) {
    const originalType = item.type === 'recent' ? (item.meta?.originalType || 'command') : item.type
    recentCommands.value = saveRecentCommand({ ...item, type: originalType }, recentCommands.value)
    close()

    if (item.action) {
      item.action()
      return
    }
    if (item.route) {
      router.push(item.route)
      return
    }
  }

  async function performSearch(val: string) {
    if (!val || val.length < 1) {
      searchResults.value = []
      return
    }
    loading.value = true
    activeIndex.value = 0
    try {
      const res = await searchApi.search({ q: val })
      const data = res.data ?? {}
      const items: CommandItem[] = []

      if (data.tickets?.length) {
        items.push(...data.tickets.map((t: Ticket) => ({
          id: `ticket-${t.id}`,
          type: 'ticket' as const,
          title: `#${t.id} ${t.client || ''}`,
          subtitle: t.content?.slice(0, 50) || t.description?.slice(0, 50) || '',
          icon: 'bi-ticket-perforated',
          route: `/tickets/${t.id}`,
          meta: { originalType: 'ticket' },
        })))
      }

      if (data.clients?.length) {
        items.push(...data.clients.map((c: Client) => ({
          id: `client-${c.id}`,
          type: 'client' as const,
          title: c.name || '',
          subtitle: [c.contact, c.phone].filter(Boolean).join(' ') || '',
          icon: 'bi-person',
          route: `/clients/${encodeURIComponent(c.name || '')}`,
          meta: { originalType: 'client' },
        })))
      }

      searchResults.value = items
    } catch {
      searchResults.value = []
    } finally {
      loading.value = false
    }
  }

  function onQueryChange(val: string) {
    if (debounceTimer) clearTimeout(debounceTimer)
    if (!val.trim()) {
      searchResults.value = []
      return
    }
    debounceTimer = setTimeout(() => performSearch(val), 300)
  }

  return {
    isOpen,
    query,
    loading,
    activeIndex,
    filteredItems,
    open,
    close,
    toggle,
    moveDown,
    moveUp,
    moveToFirst,
    moveToLast,
    selectCurrent,
    executeItem,
    onQueryChange,
  }
}
