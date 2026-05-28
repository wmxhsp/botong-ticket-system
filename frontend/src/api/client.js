import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add CSRF token
client.interceptors.request.use((config) => {
  const csrfToken = localStorage.getItem('bt_csrf_token')
  if (csrfToken && config.method !== 'get') {
    config.headers['X-CSRF-Token'] = csrfToken
  }
  return config
})

// Response interceptor - error handling
client.interceptors.response.use(
  (response) => {
    if (response.config?.responseType === 'blob') {
      return response
    }
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('bt_auth_token')
      window.location.href = '/login'
    }
    // Dispatch custom event for toast notifications
    const msg = error.response?.data?.error || error.message || '请求失败'
    window.dispatchEvent(new CustomEvent('api-error', { detail: { message: msg } }))
    return Promise.reject(error)
  }
)

// Fetch CSRF token on startup
export async function fetchCsrfToken() {
  try {
    const { data } = await axios.get('/api/v1/csrf-token')
    const token = data.csrf_token || ''
    localStorage.setItem('bt_csrf_token', token)
    return token
  } catch {
    return ''
  }
}

export default client
