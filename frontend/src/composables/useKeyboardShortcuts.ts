import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

export interface ShortcutConfig {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  meta?: boolean
  description: string
  action: () => void
  condition?: () => boolean
}

const shortcutsHelpVisible = ref(false)
const registeredShortcuts = ref<ShortcutConfig[]>([])

let globalHandlerRegistered = false
let globalHandler: ((e: KeyboardEvent) => void) | null = null

export function useKeyboardShortcuts() {
  const router = useRouter()

  function isInputElement(target: EventTarget | null): boolean {
    if (!target || !(target instanceof HTMLElement)) return false
    const tag = target.tagName.toLowerCase()
    const editable = target.getAttribute('contenteditable') === 'true'
    return tag === 'input' || tag === 'textarea' || tag === 'select' || editable
  }

  function matchShortcut(e: KeyboardEvent, config: ShortcutConfig): boolean {
    const keyMatch = e.key.toLowerCase() === config.key.toLowerCase()
    const ctrlMatch = !!config.ctrl === (e.ctrlKey || e.metaKey)
    const shiftMatch = !!config.shift === e.shiftKey
    const altMatch = !!config.alt === e.altKey
    const metaMatch = !!config.meta === e.metaKey
    return keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch
  }

  function register(config: ShortcutConfig) {
    registeredShortcuts.value.push(config)
  }

  function unregister(config: ShortcutConfig) {
    const idx = registeredShortcuts.value.findIndex(
      s =>
        s.key === config.key &&
        s.ctrl === config.ctrl &&
        s.shift === config.shift &&
        s.alt === config.alt &&
        s.meta === config.meta
    )
    if (idx > -1) registeredShortcuts.value.splice(idx, 1)
  }

  function showHelp() {
    shortcutsHelpVisible.value = true
  }

  function hideHelp() {
    shortcutsHelpVisible.value = false
  }

  function toggleHelp() {
    shortcutsHelpVisible.value = !shortcutsHelpVisible.value
  }

  function navigateTo(path: string) {
    router.push(path).catch(() => {})
  }

  function setupGlobalShortcuts(options: {
    onSearch?: () => void
    onNewTicket?: () => void
    onQuickSettle?: () => void
    onTodayView?: () => void
    onHelp?: () => void
  } = {}) {
    const configs: ShortcutConfig[] = [
      {
        key: 'k',
        ctrl: true,
        description: '打开命令面板/搜索',
        action: () => options.onSearch?.(),
      },
      {
        key: 'n',
        ctrl: true,
        description: '新建工单',
        action: () => options.onNewTicket?.(),
      },
      {
        key: 's',
        ctrl: true,
        description: '快速结算',
        action: () => options.onQuickSettle?.(),
      },
      {
        key: 't',
        ctrl: true,
        description: '今日视图（仪表盘）',
        action: () => options.onTodayView?.(),
      },
      {
        key: 'f',
        ctrl: true,
        description: '搜索',
        action: () => options.onSearch?.(),
      },
      {
        key: '?',
        shift: true,
        description: '快捷键帮助',
        action: () => options.onHelp?.() ?? toggleHelp(),
      },
    ]

    configs.forEach(register)

    const handler = (e: KeyboardEvent) => {
      if (isInputElement(e.target)) {
        if (!e.ctrlKey && !e.metaKey && !e.altKey) {
          if (e.key !== 'Escape') return
        }
        if (e.shiftKey && e.key === '?') {
          return
        }
      }

      for (const config of registeredShortcuts.value) {
        if (matchShortcut(e, config)) {
          if (config.condition && !config.condition()) continue
          e.preventDefault()
          config.action()
          return
        }
      }
    }

    globalHandler = handler

    if (!globalHandlerRegistered) {
      globalHandlerRegistered = true
      onMounted(() => {
        if (globalHandler) {
          document.addEventListener('keydown', globalHandler)
        }
      })
      onUnmounted(() => {
        if (globalHandler) {
          document.removeEventListener('keydown', globalHandler)
        }
      })
    }

    return { configs }
  }

  return {
    registeredShortcuts,
    shortcutsHelpVisible,
    register,
    unregister,
    showHelp,
    hideHelp,
    toggleHelp,
    navigateTo,
    setupGlobalShortcuts,
    isInputElement,
  }
}
