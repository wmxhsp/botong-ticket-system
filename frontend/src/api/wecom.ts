import client from './client'

/**
 * 企业微信推送配置 API
 */
export const wecomApi = {
  /** 获取配置 */
  getConfig(): Promise<any> {
    return client.get('/wecom/config')
  },

  /** 更新配置 */
  updateConfig(data: Record<string, any>): Promise<any> {
    return client.post('/wecom/config', data)
  },

  /** 发送测试消息 */
  sendTest(data: Record<string, any> = {}): Promise<any> {
    return client.post('/wecom/test', data)
  },
}
