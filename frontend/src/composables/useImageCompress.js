import { ref } from 'vue'

/**
 * 图片压缩上传 composable
 *
 * 在上传前自动压缩图片（按尺寸缩放 + 质量降低），减少上传体积。
 * 适用于工单照片、客户头像等移动端拍照场景。
 *
 * @example
 *   const { compressFile, compressing, compressAndUpload } = useImageCompress({ maxWidth: 1920, quality: 0.8 })
 *   const compressed = await compressFile(file)
 *   // or
 *   await compressAndUpload(file, (fd) => ticketApi.uploadPhotos(ticketId, fd))
 *
 * @param {Object} options
 * @param {number} [options.maxWidth=1920] - 最大宽度（px），超出等比缩放
 * @param {number} [options.maxHeight=1920] - 最大高度（px），超出等比缩放
 * @param {number} [options.quality=0.8] - JPEG 压缩质量 (0-1)
 * @param {number} [options.maxSizeMB=5] - 超过此大小 (MB) 才触发压缩
 */
export function useImageCompress({
  maxWidth = 1920,
  maxHeight = 1920,
  quality = 0.8,
  maxSizeMB = 5,
} = {}) {
  const compressing = ref(false)
  const progress = ref(0)

  /**
   * 压缩单个文件
   * @param {File} file - 原始图片文件
   * @returns {Promise<File>} 压缩后的文件（如果无需压缩则返回原文件）
   */
  async function compressFile(file) {
    // 非图片直接返回
    if (!file.type.startsWith('image/')) return file
    // GIF 不压缩（会破坏动画）
    if (file.type === 'image/gif') return file
    // 小文件不压缩
    if (file.size <= maxSizeMB * 1024 * 1024) return file

    compressing.value = true
    progress.value = 0

    try {
      const bitmap = await createImageBitmap(file)
      const { width, height } = bitmap

      // 计算缩放尺寸
      let targetWidth = width
      let targetHeight = height
      if (width > maxWidth || height > maxHeight) {
        const ratio = Math.min(maxWidth / width, maxHeight / height)
        targetWidth = Math.round(width * ratio)
        targetHeight = Math.round(height * ratio)
      }

      // Canvas 绘制
      const canvas = new OffscreenCanvas(targetWidth, targetHeight)
      const ctx = canvas.getContext('2d')
      ctx.drawImage(bitmap, 0, 0, targetWidth, targetHeight)
      bitmap.close()

      progress.value = 50

      // 导出为 Blob
      const blob = await canvas.convertToBlob({
        type: 'image/jpeg',
        quality,
      })

      progress.value = 100

      // 如果压缩后反而更大，返回原文件
      if (blob.size >= file.size) return file

      // Blob → File
      const compressedFile = new File([blob], file.name.replace(/\.\w+$/, '.jpg'), {
        type: 'image/jpeg',
        lastModified: Date.now(),
      })

      return compressedFile
    } catch {
      // 压缩失败，返回原文件
      return file
    } finally {
      compressing.value = false
      progress.value = 0
    }
  }

  /**
   * 压缩并上传
   * @param {File|File[]} files - 单个或多个文件
   * @param {(formData: FormData) => Promise} uploadFn - 上传函数
   * @returns {Promise} 上传结果
   */
  async function compressAndUpload(files, uploadFn) {
    const fileArray = Array.isArray(files) ? files : [files]
    const compressed = []

    for (const f of fileArray) {
      compressed.push(await compressFile(f))
    }

    const formData = new FormData()
    compressed.forEach((f, i) => {
      formData.append('photos', f)
      formData.append(`caption_${i}`, '')
    })

    return uploadFn(formData)
  }

  return {
    compressing,
    progress,
    compressFile,
    compressAndUpload,
  }
}
