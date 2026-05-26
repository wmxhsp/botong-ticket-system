import { ref, onMounted, onUnmounted, computed } from 'vue'

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