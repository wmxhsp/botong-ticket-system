import { ref, computed, type Ref, type ComputedRef } from 'vue'

/**
 * 分页状态管理
 *
 * 管理分页参数（page/perPage/total），自动计算总页数和偏移量。
 *
 * 用法:
 *   const pagination = usePagination(20)
 *   pagination.setTotal(100)
 *   pagination.goTo(3)      // 跳转第3页
 *   pagination.next()       // 下一页
 *   pagination.prev()       // 上一页
 *   pagination.reset()      // 重置到第1页
 */
export interface UsePaginationReturn {
  page: Ref<number>
  perPage: Ref<number>
  total: Ref<number>
  totalPages: ComputedRef<number>
  offset: ComputedRef<number>
  setTotal: (count: number) => void
  goTo: (p: number) => void
  next: () => void
  prev: () => void
  reset: () => void
}

export function usePagination(defaultPerPage: number = 50): UsePaginationReturn {
  const page = ref(1)
  const perPage = ref(defaultPerPage)
  const total = ref(0)

  const totalPages = computed(() =>
    Math.max(1, Math.ceil(total.value / perPage.value))
  )

  const offset = computed(() => (page.value - 1) * perPage.value)

  function setTotal(count: number): void {
    total.value = count
  }

  function goTo(p: number): void {
    page.value = Math.max(1, Math.min(p, totalPages.value))
  }

  function next(): void {
    if (page.value < totalPages.value) page.value++
  }

  function prev(): void {
    if (page.value > 1) page.value--
  }

  function reset(): void {
    page.value = 1
    total.value = 0
  }

  return {
    page,
    perPage,
    total,
    totalPages,
    offset,
    setTotal,
    goTo,
    next,
    prev,
    reset,
  }
}
