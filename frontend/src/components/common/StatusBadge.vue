<template>
  <span class="bt-status-badge" :class="statusClass">
    {{ displayName }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const STATUS_MAP = {
  'open': { name: '待处理', class: 'bt-status-open' },
  'in-progress': { name: '进行中', class: 'bt-status-in-progress' },
  'pending-parts': { name: '待配件', class: 'bt-status-pending-parts' },
  'pending-client': { name: '待确认', class: 'bt-status-pending-client' },
  'pending-payment': { name: '待结算', class: 'bt-status-pending-payment' },
  'completed': { name: '已完成', class: 'bt-status-completed' },
  'closed': { name: '已关闭', class: 'bt-status-closed' },
  'cancelled': { name: '已取消', class: 'bt-status-cancelled' },
  'archived': { name: '已归档', class: 'bt-status-archived' },
}

const props = defineProps({
  status: { type: String, required: true },
  name: { type: String, default: '' },
})

const statusConfig = computed(() => STATUS_MAP[props.status] || { name: props.status, class: 'bt-status-open' })
const statusClass = computed(() => statusConfig.value.class)
const displayName = computed(() => props.name || statusConfig.value.name)
</script>
