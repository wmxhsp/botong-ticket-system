import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client, { fetchCsrfToken } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const checked = ref(false)

  const isAuthenticated = computed(() => !!user.value)

  function _hasAuthCookie() {
    return document.cookie.includes('bt_auth=')
  }

  async function checkAuth() {
    if (checked.value) return
    checked.value = true
    if (_hasAuthCookie()) {
      user.value = { authenticated: true }
    } else {
      user.value = null
    }
  }

  async function login(password) {
    await fetchCsrfToken()
    const result = await client.post('/login', { pwd: password })
    if (result.ok) {
      user.value = { authenticated: true }
      checked.value = true
    }
    return result
  }

  async function logout() {
    try {
      await client.get('/logout')
    } finally {
      user.value = null
      checked.value = false
      document.cookie = 'bt_auth=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'
    }
  }

  return { user, checked, isAuthenticated, checkAuth, login, logout }
})