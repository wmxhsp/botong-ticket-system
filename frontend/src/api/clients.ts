import client from './client'
import type { ApiResponse, Client, PaginatedResponse } from '@/types'

/**
 * 客户 API
 *
 * 封装所有客户相关的后端接口，包括 CRUD、画像、概览等。
 */

export interface ClientListParams {
  page?: number
  per_page?: number
  q?: string
  type?: string
  status?: string
}

export interface ClientCreateData {
  name: string
  phone?: string
  email?: string
  address?: string
  notes?: string
  payment_terms?: number
  tier?: string
}

export const clientApi = {
  /** 客户列表 */
  list(params: ClientListParams = {}): Promise<ApiResponse<PaginatedResponse<Client>>> {
    return client.get('/clients/', { params })
  },

  /** 客户详情（含统计） */
  getByName(name: string): Promise<ApiResponse<Client>> {
    return client.get('/clients/' + encodeURIComponent(name))
  },

  /** 客户画像 */
  getProfile(name: string): Promise<ApiResponse<any>> {
    return client.get('/clients/' + encodeURIComponent(name) + '/profile')
  },

  /** 客户概览（工单/设备/财务汇总） */
  getOverview(name: string): Promise<ApiResponse<any>> {
    return client.get('/clients/' + encodeURIComponent(name) + '/overview')
  },

  /** 客户等级配置 */
  getTierConfig(): Promise<ApiResponse<any>> {
    return client.get('/clients/tier-config')
  },

  /** 创建客户 */
  create(data: ClientCreateData): Promise<ApiResponse<Client>> {
    return client.post('/clients/', data)
  },

  /** 更新客户 */
  update(name: string, data: Partial<ClientCreateData>): Promise<ApiResponse<Client>> {
    return client.put('/clients/' + encodeURIComponent(name), data)
  },

  /** 删除客户 */
  delete(name: string): Promise<ApiResponse<null>> {
    return client.delete('/clients/' + encodeURIComponent(name))
  },
}
