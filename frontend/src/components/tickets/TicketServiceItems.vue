<template>
  <div class="card p-3 p-md-4 mb-2">
    <h5 class="mb-3 d-flex align-items-center gap-2">
      <i class="bi bi-clock-history me-2"></i>服务明细
      <button class="btn btn-sm btn-outline-primary ms-auto" @click="$emit('add-service-item')">
        <i class="bi bi-plus-lg"></i> 添加服务明细
      </button>
    </h5>
    <div v-if="items.length === 0" class="text-muted small py-4 text-center">
      <i class="bi bi-clock-history me-1"></i>暂无服务明细
    </div>
    <div v-else class="space-y-3">
      <div v-for="item in items" :key="item.id" class="border rounded-lg p-3" style="background:var(--bt-gray-50, #f8f9fa)">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <div class="d-flex items-center gap-2">
            <div class="bt-avatar bt-avatar-sm" :class="'bt-avatar-color-' + (item.id % 8)">
              {{ (item.technician_name || '?')[0] }}
            </div>
            <div>
              <span class="font-medium">{{ item.technician_name || '-' }}</span>
              <span class="text-muted small ms-2">{{ item.name || '-' }}</span>
            </div>
          </div>
          <button class="btn btn-sm btn-outline-danger" @click="$emit('delete-service-item', item.id)">
            <i class="bi bi-trash"></i>
          </button>
        </div>
        <div class="row g-2 text-center">
          <div class="col-3">
            <div class="text-xs text-muted">工时</div>
            <div class="font-bold">{{ item.hours || 0 }}h</div>
          </div>
          <div class="col-3">
            <div class="text-xs text-muted">成本时薪</div>
            <div class="font-bold text-warning">¥{{ item.cost_price || 0 }}/h</div>
          </div>
          <div class="col-3">
            <div class="text-xs text-muted">计费时薪</div>
            <div class="font-bold text-primary">¥{{ item.unit_price || 0 }}/h</div>
          </div>
          <div class="col-3">
            <div class="text-xs text-muted">毛利</div>
            <div class="font-bold" :class="(item.line_profit || 0) >= 0 ? 'text-success' : 'text-danger'">
              ¥{{ formatMoney(item.line_profit || 0) }}
            </div>
          </div>
        </div>
        <div class="mt-2 pt-2 d-flex justify-content-between small" style="border-top:1px solid var(--bt-gray-200, #e5e7eb)">
          <span class="text-muted">成本: ¥{{ formatMoney(item.line_cost || 0) }}</span>
          <span class="text-success">收入: ¥{{ formatMoney(item.line_total || 0) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
})
defineEmits(['add-service-item', 'delete-service-item'])

function formatMoney(val) { return parseFloat(val || 0).toFixed(2) }
</script>

<style scoped>
.text-xs { font-size: 12px; }
.font-bold { font-weight: 700; }
</style>
