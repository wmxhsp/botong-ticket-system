<template>
  <div class="page-feature-map">
    <div class="bt-page-title">
      <h2><i class="bi bi-diagram-3 me-2"></i>功能地图</h2>
      <p>前后端功能对齐一览 · 共 {{ totalFeatures }} 个功能点 · {{ doneCount }} 已完成</p>
    </div>

    <!-- 统计卡片 -->
    <div class="row g-2 mb-3">
      <div class="col-6 col-md-3">
        <div class="card p-2 text-center">
          <div class="stat-value">{{ totalFeatures }}</div>
          <div class="stat-label">功能点总数</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="card p-2 text-center">
          <div class="stat-value text-success">{{ doneCount }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="card p-2 text-center">
          <div class="stat-value text-warning">{{ pendingCount }}</div>
          <div class="stat-label">待完善</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="card p-2 text-center">
          <div class="stat-value text-info">{{ coverageRate }}%</div>
          <div class="stat-label">覆盖率</div>
        </div>
      </div>
    </div>

    <!-- 模块功能列表 -->
    <div class="row g-3">
      <div v-for="mod in modulesWithFeatures" :key="mod.name" class="col-12 col-md-6 col-xl-4">
        <div class="card h-100">
          <div class="card-header d-flex justify-content-between align-items-center py-2">
            <span class="fw-medium">
              <i :class="['bi', mod.nav?.icon || 'bi-box', 'me-2']"></i>
              {{ mod.nav?.title || mod.name }}
            </span>
            <span class="badge bg-secondary">{{ mod.features.length }}</span>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-sm table-hover mb-0" style="font-size:12px">
                <thead class="table-light">
                  <tr>
                    <th class="ps-3">功能</th>
                    <th>端点</th>
                    <th class="text-center" style="width:60px">状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="f in mod.features" :key="f.id || f.name">
                    <td class="ps-3">{{ f.name }}</td>
                    <td class="text-muted font-monospace small">{{ f.endpoint }}</td>
                    <td class="text-center">
                      <span class="badge" :class="statusBadgeClass(f.status)">
                        {{ statusLabel(f.status) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 未覆盖的后端端点提示 -->
    <div class="card mt-3">
      <div class="card-header py-2">
        <i class="bi bi-exclamation-triangle me-2 text-warning"></i>
        后端有但前端未覆盖的端点（{{ uncoveredEndpoints.length }} 个）
      </div>
      <div class="card-body">
        <div v-if="uncoveredEndpoints.length === 0" class="text-muted small">暂无 — 所有端点均已覆盖</div>
        <div v-else class="row g-2">
          <div v-for="ep in uncoveredEndpoints" :key="ep" class="col-auto">
            <span class="badge bg-light text-dark border font-monospace small">{{ ep }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { modules, moduleFeatures } from '@/modules'

const modulesWithFeatures = computed(() =>
  modules.filter(m => m.features && m.features.length > 0)
)

const totalFeatures = computed(() => moduleFeatures.length)
const doneCount = computed(() => moduleFeatures.filter(f => f.status === 'done').length)
const pendingCount = computed(() => moduleFeatures.filter(f => f.status !== 'done').length)
const coverageRate = computed(() => {
  if (totalFeatures.value === 0) return 0
  return Math.round((doneCount.value / totalFeatures.value) * 100)
})

function statusBadgeClass(status) {
  switch (status) {
    case 'done': return 'bg-success'
    case 'partial': return 'bg-warning text-dark'
    case 'pending': return 'bg-secondary'
    default: return 'bg-light text-dark'
  }
}

function statusLabel(status) {
  switch (status) {
    case 'done': return '完成'
    case 'partial': return '部分'
    case 'pending': return '待办'
    default: return status
  }
}

// 已知的前端未覆盖端点（从前后端对比分析中整理）
const uncoveredEndpoints = [
  'GET /api/v1/equipment/components',
  'POST /api/v1/equipment/components',
  'PUT /api/v1/equipment/components/:id',
  'DELETE /api/v1/equipment/components/:id',
  'POST /api/v1/equipment/:id/maintenance',
  'GET /api/v1/equipment/:id/maintenance',
  'POST /api/v1/purchase-orders/:id/receive',
  'POST /api/v1/inventory/adjust',
  'POST /api/v1/inventory/transfer',
  'GET /api/v1/inventory/alerts',
  'POST /api/v1/service-agreements',
  'GET /api/v1/service-agreements',
  'POST /api/v1/automation-rules/trigger',
  'GET /api/v1/ticket-templates',
  'POST /api/v1/ticket-templates',
  'POST /api/v1/notifications/settings',
  'GET /api/v1/export/tickets',
  'GET /api/v1/export/clients',
  'GET /api/v1/export/finance',
  'GET /api/v1/export/inventory',
  'GET /api/v1/export/equipment',
]
</script>

<style scoped>
.page-feature-map {
  padding: 0.5rem;
}
.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
}
.stat-label {
  font-size: 0.75rem;
  color: #6c757d;
}
</style>
