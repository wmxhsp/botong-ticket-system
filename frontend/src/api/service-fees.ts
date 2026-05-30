import client from './client'
import type { ApiResponse } from './schemas'
import type { ServiceFee } from '@/types'

export const serviceFeeApi = {
  list(params: Record<string, any> = {}) {
    return client.get('/service-fees/', { params })
  },
  getTypes() {
    return client.get('/service-fees/types')
  },
  create(data: any) {
    return client.post('/service-fees/', data)
  },
  update(id: number | string, data: any) {
    return client.put(`/service-fees/${id}`, data)
  },
  delete(id: number | string) {
    return client.delete(`/service-fees/${id}`)
  },
}
