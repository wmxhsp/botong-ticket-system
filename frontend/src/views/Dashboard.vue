<template>
  <div class="page-dashboard">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div><h2><i class="bi bi-speedometer2 me-2"></i>仪表盘</h2><p>{{ currentDate }} · 系统正常运行</p></div>
      <router-link to="/tickets/new" class="btn btn-primary"><i class="bi bi-plus-lg"></i> 新建工单</router-link>
    </div>

    <!-- Stats Cards: 手机一行3个，平板一行4个，桌面一行6个 -->
    <LoadingSkeleton v-if="!dashboard.openTickets && dashboard.openTickets !== 0" type="cards" :count="6" />
    <div v-else class="row g-2 mb-2">
      <div class="col-4 col-sm-3 col-md-2"><div class="card p-2 text-center"><div class="stat-value">{{ dashboard.openTickets || 0 }}</div><div class="stat-label">待处理</div></div></div>
      <div class="col-4 col-sm-3 col-md-2"><div class="card p-2 text-center"><div class="stat-value text-primary">{{ dashboard.todayTickets || 0 }}</div><div class="stat-label">今日新增</div></div></div>
      <div class="col-4 col-sm-3 col-md-2"><div class="card p-2 text-center"><div class="stat-value text-warning">{{ dashboard.pendingPayment || 0 }}</div><div class="stat-label">待结算</div></div></div>
      <div class="col-4 col-sm-3 col-md-2"><div class="card p-2 text-center"><div class="stat-value text-success">{{ formatMoney(dashboard.monthlyIncome) }}</div><div class="stat-label">本月收入</div></div></div>
      <div class="col-4 col-sm-3 col-md-2"><div class="card p-2 text-center"><div class="stat-value">{{ dashboard.totalTickets || 0 }}</div><div class="stat-label">总工单</div></div></div>
      <div class="col-4 col-sm-3 col-md-2"><div class="card p-2 text-center"><div class="stat-value text-info">{{ dashboard.equipmentCount || 0 }}</div><div class="stat-label">设备</div></div></div>
    </div>

    <!-- Chart -->
    <div class="row g-2 mb-2">
      <div class="col-12 col-md-6"><div class="card p-2"><h6 class="mb-1"><i class="bi bi-pie-chart me-2"></i>工单状态分布</h6>
        <canvas ref="chartCanvas" height="130"></canvas>
      </div></div>
    </div>

    <!-- Charts and Recent Data -->
    <div class="row g-2">
      <div class="col-md-6"><div class="card p-2"><h6 class="mb-1"><i class="bi bi-ticket-perforated me-2"></i>最近工单</h6>
        <div v-if="!recentTickets.length" class="text-muted small">暂无数据</div>
        <div v-for="t in recentTickets.slice(0, 5)" :key="t.id" class="d-flex justify-content-between align-items-center py-1 border-bottom" style="font-size:12px">
          <div><router-link :to="'/tickets/' + t.id" class="text-decoration-none fw-medium">#{{ t.id }} {{ t.client }}</router-link>
            <span class="text-muted ms-2 small">{{ t.content?.slice(0, 20) }}</span></div>
          <StatusBadge :status="t.status" />
        </div>
      </div></div>
      <div class="col-md-6"><div class="card p-2"><h6 class="mb-1"><i class="bi bi-bell me-2"></i>待办事项</h6>
        <div v-if="!recentTodos.length" class="text-muted small">暂无待办</div>
        <div v-for="t in recentTodos.slice(0, 5)" :key="t.id" class="d-flex justify-content-between align-items-center py-1 border-bottom" style="font-size:12px">
          <div><span :class="t.done ? 'text-decoration-line-through text-muted' : ''">{{ t.title }}</span></div>
          <span class="badge" :class="t.done ? 'bg-success' : 'bg-warning text-dark'">{{ t.done ? '完成' : '待办' }}</span>
        </div>
      </div></div>
    </div>

    <!-- Second Row of Panels -->
    <div class="row g-2 mt-1">
      <div class="col-md-6"><div class="card p-2"><h6 class="mb-1"><i class="bi bi-cash-coin me-2 text-success"></i>本月收支速览</h6>
        <div class="row text-center">
          <div class="col-4"><div class="small text-muted">收入</div><div class="fw-bold text-success">{{ formatMoney(dashboard.monthlyIncomeNum) }}</div></div>
          <div class="col-4"><div class="small text-muted">支出</div><div class="fw-bold text-danger">{{ formatMoney(dashboard.monthlyExpenseNum) }}</div></div>
          <div class="col-4"><div class="small text-muted">利润</div><div class="fw-bold" :class="(dashboard.monthlyProfit || 0) >= 0 ? 'text-success' : 'text-danger'">{{ formatMoney(dashboard.monthlyProfit) }}</div></div>
        </div>
      </div></div>
      <div class="col-md-6"><div class="card p-2"><h6 class="mb-1"><i class="bi bi-box-seam me-2 text-warning"></i>库存预警</h6>
        <div v-if="!alerts.length" class="text-muted small">库存充足</div>
        <div v-for="a in alerts.slice(0, 5)" :key="a.id || a.goods_id" class="d-flex justify-content-between align-items-center py-1 border-bottom" style="font-size:12px">
          <span>{{ a.name || a.product_name }}</span>
          <span class="text-danger">库存: {{ Number(a.quantity || 0) }}</span>
        </div>
      </div></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { formatMoney } from '@/utils/format'
import '@/plugins/chart'
import { Chart } from 'chart.js'

const dashboard = ref({})
const recentTickets = ref([])
const recentTodos = ref([])
const alerts = ref([])
const currentDate = ref('')
const chartCanvas = ref(null)
let statusChart = null

onMounted(async () => {
  currentDate.value = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
  try {
    const data = await dashboardApi.getSummary()
    dashboard.value = data || {}
    recentTickets.value = data?.recent_tickets || []
    recentTodos.value = data?.recent_todos || []
    await nextTick()
    renderChart(data?.all_statuses || {})
  } catch (e) { console.error('Dashboard load error:', e) }
  try {
    const data = await dashboardApi.getStockAlerts()
    alerts.value = Array.isArray(data) ? data : data?.alerts || []
  } catch (e) { /* ignore */ }
})

onBeforeUnmount(() => {
  if (statusChart) {
    statusChart.destroy()
    statusChart = null
  }
})

function renderChart(stats) {
  if (!chartCanvas.value) return
  const keys = ['open', 'in-progress', 'pending-parts', 'pending-payment', 'closed']
  const names = ['待处理', '进行中', '待配件', '待结算', '已完成']
  const values = keys.map(k => stats[k] || 0)
  if (statusChart) statusChart.destroy()
  statusChart = new Chart(chartCanvas.value, {
    type: 'doughnut',
    data: {
      labels: names,
      datasets: [{ data: values, backgroundColor: ['#818cf8','#fbbf24','#f87171','#34d399','#94a3b8'], borderWidth: 0 }]
    },
    options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { padding: 12, font: {size:11} } } } }
  })
}
</script>
