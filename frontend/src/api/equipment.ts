import client from './client'
import type { ApiResponse } from './schemas'
import type { Equipment } from '@/types'

// 设备列表查询参数
export interface EquipmentListParams {
  page?: number
  per_page?: number
  keyword?: string
  client_id?: number | string
  status?: string
}

// 设备照片
export interface EquipmentPhoto {
  id: number
  equipment_id: number | string
  url: string
  is_cover?: boolean
  uploaded_at: string
}

// 维保记录
export interface MaintenanceRecord {
  id: number
  equipment_id: number | string
  maintenance_date: string
  description: string
  technician?: string
  cost?: number
  next_maintenance_date?: string
}

// 设备组件
export interface EquipmentComponent {
  id: number
  equipment_id: number | string
  name: string
  model?: string
  serial_number?: string
  installed_date?: string
  warranty_end?: string
  notes?: string
}

// 时间线事件
export interface TimelineEvent {
  id: number
  event_type: string
  description: string
  created_at: string
  operator?: string
}

/**
 * 设备 API
 */
export const equipmentApi = {
  /** 设备列表 */
  list(params: EquipmentListParams = {}): Promise<ApiResponse<Equipment[]>> {
    return client.get('/equipment', { params })
  },

  /** 设备详情 */
  getById(id: number | string): Promise<ApiResponse<Equipment>> {
    return client.get(`/equipment/${id}`)
  },

  /** 创建设备 */
  create(data: Partial<Equipment>): Promise<ApiResponse<Equipment>> {
    return client.post('/equipment', data)
  },

  /** 更新设备 */
  update(id: number | string, data: Partial<Equipment>): Promise<ApiResponse<Equipment>> {
    return client.put(`/equipment/${id}`, data)
  },

  /** 删除设备 */
  delete(id: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/equipment/${id}`)
  },

  /** 恢复已删除设备 */
  restore(id: number | string): Promise<ApiResponse<void>> {
    return client.post(`/equipment/${id}/restore`)
  },

  /** 批量删除 */
  batchDelete(ids: Array<number | string>): Promise<ApiResponse<void>> {
    return client.post('/equipment/batch/delete', { ids })
  },

  /** 批量恢复 */
  batchRestore(ids: Array<number | string>): Promise<ApiResponse<void>> {
    return client.post('/equipment/batch/restore', { ids })
  },

  /** 批量获取QR码 */
  batchQrUrls(ids: Array<number | string>): Promise<ApiResponse<Record<string, string>>> {
    return client.post('/equipment/batch/qr-urls', { ids })
  },

  // ── 照片 ──

  /** 获取设备照片 */
  getPhotos(equipId: number | string): Promise<ApiResponse<EquipmentPhoto[]>> {
    return client.get(`/equipment/${equipId}/photos`)
  },

  /** 上传设备照片 */
  uploadPhoto(equipId: number | string, formData: FormData): Promise<ApiResponse<EquipmentPhoto>> {
    return client.post(`/equipment/${equipId}/photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 批量上传照片 */
  batchUploadPhotos(equipId: number | string, formData: FormData): Promise<ApiResponse<EquipmentPhoto[]>> {
    return client.post(`/equipment/${equipId}/photos/batch`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 删除设备照片 */
  deletePhoto(equipId: number | string, data: { photo_id: number }): Promise<ApiResponse<void>> {
    return client.delete(`/equipment/${equipId}/photos`, { data })
  },

  /** 更新照片设置（封面） */
  updatePhotoSettings(equipId: number | string, data: { photo_id: number; is_cover: boolean }): Promise<ApiResponse<void>> {
    return client.put(`/equipment/${equipId}/photos/settings`, data)
  },

  // ── 关联工单 ──

  /** 获取关联工单 */
  getTickets(equipId: number | string): Promise<ApiResponse<any[]>> {
    return client.get(`/equipment/${equipId}/tickets`)
  },

  // ── 维保 ──

  /** 维保统计 */
  getMaintenanceSummary(): Promise<ApiResponse<any>> {
    return client.get('/equipment/maintenance/summary')
  },

  /** 逾期待维保 */
  getMaintenanceOverdue(params: { page?: number; per_page?: number } = {}): Promise<ApiResponse<Equipment[]>> {
    return client.get('/equipment/maintenance/overdue', { params })
  },

  /** 记录维保 */
  recordMaintenance(equipId: number | string, data: Partial<MaintenanceRecord>): Promise<ApiResponse<void>> {
    return client.post(`/equipment/${equipId}/maintenance/record`, data)
  },

  /** 维保历史 */
  getMaintenanceHistory(equipId: number | string): Promise<ApiResponse<MaintenanceRecord[]>> {
    return client.get(`/equipment/${equipId}/maintenance/history`)
  },

  // ── 组件 ──

  /** 获取组件列表 */
  getComponents(equipId: number | string): Promise<ApiResponse<EquipmentComponent[]>> {
    return client.get(`/equipment/${equipId}/components`)
  },

  /** 添加组件 */
  addComponent(equipId: number | string, data: Partial<EquipmentComponent>): Promise<ApiResponse<EquipmentComponent>> {
    return client.post(`/equipment/${equipId}/components`, data)
  },

  /** 更新组件 */
  updateComponent(equipId: number | string, compId: number | string, data: Partial<EquipmentComponent>): Promise<ApiResponse<EquipmentComponent>> {
    return client.put(`/equipment/${equipId}/components/${compId}`, data)
  },

  /** 删除组件 */
  deleteComponent(equipId: number | string, compId: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/equipment/${equipId}/components/${compId}`)
  },

  // ── 时间线 & QR码 ──

  /** 设备时间线 */
  getTimeline(equipId: number | string): Promise<ApiResponse<TimelineEvent[]>> {
    return client.get(`/equipment/${equipId}/timeline`)
  },

  /** 生成QR码 */
  getQrCode(equipId: number | string): Promise<ApiResponse<{ qr_url: string }>> {
    return client.get(`/equipment/${equipId}/qrcode`)
  },
}
