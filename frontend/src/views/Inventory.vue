<template>
  <div class="page-inventory">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div><h2><i class="bi bi-box-seam me-2"></i>库存管理</h2><p>库存商品管理 · {{ items.length }} 项</p></div>
      <div class="d-flex gap-2 flex-wrap">
        <button class="btn btn-sm btn-outline-primary" @click="activeTab = 'logs'">流水</button>
        <button class="btn btn-sm btn-outline-warning" @click="activeTab = 'alerts'" v-if="alerts.length">预警 ({{ alerts.length }})</button>
      </div>
    </div>

    <!-- Tab Navigation -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item"><a class="nav-link" :class="{ active: activeTab === 'items' }" href="#" @click.prevent="activeTab = 'items'">库存列表</a></li>
      <li class="nav-item"><a class="nav-link" :class="{ active: activeTab === 'logs' }" href="#" @click.prevent="activeTab = 'logs'; loadLogs()">库存流水</a></li>
      <li class="nav-item"><a class="nav-link" :class="{ active: activeTab === 'alerts' }" href="#" @click.prevent="activeTab = 'alerts'; loadAlerts()">库存预警</a></li>
      <li class="nav-item"><a class="nav-link" :class="{ active: activeTab === 'adjust' }" href="#" @click.prevent="activeTab = 'adjust'">调库/盘点</a></li>
      <li class="nav-item"><a class="nav-link" :class="{ active: activeTab === 'sale' }" href="#" @click.prevent="activeTab = 'sale'; loadSales()">销售记录</a></li>
    </ul>

    <!-- Items Tab -->
    <div v-if="activeTab === 'items'" class="card p-2">
      <div class="d-flex gap-2 mb-3">
        <input v-model="searchQuery" class="form-control form-control-sm" placeholder="搜索商品..." style="max-width:300px" @input="loadItems()">
      </div>
      <div v-if="loading" class="text-center py-4"><div class="spinner"></div></div>
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>商品名称</th><th>规格</th><th>库存</th><th>单价</th><th>库位</th><th>仓库</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td class="fw-bold">{{ item.name || item.product_name }}</td>
              <td class="small text-muted">{{ item.spec || item.model || '-' }}</td>
              <td :class="item.quantity <= 0 ? 'text-danger fw-bold' : ''">{{ Number(item.quantity || 0).toFixed(0) }}</td>
              <td>¥{{ Number(item.unit_price || item.unit_cost || 0).toFixed(2) }}</td>
              <td>{{ item.location || '-' }}</td>
              <td class="small">{{ item.warehouse_name || '-' }}</td>
              <td>
                <span class="badge" :class="item.quantity <= 0 ? 'bg-danger' : item.quantity <= (item.warning_threshold || 2) ? 'bg-warning text-dark' : 'bg-success'">
                  {{ item.quantity <= 0 ? '缺货' : item.quantity <= (item.warning_threshold || 2) ? '不足' : '正常' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Logs Tab -->
    <div v-if="activeTab === 'logs'" class="card p-2">
      <div v-if="logsLoading" class="text-center py-4"><div class="spinner"></div></div>
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>时间</th><th>商品</th><th>类型</th><th>变动</th><th>操作人</th></tr></thead>
          <tbody>
            <tr v-for="log in logs" :key="log.id">
              <td class="small">{{ log.created_at?.slice(0,16) }}</td><td>{{ log.product_name || log.goods_name }}</td>
              <td><span class="badge" :class="log.type === 'in' ? 'bg-success' : 'bg-danger'">{{ log.type === 'in' ? '入库' : log.type === 'out' ? '出库' : log.type }}</span></td>
              <td :class="log.type === 'in' ? 'text-success' : 'text-danger'">{{ log.type === 'in' ? '+' : '-' }}{{ Math.abs(Number(log.quantity || 0)) }}</td>
              <td class="small text-muted">{{ log.operator || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Alerts Tab -->
    <div v-if="activeTab === 'alerts'" class="card p-2">
      <div v-if="alertsLoading" class="text-center py-4"><div class="spinner"></div></div>
      <div v-else-if="alerts.length === 0" class="text-center py-4 text-muted"><i class="bi bi-check-circle text-success" style="font-size:48px"></i><p class="mt-2">库存充足，无预警</p></div>
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>商品</th><th>当前库存</th><th>预警阈值</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="a in alerts" :key="a.id || a.goods_id">
              <td class="fw-bold">{{ a.name || a.product_name }}</td>
              <td class="text-danger">{{ Number(a.quantity || 0).toFixed(0) }}</td>
              <td>{{ a.warning_threshold || 2 }}</td>
              <td><button class="btn btn-sm btn-outline-primary" @click="alertPurchase(a)">采购补货</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Adjust Tab -->
    <div v-if="activeTab === 'adjust'" class="card p-2">
      <h5 class="mb-3">手动调库</h5>
      <form @submit.prevent="doAdjust" class="row g-2">
        <div class="col-md-4"><label class="form-label">选择商品</label><GoodsSelector @select="onAdjustGoodsSelect" /></div>
        <div class="col-md-4"><label class="form-label">变动数量</label><input v-model.number="adjustForm.quantity" type="number" class="form-control" placeholder="正=入库 负=出库" required></div>
        <div class="col-md-4"><label class="form-label">原因</label><input v-model="adjustForm.reason" class="form-control" placeholder="盘点/报废/其他"></div>
        <div class="col-12"><button type="submit" class="btn btn-primary" :disabled="adjusting">{{ adjusting ? '处理中...' : '提交调库' }}</button></div>
      </form>
      <hr>
      <h5 class="mb-3">库存盘点</h5>
      <form @submit.prevent="doCount" class="row g-2">
        <div class="col-md-4"><label class="form-label">选择商品</label><GoodsSelector @select="onCountGoodsSelect" /></div>
        <div class="col-md-4"><label class="form-label">实际数量</label><input v-model.number="countForm.actual_qty" type="number" class="form-control" required></div>
        <div class="col-md-4"><label class="form-label">备注</label><input v-model="countForm.notes" class="form-control"></div>
        <div class="col-12"><button type="submit" class="btn btn-warning" :disabled="counting">{{ counting ? '处理中...' : '提交盘点' }}</button></div>
      </form>
    </div>

    <!-- Sales Tab -->
    <div v-if="activeTab === 'sale'" class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0"><i class="bi bi-cart me-2"></i>销售记录</h5>
        <button class="btn btn-primary btn-sm" @click="showSaleForm = true"><i class="bi bi-plus-lg"></i> 新建销售</button>
      </div>
      <div v-if="salesLoading" class="text-center py-4"><div class="spinner"></div></div>
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>时间</th><th>客户</th><th>商品</th><th>数量</th><th>金额</th><th>付款</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="s in sales" :key="s.id">
              <td class="small">{{ s.created_at?.slice(0,16) }}</td><td>{{ s.client }}</td>
              <td>{{ s.product_name }}</td><td>{{ Number(s.quantity || 0).toFixed(0) }}</td>
              <td>¥{{ Number(s.total_amount || 0).toFixed(2) }}</td>
              <td>{{ s.payment_method || '-' }}</td>
              <td><span class="badge" :class="s.status === 'paid' ? 'bg-success' : 'bg-warning text-dark'">{{ s.status === 'paid' ? '已付款' : '未付款' }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 新建销售弹窗 -->
    <div v-if="showSaleForm" class="modal-backdrop" @click.self="showSaleForm = false">
      <div class="modal-content-card" style="max-width:500px">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0"><i class="bi bi-cart-plus me-2"></i>新建销售</h5>
          <button class="btn btn-sm btn-outline-secondary" @click="showSaleForm = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <form @submit.prevent="createSale">
          <div class="mb-3">
            <label class="form-label">客户名称 <span class="text-danger">*</span></label>
            <ClientSelector v-model="saleForm.client" @select="e => { if(e) saleForm.client = e.name || '' }" />
          </div>
          <div class="mb-3">
            <label class="form-label">选择商品 <span class="text-danger">*</span></label>
            <GoodsSelector @select="onSaleGoodsSelect" />
          </div>
          <div class="row g-2">
            <div class="col-4"><label class="form-label">数量</label><input v-model.number="saleForm.quantity" type="number" class="form-control" min="1" required></div>
            <div class="col-4"><label class="form-label">单价</label><input v-model.number="saleForm.unit_price" type="number" step="0.01" class="form-control" required></div>
            <div class="col-4"><label class="form-label">总价</label><input class="form-control" :value="(saleForm.quantity * saleForm.unit_price).toFixed(2)" disabled></div>
            <div class="col-6"><label class="form-label">付款方式</label>
              <select v-model="saleForm.payment_method" class="form-control" @change="onPaymentMethodChange">
                <option value="微信">微信</option><option value="支付宝">支付宝</option><option value="现金">现金</option><option value="银行转账">银行转账</option><option value="未收款">未收款</option>
              </select>
            </div>
            <div class="col-6"><label class="form-label">状态</label>
              <select v-model="saleForm.status" class="form-control" :disabled="saleForm.payment_method === '未收款'">
                <option value="paid">已付款</option><option value="unpaid">未付款</option>
              </select>
            </div>
          </div>
          <div class="d-flex gap-2 justify-content-end mt-3">
            <button type="button" class="btn btn-outline-secondary" @click="showSaleForm = false">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="saleSaving">{{ saleSaving ? '提交中...' : '确认销售' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { inventoryApi } from '@/api/inventory'
import ClientSelector from '@/components/selectors/ClientSelector.vue'
import GoodsSelector from '@/components/selectors/GoodsSelector.vue'
import { useToast } from '@/composables/useToast'

const { show: showToast } = useToast()
const activeTab = ref('items')
const items = ref([]); const loading = ref(false); const searchQuery = ref('')
const logs = ref([]); const logsLoading = ref(false)
const alerts = ref([]); const alertsLoading = ref(false)
const sales = ref([]); const salesLoading = ref(false)
const adjusting = ref(false); const counting = ref(false)
const adjustForm = ref({ goods_id: null, quantity: 0, reason: '' })
const countForm = ref({ goods_id: null, actual_qty: 0, notes: '' })

// Sale form
const showSaleForm = ref(false)
const saleSaving = ref(false)
const saleForm = ref({ client: '', goods_id: null, product_name: '', quantity: 1, unit_price: 0, payment_method: '微信', status: 'paid' })

function onSaleGoodsSelect(item) {
  if (!item) return
  const raw = item._raw || item
  saleForm.value.goods_id = raw.id
  saleForm.value.product_name = raw.name
  saleForm.value.unit_price = raw.selling_price || raw.price || raw.unit_price || 0
}

function onPaymentMethodChange() {
  if (saleForm.value.payment_method === '未收款') {
    saleForm.value.status = 'unpaid'
  }
}

function onAdjustGoodsSelect(item) {
  if (!item) return
  const raw = item._raw || item
  adjustForm.value.goods_id = raw.id
}

function onCountGoodsSelect(item) {
  if (!item) return
  const raw = item._raw || item
  countForm.value.goods_id = raw.id
}

async function createSale() {
  if (!saleForm.value.client || !saleForm.value.goods_id) { showToast('请填写客户和商品', 'warning'); return }
  saleSaving.value = true
  try {
    await inventoryApi.sale({
      client: saleForm.value.client,
      product_id: saleForm.value.goods_id,
      product_name: saleForm.value.product_name,
      quantity: saleForm.value.quantity,
      unit_price: saleForm.value.unit_price,
      total_amount: saleForm.value.quantity * saleForm.value.unit_price,
      payment_method: saleForm.value.payment_method,
      status: saleForm.value.status,
    })
    showSaleForm.value = false
    saleForm.value = { client: '', goods_id: null, product_name: '', quantity: 1, unit_price: 0, payment_method: '微信', status: 'paid' }
    showToast('销售记录已创建', 'success')
    await loadSales()
    await loadItems()
  } catch (e) { showToast('创建失败: ' + (e.response?.data?.error || e.message), 'danger') } finally { saleSaving.value = false }
}

onMounted(() => { loadItems(); loadAlerts() })

async function loadItems() {
  loading.value = true
  try {
    const params = {}
    if (searchQuery.value) params.q = searchQuery.value
    const data = await inventoryApi.list(params)
    items.value = Array.isArray(data) ? data : data?.items || data?.data || []
  } catch (e) { console.error(e); items.value = [] } finally { loading.value = false }
}
async function loadLogs() {
  logsLoading.value = true
  try { const data = await inventoryApi.getLogs(); logs.value = Array.isArray(data) ? data : data?.logs || data?.data || [] }
  catch (e) { console.error(e) } finally { logsLoading.value = false }
}
async function loadAlerts() {
  alertsLoading.value = true
  try { const data = await inventoryApi.getAlerts(); alerts.value = Array.isArray(data) ? data : data?.alerts || data?.data || [] }
  catch (e) { console.error(e) } finally { alertsLoading.value = false }
}
async function loadSales() {
  salesLoading.value = true
  try { const data = await inventoryApi.getSales(); sales.value = Array.isArray(data) ? data : data?.sales || data?.data || [] }
  catch (e) { console.error(e) } finally { salesLoading.value = false }
}
async function doAdjust() {
  adjusting.value = true
  try { await inventoryApi.adjust(adjustForm.value); showToast('调库成功', 'success'); await loadItems() }
  catch (e) { showToast('调库失败: ' + (e.response?.data?.error || e.message), 'danger') } finally { adjusting.value = false }
}
async function doCount() {
  counting.value = true
  try { await inventoryApi.count(countForm.value); showToast('盘点成功', 'success'); await loadItems() }
  catch (e) { showToast('盘点失败: ' + (e.response?.data?.error || e.message), 'danger') } finally { counting.value = false }
}
function alertPurchase(a) { showToast(`请前往采购模块为 ${a.name} 补货`, 'info') }
</script>