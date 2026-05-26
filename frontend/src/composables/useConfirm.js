/**
 * 确认对话框 composable
 *
 * 替代原生 confirm()，返回 Promise，可被全局 Toast 系统接管。
 *
 * 用法:
 *   const { confirm } = useConfirm()
 *   const ok = await confirm('确认删除这条记录吗？')
 *   if (ok) { ... }
 *
 * 支持的选项:
 *   - title: 对话框标题
 *   - type: 类型 (confirm/warning/danger)
 *   - showInput: 是否显示输入框（用于危险操作二次确认）
 *   - inputPlaceholder: 输入框占位提示
 *   - confirmText: 确认按钮文字
 */
import { ref } from 'vue'

const dialogVisible = ref(false)
const dialogConfig = ref({
  title: '确认操作',
  message: '',
  type: 'confirm',
  confirmText: '确认',
  showInput: false,
  inputPlaceholder: '请输入确认信息',
})
let resolvePromise = null

export function useConfirm() {
  function confirm(message, options = {}) {
    dialogConfig.value = {
      title: '确认操作',
      message,
      type: 'confirm',
      confirmText: '确认',
      showInput: false,
      inputPlaceholder: '请输入确认信息',
      ...options,
    }
    dialogVisible.value = true
    
    return new Promise((resolve) => {
      resolvePromise = resolve
    })
  }

  function confirmDanger(message, options = {}) {
    return confirm(message, { type: 'danger', ...options })
  }

  function confirmWarning(message, options = {}) {
    return confirm(message, { type: 'warning', ...options })
  }

  function onConfirm(inputValue = '') {
    dialogVisible.value = false
    if (resolvePromise) {
      resolvePromise({ confirmed: true, inputValue })
    }
    resolvePromise = null
  }

  function onCancel() {
    dialogVisible.value = false
    if (resolvePromise) {
      resolvePromise({ confirmed: false, inputValue: '' })
    }
    resolvePromise = null
  }

  return {
    visible: dialogVisible,
    config: dialogConfig,
    confirm,
    confirmDanger,
    confirmWarning,
    onConfirm,
    onCancel,
  }
}

export { dialogVisible, dialogConfig }
