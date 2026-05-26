<template>
  <div class="page-service-fees">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div><h2><i class="bi bi-currency-yen me-2"></i>服务规则</h2><p>服务项目和计价规则管理 · {{ fees.length }} 项</p></div>
      <button class="btn btn-primary" @click="showForm = true; editItem = null; resetForm()"><i class="bi bi-plus-lg"></i> 新增规则</button>
    </div>

    <div class="row g-2 mb-2">
      <div class="col-md-4"><div class="stat-card"><div class="stat-value">{{ totalItems }}</div><div class="stat-label">服务规则</div></div></div>
      <div class="col-md-4"><div class="stat-card"><div class="stat-value">{{ activeCount }}</div><div class="stat-label">已启用</div></div></div>
      <div class="col-md-4"><div class="stat-card"><div class="stat-value">{{ avgPrice }}</div><div class="stat-label">均价(元)</div></div></div>
    </div>

    <div class="card p-2">
      <div v-if="loading" class="text-center py-4"><div class="spinner"></div></div>
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>服务名称</th><th>计费类型</th><th>单价(元)</th><th>成本价(元)</th><th>单位</th><th>状态</th><th>使用次数</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="f in fees" :key="f.id">
              <td class="fw-bold">{{ f.name }}</td>
              <td><span class="badge" :class="getTypeClass(f.fee_type)">{{ getTypeName(f.fee_type) }}</span></td>
              <td>¥{{ Number(f.unit_price || 0).toFixed(2) }}</td>
              <td>¥{{ Number(f.cost_price || 0).toFixed(2) }}</td>
              <td>{{ getTypeUnit(f.fee_type) }}</td>
              <td><span class="badge" :class="f.active ? 'bg-success' : 'bg-secondary'">{{ f.active ? '启用' : '禁用' }}</span></td>
              <td>{{ f.usage_count || 0 }}</td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-1" @click="editFee(f)"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteFee(f.id)"><i class="bi bi-trash"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false">
      <div class="modal-content-card" style="max-width:500px">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0">{{ editItem ? '编辑服务规则' : '新增服务规则' }}</h5>
          <button class="btn btn-sm btn-outline-secondary" @click="showForm = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <form @submit.prevent="saveFee">
          <div class="row g-2">
            <div class="col-md-6"><label class="form-label">服务名称 <span class="text-danger">*</span></label><input v-model="form.name" class="form-control" required placeholder="请输入服务名称"></div>
            <div class="col-md-6"><label class="form-label">计费类型</label>
              <select v-model="form.fee_type" class="form-control">
                <option value="">请选择...</option>
                <option v-for="t in feeTypeOptions" :key="t.key" :value="t.key">{{ t.name }} ({{ t.unit }})</option>
              </select>
            </div>
            <div class="col-md-4"><label class="form-label">单价 <span class="text-danger">*</span></label><input v-model.number="form.unit_price" type="number" step="0.01" class="form-control" required placeholder="对外收费价格"></div>
            <div class="col-md-4"><label class="form-label">成本价</label><input v-model.number="form.cost_price" type="number" step="0.01" class="form-control" placeholder="内部成本价格"></div>
            <div class="col-md-4"><label class="form-label">状态</label><select v-model="form.active" class="form-control"><option :value="true">启用</option><option :value="false">禁用</option></select></div>
            <div class="col-12"><label class="form-label">描述</label><textarea v-model="form.description" class="form-control" rows="2" placeholder="服务描述说明"></textarea></div>
          </div>
          <div class="d-flex gap-2 justify-content-end mt-3">
            <button type="button" class="btn btn-outline-secondary" @click="showForm = false">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="saving || !form.name || form.unit_price === null">{{ saving ? '保存中...' : '保存' }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="visible" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,.5);z-index:1060">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-body"><p>{{ message }}</p></div>
          <div class="modal-footer">
            <button class="btn btn-secondary btn-sm" @click="onCancel">取消</button>
            <button class="btn btn-danger btn-sm" @click="onConfirm">确定</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { serviceFeeApi } from '@/api/service-fees'
import { useConfirm } from '@/composables/useConfirm'

const fees = ref([]); const serviceTypes = ref([]); const loading = ref(false)
const showForm = ref(false); const editItem = ref(null); const saving = ref(false)
const form = ref({ name: '', fee_type: 'hourly', unit_price: null, cost_price: 0, description: '', active: true })
const { confirm, visible, message, onConfirm, onCancel } = useConfirm()

const feeTypeOptions = [
  { key: 'hourly', name: '按小时', unit: '元/小时' },
  { key: 'monthly', name: '按月订阅', unit: '元/月' },
  { key: 'yearly', name: '按年订阅', unit: '元/年' },
  { key: 'fixed', name: '按次收费', unit: '元/次' },
  { key: 'free', name: '保修免费', unit: '免费' },
]

const totalItems = computed(() => fees.value.length)
const activeCount = computed(() => fees.value.filter(f => f.active).length)
const avgPrice = computed(() => fees.value.length ? (fees.value.reduce((s, f) => s + Number(f.unit_price || 0), 0) / fees.value.length).toFixed(2) : '0.00')

function getTypeName(type) {
  const found = feeTypeOptions.find(t => t.key === type)
  return found ? found.name : type || '-'
}

function getTypeUnit(type) {
  const found = feeTypeOptions.find(t => t.key === type)
  return found ? found.unit : '次'
}

function getTypeClass(type) {
  const classes = {
    hourly: 'bg-primary',
    monthly: 'bg-info',
    yearly: 'bg-success',
    fixed: 'bg-warning',
    free: 'bg-secondary',
  }
  return classes[type] || 'bg-secondary'
}

onMounted(async () => { await loadFees() })
async function loadFees() {
  loading.value = true
  try { const data = await serviceFeeApi.list(); fees.value = Array.isArray(data) ? data : data?.fees || data?.data || [] }
  catch (e) { console.error(e) } finally { loading.value = false }
}
function resetForm() { form.value = { name: '', fee_type: 'hourly', unit_price: null, cost_price: 0, description: '', active: true } }
function editFee(f) { 
  editItem.value = f; 
  form.value = { 
    ...f, 
    active: Boolean(f.active !== false && f.active !== 0),
    unit_price: Number(f.unit_price || 0),
    cost_price: Number(f.cost_price || 0),
  }; 
  showForm.value = true 
}
async function saveFee() {
  saving.value = true
  try { 
    editItem.value ? await serviceFeeApi.update(editItem.value.id, form.value) : await serviceFeeApi.create(form.value)
    showForm.value = false
    await loadFees()
  } catch (e) { console.error(e) } finally { saving.value = false }
}
async function deleteFee(id) { 
  if (!(await confirm('确定删除该服务规则？'))) return
  try { await serviceFeeApi.delete(id); await loadFees() } 
  catch (e) { console.error(e) } 
}
</script>