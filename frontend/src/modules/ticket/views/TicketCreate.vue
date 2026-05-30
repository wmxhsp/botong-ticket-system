<template>
  <div>
    <div class="bt-page-title">
      <h2>新建工单</h2>
      <p class="d-none d-md-inline">创建新的维修服务工单</p>
    </div>

    <div class="card p-4">
      <form @submit.prevent="submitTicket">
        <!-- 模板选择 -->
        <div v-if="templates.length" class="mb-3 p-2 rounded" style="background:var(--bt-gray-100)">
          <div class="d-flex align-items-center gap-2 mb-2">
            <i class="bi bi-file-earmark-text"></i>
            <span class="small fw-semibold">快速填入模板</span>
          </div>
          <div class="d-flex gap-1 flex-wrap">
            <button v-for="tpl in templates" :key="tpl.id" type="button"
                    class="btn btn-sm" :class="selectedTemplate === tpl.id ? 'btn-primary' : 'btn-outline-secondary'"
                    @click="applyTemplate(tpl)">
              {{ tpl.name }}
            </button>
          </div>
        </div>

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
                {{ t.name }} (¥{{ formatRate(t) }})
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
          <div class="col-md-3" v-if="form.billing_model === 'daily'">
            <label class="form-label">工作天数</label>
            <div class="input-group">
              <input class="form-control" v-model.number="form.estimated_days" type="number" step="0.5" min="0" placeholder="0" @input="calcFee">
              <span class="input-group-text">天</span>
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
import { toolsApi } from '@/api/tools'
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
const templates = ref([])
const selectedTemplate = ref(null)

const form = ref({
  client: '',
  contact: '',
  phone: '',
  content: '',
  service_fee_id: '',
  assignee: '',
  priority: '',
  estimated_hours: 0,
  estimated_days: 0,
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
  const days = parseFloat(form.value.estimated_days) || 0
  let laborFee = 0

  if (feeType === 'hourly') {
    laborFee = hours * price
  } else if (feeType === 'daily') {
    laborFee = days * price
  } else if (feeType === 'package') {
    laborFee = price
  } else if (feeType === 'fixed' || feeType === 'monthly' || feeType === 'yearly') {
    laborFee = price
  } else if (feeType === 'per_km') {
    const dist = parseFloat(form.value.travel_distance) || 0
    laborFee = dist * price
  }

  form.value.amount = laborFee.toFixed(2)
}

function formatRate(tech) {
  const bt = tech.billing_type || 'hourly'
  const rate = tech.cost_rate || 0
  const dailyRate = tech.daily_cost_rate || 0
  if (bt === 'daily') return `${dailyRate || rate * 8}/天`
  if (bt === 'package') return `${tech.package_cost || rate}/包`
  return `${rate}/h`
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
    estimated_hours: 0, estimated_days: 0, amount: '', parts_fee: 0,
    equipment_id: '', appointment_at: '', address: '',
    travel_distance: 0, travel_rate: 0,
    enable_reminder: true, notes: '',
  }
  reminderPreview.value = ''
  clientEquipment.value = []
  showToast('表单已重置', 'info')
}

function validateTicketForm(formData) {
  const rules = [
    { field: 'client', message: '请选择客户' },
    { field: 'content', message: '请输入服务内容' },
  ]
  const errors = rules
    .filter(rule => !formData[rule.field])
    .map(rule => rule.message)
  return { isValid: errors.length === 0, errors }
}

function buildTicketPayload(formData) {
  const toOptional = (value) => value || undefined
  const toOptionalInt = (value) => value ? parseInt(value) : undefined
  const toOptionalFloat = (value) => value ? parseFloat(value) : undefined

  return {
    client: formData.client,
    content: formData.content,
    phone: toOptional(formData.phone),
    contact: toOptional(formData.contact),
    address: toOptional(formData.address),
    assignee: toOptional(formData.assignee),
    priority: toOptional(formData.priority),
    service_fee_id: toOptionalInt(formData.service_fee_id),
    billing_model: toOptional(formData.billing_model),
    estimated_hours: toOptional(formData.estimated_hours),
    estimated_days: toOptional(formData.estimated_days),
    amount: toOptionalFloat(formData.amount),
    parts_fee: toOptional(formData.parts_fee),
    equipment_id: toOptionalInt(formData.equipment_id),
    appointment_at: toOptional(formData.appointment_at),
    travel_distance: toOptional(formData.travel_distance),
    travel_rate: toOptional(formData.travel_rate),
    notes: toOptional(formData.notes),
  }
}

function handleTicketCreated(response) {
  showToast('工单创建成功', 'success')
  const ticket = response?.ticket || response?.data || response
  if (ticket && ticket.id) {
    router.push('/tickets/' + ticket.id)
  } else {
    router.push('/tickets')
  }
}

async function submitTicket() {
  const validation = validateTicketForm(form.value)
  if (!validation.isValid) {
    showToast(validation.errors[0], 'warning')
    return
  }

  submitting.value = true
  try {
    const payload = buildTicketPayload(form.value)
    const res = await ticketApi.create(payload)
    handleTicketCreated(res)
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
  try {
    const tplData = await toolsApi.listTemplates()
    templates.value = tplData.templates || tplData || []
  } catch (e) {
    /* 无模板也正常 */
  }
})

async function applyTemplate(tpl) {
  if (selectedTemplate.value === tpl.id) {
    selectedTemplate.value = null
    return
  }
  selectedTemplate.value = tpl.id
  try {
    const data = await toolsApi.applyTemplate(tpl.id)
    const t = data.template || data
    if (t.content) form.value.content = t.content
    if (t.client) form.value.client = t.client
    if (t.service_fee_id) form.value.service_fee_id = t.service_fee_id
    if (t.priority) form.value.priority = t.priority
    if (t.assignee) form.value.assignee = t.assignee
    if (t.estimated_hours) form.value.estimated_hours = t.estimated_hours
    if (t.amount) form.value.amount = t.amount
    if (t.parts_fee) form.value.parts_fee = t.parts_fee
    if (t.notes) form.value.notes = t.notes
    showToast(`已填入模板「${tpl.name}」`, 'success')
  } catch (e) {
    /* applyTemplate 失败则手动填入本地数据 */
    if (tpl.content) form.value.content = tpl.content
    if (tpl.priority) form.value.priority = tpl.priority
    if (tpl.assignee) form.value.assignee = tpl.assignee
    showToast(`已填入模板「${tpl.name}」`, 'success')
  }
}
</script>
