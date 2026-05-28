<template>
  <div v-if="loading" class="bt-empty-state">
    <div class="bt-inline-loading"><div class="bt-spinner"></div> 加载设备信息...</div>
  </div>

  <template v-else-if="equip.id">
    <div class="bt-breadcrumbs">
      <router-link :to="{name: 'Equipment'}">设备管理</router-link>
      <span class="bt-breadcrumb-sep">/</span>
      <span class="bt-breadcrumb-current">{{ equip.name }}</span>
    </div>

    <div class="row g-2">
      <div class="col-md-8">
        <div class="card p-2 mb-3">
          <h5 class="mb-3"><i class="bi bi-pc-display me-2"></i>基本信息</h5>
          <table class="table table-borderless table-sm mb-0">
            <tr><th style="width:100px">设备名称</th><td>{{ equip.name }}</td><th>类型</th><td>{{ equip.type || '-' }}</td></tr>
            <tr><th>品牌</th><td>{{ equip.brand || '-' }}</td><th>型号</th><td>{{ equip.model || '-' }}</td></tr>
            <tr><th>序列号</th><td><code>{{ equip.serial_no || '-' }}</code></td><th>状态</th>
              <td><span class="bt-data-tag" :class="statusClass">{{ equip.status }}</span></td></tr>
            <tr><th>所属客户</th><td>
              <router-link :to="{name: 'ClientDetail', params: {name: equip.client}}" class="text-decoration-none">
                {{ equip.client_name || equip.client }}
              </router-link>
            </td><th>安装日期</th><td>{{ equip.install_date || '-' }}</td></tr>
            <tr><th>保修到期</th><td>{{ equip.warranty_expire || '-' }}</td><th>维护周期</th><td>{{ equip.maintenance_cycle || '-' }}</td></tr>
            <tr><th>位置</th><td colspan="3">{{ equip.location || '-' }}</td></tr>
            <tr><th>备注</th><td colspan="3">{{ equip.notes || '-' }}</td></tr>
          </table>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card p-2 mb-3">
          <h5 class="mb-3"><i class="bi bi-cash me-2"></i>财务摘要</h5>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-muted">工单数</span><span>{{ finance.total_tickets || 0 }}</span>
          </div>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-muted">总收入</span><span class="text-success">{{ formatMoney(finance.total_revenue) }}</span>
          </div>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-muted">总成本</span><span class="text-danger">{{ formatMoney(finance.total_cost) }}</span>
          </div>
          <hr class="my-1">
          <div class="d-flex justify-content-between small fw-bold">
            <span>利润</span><span :style="{color: (finance.total_profit||0) >= 0 ? 'var(--bt-accent-green)' : 'var(--bt-danger)'}">{{ formatMoney(finance.total_profit) }}</span>
          </div>
        </div>
        <!-- QR码 -->
        <div class="card p-2 text-center">
          <h6 class="mb-2"><i class="bi bi-qr-code me-1"></i>设备二维码</h6>
          <div v-if="qrLoading" class="py-3"><div class="bt-spinner"></div></div>
          <div v-else-if="qrData" class="mb-2">
            <img v-if="qrData.qr_url || qrData.url" :src="qrData.qr_url || qrData.url" alt="QR Code" style="max-width:160px">
            <div v-else class="p-2 bg-light rounded small">{{ qrData.content || qrData.data || equip.serial_no || equip.id }}</div>
          </div>
          <button class="btn btn-sm btn-outline-primary" @click="loadQrCode"><i class="bi bi-qr-code me-1"></i>生成二维码</button>
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'tickets' }" @click="activeTab = 'tickets'; loadRelatedTickets()">
          <i class="bi bi-ticket-perforated me-1"></i>关联工单
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'photos' }" @click="activeTab = 'photos'; loadPhotos()">
          <i class="bi bi-images me-1"></i>照片
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'maintenance' }" @click="activeTab = 'maintenance'; loadMaintenance()">
          <i class="bi bi-wrench me-1"></i>维保
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'components' }" @click="activeTab = 'components'; loadComponents()">
          <i class="bi bi-puzzle me-1"></i>组件
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'timeline' }" @click="activeTab = 'timeline'; loadTimeline()">
          <i class="bi bi-clock-history me-1"></i>时间线
        </button>
      </li>
    </ul>

    <!-- 关联工单 -->
    <div v-if="activeTab === 'tickets'" class="card p-2">
      <div v-if="ticketsLoading" class="text-center py-3"><div class="bt-spinner"></div></div>
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>工单号</th><th>内容</th><th>状态</th><th>金额</th><th>创建时间</th></tr></thead>
          <tbody>
            <tr v-for="t in relatedTickets" :key="t.id">
              <td class="fw-bold"><router-link :to="'/tickets/' + t.id" class="text-decoration-none">{{ t.ticket_no || '-' }}</router-link></td>
              <td class="small">{{ (t.description || t.content || '').substring(0, 50) }}</td>
              <td><span class="badge" :class="ticketStatusBadge(t.status)">{{ t.status }}</span></td>
              <td>{{ formatMoney(t.total || t.amount) }}</td>
              <td class="small text-muted">{{ (t.created_at || '').slice(0, 10) }}</td>
            </tr>
            <tr v-if="relatedTickets.length === 0"><td colspan="5" class="text-center text-muted py-3">暂无关联工单</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 照片 -->
    <div v-if="activeTab === 'photos'" class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0"><i class="bi bi-images me-2"></i>设备照片</h5>
        <label class="btn btn-sm btn-primary mb-0" :disabled="photoUploading">
          <i class="bi bi-cloud-upload me-1"></i>{{ photoUploading ? '上传中...' : '上传照片' }}
          <input type="file" accept="image/*" multiple hidden @change="uploadPhotos">
        </label>
      </div>
      <div v-if="photosLoading" class="text-center py-3"><div class="bt-spinner"></div></div>
      <div v-else-if="photos.length === 0" class="text-center py-4 text-muted">
        <i class="bi bi-image" style="font-size:48px"></i><p class="mt-2">暂无照片</p>
      </div>
      <div v-else class="row g-2">
        <div v-for="photo in photos" :key="photo.id" class="col-6 col-sm-4 col-md-3">
          <div class="card p-1 position-relative">
            <img :src="photo.url || photo.thumbnail || photo.path" class="img-fluid rounded" :alt="photo.filename || '照片'" style="height:140px;object-fit:cover;width:100%">
            <div v-if="photo.is_cover" class="position-absolute top-0 end-0 m-1"><span class="badge bg-primary">封面</span></div>
            <div class="d-flex gap-1 mt-1">
              <button v-if="!photo.is_cover" class="btn btn-xs btn-outline-primary" @click="setCover(photo)">设为封面</button>
              <button class="btn btn-xs btn-outline-danger" @click="deletePhoto(photo)"><i class="bi bi-trash"></i></button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 维保 -->
    <div v-if="activeTab === 'maintenance'" class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0"><i class="bi bi-wrench me-2"></i>维保记录</h5>
        <button class="btn btn-sm btn-primary" @click="showMaintForm = true"><i class="bi bi-plus-lg me-1"></i>记录维保</button>
      </div>
      <div v-if="maintLoading" class="text-center py-3"><div class="bt-spinner"></div></div>
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>日期</th><th>类型</th><th>内容</th><th>费用</th><th>下次维保</th></tr></thead>
          <tbody>
            <tr v-for="m in maintHistory" :key="m.id">
              <td class="small">{{ (m.performed_at || m.created_at || '').slice(0, 10) }}</td>
              <td><span class="badge bg-info">{{ m.type || '常规' }}</span></td>
              <td>{{ m.description || m.content || '-' }}</td>
              <td>{{ formatMoney(m.cost) }}</td>
              <td class="small">{{ m.next_maintenance || '-' }}</td>
            </tr>
            <tr v-if="maintHistory.length === 0"><td colspan="5" class="text-center text-muted py-3">暂无维保记录</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 组件 -->
    <div v-if="activeTab === 'components'" class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0"><i class="bi bi-puzzle me-2"></i>设备组件</h5>
        <button class="btn btn-sm btn-primary" @click="showCompForm = true"><i class="bi bi-plus-lg me-1"></i>添加组件</button>
      </div>
      <div v-if="compLoading" class="text-center py-3"><div class="bt-spinner"></div></div>
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>名称</th><th>型号</th><th>序列号</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="c in components" :key="c.id">
              <td class="fw-bold">{{ c.name }}</td>
              <td>{{ c.model || '-' }}</td>
              <td><code>{{ c.serial_no || '-' }}</code></td>
              <td><span class="badge" :class="compStatusBadge(c.status)">{{ c.status || '正常' }}</span></td>
              <td>
                <div class="d-flex gap-1">
                  <button class="btn btn-sm btn-outline-primary" @click="editComponent(c)"><i class="bi bi-pencil"></i></button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteComponent(c)"><i class="bi bi-trash"></i></button>
                </div>
              </td>
            </tr>
            <tr v-if="components.length === 0"><td colspan="5" class="text-center text-muted py-3">暂无组件</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 时间线 -->
    <div v-if="activeTab === 'timeline'" class="card p-2">
      <h5 class="mb-3"><i class="bi bi-clock-history me-2"></i>设备时间线</h5>
      <div v-if="timelineLoading" class="text-center py-3"><div class="bt-spinner"></div></div>
      <div v-else-if="timeline.length === 0" class="text-center py-4 text-muted">
        <i class="bi bi-clock" style="font-size:48px"></i><p class="mt-2">暂无时间线记录</p>
      </div>
      <div v-else class="bt-timeline">
        <div v-for="(evt, i) in timeline" :key="i" class="bt-timeline-item">
          <div class="bt-timeline-dot" :class="timelineDotClass(evt.type)"></div>
          <div class="bt-timeline-content">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <strong>{{ evt.title || evt.action || evt.type }}</strong>
                <p v-if="evt.description" class="small text-muted mb-0">{{ evt.description }}</p>
              </div>
              <span class="small text-muted">{{ (evt.created_at || evt.date || '').slice(0, 16) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 维保记录弹窗 -->
    <BtModal v-model:visible="showMaintForm" title="记录维保" icon="bi-wrench" max-width="500px" :show-footer="false">
      <template #body>
        <form @submit.prevent="saveMaintenance">
          <div class="mb-2">
            <label class="form-label">维保类型</label>
            <select v-model="maintForm.type" class="form-select form-select-sm">
              <option value="routine">常规保养</option>
              <option value="repair">维修</option>
              <option value="inspection">巡检</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div class="mb-2">
            <label class="form-label">维保内容 <span class="text-danger">*</span></label>
            <textarea v-model="maintForm.description" class="form-control form-control-sm" rows="3" required placeholder="描述维保内容"></textarea>
          </div>
          <div class="row g-2 mb-2">
            <div class="col-6">
              <label class="form-label">费用</label>
              <input v-model.number="maintForm.cost" type="number" step="0.01" class="form-control form-control-sm" placeholder="0.00">
            </div>
            <div class="col-6">
              <label class="form-label">下次维保日期</label>
              <input v-model="maintForm.next_maintenance" type="date" class="form-control form-control-sm">
            </div>
          </div>
          <div class="d-flex gap-2 justify-content-end mt-3">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showMaintForm = false">取消</button>
            <button type="submit" class="btn btn-sm btn-primary" :disabled="maintSaving">
              <span v-if="maintSaving" class="spinner-border spinner-border-sm me-1"></span>保存
            </button>
          </div>
        </form>
      </template>
    </BtModal>

    <!-- 组件弹窗 -->
    <BtModal v-model:visible="showCompForm" :title="editingComp ? '编辑组件' : '添加组件'" icon="bi-puzzle" max-width="500px" :show-footer="false">
      <template #body>
        <form @submit.prevent="saveComponent">
          <div class="mb-2">
            <label class="form-label">组件名称 <span class="text-danger">*</span></label>
            <input v-model="compForm.name" class="form-control form-control-sm" required>
          </div>
          <div class="row g-2 mb-2">
            <div class="col-6">
              <label class="form-label">型号</label>
              <input v-model="compForm.model" class="form-control form-control-sm">
            </div>
            <div class="col-6">
              <label class="form-label">序列号</label>
              <input v-model="compForm.serial_no" class="form-control form-control-sm">
            </div>
          </div>
          <div class="mb-2">
            <label class="form-label">状态</label>
            <select v-model="compForm.status" class="form-select form-select-sm">
              <option value="正常">正常</option>
              <option value="维修中">维修中</option>
              <option value="已更换">已更换</option>
              <option value="已报废">已报废</option>
            </select>
          </div>
          <div class="d-flex gap-2 justify-content-end mt-3">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showCompForm = false">取消</button>
            <button type="submit" class="btn btn-sm btn-primary" :disabled="compSaving">保存</button>
          </div>
        </form>
      </template>
    </BtModal>
  </template>

  <div v-else class="bt-empty-state">
    <div class="bt-empty-icon"><i class="bi bi-pc-display"></i></div>
    <div class="bt-empty-title">设备未找到</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { equipmentApi } from '@/api/equipment'
import { formatMoney } from '@/utils/format'
import { useToast } from '@/composables/useToast'
import BtModal from '@/components/common/BtModal.vue'

const props = defineProps({ id: { type: String, required: true } })
const { show: showToast } = useToast()

const equip = ref({})
const loading = ref(true)
const activeTab = ref('tickets')
const finance = computed(() => equip.value.finance_summary || {})

const statusClass = computed(() => {
  const map = { '正常': 'success', '维修中': 'warning', '已报废': 'danger' }
  return map[equip.value.status] || 'primary'
})

// QR码
const qrData = ref(null)
const qrLoading = ref(false)

// 关联工单
const relatedTickets = ref([])
const ticketsLoading = ref(false)

// 照片
const photos = ref([])
const photosLoading = ref(false)
const photoUploading = ref(false)

// 维保
const maintHistory = ref([])
const maintLoading = ref(false)
const showMaintForm = ref(false)
const maintSaving = ref(false)
const maintForm = ref({ type: 'routine', description: '', cost: '', next_maintenance: '' })

// 组件
const components = ref([])
const compLoading = ref(false)
const showCompForm = ref(false)
const compSaving = ref(false)
const editingComp = ref(null)
const compForm = ref({ name: '', model: '', serial_no: '', status: '正常' })

// 时间线
const timeline = ref([])
const timelineLoading = ref(false)

onMounted(async () => {
  try {
    equip.value = await equipmentApi.getById(props.id)
  } catch { /* empty */ } finally { loading.value = false }
})

// ── QR码 ──
async function loadQrCode() {
  qrLoading.value = true
  try { qrData.value = await equipmentApi.getQrCode(props.id) }
  catch (e) { showToast('生成二维码失败', 'danger') }
  finally { qrLoading.value = false }
}

// ── 关联工单 ──
async function loadRelatedTickets() {
  ticketsLoading.value = true
  try { relatedTickets.value = Array.isArray(await equipmentApi.getTickets(props.id)) ? await equipmentApi.getTickets(props.id) : [] }
  catch (e) { relatedTickets.value = [] }
  finally { ticketsLoading.value = false }
}

function ticketStatusBadge(status) {
  const map = { 'open': 'bg-secondary', 'in-progress': 'bg-info', 'completed': 'bg-success', 'closed': 'bg-success', 'cancelled': 'bg-danger' }
  return map[status] || 'bg-secondary'
}

// ── 照片 ──
async function loadPhotos() {
  photosLoading.value = true
  try {
    const data = await equipmentApi.getPhotos(props.id)
    photos.value = Array.isArray(data) ? data : data?.photos || []
  } catch (e) { photos.value = [] }
  finally { photosLoading.value = false }
}

async function uploadPhotos(event) {
  const files = event.target.files
  if (!files || !files.length) return
  photoUploading.value = true
  try {
    const formData = new FormData()
    for (const f of files) formData.append('photos', f)
    await equipmentApi.batchUploadPhotos(props.id, formData)
    showToast('照片上传成功', 'success')
    await loadPhotos()
  } catch (e) { showToast('上传失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { photoUploading.value = false; event.target.value = '' }
}

async function setCover(photo) {
  try {
    await equipmentApi.updatePhotoSettings(props.id, { cover_photo_id: photo.id })
    showToast('封面已设置', 'success')
    await loadPhotos()
  } catch (e) { showToast('设置失败', 'danger') }
}

async function deletePhoto(photo) {
  if (!confirm('确认删除该照片？')) return
  try {
    await equipmentApi.deletePhoto(props.id, { photo_id: photo.id })
    showToast('照片已删除', 'success')
    await loadPhotos()
  } catch (e) { showToast('删除失败', 'danger') }
}

// ── 维保 ──
async function loadMaintenance() {
  maintLoading.value = true
  try {
    const data = await equipmentApi.getMaintenanceHistory(props.id)
    maintHistory.value = Array.isArray(data) ? data : data?.records || []
  } catch (e) { maintHistory.value = [] }
  finally { maintLoading.value = false }
}

async function saveMaintenance() {
  maintSaving.value = true
  try {
    await equipmentApi.recordMaintenance(props.id, maintForm.value)
    showToast('维保记录已保存', 'success')
    showMaintForm.value = false
    maintForm.value = { type: 'routine', description: '', cost: '', next_maintenance: '' }
    await loadMaintenance()
  } catch (e) { showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { maintSaving.value = false }
}

// ── 组件 ──
async function loadComponents() {
  compLoading.value = true
  try {
    const data = await equipmentApi.getComponents(props.id)
    components.value = Array.isArray(data) ? data : data?.components || []
  } catch (e) { components.value = [] }
  finally { compLoading.value = false }
}

function editComponent(c) {
  editingComp.value = c
  compForm.value = { name: c.name, model: c.model || '', serial_no: c.serial_no || '', status: c.status || '正常' }
  showCompForm.value = true
}

async function saveComponent() {
  compSaving.value = true
  try {
    if (editingComp.value) {
      await equipmentApi.updateComponent(props.id, editingComp.value.id, compForm.value)
      showToast('组件已更新', 'success')
    } else {
      await equipmentApi.addComponent(props.id, compForm.value)
      showToast('组件已添加', 'success')
    }
    showCompForm.value = false
    editingComp.value = null
    compForm.value = { name: '', model: '', serial_no: '', status: '正常' }
    await loadComponents()
  } catch (e) { showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { compSaving.value = false }
}

async function deleteComponent(c) {
  if (!confirm(`确认删除组件「${c.name}」？`)) return
  try {
    await equipmentApi.deleteComponent(props.id, c.id)
    showToast('组件已删除', 'success')
    await loadComponents()
  } catch (e) { showToast('删除失败', 'danger') }
}

function compStatusBadge(status) {
  const map = { '正常': 'bg-success', '维修中': 'bg-warning text-dark', '已更换': 'bg-info', '已报废': 'bg-danger' }
  return map[status] || 'bg-secondary'
}

// ── 时间线 ──
async function loadTimeline() {
  timelineLoading.value = true
  try {
    const data = await equipmentApi.getTimeline(props.id)
    timeline.value = Array.isArray(data) ? data : data?.events || []
  } catch (e) { timeline.value = [] }
  finally { timelineLoading.value = false }
}

function timelineDotClass(type) {
  const map = { 'install': 'bg-primary', 'repair': 'bg-warning', 'maintenance': 'bg-info', 'payment': 'bg-success', 'ticket': 'bg-secondary' }
  return map[type] || 'bg-secondary'
}
</script>

<style scoped>
.btn-xs {
  padding: 2px 6px;
  font-size: 11px;
  border-radius: 3px;
}

.bt-timeline {
  position: relative;
  padding-left: 24px;
}

.bt-timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--card-border, #e5e7eb);
}

.bt-timeline-item {
  position: relative;
  padding-bottom: 16px;
}

.bt-timeline-item:last-child {
  padding-bottom: 0;
}

.bt-timeline-dot {
  position: absolute;
  left: -20px;
  top: 4px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
}

.bt-timeline-content {
  background: var(--card-bg, #f9fafb);
  border-radius: 8px;
  padding: 8px 12px;
  border: 1px solid var(--card-border, #e5e7eb);
}

[data-theme="dark"] .bt-timeline::before {
  background: var(--card-border, #374151);
}

[data-theme="dark"] .bt-timeline-dot {
  border-color: var(--card-bg, #1f2937);
}

[data-theme="dark"] .bt-timeline-content {
  background: var(--card-bg, #1f2937);
  border-color: var(--card-border, #374151);
}
</style>
