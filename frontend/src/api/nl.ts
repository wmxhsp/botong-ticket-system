import client from '@/api/client'
import type { ApiResponse } from './schemas'

export const nlApi = {
  command(data) { return client.post('/nl/command', data) }
}
