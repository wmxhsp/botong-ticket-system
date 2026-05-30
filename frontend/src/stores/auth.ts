import { defineStore } from 'pinia'
import { ref, computed, Ref, ComputedRef } from 'vue'
import client, { fetchCsrfToken } from '@/api/client'

export interface AuthUser {
  authenticated: boolean
  name?: string
}

export interface AuthState {
  user: Ref<AuthUser | null>
  checked: Ref<boolean>
  isAuthenticated: ComputedRef<boolean>
  checkAuth: () => Promise<void>
  login: (password: string) => Promise<any>
  logout: () => Promise<void>
}

export const useAuthStore = defineStore('auth', (): AuthState => {
  const user = ref<AuthUser | null>(null)
  const checked = ref(false)

  const isAuthenticated = computed(() => !!user.value)

  function _hasAuthCookie(): boolean {
    return document.cookie.includes('bt_auth=')
  }

  async function checkAuth(): Promise<void> {
    if (checked.value) return
    checked.value = true
    if (_hasAuthCookie()) {
      user.value = { authenticated: true }
    } else {
      user.value = null
    }
  }

  async function login(password: string): Promise<any> {
    await fetchCsrfToken()
    const result = await client.post('/login', { pwd: password }) as any
    if (result.ok) {
      user.value = { authenticated: true }
      checked.value = true
    }
    return result
  }

  async function logout(): Promise<void> {
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
