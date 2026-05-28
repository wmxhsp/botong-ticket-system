<template>
  <div class="page-purchase">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div>
        <h2><i class="bi bi-cart-check me-2"></i>采购管理</h2>
        <p>采购订单管理 · {{ orders.length }} 条</p>
      </div>
      <div class="d-flex gap-2 flex-wrap">
        <button class="btn btn-sm btn-outline-warning" @click="activeTab = 'unpaid'" v-if="unpaidCount">
          待付款 ({{ unpaidCount }})
        </button>
        <button class="btn btn-sm btn-primary" @click="openCreateModal">
          <i class="bi bi-plus-lg me-1"></i>新建采购
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="row g-2 mb-3">
      <div class="col-6 col-sm-3">
        <div class="card p-2 text-center">
          <div class="stat-value">{{ stats.total_orders || orders.length }}</div>
          <div class="stat-label">采购单总数</div>
        </div>
      </div>
      <div class="col-6 col-sm-3">
        <div class="card p-2 text-center">
          <div class="stat-value text-warning">{{ stats.pending_orders || '-' }}</div>
          <div class="stat-label">待收货</div>
        </div>
      </div>
      <div class="col-6 col-sm-3">
        <div class="card p-2 text-center">
          <div class="stat-value text-danger">{{ unpaidCount }}</div>
          <div class="stat-label">待付款</div>
        </div>
      </div>
      <div class="col-6 col-sm-3">
        <div class="card p-2 text-center">
          <div class="stat-value">{{ formatMoney(stats.total_amount) }}</div>
          <div class="stat-label">采购总额</div>
        </div>
      </div>
    </div>

    <!-- Tab 导航 -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <a class="nav-link" :class="{ active: activeTab === 'list' }" href="#" @click.prevent="activeTab = 'list'">采购列表</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{ active: activeTab === 'unpaid' }" href="#" @click.prevent="activeTab = 'unpaid'; loadUnpaid()">
          待付款
        </a>
      </li>
    </ul>

    <!-- 采购列表 -->
    <div v-if="activeTab === 'list'" class="card p-2">
      <div class="d-flex gap-2 mb-3">
        <input v-model="searchQuery" class="form-control form-control-sm" placeholder="搜索采购单..." style="max-width:300px" @input="debouncedLoad">
        <select v-model="statusFilter" class="form-select form-select-sm" style="max-width:150px" @change="loadOrders">
          <option value="">全部状态</option>
          <option value="pending">待确认</option>
          <option value="confirmed">已确认</option>
          <option value="received">已收货</option>
          <option value="partial">部分收货</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>
      <LoadingSkeleton v-if="loading" type="table" :count="5" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead>
            <tr><th>采购单号</th><th>供应商</th><th>商品</th><th>数量</th><th>金额</th><th>状态</th><th>日期</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="po in filteredOrders" :key="po.id">
              <td class="fw-bold">{{ po.order_no || po.po_number || `PO-${po.id}` }}</td>
              <td>{{ po.supplier_name || po.supplier || '-' }}</td>
              <td class="small">{{ po.product_name || po.goods_name || '-' }}</td>
              <td>{{ po.quantity || '-' }}</td>
              <td>{{ formatMoney(po.total_amount || po.amount) }}</td>
              <td>
                <span class="badge" :class="poStatusClass(po.status)">{{ poStatusLabel(po.status) }}</span>
              </td>
              <td class="small text-muted">{{ (po.created_at || '').slice(0, 10) }}</td>
              <td>
                <div class="d-flex gap-1">
                  <button v-if="po.status === 'pending' || po.status === 'confirmed'" class="btn btn-sm btn-outline-success" @click="receiveOrder(po)">收货</button>
                  <button v-if="po.status === 'received' && !po.paid" class="btn btn-sm btn-outline-warning" @click="payOrder(po)">付款</button>
                  <button class="btn btn-sm btn-outline-primary" @click="viewOrder(po)">详情</button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredOrders.length === 0">
              <td colspan="8" class="text-center text-muted py-3">暂无采购单</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 待付款 -->
    <div v-if="activeTab === 'unpaid'" class="card p-2">
      <LoadingSkeleton v-if="unpaidLoading" type="table" :count="5" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>采购单号</th><th>供应商</th><th>金额</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="po in unpaidOrders" :key="po.id">
              <td class="fw-bold">{{ po.order_no || `PO-${po.id}` }}</td>
              <td>{{ po.supplier_name || po.supplier || '-' }}</td>
              <td class="text-danger">{{ formatMoney(po.total_amount || po.amount) }}</td>
              <td><button class="btn btn-sm btn-warning" @click="payOrder(po)">付款</button></td>
            </tr>
            <tr v-if="unpaidOrders.length === 0"><td colspan="4" class="text-center text-muted py-3">无待付款</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 新建采购弹窗 -->
    <BtModal v-model:visible="showCreateModal" title="新建采购单" icon="bi-cart-plus" max-width="550px" :show-footer="false">
      <template #body>
        <form @submit.prevent="createOrder">
          <div class="mb-3">
            <label class="form-label">供应商 <span class="text-danger">*</span></label>
            <input v-model="form.supplier_name" class="form-control form-control-sm" placeholder="供应商名称" required>
          </div>
          <div class="mb-3">
            <label class="form-label">商品名称 <span class="text-danger">*</span></label>
            <input v-model="form.product_name" class="form-control form-control-sm" placeholder="商品名称" required>
          </div>
          <div class="row g-2 mb-3">
            <div class="col-4">
              <label class="form-label">数量</label>
              <input v-model.number="form.quantity" type="number" class="form-control form-control-sm" min="1" required>
            </div>
            <div class="col-4">
              <label class="form-label">单价</label>
              <input v-model.number="form.unit_price" type="number" step="0.01" class="form-control form-control-sm" required>
            </div>
            <div class="col-4">
              <label class="form-label">总价</label>
              <input class="form-control form-control-sm" :value="(form.quantity * form.unit_price).toFixed(2)" disabled>
            </div>
          </div>
          <div class="mb-3">
            <label class="form-label">备注</label>
            <textarea v-model="form.notes" class="form-control form-control-sm" rows="2" placeholder="可选备注"></textarea>
          </div>
          <div class="d-flex gap-2 justify-content-end">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showCreateModal = false">取消</button>
            <button type="submit" class="btn btn-sm btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>确认创建
            </button>
          </div>
        </form>
      </template>
    </BtModal>

    <!-- 收货弹窗 -->
    <BtModal v-model:visible="showReceiveModal" title="确认收货" icon="bi-box-seam" max-width="450px" :show-footer="false">
      <template #body>
        <form @submit.prevent="confirmReceive">
          <p>采购单 <strong>{{ receivingOrder?.order_no || `PO-${receivingOrder?.id}` }}</strong></p>
          <div class="mb-3">
            <label class="form-label">实收数量</label>
            <input v-model.number="receiveForm.quantity_received" type="number" class="form-control form-control-sm" min="1" required>
          </div>
          <div class="mb-3">
            <label class="form-label">备注</label>
            <input v-model="receiveForm.notes" class="form-control form-control-sm" placeholder="可选">
          </div>
          <div class="d-flex gap-2 justify-content-end">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showReceiveModal = false">取消</button>
            <button type="submit" class="btn btn-sm btn-success" :disabled="saving">确认收货</button>
          </div>
        </form>
      </template>
    </BtModal>

    <!-- 付款弹窗 -->
    <BtModal v-model:visible="showPayModal" title="确认付款" icon="bi-cash-coin" max-width="450px" :show-footer="false">
      <template #body>
        <form @submit.prevent="confirmPay">
          <p>采购单 <strong>{{ payingOrder?.order_no || `PO-${payingOrder?.id}` }}</strong>，金额 <strong class="text-danger">{{ formatMoney(payingOrder?.total_amount || payingOrder?.amount) }}</strong></p>
          <div class="mb-3">
            <label class="form-label">付款方式</label>
            <select v-model="payForm.method" class="form-select form-select-sm">
              <option value="微信">微信</option><option value="支付宝">支付宝</option>
              <option value="现金">现金</option><option value="银行转账">银行转账</option>
            </select>
          </div>
          <div class="d-flex gap-2 justify-content-end">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showPayModal = false">取消</button>
            <button type="submit" class="btn btn-sm btn-warning" :disabled="saving">确认付款</button>
          </div>
        </form>
      </template>
    </BtModal>

    <!-- 详情弹窗 -->
    <BtModal v-model:visible="showDetailModal" title="采购单详情" icon="bi-info-circle" max-width="600px" :show-footer="false">
      <template #body>
        <template v-if="detailOrder">
          <div class="row g-2 mb-3">
            <div class="col-6"><strong>采购单号：</strong>{{ detailOrder.order_no || `PO-${detailOrder.id}` }}</div>
            <div class="col-6"><strong>供应商：</strong>{{ detailOrder.supplier_name || '-' }}</div>
            <div class="col-6"><strong>状态：</strong><span class="badge" :class="poStatusClass(detailOrder.status)">{{ poStatusLabel(detailOrder.status) }}</span></div>
            <div class="col-6"><strong>金额：</strong>{{ formatMoney(detailOrder.total_amount || detailOrder.amount) }}</div>
            <div class="col-6"><strong>商品：</strong>{{ detailOrder.product_name || '-' }}</div>
            <div class="col-6"><strong>数量：</strong>{{ detailOrder.quantity || '-' }}</div>
            <div class="col-12"><strong>备注：</strong>{{ detailOrder.notes || '-' }}</div>
            <div class="col-12"><strong>创建时间：</strong>{{ detailOrder.created_at || '-' }}</div>
          </div>
          <div class="d-flex gap-2 justify-content-end">
            <button class="btn btn-sm btn-outline-secondary" @click="showDetailModal = false">关闭</button>
            <button v-if="detailOrder.status === 'pending' || detailOrder.status === 'confirmed'" class="btn btn-sm btn-outline-success" @click="showDetailModal = false; receiveOrder(detailOrder)">收货</button>
            <button v-if="detailOrder.status === 'received' && !detailOrder.paid" class="btn btn-sm btn-outline-warning" @click="showDetailModal = false; payOrder(detailOrder)">付款</button>
          </div>
        </template>
      </template>
    </BtModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { purchaseApi } from '@/api/purchase'
import { useToast } from '@/composables/useToast'
import { formatMoney } from '@/utils/format'
import BtModal from '@/components/common/BtModal.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'

const { show: showToast } = useToast()

const activeTab = ref('list')
const loading = ref(false)
const saving = ref(false)
const orders = ref([])
const stats = ref({})
const searchQuery = ref('')
const statusFilter = ref('')
const unpaidOrders = ref([])
const unpaidLoading = ref(false)

// 弹窗状态
const showCreateModal = ref(false)
const showReceiveModal = ref(false)
const showPayModal = ref(false)
const showDetailModal = ref(false)
const receivingOrder = ref(null)
const payingOrder = ref(null)
const detailOrder = ref(null)

const form = ref({ supplier_name: '', product_name: '', quantity: 1, unit_price: 0, notes: '' })
const receiveForm = ref({ quantity_received: 0, notes: '' })
const payForm = ref({ method: '微信' })

const unpaidCount = computed(() => unpaidOrders.value.length)

const filteredOrders = computed(() => {
  let result = orders.value
  if (statusFilter.value) {
    result = result.filter(o => o.status === statusFilter.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(o =>
      (o.order_no || '').toLowerCase().includes(q) ||
      (o.supplier_name || '').toLowerCase().includes(q) ||
      (o.product_name || '').toLowerCase().includes(q)
    )
  }
  return result
})

let debounceTimer = null
function debouncedLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadOrders, 300)
}

function poStatusClass(status) {
  const map = { pending: 'bg-secondary', confirmed: 'bg-info', received: 'bg-success', partial: 'bg-warning text-dark', cancelled: 'bg-danger' }
  return map[status] || 'bg-secondary'
}

function poStatusLabel(status) {
  const map = { pending: '待确认', confirmed: '已确认', received: '已收货', partial: '部分收货', cancelled: '已取消' }
  return map[status] || status || '未知'
}

onMounted(async () => {
  await Promise.all([loadOrders(), loadStats(), loadUnpaid()])
})

async function loadOrders() {
  loading.value = true
  try {
    const data = await purchaseApi.list()
    orders.value = Array.isArray(data) ? data : data?.orders || data?.data || []
  } catch (e) { console.error(e); orders.value = [] }
  finally { loading.value = false }
}

async function loadStats() {
  try {
    const data = await purchaseApi.stats()
    stats.value = data || {}
  } catch (e) { console.error(e) }
}

async function loadUnpaid() {
  unpaidLoading.value = true
  try {
    const data = await purchaseApi.unpaid()
    unpaidOrders.value = Array.isArray(data) ? data : data?.orders || data?.data || []
  } catch (e) { console.error(e); unpaidOrders.value = [] }
  finally { unpaidLoading.value = false }
}

function openCreateModal() {
  form.value = { supplier_name: '', product_name: '', quantity: 1, unit_price: 0, notes: '' }
  showCreateModal.value = true
}

async function createOrder() {
  if (!form.value.supplier_name || !form.value.product_name) {
    showToast('请填写供应商和商品名称', 'warning'); return
  }
  saving.value = true
  try {
    await purchaseApi.create(form.value)
    showToast('采购单已创建', 'success')
    showCreateModal.value = false
    await Promise.all([loadOrders(), loadStats(), loadUnpaid()])
  } catch (e) { showToast('创建失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { saving.value = false }
}

function receiveOrder(po) {
  receivingOrder.value = po
  receiveForm.value = { quantity_received: po.quantity || 1, notes: '' }
  showReceiveModal.value = true
}

async function confirmReceive() {
  saving.value = true
  try {
    await purchaseApi.receive(receivingOrder.value.id, receiveForm.value)
    showToast('收货成功', 'success')
    showReceiveModal.value = false
    await Promise.all([loadOrders(), loadStats(), loadUnpaid()])
  } catch (e) { showToast('收货失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { saving.value = false }
}

function payOrder(po) {
  payingOrder.value = po
  payForm.value = { method: '微信' }
  showPayModal.value = true
}

async function confirmPay() {
  saving.value = true
  try {
    await purchaseApi.pay(payingOrder.value.id, payForm.value)
    showToast('付款成功', 'success')
    showPayModal.value = false
    await Promise.all([loadOrders(), loadStats(), loadUnpaid()])
  } catch (e) { showToast('付款失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { saving.value = false }
}

function viewOrder(po) {
  detailOrder.value = po
  showDetailModal.value = true
}
</script>
