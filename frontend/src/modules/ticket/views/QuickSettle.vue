<template>
  <div class="qs-page">
    <!-- Loading -->
    <div v-if="loading" class="qs-loading">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-2 text-muted">加载工单信息...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="qs-error">
      <i class="bi bi-exclamation-triangle-fill qs-error-icon"></i>
      <p>{{ error }}</p>
      <button class="btn btn-primary btn-sm" @click="fetchTicket">重试</button>
    </div>

    <template v-else>
      <!-- Header: 工单 + 客户信息 -->
      <div class="qs-header">
        <div class="qs-ticket-no">{{ ticket.ticket_no }}</div>
        <div class="qs-client-row">
          <span class="qs-client-name">{{ ticket.client || '-' }}</span>
          <span v-if="ticket.phone" class="qs-client-phone">
            <a :href="'tel:' + ticket.phone" class="text-decoration-none">
              <i class="bi bi-telephone-fill"></i> {{ ticket.phone }}
            </a>
          </span>
        </div>
        <div class="qs-desc">{{ ticket.description || ticket.title || '-' }}</div>
      </div>

      <!-- 工时调整 -->
      <div class="qs-section">
        <div class="qs-section-title">
          <i class="bi bi-clock"></i> 工时
          <span class="qs-rate-tag" v-if="clientRate">¥{{ clientRate }}/h</span>
        </div>
        <div class="qs-hours-control">
          <button class="qs-big-btn qs-minus" @click="adjustHours(-0.5)" :disabled="hours <= 0">
            <i class="bi bi-dash-lg"></i>
          </button>
          <div class="qs-hours-display">
            <span class="qs-hours-value">{{ hours }}</span>
            <span class="qs-hours-unit">小时</span>
          </div>
          <button class="qs-big-btn qs-plus" @click="adjustHours(0.5)">
            <i class="bi bi-plus-lg"></i>
          </button>
        </div>
        <div class="qs-labor-fee">劳务费: <strong>{{ formatMoney(laborFee) }}</strong></div>
      </div>

      <!-- 材料列表 -->
      <div class="qs-section">
        <div class="qs-section-title">
          <i class="bi bi-box-seam"></i> 材料
          <span class="qs-badge">{{ materials.length }}</span>
        </div>

        <div v-if="materials.length === 0" class="qs-empty-materials">
          暂无材料，点击下方按钮添加
        </div>

        <div v-else class="qs-material-list">
          <div v-for="(m, idx) in materials" :key="idx" class="qs-material-item">
            <div class="qs-material-info">
              <div class="qs-material-name">{{ m.name }}</div>
              <div class="qs-material-price">¥{{ m.unit_price }} × {{ m.quantity }}</div>
            </div>
            <div class="qs-material-actions">
              <button class="qs-icon-btn" @click="changeQty(idx, -1)">
                <i class="bi bi-dash"></i>
              </button>
              <span class="qs-material-qty">{{ m.quantity }}</span>
              <button class="qs-icon-btn" @click="changeQty(idx, 1)">
                <i class="bi bi-plus"></i>
              </button>
              <button class="qs-icon-btn qs-delete" @click="removeMaterial(idx)">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>

        <button class="qs-add-material-btn" @click="showScanner = true">
          <i class="bi bi-upc-scan"></i> 扫码添加材料
        </button>
      </div>

      <!-- 金额汇总 -->
      <div class="qs-summary">
        <div class="qs-summary-row">
          <span>劳务费</span>
          <span>{{ formatMoney(laborFee) }}</span>
        </div>
        <div class="qs-summary-row">
          <span>材料费</span>
          <span>{{ formatMoney(materialFee) }}</span>
        </div>
        <div class="qs-summary-divider"></div>
        <div class="qs-summary-row qs-total">
          <span>合计应收</span>
          <span class="qs-total-amount">{{ formatMoney(totalFee) }}</span>
        </div>
      </div>

      <!-- 收款方式 -->
      <div class="qs-section">
        <div class="qs-section-title"><i class="bi bi-wallet2"></i> 收款方式</div>
        <div class="qs-payment-methods">
          <button
            v-for="method in paymentMethods"
            :key="method.value"
            class="qs-payment-btn"
            :class="{ active: selectedMethod === method.value }"
            @click="selectedMethod = method.value"
          >
            <i :class="method.icon"></i>
            <span>{{ method.label }}</span>
          </button>
        </div>
      </div>

      <!-- 底部确认按钮 -->
      <div class="qs-footer">
        <button
          class="qs-confirm-btn"
          :disabled="settling || totalFee <= 0"
          @click="confirmSettle"
        >
          <span v-if="settling" class="spinner-border spinner-border-sm me-2"></span>
          {{ settling ? '处理中...' : '确认收款 ' + formatMoney(totalFee) }}
        </button>
      </div>
    </template>

    <!-- 扫码/添加材料弹窗 -->
    <BtModal v-model:visible="showScanner" title="添加材料" icon="bi bi-upc-scan" max-width="420px">
      <template #body>
        <div class="mb-3">
          <label class="form-label">选择商品</label>
          <GoodsSelector @select="onGoodsSelect" />
        </div>
        <div class="row g-2">
          <div class="col-6">
            <label class="form-label">数量</label>
            <input v-model.number="materialForm.quantity" type="number" class="form-control" min="1">
          </div>
          <div class="col-6">
            <label class="form-label">单价</label>
            <input v-model.number="materialForm.unit_price" type="number" step="0.01" class="form-control">
          </div>
        </div>
      </template>
      <template #footer>
        <button class="btn btn-outline-secondary btn-sm" @click="showScanner = false">取消</button>
        <button class="btn btn-primary btn-sm" @click="addMaterial" :disabled="!materialForm.name">
          确认添加
        </button>
      </template>
    </BtModal>
  </div>
</template>

<script setup>
defineOptions({ name: 'QuickSettle' })

import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ticketApi } from '@/api/tickets'
import { goodsApi } from '@/api/goods'
import GoodsSelector from '@/components/selectors/GoodsSelector.vue'
import BtModal from '@/components/common/BtModal.vue'
import { useToast } from '@/composables/useToast'
import { formatMoney } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const { show: showToast } = useToast()

const ticketId = computed(() => route.params.id)

// State
const loading = ref(true)
const error = ref('')
const ticket = ref({})
const hours = ref(1)
const clientRate = ref(60)
const materials = ref([])
const selectedMethod = ref('微信')
const settling = ref(false)
const showScanner = ref(false)
const materialForm = ref({ name: '', goods_id: null, quantity: 1, unit_price: 0 })

const paymentMethods = [
  { value: '微信', label: '微信', icon: 'bi bi-wechat' },
  { value: '支付宝', label: '支付宝', icon: 'bi bi-alipay' },
  { value: '现金', label: '现金', icon: 'bi bi-cash-coin' },
  { value: '银行转账', label: '转账', icon: 'bi bi-bank' },
  { value: '其他', label: '其他', icon: 'bi bi-three-dots' },
]

// Computed
const laborFee = computed(() => hours.value * clientRate.value)

const materialFee = computed(() =>
  materials.value.reduce((sum, m) => sum + (m.unit_price || 0) * (m.quantity || 0), 0)
)

const totalFee = computed(() => laborFee.value + materialFee.value)

// Data fetching
async function fetchTicket() {
  loading.value = true
  error.value = ''
  try {
    const data = await ticketApi.getDetail(ticketId.value)
    ticket.value = data
    // 初始化工时：优先用已有服务明细的工时合计，否则默认1小时
    const items = data.service_items || []
    if (items.length > 0) {
      const totalHours = items
        .filter(i => i.billing_type === 'hourly')
        .reduce((sum, i) => sum + (i.hours || 0), 0)
      hours.value = totalHours > 0 ? totalHours : 1
    } else {
      hours.value = data.estimated_hours || 1
    }
    // 客户费率
    clientRate.value = data.client_hourly_rate || data.hourly_rate || 60
    // 已有材料
    materials.value = (data.materials || []).map(m => ({
      id: m.id,
      goods_id: m.product_id || m.goods_id,
      name: m.name || m.product_name || '未知商品',
      quantity: m.quantity || 1,
      unit_price: m.unit_price || 0,
    }))
  } catch (e) {
    error.value = e.response?.data?.error || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

// Hours
function adjustHours(delta) {
  const newVal = hours.value + delta
  if (newVal >= 0) {
    hours.value = Math.round(newVal * 2) / 2
  }
}

// Materials
function onGoodsSelect(item) {
  materialForm.value.goods_id = item.id
  materialForm.value.name = item.name || item.label || ''
  materialForm.value.unit_price = item.price || item.selling_price || item.unit_price || 0
}

function addMaterial() {
  if (!materialForm.value.name) return
  materials.value.push({
    goods_id: materialForm.value.goods_id,
    name: materialForm.value.name,
    quantity: materialForm.value.quantity || 1,
    unit_price: materialForm.value.unit_price || 0,
  })
  materialForm.value = { name: '', goods_id: null, quantity: 1, unit_price: 0 }
  showScanner.value = false
}

function changeQty(idx, delta) {
  const m = materials.value[idx]
  const newQty = (m.quantity || 0) + delta
  if (newQty > 0) {
    m.quantity = newQty
  }
}

function removeMaterial(idx) {
  materials.value.splice(idx, 1)
}

// Settlement
async function confirmSettle() {
  if (totalFee.value <= 0) {
    showToast('金额必须大于0', 'warning')
    return
  }
  settling.value = true
  try {
    // 1. 保存服务明细（时薪模式）
    if (hours.value > 0) {
      await ticketApi.addServiceItem(ticketId.value, {
        technician_name: '本人',
        name: '现场服务',
        billing_type: 'hourly',
        hours: hours.value,
        unit_price: clientRate.value,
        cost_price: 0,
      })
    }
    // 2. 保存材料
    for (const m of materials.value) {
      if (m.goods_id) {
        await ticketApi.addMaterial(ticketId.value, {
          product_id: m.goods_id,
          quantity: m.quantity,
          unit_price: m.unit_price,
        })
      }
    }
    // 3. 确认收款
    await ticketApi.confirmPayment(ticketId.value, totalFee.value, selectedMethod.value, '一键结算')
    // 4. 完工
    await ticketApi.changeStatus(ticketId.value, 'completed')

    showToast('结算成功', 'success')
    router.push('/tickets/' + ticketId.value)
  } catch (e) {
    showToast('结算失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    settling.value = false
  }
}

onMounted(fetchTicket)
</script>

<style scoped>
.qs-page {
  max-width: 480px;
  margin: 0 auto;
  padding: 0 0 100px;
  background: #f5f6f8;
  min-height: 100vh;
}

.qs-loading,
.qs-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 2rem;
}

.qs-error-icon {
  font-size: 3rem;
  color: var(--bt-warning, #f59e0b);
  margin-bottom: 1rem;
}

/* Header */
.qs-header {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: #fff;
  padding: 1.25rem;
  border-radius: 0 0 1.25rem 1.25rem;
  margin-bottom: 0.75rem;
}

.qs-ticket-no {
  font-size: 0.875rem;
  opacity: 0.85;
  margin-bottom: 0.25rem;
}

.qs-client-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.qs-client-name {
  font-size: 1.25rem;
  font-weight: 700;
}

.qs-client-phone a {
  color: #fff;
  font-size: 0.875rem;
  opacity: 0.9;
}

.qs-desc {
  font-size: 0.875rem;
  opacity: 0.85;
  line-height: 1.4;
}

/* Section */
.qs-section {
  background: #fff;
  margin: 0.75rem;
  padding: 1rem;
  border-radius: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.qs-section-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.qs-section-title i {
  color: var(--bt-primary, #2563eb);
}

.qs-rate-tag {
  margin-left: auto;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
}

.qs-badge {
  margin-left: auto;
  font-size: 0.75rem;
  font-weight: 600;
  color: #fff;
  background: var(--bt-primary, #2563eb);
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  min-width: 1.5rem;
  text-align: center;
}

/* Hours Control */
.qs-hours-control {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  margin-bottom: 0.75rem;
}

.qs-big-btn {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  transition: transform 0.1s, opacity 0.2s;
  cursor: pointer;
}

.qs-big-btn:active {
  transform: scale(0.92);
}

.qs-big-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.qs-minus {
  background: #fee2e2;
  color: #dc2626;
}

.qs-plus {
  background: #dbeafe;
  color: #2563eb;
}

.qs-hours-display {
  text-align: center;
  min-width: 5rem;
}

.qs-hours-value {
  display: block;
  font-size: 2.5rem;
  font-weight: 800;
  color: #1f2937;
  line-height: 1;
}

.qs-hours-unit {
  font-size: 0.75rem;
  color: #9ca3af;
}

.qs-labor-fee {
  text-align: center;
  font-size: 0.875rem;
  color: #6b7280;
}

.qs-labor-fee strong {
  color: #1f2937;
  font-size: 1.125rem;
}

/* Materials */
.qs-empty-materials {
  text-align: center;
  padding: 1.5rem 0;
  color: #9ca3af;
  font-size: 0.875rem;
}

.qs-material-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  margin-bottom: 0.875rem;
}

.qs-material-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 0.75rem;
  background: #f9fafb;
  border-radius: 0.75rem;
}

.qs-material-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
}

.qs-material-price {
  font-size: 0.75rem;
  color: #6b7280;
}

.qs-material-actions {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.qs-material-qty {
  font-size: 0.875rem;
  font-weight: 600;
  min-width: 1.25rem;
  text-align: center;
}

.qs-icon-btn {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  border: none;
  background: #e5e7eb;
  color: #374151;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background 0.15s;
}

.qs-icon-btn:active {
  background: #d1d5db;
}

.qs-icon-btn.qs-delete {
  background: #fee2e2;
  color: #dc2626;
  margin-left: 0.25rem;
}

.qs-add-material-btn {
  width: 100%;
  padding: 0.75rem;
  border: 2px dashed #d1d5db;
  border-radius: 0.75rem;
  background: transparent;
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  cursor: pointer;
  transition: all 0.15s;
}

.qs-add-material-btn:active {
  border-color: var(--bt-primary, #2563eb);
  color: var(--bt-primary, #2563eb);
  background: #eff6ff;
}

/* Summary */
.qs-summary {
  background: #fff;
  margin: 0.75rem;
  padding: 1rem;
  border-radius: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.qs-summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9375rem;
  color: #4b5563;
  padding: 0.375rem 0;
}

.qs-summary-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 0.5rem 0;
}

.qs-summary-row.qs-total {
  font-size: 1.0625rem;
  font-weight: 700;
  color: #1f2937;
}

.qs-total-amount {
  color: #dc2626;
  font-size: 1.375rem;
}

/* Payment Methods */
.qs-payment-methods {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.5rem;
}

.qs-payment-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
  padding: 0.75rem 0.25rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.75rem;
  background: #fff;
  color: #6b7280;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.qs-payment-btn i {
  font-size: 1.25rem;
}

.qs-payment-btn.active {
  border-color: var(--bt-primary, #2563eb);
  color: var(--bt-primary, #2563eb);
  background: #eff6ff;
}

.qs-payment-btn:active {
  transform: scale(0.96);
}

/* Footer */
.qs-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.75rem 1rem;
  background: #fff;
  border-top: 1px solid #e5e7eb;
  z-index: 100;
  max-width: 480px;
  margin: 0 auto;
}

.qs-confirm-btn {
  width: 100%;
  padding: 1rem;
  border: none;
  border-radius: 1rem;
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  color: #fff;
  font-size: 1.0625rem;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
  box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3);
}

.qs-confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.qs-confirm-btn:active:not(:disabled) {
  transform: scale(0.98);
  opacity: 0.9;
}

@media (max-width: 360px) {
  .qs-payment-methods {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
