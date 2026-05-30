import { ref, readonly, type Ref, type DeepReadonly } from 'vue'

/**
 * 通用 API 请求状态管理
 *
 * 包装异步 API 调用，自动管理 loading/error/data 状态。
 * 内置 AbortController，快速连续调用时自动取消前一次请求。
 *
 * 用法:
 *   const { data, loading, error, execute } = useApi(ticketApi.getById)
 *   await execute(123)    // 自动设置 loading=true, 完成后重置
 *   data.value            // API 返回的 data
 *   loading.value         // 布尔值
 */

export interface UseApiReturn<T> {
  data: DeepReadonly<Ref<T | null>>
  loading: DeepReadonly<Ref<boolean>>
  error: DeepReadonly<Ref<string | null>>
  execute: (...args: any[]) => Promise<any>
  reset: () => void
}

export function useApi<T = any>(apiFn: (...args: any[]) => Promise<any>): UseApiReturn<T> {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  let abortController: AbortController | null = null

  async function execute(...args: any[]) {
    // Cancel previous in-flight request
    abortController?.abort()
    abortController = new AbortController()

    loading.value = true
    error.value = null
    try {
      // Pass signal as last arg if the API function accepts an options object
      const lastArg = args[args.length - 1]
      if (lastArg && typeof lastArg === 'object' && !Array.isArray(lastArg)) {
        lastArg.signal = abortController.signal
      } else {
        args.push({ signal: abortController.signal })
      }
      const result = await apiFn(...args)
      data.value = result?.data ?? result ?? null
      return result
    } catch (e: any) {
      if (e.name === 'AbortError') return  // Silently ignore cancelled requests
      const message = e.response?.data?.error || e.message || '请求失败'
      error.value = message
      throw e
    } finally {
      loading.value = false
    }
  }

  /** 重置状态 */
  function reset() {
    data.value = null
    loading.value = false
    error.value = null
  }

  return {
    data: readonly(data) as DeepReadonly<Ref<T | null>>,
    loading: readonly(loading) as DeepReadonly<Ref<boolean>>,
    error: readonly(error) as DeepReadonly<Ref<string | null>>,
    execute,
    reset,
  }
}
