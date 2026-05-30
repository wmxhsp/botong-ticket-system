import client from './client'

/**
 * 认证 API
 *
 * 封装用户认证相关的后端接口，包括修改密码等。
 */

export interface ChangePasswordData {
  old_password: string
  new_password: string
  confirm_password: string
}

export const authApi = {
  /** 修改密码 */
  changePassword(data: ChangePasswordData) {
    return client.post('/auth/change-password', data)
  },
}
