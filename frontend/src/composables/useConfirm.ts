import { ref } from 'vue'

export interface ConfirmOptions {
  title?: string
  message?: string
  type?: 'confirm' | 'warning' | 'danger'
  confirmText?: string
  showInput?: boolean
  inputPlaceholder?: string
}

export interface ConfirmResult {
  confirmed: boolean
  inputValue: string
}

const dialogVisible = ref(false)
const dialogConfig = ref<ConfirmOptions>({
  title: '确认操作',
  message: '',
  type: 'confirm',
  confirmText: '确认',
  showInput: false,
  inputPlaceholder: '请输入确认信息',
})
let resolvePromise: ((result: ConfirmResult) => void) | null = null

export function useConfirm() {
  function confirm(message: string, options: ConfirmOptions = {}) {
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

    return new Promise<ConfirmResult>((resolve) => {
      resolvePromise = resolve
    })
  }

  function confirmDanger(message: string, options: ConfirmOptions = {}) {
    return confirm(message, { type: 'danger', ...options })
  }

  function confirmWarning(message: string, options: ConfirmOptions = {}) {
    return confirm(message, { type: 'warning', ...options })
  }

  function onConfirm(inputValue: string = '') {
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
