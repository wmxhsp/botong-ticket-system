<template>
  <div>
    <div class="bt-page-title">
      <h2>新建工单</h2>
      <p class="d-none d-md-inline">创建新的维修服务工单</p>
    </div>

    <div class="card p-4">
      <form @submit.prevent="submitTicket">
        <div class="row g-2">
          <div class="col-md-4">
            <label class="form-label">客户名称 <span class="text-danger">*</span></label>
            <ClientSelector v-model="form.client" @select="onClientSelect" />
          </div>
          <div class="col-md-4">
            <label class="form-label">联系人</label>
            <input class="form-control" v-model="form.contact" placeholder="联系人姓名">
          </div>
          <div class="col-md-4">
            <label class="form-label">联系电话</label>
            <input class="form-control" v-model="form.phone" placeholder="客户联系电话">
          </div>

          <div class="col-md-4">
            <label class="form-label">服务项目 <span class="text-danger">*</span></label>
            <select class="form-select" v-model="form.service_fee_id" @change="onServiceFeeChange">
              <option value="">选择服务项目...</option>
              <option v-for="f in serviceFees" :key="f.id" :value="f.id"
                      :data-fee-type="f.fee_type" :data-price="f.unit_price">
                {{ f.name }} (¥{{ f.unit_price }}{{ feeSuffix(f.fee_type) }})
              </option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">工程师</label>
            <select class="form-select" v-model="form.assignee">
              <option value="">选择工程师...</option>
              <option v-for="t in technicians" :key="t.id" :value="t.name">
                {{ t.name }} (¥{{ t.cost_rate || 0 }}/h)
              </option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">优先级</label>
            <select class="form-select" v-model="form.priority">
              <option value="">默认</option>
              <option value="L">低</option>
              <option value="M">中</option>
              <option value="H">高</option>
              <option value="U">紧急</option>
            </select>
          </div>

          <div class="col-12">
            <label class="form-label">服务内容 <span class="text-danger">*</span></label>
            <textarea class="form-control" v-model="form.content" rows="3"
                      placeholder="描述服务内容" required @input="updateReminderPreview"></textarea>
          </div>

          <div class="col-md-3">
            <label class="form-label">预计工时</label>
            <div class="input-group">
              <input class="form-control" v-model.number="form.estimated_hours" type="number" step="0.5" min="0" placeholder="0" @input="calcFee">
              <span class="input-group-text">小时</span>
            </div>
          </div>
          <div class="col-md-3">
            <label class="form-label">人工费</label>
            <div class="input-group">
              <span class="input-group-text">¥</span>
              <input class="form-control" v-model="form.amount" type="number" step="0.01" placeholder="0.00">
            </div>
          </div>
          <div class="col-md-3">
            <label class="form-label">配件费</label>
            <div class="input-group">
              <span class="input-group-text">¥</span>
              <input class="form-control" v-model.number="form.parts_fee" type="number" step="0.01" placeholder="0.00" @input="calcFee">
            </div>
          </div>
          <div class="col-md-3">
            <label class="form-label">合计</label>
            <div class="form-control-plaintext fw-bold text-primary">
              ¥{{ totalDisplay }}
            </div>
          </div>

          <div class="col-md-4">
            <label class="form-label">关联设备</label>
            <select class="form-select" v-model="form.equipment_id" :disabled="!form.client">
              <option value="">不关联设备</option>
              <option v-for="eq in clientEquipment" :key="eq.id" :value="eq.id">
                {{ eq.name }}{{ eq.model ? ` (${eq.model})` : '' }}{{ eq.location ? ` - ${eq.location}` : '' }}
              </option>
            </select>
            <small v-if="!form.client" class="text-muted">请先选择客户</small>
          </div>
          <div class="col-md-4">
            <label class="form-label">预约时间</label>
            <input class="form-control" v-model="form.appointment_at" type="datetime-local" @input="updateReminderPreview">
          </div>
          <div class="col-md-4">
            <label class="form-label">地址</label>
            <input class="form-control" v-model="form.address" placeholder="服务地址">
          </div>

          <div class="col-md-4">
            <label class="form-label">出行距离</label>
            <div class="input-group">
              <input class="form-control" v-model.number="form.travel_distance" type="number" step="0.1" min="0" placeholder="0" @input="calcFee">
              <span class="input-group-text">km</span>
            </div>
          </div>
          <div class="col-md-4">
            <label class="form-label">出行费率</label>
            <div class="input-group">
              <input class="form-control" v-model.number="form.travel_rate" type="number" step="0.1" min="0" placeholder="0" @input="calcFee">
              <span class="input-group-text">元/km</span>
            </div>
          </div>
          <div class="col-md-4">
            <label class="form-label">出行费</label>
            <div class="form-control-plaintext">
              ¥{{ travelDisplay }}
            </div>
          </div>

          <div class="col-12" v-if="form.appointment_at">
            <div class="form-check">
              <input class="form-check-input" type="checkbox" v-model="form.enable_reminder" id="enableReminder" @change="updateReminderPreview">
              <label class="form-check-label" for="enableReminder">
                创建预约提醒
              </label>
            </div>
            <small class="text-muted ms-4" v-if="reminderPreview">{{ reminderPreview }}</small>
          </div>

          <div class="col-12">
            <label class="form-label">备注</label>
            <textarea class="form-control" v-model="form.notes" rows="2" placeholder="其他备注信息"></textarea>
          </div>
        </div>

        <div class="mt-4 d-flex gap-2">
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-plus-lg me-1"></i>
            {{ submitting ? '提交中...' : '创建工单' }}
          </button>
          <button type="button" class="btn btn-outline-secondary" @click="resetForm">重置</button>
          <router-link to="/tickets" class="btn btn-outline-secondary">取消</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ticketApi } from '@/api/tickets'
import { serviceFeeApi } from '@/api/service-fees'
import { staffApi } from '@/api/staff'
import { equipmentApi } from '@/api/equipment'
import { useToast } from '@/composables/useToast'
import ClientSelector from '@/components/selectors/ClientSelector.vue'

const router = useRouter()
const submitting = ref(false)
const { show: showToast } = useToast()

const serviceFees = ref([])
const technicians = ref([])
const clientEquipment = ref([])
const reminderPreview = ref('')

const form = ref({
  client: '',
  contact: '',
  phone: '',
  content: '',
  service_fee_id: '',
  assignee: '',
  priority: '',
  estimated_hours: 0,
  amount: '',
  parts_fee: 0,
  equipment_id: '',
  appointment_at: '',
  address: '',
  travel_distance: 0,
  travel_rate: 0,
  enable_reminder: true,
  notes: '',
})

const totalDisplay = computed(() => {
  const labor = parseFloat(form.value.amount) || 0
  const parts = parseFloat(form.value.parts_fee) || 0
  const travel = (parseFloat(form.value.travel_distance) || 0) * (parseFloat(form.value.travel_rate) || 0)
  return (labor + parts + travel).toFixed(2)
})

const travelDisplay = computed(() => {
  const dist = parseFloat(form.value.travel_distance) || 0
  const rate = parseFloat(form.value.travel_rate) || 0
  return (dist * rate).toFixed(2)
})

function feeSuffix(feeType) {
  const map = { hourly: '/h', fixed: '/次', monthly: '/月', yearly: '/年', per_km: '/km' }
  return map[feeType] || '/次'
}

function onClientSelect(client) {
  if (client) {
    form.value.contact = form.value.contact || client.contact || ''
    form.value.phone = form.value.phone || client.phone || ''
    form.value.address = form.value.address || client.address || ''
    loadClientEquipment(client.name)
  } else {
    clientEquipment.value = []
    form.value.equipment_id = ''
  }
}

async function loadClientEquipment(clientName) {
  if (!clientName) {
    clientEquipment.value = []
    return
  }
  try {
    const data = await equipmentApi.list({ client: clientName })
    clientEquipment.value = data.equipment || []
  } catch (e) {
    clientEquipment.value = []
  }
}

function onServiceFeeChange() {
  const sel = form.value.service_fee_id
  if (!sel) return
  const fee = serviceFees.value.find(f => f.id === sel)
  if (!fee) return
  form.value.billing_model = fee.fee_type || 'hourly'
  calcFee()
}

function calcFee() {
  const sel = form.value.service_fee_id
  const fee = serviceFees.value.find(f => f.id === sel)
  if (!fee) return

  const price = parseFloat(fee.unit_price) || 0
  const feeType = fee.fee_type || ''
  const hours = parseFloat(form.value.estimated_hours) || 0
  let laborFee = 0

  if (feeType === 'hourly') {
    laborFee = hours * price
  } else if (feeType === 'fixed' || feeType === 'monthly' || feeType === 'yearly') {
    laborFee = price
  } else if (feeType === 'per_km') {
    const dist = parseFloat(form.value.travel_distance) || 0
    laborFee = dist * price
  }

  form.value.amount = laborFee.toFixed(2)
}

function updateReminderPreview() {
  if (!form.value.appointment_at) {
    reminderPreview.value = ''
    return
  }
  if (!form.value.enable_reminder) {
    reminderPreview.value = '每日提醒已关闭'
    return
  }
  const client = form.value.client || '未知客户'
  const content = (form.value.content || '').trim() || '服务内容'
  reminderPreview.value = `${client} - ${content}`
}

function resetForm() {
  form.value = {
    client: '', contact: '', phone: '', content: '',
    service_fee_id: '', assignee: '', priority: '',
    estimated_hours: 0, amount: '', parts_fee: 0,
    equipment_id: '', appointment_at: '', address: '',
    travel_distance: 0, travel_rate: 0,
    enable_reminder: true, notes: '',
  }
  reminderPreview.value = ''
  clientEquipment.value = []
  showToast('表单已重置', 'info')
}

async function submitTicket() {
  if (!form.value.client) {
    showToast('请选择客户', 'warning')
    return
  }
  if (!form.value.content) {
    showToast('请输入服务内容', 'warning')
    return
  }

  submitting.value = true
  try {
    const payload = {
      client: form.value.client,
      content: form.value.content,
      phone: form.value.phone || undefined,
      contact: form.value.contact || undefined,
      address: form.value.address || undefined,
      assignee: form.value.assignee || undefined,
      priority: form.value.priority || undefined,
      service_fee_id: form.value.service_fee_id ? parseInt(form.value.service_fee_id) : undefined,
      billing_model: form.value.billing_model || undefined,
      estimated_hours: form.value.estimated_hours || undefined,
      amount: form.value.amount ? parseFloat(form.value.amount) : undefined,
      parts_fee: form.value.parts_fee || undefined,
      equipment_id: form.value.equipment_id ? parseInt(form.value.equipment_id) : undefined,
      appointment_at: form.value.appointment_at || undefined,
      travel_distance: form.value.travel_distance || undefined,
      travel_rate: form.value.travel_rate || undefined,
      notes: form.value.notes || undefined,
    }

    const res = await ticketApi.create(payload)
    showToast('工单创建成功', 'success')
    const resData = res.data || res
    const ticket = resData.ticket || resData.data || resData
    if (ticket && ticket.id) {
      router.push('/tickets/' + ticket.id)
    } else {
      router.push('/tickets')
    }
  } catch (e) {
    console.error('创建失败:', e)
    showToast('创建失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const feeData = await serviceFeeApi.list()
    serviceFees.value = (feeData.fees || []).filter(f => f.active)
  } catch (e) {
    console.error('加载服务项目失败:', e)
  }
  try {
    const techData = await staffApi.list()
    technicians.value = techData.technicians || []
  } catch (e) {
    console.error('加载工程师列表失败:', e)
  }
})
</script>
