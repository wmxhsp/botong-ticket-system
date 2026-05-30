import client from './client'
import type { ApiResponse } from '@/types'

export interface SearchParams {
  q?: string
  type?: string
  limit?: number
}

export const searchApi = {
  search(params: SearchParams = {}): Promise<ApiResponse<{ tickets?: any[]; clients?: any[] }>> {
    return client.get('/search', { params })
  },
}
