<template>
  <div class="page-expenses">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div>
        <h2><i class="bi bi-wallet2 me-2"></i>支出管理</h2>
        <p>支出分类管理 · 个人账本 · {{ expenses.length }} 笔</p>
      </div>
      <div class="d-flex gap-2 flex-wrap">
        <button class="btn btn-sm btn-outline-primary" @click="activeTab = 'personal'">个人账本</button>
        <button class="btn btn-sm btn-success" @click="openExpenseModal">
          <i class="bi bi-plus-lg me-1"></i>记支出
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="row g-2 mb-3">
      <div class="col-6 col-sm-3">
        <div class="card p-2 text-center">
          <div class="stat-value text-danger">{{ formatMoney(monthlyTotal) }}</div>
          <div class="stat-label">本月支出</div>
        </div>
      </div>
      <div class="col-6 col-sm-3">
        <div class="card p-2 text-center">
          <div class="stat-value">{{ categories.length }}</div>
          <div class="stat-label">支出分类</div>
        </div>
      </div>
      <div class="col-6 col-sm-3">
        <div class="card p-2 text-center">
          <div class="stat-value">{{ personalItems.length }}</div>
          <div class="stat-label">个人支出</div>
        </div>
      </div>
      <div class="col-6 col-sm-3">
        <div class="card p-2 text-center">
          <div class="stat-value">{{ personalBudget ? formatMoney(personalBudget) : '-' }}</div>
          <div class="stat-label">个人预算</div>
        </div>
      </div>
    </div>

    <!-- Tab 导航 -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <a class="nav-link" :class="{ active: activeTab === 'categories' }" href="#" @click.prevent="activeTab = 'categories'">支出分类</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{ active: activeTab === 'expenses' }" href="#" @click.prevent="activeTab = 'expenses'; loadExpenses()">支出记录</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{ active: activeTab === 'personal' }" href="#" @click.prevent="activeTab = 'personal'; loadPersonal()">个人账本</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{ active: activeTab === 'recurring' }" href="#" @click.prevent="activeTab = 'recurring'; loadRecurring()">周期支出</a>
      </li>
    </ul>

    <!-- 分类管理 -->
    <div v-if="activeTab === 'categories'" class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">支出分类</h5>
        <button class="btn btn-sm btn-primary" @click="openCategoryModal()"><i class="bi bi-plus-lg me-1"></i>新建分类</button>
      </div>
      <div class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>分类名称</th><th>描述</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="cat in categories" :key="cat.id">
              <td class="fw-bold">{{ cat.name }}</td>
              <td class="small text-muted">{{ cat.description || '-' }}</td>
              <td>
                <div class="d-flex gap-1">
                  <button class="btn btn-sm btn-outline-primary" @click="openCategoryModal(cat)">编辑</button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteCategory(cat)">删除</button>
                </div>
              </td>
            </tr>
            <tr v-if="categories.length === 0">
              <td colspan="3" class="text-center text-muted py-3">暂无分类，请新建</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 支出记录 -->
    <div v-if="activeTab === 'expenses'" class="card p-2">
      <div class="d-flex gap-2 mb-3">
        <input v-model="searchQuery" class="form-control form-control-sm" placeholder="搜索说明..." style="max-width:250px">
        <select v-model="categoryFilter" class="form-select form-select-sm" style="max-width:150px">
          <option value="">全部分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.name">{{ c.name }}</option>
        </select>
        <input type="month" v-model="monthFilter" class="form-control form-control-sm" style="max-width:160px">
      </div>
      <LoadingSkeleton v-if="expensesLoading" type="table" :count="5" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>分类</th><th>金额</th><th>说明</th><th>供应商</th><th>日期</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="e in filteredExpenses" :key="e.id">
              <td><span class="badge bg-secondary">{{ e.category }}</span></td>
              <td class="text-danger fw-bold">{{ formatMoney(e.amount) }}</td>
              <td>{{ e.description || '-' }}</td>
              <td class="small">{{ e.vendor || '-' }}</td>
              <td class="small text-muted">{{ (e.paid_at || '').slice(0, 10) }}</td>
              <td>
                <div class="d-flex gap-1">
                  <button class="btn btn-sm btn-outline-primary" @click="openExpenseModal(e)">编辑</button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteExpense(e)">删除</button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredExpenses.length === 0">
              <td colspan="6" class="text-center text-muted py-3">暂无支出记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 个人账本 -->
    <div v-if="activeTab === 'personal'" class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">个人账本</h5>
        <div class="d-flex gap-2">
          <button class="btn btn-sm btn-outline-warning" @click="openBudgetModal">预算设置</button>
          <button class="btn btn-sm btn-success" @click="openPersonalModal()"><i class="bi bi-plus-lg me-1"></i>记一笔</button>
        </div>
      </div>
      <LoadingSkeleton v-if="personalLoading" type="table" :count="5" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>分类</th><th>金额</th><th>说明</th><th>日期</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="item in personalItems" :key="item.id">
              <td><span class="badge bg-info text-dark">{{ item.category || '个人' }}</span></td>
              <td class="text-danger fw-bold">{{ formatMoney(item.amount) }}</td>
              <td>{{ item.description || '-' }}</td>
              <td class="small text-muted">{{ (item.paid_at || '').slice(0, 10) }}</td>
              <td>
                <div class="d-flex gap-1">
                  <button class="btn btn-sm btn-outline-primary" @click="openPersonalModal(item)">编辑</button>
                  <button class="btn btn-sm btn-outline-danger" @click="deletePersonalItem(item)">删除</button>
                </div>
              </td>
            </tr>
            <tr v-if="personalItems.length === 0">
              <td colspan="5" class="text-center text-muted py-3">暂无个人支出，点"记一笔"开始</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- 预算进度 -->
      <div v-if="personalBudget > 0" class="mt-3">
        <label class="form-label">预算使用进度（{{ formatMoney(personalTotal) }} / {{ formatMoney(personalBudget) }}）</label>
        <div class="progress" style="height:8px">
          <div class="progress-bar" :class="budgetPct >= 100 ? 'bg-danger' : budgetPct >= 80 ? 'bg-warning' : 'bg-success'"
               :style="{ width: Math.min(budgetPct, 100) + '%' }"></div>
        </div>
        <small class="text-muted">已使用 {{ budgetPct.toFixed(0) }}%</small>
      </div>
    </div>

    <!-- 周期支出 -->
    <div v-if="activeTab === 'recurring'" class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">周期支出</h5>
        <button class="btn btn-sm btn-primary" @click="openRecurringModal()"><i class="bi bi-plus-lg me-1"></i>新建</button>
      </div>
      <LoadingSkeleton v-if="recurringLoading" type="table" :count="3" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>名称</th><th>分类</th><th>金额</th><th>周期</th><th>下次日期</th></tr></thead>
          <tbody>
            <tr v-for="r in recurringList" :key="r.id">
              <td>{{ r.name }}</td>
              <td><span class="badge bg-secondary">{{ r.category }}</span></td>
              <td>{{ formatMoney(r.amount) }}</td>
              <td>{{ r.frequency || '每月' }}</td>
              <td class="small">{{ (r.next_date || '').slice(0, 10) }}</td>
            </tr>
            <tr v-if="recurringList.length === 0">
              <td colspan="5" class="text-center text-muted py-3">暂无周期支出</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 支出记录弹窗 -->
    <BtModal v-model:visible="showExpenseModal" :title="editingExpense ? '编辑支出' : '记支出'" icon="bi-dash-lg" max-width="500px" :show-footer="false">
      <template #body>
        <form @submit.prevent="saveExpense">
          <div class="mb-2">
            <label class="form-label">分类 <span class="text-danger">*</span></label>
            <select v-model="expenseForm.category" class="form-select form-select-sm" required>
              <option value="">请选择</option>
              <option v-for="c in categories" :key="c.id" :value="c.name">{{ c.name }}</option>
            </select>
          </div>
          <div class="mb-2">
            <label class="form-label">金额 <span class="text-danger">*</span></label>
            <input v-model.number="expenseForm.amount" type="number" step="0.01" class="form-control form-control-sm" required>
          </div>
          <div class="mb-2">
            <label class="form-label">说明</label>
            <input v-model="expenseForm.description" class="form-control form-control-sm">
          </div>
          <div class="mb-2">
            <label class="form-label">供应商</label>
            <input v-model="expenseForm.vendor" class="form-control form-control-sm">
          </div>
          <div class="mb-2">
            <label class="form-label">日期</label>
            <input v-model="expenseForm.date" type="date" class="form-control form-control-sm">
          </div>
          <div class="d-flex gap-2 justify-content-end mt-3">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showExpenseModal = false">取消</button>
            <button type="submit" class="btn btn-sm btn-danger" :disabled="saving">
              <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
              {{ editingExpense ? '更新' : '确认支出' }}
            </button>
          </div>
        </form>
      </template>
    </BtModal>

    <!-- 个人支出弹窗 -->
    <BtModal v-model:visible="showPersonalModal" :title="editingPersonal ? '编辑' : '记一笔'" icon="bi-wallet2" max-width="450px" :show-footer="false">
      <template #body>
        <form @submit.prevent="savePersonal">
          <div class="mb-2">
            <label class="form-label">分类</label>
            <input v-model="personalForm.category" class="form-control form-control-sm" placeholder="如：餐饮、交通">
          </div>
          <div class="mb-2">
            <label class="form-label">金额 <span class="text-danger">*</span></label>
            <input v-model.number="personalForm.amount" type="number" step="0.01" class="form-control form-control-sm" required>
          </div>
          <div class="mb-2">
            <label class="form-label">说明</label>
            <input v-model="personalForm.description" class="form-control form-control-sm">
          </div>
          <div class="mb-2">
            <label class="form-label">日期</label>
            <input v-model="personalForm.date" type="date" class="form-control form-control-sm">
          </div>
          <div class="d-flex gap-2 justify-content-end mt-3">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showPersonalModal = false">取消</button>
            <button type="submit" class="btn btn-sm btn-success" :disabled="saving">
              {{ editingPersonal ? '更新' : '保存' }}
            </button>
          </div>
        </form>
      </template>
    </BtModal>

    <!-- 预算设置弹窗 -->
    <BtModal v-model:visible="showBudgetModal" title="个人预算设置" icon="bi-piggy-bank" max-width="400px" :show-footer="false">
      <template #body>
        <form @submit.prevent="saveBudget">
          <div class="mb-3">
            <label class="form-label">每月预算（元）</label>
            <input v-model.number="budgetForm.amount" type="number" step="100" class="form-control form-control-sm" placeholder="留空则不限制">
          </div>
          <div class="d-flex gap-2 justify-content-end">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showBudgetModal = false">取消</button>
            <button type="submit" class="btn btn-sm btn-primary">保存</button>
          </div>
        </form>
      </template>
    </BtModal>

    <!-- 分类弹窗 -->
    <BtModal v-model:visible="showCategoryModal" :title="editingCategory ? '编辑分类' : '新建分类'" icon="bi-tags" max-width="400px" :show-footer="false">
      <template #body>
        <form @submit.prevent="saveCategory">
          <div class="mb-2">
            <label class="form-label">分类名称 <span class="text-danger">*</span></label>
            <input v-model="categoryForm.name" class="form-control form-control-sm" required>
          </div>
          <div class="mb-2">
            <label class="form-label">描述</label>
            <input v-model="categoryForm.description" class="form-control form-control-sm">
          </div>
          <div class="d-flex gap-2 justify-content-end mt-3">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showCategoryModal = false">取消</button>
            <button type="submit" class="btn btn-sm btn-primary">保存</button>
          </div>
        </form>
      </template>
    </BtModal>

    <!-- 周期支出弹窗 -->
    <BtModal v-model:visible="showRecurringModal" title="新建周期支出" icon="bi-arrow-repeat" max-width="450px" :show-footer="false">
      <template #body>
        <form @submit.prevent="saveRecurring">
          <div class="mb-2">
            <label class="form-label">名称</label>
            <input v-model="recurringForm.name" class="form-control form-control-sm">
          </div>
          <div class="mb-2">
            <label class="form-label">分类</label>
            <select v-model="recurringForm.category" class="form-select form-select-sm">
              <option value="个人">个人</option>
              <option value="房租">房租</option>
              <option value="订阅">订阅</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="mb-2">
            <label class="form-label">金额</label>
            <input v-model.number="recurringForm.amount" type="number" step="0.01" class="form-control form-control-sm">
          </div>
          <div class="d-flex gap-2 justify-content-end mt-3">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showRecurringModal = false">取消</button>
            <button type="submit" class="btn btn-sm btn-primary">保存</button>
          </div>
        </form>
      </template>
    </BtModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { expenseApi } from '@/api/expenses'
import { useToast } from '@/composables/useToast'
import { formatMoney } from '@/utils/format'
import BtModal from '@/components/common/BtModal.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'

const { show: showToast } = useToast()

const activeTab = ref('categories')
const loading = ref(false)
const saving = ref(false)

// 分类
const categories = ref([])
const showCategoryModal = ref(false)
const editingCategory = ref(null)
const categoryForm = ref({ name: '', description: '' })

// 支出记录
const expenses = ref([])
const expensesLoading = ref(false)
const searchQuery = ref('')
const categoryFilter = ref('')
const monthFilter = ref('')

// 个人账本
const personalItems = ref([])
const personalLoading = ref(false)
const personalBudget = ref(0)
const showPersonalModal = ref(false)
const editingPersonal = ref(null)
const personalForm = ref({ category: '个人', amount: '', description: '', date: '' })

// 周期支出
const recurringList = ref([])
const recurringLoading = ref(false)
const showRecurringModal = ref(false)
const recurringForm = ref({ name: '', category: '个人', amount: '' })

// 预算
const showBudgetModal = ref(false)
const budgetForm = ref({ amount: '' })

// 支出记录弹窗
const showExpenseModal = ref(false)
const editingExpense = ref(null)
const expenseForm = ref({ category: '', amount: '', description: '', vendor: '', date: '' })

const monthlyTotal = computed(() => {
  const m = (monthFilter.value || new Date().toISOString().slice(0, 7))
  return expenses.value.filter(e => (e.paid_at || '').slice(0, 7) === m).reduce((s, e) => s + parseFloat(e.amount || 0), 0)
})

const personalTotal = computed(() =>
  personalItems.value.reduce((s, e) => s + parseFloat(e.amount || 0), 0)
)

const budgetPct = computed(() =>
  personalBudget.value > 0 ? (personalTotal.value / personalBudget.value) * 100 : 0
)

const filteredExpenses = computed(() => {
  let result = expenses.value
  if (categoryFilter.value) result = result.filter(e => e.category === categoryFilter.value)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(e => (e.description || '').toLowerCase().includes(q) || (e.vendor || '').toLowerCase().includes(q))
  }
  if (monthFilter.value) result = result.filter(e => (e.paid_at || '').slice(0, 7) === monthFilter.value)
  return result
})

function todayStr() { return new Date().toISOString().slice(0, 10) }

onMounted(async () => {
  await loadCategories()
  await loadPersonal()
  personalBudget.value = await loadBudget()
})

async function loadCategories() {
  try {
    const data = await expenseApi.listCategories()
    categories.value = Array.isArray(data) ? data : data?.categories || []
  } catch (e) { console.error(e) }
}

async function loadExpenses() {
  expensesLoading.value = true
  try {
    const data = await expenseApi.list()
    expenses.value = Array.isArray(data) ? data : data?.expenses || data?.data || []
  } catch (e) { console.error(e); expenses.value = [] }
  finally { expensesLoading.value = false }
}

async function loadPersonal() {
  personalLoading.value = true
  try {
    const data = await expenseApi.listPersonal()
    personalItems.value = Array.isArray(data) ? data : data?.items || []
  } catch (e) { console.error(e); personalItems.value = [] }
  finally { personalLoading.value = false }
}

async function loadBudget() {
  try {
    const data = await expenseApi.getPersonalBudget()
    return data?.budget || data?.amount || 0
  } catch (e) { return 0 }
}

async function loadRecurring() {
  recurringLoading.value = true
  try {
    const data = await expenseApi.listRecurring()
    recurringList.value = Array.isArray(data) ? data : data?.items || []
  } catch (e) { console.error(e); recurringList.value = [] }
  finally { recurringLoading.value = false }
}

// ── 分类操作 ──
function openCategoryModal(cat = null) {
  editingCategory.value = cat
  categoryForm.value = cat ? { name: cat.name, description: cat.description || '' } : { name: '', description: '' }
  showCategoryModal.value = true
}

async function saveCategory() {
  saving.value = true
  try {
    if (editingCategory.value) {
      await expenseApi.updateCategory({ id: editingCategory.value.id, ...categoryForm.value })
      showToast('分类已更新', 'success')
    } else {
      await expenseApi.createCategory(categoryForm.value)
      showToast('分类已创建', 'success')
    }
    showCategoryModal.value = false
    await loadCategories()
  } catch (e) { showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { saving.value = false }
}

async function deleteCategory(cat) {
  if (!confirm(`确认删除分类「${cat.name}」？`)) return
  try {
    await expenseApi.deleteCategory(cat.id)
    showToast('分类已删除', 'success')
    await loadCategories()
  } catch (e) { showToast('删除失败', 'danger') }
}

// ── 支出记录操作 ──
function openExpenseModal(e = null) {
  editingExpense.value = e
  expenseForm.value = e
    ? { category: e.category, amount: e.amount, description: e.description || '', vendor: e.vendor || '', date: (e.paid_at || '').slice(0, 10) }
    : { category: '', amount: '', description: '', vendor: '', date: todayStr() }
  showExpenseModal.value = true
}

async function saveExpense() {
  saving.value = true
  try {
    const payload = {
      ...expenseForm.value,
      paid_at: expenseForm.value.date,
    }
    if (editingExpense.value) {
      await expenseApi.update(editingExpense.value.id, payload)
      showToast('支出已更新', 'success')
    } else {
      await expenseApi.create(payload)
      showToast('支出已记录', 'success')
    }
    showExpenseModal.value = false
    await loadExpenses()
  } catch (e) { showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { saving.value = false }
}

async function deleteExpense(e) {
  if (!confirm('确认删除该支出记录？')) return
  try {
    await expenseApi.delete(e.id)
    showToast('支出已删除', 'success')
    await loadExpenses()
  } catch (e) { showToast('删除失败', 'danger') }
}

// ── 个人账本操作 ──
function openPersonalModal(item = null) {
  editingPersonal.value = item
  personalForm.value = item
    ? { category: item.category || '个人', amount: item.amount, description: item.description || '', date: (item.paid_at || '').slice(0, 10) }
    : { category: '个人', amount: '', description: '', date: todayStr() }
  showPersonalModal.value = true
}

async function savePersonal() {
  saving.value = true
  try {
    const payload = { ...personalForm.value, paid_at: personalForm.value.date }
    if (editingPersonal.value) {
      await expenseApi.updatePersonalItem(editingPersonal.value.id, payload)
      showToast('已更新', 'success')
    } else {
      await expenseApi.addPersonal(payload)
      showToast('已记录', 'success')
    }
    showPersonalModal.value = false
    await loadPersonal()
    personalBudget.value = await loadBudget()
  } catch (e) { showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { saving.value = false }
}

async function deletePersonalItem(item) {
  if (!confirm('确认删除？')) return
  try {
    await expenseApi.deletePersonalItem(item.id)
    showToast('已删除', 'success')
    await loadPersonal()
  } catch (e) { showToast('删除失败', 'danger') }
}

// ── 预算 ──
function openBudgetModal() {
  budgetForm.value = { amount: personalBudget.value || '' }
  showBudgetModal.value = true
}

async function saveBudget() {
  saving.value = true
  try {
    await expenseApi.setPersonalBudget({ budget: budgetForm.value.amount || null })
    personalBudget.value = budgetForm.value.amount || 0
    showToast('预算已保存', 'success')
    showBudgetModal.value = false
  } catch (e) { showToast('保存失败', 'danger') }
  finally { saving.value = false }
}

// ── 周期支出 ──
function openRecurringModal() {
  recurringForm.value = { name: '', category: '个人', amount: '' }
  showRecurringModal.value = true
}

async function saveRecurring() {
  saving.value = true
  try {
    await expenseApi.createRecurring(recurringForm.value)
    showToast('周期支出已创建', 'success')
    showRecurringModal.value = false
    await loadRecurring()
  } catch (e) { showToast('保存失败', 'danger') }
  finally { saving.value = false }
}
</script>
