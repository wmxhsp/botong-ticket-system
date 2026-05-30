import client from './client'
import type { ApiResponse, Ticket, TicketServiceItem, PaginatedResponse } from '@/types'

/**
 * 工单 API
 *
 * 封装所有工单相关的后端接口，包括 CRUD、状态流转、服务项目、
 * 配件材料、照片上传、计时器、利润统计、批量操作等。
 */

export interface TicketListParams {
  page?: number
  per_page?: number
  status?: string
  client?: string
  priority?: string
  q?: string
  start_date?: string
  end_date?: string
}

export interface TicketCreateData {
  title: string
  client: string
  service_type?: string
  description?: string
  priority?: string
  appointment_at?: string
}

export interface ServiceItemData {
  technician_name?: string
  service_name?: string
  billing_type?: 'hourly' | 'daily' | 'package'
  hours?: number
  days?: number
  package_fee?: number
  unit_price?: number
  cost_price?: number
}

export interface MaterialData {
  goods_id?: number
  goods_name?: string
  quantity?: number
  unit_price?: number
  cost_price?: number
}

export interface BatchActionData {
  action: string
  ids: number[]
  [key: string]: any
}

export const ticketApi = {
  list(params: TicketListParams = {}): Promise<ApiResponse<PaginatedResponse<Ticket>>> {
    return client.get('/tickets/', { params })
  },

  getById(id: number | string): Promise<ApiResponse<Ticket>> {
    return client.get(`/tickets/${id}`)
  },

  getDetail(id: number | string): Promise<ApiResponse<Ticket>> {
    return client.get(`/tickets/${id}`)
  },

  create(data: TicketCreateData): Promise<ApiResponse<Ticket>> {
    return client.post('/tickets/', data)
  },

  update(id: number | string, data: Partial<TicketCreateData>): Promise<ApiResponse<Ticket>> {
    return client.put(`/tickets/${id}`, data)
  },

  delete(id: number | string): Promise<ApiResponse<null>> {
    return client.delete(`/tickets/${id}`)
  },

  changeStatus(id: number | string, status: string): Promise<ApiResponse<Ticket>> {
    return client.put(`/tickets/${id}/status`, { status })
  },

  updateStatus(id: number | string, data: { status: string; note?: string }): Promise<ApiResponse<Ticket>> {
    return client.put(`/tickets/${id}/status`, data)
  },

  confirmPayment(id: number | string, amount: number, method: string = '微信', note: string = ''): Promise<ApiResponse<Ticket>> {
    return client.post(`/tickets/${id}/pay`, { amount, method, note })
  },

  batchAction(action: string, ids: (number | string)[], extra: Record<string, any> = {}): Promise<ApiResponse<null>> {
    return client.post('/tickets/batch', { action, ids, ...extra })
  },

  getStatusStats(): Promise<ApiResponse<Record<string, number>>> {
    return client.get('/tickets/stats')
  },

  getStatusFlow(): Promise<ApiResponse<Record<string, any>>> {
    return client.get('/tickets/status-flow')
  },

  getTechnicians(): Promise<ApiResponse<any[]>> {
    return client.get('/technicians')
  },

  getServiceFees(): Promise<ApiResponse<any[]>> {
    return client.get('/service-fees')
  },

  getServiceItems(ticketId: number | string): Promise<ApiResponse<TicketServiceItem[]>> {
    return client.get(`/tickets/${ticketId}/service-items`)
  },

  addServiceItem(ticketId: number | string, data: ServiceItemData): Promise<ApiResponse<TicketServiceItem>> {
    return client.post(`/tickets/${ticketId}/service-items`, data)
  },

  updateServiceItem(ticketId: number | string, itemId: number | string, data: ServiceItemData): Promise<ApiResponse<TicketServiceItem>> {
    return client.put(`/tickets/${ticketId}/service-items/${itemId}`, data)
  },

  deleteServiceItem(ticketId: number | string, itemId: number | string): Promise<ApiResponse<null>> {
    return client.delete(`/tickets/${ticketId}/service-items/${itemId}`)
  },

  batchServiceItems(ticketId: number | string, items: ServiceItemData[]): Promise<ApiResponse<TicketServiceItem[]>> {
    return client.post(`/tickets/${ticketId}/service-items/batch`, { items })
  },

  addMaterial(ticketId: number | string, data: MaterialData): Promise<ApiResponse<any>> {
    return client.post(`/tickets/${ticketId}/materials`, data)
  },

  deleteMaterial(ticketId: number | string, materialId: number | string): Promise<ApiResponse<null>> {
    return client.delete(`/tickets/${ticketId}/materials/${materialId}`)
  },

  updateMaterial(ticketId: number | string, materialId: number | string, data: MaterialData): Promise<ApiResponse<any>> {
    return client.put(`/tickets/${ticketId}/materials/${materialId}`, data)
  },

  getMaterialsTrace(ticketId: number | string): Promise<ApiResponse<any[]>> {
    return client.get(`/tickets/${ticketId}/materials/trace`)
  },

  getPhotos(ticketId: number | string): Promise<ApiResponse<any[]>> {
    return client.get(`/tickets/${ticketId}/photos`)
  },

  uploadPhotos(ticketId: number | string, formData: FormData): Promise<ApiResponse<any[]>> {
    return client.post(`/tickets/${ticketId}/photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  deletePhoto(ticketId: number | string, data: { filename: string }): Promise<ApiResponse<null>> {
    return client.delete(`/tickets/${ticketId}/photos`, { data })
  },

  getTimeline(ticketId: number | string): Promise<ApiResponse<any[]>> {
    return client.get(`/tickets/${ticketId}/timeline`)
  },

  linkEquipment(ticketId: number | string, equipmentId: number | string): Promise<ApiResponse<null>> {
    return client.post(`/tickets/${ticketId}/link-equipment`, { equipment_id: equipmentId })
  },

  unlinkEquipment(ticketId: number | string, equipmentId: number | string): Promise<ApiResponse<null>> {
    return client.delete(`/tickets/${ticketId}/equipment/${equipmentId}`)
  },

  startTimer(id: number | string): Promise<ApiResponse<any>> {
    return client.post(`/tickets/${id}/timer/start`)
  },

  stopTimer(id: number | string): Promise<ApiResponse<any>> {
    return client.post(`/tickets/${id}/timer/stop`)
  },

  getTimerStatus(id: number | string): Promise<ApiResponse<any>> {
    return client.get(`/tickets/${id}/timer/status`)
  },

  getProfit(id: number | string): Promise<ApiResponse<any>> {
    return client.get(`/tickets/${id}/profit`)
  },

  getProfitList(params: TicketListParams = {}): Promise<ApiResponse<PaginatedResponse<any>>> {
    return client.get('/tickets/profit-list', { params })
  },

  setDiscount(id: number | string, data: { discount_type: string; discount_value: number }): Promise<ApiResponse<Ticket>> {
    return client.put(`/tickets/${id}/discount`, data)
  },

  getHistory(id: number | string, params: { page?: number; per_page?: number } = {}): Promise<ApiResponse<PaginatedResponse<any>>> {
    return client.get(`/tickets/${id}/history`, { params })
  },

  getDelta(id: number | string): Promise<ApiResponse<any>> {
    return client.get(`/tickets/${id}/delta`)
  },

  confirmDelete(id: number | string): Promise<ApiResponse<any>> {
    return client.get(`/tickets/${id}/confirm-delete`)
  },

  doConfirmDelete(id: number | string, data: Record<string, any> = {}): Promise<ApiResponse<null>> {
    return client.post(`/tickets/${id}/confirm-delete`, data)
  },

  batchPreview(data: BatchActionData): Promise<ApiResponse<any>> {
    return client.post('/tickets/batch-preview', data)
  },

  batchConfirm(data: BatchActionData): Promise<ApiResponse<null>> {
    return client.post('/tickets/batch-confirm', data)
  },

  batchByFilter(data: { filter: Record<string, any>; action: string; action_params?: Record<string, any> }): Promise<ApiResponse<null>> {
    return client.post('/tickets/batch-by-filter', data)
  },

  parse(data: { text: string }): Promise<ApiResponse<any>> {
    return client.post('/tickets/parse', data)
  },
}
