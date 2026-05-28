import client from './client'

/**
 * 客户 API
 *
 * 用法:
 *   import { clientApi } from '@/api/clients'
 *   const clients = await clientApi.list({ page: 1 })
 */
export const clientApi = {
  /** 客户列表 */
  list(params = {}) {
    return client.get('/clients/', { params })
  },

  /** 客户详情（含统计） */
  getByName(name) {
    return client.get('/clients/' + encodeURIComponent(name))
  },

  /** 客户画像 */
  getProfile(name) {
    return client.get('/clients/' + encodeURIComponent(name) + '/profile')
  },

  /** 客户概览（工单/设备/财务汇总） */
  getOverview(name) {
    return client.get('/clients/' + encodeURIComponent(name) + '/overview')
  },

  /** 客户等级配置 */
  getTierConfig() {
    return client.get('/clients/tier-config')
  },

  /** 创建客户 */
  create(data) {
    return client.post('/clients/', data)
  },

  /** 更新客户 */
  update(name, data) {
    return client.put('/clients/' + encodeURIComponent(name), data)
  },

  /** 删除客户 */
  delete(name) {
    return client.delete('/clients/' + encodeURIComponent(name))
  },
}
