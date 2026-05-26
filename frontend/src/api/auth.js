import client from './client'

export const authApi = {
  changePassword(data) {
    return client.post('/auth/change-password', data)
  },
}
