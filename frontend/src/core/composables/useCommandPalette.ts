import { ref, computed, watch } from 'vue'
import { ticketApi } from '@/modules/ticket/api'
import { clientApi } from '@/modules/client/api'

export interface CommandItem {
  id: string
  type: 'ticket' | 'client' | 'command'
  title: string
  subtitle?: string
  icon?: string
  action: () => void
  score?: number  // 用于排序
}

export function useCommandPalette() {
  const isOpen = ref(false)
  const searchQuery = ref('')
  const selectedIndex = ref(0)
  const commands = ref<CommandItem[]>([])
  const recentCommands = ref<string[]>([])  // 最近使用的命令ID
  
  // 加载状态
  const isLoading = ref(false)
  
  // 搜索结果（使用ref存储异步结果）
  const results = ref<CommandItem[]>([])
  
  // 搜索查询变化时重新加载
  async function refreshResults() {
    if (!searchQuery.value.trim()) {
      // 无搜索时显示最近使用和常用命令
      results.value = getRecentAndCommonCommands()
    } else {
      // 有搜索时执行过滤
      results.value = await filterCommands(searchQuery.value)
    }
  }
  
  // 打开命令面板
  function open() {
    isOpen.value = true
    searchQuery.value = ''
    selectedIndex.value = 0
    loadInitialData()
    refreshResults()
  }
  
  // 关闭命令面板
  function close() {
    isOpen.value = false
    searchQuery.value = ''
    selectedIndex.value = 0
  }
  
  // 切换开关
  function toggle() {
    if (isOpen.value) {
      close()
    } else {
      open()
    }
  }
  
  // 选择上一项
  function selectPrevious() {
    if (selectedIndex.value > 0) {
      selectedIndex.value--
    } else {
      selectedIndex.value = results.value.length - 1
    }
  }
  
  // 选择下一项
  function selectNext() {
    if (selectedIndex.value < results.value.length - 1) {
      selectedIndex.value++
    } else {
      selectedIndex.value = 0
    }
  }
  
  // 执行选中项
  async function executeSelected() {
    const item = results.value[selectedIndex.value]
    if (item) {
      // 记录到最近使用
      addToRecent(item.id)
      
      // 执行动作
      await item.action()
      
      // 关闭面板
      close()
    }
  }
  
  // 加载初始数据
  async function loadInitialData() {
    isLoading.value = true
    
    try {
      // 加载最近的工单
      const response = await ticketApi.list({ page: 1, page_size: 10 })
      const tickets = response.data?.items || []
      
      commands.value = [
        // 快捷命令
        ...getQuickCommands(),
        
        // 最近工单
        ...tickets.map((ticket: any) => ({
          id: `ticket-${ticket.id}`,
          type: 'ticket' as const,
          title: `${ticket.ticket_no} - ${ticket.client}`,
          subtitle: `状态: ${getStatusText(ticket.status)} | 金额: ¥${ticket.total}`,
          icon: '🎫',
          score: 0,
          action: () => navigateToTicket(ticket.id)
        }))
      ]
    } catch (error) {
      console.error('Failed to load initial data:', error)
    } finally {
      isLoading.value = false
    }
  }
  
  // 过滤命令
  async function filterCommands(query: string): Promise<CommandItem[]> {
    isLoading.value = true
    
    try {
      const results: CommandItem[] = []
      
      // 1. 搜索工单
      if (query.length >= 2) {
        const ticketResponse = await ticketApi.list({ 
          keyword: query,
          page: 1, 
          page_size: 10 
        })
        const tickets = ticketResponse.data?.items || []
        
        results.push(...tickets.map((ticket: any) => ({
          id: `ticket-${ticket.id}`,
          type: 'ticket' as const,
          title: `${ticket.ticket_no} - ${ticket.client}`,
          subtitle: `状态: ${getStatusText(ticket.status)}`,
          icon: '🎫',
          score: calculateRelevanceScore(ticket, query),
          action: () => navigateToTicket(ticket.id)
        })))
        
        // 2. 搜索客户
        const clientResponse = await clientApi.list({
          keyword: query,
          page: 1,
          page_size: 5
        })
        const clients = clientResponse.data?.items || []
        
        results.push(...clients.map((client: any) => ({
          id: `client-${client.id}`,
          type: 'client' as const,
          title: client.name,
          subtitle: client.phone || '无电话',
          icon: '👤',
          score: calculateRelevanceScore(client, query),
          action: () => navigateToClient(client.id)
        })))
      }
      
      // 3. 过滤快捷命令
      const quickCommands = getQuickCommands().filter(cmd => 
        fuzzyMatch(cmd.title, query) || fuzzyMatch(cmd.subtitle || '', query)
      )
      
      results.unshift(...quickCommands)
      
      // 按相关性排序
      return results.sort((a, b) => (b.score || 0) - (a.score || 0))
      
    } catch (error) {
      console.error('Failed to filter commands:', error)
      return []
    } finally {
      isLoading.value = false
    }
  }
  
  // 获取快捷命令
  function getQuickCommands(): CommandItem[] {
    return [
      {
        id: 'cmd-new-ticket',
        type: 'command',
        title: '新建工单',
        subtitle: '快速创建新工单',
        icon: '➕',
        action: () => navigateTo('/tickets/quick')
      },
      {
        id: 'cmd-today-tickets',
        type: 'command',
        title: '今日工单',
        subtitle: '查看今天的工单',
        icon: '📅',
        action: () => navigateTo('/tickets?date=today')
      },
      {
        id: 'cmd-unpaid-tickets',
        type: 'command',
        title: '未收款工单',
        subtitle: '查看待收款的工单',
        icon: '💰',
        action: () => navigateTo('/tickets?billing=unpaid')
      },
      {
        id: 'cmd-dashboard',
        type: 'command',
        title: '仪表盘',
        subtitle: '查看数据统计',
        icon: '📊',
        action: () => navigateTo('/dashboard')
      }
    ]
  }
  
  // 获取最近和常用命令
  function getRecentAndCommonCommands(): CommandItem[] {
    const recent = commands.value.filter(cmd => 
      recentCommands.value.includes(cmd.id)
    ).slice(0, 5)
    
    const common = getQuickCommands()
    
    return [...recent, ...common]
  }
  
  // 添加到最近使用
  function addToRecent(commandId: string) {
    // 移除已存在的
    recentCommands.value = recentCommands.value.filter(id => id !== commandId)
    
    // 添加到开头
    recentCommands.value.unshift(commandId)
    
    // 只保留10个
    recentCommands.value = recentCommands.value.slice(0, 10)
    
    // 持久化
    localStorage.setItem('bt_recent_commands', JSON.stringify(recentCommands.value))
  }
  
  // 从localStorage恢复最近使用
  function loadRecentCommands() {
    const saved = localStorage.getItem('bt_recent_commands')
    if (saved) {
      try {
        recentCommands.value = JSON.parse(saved)
      } catch (e) {
        console.error('Failed to parse recent commands:', e)
      }
    }
  }
  
  // 模糊匹配
  function fuzzyMatch(text: string, query: string): boolean {
    if (!query) return true
    if (!text) return false
    
    const lowerText = text.toLowerCase()
    const lowerQuery = query.toLowerCase()
    
    // 简单包含匹配
    return lowerText.includes(lowerQuery)
  }
  
  // 计算相关性分数
  function calculateRelevanceScore(item: any, query: string): number {
    let score = 0
    
    // 完全匹配得分高
    if (item.ticket_no?.toLowerCase() === query.toLowerCase()) {
      score += 100
    }
    
    // 前缀匹配
    if (item.ticket_no?.toLowerCase().startsWith(query.toLowerCase())) {
      score += 50
    }
    
    // 包含匹配
    if (item.ticket_no?.toLowerCase().includes(query.toLowerCase())) {
      score += 20
    }
    
    if (item.client?.toLowerCase().includes(query.toLowerCase())) {
      score += 10
    }
    
    return score
  }
  
  // 获取状态文本
  function getStatusText(status: string): string {
    const statusMap: Record<string, string> = {
      open: '待处理',
      in_progress: '进行中',
      completed: '已完成',
      cancelled: '已取消'
    }
    return statusMap[status] || status
  }
  
  // 导航到工单详情
  function navigateToTicket(ticketId: number) {
    navigateTo(`/tickets/${ticketId}`)
  }
  
  // 导航到客户详情
  function navigateToClient(clientId: number) {
    navigateTo(`/clients/${clientId}`)
  }
  
  // 通用导航
  function navigateTo(path: string) {
    // 使用Vue Router
    import('@/router').then((routerModule) => {
      const router = routerModule.default
      router.push(path)
    })
  }
  
  // 初始化
  loadRecentCommands()
  
  // 监听搜索查询变化
  watch(searchQuery, () => {
    selectedIndex.value = 0
    refreshResults()
  })
  
  return {
    isOpen,
    searchQuery,
    selectedIndex,
    results,
    isLoading,
    open,
    close,
    toggle,
    selectPrevious,
    selectNext,
    executeSelected
  }
}
