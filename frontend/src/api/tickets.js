import client from './client'

export const ticketApi = {
  list(params = {}) {
    return client.get('/tickets/', { params }).then(r => r.data)
  },
  getById(id) {
    return client.get(`/tickets/${id}`).then(r => r.data)
  },
  getDetail(id) {
    return client.get(`/tickets/${id}`).then(r => r.data)
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
    return client.get('/tickets/stats').then(r => r.data)
  },
  getStatusFlow() {
    return client.get('/tickets/status-flow').then(r => r.data)
  },

  getTechnicians() {
    return client.get('/technicians').then(r => r.data)
  },
  getServiceFees() {
    return client.get('/service-fees').then(r => r.data)
  },

  getServiceItems(ticketId) {
    return client.get(`/tickets/${ticketId}/service-items`).then(r => r.data)
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
    return client.get(`/tickets/${ticketId}/materials/trace`).then(r => r.data)
  },

  getPhotos(ticketId) {
    return client.get(`/tickets/${ticketId}/photos`).then(r => r.data)
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
    return client.get(`/tickets/${ticketId}/timeline`).then(r => r.data)
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
    return client.get(`/tickets/${id}/timer/status`).then(r => r.data)
  },

  getProfit(id) {
    return client.get(`/tickets/${id}/profit`).then(r => r.data)
  },
  getProfitList(params = {}) {
    return client.get('/tickets/profit-list', { params }).then(r => r.data)
  },
  setDiscount(id, data) {
    return client.put(`/tickets/${id}/discount`, data)
  },

  getHistory(id, params = {}) {
    return client.get(`/tickets/${id}/history`, { params }).then(r => r.data)
  },
  getDelta(id) {
    return client.get(`/tickets/${id}/delta`).then(r => r.data)
  },
  confirmDelete(id) {
    return client.get(`/tickets/${id}/confirm-delete`).then(r => r.data)
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
