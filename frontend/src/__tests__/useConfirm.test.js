import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useConfirm } from '../composables/useConfirm'

describe('useConfirm', () => {
  it('shows dialog and resolves true on confirm', async () => {
    const { confirm, visible, config, onConfirm } = useConfirm()

    const promise = confirm('确认删除？')

    expect(visible.value).toBe(true)
    expect(config.value.message).toBe('确认删除？')

    onConfirm()

    const result = await promise
    expect(result.confirmed).toBe(true)
    expect(visible.value).toBe(false)
  })

  it('resolves false on cancel', async () => {
    const { confirm, onCancel } = useConfirm()

    const promise = confirm('确认吗？')
    onCancel()

    const result = await promise
    expect(result.confirmed).toBe(false)
  })

  it('accepts custom options', async () => {
    const { confirm, config, onConfirm } = useConfirm()

    const promise = confirm('危险操作', {
      title: '警告',
      type: 'danger',
      confirmText: '删除',
    })

    expect(config.value.title).toBe('警告')
    expect(config.value.type).toBe('danger')
    expect(config.value.confirmText).toBe('删除')

    onConfirm()
    await promise
  })

  it('confirmDanger sets type to danger', async () => {
    const { confirmDanger, config, onConfirm } = useConfirm()

    confirmDanger('确定？')
    expect(config.value.type).toBe('danger')

    onConfirm()
  })

  it('confirmWarning sets type to warning', async () => {
    const { confirmWarning, config, onConfirm } = useConfirm()

    confirmWarning('注意？')
    expect(config.value.type).toBe('warning')

    onConfirm()
  })

  it('passes inputValue on confirm with input', async () => {
    const { confirm, onConfirm } = useConfirm()

    const promise = confirm('输入确认', { showInput: true })
    onConfirm('DELETE')

    const result = await promise
    expect(result.inputValue).toBe('DELETE')
  })
})
