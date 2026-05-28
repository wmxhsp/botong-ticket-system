import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client, { fetchCsrfToken } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const checked = ref(false)

  const isAuthenticated = computed(() => !!user.value)

  async function checkAuth() {
    if (checked.value) return
    checked.value = true
    try {
      await client.get('/health')
      user.value = { authenticated: true }
    } catch {
      user.value = null
    }
  }

  async function login(password) {
    await fetchCsrfToken()
    const result = await client.post('/login', { pwd: password })
    user.value = { authenticated: true }
    checked.value = true
    return result
  }

  async function logout() {
    await client.get('/logout')
    user.value = null
    checked.value = false
  }

  return { user, checked, isAuthenticated, checkAuth, login, logout }
})
