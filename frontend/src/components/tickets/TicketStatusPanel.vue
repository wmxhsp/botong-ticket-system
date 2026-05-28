<template>
  <div>
    <!-- Status Flow -->
    <div class="card p-3 p-md-4 mb-2">
      <h5 class="mb-2"><i class="bi bi-diagram-3 me-2"></i>工单状态</h5>
      <div class="bt-process-panel mb-2">
        <div v-for="step in statusFlow" :key="step.key"
             class="bt-process-item"
             :class="{ done: step.done, active: step.active, pending: !step.done && !step.active }">
          <i v-if="step.done" class="bi bi-check-circle-fill text-success"></i>
          <i v-else-if="step.active" class="bi bi-play-circle-fill text-primary"></i>
          <i v-else class="bi bi-circle text-muted"></i>
          <span>{{ step.label }}</span>
        </div>
      </div>
      <div class="d-flex gap-2 flex-wrap">
        <button v-for="action in availableActions" :key="action.status"
                class="btn btn-sm"
                :class="'btn-' + action.btnClass"
                @click="$emit('change-status', action.status)">
          {{ action.label }}
        </button>
      </div>
    </div>

    <!-- Fee Details -->
    <div class="card p-3 p-md-4 mb-2">
      <h5 class="mb-2"><i class="bi bi-cash me-2"></i>费用明细</h5>
      <div class="space-y-2">
        <div class="d-flex justify-content-between small">
          <span class="text-muted">材料费用</span>
          <span>{{ formatMoney(ticket.total_material || 0) }}</span>
        </div>
        <div class="d-flex justify-content-between small">
          <span class="text-muted">人工费用</span>
          <span>{{ formatMoney(ticket.total_labor || totalLaborRevenue) }}</span>
        </div>
        <div class="d-flex justify-content-between small">
          <span class="text-muted">外协费用</span>
          <span>{{ formatMoney(ticket.total_external || 0) }}</span>
        </div>
        <div style="border-top:1px solid var(--bt-gray-200, #e5e7eb);padding-top:8px;margin-top:8px">
          <div class="d-flex justify-content-between font-bold">
            <span>总计</span>
            <span class="text-success">{{ formatMoney(ticket.total || 0) }}</span>
          </div>
        </div>
        <div style="border-top:1px solid var(--bt-gray-200, #e5e7eb);padding-top:8px;margin-top:8px">
          <div class="d-flex justify-content-between small">
            <span class="text-muted">成本合计</span>
            <span class="text-danger">{{ formatMoney(totalCost) }}</span>
          </div>
          <div class="d-flex justify-content-between small">
            <span class="text-muted">净利润</span>
            <span :class="netProfit >= 0 ? 'text-success' : 'text-danger'" class="font-bold">
              {{ formatMoney(netProfit) }}
            </span>
          </div>
          <div class="d-flex justify-content-between small">
            <span class="text-muted">利润率</span>
            <span :class="profitMargin >= 0 ? 'text-success' : 'text-danger'">
              {{ profitMargin.toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Timer -->
    <div class="card p-3 p-md-4 mb-2">
      <h5 class="mb-2"><i class="bi bi-stopwatch me-2"></i>工时计时</h5>
      <div class="text-center mb-3">
        <span class="display-6 font-bold" :class="timerRunning ? 'text-primary' : 'text-muted'">{{ timerDisplay }}</span>
      </div>
      <div class="d-flex gap-2 justify-content-center">
        <button v-if="!timerRunning" class="btn btn-sm btn-primary" @click="$emit('start-timer')" :disabled="isClosed">
          <i class="bi bi-play-fill"></i> 开始
        </button>
        <button v-if="timerRunning" class="btn btn-sm btn-danger" @click="$emit('stop-timer')">
          <i class="bi bi-stop-fill"></i> 停止
        </button>
      </div>
      <div class="mt-3 small text-muted text-center">
        累计工时: {{ parseFloat(ticket.time_spent || 0).toFixed(2) }} 小时
      </div>
    </div>

    <!-- Appointment -->
    <div class="card p-3 p-md-4">
      <h5 class="mb-3 d-flex align-items-center gap-2">
        <i class="bi bi-calendar-check me-2"></i>预约
        <span v-if="ticket.appointment_at" class="badge bg-info ms-auto">已预约</span>
      </h5>
      <div v-if="ticket.appointment_at" class="mb-3">
        <div class="font-medium">{{ formatDateTime(ticket.appointment_at) }}</div>
        <div class="small text-muted mt-1">
          <span v-if="appointmentStatus === 'upcoming'" class="text-primary">即将到来</span>
          <span v-else-if="appointmentStatus === 'overdue'" class="text-danger">已过期</span>
          <span v-else class="text-success">今天</span>
        </div>
      </div>
      <div v-else class="text-muted small py-2">未设置预约</div>
      <button class="btn btn-sm btn-outline-info w-100 mt-2" @click="$emit('edit-appointment')">
        <i class="bi bi-pencil"></i> {{ ticket.appointment_at ? '修改预约' : '设置预约' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney, formatDateTime } from '@/utils/format'

const props = defineProps({
  ticket: { type: Object, required: true },
  serviceItems: { type: Array, default: () => [] },
  timerDisplay: { type: String, default: '00:00:00' },
  timerRunning: { type: Boolean, default: false },
})

defineEmits(['change-status', 'start-timer', 'stop-timer', 'edit-appointment'])

const isClosed = computed(() => ['closed', 'cancelled'].includes(props.ticket.status))

const totalLaborRevenue = computed(() => props.serviceItems.reduce((sum, r) => sum + (r.line_total || 0), 0))
const laborCost = computed(() => props.serviceItems.reduce((sum, r) => sum + (r.line_cost || 0), 0))
const totalCost = computed(() => laborCost.value + parseFloat(props.ticket.material_cost || 0))
const netProfit = computed(() => parseFloat(props.ticket.total || 0) - totalCost.value)
const profitMargin = computed(() => {
  const total = parseFloat(props.ticket.total || 0)
  return total > 0 ? (netProfit.value / total) * 100 : 0
})

const statusFlow = computed(() => {
  const s = props.ticket.status
  return [
    { key: 'open', label: '待处理', done: true, active: s === 'open' },
    { key: 'in-progress', label: '进行中', done: ['in-progress','pending-parts','pending-client','pending-payment','completed','closed','archived'].includes(s), active: s === 'in-progress' },
    { key: 'pending-payment', label: '待结算', done: ['pending-payment','completed','closed','archived'].includes(s), active: s === 'pending-payment' },
    { key: 'completed', label: '已完成', done: ['completed','closed','archived'].includes(s), active: s === 'completed' },
    { key: 'closed', label: '已关闭', done: ['closed','archived'].includes(s), active: s === 'closed' },
    { key: 'archived', label: '已归档', done: s === 'archived', active: s === 'archived' },
  ]
})

const availableActions = computed(() => {
  const s = props.ticket.status
  const actions = []
  if (s === 'open') actions.push({ status: 'in-progress', label: '开始服务', btnClass: 'primary' })
  if (s === 'in-progress') actions.push({ status: 'pending-parts', label: '待配件', btnClass: 'warning' })
  if (s === 'in-progress') actions.push({ status: 'pending-client', label: '待确认', btnClass: 'info' })
  if (s === 'in-progress') actions.push({ status: 'pending-payment', label: '完工结算', btnClass: 'success' })
  if (s === 'pending-parts') actions.push({ status: 'in-progress', label: '恢复服务', btnClass: 'primary' })
  if (s === 'pending-client') actions.push({ status: 'in-progress', label: '恢复服务', btnClass: 'primary' })
  if (s === 'pending-payment') actions.push({ status: 'completed', label: '确认完工', btnClass: 'success' })
  if (s === 'completed') actions.push({ status: 'closed', label: '关闭工单', btnClass: 'secondary' })
  if (s === 'closed') actions.push({ status: 'archived', label: '归档', btnClass: 'secondary' })
  if (s === 'cancelled') actions.push({ status: 'open', label: '重新打开', btnClass: 'primary' })
  if (!['closed','archived','cancelled'].includes(s)) actions.push({ status: 'cancelled', label: '取消工单', btnClass: 'danger' })
  return actions
})

const appointmentStatus = computed(() => {
  if (!props.ticket.appointment_at) return ''
  const appt = new Date(props.ticket.appointment_at)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const apptDay = new Date(appt.getFullYear(), appt.getMonth(), appt.getDate())
  if (apptDay < today) return 'overdue'
  if (apptDay.getTime() === today.getTime()) return 'today'
  return 'upcoming'
})
</script>
