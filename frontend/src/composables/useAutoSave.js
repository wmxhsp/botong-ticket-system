import { ref, watch, onUnmounted } from 'vue'

/**
 * Auto-save composable for form drafts
 *
 * Automatically saves form data to localStorage with debounce,
 * and restores on mount. Prevents data loss on accidental navigation.
 *
 * Usage:
 *   const { formData, isDirty, lastSaved, clearDraft } = useAutoSave('ticket-create', { client: '', content: '' })
 *   // formData is a ref that auto-saves on change
 *   // On mount, it tries to restore from localStorage
 *
 * @param {string} key - Unique storage key
 * @param {object} defaultValue - Default form values
 * @param {number} debounceMs - Debounce interval (default 1000ms)
 */
export function useAutoSave(key, defaultValue = {}, debounceMs = 1000) {
  const storageKey = `bt_draft_${key}`
  const formData = ref({ ...defaultValue })
  const isDirty = ref(false)
  const lastSaved = ref(null)
  let saveTimer = null

  // Restore from localStorage
  function restore() {
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        const parsed = JSON.parse(saved)
        const savedTime = parsed._savedAt
        // Only restore if saved within last 24 hours
        if (savedTime && (Date.now() - savedTime) < 24 * 60 * 60 * 1000) {
          const { _savedAt, ...values } = parsed
          formData.value = { ...defaultValue, ...values }
          isDirty.value = true
          return true
        }
      }
    } catch {
      // Silently fail
    }
    return false
  }

  // Save to localStorage
  function save() {
    try {
      const data = { ...formData.value, _savedAt: Date.now() }
      localStorage.setItem(storageKey, JSON.stringify(data))
      lastSaved.value = new Date()
      isDirty.value = false
    } catch {
      // Storage full or unavailable
    }
  }

  // Clear draft
  function clearDraft() {
    try {
      localStorage.removeItem(storageKey)
    } catch {
      // ignore
    }
    formData.value = { ...defaultValue }
    isDirty.value = false
    lastSaved.value = null
  }

  // Auto-save with debounce
  watch(formData, () => {
    isDirty.value = true
    clearTimeout(saveTimer)
    saveTimer = setTimeout(save, debounceMs)
  }, { deep: true })

  onUnmounted(() => {
    clearTimeout(saveTimer)
  })

  // Try to restore on init
  restore()

  return {
    formData,
    isDirty,
    lastSaved,
    clearDraft,
    save,
  }
}
