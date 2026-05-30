/**
 * API模块补充类型定义
 * 用于完善TypeScript类型安全
 */

// 采购订单
export interface PurchaseOrder {
  id: number | string
  po_no?: string
  supplier_id?: number | string
  supplier_name?: string
  total_amount?: number
  status?: string
  created_at?: string
  updated_at?: string
}

// 服务费率
export interface ServiceFeeItem {
  id: number | string
  name: string
  rate: number
  unit?: string
  description?: string
  is_active?: boolean
}

// 员工
export interface StaffMember {
  id: number | string
  name: string
  role?: string
  phone?: string
  email?: string
  status?: string
  department?: string
}

// 供应商
export interface SupplierInfo {
  id: number | string
  name: string
  contact?: string
  phone?: string
  email?: string
  address?: string
  notes?: string
}

// 提醒
export interface ReminderItem {
  id: number | string
  title: string
  content?: string
  remind_at: string
  ticket_id?: number | string
  status?: 'pending' | 'sent' | 'cancelled'
  created_at?: string
}

// 仓库
export interface WarehouseInfo {
  id: number | string
  name: string
  location?: string
  capacity?: number
  current_stock_count?: number
  manager?: string
}

// 企业微信配置
export interface WecomConfig {
  webhook_url: string
  enabled: boolean
  notify_events?: string[]
  created_at?: string
  updated_at?: string
}

// PushPlus配置
export interface PushPlusConfig {
  token: string
  enabled: boolean
  channel?: string
  title?: string
  template?: string
}

// 自然语言命令
export interface NLCommand {
  command: string
  result?: any
  error?: string
  executed_at?: string
}

// 搜索参数
export interface SearchParams {
  keyword?: string
  type?: 'ticket' | 'client' | 'all'
  page?: number
  page_size?: number
}

// 库存预警参数
export interface StockAlertParams {
  threshold?: number
  warehouse_id?: number | string
}

// 财务概览
export interface FinanceOverview {
  total_revenue: number
  total_cost: number
  profit: number
  period?: string
  revenue_trend?: Array<{ date: string; amount: number }>
}

// 个人支出摘要
export interface ExpenseSummary {
  period: string
  total: number
  by_category: Record<string, number>
  trend?: Array<{ date: string; amount: number }>
}

// 商品分类
export interface GoodsCategory {
  id: number | string
  name: string
  description?: string
  parent_id?: number | string
  sort_order?: number
}

// 商品类型/规格
export interface GoodsType {
  id: number | string
  category_id: number | string
  name: string
  specs?: string
  unit?: string
}

// 工单状态流
export interface StatusFlow {
  from: string
  to: string[]
  conditions?: Record<string, any>
}

// 自动化规则
export interface AutomationRuleCondition {
  field: string
  operator: string
  value: any
}

export interface AutomationRuleAction {
  type: string
  target?: string
  payload?: Record<string, any>
}
