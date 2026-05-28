import { ref, onMounted, onUnmounted, computed } from 'vue'

/**
 * 无限滚动 composable
 *
 * 基于 IntersectionObserver 的无限滚动加载，自动管理分页状态。
 * 适用于工单列表、客户列表等大量数据的滚动加载场景。
 *
 * @param {Object} options
 * @param {(page: number, pageSize: number) => Promise<Object>} options.fetchFn - 数据获取函数，返回 { items, total }
 * @param {(data: Object) => boolean} [options.hasMore] - 判断是否还有更多数据
 * @param {number} [options.threshold=200] - 触发加载的底部距离 (px)
 * @param {number} [options.initialPage=1] - 起始页码
 * @param {number} [options.pageSize=20] - 每页条数
 * @returns {{ items: Ref<Array>, loading: Ref<boolean>, loadingMore: Ref<boolean>, hasMore: Ref<boolean>, error: Ref<string|null>, total: Ref<number>, page: Ref<number>, targetRef: Ref<HTMLElement|null>, setTarget: (el: HTMLElement) => void, loadMore: () => void, reset: () => void }}
 */
export function useInfiniteScroll({
  fetchFn,
  hasMore = () => true,
  threshold = 200,
  initialPage = 1,
  pageSize = 20
} = {}) {
  const items = ref([])
  const page = ref(initialPage)
  const loading = ref(false)
  const loadingMore = ref(false)
  const hasMoreData = ref(true)
  const error = ref(null)
  const total = ref(0)
  const observer = ref(null)
  const targetRef = ref(null)

  const isLoading = computed(() => loading.value || loadingMore.value)

  async function fetchData(pageNum = 1, reset = false) {
    if (loading.value || loadingMore.value) return
    
    if (reset) {
      loading.value = true
      error.value = null
    } else {
      loadingMore.value = true
    }

    try {
      const data = await fetchFn(pageNum, pageSize)
      
      if (reset) {
        items.value = data.items || data.data || data.records || []
        page.value = pageNum
        hasMoreData.value = hasMore(data)
      } else {
        const newItems = data.items || data.data || data.records || []
        if (newItems.length === 0) {
          hasMoreData.value = false
        } else {
          items.value = [...items.value, ...newItems]
          page.value = pageNum
        }
      }
      
      total.value = data.total || data.count || items.value.length
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
      loadingMore.value = false
    }
  }

  function loadMore() {
    if (hasMoreData.value && !loading.value && !loadingMore.value) {
      fetchData(page.value + 1)
    }
  }

  function reset() {
    items.value = []
    page.value = initialPage
    hasMoreData.value = true
    error.value = null
    total.value = 0
    fetchData(initialPage, true)
  }

  function setupObserver() {
    if (!targetRef.value) return
    
    observer.value = new IntersectionObserver(
      (entries) => {
        const [entry] = entries
        if (entry.isIntersecting && hasMoreData.value && !loading.value && !loadingMore.value) {
          loadMore()
        }
      },
      {
        rootMargin: `${threshold}px`,
        threshold: 0.1
      }
    )

    observer.value.observe(targetRef.value)
  }

  function setTarget(element) {
    targetRef.value = element
    if (observer.value) {
      observer.value.disconnect()
    }
    setupObserver()
  }

  onMounted(() => {
    fetchData(initialPage, true)
  })

  onUnmounted(() => {
    if (observer.value) {
      observer.value.disconnect()
    }
  })

  return {
    items,
    loading,
    loadingMore,
    hasMore: hasMoreData,
    error,
    total,
    page,
    targetRef,
    setTarget,
    loadMore,
    reset
  }
}