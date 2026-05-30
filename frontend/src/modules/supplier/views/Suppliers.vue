<template>
  <div class="page-suppliers">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div><h2><i class="bi bi-truck me-2"></i>供应商管理</h2><p>管理供应商信息 · {{ suppliers.length }} 家</p></div>
      <button class="btn btn-primary" @click="showForm = true; editItem = null; resetForm()"><i class="bi bi-plus-lg"></i> 新增供应商</button>
    </div>

    <div class="card p-2">
      <LoadingSkeleton v-if="loading" type="table" :count="6" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>名称</th><th>联系人</th><th>电话</th><th>银行</th><th>账期</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="s in suppliers" :key="s.id">
              <td class="fw-bold">{{ s.name }}</td>
              <td>{{ s.contact || '-' }}</td>
              <td>{{ s.phone || '-' }}</td>
              <td class="small text-muted">{{ s.bank_name || '-' }}</td>
              <td>{{ s.payment_terms || 30 }} 天</td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-1" @click="editSupplier(s)"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteSupplier(s.id)"><i class="bi bi-trash"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <BtModal v-model:visible="showForm" :title="editItem ? '编辑供应商' : '新增供应商'" icon="bi bi-truck" max-width="500px">
      <template #body>
        <form @submit.prevent="saveSupplier">
          <div class="row g-2">
            <div class="col-md-6">
              <label class="form-label">名称 <span class="text-danger">*</span></label>
              <input v-model="form.name" class="form-control" required>
            </div>
            <div class="col-md-6">
              <label class="form-label">联系人</label>
              <input v-model="form.contact" class="form-control">
            </div>
            <div class="col-md-6">
              <label class="form-label">电话</label>
              <input v-model="form.phone" class="form-control">
            </div>
            <div class="col-md-6">
              <label class="form-label">开户行</label>
              <input v-model="form.bank_name" class="form-control">
            </div>
            <div class="col-md-6">
              <label class="form-label">银行账号</label>
              <input v-model="form.bank_account" class="form-control">
            </div>
            <div class="col-md-6">
              <label class="form-label">账期（天）</label>
              <input v-model.number="form.payment_terms" type="number" class="form-control">
            </div>
          </div>
        </form>
      </template>
      <template #footer>
        <button type="button" class="btn btn-outline-secondary btn-sm" @click="showForm = false">取消</button>
        <button type="submit" class="btn btn-primary btn-sm" @click="saveSupplier" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </template>
    </BtModal>
  </div>
</template>

<script setup>
defineOptions({ name: 'Suppliers' })

import { ref, onMounted } from 'vue'
import { supplierApi } from '@/api/suppliers'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import BtModal from '@/components/common/BtModal.vue'

const { show: showToast } = useToast()
const { confirm } = useConfirm()

const suppliers = ref([])
const loading = ref(false)
const showForm = ref(false)
const editItem = ref(null)
const saving = ref(false)
const form = ref({ name: '', contact: '', phone: '', bank_name: '', bank_account: '', payment_terms: 30 })

onMounted(() => loadSuppliers())

async function loadSuppliers() {
  loading.value = true
  try {
    const data = await supplierApi.list()
    suppliers.value = Array.isArray(data) ? data : data?.suppliers || data?.data || []
  } catch (e) {
    showToast('加载失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = { name: '', contact: '', phone: '', bank_name: '', bank_account: '', payment_terms: 30 }
}

function editSupplier(s) {
  editItem.value = s
  form.value = { ...s }
  showForm.value = true
}

async function saveSupplier() {
  if (!form.value.name) return
  saving.value = true
  try {
    editItem.value ? await supplierApi.update(editItem.value.id, form.value) : await supplierApi.create(form.value)
    showForm.value = false
    showToast('保存成功', 'success')
    await loadSuppliers()
  } catch (e) {
    showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    saving.value = false
  }
}

async function deleteSupplier(id) {
  if (!(await confirm('确定删除该供应商？'))) return
  try {
    await supplierApi.delete(id)
    showToast('删除成功', 'success')
    await loadSuppliers()
  } catch (e) {
    showToast('删除失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}
</script>
