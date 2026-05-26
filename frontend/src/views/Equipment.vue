<template>
  <div>
    <div class="bt-page-title d-flex justify-content-between align-items-center">
      <div>
        <h2>设备管理</h2>
        <p class="d-none d-md-inline">管理所有服务设备信息</p>
      </div>
      <button class="btn btn-primary btn-sm" @click="openCreateModal">
        <i class="bi bi-plus-lg me-1"></i>新建设备
      </button>
    </div>

    <div class="bt-filter-bar">
      <div class="row g-2 align-items-end">
        <div class="col-6 col-md-3">
          <input class="form-control form-control-sm" v-model="searchQuery" placeholder="搜索名称/客户/序列号...">
        </div>
        <div class="col-6 col-md-2">
          <select class="form-select form-select-sm" v-model="statusFilter">
            <option value="">全部状态</option>
            <option value="正常">正常</option>
            <option value="维修中">维修中</option>
            <option value="已报废">已报废</option>
          </select>
        </div>
        <div class="col-auto">
          <button class="btn btn-primary btn-sm" @click="loadEquipment(1)"><i class="bi bi-search"></i> 查询</button>
        </div>
      </div>
    </div>

    <div class="card p-2">
      <div class="table-responsive">
        <table class="bt-table">
          <thead>
            <tr>
              <th>设备名称</th>
              <th>客户</th>
              <th>型号</th>
              <th>序列号</th>
              <th>状态</th>
              <th>保修到期</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in equipment" :key="e.id" class="bt-clickable" @click="goDetail(e)">
              <td data-label="名称"><strong>{{ e.name || '-' }}</strong></td>
              <td data-label="客户">{{ e.client || e.client_name || '-' }}</td>
              <td data-label="型号">{{ e.model || '-' }}</td>
              <td data-label="序列号"><code style="font-size:11px">{{ e.serial_no || '-' }}</code></td>
              <td data-label="状态">
                <span class="bt-data-tag" :class="statusClass(e.status)">{{ e.status || '-' }}</span>
              </td>
              <td data-label="保修">{{ e.warranty_expire || '-' }}</td>
              <td data-label="操作" @click.stop>
                <router-link :to="{name: 'EquipmentDetail', params: {id: e.id}}" class="btn btn-sm btn-outline-primary">详情</router-link>
                <button class="btn btn-sm btn-outline-secondary ms-1" @click="openEditModal(e)">编辑</button>
              </td>
            </tr>
            <tr v-if="equipment.length === 0">
              <td colspan="7" class="text-center text-muted py-4">暂无设备</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="modal fade" id="equipmentModal" tabindex="-1" ref="modalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEdit ? '编辑设备' : '新建设备' }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-2">
              <label class="form-label">设备名称 <span class="text-danger">*</span></label>
              <input class="form-control form-control-sm" v-model="form.name" required>
            </div>
            <div class="mb-2">
              <label class="form-label">客户名称</label>
              <ClientSelector v-model="form.client_name" />
            </div>
            <div class="row g-2 mb-2">
              <div class="col-6">
                <label class="form-label">品牌</label>
                <input class="form-control form-control-sm" v-model="form.brand">
              </div>
              <div class="col-6">
                <label class="form-label">型号</label>
                <input class="form-control form-control-sm" v-model="form.model">
              </div>
            </div>
            <div class="row g-2 mb-2">
              <div class="col-6">
                <label class="form-label">类型</label>
                <input class="form-control form-control-sm" v-model="form.type">
              </div>
              <div class="col-6">
                <label class="form-label">序列号</label>
                <input class="form-control form-control-sm" v-model="form.serial_no">
              </div>
            </div>
            <div class="row g-2 mb-2">
              <div class="col-6">
                <label class="form-label">安装位置</label>
                <input class="form-control form-control-sm" v-model="form.location">
              </div>
              <div class="col-6">
                <label class="form-label">状态</label>
                <select class="form-select form-select-sm" v-model="form.status">
                  <option value="正常">正常</option>
                  <option value="维修中">维修中</option>
                  <option value="已报废">已报废</option>
                </select>
              </div>
            </div>
            <div class="row g-2 mb-2">
              <div class="col-6">
                <label class="form-label">保修到期</label>
                <input type="date" class="form-control form-control-sm" v-model="form.warranty_expire">
              </div>
              <div class="col-6">
                <label class="form-label">安装日期</label>
                <input type="date" class="form-control form-control-sm" v-model="form.install_date">
              </div>
            </div>
            <div class="mb-2">
              <label class="form-label">备注</label>
              <textarea class="form-control form-control-sm" rows="2" v-model="form.notes"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-sm btn-primary" @click="submitForm" :disabled="submitting">
              <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
              {{ isEdit ? '保存' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { equipmentApi } from '@/api/equipment'
import { useToast } from '@/composables/useToast'
import ClientSelector from '@/components/selectors/ClientSelector.vue'

const { show: showToast } = useToast()
const router = useRouter()

const equipment = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const page = ref(1)
const modalEl = ref(null)
const isEdit = ref(false)
const editingId = ref(null)

watch(statusFilter, () => { page.value = 1; loadData() })
const submitting = ref(false)
const form = ref(getEmptyForm())

function getEmptyForm() {
  return {
    name: '', client_name: '', brand: '', model: '', type: '',
    serial_no: '', location: '', status: '正常',
    warranty_expire: '', install_date: '', notes: ''
  }
}

onMounted(() => loadEquipment(1))

async function loadEquipment(p) {
  page.value = p
  try {
    const params = { page: p }
    if (searchQuery.value.trim()) params.q = searchQuery.value.trim()
    if (statusFilter.value) params.status = statusFilter.value
    const data = await equipmentApi.list(params)
    equipment.value = data.equipment || data.data || data.records || []
  } catch {
    equipment.value = []
  }
}

function statusClass(status) {
  const map = { '正常': 'success', '维修中': 'warning', '已报废': 'danger' }
  return map[status] || 'primary'
}

function goDetail(e) {
  router.push({ name: 'EquipmentDetail', params: { id: e.id } })
}

function openCreateModal() {
  isEdit.value = false
  editingId.value = null
  form.value = getEmptyForm()
  getModal().show()
}

function openEditModal(item) {
  isEdit.value = true
  editingId.value = item.id
  form.value = {
    name: item.name || '',
    client_name: item.client_name || item.client || '',
    brand: item.brand || '',
    model: item.model || '',
    type: item.type || '',
    serial_no: item.serial_no || '',
    location: item.location || '',
    status: item.status || '正常',
    warranty_expire: item.warranty_expire || '',
    install_date: item.install_date || '',
    notes: item.notes || ''
  }
  getModal().show()
}

let modalInstance = null
function getModal() {
  if (!modalInstance) {
    modalInstance = new window.bootstrap.Modal(modalEl.value)
  }
  return modalInstance
}

async function submitForm() {
  if (!form.value.name.trim()) {
    showToast('请填写设备名称', 'warning')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await equipmentApi.update(editingId.value, form.value)
      showToast('设备更新成功', 'success')
    } else {
      await equipmentApi.create(form.value)
      showToast('设备创建成功', 'success')
    }
    getModal().hide()
    await loadEquipment(page.value)
  } catch (e) {
    showToast(e.response?.data?.error || '操作失败', 'danger')
  } finally {
    submitting.value = false
  }
}
</script>
