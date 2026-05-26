<template>
  <div class="stat-card">
    <div class="d-flex align-items-center">
      <div class="bt-stat-icon" :class="iconColor">
        <i :class="icon"></i>
      </div>
      <div class="ms-2">
        <div class="stat-value">{{ value }}</div>
        <div class="stat-label">{{ label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: 'bi bi-inbox' },
  iconColor: { type: String, default: 'blue' },
  value: { type: [String, Number], default: '0' },
  label: { type: String, default: '' },
})
</script>
