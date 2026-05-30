import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'

const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add CSRF token
client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const csrfToken = localStorage.getItem('bt_csrf_token')
  if (csrfToken && config.method?.toLowerCase() !== 'get') {
    config.headers = config.headers || {}
    config.headers['X-CSRF-Token'] = csrfToken
  }
  return config
})

// Response interceptor - error handling & unwrap ApiResponse<T>
client.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => {
    if (response.config?.responseType === 'blob') {
      return response
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('bt_csrf_token')
      const path = window.location.pathname
      if (!path.includes('/login')) {
        window.location.href = '/login'
      }
    }
    const msg = error.response?.data?.error || error.message || '请求失败'
    window.dispatchEvent(new CustomEvent('api-error', { detail: { message: msg } }))
    return Promise.reject(error)
  }
)

// Fetch CSRF token on startup
export async function fetchCsrfToken(): Promise<string> {
  try {
    const { data } = await axios.get<{ csrf_token?: string }>('/api/v1/csrf-token')
    const token = data.csrf_token || ''
    localStorage.setItem('bt_csrf_token', token)
    return token
  } catch {
    return ''
  }
}

export default client
