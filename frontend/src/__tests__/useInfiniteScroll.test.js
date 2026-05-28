import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useInfiniteScroll } from '../composables/useInfiniteScroll'

// Mock Vue lifecycle hooks
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onMounted: (fn) => fn(),
    onUnmounted: vi.fn(),
  }
})

describe('useInfiniteScroll', () => {
  let mockFetchFn

  beforeEach(() => {
    mockFetchFn = vi.fn()
  })

  it('fetches initial data on mount', async () => {
    mockFetchFn.mockResolvedValue({
      items: [{ id: 1 }, { id: 2 }],
      total: 10,
    })

    const { items, total, hasMore } = useInfiniteScroll({
      fetchFn: mockFetchFn,
      pageSize: 2,
    })

    // Wait for microtask
    await vi.waitFor(() => {
      expect(items.value).toHaveLength(2)
    })
    expect(total.value).toBe(10)
    expect(hasMore.value).toBe(true)
  })

  it('appends items on loadMore', async () => {
    mockFetchFn
      .mockResolvedValueOnce({ items: [{ id: 1 }], total: 2 })
      .mockResolvedValueOnce({ items: [{ id: 2 }], total: 2 })

    const { items, loadMore } = useInfiniteScroll({
      fetchFn: mockFetchFn,
      pageSize: 1,
    })

    await vi.waitFor(() => expect(items.value).toHaveLength(1))
    await loadMore()
    expect(items.value).toHaveLength(2)
  })

  it('sets hasMore to false when no new items returned', async () => {
    mockFetchFn
      .mockResolvedValueOnce({ items: [{ id: 1 }], total: 1 })
      .mockResolvedValueOnce({ items: [], total: 1 })

    const { hasMore, loadMore } = useInfiniteScroll({
      fetchFn: mockFetchFn,
      pageSize: 10,
    })

    await vi.waitFor(() => expect(hasMore.value).toBe(true))
    await loadMore()
    expect(hasMore.value).toBe(false)
  })

  it('supports data/records key from API response', async () => {
    mockFetchFn.mockResolvedValue({
      data: [{ id: 1 }],
      total: 5,
    })

    const { items } = useInfiniteScroll({ fetchFn: mockFetchFn })
    await vi.waitFor(() => expect(items.value).toHaveLength(1))
  })

  it('resets and re-fetches', async () => {
    mockFetchFn
      .mockResolvedValueOnce({ items: [{ id: 1 }, { id: 2 }], total: 10 })
      .mockResolvedValueOnce({ items: [{ id: 99 }], total: 1 })

    const { items, reset } = useInfiniteScroll({
      fetchFn: mockFetchFn,
      pageSize: 2,
    })

    await vi.waitFor(() => expect(items.value).toHaveLength(2))
    await reset()
    await vi.waitFor(() => expect(items.value).toHaveLength(1))
  })

  it('handles fetch errors gracefully', async () => {
    mockFetchFn.mockRejectedValue(new Error('Server error'))

    const { error } = useInfiniteScroll({ fetchFn: mockFetchFn })

    await vi.waitFor(() => {
      expect(error.value).toBe('Server error')
    })
  })
})
