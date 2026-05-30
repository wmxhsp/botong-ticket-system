import { ref, watch } from 'vue'

/**
 * 通用防抖 Hook
 * 
 * @param delay - 防抖延迟时间（毫秒），默认300ms
 * @returns 防抖后的值和设置函数
 * 
 * @example
 * ```ts
 * const { debouncedValue, setValue } = useDebounce(300)
 * 
 * // 在输入事件中调用
 * onInput((e) => {
 *   setValue(e.target.value)
 * })
 * 
 * // 监听防抖后的值
 * watch(debouncedValue, (newValue) => {
 *   performSearch(newValue)
 * })
 * ```
 */
export function useDebounce(delay: number = 300) {
  const debouncedValue = ref<string>('')
  let timer: ReturnType<typeof setTimeout> | null = null
  
  /**
   * 设置新的值（会触发防抖）
   */
  function setValue(value: string) {
    if (timer) {
      clearTimeout(timer)
    }
    
    timer = setTimeout(() => {
      debouncedValue.value = value
      timer = null
    }, delay)
  }
  
  /**
   * 立即设置值（不防抖）
   */
  function setValueImmediate(value: string) {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    debouncedValue.value = value
  }
  
  /**
   * 取消当前的防抖
   */
  function cancel() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }
  
  /**
   * 刷新防抖计时器（立即执行）
   */
  function flush() {
    if (timer) {
      clearTimeout(timer)
      debouncedValue.value = ''
      timer = null
    }
  }
  
  return {
    debouncedValue,
    setValue,
    setValueImmediate,
    cancel,
    flush
  }
}

/**
 * 防抖函数包装器
 * 
 * @param fn - 要防抖的函数
 * @param delay - 防抖延迟时间（毫秒），默认300ms
 * @returns 防抖后的函数
 * 
 * @example
 * ```ts
 * const debouncedSearch = useDebounceFn(searchApi.search, 300)
 * 
 * // 调用时会自动防抖
 * debouncedSearch(keyword)
 * ```
 */
export function useDebounceFn<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null
  
  return (...args: Parameters<T>) => {
    if (timer) {
      clearTimeout(timer)
    }
    
    timer = setTimeout(() => {
      fn(...args)
      timer = null
    }, delay)
  }
}
