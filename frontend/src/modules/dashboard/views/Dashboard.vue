<template>
  <div class="page-dashboard">
    <!-- Header -->
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div>
        <h2><i class="bi bi-speedometer2 me-2"></i>仪表盘</h2>
        <p>{{ currentDate }} · 系统正常运行</p>
      </div>
      <router-link to="/tickets/new" class="btn btn-primary">
        <i class="bi bi-plus-lg"></i> 新建工单
      </router-link>
    </div>

    <!-- Quick Stats -->
    <LoadingSkeleton v-if="loading" type="cards" :count="6" />
    <QuickStats
      v-else
      :stats="quickStats"
      class="mb-3"
      @click="handleStatClick"
    />

    <!-- Charts & Activity -->
    <div class="row g-3">
      <!-- Left Column: Chart + Recent Tickets -->
      <div class="col-12 col-lg-8">
        <!-- Status Chart -->
        <div class="card mb-3">
          <div class="card-body">
            <h6 class="card-title mb-3"><i class="bi bi-pie-chart me-2"></i>工单状态分布</h6>
            <div style="max-height: 220px;">
              <canvas ref="chartCanvas" height="180"></canvas>
            </div>
          </div>
        </div>

        <!-- Recent Tickets -->
        <div class="card">
          <div class="card-body">
            <div class="d-flex align-items-center justify-content-between mb-3">
              <h6 class="card-title mb-0"><i class="bi bi-ticket-perforated me-2"></i>最近工单</h6>
              <router-link to="/tickets" class="btn btn-sm btn-link text-decoration-none">查看全部</router-link>
            </div>
            <div v-if="!recentTickets.length" class="text-muted small text-center py-4">
              <i class="bi bi-inbox fs-4 d-block mb-2 opacity-50"></i>
              暂无工单
            </div>
            <div v-else class="recent-list">
              <div
                v-for="t in recentTickets.slice(0, 6)"
                :key="t.id"
                class="recent-item"
              >
                <div class="d-flex align-items-center gap-2">
                  <div class="recent-icon" :class="getStatusIconColor(t.status)">
                    <i :class="getStatusIcon(t.status)"></i>
                  </div>
                  <div class="flex-fill min-width-0">
                    <div class="d-flex align-items-center gap-2">
                      <router-link :to="'/tickets/' + t.id" class="text-decoration-none fw-medium text-truncate">
                        #{{ t.id }} {{ t.client }}
                      </router-link>
                      <StatusBadge :status="t.status" />
                    </div>
                    <div class="text-muted small text-truncate">{{ t.content?.slice(0, 30) }}</div>
                  </div>
                  <div class="text-muted small text-nowrap">{{ formatDate(t.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Activity Stream + Todos + Finance -->
      <div class="col-12 col-lg-4">
        <!-- Activity Stream -->
        <div class="card mb-3">
          <div class="card-body">
            <ActivityStream
              title="今日动态"
              :activities="todayActivities"
              :limit="6"
            />
          </div>
        </div>

        <!-- Monthly Finance -->
        <div class="card mb-3">
          <div class="card-body">
            <h6 class="card-title mb-3"><i class="bi bi-cash-coin me-2 text-success"></i>本月收支速览</h6>
            <div class="row text-center g-2">
              <div class="col-4">
                <div class="small text-muted mb-1">收入</div>
                <div class="fw-bold text-success">{{ formatMoney(dashboard.monthlyIncomeNum) }}</div>
              </div>
              <div class="col-4">
                <div class="small text-muted mb-1">支出</div>
                <div class="fw-bold text-danger">{{ formatMoney(dashboard.monthlyExpenseNum) }}</div>
              </div>
              <div class="col-4">
                <div class="small text-muted mb-1">利润</div>
                <div class="fw-bold" :class="(dashboard.monthlyProfit || 0) >= 0 ? 'text-success' : 'text-danger'">
                  {{ formatMoney(dashboard.monthlyProfit) }}
                </div>
              </div>
            </div>
            <div v-if="dashboard.monthlyIncomeNum" class="mt-3">
              <div class="d-flex justify-content-between small mb-1">
                <span class="text-muted">利润率</span>
                <span class="fw-medium">{{ profitRate }}%</span>
              </div>
              <div class="progress" style="height: 6px;">
                <div
                  class="progress-bar bg-success"
                  :style="{ width: `${Math.max(0, Math.min(profitRate, 100))}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Todos -->
        <div class="card mb-3">
          <div class="card-body">
            <div class="d-flex align-items-center justify-content-between mb-3">
              <h6 class="card-title mb-0"><i class="bi bi-bell me-2"></i>待办事项</h6>
              <router-link to="/todos" class="btn btn-sm btn-link text-decoration-none">查看全部</router-link>
            </div>
            <div v-if="!recentTodos.length" class="text-muted small text-center py-4">
              <i class="bi bi-check-circle fs-4 d-block mb-2 opacity-50"></i>
              暂无待办
            </div>
            <div v-else class="todo-list">
              <div
                v-for="t in recentTodos.slice(0, 5)"
                :key="t.id"
                class="todo-item"
                :class="{ 'done': t.done }"
              >
                <div class="d-flex align-items-center gap-2">
                  <i :class="t.done ? 'bi bi-check-circle-fill text-success' : 'bi bi-circle text-warning'"></i>
                  <span :class="t.done ? 'text-decoration-line-through text-muted' : ''" class="flex-fill text-truncate">
                    {{ t.title }}
                  </span>
                  <span class="badge" :class="t.done ? 'bg-success' : 'bg-warning text-dark'">
                    {{ t.done ? '完成' : '待办' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Stock Alerts -->
        <div class="card">
          <div class="card-body">
            <div class="d-flex align-items-center justify-content-between mb-3">
              <h6 class="card-title mb-0"><i class="bi bi-box-seam me-2 text-warning"></i>库存预警</h6>
              <router-link to="/inventory" class="btn btn-sm btn-link text-decoration-none">查看全部</router-link>
            </div>
            <div v-if="!alerts.length" class="text-muted small text-center py-4">
              <i class="bi bi-check-circle fs-4 d-block mb-2 opacity-50"></i>
              库存充足
            </div>
            <div v-else class="alert-list">
              <div
                v-for="a in alerts.slice(0, 5)"
                :key="a.id || a.goods_id"
                class="alert-item"
              >
                <div class="d-flex justify-content-between align-items-center">
                  <span class="text-truncate">{{ a.name || a.product_name }}</span>
                  <span class="badge bg-danger">{{ Number(a.quantity || 0) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as dashboardApi from '../api'
import QuickStats from '@/components/common/QuickStats.vue'
import ActivityStream from '@/components/common/ActivityStream.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { formatMoney, formatDate, formatRelativeTime } from '@/utils/format'
import '@/plugins/chart'
import { Chart } from 'chart.js'

const router = useRouter()

const dashboard = ref({})
const recentTickets = ref([])
const recentTodos = ref([])
const alerts = ref([])
const currentDate = ref('')
const chartCanvas = ref(null)
const loading = ref(true)
let statusChart = null

const quickStats = computed(() => [
  {
    key: 'open',
    icon: 'bi bi-inbox',
    iconColor: 'blue',
    value: dashboard.value.openTickets || 0,
    label: '待处理',
    pulse: (dashboard.value.openTickets || 0) > 0,
    route: '/tickets?status=open'
  },
  {
    key: 'today',
    icon: 'bi bi-calendar-check',
    iconColor: 'green',
    value: dashboard.value.todayTickets || 0,
    label: '今日新增',
    route: '/tickets?date=today'
  },
  {
    key: 'pending',
    icon: 'bi bi-credit-card',
    iconColor: 'yellow',
    value: dashboard.value.pendingPayment || 0,
    label: '待结算',
    pulse: (dashboard.value.pendingPayment || 0) > 0,
    route: '/tickets?status=pending-payment'
  },
  {
    key: 'income',
    icon: 'bi bi-cash-stack',
    iconColor: 'green',
    value: formatMoney(dashboard.value.monthlyIncome).replace('¥', ''),
    label: '本月收入',
    valueClass: 'text-success',
    route: '/finance'
  },
  {
    key: 'total',
    icon: 'bi bi-collection',
    iconColor: 'purple',
    value: dashboard.value.totalTickets || 0,
    label: '总工单',
    route: '/tickets'
  },
  {
    key: 'equipment',
    icon: 'bi bi-cpu',
    iconColor: 'orange',
    value: dashboard.value.equipmentCount || 0,
    label: '设备',
    route: '/equipment'
  }
])

const todayActivities = computed(() => {
  const acts = []

  recentTickets.value.forEach(t => {
    if (t.created_at) {
      const date = new Date(t.created_at)
      const now = new Date()
      if (date.toDateString() === now.toDateString()) {
        acts.push({
          id: `ticket-new-${t.id}`,
          icon: 'bi bi-plus-circle',
          iconColor: 'green',
          title: `新建工单 #${t.id}`,
          description: t.client,
          time: t.created_at,
          amount: t.total_amount
        })
      }
    }
    if (t.status === 'closed' && t.closed_at) {
      const date = new Date(t.closed_at)
      const now = new Date()
      if (date.toDateString() === now.toDateString()) {
        acts.push({
          id: `ticket-close-${t.id}`,
          icon: 'bi bi-check-circle',
          iconColor: 'blue',
          title: `完工结算 #${t.id}`,
          description: t.client,
          time: t.closed_at,
          amount: t.total_amount
        })
      }
    }
  })

  return acts.sort((a, b) => new Date(b.time) - new Date(a.time))
})

const profitRate = computed(() => {
  const income = dashboard.value.monthlyIncomeNum || 0
  if (!income) return 0
  const profit = dashboard.value.monthlyProfit || 0
  return Math.round((profit / income) * 100)
})

onMounted(async () => {
  currentDate.value = new Date().toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
  })

  try {
    const data = await dashboardApi.getSummary()
    dashboard.value = data || {}
    recentTickets.value = data?.recent_tickets || []
    recentTodos.value = data?.recent_todos || []
    await nextTick()
    renderChart(data?.all_statuses || {})
  } catch (e) {
    console.error('Dashboard load error:', e)
  }

  try {
    const data = await dashboardApi.getStockAlerts()
    alerts.value = Array.isArray(data) ? data : data?.alerts || []
  } catch (e) {
    // ignore
  }

  loading.value = false
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
      datasets: [{
        data: values,
        backgroundColor: ['#818cf8', '#fbbf24', '#f87171', '#34d399', '#94a3b8'],
        borderWidth: 2,
        borderColor: 'var(--card-bg, #ffffff)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '60%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 16,
            usePointStyle: true,
            pointStyle: 'circle',
            font: { size: 12 }
          }
        }
      }
    }
  })
}

function handleStatClick(stat) {
  if (stat.route) {
    router.push(stat.route)
  }
}

function getStatusIcon(status) {
  const map = {
    'open': 'bi bi-inbox',
    'in-progress': 'bi bi-arrow-repeat',
    'pending-parts': 'bi bi-box-seam',
    'pending-payment': 'bi bi-credit-card',
    'closed': 'bi bi-check-circle'
  }
  return map[status] || 'bi bi-circle'
}

function getStatusIconColor(status) {
  const map = {
    'open': 'blue',
    'in-progress': 'yellow',
    'pending-parts': 'red',
    'pending-payment': 'green',
    'closed': 'gray'
  }
  return map[status] || 'gray'
}
</script>

<style scoped>
.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--bt-gray-700);
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.recent-item {
  padding: 10px 12px;
  border-radius: var(--bt-radius-sm);
  transition: background 0.15s ease;
}

.recent-item:hover {
  background: var(--bt-gray-50);
}

.recent-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.recent-icon.blue { background: var(--bt-primary-100); color: var(--bt-primary-600); }
.recent-icon.yellow { background: var(--bt-warning-light); color: var(--bt-warning); }
.recent-icon.red { background: var(--bt-danger-light); color: var(--bt-danger); }
.recent-icon.green { background: var(--bt-success-light); color: var(--bt-success); }
.recent-icon.gray { background: var(--bt-gray-200); color: var(--bt-gray-500); }

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.todo-item {
  padding: 8px 12px;
  border-radius: var(--bt-radius-sm);
  transition: background 0.15s ease;
  font-size: 13px;
}

.todo-item:hover {
  background: var(--bt-gray-50);
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.alert-item {
  padding: 8px 12px;
  border-radius: var(--bt-radius-sm);
  transition: background 0.15s ease;
  font-size: 13px;
}

.alert-item:hover {
  background: var(--bt-gray-50);
}

.min-width-0 {
  min-width: 0;
}

.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 576px) {
  .card-title {
    font-size: 13px;
  }
}
</style>
