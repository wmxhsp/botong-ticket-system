import client from './client'
import type { ApiResponse } from './schemas'

// 工单模板
export interface TicketTemplate {
  id: number | string
  name: string
  description?: string
  content?: string
  created_at?: string
}

// 自动化规则
export interface AutomationRule {
  id: number | string
  name: string
  event: string
  conditions: any[]
  actions: any[]
  enabled: boolean
  created_at?: string
}

/**
 * 工具 API — 导出 / 模板 / 规则 / 导入 / 每日摘要
 */
export const toolsApi = {
  // ── 导出 ──

  /** 导出工单 CSV */
  exportTickets(params: Record<string, any> = {}): Promise<Blob> {
    return client.get('/export/tickets', { params, responseType: 'blob' })
  },

  /** 导出客户 CSV */
  exportClients(): Promise<Blob> {
    return client.get('/export/clients', { responseType: 'blob' })
  },

  /** 导出财务 CSV */
  exportFinance(): Promise<Blob> {
    return client.get('/export/finance', { responseType: 'blob' })
  },

  /** 导出利润 CSV */
  exportProfit(): Promise<Blob> {
    return client.get('/export/profit', { responseType: 'blob' })
  },

  /** 导出客户对账单 */
  exportClientStatement(clientName: string, params: Record<string, any> = {}): Promise<Blob> {
    return client.get(`/export/statement/client/${encodeURIComponent(clientName)}`, { params, responseType: 'blob' })
  },

  /** 导出供应商对账单 */
  exportSupplierStatement(supplierId: number | string): Promise<Blob> {
    return client.get(`/export/statement/supplier/${supplierId}`, { responseType: 'blob' })
  },

  /** 导出设备 CSV */
  exportEquipment(): Promise<Blob> {
    return client.get('/export/equipment', { responseType: 'blob' })
  },

  // ── 报告 ──

  /** 生成报告 */
  generateReport(data: any): Promise<ApiResponse<any>> {
    return client.post('/report/generate', data)
  },

  /** 每日摘要 */
  getDailyDigest(): Promise<ApiResponse<any>> {
    return client.get('/daily-digest')
  },

  // ── 工单模板 ──

  /** 模板列表 */
  listTemplates(): Promise<ApiResponse<TicketTemplate[]>> {
    return client.get('/ticket-templates')
  },

  /** 创建模板 */
  createTemplate(data: Partial<TicketTemplate>): Promise<ApiResponse<TicketTemplate>> {
    return client.post('/ticket-templates', data)
  },

  /** 获取模板详情 */
  getTemplate(id: number | string): Promise<ApiResponse<TicketTemplate>> {
    return client.get(`/ticket-templates/${id}`)
  },

  /** 更新模板 */
  updateTemplate(id: number | string, data: Partial<TicketTemplate>): Promise<ApiResponse<TicketTemplate>> {
    return client.put(`/ticket-templates/${id}`, data)
  },

  /** 删除模板 */
  deleteTemplate(id: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/ticket-templates/${id}`)
  },

  /** 应用模板 */
  applyTemplate(id: number | string, data: Record<string, any> = {}): Promise<ApiResponse<any>> {
    return client.post(`/ticket-templates/apply/${id}`, data)
  },

  // ── 自动化规则 ──

  /** 规则列表 */
  listRules(): Promise<ApiResponse<AutomationRule[]>> {
    return client.get('/rules')
  },

  /** 创建规则 */
  createRule(data: Partial<AutomationRule>): Promise<ApiResponse<AutomationRule>> {
    return client.post('/rules', data)
  },

  /** 规则详情 */
  getRule(id: number | string): Promise<ApiResponse<AutomationRule>> {
    return client.get(`/rules/${id}`)
  },

  /** 更新规则 */
  updateRule(id: number | string, data: Partial<AutomationRule>): Promise<ApiResponse<AutomationRule>> {
    return client.put(`/rules/${id}`, data)
  },

  /** 删除规则 */
  deleteRule(id: number | string): Promise<ApiResponse<void>> {
    return client.delete(`/rules/${id}`)
  },

  /** 启用/禁用规则 */
  toggleRule(id: number | string): Promise<ApiResponse<void>> {
    return client.post(`/rules/${id}/toggle`)
  },

  /** 执行规则 */
  executeRule(event: string, context: Record<string, any> = {}): Promise<ApiResponse<any>> {
    return client.post(`/rules/execute/${event}`, { context })
  },

  /** 评估规则 */
  evaluateRule(data: any): Promise<ApiResponse<any>> {
    return client.post('/rules/evaluate', data)
  },

  /** 预置默认规则 */
  seedRules(): Promise<ApiResponse<void>> {
    return client.post('/rules/seed')
  },

  // ── 导入 ──

  /** 导入客户 CSV */
  importClients(formData: FormData): Promise<ApiResponse<any>> {
    return client.post('/import/clients', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 导入设备 CSV */
  importEquipment(formData: FormData): Promise<ApiResponse<any>> {
    return client.post('/import/equipment', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 导入商品 CSV */
  importGoods(formData: FormData): Promise<ApiResponse<any>> {
    return client.post('/import/goods', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

/**
 * 通用导出下载辅助：将 blob 响应转为文件下载
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
