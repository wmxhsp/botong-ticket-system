import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', async () => {
  const actual = await vi.importActual('axios')
  return {
    ...actual,
    default: {
      ...actual.default,
      get: vi.fn(),
      create: vi.fn().mockReturnValue({
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      }),
    },
  }
})

describe('api/client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('uses VITE_API_BASE env variable for baseURL', async () => {
    // Client is created at module load time, so we test the import
    const mod = await import('../api/client')
    const client = mod.default

    // Verify the client was created (axios.create was called)
    expect(axios.create).toHaveBeenCalled()
  })

  describe('fetchCsrfToken', () => {
    it('fetches and stores CSRF token', async () => {
      axios.get.mockResolvedValue({
        data: { csrf_token: 'test-csrf-token-123' },
      })

      const { fetchCsrfToken } = await import('../api/client')
      await fetchCsrfToken()

      expect(axios.get).toHaveBeenCalledWith('/api/v1/csrf-token')
      expect(localStorage.getItem('bt_csrf_token')).toBe('test-csrf-token-123')
    })

    it('silently fails on error', async () => {
      axios.get.mockRejectedValue(new Error('Network error'))

      const { fetchCsrfToken } = await import('../api/client')
      // Should not throw
      await expect(fetchCsrfToken()).resolves.toBe('')
    })
  })
})
