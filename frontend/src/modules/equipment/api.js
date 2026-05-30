import client from '@/api/client'

/**
 * 设备 API
 */
export const equipmentApi = {
  /** 设备列表 */
  list(params = {}) {
    return client.get('/equipment', { params })
  },

  /** 设备详情 */
  getById(id) {
    return client.get(`/equipment/${id}`)
  },

  /** 创建设备 */
  create(data) {
    return client.post('/equipment', data)
  },

  /** 更新设备 */
  update(id, data) {
    return client.put(`/equipment/${id}`, data)
  },

  /** 删除设备 */
  delete(id) {
    return client.delete(`/equipment/${id}`)
  },

  /** 恢复已删除设备 */
  restore(id) {
    return client.post(`/equipment/${id}/restore`)
  },

  /** 批量删除 */
  batchDelete(ids) {
    return client.post('/equipment/batch/delete', { ids })
  },

  /** 批量恢复 */
  batchRestore(ids) {
    return client.post('/equipment/batch/restore', { ids })
  },

  /** 批量获取QR码 */
  batchQrUrls(ids) {
    return client.post('/equipment/batch/qr-urls', { ids })
  },

  // ── 照片 ──

  /** 获取设备照片 */
  getPhotos(equipId) {
    return client.get(`/equipment/${equipId}/photos`)
  },

  /** 上传设备照片 */
  uploadPhoto(equipId, formData) {
    return client.post(`/equipment/${equipId}/photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 批量上传照片 */
  batchUploadPhotos(equipId, formData) {
    return client.post(`/equipment/${equipId}/photos/batch`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 删除设备照片 */
  deletePhoto(equipId, data) {
    return client.delete(`/equipment/${equipId}/photos`, { data })
  },

  /** 更新照片设置（封面） */
  updatePhotoSettings(equipId, data) {
    return client.put(`/equipment/${equipId}/photos/settings`, data)
  },

  // ── 关联工单 ──

  /** 获取关联工单 */
  getTickets(equipId) {
    return client.get(`/equipment/${equipId}/tickets`)
  },

  // ── 维保 ──

  /** 维保统计 */
  getMaintenanceSummary() {
    return client.get('/equipment/maintenance/summary')
  },

  /** 逾期待维保 */
  getMaintenanceOverdue(params = {}) {
    return client.get('/equipment/maintenance/overdue', { params })
  },

  /** 记录维保 */
  recordMaintenance(equipId, data) {
    return client.post(`/equipment/${equipId}/maintenance/record`, data)
  },

  /** 维保历史 */
  getMaintenanceHistory(equipId) {
    return client.get(`/equipment/${equipId}/maintenance/history`)
  },

  // ── 组件 ──

  /** 获取组件列表 */
  getComponents(equipId) {
    return client.get(`/equipment/${equipId}/components`)
  },

  /** 添加组件 */
  addComponent(equipId, data) {
    return client.post(`/equipment/${equipId}/components`, data)
  },

  /** 更新组件 */
  updateComponent(equipId, compId, data) {
    return client.put(`/equipment/${equipId}/components/${compId}`, data)
  },

  /** 删除组件 */
  deleteComponent(equipId, compId) {
    return client.delete(`/equipment/${equipId}/components/${compId}`)
  },

  // ── 时间线 & QR码 ──

  /** 设备时间线 */
  getTimeline(equipId) {
    return client.get(`/equipment/${equipId}/timeline`)
  },

  /** 生成QR码 */
  getQrCode(equipId) {
    return client.get(`/equipment/${equipId}/qrcode`)
  },
}
