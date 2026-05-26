<template>
  <div class="row g-2 g-md-3 mb-2">
    <div class="col-6 col-md-3">
      <div class="card p-2 p-md-3">
        <div class="d-flex items-center justify-content-between">
          <div>
            <div class="text-xs text-muted">总收入</div>
            <div class="text-lg font-bold text-success">¥{{ formatMoney(ticket.total || 0) }}</div>
          </div>
          <div class="bt-stat-icon-wrap bg-success/10">
            <i class="bi bi-trending-up text-success"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="card p-2 p-md-3">
        <div class="d-flex items-center justify-content-between">
          <div>
            <div class="text-xs text-muted">材料成本</div>
            <div class="text-lg font-bold text-danger">¥{{ formatMoney(ticket.material_cost || 0) }}</div>
          </div>
          <div class="bt-stat-icon-wrap bg-danger/10">
            <i class="bi bi-box-seam text-danger"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="card p-2 p-md-3">
        <div class="d-flex items-center justify-content-between">
          <div>
            <div class="text-xs text-muted">人工成本</div>
            <div class="text-lg font-bold text-warning">¥{{ formatMoney(laborCost) }}</div>
          </div>
          <div class="bt-stat-icon-wrap bg-warning/10">
            <i class="bi bi-people text-warning"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="card p-2 p-md-3">
        <div class="d-flex items-center justify-content-between">
          <div>
            <div class="text-xs text-muted">净利润</div>
            <div class="text-lg font-bold" :class="netProfit >= 0 ? 'text-success' : 'text-danger'">¥{{ formatMoney(netProfit) }}</div>
          </div>
          <div class="bt-stat-icon-wrap" :class="netProfit >= 0 ? 'bg-success/10' : 'bg-danger/10'">
            <i class="bi bi-chart-line" :class="netProfit >= 0 ? 'text-success' : 'text-danger'"></i>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  ticket: { type: Object, required: true },
  serviceItems: { type: Array, default: () => [] },
})

const laborCost = computed(() => props.serviceItems.reduce((sum, r) => sum + (r.line_cost || 0), 0))
const netProfit = computed(() => parseFloat(props.ticket.total || 0) - (laborCost.value + parseFloat(props.ticket.material_cost || 0)))

function formatMoney(val) { return parseFloat(val || 0).toFixed(2) }
</script>

<style scoped>
.bt-stat-icon-wrap {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}
.bg-success\/10 { background: rgba(16, 185, 129, 0.1); }
.bg-danger\/10 { background: rgba(239, 68, 68, 0.1); }
.bg-warning\/10 { background: rgba(245, 158, 11, 0.1); }
.text-xs { font-size: 12px; }
.text-lg { font-size: 1.1rem; }
.font-bold { font-weight: 700; }
</style>
