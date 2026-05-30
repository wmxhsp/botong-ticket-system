import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { validateResponse, ApiResponseSchema, type ApiResponse } from './schemas'

// 扩展AxiosRequestConfig以支持自定义属性
interface ExtendedAxiosRequestConfig extends AxiosRequestConfig {
  _endpoint?: string
}

const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 存储每个 API 端点的验证 Schema（可选）
export const apiSchemas: Record<string, any> = {}

// 设置端点验证 Schema 的工具函数
export function setApiSchema(endpoint: string, schema: any): void {
  apiSchemas[endpoint] = schema
}

// Request interceptor - add CSRF token
client.interceptors.request.use((config: ExtendedAxiosRequestConfig) => {
  const csrfToken = localStorage.getItem('bt_csrf_token')
  if (csrfToken && config.method && config.method !== 'get') {
    config.headers['X-CSRF-Token'] = csrfToken
  }
  return config
})

// Response interceptor - error handling & validation
client.interceptors.response.use(
  (response: AxiosResponse) => {
    if (response.config?.responseType === 'blob') {
      return response
    }
    const data = response.data
    
    // 验证响应格式
    const endpoint = response.config.url
    if (endpoint && apiSchemas[endpoint]) {
      validateResponse(apiSchemas[endpoint], data)
    } else {
      // 通用验证
      validateResponse(ApiResponseSchema, data)
    }
    
    return data
  },
  (error: any) => {
    if (error.response?.status === 401) {
      // 清除认证状态并跳转登录页
      localStorage.removeItem('bt_csrf_token')
      const path = window.location.pathname
      if (!path.includes('/login')) {
        window.location.href = '/login'
      }
    }
    // Dispatch custom event for toast notifications
    const msg = error.response?.data?.error || error.message || '请求失败'
    window.dispatchEvent(new CustomEvent('api-error', { detail: { message: msg } }))
    return Promise.reject(error)
  }
)

// Fetch CSRF token on startup
export async function fetchCsrfToken(): Promise<string> {
  try {
    const { data } = await axios.get<{ csrf_token: string }>('/api/v1/csrf-token')
    const token = data.csrf_token || ''
    localStorage.setItem('bt_csrf_token', token)
    return token
  } catch {
    return ''
  }
}

export default client
