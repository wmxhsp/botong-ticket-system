import client from '@/api/client'

export const nlApi = {
  command(data) { return client.post('/nl/command', data) }
}
