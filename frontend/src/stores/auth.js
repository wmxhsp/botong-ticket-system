import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import client from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const checked = ref(false)
  const csrfToken = ref(null)

  const isAuthenticated = computed(() => !!user.value)

  async function fetchCsrfToken() {
    try {
      const res = await axios.get('/api/v1/csrf-token')
      csrfToken.value = res.data.csrf_token
      return csrfToken.value
    } catch {
      return null
    }
  }

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
    const headers = csrfToken.value ? { 'X-CSRF-Token': csrfToken.value } : {}
    const { data } = await axios.post('/login', { pwd: password }, { headers })
    user.value = { authenticated: true }
    checked.value = true
    return data
  }

  async function logout() {
    await axios.get('/logout')
    user.value = null
    checked.value = false
    csrfToken.value = null
  }

  return { user, checked, csrfToken, isAuthenticated, checkAuth, login, logout }
})
