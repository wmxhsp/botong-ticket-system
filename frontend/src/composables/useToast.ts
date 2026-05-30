import { ref } from 'vue'

export interface Toast {
  id: number
  message: string
  type: 'success' | 'danger' | 'warning' | 'info'
  icon: string
  title: string
  duration: number
  removing?: boolean
}

// Global toast state
const toasts = ref<Toast[]>([])
let toastId = 0

export function useToast() {
  function show(message: string, type: 'success' | 'danger' | 'warning' | 'info' = 'info', duration: number = 4000) {
    const id = ++toastId
    const icons: Record<string, string> = {
      success: 'bi-check-circle-fill',
      danger: 'bi-exclamation-circle-fill',
      warning: 'bi-exclamation-triangle-fill',
      info: 'bi-info-circle-fill',
    }
    const titles: Record<string, string> = {
      success: '成功',
      danger: '错误',
      warning: '警告',
      info: '提示',
    }

    toasts.value.push({ id, message, type, icon: icons[type] || icons.info, title: titles[type] || '', duration })

    // Auto remove
    setTimeout(() => {
      remove(id)
    }, duration)
  }

  function remove(id: number) {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx > -1) {
      toasts.value[idx].removing = true
      setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id)
      }, 200)
    }
  }

  const toast = {
    success: (message: string, duration?: number) => show(message, 'success', duration),
    error: (message: string, duration?: number) => show(message, 'danger', duration),
    warning: (message: string, duration?: number) => show(message, 'warning', duration),
    info: (message: string, duration?: number) => show(message, 'info', duration),
    danger: (message: string, duration?: number) => show(message, 'danger', duration),
  }

  return { toasts, show, remove, toast }
}
