import { ref } from 'vue'

/**
 * 全局 Toast 通知 composable
 *
 * 提供 success/error/warning/info 四种类型的轻量通知。
 * 状态为全局共享，可在任意组件中使用。
 *
 * @example
 *   const { toast } = useToast()
 *   toast.success('保存成功')
 *   toast.error('网络异常', 6000)
 */

// Global toast state
const toasts = ref([])
let toastId = 0

export function useToast() {
  function show(message, type = 'info', duration = 4000) {
    const id = ++toastId
    const icons = {
      success: 'bi-check-circle-fill',
      danger: 'bi-exclamation-circle-fill',
      warning: 'bi-exclamation-triangle-fill',
      info: 'bi-info-circle-fill',
    }
    const titles = {
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

  function remove(id) {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx > -1) {
      toasts.value[idx].removing = true
      setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id)
      }, 200)
    }
  }

  const toast = {
    success: (message, duration) => show(message, 'success', duration),
    error: (message, duration) => show(message, 'danger', duration),
    warning: (message, duration) => show(message, 'warning', duration),
    info: (message, duration) => show(message, 'info', duration),
    danger: (message, duration) => show(message, 'danger', duration),
  }

  return { toasts, show, remove, toast }
}
