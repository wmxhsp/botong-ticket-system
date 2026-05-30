<template>
  <div class="quick-stats">
    <div class="row g-2">
      <div
        v-for="(stat, index) in stats"
        :key="stat.key || index"
        class="col-6 col-sm-4 col-lg-2"
      >
        <div
          class="stat-card stat-card-interactive"
          :class="{ 'pulse': stat.pulse, 'active': activeIndex === index }"
          @click="handleClick(stat, index)"
        >
          <div class="d-flex align-items-center justify-content-between mb-2">
            <div class="bt-stat-icon" :class="stat.iconColor || 'blue'">
              <i :class="stat.icon || 'bi bi-inbox'"></i>
            </div>
            <div v-if="stat.trend !== undefined" class="stat-trend" :class="stat.trend >= 0 ? 'up' : 'down'">
              <i :class="stat.trend >= 0 ? 'bi bi-arrow-up-short' : 'bi bi-arrow-down-short'"></i>
              <span>{{ Math.abs(stat.trend) }}%</span>
            </div>
          </div>
          <div class="stat-value" :class="stat.valueClass">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div v-if="stat.progress !== undefined" class="stat-progress mt-2">
            <div class="progress" style="height: 4px;">
              <div
                class="progress-bar"
                :class="stat.progressClass || 'bg-primary'"
                :style="{ width: `${Math.min(stat.progress, 100)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  stats: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['click'])

const activeIndex = ref(-1)

function handleClick(stat, index) {
  activeIndex.value = index
  setTimeout(() => {
    if (activeIndex.value === index) {
      activeIndex.value = -1
    }
  }, 200)
  emit('click', stat, index)
}
</script>

<style scoped>
.stat-card-interactive {
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
}

.stat-card-interactive:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-card-interactive.active {
  transform: scale(0.97);
}

.stat-card-interactive.pulse .bt-stat-icon {
  animation: pulse-ring 2s ease-in-out infinite;
}

@keyframes pulse-ring {
  0% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(59, 130, 246, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
}

.stat-progress .progress {
  background-color: var(--bt-gray-100);
  border-radius: 2px;
  overflow: hidden;
}

.stat-progress .progress-bar {
  transition: width 0.6s ease;
}

@media (hover: none) and (pointer: coarse) {
  .stat-card-interactive:hover {
    transform: none;
    box-shadow: none;
  }

  .stat-card-interactive:active {
    transform: scale(0.97);
    background-color: rgba(59, 130, 246, 0.05);
  }
}
</style>
