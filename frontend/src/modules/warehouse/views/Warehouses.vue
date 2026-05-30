<template>
  <div class="page-warehouses">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div><h2><i class="bi bi-building me-2"></i>仓库管理</h2><p>管理仓库信息 · {{ warehouses.length }} 个仓库</p></div>
      <button class="btn btn-primary" @click="showForm = true; editItem = null; resetForm()"><i class="bi bi-plus-lg"></i> 新增仓库</button>
    </div>

    <div class="card p-2">
      <LoadingSkeleton v-if="loading" type="table" :count="6" />
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th>仓库名称</th><th>地址/位置</th><th>负责人</th><th>排序</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="w in warehouses" :key="w.id">
              <td class="fw-bold">{{ w.name }}</td>
              <td class="text-muted">{{ w.address || '-' }}</td>
              <td>{{ w.manager || '-' }}</td>
              <td>{{ w.sort_order || 99 }}</td>
              <td><span class="badge" :class="w.is_active ? 'bg-success' : 'bg-secondary'">{{ w.is_active ? '启用' : '停用' }}</span></td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-1" @click="editWarehouse(w)"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteWarehouse(w.id)"><i class="bi bi-trash"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <BtModal v-model:visible="showForm" :title="editItem ? '编辑仓库' : '新增仓库'" icon="bi bi-building" max-width="500px">
      <template #body>
        <form @submit.prevent="saveWarehouse">
          <div class="mb-3">
            <label class="form-label">仓库名称 <span class="text-danger">*</span></label>
            <input v-model="form.name" class="form-control" required>
          </div>
          <div class="mb-3">
            <label class="form-label">地址</label>
            <input v-model="form.address" class="form-control">
          </div>
          <div class="mb-3">
            <label class="form-label">负责人</label>
            <input v-model="form.manager" class="form-control">
          </div>
          <div class="mb-3">
            <label class="form-label">排序</label>
            <input v-model.number="form.sort_order" type="number" class="form-control">
          </div>
        </form>
      </template>
      <template #footer>
        <button type="button" class="btn btn-outline-secondary btn-sm" @click="showForm = false">取消</button>
        <button type="submit" class="btn btn-primary btn-sm" @click="saveWarehouse" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </template>
    </BtModal>
  </div>
</template>

<script setup>
defineOptions({ name: 'Warehouses' })

import { ref, onMounted } from 'vue'
import { warehouseApi } from '@/api/warehouses'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import BtModal from '@/components/common/BtModal.vue'

const { show: showToast } = useToast()
const { confirm } = useConfirm()

const warehouses = ref([])
const loading = ref(false)
const showForm = ref(false)
const editItem = ref(null)
const saving = ref(false)
const form = ref({ name: '', address: '', manager: '', sort_order: 99 })

onMounted(() => loadWarehouses())

async function loadWarehouses() {
  loading.value = true
  try {
    const data = await warehouseApi.list()
    warehouses.value = Array.isArray(data) ? data : data?.warehouses || data?.data || []
  } catch (e) {
    showToast('加载失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = { name: '', address: '', manager: '', sort_order: 99 }
}

function editWarehouse(w) {
  editItem.value = w
  form.value = { name: w.name, address: w.address || '', manager: w.manager || '', sort_order: w.sort_order || 99 }
  showForm.value = true
}

async function saveWarehouse() {
  if (!form.value.name) return
  saving.value = true
  try {
    editItem.value ? await warehouseApi.update(editItem.value.id, form.value) : await warehouseApi.create(form.value)
    showForm.value = false
    showToast('保存成功', 'success')
    await loadWarehouses()
  } catch (e) {
    showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    saving.value = false
  }
}

async function deleteWarehouse(id) {
  if (!(await confirm('确定删除该仓库？'))) return
  try {
    await warehouseApi.delete(id)
    showToast('删除成功', 'success')
    await loadWarehouses()
  } catch (e) {
    showToast('删除失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}
</script>
