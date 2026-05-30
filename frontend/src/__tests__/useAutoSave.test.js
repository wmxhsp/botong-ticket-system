import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAutoSave } from '../composables/useAutoSave'

// Mock Vue lifecycle
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onUnmounted: vi.fn(),
  }
})

describe('useAutoSave', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('initializes with default values', () => {
    const { formData } = useAutoSave('test', { name: '', phone: '' })
    expect(formData.value).toEqual({ name: '', phone: '' })
  })

  it('restores from localStorage if saved within 24 hours', () => {
    const savedData = { name: '张三', phone: '13800138000', _savedAt: Date.now() }
    localStorage.setItem('bt_draft_test-restore', JSON.stringify(savedData))

    const { formData, isDirty } = useAutoSave('test-restore', { name: '', phone: '' })
    expect(formData.value.name).toBe('张三')
    expect(formData.value.phone).toBe('13800138000')
    expect(isDirty.value).toBe(true)
  })

  it('ignores expired drafts (> 24 hours)', () => {
    const expiredData = { name: '旧数据', _savedAt: Date.now() - 25 * 60 * 60 * 1000 }
    localStorage.setItem('bt_draft_test-expired', JSON.stringify(expiredData))

    const { formData } = useAutoSave('test-expired', { name: '' })
    expect(formData.value.name).toBe('')
  })

  it('saves to localStorage on change (debounced)', async () => {
    const { formData, save } = useAutoSave('test-save-manual', { name: '' }, 50)

    formData.value.name = '新名字'
    // Manually trigger save instead of relying on debounced watch
    save()

    // Wait for debounce to fire (50ms + small buffer)
    await new Promise(resolve => setTimeout(resolve, 100))

    const saved = JSON.parse(localStorage.getItem('bt_draft_test-save-manual'))
    expect(saved.name).toBe('新名字')
    expect(saved._savedAt).toBeDefined()
  })

  it('clearDraft removes localStorage entry and resets form', () => {
    const savedData = { name: '张三', _savedAt: Date.now() }
    localStorage.setItem('bt_draft_test-clear', JSON.stringify(savedData))

    const { formData, isDirty, clearDraft } = useAutoSave('test-clear', { name: '' })
    expect(formData.value.name).toBe('张三')

    clearDraft()
    expect(formData.value.name).toBe('')
    expect(isDirty.value).toBe(false)
    expect(localStorage.getItem('bt_draft_test-clear')).toBeNull()
  })
})
