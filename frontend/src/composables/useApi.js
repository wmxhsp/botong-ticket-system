import { ref, readonly } from 'vue'

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
export function useApi(apiFn) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)
  let abortController = null

  async function execute(...args) {
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
    } catch (e) {
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
    data: readonly(data),
    loading: readonly(loading),
    error: readonly(error),
    execute,
    reset,
  }
}
