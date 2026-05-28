<template>
  <div class="row g-2 mb-2">
    <div class="col-md-6">
      <div class="card p-2 p-md-3">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h6 class="mb-0"><i class="bi bi-credit-card me-1"></i>收款进度</h6>
          <button v-if="canAddPayment" class="btn btn-sm btn-outline-success" @click="$emit('add-payment')">
            <i class="bi bi-plus-lg"></i> 收款
          </button>
        </div>
        <div class="d-flex justify-content-between small mb-1">
          <span>已收 {{ formatMoney(ticket.paid_amount || 0) }}</span>
          <span>未收 {{ formatMoney(remaining) }}</span>
        </div>
        <div class="progress" style="height:8px">
          <div class="progress-bar bg-success" :style="{ width: paymentPercent + '%' }"></div>
        </div>
        <div class="text-center small text-muted mt-1">{{ paymentPercent.toFixed(0) }}%</div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="card p-2 p-md-3">
        <h6 class="mb-2"><i class="bi bi-pie-chart me-1"></i>费用分布</h6>
        <div class="d-flex gap-1" style="height:12px;border-radius:6px;overflow:hidden">
          <div v-if="feeDistribution.material > 0" class="bg-danger" :style="{ width: feeDistribution.material + '%' }" title="材料费"></div>
          <div v-if="feeDistribution.labor > 0" class="bg-primary" :style="{ width: feeDistribution.labor + '%' }" title="人工费"></div>
          <div v-if="feeDistribution.travel > 0" class="bg-info" :style="{ width: feeDistribution.travel + '%' }" title="交通费"></div>
          <div v-if="feeDistribution.parts > 0" class="bg-warning" :style="{ width: feeDistribution.parts + '%' }" title="配件费"></div>
        </div>
        <div class="d-flex gap-3 mt-2 small flex-wrap">
          <span><span class="badge bg-danger me-1">&nbsp;</span>材料 {{ feeDistribution.material.toFixed(0) }}%</span>
          <span><span class="badge bg-primary me-1">&nbsp;</span>人工 {{ feeDistribution.labor.toFixed(0) }}%</span>
          <span><span class="badge bg-info me-1">&nbsp;</span>交通 {{ feeDistribution.travel.toFixed(0) }}%</span>
          <span><span class="badge bg-warning me-1">&nbsp;</span>配件 {{ feeDistribution.parts.toFixed(0) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  ticket: { type: Object, required: true },
  serviceItems: { type: Array, default: () => [] },
  canAddPayment: { type: Boolean, default: true },
})

defineEmits(['add-payment'])

const remaining = computed(() => (props.ticket.total || 0) - (props.ticket.paid_amount || 0))
const paymentPercent = computed(() => {
  const total = parseFloat(props.ticket.total || 0)
  return total > 0 ? Math.min(100, (parseFloat(props.ticket.paid_amount || 0) / total) * 100) : 0
})

const totalLaborRevenue = computed(() => props.serviceItems.reduce((sum, r) => sum + (r.line_total || 0), 0))

const feeDistribution = computed(() => {
  const total = parseFloat(props.ticket.total || 0) || 1
  const material = parseFloat(props.ticket.total_material || 0)
  const labor = parseFloat(props.ticket.total_labor || totalLaborRevenue.value)
  const travel = parseFloat(props.ticket.travel_fee || 0)
  const parts = parseFloat(props.ticket.parts_fee || 0)
  return {
    material: (material / total) * 100,
    labor: (labor / total) * 100,
    travel: (travel / total) * 100,
    parts: (parts / total) * 100,
  }
})

</script>
