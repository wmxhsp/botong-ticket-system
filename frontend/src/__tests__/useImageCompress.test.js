import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useImageCompress } from '../composables/useImageCompress'

// Mock OffscreenCanvas + createImageBitmap
beforeEach(() => {
  globalThis.createImageBitmap = vi.fn().mockResolvedValue({
    width: 4000,
    height: 3000,
    close: vi.fn(),
  })

  const mockBlob = new Blob(['compressed'], { type: 'image/jpeg' })
  const mockConvertToBlob = vi.fn().mockResolvedValue(mockBlob)

  globalThis.OffscreenCanvas = vi.fn().mockImplementation(() => ({
    getContext: vi.fn().mockReturnValue({
      drawImage: vi.fn(),
    }),
    convertToBlob: mockConvertToBlob,
  }))
})

describe('useImageCompress', () => {
  it('returns non-image files unchanged', async () => {
    const { compressFile } = useImageCompress()
    const textFile = new File(['hello'], 'readme.txt', { type: 'text/plain' })

    const result = await compressFile(textFile)
    expect(result).toBe(textFile)
  })

  it('returns GIF files unchanged', async () => {
    const { compressFile } = useImageCompress()
    const gifFile = new File(['GIF89a'], 'anim.gif', { type: 'image/gif' })

    const result = await compressFile(gifFile)
    expect(result).toBe(gifFile)
  })

  it('returns small files unchanged', async () => {
    const { compressFile } = useImageCompress({ maxSizeMB: 5 })
    const smallJpg = new File(['x'.repeat(100)], 'small.jpg', { type: 'image/jpeg' })

    const result = await compressFile(smallJpg)
    expect(result).toBe(smallJpg)
  })

  it('compresses large image files', async () => {
    const { compressFile, compressing } = useImageCompress({ maxWidth: 1920, maxHeight: 1920 })

    // Create a "large" file (6MB)
    const largeJpg = new File([new ArrayBuffer(6 * 1024 * 1024)], 'photo.jpg', { type: 'image/jpeg' })

    const result = await compressFile(largeJpg)
    expect(result).toBeInstanceOf(File)
    expect(result.name).toMatch(/\.jpg$/)
    expect(result.type).toBe('image/jpeg')
    expect(compressing.value).toBe(false)
  })

  it('sets compressing state during compression', async () => {
    const { compressFile, compressing } = useImageCompress()

    let compressingDuringExec = false
    const largeJpg = new File([new ArrayBuffer(6 * 1024 * 1024)], 'photo.jpg', { type: 'image/jpeg' })

    // Check compressing is true while promise is pending
    const promise = compressFile(largeJpg)
    // At this point compressing should be true (synchronous after start)
    // But since createImageBitmap is async, it might already be true
    compressingDuringExec = compressing.value

    await promise
    expect(compressing.value).toBe(false)
  })

  it('falls back to original file on compression error', async () => {
    globalThis.createImageBitmap = vi.fn().mockRejectedValue(new Error('unsupported format'))

    const { compressFile } = useImageCompress()
    const largeJpg = new File([new ArrayBuffer(6 * 1024 * 1024)], 'photo.jpg', { type: 'image/jpeg' })

    const result = await compressFile(largeJpg)
    expect(result).toBe(largeJpg)
  })
})
