export const TICKET_STATUS = {
  'open': { label: '待处理', color: '#718096', cssClass: 'bt-status-open' },
  'in-progress': { label: '进行中', color: '#4299e1', cssClass: 'bt-status-in-progress' },
  'pending-parts': { label: '待配件', color: '#ecc94b', cssClass: 'bt-status-pending-parts' },
  'pending-client': { label: '待客户确认', color: '#ecc94b', cssClass: 'bt-status-pending-client' },
  'pending-payment': { label: '待结算', color: '#f56565', cssClass: 'bt-status-pending-payment' },
  'completed': { label: '待确认', color: '#48bb78', cssClass: 'bt-status-completed' },
  'closed': { label: '已完成', color: '#48bb78', cssClass: 'bt-status-closed' },
  'cancelled': { label: '已取消', color: '#a0aec0', cssClass: 'bt-status-cancelled' },
  'archived': { label: '已归档', color: '#a0aec0', cssClass: 'bt-status-archived' },
}

export const PAYMENT_METHODS = ['微信', '支付宝', '现金', '银行转账']

export const EQUIPMENT_STATUS = [
  { value: '正常', cssClass: 'success' },
  { value: '维修中', cssClass: 'warning' },
  { value: '已报废', cssClass: 'danger' },
]

export const EXPENSE_CATEGORIES = ['配件采购', '工具耗材', '交通费用', '人工费用', '办公费用', '其他']
