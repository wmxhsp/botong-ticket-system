<template>
  <div v-if="loading" class="bt-empty-state">
    <div class="bt-inline-loading"><div class="bt-spinner"></div> 加载设备信息...</div>
  </div>

  <template v-else-if="equip.id">
    <div class="bt-breadcrumbs">
      <router-link :to="{name: 'Equipment'}">设备管理</router-link>
      <span class="bt-breadcrumb-sep">/</span>
      <span class="bt-breadcrumb-current">{{ equip.name }}</span>
    </div>

    <div class="row g-2">
      <div class="col-md-8">
        <div class="card p-2 mb-3">
          <h5 class="mb-3"><i class="bi bi-pc-display me-2"></i>基本信息</h5>
          <table class="table table-borderless table-sm mb-0">
            <tr><th style="width:100px">设备名称</th><td>{{ equip.name }}</td><th>类型</th><td>{{ equip.type || '-' }}</td></tr>
            <tr><th>品牌</th><td>{{ equip.brand || '-' }}</td><th>型号</th><td>{{ equip.model || '-' }}</td></tr>
            <tr><th>序列号</th><td><code>{{ equip.serial_no || '-' }}</code></td><th>状态</th>
              <td><span class="bt-data-tag" :class="statusClass">{{ equip.status }}</span></td></tr>
            <tr><th>所属客户</th><td>
              <router-link :to="{name: 'ClientDetail', params: {name: equip.client}}" class="text-decoration-none">
                {{ equip.client_name || equip.client }}
              </router-link>
            </td><th>安装日期</th><td>{{ equip.install_date || '-' }}</td></tr>
            <tr><th>保修到期</th><td>{{ equip.warranty_expire || '-' }}</td><th>维护周期</th><td>{{ equip.maintenance_cycle || '-' }}</td></tr>
            <tr><th>位置</th><td colspan="3">{{ equip.location || '-' }}</td></tr>
            <tr><th>备注</th><td colspan="3">{{ equip.notes || '-' }}</td></tr>
          </table>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card p-2 mb-3">
          <h5 class="mb-3"><i class="bi bi-cash me-2"></i>财务摘要</h5>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-muted">工单数</span><span>{{ finance.total_tickets || 0 }}</span>
          </div>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-muted">总收入</span><span class="text-success">{{ formatMoney(finance.total_revenue) }}</span>
          </div>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-muted">总成本</span><span class="text-danger">{{ formatMoney(finance.total_cost) }}</span>
          </div>
          <hr class="my-1">
          <div class="d-flex justify-content-between small fw-bold">
            <span>利润</span><span :style="{color: (finance.total_profit||0) >= 0 ? 'var(--bt-accent-green)' : 'var(--bt-danger)'}">{{ formatMoney(finance.total_profit) }}</span>
          </div>
        </div>
      </div>
    </div>
  </template>

  <div v-else class="bt-empty-state">
    <div class="bt-empty-icon"><i class="bi bi-pc-display"></i></div>
    <div class="bt-empty-title">设备未找到</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { equipmentApi } from '@/api/equipment'
import { formatMoney } from '@/utils/format'

const props = defineProps({ id: { type: String, required: true } })
const equip = ref({})
const loading = ref(true)
const finance = computed(() => equip.value.finance_summary || {})

const statusClass = computed(() => {
  const map = { '正常': 'success', '维修中': 'warning', '已报废': 'danger' }
  return map[equip.value.status] || 'primary'
})

onMounted(async () => {
  try {
    equip.value = await equipmentApi.getById(props.id)
  } catch { /* empty */ } finally { loading.value = false }
})
</script>
