import { ref, computed } from 'vue'

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
export function usePagination(defaultPerPage = 50) {
  const page = ref(1)
  const perPage = ref(defaultPerPage)
  const total = ref(0)

  const totalPages = computed(() =>
    Math.max(1, Math.ceil(total.value / perPage.value))
  )

  const offset = computed(() => (page.value - 1) * perPage.value)

  function setTotal(count) {
    total.value = count
  }

  function goTo(p) {
    page.value = Math.max(1, Math.min(p, totalPages.value))
  }

  function next() {
    if (page.value < totalPages.value) page.value++
  }

  function prev() {
    if (page.value > 1) page.value--
  }

  function reset() {
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
