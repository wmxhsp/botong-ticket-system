import { z } from 'zod'

// 通用响应模式
export const ApiResponseSchema = z.object({
  success: z.boolean().optional(),
  error: z.string().optional(),
})

// CSRF Token 响应
export const CsrfTokenSchema = ApiResponseSchema.extend({
  csrf_token: z.string(),
})

// 工单模式
export const TicketSchema = z.object({
  id: z.number(),
  client_id: z.number(),
  status: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  priority: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  completed_at: z.string().nullable(),
})

// 客户模式
export const ClientSchema = z.object({
  id: z.number(),
  name: z.string(),
  contact: z.string().nullable(),
  phone: z.string().nullable(),
  email: z.string().nullable(),
  address: z.string().nullable(),
  created_at: z.string(),
})

// 统计数据模式
export const DashboardStatsSchema = z.object({
  total_tickets: z.number(),
  pending_tickets: z.number(),
  completed_tickets: z.number(),
  total_revenue: z.number(),
  total_cost: z.number(),
  active_clients: z.number(),
})

// 校验函数
export function validateResponse(schema, data) {
  const result = schema.safeParse(data)
  if (!result.success) {
    console.warn('API 响应格式不正确:', result.error)
    console.warn('原始数据:', data)
  }
  return result
}
