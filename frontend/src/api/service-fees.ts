import client from './client'
import type { ApiResponse } from './schemas'
import type { ServiceFee } from '@/types'
import type { ServiceFeeItem } from '@/types/api'

export const serviceFeeApi = {
  list(params: Record<string, any> = {}): Promise<ApiResponse<ServiceFee[]>> {
    return client.get('/service-fees/', { params })
  },
  getTypes(): Promise<ApiResponse<any>> {
    return client.get('/service-fees/types')
  },
  create(data: Partial<ServiceFeeItem>): Promise<ApiResponse<ServiceFeeItem>> {
    return client.post('/service-fees/', data)
  },
  update(id: number | string, data: Partial<ServiceFeeItem>): Promise<ApiResponse<ServiceFeeItem>> {
    return client.put(`/service-fees/${id}`, data)
  },
  delete(id: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/service-fees/${id}`)
  },
}
