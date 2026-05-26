<template>
  <div v-if="loading" class="bt-empty-state">
    <div class="bt-inline-loading"><div class="bt-spinner"></div> 加载客户信息...</div>
  </div>

  <div v-else-if="error" class="bt-empty-state">
    <div class="bt-empty-icon"><i class="bi bi-person-x"></i></div>
    <div class="bt-empty-title">客户不存在</div>
    <div class="bt-empty-desc">{{ error }}</div>
    <router-link to="/clients" class="btn btn-primary btn-sm mt-3">
      <i class="bi bi-arrow-left me-1"></i> 返回客户列表
    </router-link>
  </div>

  <template v-else-if="client_data.name">
    <div class="bt-breadcrumbs">
      <router-link to="/clients">客户管理</router-link>
      <span class="bt-breadcrumb-sep">/</span>
      <span class="bt-breadcrumb-current">{{ client_data.name }}</span>
    </div>

    <div class="row g-2 mb-2">
      <div class="col-md-8">
        <div class="card p-2">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <div class="d-flex align-items-center gap-3">
              <div class="bt-avatar bt-avatar-lg" :class="'bt-avatar-color-' + ((client_data.id || 0) % 8)">
                {{ client_data.name?.[0] || '?' }}
              </div>
              <div>
                <h4 class="mb-1 d-flex align-items-center gap-2" style="color:var(--bt-text-heading)">
                  {{ client_data.name }}
                  <span v-if="client_data.credit_frozen" class="badge bg-danger">已冻结</span>
                </h4>
                <p class="text-muted small mb-0">
                  {{ client_data.contact || '无联系人' }}
                  <span v-if="client_data.phone"> · {{ client_data.phone }}</span>
                </p>
              </div>
            </div>
            <button class="btn btn-sm btn-outline-secondary" @click="openEditModal">
              <i class="bi bi-pencil me-1"></i>编辑
            </button>
          </div>
          <table class="table table-borderless table-sm mb-0">
            <tr>
              <th style="width:100px">客户类型</th>
              <td>{{ client_data.client_type || '未分类' }}</td>
              <th style="width:100px">服务范围</th>
              <td>{{ client_data.scope || '-' }}</td>
            </tr>
            <tr>
              <th>结算方式</th>
              <td>{{ client_data.agreement_type || '按次' }}</td>
              <th>账期</th>
              <td>{{ client_data.payment_terms || 30 }} 天</td>
            </tr>
            <tr>
              <th>地址</th>
              <td colspan="3">{{ client_data.address || '-' }}</td>
            </tr>
            <tr>
              <th>备注</th>
              <td colspan="3">{{ client_data.notes || '-' }}</td>
            </tr>
          </table>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card p-2 mb-2">
          <div class="d-flex align-items-center justify-content-between mb-2">
            <h6 class="mb-0"><i class="bi bi-award me-1"></i>客户画像</h6>
            <span class="badge" :class="tierBadge.class">{{ tierBadge.label }}</span>
          </div>
          <div class="row g-2 text-center">
            <div class="col-4">
              <div class="fw-bold" style="font-size:20px">{{ stats.total_tickets }}</div>
              <div class="small text-muted">总工单</div>
            </div>
            <div class="col-4">
              <div class="fw-bold text-success" style="font-size:20px">{{ formatMoney(stats.total_spent) }}</div>
              <div class="small text-muted">总消费</div>
            </div>
            <div class="col-4">
              <div class="fw-bold" :class="stats.unpaid_amount > 0 ? 'text-danger' : 'text-success'" style="font-size:20px">{{ formatMoney(stats.unpaid_amount) }}</div>
              <div class="small text-muted">未结清</div>
            </div>
          </div>
          <div v-if="stats.unpaid_amount > 0" class="alert alert-warning py-1 px-2 mt-2 mb-0 small">
            <i class="bi bi-exclamation-triangle me-1"></i>该客户有未结清款项
          </div>
        </div>

        <div class="row g-2">
          <div class="col-6">
            <div class="card p-2 text-center">
              <div class="fw-bold" style="font-size:18px">{{ stats.active_tickets }}</div>
              <div class="small text-muted">活跃工单</div>
            </div>
          </div>
          <div class="col-6">
            <div class="card p-2 text-center">
              <div class="fw-bold" style="font-size:18px">{{ stats.device_count }}</div>
              <div class="small text-muted">设备数量</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'tickets' }" @click="activeTab = 'tickets'">
          <i class="bi bi-ticket-perforated me-1"></i>工单记录
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'equipment' }" @click="activeTab = 'equipment'">
          <i class="bi bi-pc-display me-1"></i>设备清单
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'payments' }" @click="activeTab = 'payments'">
          <i class="bi bi-credit-card me-1"></i>收款记录
        </button>
      </li>
    </ul>

    <!-- 工单记录 -->
    <div v-if="activeTab === 'tickets'" class="card p-2">
      <div class="table-responsive">
        <table class="bt-table">
          <thead>
            <tr>
              <th>工单号</th>
              <th>内容</th>
              <th>状态</th>
              <th>金额</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tickets" :key="t.id" class="bt-clickable" @click="goTicket(t.id)">
              <td data-label="工单号"><strong>{{ t.ticket_no || '-' }}</strong></td>
              <td data-label="内容">{{ (t.description || t.content || '').substring(0, 40) }}</td>
              <td data-label="状态"><StatusBadge :status="t.status" /></td>
              <td data-label="金额">{{ formatMoney(t.total || t.amount) }}</td>
              <td data-label="时间">{{ formatDate(t.created_at) }}</td>
              <td data-label="操作" @click.stop>
                <router-link :to="'/tickets/' + t.id" class="btn btn-sm btn-outline-primary">详情</router-link>
              </td>
            </tr>
            <tr v-if="tickets.length === 0">
              <td colspan="6" class="text-center text-muted py-3">暂无工单记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 设备清单 -->
    <div v-if="activeTab === 'equipment'" class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0"><i class="bi bi-pc-display me-2"></i>设备清单</h5>
        <button class="btn btn-sm btn-outline-primary" @click="showAddEquipment = true">
          <i class="bi bi-plus-lg"></i> 添加设备
        </button>
      </div>
      <div class="table-responsive">
        <table class="bt-table">
          <thead>
            <tr>
              <th>设备名称</th>
              <th>型号</th>
              <th>位置</th>
              <th>保修到期</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="eq in equipment" :key="eq.id">
              <td>{{ eq.name }}</td>
              <td>{{ eq.model || '-' }}</td>
              <td>{{ eq.location || '-' }}</td>
              <td>
                <span v-if="eq.warranty_expiry" :class="isOverdue(eq.warranty_expiry) ? 'text-danger' : ''">
                  {{ formatDate(eq.warranty_expiry) }}
                </span>
                <span v-else class="text-muted">-</span>
              </td>
              <td>
                <button class="btn btn-sm btn-outline-danger" @click="deleteEquipment(eq.id)">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
            <tr v-if="equipment.length === 0">
              <td colspan="5" class="text-center text-muted py-3">暂无设备记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 收款记录 -->
    <div v-if="activeTab === 'payments'" class="card p-2">
      <h5 class="mb-3"><i class="bi bi-credit-card me-2"></i>收款记录</h5>
      <div class="table-responsive">
        <table class="bt-table">
          <thead>
            <tr>
              <th>金额</th>
              <th>方式</th>
              <th>关联工单</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in payments" :key="p.id">
              <td class="text-success fw-bold">{{ formatMoney(p.amount) }}</td>
              <td>{{ p.method || '-' }}</td>
              <td>{{ p.ticket_no || p.ticket_id || '-' }}</td>
              <td>{{ formatDate(p.created_at || p.paid_at) }}</td>
            </tr>
            <tr v-if="payments.length === 0">
              <td colspan="4" class="text-center text-muted py-3">暂无收款记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div class="modal fade" id="editClientModal" tabindex="-1" ref="modalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">编辑客户</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-2">
              <label class="form-label">客户名称</label>
              <input class="form-control form-control-sm" :value="editForm.name" disabled>
            </div>
            <div class="mb-2">
              <label class="form-label">联系人</label>
              <input class="form-control form-control-sm" v-model="editForm.contact">
            </div>
            <div class="mb-2">
              <label class="form-label">电话</label>
              <input class="form-control form-control-sm" v-model="editForm.phone">
            </div>
            <div class="mb-2">
              <label class="form-label">邮箱</label>
              <input type="email" class="form-control form-control-sm" v-model="editForm.email">
            </div>
            <div class="mb-2">
              <label class="form-label">地址</label>
              <input class="form-control form-control-sm" v-model="editForm.address">
            </div>
            <div class="mb-2">
              <label class="form-label">备注</label>
              <textarea class="form-control form-control-sm" rows="2" v-model="editForm.notes"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-sm btn-primary" @click="submitEdit" :disabled="submitting">
              <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
              保存
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加设备弹窗 -->
    <div v-if="showAddEquipment" class="modal-backdrop" @click.self="showAddEquipment = false">
      <div class="modal-content-card" style="max-width:500px">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0"><i class="bi bi-pc-display me-2"></i>添加设备</h5>
          <button class="btn btn-sm btn-outline-secondary" @click="showAddEquipment = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="row g-2">
          <div class="col-6">
            <label class="form-label">设备名称 *</label>
            <input v-model="equipForm.name" class="form-control" placeholder="设备名称">
          </div>
          <div class="col-6">
            <label class="form-label">型号</label>
            <input v-model="equipForm.model" class="form-control" placeholder="型号">
          </div>
          <div class="col-6">
            <label class="form-label">序列号</label>
            <input v-model="equipForm.serial_no" class="form-control" placeholder="序列号">
          </div>
          <div class="col-6">
            <label class="form-label">位置</label>
            <input v-model="equipForm.location" class="form-control" placeholder="安装位置">
          </div>
          <div class="col-6">
            <label class="form-label">保修到期</label>
            <input v-model="equipForm.warranty_expiry" type="date" class="form-control">
          </div>
        </div>
        <div class="d-flex gap-2 justify-content-end mt-3">
          <button class="btn btn-outline-secondary" @click="showAddEquipment = false">取消</button>
          <button class="btn btn-primary" @click="addEquipment" :disabled="!equipForm.name">添加</button>
        </div>
      </div>
    </div>
  </template>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { clientApi } from '@/api/clients'
import { ticketApi } from '@/api/tickets'
import { financeApi } from '@/api/finance'
import { equipmentApi } from '@/api/equipment'
import { useToast } from '@/composables/useToast'
import { formatMoney, formatDate } from '@/utils/format'
import StatusBadge from '@/components/common/StatusBadge.vue'

const props = defineProps({ name: { type: String, required: true } })
const { show: showToast } = useToast()
const router = useRouter()

const client_data = ref({})
const tickets = ref([])
const equipment = ref([])
const payments = ref([])
const loading = ref(true)
const error = ref('')
const activeTab = ref('tickets')
const stats = ref({ active_tickets: 0, total_tickets: 0, device_count: 0, unpaid_amount: 0, total_spent: 0 })
const modalEl = ref(null)
const submitting = ref(false)
const editForm = ref({ name: '', contact: '', phone: '', email: '', address: '', notes: '' })
const showAddEquipment = ref(false)
const equipForm = ref({ name: '', model: '', serial_no: '', location: '', warranty_expiry: '' })

let modalInstance = null
function getModal() {
  if (!modalInstance) {
    modalInstance = new window.bootstrap.Modal(modalEl.value)
  }
  return modalInstance
}

const tierBadge = computed(() => {
  const spent = parseFloat(stats.value.total_spent || 0)
  if (spent >= 50000) return { label: '钻石', class: 'bg-primary' }
  if (spent >= 20000) return { label: '金牌', class: 'bg-warning text-dark' }
  if (spent >= 5000) return { label: '银牌', class: 'bg-secondary' }
  return { label: '普通', class: 'bg-light text-dark' }
})

function isOverdue(dateStr) {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}

function goTicket(id) {
  router.push('/tickets/' + id)
}

onMounted(() => loadClient())

async function loadClient() {
  loading.value = true
  try {
    const clientRes = await clientApi.getByName(props.name)
    client_data.value = clientRes || {}
    if (!client_data.value.name) {
      error.value = '未找到该客户'
    }

    const [ticketsRes, equipRes] = await Promise.all([
      ticketApi.list({ client: props.name }),
      equipmentApi.list({ client: props.name }),
    ])
    tickets.value = ticketsRes?.tickets || ticketsRes?.data || []
    equipment.value = equipRes?.equipment || equipRes || []

    stats.value = {
      active_tickets: clientRes?.active_tickets || 0,
      total_tickets: ticketsRes?.total || tickets.value.length,
      device_count: equipment.value.length,
      unpaid_amount: clientRes?.unpaid_amount || 0,
      total_spent: clientRes?.total_spent || 0,
    }

    loadPayments()
  } catch (e) {
    error.value = e.response?.data?.error || '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadEquipment() {
  try {
    const data = await equipmentApi.list({ client: props.name })
    equipment.value = data?.equipment || data || []
    stats.value.device_count = equipment.value.length
  } catch (e) {
    equipment.value = []
  }
}

async function loadPayments() {
  try {
    const data = await financeApi.getClientStatement(props.name)
    payments.value = data?.payments || data?.income || []
  } catch (e) {
    try {
      const data = await financeApi.getIncome({ client: props.name })
      payments.value = data?.income || data?.records || []
    } catch {
      payments.value = []
    }
  }
}

function openEditModal() {
  editForm.value = {
    name: client_data.value.name || '',
    contact: client_data.value.contact || '',
    phone: client_data.value.phone || '',
    email: client_data.value.email || '',
    address: client_data.value.address || '',
    notes: client_data.value.notes || ''
  }
  getModal().show()
}

async function submitEdit() {
  submitting.value = true
  try {
    const { name, ...data } = editForm.value
    await clientApi.update(name, data)
    showToast('客户信息更新成功', 'success')
    getModal().hide()
    await loadClient()
  } catch (e) {
    showToast(e.response?.data?.error || '更新失败', 'danger')
  } finally {
    submitting.value = false
  }
}

async function addEquipment() {
  if (!equipForm.value.name) return
  try {
    await equipmentApi.create({
      ...equipForm.value,
      client: props.name,
    })
    showToast('设备已添加', 'success')
    showAddEquipment.value = false
    equipForm.value = { name: '', model: '', serial_no: '', location: '', warranty_expiry: '' }
    await loadEquipment()
  } catch (e) {
    showToast('添加失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}

async function deleteEquipment(eqId) {
  try {
    await equipmentApi.delete(eqId)
    showToast('设备已删除', 'success')
    await loadEquipment()
  } catch (e) {
    showToast('删除失败', 'danger')
  }
}
</script>
