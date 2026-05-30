<template>
  <div>
    <div class="bt-page-title">
      <h2><i class="bi bi-graph-up me-2"></i>统计分析</h2>
      <p class="d-none d-md-inline">工单、设备、财务数据统计与分析</p>
    </div>

    <LoadingSkeleton v-if="loading" type="card" :count="4" />

    <template v-else>
      <div class="row g-2 mb-3" id="statsCards">
        <div class="col-6 col-lg-3">
          <div class="card p-2 text-center">
            <div class="stat-value">{{ totalTickets }}</div>
            <div class="stat-label">工单总数</div>
          </div>
        </div>
        <div class="col-6 col-lg-3">
          <div class="card p-2 text-center">
            <div class="stat-value">{{ totalEquipment }}</div>
            <div class="stat-label">设备总数</div>
          </div>
        </div>
        <div class="col-6 col-lg-3">
          <div class="card p-2 text-center">
            <div class="stat-value bt-stat-profit">{{ formatMoney(totalProfit) }}</div>
            <div class="stat-label">总利润</div>
          </div>
        </div>
        <div class="col-6 col-lg-3">
          <div class="card p-2 text-center">
            <div class="stat-value">{{ profitMargin }}%</div>
            <div class="stat-label">利润率</div>
          </div>
        </div>
      </div>

      <div class="row g-2">
        <div class="col-md-6">
          <div class="card p-2">
            <h5 class="mb-3"><i class="bi bi-pie-chart me-2"></i>工单状态分布</h5>
            <div class="chart-container">
              <canvas ref="statusChart" height="200"></canvas>
            </div>
          </div>
        </div>

        <div class="col-md-6">
          <div class="card p-2">
            <h5 class="mb-3"><i class="bi bi-pc-display me-2"></i>设备类型分布</h5>
            <div class="chart-container">
              <canvas ref="equipTypeChart" height="200"></canvas>
            </div>
          </div>
        </div>

        <div class="col-md-8">
          <div class="card p-2">
            <h5 class="mb-3"><i class="bi bi-graph-up me-2"></i>月度收入趋势</h5>
            <div class="chart-container">
              <canvas ref="trendChart" height="200"></canvas>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card p-2">
            <h5 class="mb-3"><i class="bi bi-shield-check me-2"></i>设备保修状态</h5>
            <div class="chart-container">
              <canvas ref="warrantyChart" height="200"></canvas>
            </div>
            <div class="mt-2 small text-muted text-center">
              保内 {{ warrantyIn }} 台 · 过保 {{ expiredWarranty }} 台 · 未知 {{ warrantyNone }} 台
            </div>
          </div>
        </div>

        <div class="col-md-6">
          <div class="card p-2">
            <h5 class="mb-3"><i class="bi bi-trophy me-2"></i>客户排行</h5>
            <div class="table-responsive">
              <table class="bt-table">
                <thead>
                  <tr>
                    <th>排名</th>
                    <th>客户名称</th>
                    <th>工单数量</th>
                    <th>总金额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(c, i) in clientRanking" :key="i">
                    <td data-label="排名">
                      <span v-if="i === 0" class="text-warning">&#9733;</span>
                      <span v-else>{{ i + 1 }}</span>
                    </td>
                    <td data-label="客户"><strong>{{ c.client || '-' }}</strong></td>
                    <td data-label="工单数">{{ c.cnt || 0 }} 单</td>
                    <td data-label="金额">{{ formatMoney(c.total) }}</td>
                  </tr>
                  <tr v-if="clientRanking.length === 0">
                    <td colspan="4" class="text-center text-muted py-3">暂无数据</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="col-md-6">
          <div class="card p-2">
            <h5 class="mb-3"><i class="bi bi-award me-2"></i>工程师绩效排行</h5>
            <div class="table-responsive">
              <table class="bt-table">
                <thead>
                  <tr>
                    <th>排名</th>
                    <th>工程师</th>
                    <th>工单数</th>
                    <th>贡献毛利</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(t, i) in technicianRanking" :key="i">
                    <td data-label="排名">
                      <span v-if="i === 0" class="text-warning">&#9733;</span>
                      <span v-else>{{ i + 1 }}</span>
                    </td>
                    <td data-label="工程师"><strong>{{ t.name || '-' }}</strong></td>
                    <td data-label="工单数">{{ t.ticket_count || 0 }} 单</td>
                    <td data-label="毛利">{{ formatMoney(t.profit || 0) }}</td>
                  </tr>
                  <tr v-if="technicianRanking.length === 0">
                    <td colspan="4" class="text-center text-muted py-3">暂无数据</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="col-12">
          <div class="card p-2">
            <h5 class="mb-3"><i class="bi bi-bar-chart me-2"></i>服务类型收入分布</h5>
            <div class="chart-container">
              <canvas ref="serviceTypeChart" height="200"></canvas>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { statsApi } from '@/api/stats'
import { formatMoney } from '@/utils/format'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'

const loading = ref(true)
const totalTickets = ref(0)
const totalEquipment = ref(0)
const totalProfit = ref(0)
const profitMargin = ref(0)
const clientRanking = ref([])
const technicianRanking = ref([])
const warrantyIn = ref(0)
const expiredWarranty = ref(0)
const warrantyNone = ref(0)

const statusChart = ref(null)
const equipTypeChart = ref(null)
const trendChart = ref(null)
const warrantyChart = ref(null)
const serviceTypeChart = ref(null)

let chartInstances = []

async function loadStats() {
  loading.value = true
  try {
    const data = await statsApi.getDashboard()
    
    totalTickets.value = data.total_tickets || data.ticket_count || 0
    totalEquipment.value = data.total_equipment || data.equipment_count || 0
    totalProfit.value = data.total_profit || 0
    profitMargin.value = data.profit_margin || 0
    
    clientRanking.value = data.client_ranking || data.top_clients || []
    technicianRanking.value = data.technician_ranking || data.top_technicians || []
    
    if (data.warranty_stats) {
      warrantyIn.value = data.warranty_stats.inside || 0
      expiredWarranty.value = data.warranty_stats.expired || 0
      warrantyNone.value = data.warranty_stats.none || 0
    }
    
    await nextTick()
    renderCharts(data)
  } catch (e) {
    console.error('加载统计数据失败:', e)
  } finally {
    loading.value = false
  }
}

async function renderCharts(data) {
  const Chart = (await import('chart.js/auto')).default
  
  const destroyChart = (ref) => {
    if (ref?.value) {
      const instance = Chart.getChart(ref.value)
      if (instance) instance.destroy()
    }
  }
  
  destroyChart(statusChart)
  destroyChart(equipTypeChart)
  destroyChart(trendChart)
  destroyChart(warrantyChart)
  destroyChart(serviceTypeChart)
  
  chartInstances = []
  
  if (data.status_distribution && statusChart.value) {
    const ctx = statusChart.value.getContext('2d')
    chartInstances.push(new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: data.status_distribution.map(s => s.status),
        datasets: [{
          data: data.status_distribution.map(s => s.count),
          backgroundColor: ['#f59e0b', '#3b82f6', '#10b981', '#ef4444', '#6366f1', '#8b5cf6']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { position: 'bottom' } }
      }
    }))
  }
  
  if (data.equipment_type_distribution && equipTypeChart.value) {
    const ctx = equipTypeChart.value.getContext('2d')
    chartInstances.push(new Chart(ctx, {
      type: 'pie',
      data: {
        labels: data.equipment_type_distribution.map(e => e.type),
        datasets: [{
          data: data.equipment_type_distribution.map(e => e.count),
          backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { position: 'bottom' } }
      }
    }))
  }
  
  if (data.monthly_trend && trendChart.value) {
    const ctx = trendChart.value.getContext('2d')
    chartInstances.push(new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.monthly_trend.map(m => m.month),
        datasets: [{
          label: '收入',
          data: data.monthly_trend.map(m => m.income),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.3
        }, {
          label: '成本',
          data: data.monthly_trend.map(m => m.cost),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { position: 'bottom' } },
        scales: { y: { beginAtZero: true } }
      }
    }))
  }
  
  if (data.warranty_stats && warrantyChart.value) {
    const ctx = warrantyChart.value.getContext('2d')
    chartInstances.push(new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['保内', '过保', '未知'],
        datasets: [{
          data: [data.warranty_stats.inside || 0, data.warranty_stats.expired || 0, data.warranty_stats.none || 0],
          backgroundColor: ['#10b981', '#ef4444', '#9ca3af']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    }))
  }
  
  if (data.service_type_income && serviceTypeChart.value) {
    const ctx = serviceTypeChart.value.getContext('2d')
    chartInstances.push(new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.service_type_income.map(s => s.type),
        datasets: [{
          label: '收入',
          data: data.service_type_income.map(s => s.income),
          backgroundColor: '#3b82f6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        indexAxis: 'y',
        plugins: { legend: { display: false } }
      }
    }))
  }
}

onMounted(() => loadStats())

onUnmounted(() => {
  chartInstances.forEach(chart => chart.destroy())
})
</script>

<style scoped>
.bt-stat-profit { color: var(--bt-success); }

@media (max-width: 768px) {
  .chart-container {
    max-height: 180px;
    overflow: hidden;
  }
}

@media (max-width: 576px) {
  .chart-container {
    max-height: 150px;
  }
  
  .stat-value {
    font-size: 16px !important;
  }
}

[data-theme="dark"] .bt-stat-profit {
  color: #34d399;
}
</style>