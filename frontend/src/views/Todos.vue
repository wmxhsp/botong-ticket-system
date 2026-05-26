<template>
  <div class="page-todos">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div><h2><i class="bi bi-check2-square me-2"></i>待办事项</h2><p>管理待办任务 · {{ totalCount }} 项 <template v-if="stats">(已完成 {{ stats.done || 0 }})</template></p></div>
      <button class="btn btn-primary" @click="showForm = true; editItem = null; resetForm()"><i class="bi bi-plus-lg"></i> 新增待办</button>
    </div>

    <div class="row g-2 mb-2">
      <div class="col-md-3"><div class="stat-card"><div class="stat-value">{{ stats.pending || 0 }}</div><div class="stat-label">待处理</div></div></div>
      <div class="col-md-3"><div class="stat-card"><div class="stat-value">{{ stats.done || 0 }}</div><div class="stat-label">已完成</div></div></div>
      <div class="col-md-3"><div class="stat-card"><div class="stat-value">{{ stats.overdue || 0 }}</div><div class="stat-label">已逾期</div></div></div>
      <div class="col-md-3"><div class="stat-card"><div class="stat-value">{{ stats.today || 0 }}</div><div class="stat-label">今日到期</div></div></div>
    </div>

    <div class="card p-2">
      <div class="d-flex gap-2 mb-3 flex-wrap">
        <button class="btn btn-sm" :class="filter === 'all' ? 'btn-primary' : 'btn-outline-secondary'" @click="filter = 'all'; loadTodos()">全部</button>
        <button class="btn btn-sm" :class="filter === 'pending' ? 'btn-primary' : 'btn-outline-secondary'" @click="filter = 'pending'; loadTodos()">待处理</button>
        <button class="btn btn-sm" :class="filter === 'done' ? 'btn-primary' : 'btn-outline-secondary'" @click="filter = 'done'; loadTodos()">已完成</button>
        <button class="btn btn-sm" :class="filter === 'overdue' ? 'btn-primary' : 'btn-outline-secondary'" @click="filter = 'overdue'; loadTodos()">已逾期</button>
      </div>

      <div v-if="loading" class="text-center py-4"><div class="spinner"></div></div>
      <div v-else-if="todos.length === 0" class="text-center py-5 text-muted"><i class="bi bi-inbox" style="font-size:48px"></i><p class="mt-2">暂无待办事项</p></div>
      <div v-else class="list-group">
        <div v-for="t in todos" :key="t.id" class="list-group-item d-flex align-items-center gap-3">
          <input type="checkbox" class="form-check-input mt-0" :checked="t.done" @change="toggleDone(t)" style="width:20px;height:20px;cursor:pointer">
          <div class="flex-grow-1">
            <div :class="{ 'text-decoration-line-through text-muted': t.done }" class="fw-bold">{{ t.title }}</div>
            <div v-if="t.description" class="small text-muted mt-1">{{ t.description }}</div>
            <div class="d-flex gap-3 mt-1">
              <span class="badge" :class="priorityClass(t.priority)">{{ t.priority || 'M' }}</span>
              <span class="badge bg-info" v-if="t.category">{{ t.category }}</span>
              <span v-if="t.due_date" class="small" :class="t.done ? '' : isOverdue(t.due_date) ? 'text-danger' : 'text-muted'">
                <i class="bi bi-calendar3"></i> {{ t.due_date }}
              </span>
            </div>
          </div>
          <button class="btn btn-sm btn-outline-danger" @click="deleteTodo(t.id)"><i class="bi bi-trash"></i></button>
          <button class="btn btn-sm btn-outline-primary" @click="editItem = t; showForm = true; form = { title: t.title, description: t.description || '', priority: t.priority || 'M', category: t.category || 'work', due_date: t.due_date || '' }"><i class="bi bi-pencil"></i></button>
        </div>
      </div>
    </div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false">
      <div class="modal-content-card">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0">{{ editItem ? '编辑待办' : '新增待办' }}</h5>
          <button class="btn btn-sm btn-outline-secondary" @click="showForm = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <form @submit.prevent="saveTodo">
          <div class="mb-3"><label class="form-label">标题 <span class="text-danger">*</span></label><input v-model="form.title" class="form-control" required></div>
          <div class="mb-3"><label class="form-label">描述</label><textarea v-model="form.description" class="form-control" rows="2"></textarea></div>
          <div class="row g-2">
            <div class="col-md-4"><label class="form-label">优先级</label><select v-model="form.priority" class="form-control"><option value="H">高</option><option value="M">中</option><option value="L">低</option></select></div>
            <div class="col-md-4"><label class="form-label">分类</label><select v-model="form.category" class="form-control"><option value="work">工作</option><option value="personal">个人</option><option value="follow_up">跟进</option><option value="purchase">采购</option></select></div>
            <div class="col-md-4"><label class="form-label">到期日</label><input v-model="form.due_date" type="date" class="form-control"></div>
          </div>
          <div class="d-flex gap-2 justify-content-end mt-3">
            <button type="button" class="btn btn-outline-secondary" @click="showForm = false">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
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
import { ref, onMounted } from 'vue'
import { todoApi } from '@/api/todos'
import { useConfirm } from '@/composables/useConfirm'

const todos = ref([]); const stats = ref({}); const loading = ref(false)
const filter = ref('pending'); const showForm = ref(false); const editItem = ref(null); const saving = ref(false)
const totalCount = ref(0)
const form = ref({ title: '', description: '', priority: 'M', category: 'work', due_date: '' })
const { confirm, visible, message, onConfirm, onCancel } = useConfirm()

onMounted(async () => { await Promise.all([loadTodos(), loadStats()]) })
async function loadTodos() {
  loading.value = true
  try {
    const params = filter.value === 'all' ? {} : { status: filter.value }
    const data = await todoApi.list(params)
    if (Array.isArray(data)) todos.value = data
    else if (data?.todos) todos.value = data.todos
    else if (data?.data) todos.value = data.data
    else todos.value = []
    totalCount.value = todos.value.length
  } catch (e) { console.error(e); todos.value = [] } finally { loading.value = false }
}
async function loadStats() {
  try { stats.value = await todoApi.getStats() || {} }
  catch (e) { console.error(e) }
}
function resetForm() { form.value = { title: '', description: '', priority: 'M', category: 'work', due_date: '' } }
function priorityClass(p) { return { H: 'bg-danger', M: 'bg-warning text-dark', L: 'bg-secondary' }[p] || 'bg-warning text-dark' }
function isOverdue(d) { return d && new Date(d) < new Date(new Date().toDateString()) }

async function toggleDone(t) {
  try { await todoApi.update(t.id, { done: t.done ? 0 : 1 }); t.done = t.done ? 0 : 1; if (filter.value === 'pending' && t.done) await loadTodos() }
  catch (e) { console.error(e) }
}
async function saveTodo() {
  saving.value = true
  try {
    editItem.value ? await todoApi.update(editItem.value.id, form.value) : await todoApi.create(form.value)
    showForm.value = false; await Promise.all([loadTodos(), loadStats()])
  } catch (e) { console.error(e) } finally { saving.value = false }
}
async function deleteTodo(id) {
  if (!(await confirm('确定删除？'))) return
  try { await todoApi.delete(id); await Promise.all([loadTodos(), loadStats()]) }
  catch (e) { console.error(e) }
}
</script>