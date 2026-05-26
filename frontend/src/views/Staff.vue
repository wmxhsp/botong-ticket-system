<template>
  <div class="page-staff">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div><h2><i class="bi bi-people-fill me-2"></i>工程师管理</h2><p>技术人员管理 · {{ staff.length }} 人</p></div>
      <button class="btn btn-primary" @click="showForm = true; editItem = null; resetForm()"><i class="bi bi-plus-lg"></i> 新增工程师</button>
    </div>

    <div class="row g-2 mb-2">
      <div class="col-md-4"><div class="card p-2 text-center"><div class="stat-value">{{ staff.length }}</div><div class="stat-label">工程师总数</div></div></div>
      <div class="col-md-4"><div class="card p-2 text-center"><div class="stat-value">{{ activeCount }}</div><div class="stat-label">在职</div></div></div>
      <div class="col-md-4"><div class="card p-2 text-center"><div class="stat-value">{{ avgBillRate }}</div><div class="stat-label">平均计费单价</div></div></div>
    </div>

    <div class="card p-2">
      <LoadingSkeleton v-if="loading" type="table" :count="6" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>姓名</th><th>计费模式</th><th>计费单价(元)</th><th>成本单价(元)</th><th>状态</th><th>工单数</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="s in staff" :key="s.id">
              <td class="fw-bold">{{ s.name }}</td>
              <td><span class="badge" :class="billingBadge(s.billing_type)">{{ billingLabel(s.billing_type) }}</span></td>
              <td>¥{{ formatRate(s, 'bill') }}</td>
              <td>¥{{ formatRate(s, 'cost') }}</td>
              <td><span class="badge" :class="s.status === 'active' ? 'bg-success' : 'bg-secondary'">{{ s.status === 'active' ? '在职' : '离职' }}</span></td>
              <td>{{ s.ticket_count || s.tickets || 0 }}</td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-1" @click="editStaff(s)"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteStaff(s.id)"><i class="bi bi-trash"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <BtModal v-model:visible="showForm" :title="editItem ? '编辑工程师' : '新增工程师'" icon="bi bi-person-plus" max-width="500px">
      <template #body>
        <form @submit.prevent="saveStaff">
          <div class="row g-2">
            <div class="col-md-6">
              <label class="form-label">姓名 <span class="text-danger">*</span></label>
              <input v-model="form.name" class="form-control" required placeholder="请输入姓名">
            </div>
            <div class="col-md-6">
              <label class="form-label">计费模式 <span class="text-danger">*</span></label>
              <select v-model="form.billing_type" class="form-control" required>
                <option value="hourly">时薪（按小时计费）</option>
                <option value="daily">天薪（按天计费）</option>
                <option value="package">包工（固定金额）</option>
              </select>
            </div>
            <!-- 时薪模式 -->
            <div class="col-md-6" v-if="form.billing_type === 'hourly'">
              <label class="form-label">计费时薪(元) <span class="text-danger">*</span></label>
              <input v-model.number="form.bill_rate" type="number" step="1" class="form-control" required placeholder="对外收费时薪">
            </div>
            <div class="col-md-6" v-if="form.billing_type === 'hourly'">
              <label class="form-label">成本时薪(元)</label>
              <input v-model.number="form.cost_rate" type="number" step="1" class="form-control" placeholder="内部成本时薪">
            </div>
            <!-- 天薪模式 -->
            <div class="col-md-6" v-if="form.billing_type === 'daily'">
              <label class="form-label">计费日薪(元) <span class="text-danger">*</span></label>
              <input v-model.number="form.daily_rate" type="number" step="1" class="form-control" required placeholder="对外收费日薪">
            </div>
            <div class="col-md-6" v-if="form.billing_type === 'daily'">
              <label class="form-label">成本日薪(元)</label>
              <input v-model.number="form.daily_cost_rate" type="number" step="1" class="form-control" placeholder="内部成本日薪">
            </div>
            <!-- 包工模式 -->
            <div class="col-md-6" v-if="form.billing_type === 'package'">
              <label class="form-label">包工收费(元) <span class="text-danger">*</span></label>
              <input v-model.number="form.package_rate" type="number" step="1" class="form-control" required placeholder="对外包工总价">
            </div>
            <div class="col-md-6" v-if="form.billing_type === 'package'">
              <label class="form-label">包工成本(元)</label>
              <input v-model.number="form.package_cost" type="number" step="1" class="form-control" placeholder="内部包工成本">
            </div>
            <div class="col-md-6">
              <label class="form-label">电话</label>
              <input v-model="form.phone" class="form-control" placeholder="联系电话">
            </div>
            <div class="col-md-6">
              <label class="form-label">技能标签</label>
              <input v-model="form.skills" class="form-control" placeholder="用逗号分隔">
            </div>
            <div class="col-md-6">
              <label class="form-label">状态</label>
              <select v-model="form.status" class="form-control">
                <option value="active">在职</option>
                <option value="inactive">离职</option>
              </select>
            </div>
            <div class="col-12">
              <label class="form-label">备注</label>
              <textarea v-model="form.notes" class="form-control" rows="2" placeholder="备注信息"></textarea>
            </div>
          </div>
        </form>
      </template>
      <template #footer>
        <button type="button" class="btn btn-outline-secondary btn-sm" @click="showForm = false">取消</button>
        <button type="submit" class="btn btn-primary btn-sm" @click="saveStaff" :disabled="saving || !form.name || !isValidForm">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </template>
    </BtModal>
  </div>
</template>

<script setup>
defineOptions({ name: 'Staff' })

import { ref, computed, onMounted } from 'vue'
import { staffApi } from '@/api/staff'
import { useApi } from '@/composables/useApi'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import BtModal from '@/components/common/BtModal.vue'

const { show: showToast } = useToast()
const { confirm } = useConfirm()

const { data: staffData, loading, execute: loadStaff } = useApi(staffApi.list)
const staff = computed(() => Array.isArray(staffData.value) ? staffData.value : staffData.value?.technicians || staffData.value?.data || [])
const showForm = ref(false)
const editItem = ref(null)
const saving = ref(false)
const form = ref({ name: '', phone: '', billing_type: 'hourly', bill_rate: 150, cost_rate: 50, daily_rate: 800, daily_cost_rate: 400, package_rate: 3000, package_cost: 2000, skills: '', status: 'active', notes: '' })

const activeCount = computed(() => staff.value.filter(s => s.status === 'active').length)
const avgBillRate = computed(() => {
  const active = staff.value.filter(s => s.status === 'active')
  return active.length ? (active.reduce((sum, s) => sum + getEffectiveRate(s, 'bill'), 0) / active.length).toFixed(0) : '0'
})

const isValidForm = computed(() => {
  if (!form.value.name) return false
  if (form.value.billing_type === 'hourly') return !!form.value.bill_rate
  if (form.value.billing_type === 'daily') return !!form.value.daily_rate
  if (form.value.billing_type === 'package') return !!form.value.package_rate
  return false
})

function getEffectiveRate(s, type) {
  const bt = s.billing_type || 'hourly'
  if (bt === 'hourly') return Number(type === 'bill' ? (s.bill_rate || s.hourly_rate || 0) : (s.cost_rate || 0))
  if (bt === 'daily') return Number(type === 'bill' ? (s.daily_rate || 0) : (s.daily_cost_rate || 0))
  if (bt === 'package') return Number(type === 'bill' ? (s.package_rate || 0) : (s.package_cost || 0))
  return 0
}

function formatRate(s, type) {
  return getEffectiveRate(s, type).toFixed(0)
}

function billingLabel(bt) {
  const labels = { hourly: '时薪', daily: '天薪', package: '包工' }
  return labels[bt] || '时薪'
}

function billingBadge(bt) {
  const badges = { hourly: 'bg-info', daily: 'bg-warning text-dark', package: 'bg-primary' }
  return badges[bt] || 'bg-info'
}

onMounted(() => loadStaff())

function resetForm() {
  form.value = { name: '', phone: '', billing_type: 'hourly', bill_rate: 150, cost_rate: 50, daily_rate: 800, daily_cost_rate: 400, package_rate: 3000, package_cost: 2000, skills: '', status: 'active', notes: '' }
}

function editStaff(s) {
  editItem.value = s
  form.value = {
    name: s.name,
    phone: s.phone || '',
    billing_type: s.billing_type || 'hourly',
    bill_rate: Number(s.bill_rate || s.hourly_rate || 150),
    cost_rate: Number(s.cost_rate || 50),
    daily_rate: Number(s.daily_rate || 800),
    daily_cost_rate: Number(s.daily_cost_rate || 400),
    package_rate: Number(s.package_rate || 3000),
    package_cost: Number(s.package_cost || 2000),
    skills: s.skills || '',
    status: s.status || 'active',
    notes: s.notes || ''
  }
  showForm.value = true
}

async function saveStaff() {
  if (!form.value.name || !form.value.bill_rate) return
  saving.value = true
  try {
    editItem.value ? await staffApi.update(editItem.value.id, form.value) : await staffApi.create(form.value)
    showForm.value = false
    showToast('保存成功', 'success')
    await loadStaff()
  } catch (e) {
    showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    saving.value = false
  }
}

async function deleteStaff(id) {
  if (!(await confirm('确定删除该工程师？'))) return
  try {
    await staffApi.delete(id)
    showToast('删除成功', 'success')
    await loadStaff()
  } catch (e) {
    showToast('删除失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}
</script>
