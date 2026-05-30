export interface ApiResponse<T = unknown> {
  code?: number
  message?: string
  data?: T
  error?: string
}

export interface PaginationParams {
  page?: number
  page_size?: number
  pageSize?: number
  limit?: number
  offset?: number
}

export interface PaginatedResponse<T> {
  items?: T[]
  data?: T[]
  records?: T[]
  total?: number
  count?: number
  page?: number
  page_size?: number
  pageSize?: number
}

export interface Ticket {
  id: number | string
  ticket_no?: string
  client?: string
  contact?: string
  phone?: string
  location?: string
  description?: string
  content?: string
  notes?: string
  status?: string
  status_name?: string
  priority?: 'H' | 'L' | ''
  total?: number
  amount?: number
  paid_amount?: number
  created_at?: string
  created_by?: string
  appointment_at?: string
  time_spent?: number
  photos?: TicketPhoto[]
  materials?: TicketMaterial[]
  history?: TicketHistory[]
  timeline?: TimelineEvent[]
}

export interface TicketPhoto {
  id?: number | string
  filepath?: string
  url?: string
  filename?: string
  created_at?: string
}

export interface TicketMaterial {
  id?: number | string
  product_id?: number | string
  product_name?: string
  name?: string
  quantity?: number
  unit_price?: number
  total_price?: number
}

export interface TicketHistory {
  id?: number
  action?: string
  description?: string
  operator?: string
  created_at?: string
}

export interface TimelineEvent {
  id?: number
  description?: string
  message?: string
  created_at?: string
}

export interface Client {
  id: number | string
  name?: string
  contact?: string
  phone?: string
  address?: string
  contract_rate?: number
  payment_terms?: number
  notes?: string
}

export interface Equipment {
  id: number | string
  name?: string
  client?: string
  client_id?: number | string
  type?: string
  brand?: string
  model?: string
  serial_number?: string
  purchase_date?: string
  warranty_end?: string
  location?: string
  notes?: string
  status?: string
}

export interface Staff {
  id: number | string
  name?: string
  phone?: string
  email?: string
  bill_rate?: number
  hourly_rate?: number
  cost_rate?: number
  skills?: string
  status?: 'active' | 'inactive'
  notes?: string
  ticket_count?: number
}

export interface Supplier {
  id: number | string
  name?: string
  contact?: string
  phone?: string
  email?: string
  bank_name?: string
  bank_account?: string
  payment_terms?: number
  notes?: string
}

export interface Warehouse {
  id: number | string
  name?: string
  address?: string
  manager?: string
  sort_order?: number
  is_active?: boolean
}

export interface Goods {
  id: number | string
  name?: string
  sku?: string
  category?: string
  unit?: string
  cost_price?: number
  selling_price?: number
  price?: number
  stock?: number
  quantity?: number
  warehouse_id?: number | string
}

export interface ServiceFee {
  id: number | string
  name?: string
  type?: string
  base_price?: number
  unit_price?: number
  cost_price?: number
  description?: string
}

export interface FinanceSummary {
  monthly_income?: number
  monthly_expense?: number
  monthly_profit?: number
  unpaid_count?: number
  total_unpaid?: number
  income_history?: IncomeRecord[]
  expense_history?: ExpenseRecord[]
  unpaid_tickets?: Ticket[]
}

export interface IncomeRecord {
  id: number | string
  client?: string
  amount?: number
  payment_method?: string
  description?: string
  received_at?: string
}

export interface ExpenseRecord {
  id: number | string
  category?: string
  amount?: number
  description?: string
  vendor?: string
  paid_at?: string
}

export interface DashboardStats {
  open_tickets?: number
  openTickets?: number
  today_tickets?: number
  todayTickets?: number
  pending_payment?: number
  pendingPayment?: number
  monthly_income?: number
  monthlyIncome?: number
  total_tickets?: number
  totalTickets?: number
  equipment_count?: number
  equipmentCount?: number
  all_statuses?: Record<string, number>
  recent_tickets?: Ticket[]
  recent_todos?: Todo[]
}

export interface Todo {
  id: number | string
  title?: string
  done?: boolean
  due_date?: string
  priority?: string
}

export interface PurchaseOrder {
  id: number | string
  order_no?: string
  supplier?: string
  supplier_id?: number | string
  status?: string
  total_amount?: number
  order_date?: string
  expected_date?: string
  notes?: string
  items?: PurchaseItem[]
}

export interface PurchaseItem {
  id?: number | string
  order_id?: number | string
  product_id?: number | string
  product_name?: string
  quantity?: number
  unit_price?: number
  total_price?: number
}

export interface InventoryItem {
  id: number | string
  goods_id?: number | string
  goods_name?: string
  warehouse_id?: number | string
  warehouse_name?: string
  quantity?: number
  min_stock?: number
  max_stock?: number
  last_check?: string
}

export interface Expense {
  id: number | string
  category?: string
  amount?: number
  description?: string
  vendor?: string
  paid_at?: string
  paid_by?: string
  receipt_url?: string
}

export interface Notification {
  id: number | string
  title?: string
  message?: string
  type?: string
  is_read?: boolean
  created_at?: string
  read_at?: string
}

export interface AutomationRule {
  id: number | string
  name?: string
  trigger_type?: string
  action_type?: string
  is_enabled?: boolean
  conditions?: Record<string, any>
  actions?: Record<string, any>
  created_at?: string
}

export interface ServiceAgreement {
  id: number | string
  client_id?: number | string
  client_name?: string
  start_date?: string
  end_date?: string
  service_type?: string
  price?: number
  status?: string
}

export interface Technician {
  id: number | string
  name?: string
  phone?: string
  email?: string
  skill_level?: string
  billing_type?: 'hourly' | 'daily' | 'package'
  cost_rate?: number
  daily_cost_rate?: number
  package_cost?: number
  status?: string
}

export interface TicketServiceItem {
  id?: number | string
  ticket_id?: number | string
  technician_name?: string
  service_name?: string
  billing_type?: 'hourly' | 'daily' | 'package'
  hours?: number
  days?: number
  package_fee?: number
  unit_price?: number
  cost_price?: number
  line_total?: number
  line_cost?: number
}

export type TicketStatus = 
  | 'open' 
  | 'in-progress' 
  | 'pending-parts' 
  | 'pending-client' 
  | 'pending-payment' 
  | 'completed' 
  | 'closed' 
  | 'cancelled' 
  | 'archived'

export type Priority = 'H' | 'L' | ''

export type BillingType = 'hourly' | 'daily' | 'package'

export type PaymentMethod = '微信' | '支付宝' | '现金' | '银行转账'

export interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
}

export interface TableColumn {
  key: string
  label: string
  sortable?: boolean
  width?: string
  align?: 'left' | 'center' | 'right'
}

export interface FilterOption {
  key: string
  label: string
  type: 'text' | 'select' | 'date' | 'daterange'
  options?: SelectOption[]
  placeholder?: string
}
