import client from './client'

/**
 * 设备 API
 */
export const equipmentApi = {
  /** 设备列表 */
  list(params = {}) {
    return client.get('/equipment', { params }).then(r => r.data)
  },

  /** 设备详情 */
  getById(id) {
    return client.get(`/equipment/${id}`).then(r => r.data)
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
}
