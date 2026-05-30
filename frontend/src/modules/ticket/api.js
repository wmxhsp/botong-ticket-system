import client from '@/api/client'

/**
 * 工单 API
 *
 * 封装所有工单相关的后端接口，包括 CRUD、状态流转、服务项目、
 * 配件材料、照片上传、计时器、利润统计、批量操作等。
 *
 * 所有方法返回 Promise，部分方法自动解包 r.data。
 */
export const ticketApi = {
  list(params = {}) {
    return client.get('/tickets/', { params })
  },
  getById(id) {
    return client.get(`/tickets/${id}`)
  },
  getDetail(id) {
    return client.get(`/tickets/${id}`)
  },
  create(data) {
    return client.post('/tickets/', data)
  },
  update(id, data) {
    return client.put(`/tickets/${id}`, data)
  },
  delete(id) {
    return client.delete(`/tickets/${id}`)
  },
  changeStatus(id, status) {
    return client.put(`/tickets/${id}/status`, { status })
  },
  updateStatus(id, data) {
    return client.put(`/tickets/${id}/status`, data)
  },
  confirmPayment(id, amount, method = '微信', note = '') {
    return client.post(`/tickets/${id}/pay`, { amount, method, note })
  },
  batchAction(action, ids, extra = {}) {
    return client.post('/tickets/batch', { action, ids, ...extra })
  },
  getStatusStats() {
    return client.get('/tickets/stats')
  },
  getStatusFlow() {
    return client.get('/tickets/status-flow')
  },

  getTechnicians() {
    return client.get('/technicians')
  },
  getServiceFees() {
    return client.get('/service-fees')
  },

  getServiceItems(ticketId) {
    return client.get(`/tickets/${ticketId}/service-items`)
  },
  addServiceItem(ticketId, data) {
    return client.post(`/tickets/${ticketId}/service-items`, data)
  },
  updateServiceItem(ticketId, itemId, data) {
    return client.put(`/tickets/${ticketId}/service-items/${itemId}`, data)
  },
  deleteServiceItem(ticketId, itemId) {
    return client.delete(`/tickets/${ticketId}/service-items/${itemId}`)
  },
  batchServiceItems(ticketId, items) {
    return client.post(`/tickets/${ticketId}/service-items/batch`, { items })
  },

  addMaterial(ticketId, data) {
    return client.post(`/tickets/${ticketId}/materials`, data)
  },
  deleteMaterial(ticketId, materialId) {
    return client.delete(`/tickets/${ticketId}/materials/${materialId}`)
  },
  updateMaterial(ticketId, materialId, data) {
    return client.put(`/tickets/${ticketId}/materials/${materialId}`, data)
  },
  getMaterialsTrace(ticketId) {
    return client.get(`/tickets/${ticketId}/materials/trace`)
  },

  getPhotos(ticketId) {
    return client.get(`/tickets/${ticketId}/photos`)
  },
  uploadPhotos(ticketId, formData) {
    return client.post(`/tickets/${ticketId}/photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deletePhoto(ticketId, data) {
    return client.delete(`/tickets/${ticketId}/photos`, { data })
  },

  getTimeline(ticketId) {
    return client.get(`/tickets/${ticketId}/timeline`)
  },

  linkEquipment(ticketId, equipmentId) {
    return client.post(`/tickets/${ticketId}/link-equipment`, { equipment_id: equipmentId })
  },
  unlinkEquipment(ticketId, equipmentId) {
    return client.delete(`/tickets/${ticketId}/equipment/${equipmentId}`)
  },

  startTimer(id) {
    return client.post(`/tickets/${id}/timer/start`)
  },
  stopTimer(id) {
    return client.post(`/tickets/${id}/timer/stop`)
  },
  getTimerStatus(id) {
    return client.get(`/tickets/${id}/timer/status`)
  },

  getProfit(id) {
    return client.get(`/tickets/${id}/profit`)
  },
  getProfitList(params = {}) {
    return client.get('/tickets/profit-list', { params })
  },
  setDiscount(id, data) {
    return client.put(`/tickets/${id}/discount`, data)
  },

  getHistory(id, params = {}) {
    return client.get(`/tickets/${id}/history`, { params })
  },
  getDelta(id) {
    return client.get(`/tickets/${id}/delta`)
  },
  confirmDelete(id) {
    return client.get(`/tickets/${id}/confirm-delete`)
  },
  doConfirmDelete(id, data = {}) {
    return client.post(`/tickets/${id}/confirm-delete`, data)
  },
  batchPreview(data) {
    return client.post('/tickets/batch-preview', data)
  },
  batchConfirm(data) {
    return client.post('/tickets/batch-confirm', data)
  },
  batchByFilter(data) {
    return client.post('/tickets/batch-by-filter', data)
  },
  parse(data) {
    return client.post('/tickets/parse', data)
  },
}
