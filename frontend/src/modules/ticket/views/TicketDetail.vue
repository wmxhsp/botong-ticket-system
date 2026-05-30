<template>
  <div v-if="loading" class="bt-empty-state">
    <LoadingSkeleton type="page" text="加载工单详情..." />
  </div>

  <div v-else-if="error" class="bt-empty-state">
    <div class="bt-empty-icon"><i class="bi bi-exclamation-triangle-fill" style="color:var(--bt-warning)"></i></div>
    <div class="bt-empty-title">加载失败</div>
    <div class="bt-empty-desc">{{ error }}</div>
    <button class="btn btn-primary btn-sm mt-3" @click="fetchTicket">重试</button>
  </div>

  <template v-else>
    <!-- Breadcrumbs -->
    <div class="bt-breadcrumbs">
      <router-link to="/tickets">工单管理</router-link>
      <span class="bt-breadcrumb-sep">/</span>
      <span class="bt-breadcrumb-current">{{ ticket.ticket_no }}</span>
    </div>

    <!-- Header -->
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div>
        <div class="d-flex align-items-center gap-2 mb-1 flex-wrap">
          <h2 class="mb-0">{{ ticket.ticket_no }}</h2>
          <StatusBadge :status="ticket.status" :name="ticket.status_name" />
          <span v-if="ticket.priority === 'H'" class="bt-data-tag danger">高优先级</span>
          <span v-else-if="ticket.priority === 'L'" class="bt-data-tag primary">低优先级</span>
        </div>
        <p class="mb-0 text-truncate" style="max-width:400px">{{ ticket.title || ticket.description }}</p>
      </div>
      <div class="d-flex gap-2 flex-shrink-0">
        <button class="btn btn-sm btn-outline-primary" @click="showEditModal = true">
          <i class="bi bi-pencil"></i> <span class="d-none d-sm-inline">编辑</span>
        </button>
        <button class="btn btn-sm btn-outline-info" @click="showHistory = !showHistory">
          <i class="bi bi-clock-history"></i> <span class="d-none d-sm-inline">历史</span>
        </button>
      </div>
    </div>

    <!-- Stat Cards -->
    <TicketStatCards :ticket="ticket" :service-items="serviceItems" />

    <!-- Payment & Fee Distribution -->
    <TicketPaymentBar :ticket="ticket" :service-items="serviceItems" :can-add-payment="!isClosed" @add-payment="showPaymentModal = true" />

    <!-- Main Content + Sidebar -->
    <div class="row g-2 g-lg-3">
      <div class="col-lg-8">
        <!-- Basic Info -->
        <div class="card p-3 p-md-4 mb-2">
          <h5 class="mb-3"><i class="bi bi-info-circle me-2"></i>基本信息</h5>
          <div class="row g-2">
            <div class="col-6 col-md-4">
              <label class="form-label small text-muted">客户</label>
              <router-link :to="'/clients/' + encodeURIComponent(ticket.client)" class="text-decoration-none d-block">
                {{ ticket.client || '-' }}
              </router-link>
            </div>
            <div class="col-6 col-md-4">
              <label class="form-label small text-muted">联系人</label>
              <div>{{ ticket.contact || '-' }}</div>
            </div>
            <div class="col-6 col-md-4">
              <label class="form-label small text-muted">联系电话</label>
              <div>{{ ticket.phone || '-' }}</div>
            </div>
            <div class="col-6 col-md-4">
              <label class="form-label small text-muted">服务地址</label>
              <div>{{ ticket.location || '-' }}</div>
            </div>
            <div class="col-6 col-md-4">
              <label class="form-label small text-muted">创建时间</label>
              <div>{{ formatDateTime(ticket.created_at) }}</div>
            </div>
            <div class="col-6 col-md-4">
              <label class="form-label small text-muted">创建人</label>
              <div>{{ ticket.created_by || '系统' }}</div>
            </div>
            <div class="col-12">
              <label class="form-label small text-muted">服务内容</label>
              <div>{{ ticket.description || '-' }}</div>
            </div>
            <div class="col-12">
              <label class="form-label small text-muted">备注</label>
              <div>{{ ticket.notes || '-' }}</div>
            </div>
          </div>
        </div>

        <!-- Service Items -->
        <TicketServiceItems :items="serviceItems" @add-service-item="openServiceItemForm" @delete-service-item="deleteServiceItem" />

        <!-- Materials -->
        <TicketMaterials :materials="ticket.materials || []" @add-material="showMaterialForm = true" @delete-material="deleteMaterial" @update-qty="updateMaterialQty" />

        <!-- Photos -->
        <TicketPhotos :photos="photos" @upload="triggerUpload" @delete="deletePhoto" />

        <input type="file" ref="fileInput" accept="image/*" multiple style="display:none" @change="uploadPhotos">

        <!-- History -->
        <div class="card p-3 p-md-4 mb-2" v-if="showHistory">
          <h5 class="mb-2"><i class="bi bi-clock-history me-2"></i>操作历史</h5>
          <div v-if="!ticket.history || ticket.history.length === 0" class="text-muted small py-4 text-center">暂无操作记录</div>
          <div v-else v-for="h in ticket.history" :key="h.id" class="bt-notification-item">
            <div class="bt-notif-icon" style="background:var(--bt-primary-bg);color:var(--bt-primary)">
              <i class="bi bi-arrow-repeat"></i>
            </div>
            <div class="bt-notif-content">
              <div class="bt-notif-title">{{ h.action || h.description }}</div>
              <div class="bt-notif-desc">{{ h.operator || '系统' }} · {{ formatDateTime(h.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="col-lg-4">
        <TicketStatusPanel
          :ticket="ticket"
          :service-items="serviceItems"
          :timer-display="timerDisplay"
          :timer-running="timerRunning"
          @change-status="changeStatus"
          @start-timer="startTimer"
          @stop-timer="stopTimer"
          @edit-appointment="showAppointmentModal = true"
        />
      </div>
    </div>

    <!-- Timeline -->
    <div class="card p-3 p-md-4 mt-2" v-if="timeline && timeline.length">
      <h5 class="mb-2"><i class="bi bi-clock-history me-2"></i>状态时间线</h5>
      <div class="bt-timeline">
        <div v-for="(item, i) in timeline" :key="i" class="d-flex gap-3 mb-3">
          <div style="width:10px;height:10px;border-radius:50%;background:var(--bt-primary);margin-top:6px;flex-shrink:0"></div>
          <div>
            <div class="small font-medium">{{ item.description || item.message }}</div>
            <div class="small text-muted">{{ formatDateTime(item.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>
  </template>

  <!-- Edit Modal -->
  <BtModal v-model:visible="showEditModal" title="编辑工单" icon="bi bi-pencil" max-width="700px">
    <template #body>
      <div class="row g-2">
        <div class="col-md-6">
          <label class="form-label">客户名称</label>
          <ClientSelector v-model="editForm.client" @select="onEditClientSelect" />
        </div>
        <div class="col-md-6">
          <label class="form-label">联系人</label>
          <input class="form-control" v-model="editForm.contact">
        </div>
        <div class="col-12">
          <label class="form-label">服务内容</label>
          <textarea class="form-control" v-model="editForm.description" rows="3"></textarea>
        </div>
        <div class="col-md-6">
          <label class="form-label">服务地址</label>
          <input class="form-control" v-model="editForm.location">
        </div>
        <div class="col-md-6">
          <label class="form-label">备注</label>
          <input class="form-control" v-model="editForm.notes">
        </div>
      </div>
    </template>
    <template #footer>
      <button class="btn btn-outline-secondary btn-sm" @click="showEditModal = false">取消</button>
      <button class="btn btn-primary btn-sm" @click="saveEdit" :disabled="saving">
        <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </template>
  </BtModal>

  <!-- Material Modal -->
  <BtModal v-model:visible="showMaterialForm" title="添加物料" icon="bi bi-box-seam" max-width="500px">
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
      <button class="btn btn-outline-secondary btn-sm" @click="showMaterialForm = false">取消</button>
      <button class="btn btn-primary btn-sm" @click="addMaterial" :disabled="!materialForm.goods_id">确认添加</button>
    </template>
  </BtModal>

  <!-- Service Item Modal -->
  <BtModal v-model:visible="showServiceItemForm" title="添加服务明细" icon="bi bi-clock-history" max-width="500px">
    <template #body>
      <div class="mb-3">
        <label class="form-label">工程师</label>
        <select v-model="serviceItemForm.technician_id" class="form-select">
          <option value="">请选择工程师...</option>
          <option v-for="t in availableTechnicians" :key="t.id" :value="t.id">
            {{ t.name }} ({{ formatRate(t) }})
          </option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">服务项目</label>
        <select v-model="serviceItemForm.service_fee_id" class="form-select">
          <option value="">请选择服务项目...</option>
          <option v-for="sf in availableServiceFees" :key="sf.id" :value="sf.id">
            {{ sf.name }} (¥{{ sf.base_price || sf.unit_price || 0 }}{{ feeSuffix(sf.fee_type) }})
          </option>
        </select>
      </div>
      <!-- 计费模式选择 -->
      <div class="mb-3">
        <label class="form-label">计费模式</label>
        <div class="btn-group w-100">
          <button type="button" class="btn btn-sm" :class="serviceItemForm.billing_type === 'hourly' ? 'btn-primary' : 'btn-outline-secondary'" @click="serviceItemForm.billing_type = 'hourly'">时薪</button>
          <button type="button" class="btn btn-sm" :class="serviceItemForm.billing_type === 'daily' ? 'btn-primary' : 'btn-outline-secondary'" @click="serviceItemForm.billing_type = 'daily'">天薪</button>
          <button type="button" class="btn btn-sm" :class="serviceItemForm.billing_type === 'package' ? 'btn-primary' : 'btn-outline-secondary'" @click="serviceItemForm.billing_type = 'package'">包工</button>
        </div>
      </div>
      <!-- 时薪输入 -->
      <div v-if="serviceItemForm.billing_type === 'hourly'" class="mb-3">
        <label class="form-label">工时（小时）</label>
        <input v-model.number="serviceItemForm.hours" type="number" step="0.5" class="form-control" min="0" placeholder="输入工时">
      </div>
      <!-- 天薪输入 -->
      <div v-else-if="serviceItemForm.billing_type === 'daily'" class="mb-3">
        <label class="form-label">工作天数</label>
        <input v-model.number="serviceItemForm.days" type="number" step="0.5" class="form-control" min="0" placeholder="输入天数">
      </div>
      <!-- 包工输入 -->
      <div v-else-if="serviceItemForm.billing_type === 'package'" class="mb-3">
        <label class="form-label">包工费</label>
        <div class="input-group">
          <span class="input-group-text">¥</span>
          <input v-model.number="serviceItemForm.package_fee" type="number" step="0.01" class="form-control" min="0" placeholder="输入包工费">
        </div>
      </div>
      <div v-if="serviceItemForm.technician_id && serviceItemForm.service_fee_id && isServiceItemFormValid" class="mb-3 p-3 rounded-lg" style="background:var(--bt-gray-50, #f8f9fa)">
        <div class="small text-muted mb-1">费用预估</div>
        <div class="d-flex justify-content-between small flex-wrap gap-1">
          <span>成本: ¥{{ serviceItemCost.toFixed(2) }}</span>
          <span>收入: ¥{{ serviceItemRevenue.toFixed(2) }}</span>
          <span class="font-bold" :class="serviceItemProfit >= 0 ? 'text-success' : 'text-danger'">毛利: ¥{{ serviceItemProfit.toFixed(2) }}</span>
        </div>
      </div>
    </template>
    <template #footer>
      <button class="btn btn-outline-secondary btn-sm" @click="showServiceItemForm = false">取消</button>
      <button class="btn btn-primary btn-sm" @click="addServiceItem" :disabled="!isServiceItemFormValid">
        确认添加
      </button>
    </template>
  </BtModal>

  <!-- Payment Modal -->
  <BtModal v-model:visible="showPaymentModal" title="确认收款" icon="bi bi-credit-card" max-width="400px">
    <template #body>
      <div class="mb-2 small text-muted">
        工单总额: {{ formatMoney(ticket.total || 0) }}，已收: {{ formatMoney(ticket.paid_amount || 0) }}
      </div>
      <div class="mb-3">
        <label class="form-label">收款金额</label>
        <input v-model.number="paymentForm.amount" type="number" step="0.01" class="form-control" placeholder="输入收款金额">
        <div class="small text-muted mt-1">留空或输入0表示全额收款</div>
      </div>
      <div class="mb-3">
        <label class="form-label">收款方式</label>
        <select v-model="paymentForm.method" class="form-select">
          <option value="微信">微信</option>
          <option value="支付宝">支付宝</option>
          <option value="银行转账">银行转账</option>
          <option value="现金">现金</option>
          <option value="其他">其他</option>
        </select>
      </div>
    </template>
    <template #footer>
      <button class="btn btn-outline-secondary btn-sm" @click="showPaymentModal = false">取消</button>
      <button class="btn btn-success btn-sm" @click="confirmPayment">确认收款</button>
    </template>
  </BtModal>

  <!-- Appointment Modal -->
  <BtModal v-model:visible="showAppointmentModal" title="预约设置" icon="bi bi-calendar-check" max-width="400px">
    <template #body>
      <div class="mb-3">
        <label class="form-label">预约时间</label>
        <input v-model="appointmentForm.appointment_at" type="datetime-local" class="form-control">
      </div>
    </template>
    <template #footer>
      <button v-if="ticket.appointment_at" class="btn btn-outline-danger btn-sm" @click="clearAppointment">清除预约</button>
      <button class="btn btn-outline-secondary btn-sm" @click="showAppointmentModal = false">取消</button>
      <button class="btn btn-primary btn-sm" @click="saveAppointment">保存</button>
    </template>
  </BtModal>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { ticketApi } from '@/api/tickets'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ClientSelector from '@/components/selectors/ClientSelector.vue'
import GoodsSelector from '@/components/selectors/GoodsSelector.vue'
import BtModal from '@/components/common/BtModal.vue'
import TicketStatCards from '@/components/tickets/TicketStatCards.vue'
import TicketPaymentBar from '@/components/tickets/TicketPaymentBar.vue'
import TicketStatusPanel from '@/components/tickets/TicketStatusPanel.vue'
import TicketServiceItems from '@/components/tickets/TicketServiceItems.vue'
import TicketMaterials from '@/components/tickets/TicketMaterials.vue'
import TicketPhotos from '@/components/tickets/TicketPhotos.vue'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { formatMoney, formatDateTime } from '@/utils/format'

const props = defineProps({ id: { type: String, required: true } })
const { show: showToast } = useToast()
const { confirm } = useConfirm()

// State
const fileInput = ref(null)
const photos = ref([])
const timeline = ref([])
const ticket = ref({})
const loading = ref(true)
const error = ref('')
const showHistory = ref(false)
const showEditModal = ref(false)
const saving = ref(false)
const showMaterialForm = ref(false)
const showServiceItemForm = ref(false)
const showPaymentModal = ref(false)
const showAppointmentModal = ref(false)

const editForm = ref({ client: '', contact: '', description: '', location: '', notes: '' })
const materialForm = ref({ goods_id: null, goods_name: '', quantity: 1, unit_price: 0 })
const serviceItemForm = ref({ technician_id: null, service_fee_id: null, billing_type: 'hourly', hours: 1, days: 1, package_fee: 0 })
const serviceItems = ref([])
const paymentForm = ref({ amount: null, method: '微信' })
const appointmentForm = ref({ appointment_at: '' })
const availableTechnicians = ref([])
const availableServiceFees = ref([])

// Timer
const timerSeconds = ref(0)
const timerRunning = ref(false)
let timerInterval = null

// Computed
const isClosed = computed(() => ['closed', 'cancelled'].includes(ticket.value.status))

const timerDisplay = computed(() => {
  const h = Math.floor(timerSeconds.value / 3600)
  const m = Math.floor((timerSeconds.value % 3600) / 60)
  const s = timerSeconds.value % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
})

const currentTechnician = computed(() => availableTechnicians.value.find(t => t.id === serviceItemForm.value.technician_id))
const currentServiceFee = computed(() => availableServiceFees.value.find(f => f.id === serviceItemForm.value.service_fee_id))

const isServiceItemFormValid = computed(() => {
  if (!serviceItemForm.value.technician_id || !serviceItemForm.value.service_fee_id) return false
  const bt = serviceItemForm.value.billing_type || 'hourly'
  if (bt === 'hourly') return (serviceItemForm.value.hours || 0) > 0
  if (bt === 'daily') return (serviceItemForm.value.days || 0) > 0
  if (bt === 'package') return (serviceItemForm.value.package_fee || 0) > 0
  return false
})

const serviceItemCost = computed(() => {
  const tech = currentTechnician.value
  const bt = serviceItemForm.value.billing_type || 'hourly'
  if (bt === 'daily') return (tech?.daily_cost_rate || tech?.cost_rate || 0) * (serviceItemForm.value.days || 0)
  if (bt === 'package') return tech?.package_cost || tech?.cost_rate || 0
  return (tech?.cost_rate || 0) * (serviceItemForm.value.hours || 0)
})

const serviceItemRevenue = computed(() => {
  const sf = currentServiceFee.value
  const bt = serviceItemForm.value.billing_type || 'hourly'
  const price = sf?.base_price || sf?.unit_price || 0
  if (bt === 'daily') return price * (serviceItemForm.value.days || 0)
  if (bt === 'package') return serviceItemForm.value.package_fee || price
  return price * (serviceItemForm.value.hours || 0)
})

const serviceItemProfit = computed(() => serviceItemRevenue.value - serviceItemCost.value)

// Data fetching
async function fetchTicket() {
  loading.value = true
  error.value = ''
  try {
    const data = await ticketApi.getDetail(props.id)
    ticket.value = data
    photos.value = data.photos || []
    timeline.value = data.timeline || []
    editForm.value = {
      client: data.client || '',
      contact: data.contact || '',
      description: data.description || '',
      location: data.location || '',
      notes: data.notes || '',
    }
    if (data.appointment_at) {
      const d = new Date(data.appointment_at)
      appointmentForm.value.appointment_at = d.toISOString().slice(0, 16)
    }
    await fetchServiceItems()
  } catch (e) {
    error.value = e.response?.data?.error || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function fetchServiceItems() {
  try {
    const data = await ticketApi.getServiceItems(props.id)
    serviceItems.value = data.service_items || []
  } catch { serviceItems.value = [] }
}

async function fetchServiceFees() {
  try {
    const data = await ticketApi.getServiceFees()
    availableServiceFees.value = data.fees || []
  } catch { availableServiceFees.value = [] }
}

// Edit
function onEditClientSelect(client) {
  if (client) {
    editForm.value.contact = editForm.value.contact || client.contact || ''
    editForm.value.location = editForm.value.location || client.address || ''
  }
}

async function saveEdit() {
  saving.value = true
  try {
    await ticketApi.update(props.id, editForm.value)
    showEditModal.value = false
    showToast('已更新', 'success')
    await fetchTicket()
  } catch (e) {
    showToast('更新失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    saving.value = false
  }
}

// Materials
function onGoodsSelect(item) {
  materialForm.value.goods_id = item.id
  materialForm.value.goods_name = item.name
  materialForm.value.unit_price = item.selling_price || item.unit_price || item.price || 0
  materialForm.value.quantity = 1
}

async function addMaterial() {
  if (!materialForm.value.goods_id) return
  try {
    await ticketApi.addMaterial(props.id, {
      product_id: materialForm.value.goods_id,
      quantity: materialForm.value.quantity,
      unit_price: materialForm.value.unit_price,
    })
    showMaterialForm.value = false
    materialForm.value = { goods_id: null, goods_name: '', quantity: 1, unit_price: 0 }
    showToast('物料已添加', 'success')
    await fetchTicket()
  } catch (e) {
    showToast('添加失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}

async function deleteMaterial(mid) {
  if (!(await confirm('确定删除该物料？'))) return
  try {
    await ticketApi.deleteMaterial(props.id, mid)
    showToast('物料已删除', 'success')
    await fetchTicket()
  } catch { showToast('删除失败', 'danger') }
}

async function updateMaterialQty(mid, event) {
  const qty = parseFloat(event.target.value) || 1
  try {
    await ticketApi.updateMaterial(props.id, mid, { quantity: qty })
    await fetchTicket()
  } catch { showToast('更新失败', 'danger') }
}

// Service items
function openServiceItemForm() {
  serviceItemForm.value = { technician_id: null, service_fee_id: null, billing_type: 'hourly', hours: 1, days: 1, package_fee: 0 }
  showServiceItemForm.value = true
}

function feeSuffix(feeType) {
  const map = { hourly: '/h', fixed: '/次', monthly: '/月', yearly: '/年', per_km: '/km', daily: '/天', package: '/包' }
  return map[feeType] || '/次'
}

function formatRate(tech) {
  const bt = tech.billing_type || 'hourly'
  const rate = tech.cost_rate || 0
  const dailyRate = tech.daily_cost_rate || 0
  if (bt === 'daily') return `¥${dailyRate || rate * 8}/天`
  if (bt === 'package') return `¥${tech.package_cost || rate}/包`
  return `¥${rate}/h`
}

async function addServiceItem() {
  if (!isServiceItemFormValid.value) return
  const tech = currentTechnician.value
  const sf = currentServiceFee.value
  const bt = serviceItemForm.value.billing_type || 'hourly'
  let unit_price = sf?.base_price || sf?.unit_price || 0
  let cost_price = tech?.cost_rate || 0
  if (bt === 'daily') {
    unit_price = sf?.base_price || sf?.unit_price || 0
    cost_price = tech?.daily_cost_rate || tech?.cost_rate || 0
  } else if (bt === 'package') {
    cost_price = tech?.package_cost || tech?.cost_rate || 0
  }
  try {
    await ticketApi.addServiceItem(props.id, {
      technician_name: tech?.name || '',
      service_fee_id: serviceItemForm.value.service_fee_id,
      name: sf?.name || '',
      billing_type: bt,
      hours: serviceItemForm.value.hours || 0,
      days: serviceItemForm.value.days || 0,
      package_fee: serviceItemForm.value.package_fee || 0,
      unit_price: unit_price,
      cost_price: cost_price,
    })
    showServiceItemForm.value = false
    showToast('服务明细已添加', 'success')
    await fetchTicket()
  } catch (e) {
    showToast('添加失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}

async function deleteServiceItem(itemId) {
  if (!(await confirm('确定删除该服务明细？'))) return
  try {
    await ticketApi.deleteServiceItem(props.id, itemId)
    showToast('记录已删除', 'success')
    await fetchTicket()
  } catch { showToast('删除失败', 'danger') }
}

// Payment
async function confirmPayment() {
  try {
    await ticketApi.confirmPayment(props.id, paymentForm.value.amount || 0, paymentForm.value.method)
    showPaymentModal.value = false
    paymentForm.value = { amount: null, method: '微信' }
    showToast('收款成功', 'success')
    await fetchTicket()
  } catch (e) {
    showToast('收款失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}

// Appointment
async function saveAppointment() {
  try {
    await ticketApi.update(props.id, { appointment_at: appointmentForm.value.appointment_at })
    showAppointmentModal.value = false
    showToast('预约已保存', 'success')
    await fetchTicket()
  } catch (e) {
    showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}

async function clearAppointment() {
  if (!(await confirm('确定清除预约？'))) return
  try {
    await ticketApi.update(props.id, { appointment_at: null })
    showAppointmentModal.value = false
    appointmentForm.value.appointment_at = ''
    showToast('预约已清除', 'success')
    await fetchTicket()
  } catch { showToast('操作失败', 'danger') }
}

// Status
async function changeStatus(status) {
  const msg = {
    in_progress: '开始服务后工单状态将变为"进行中"',
    pending_payment: '完工结算后工单将进入待结算状态',
    completed: '确认完工后工单将标记为已完成',
    closed: '关闭工单后将无法继续操作',
    cancelled: '取消工单后将无法恢复',
  }[status] || '确定要更改状态吗？'

  if (!(await confirm(msg))) return
  try {
    await ticketApi.changeStatus(props.id, status)
    showToast('状态已更新', 'success')
    await fetchTicket()
  } catch (e) {
    showToast('操作失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}

// Timer
function startTimer() {
  timerRunning.value = true
  timerInterval = setInterval(() => { timerSeconds.value++ }, 1000)
}

async function stopTimer() {
  timerRunning.value = false
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
  const hours = timerSeconds.value / 3600
  timerSeconds.value = 0
  if (hours > 0) {
    if (!(await confirm(`确认记录 ${hours.toFixed(2)} 工时？`))) return
    try {
      await ticketApi.update(props.id, { time_spent: parseFloat(ticket.value.time_spent || 0) + hours })
      showToast('工时已记录', 'success')
      await fetchTicket()
    } catch { showToast('记录失败', 'danger') }
  }
}

// Photos
function triggerUpload() { fileInput.value?.click() }

async function uploadPhotos(event) {
  const files = Array.from(event.target.files)
  if (!files.length) return
  try {
    const formData = new FormData()
    files.forEach(f => formData.append('photos', f))
    await ticketApi.uploadPhotos(props.id, formData)
    showToast('照片上传成功', 'success')
    await fetchTicket()
  } catch { showToast('上传失败', 'danger') }
  event.target.value = ''
}

async function deletePhoto(p) {
  if (!(await confirm('确定删除这张照片？'))) return
  try {
    await ticketApi.deletePhoto(props.id, { id: p.id, filepath: p.filepath || p.url })
    showToast('照片已删除', 'success')
    await fetchTicket()
  } catch { showToast('删除失败', 'danger') }
}

// Watch & Mount
watch(() => props.id, () => { fetchTicket() })

onMounted(() => {
  fetchTicket()
  fetchServiceFees()
})

onBeforeUnmount(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
})
</script>
