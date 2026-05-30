<template>
  <div class="activity-stream">
    <div class="d-flex align-items-center justify-content-between mb-3">
      <h6 class="mb-0"><i class="bi bi-activity me-2"></i>{{ title }}</h6>
      <span v-if="activities.length" class="badge bg-secondary">{{ activities.length }}</span>
    </div>

    <div v-if="!activities.length" class="text-muted small text-center py-4">
      <i class="bi bi-inbox fs-4 d-block mb-2 opacity-50"></i>
      暂无动态
    </div>

    <div v-else class="activity-list">
      <div
        v-for="(activity, index) in displayedActivities"
        :key="activity.id || index"
        class="activity-item"
        :class="{ 'has-amount': activity.amount !== undefined }"
      >
        <div class="activity-icon" :class="activity.iconColor || 'blue'">
          <i :class="activity.icon || 'bi bi-circle'"></i>
        </div>
        <div class="activity-content">
          <div class="activity-title">
            <span class="fw-medium">{{ activity.title }}</span>
            <span v-if="activity.amount !== undefined" class="activity-amount" :class="activity.amountClass || 'text-success'">
              {{ formatMoney(activity.amount) }}
            </span>
          </div>
          <div class="activity-meta">
            <span class="text-muted">{{ activity.description }}</span>
            <span class="activity-time">{{ formatRelativeTime(activity.time) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activities.length > limit" class="text-center mt-2">
      <button class="btn btn-sm btn-link text-decoration-none" @click="toggleExpand">
        <i :class="expanded ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
        {{ expanded ? '收起' : `查看更多 (${activities.length - limit})` }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatMoney, formatRelativeTime } from '@/utils/format'

const props = defineProps({
  title: {
    type: String,
    default: '今日动态'
  },
  activities: {
    type: Array,
    default: () => []
  },
  limit: {
    type: Number,
    default: 5
  }
})

const expanded = ref(false)

const displayedActivities = computed(() => {
  if (expanded.value) {
    return props.activities
  }
  return props.activities.slice(0, props.limit)
})

function toggleExpand() {
  expanded.value = !expanded.value
}
</script>

<style scoped>
.activity-stream {
  padding: 4px;
}

.activity-list {
  position: relative;
}

.activity-list::before {
  content: '';
  position: absolute;
  left: 16px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--bt-gray-200);
  border-radius: 1px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 0;
  position: relative;
}

.activity-item:first-child {
  padding-top: 0;
}

.activity-item:last-child {
  padding-bottom: 0;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  z-index: 1;
  background: var(--bt-primary-100);
  color: var(--bt-primary-600);
}

.activity-icon.green {
  background: var(--bt-success-light);
  color: var(--bt-success);
}

.activity-icon.yellow {
  background: var(--bt-warning-light);
  color: var(--bt-warning);
}

.activity-icon.red {
  background: var(--bt-danger-light);
  color: var(--bt-danger);
}

.activity-icon.purple {
  background: #ede9fe;
  color: #7c3aed;
}

.activity-icon.gray {
  background: var(--bt-gray-200);
  color: var(--bt-gray-500);
}

.activity-content {
  flex: 1;
  min-width: 0;
  padding-top: 2px;
}

.activity-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 2px;
}

.activity-title span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-amount {
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
  flex-shrink: 0;
}

.activity-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
}

.activity-meta span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--bt-gray-500);
}

.activity-time {
  color: var(--bt-gray-400);
  white-space: nowrap;
  flex-shrink: 0;
  font-size: 11px;
}

@media (hover: hover) and (pointer: fine) {
  .activity-item:hover .activity-content {
    background: var(--bt-gray-50);
    margin: -6px -8px;
    padding: 6px 8px;
    border-radius: var(--bt-radius-sm);
  }
}

@media (max-width: 576px) {
  .activity-list::before {
    left: 14px;
  }

  .activity-icon {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }

  .activity-title {
    font-size: 12px;
  }

  .activity-amount {
    font-size: 12px;
  }

  .activity-meta {
    font-size: 11px;
  }
}
</style>
