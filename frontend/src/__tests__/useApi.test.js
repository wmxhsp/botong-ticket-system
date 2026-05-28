import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useApi } from '../composables/useApi'

describe('useApi', () => {
  let mockFn

  beforeEach(() => {
    mockFn = vi.fn()
  })

  it('sets loading during execution and data on success', async () => {
    mockFn.mockResolvedValue({ data: { id: 1, name: '测试' } })
    const { data, loading, execute } = useApi(mockFn)

    const promise = execute()
    expect(loading.value).toBe(true)

    await promise
    expect(loading.value).toBe(false)
    expect(data.value).toEqual({ id: 1, name: '测试' })
  })

  it('extracts data from response.data', async () => {
    mockFn.mockResolvedValue({ data: { id: 2 } })
    const { data, execute } = useApi(mockFn)

    await execute()
    expect(data.value).toEqual({ id: 2 })
  })

  it('uses result directly if no .data property', async () => {
    mockFn.mockResolvedValue({ id: 3 })
    const { data, execute } = useApi(mockFn)

    await execute()
    expect(data.value).toEqual({ id: 3 })
  })

  it('sets error on failure', async () => {
    mockFn.mockRejectedValue(new Error('网络异常'))
    const { error, execute } = useApi(mockFn)

    await expect(execute()).rejects.toThrow('网络异常')
    expect(error.value).toBe('网络异常')
  })

  it('extracts error from response.data.error', async () => {
    const err = new Error('fail')
    err.response = { data: { error: '权限不足' } }
    mockFn.mockRejectedValue(err)

    const { error, execute } = useApi(mockFn)
    await expect(execute()).rejects.toThrow()
    expect(error.value).toBe('权限不足')
  })

  it('cancels previous request when called again rapidly', async () => {
    let callCount = 0
    mockFn.mockImplementation(async (arg, opts) => {
      callCount++
      // Simulate async work — check if signal was aborted
      await new Promise((resolve) => setTimeout(resolve, 50))
      if (opts?.signal?.aborted) throw new DOMException('Aborted', 'AbortError')
      return { data: `result-${callCount}` }
    })

    const { data, execute } = useApi(mockFn)

    // Fire two rapid calls
    execute('first')
    await new Promise((r) => setTimeout(r, 10))
    await execute('second')

    // Only the second call should complete
    expect(data.value).toBe('result-2')
  })

  it('silently ignores AbortError', async () => {
    const err = new DOMException('Aborted', 'AbortError')
    mockFn.mockRejectedValue(err)

    const { error, execute } = useApi(mockFn)
    const result = await execute()
    expect(result).toBeUndefined()
    expect(error.value).toBeNull()
  })

  it('passes signal to API function via options object', async () => {
    let receivedSignal = null
    mockFn.mockImplementation(async (id, opts) => {
      receivedSignal = opts?.signal
      return { data: { id } }
    })

    const { execute } = useApi(mockFn)
    await execute(123, {})
    expect(receivedSignal).toBeInstanceOf(AbortSignal)
  })

  it('resets state', async () => {
    mockFn.mockResolvedValue({ data: 'hello' })
    const { data, loading, error, execute, reset } = useApi(mockFn)

    await execute()
    expect(data.value).toBe('hello')

    reset()
    expect(data.value).toBeNull()
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })
})
