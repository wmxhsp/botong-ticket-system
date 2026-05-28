import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useToast } from '../composables/useToast'

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // Reset global state between tests
    const { toasts } = useToast()
    toasts.value = []
  })

  it('creates a success toast', () => {
    const { toast, toasts } = useToast()
    toast.success('保存成功')

    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('保存成功')
    expect(toasts.value[0].type).toBe('success')
    expect(toasts.value[0].icon).toBe('bi-check-circle-fill')
  })

  it('creates an error/danger toast', () => {
    const { toast, toasts } = useToast()
    toast.error('出错了')

    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('danger')
    expect(toasts.value[0].icon).toBe('bi-exclamation-circle-fill')
  })

  it('creates warning and info toasts', () => {
    const { toast, toasts } = useToast()
    toast.warning('注意')
    toast.info('提示')

    expect(toasts.value).toHaveLength(2)
    expect(toasts.value[0].type).toBe('warning')
    expect(toasts.value[1].type).toBe('info')
  })

  it('auto-removes toast after duration', () => {
    const { show, toasts } = useToast()
    show('临时消息', 'info', 3000)

    expect(toasts.value).toHaveLength(1)

    vi.advanceTimersByTime(3000)
    // First sets removing=true, then 200ms later removes
    vi.advanceTimersByTime(250)

    expect(toasts.value).toHaveLength(0)
  })

  it('manually removes a toast', () => {
    const { show, remove, toasts } = useToast()
    show('消息1', 'info', 60000)

    const id = toasts.value[0].id
    remove(id)

    vi.advanceTimersByTime(250)
    expect(toasts.value).toHaveLength(0)
  })

  it('defaults to info type', () => {
    const { show, toasts } = useToast()
    show('默认消息')

    expect(toasts.value[0].type).toBe('info')
  })
})
