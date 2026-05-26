<template>
  <div>
    <div class="bt-page-title d-flex justify-content-between align-items-center flex-wrap gap-2">
      <div>
        <h2>财务管理</h2>
        <p class="d-none d-md-inline">{{ dateRangeLabel }} 财务概况</p>
      </div>
      <div class="finance-toolbar d-flex gap-2 align-items-center flex-wrap">
        <input type="month" class="form-control form-control-sm finance-month-input" v-model="selectedMonth" @change="loadData">
        <button class="btn btn-success btn-sm" @click="openIncomeModal">
          <i class="bi bi-plus-lg me-1"></i><span class="d-none d-sm-inline">记收入</span><span class="d-sm-none">收入</span>
        </button>
        <button class="btn btn-danger btn-sm" @click="openExpenseModal">
          <i class="bi bi-dash-lg me-1"></i><span class="d-none d-sm-inline">记支出</span><span class="d-sm-none">支出</span>
        </button>
      </div>
    </div>

    <div class="row g-2 mb-3">
      <div class="col-6 col-sm-4 col-lg-3">
        <div class="card p-2 text-center">
          <div class="stat-value bt-finance-income">
            {{ formatMoney(summary.monthly_income) }}
          </div>
          <div class="stat-label">本月收入</div>
        </div>
      </div>
      <div class="col-6 col-sm-4 col-lg-3">
        <div class="card p-2 text-center">
          <div class="stat-value bt-finance-expense">
            {{ formatMoney(summary.monthly_expense) }}
          </div>
          <div class="stat-label">本月支出</div>
        </div>
      </div>
      <div class="col-6 col-sm-4 col-lg-3">
        <div class="card p-2 text-center">
          <div class="stat-value bt-finance-profit">
            {{ formatMoney(summary.monthly_profit) }}
          </div>
          <div class="stat-label">本月利润</div>
        </div>
      </div>
      <div class="col-6 col-sm-4 col-lg-3">
        <div class="card p-2 text-center">
          <div class="stat-value" :class="{ 'bt-finance-unpaid': summary.unpaid_count > 0 }">
            {{ summary.unpaid_count }} 单
          </div>
          <div class="stat-label">未收款 · {{ formatMoney(summary.total_unpaid) }}</div>
        </div>
      </div>
    </div>

    <div class="card p-2 mb-3">
      <h5 class="mb-3"><i class="bi bi-cash-stack me-2 text-success"></i>收入记录</h5>
      <LoadingSkeleton v-if="loading" type="table" :count="5" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead>
            <tr>
              <th>客户</th>
              <th>金额</th>
              <th>方式</th>
              <th>描述</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in incomeRecords" :key="r.id">
              <td data-label="客户">{{ r.client || '-' }}</td>
              <td data-label="金额" class="bt-income-cell">{{ formatMoney(r.amount) }}</td>
              <td data-label="方式">{{ r.payment_method || '-' }}</td>
              <td data-label="描述">{{ r.description || '-' }}</td>
              <td data-label="时间">{{ formatDateTime(r.received_at) }}</td>
            </tr>
            <tr v-if="incomeRecords.length === 0">
              <td colspan="5" class="text-center text-muted py-3">暂无收入记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card p-2 mb-3">
      <h5 class="mb-3"><i class="bi bi-cash me-2 text-danger"></i>支出记录</h5>
      <LoadingSkeleton v-if="loading" type="table" :count="5" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>类别</th><th>金额</th><th>说明</th><th>时间</th></tr></thead>
          <tbody>
            <tr v-for="r in expenseRecords" :key="r.id">
              <td data-label="类别"><span class="badge bg-secondary">{{ r.category || '-' }}</span></td>
              <td data-label="金额" class="bt-expense-cell">{{ formatMoney(r.amount) }}</td>
              <td data-label="说明">{{ r.description || '-' }}</td>
              <td data-label="时间">{{ formatDateTime(r.paid_at) }}</td>
            </tr>
            <tr v-if="expenseRecords.length === 0"><td colspan="4" class="text-center text-muted py-3">暂无支出记录</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card p-2">
      <h5 class="mb-3">
        <i class="bi bi-exclamation-circle me-2 text-warning"></i>待收款工单
        <span class="badge bg-warning ms-2">{{ unpaidTickets.length }}</span>
      </h5>
      <LoadingSkeleton v-if="loading" type="table" :count="5" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead>
            <tr>
              <th>工单号</th>
              <th>客户</th>
              <th>金额</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in unpaidTickets" :key="t.id">
              <td data-label="工单号"><strong>{{ t.ticket_no || '-' }}</strong></td>
              <td data-label="客户">{{ t.client || '-' }}</td>
              <td data-label="金额">{{ formatMoney(t.total || t.amount) }}</td>
              <td data-label="状态"><StatusBadge :status="t.status" /></td>
              <td data-label="操作">
                <router-link :to="'/tickets/' + t.id" class="btn btn-sm btn-outline-primary">处理</router-link>
              </td>
            </tr>
            <tr v-if="unpaidTickets.length === 0">
              <td colspan="5" class="text-center text-muted py-3">暂无待收款工单</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="modal fade" id="incomeModal" tabindex="-1" ref="incomeModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">记录收入</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-2">
              <label class="form-label">金额 <span class="text-danger">*</span></label>
              <input type="number" step="0.01" class="form-control form-control-sm" v-model="incomeForm.amount">
            </div>
            <div class="mb-2">
              <label class="form-label">客户</label>
              <ClientSelector v-model="incomeForm.client" />
            </div>
            <div class="mb-2">
              <label class="form-label">收款方式</label>
              <select class="form-select form-select-sm" v-model="incomeForm.method">
                <option value="微信">微信</option>
                <option value="支付宝">支付宝</option>
                <option value="现金">现金</option>
                <option value="银行转账">银行转账</option>
              </select>
            </div>
            <div class="mb-2">
              <label class="form-label">描述</label>
              <input class="form-control form-control-sm" v-model="incomeForm.description">
            </div>
            <div class="mb-2">
              <label class="form-label">日期</label>
              <input type="date" class="form-control form-control-sm" v-model="incomeForm.date">
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-sm btn-success" @click="submitIncome" :disabled="submitting">
              <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
              确认录入
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="expenseModal" tabindex="-1" ref="expenseModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">记录支出</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-2">
              <label class="form-label">支出类别</label>
              <select class="form-select form-select-sm" v-model="expenseForm.category">
                <option value="配件采购">配件采购</option>
                <option value="工具耗材">工具耗材</option>
                <option value="交通费用">交通费用</option>
                <option value="人工费用">人工费用</option>
                <option value="办公费用">办公费用</option>
                <option value="其他">其他</option>
              </select>
            </div>
            <div class="mb-2">
              <label class="form-label">金额 <span class="text-danger">*</span></label>
              <input type="number" step="0.01" class="form-control form-control-sm" v-model="expenseForm.amount">
            </div>
            <div class="mb-2">
              <label class="form-label">说明</label>
              <input class="form-control form-control-sm" v-model="expenseForm.description">
            </div>
            <div class="mb-2">
              <label class="form-label">供应商</label>
              <input class="form-control form-control-sm" v-model="expenseForm.vendor">
            </div>
            <div class="mb-2">
              <label class="form-label">日期</label>
              <input type="date" class="form-control form-control-sm" v-model="expenseForm.date">
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-sm btn-danger" @click="submitExpense" :disabled="submitting">
              <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
              确认录入
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { financeApi } from '@/api/finance'
import { useToast } from '@/composables/useToast'
import { formatMoney, formatDateTime } from '@/utils/format'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ClientSelector from '@/components/selectors/ClientSelector.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'

const { show: showToast } = useToast()

const selectedMonth = ref(new Date().toISOString().slice(0, 7))
const dateRangeLabel = computed(() => {
  const [y, m] = (selectedMonth.value || '').split('-')
  if (y && m) return `${y}年${parseInt(m)}月`
  return '本月'
})

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

const summary = ref({})
const incomeRecords = ref([])
const expenseRecords = ref([])
const unpaidTickets = ref([])
const loading = ref(true)
const submitting = ref(false)
const incomeModalEl = ref(null)
const expenseModalEl = ref(null)

const incomeForm = ref({ amount: '', method: '微信', description: '', date: todayStr(), client: '' })
const expenseForm = ref({ category: '配件采购', amount: '', description: '', vendor: '', date: todayStr() })

let incomeModalInstance = null
let expenseModalInstance = null

function getIncomeModal() {
  if (!incomeModalInstance) {
    incomeModalInstance = new window.bootstrap.Modal(incomeModalEl.value)
  }
  return incomeModalInstance
}

function getExpenseModal() {
  if (!expenseModalInstance) {
    expenseModalInstance = new window.bootstrap.Modal(expenseModalEl.value)
  }
  return expenseModalInstance
}

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const params = {}
    if (selectedMonth.value) {
      const [y, m] = selectedMonth.value.split('-')
      params.month = `${y}-${m}`
    }
    const [sumRes, expRes] = await Promise.all([
      financeApi.getSummary(params),
      financeApi.getExpenses(params),
    ])
    summary.value = sumRes || {}
    incomeRecords.value = sumRes?.income_history || []
    unpaidTickets.value = sumRes?.unpaid_tickets || []
    expenseRecords.value = Array.isArray(expRes) ? expRes : expRes?.expenses || expRes?.data || []
  } catch (e) { console.error('加载财务数据失败:', e); showToast('加载财务数据失败', 'danger') }
  finally { loading.value = false }
}

function openIncomeModal() {
  incomeForm.value = { amount: '', method: '微信', description: '', date: todayStr(), client: '' }
  getIncomeModal().show()
}

function openExpenseModal() {
  expenseForm.value = { category: '配件采购', amount: '', description: '', vendor: '', date: todayStr() }
  getExpenseModal().show()
}

async function submitIncome() {
  if (!incomeForm.value.amount || parseFloat(incomeForm.value.amount) <= 0) {
    showToast('请填写有效金额', 'warning')
    return
  }
  submitting.value = true
  try {
    await financeApi.recordIncome(incomeForm.value)
    showToast('收入录入成功', 'success')
    getIncomeModal().hide()
    await loadData()
  } catch (e) {
    showToast(e.response?.data?.error || '录入失败', 'danger')
  } finally {
    submitting.value = false
  }
}

async function submitExpense() {
  if (!expenseForm.value.amount || parseFloat(expenseForm.value.amount) <= 0) {
    showToast('请填写有效金额', 'warning')
    return
  }
  submitting.value = true
  try {
    await financeApi.recordExpense(expenseForm.value)
    showToast('支出录入成功', 'success')
    getExpenseModal().hide()
    await loadData()
  } catch (e) {
    showToast(e.response?.data?.error || '录入失败', 'danger')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.bt-finance-income { color: var(--bt-accent-green); }
.bt-finance-expense { color: var(--bt-danger); }
.bt-finance-profit { color: var(--bt-text-heading); }
.bt-finance-unpaid { color: var(--bt-danger); }
.bt-income-cell { color: var(--bt-accent-green); }
.bt-expense-cell { color: var(--bt-danger); }

@media (max-width: 576px) {
  .finance-toolbar {
    width: 100%;
    justify-content: flex-start;
  }
  
  .finance-month-input {
    flex: 1;
    min-width: 120px;
  }
  
  .finance-toolbar .btn {
    flex: 1;
  }
}

[data-theme="dark"] .bt-finance-income { color: #34d399; }
[data-theme="dark"] .bt-finance-expense { color: #f87171; }
[data-theme="dark"] .bt-finance-unpaid { color: #f87171; }
[data-theme="dark"] .bt-income-cell { color: #34d399; }
[data-theme="dark"] .bt-expense-cell { color: #f87171; }
</style>