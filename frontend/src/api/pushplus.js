import client from './client'

/**
 * PushPlus 推送配置 API
 */
export const pushplusApi = {
  /** 获取配置 */
  getConfig() {
    return client.get('/pushplus/config')
  },

  /** 更新配置 */
  updateConfig(data) {
    return client.post('/pushplus/config', data)
  },

  /** 发送测试消息 */
  sendTest(data = {}) {
    return client.post('/pushplus/test', data)
  },
}
