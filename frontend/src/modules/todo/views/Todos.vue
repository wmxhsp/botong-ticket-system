<template>
  <div class="page-todos">
    <div class="bt-page-title d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div><h2><i class="bi bi-check2-square me-2"></i>待办事项</h2><p>管理待办任务 · {{ totalCount }} 项 <template v-if="stats">(已完成 {{ stats.done || 0 }})</template></p></div>
      <div class="d-flex gap-2">
        <button class="btn btn-sm btn-outline-danger" @click="cleanupDone" v-if="stats.done > 0">
          <i class="bi bi-trash me-1"></i>清理已完成 ({{ stats.done }})
        </button>
        <button class="btn btn-primary" @click="showForm = true; editItem = null; resetForm()"><i class="bi bi-plus-lg"></i> 新增待办</button>
      </div>
    </div>

    <div class="row g-2 mb-2">
      <div class="col-md-3"><div class="stat-card clickable" @click="quickFilter = 'today'; loadTodos()"><div class="stat-value">{{ stats.today || 0 }}</div><div class="stat-label">今日到期</div></div></div>
      <div class="col-md-3"><div class="stat-card clickable" @click="quickFilter = 'overdue'; loadTodos()"><div class="stat-value text-danger">{{ stats.overdue || 0 }}</div><div class="stat-label">已逾期</div></div></div>
      <div class="col-md-3"><div class="stat-card clickable" @click="quickFilter = 'pending'; loadTodos()"><div class="stat-value">{{ stats.pending || 0 }}</div><div class="stat-label">待处理</div></div></div>
      <div class="col-md-3"><div class="stat-card clickable" @click="quickFilter = 'done'; loadTodos()"><div class="stat-value text-success">{{ stats.done || 0 }}</div><div class="stat-label">已完成</div></div></div>
    </div>

    <div class="card p-2">
      <div class="d-flex gap-2 mb-3 flex-wrap">
        <button class="btn btn-sm" :class="filter === 'all' && !quickFilter ? 'btn-primary' : 'btn-outline-secondary'" @click="filter = 'all'; quickFilter = ''; loadTodos()">全部</button>
        <button class="btn btn-sm" :class="quickFilter === 'today' ? 'btn-primary' : 'btn-outline-secondary'" @click="quickFilter = 'today'; loadTodos()">今日</button>
        <button class="btn btn-sm" :class="quickFilter === 'overdue' ? 'btn-primary' : 'btn-outline-secondary'" @click="quickFilter = 'overdue'; loadTodos()">逾期</button>
        <button class="btn btn-sm" :class="quickFilter === 'upcoming' ? 'btn-primary' : 'btn-outline-secondary'" @click="quickFilter = 'upcoming'; loadTodos()">即将到期</button>
        <button class="btn btn-sm" :class="filter === 'pending' && !quickFilter ? 'btn-primary' : 'btn-outline-secondary'" @click="filter = 'pending'; quickFilter = ''; loadTodos()">待处理</button>
        <button class="btn btn-sm" :class="filter === 'done' && !quickFilter ? 'btn-primary' : 'btn-outline-secondary'" @click="filter = 'done'; quickFilter = ''; loadTodos()">已完成</button>
        <select v-model="sourceFilter" class="form-select form-select-sm" style="max-width:130px" @change="loadTodos">
          <option value="">全部来源</option>
          <option value="manual">手动创建</option>
          <option value="ticket">工单</option>
          <option value="system">系统</option>
        </select>
      </div>

      <div v-if="loading" class="text-center py-4"><div class="spinner"></div></div>
      <div v-else-if="todos.length === 0" class="text-center py-5 text-muted"><i class="bi bi-inbox" style="font-size:48px"></i><p class="mt-2">{{ emptyMessage }}</p></div>
      <div v-else class="list-group">
        <div v-for="t in todos" :key="t.id" class="list-group-item d-flex align-items-center gap-3">
          <input type="checkbox" class="form-check-input mt-0" :checked="t.done" @change="toggleDone(t)" style="width:20px;height:20px;cursor:pointer">
          <div class="flex-grow-1">
            <div :class="{ 'text-decoration-line-through text-muted': t.done }" class="fw-bold">{{ t.title }}</div>
            <div v-if="t.description" class="small text-muted mt-1">{{ t.description }}</div>
            <div class="d-flex gap-3 mt-1 flex-wrap">
              <span class="badge" :class="priorityClass(t.priority)">{{ priorityLabel(t.priority) }}</span>
              <span class="badge bg-info" v-if="t.category">{{ categoryLabel(t.category) }}</span>
              <span class="badge bg-secondary" v-if="t.source">{{ sourceLabel(t.source) }}</span>
              <span v-if="t.ticket_id" class="small">
                <router-link :to="'/tickets/' + t.ticket_id" class="text-decoration-none">
                  <i class="bi bi-link-45deg"></i>工单
                </router-link>
              </span>
              <span v-if="t.due_date" class="small" :class="t.done ? '' : isOverdue(t.due_date) ? 'text-danger fw-bold' : 'text-muted'">
                <i class="bi bi-calendar3"></i> {{ t.due_date }}
              </span>
            </div>
            <!-- 子任务 -->
            <div v-if="t.subtask_count > 0 || expandedTodo === t.id" class="mt-2 ps-3 border-start">
              <div class="d-flex align-items-center gap-2 mb-1">
                <button class="btn btn-xs btn-outline-secondary" @click="toggleSubtasks(t)">
                  <i class="bi" :class="expandedTodo === t.id ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
                  子任务 ({{ t.subtask_done || 0 }}/{{ t.subtask_count }})
                </button>
              </div>
              <div v-if="expandedTodo === t.id">
                <div v-if="subtasksLoading" class="small text-muted py-1">加载中...</div>
                <div v-else>
                  <div v-for="sub in subtasks" :key="sub.id" class="d-flex align-items-center gap-2 py-1">
                    <input type="checkbox" class="form-check-input" :checked="sub.done" @change="toggleSubtask(sub)" style="width:16px;height:16px;cursor:pointer">
                    <span :class="{ 'text-decoration-line-through text-muted': sub.done }" class="small">{{ sub.title }}</span>
                  </div>
                  <div class="d-flex gap-1 mt-1">
                    <input v-model="newSubtask" class="form-control form-control-sm" style="max-width:200px" placeholder="添加子任务" @keyup.enter="addSubtask(t.id)">
                    <button class="btn btn-sm btn-outline-primary" @click="addSubtask(t.id)" :disabled="!newSubtask"><i class="bi bi-plus"></i></button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="d-flex gap-1">
            <button class="btn btn-sm btn-outline-primary" @click="editItem = t; showForm = true; form = { title: t.title, description: t.description || '', priority: t.priority || 'M', category: t.category || 'work', due_date: t.due_date || '' }"><i class="bi bi-pencil"></i></button>
            <button class="btn btn-sm btn-outline-danger" @click="deleteTodo(t.id)"><i class="bi bi-trash"></i></button>
          </div>
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
import { ref, computed, onMounted } from 'vue'
import { todoApi } from '@/api/todos'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'

const { show: showToast } = useToast()
const todos = ref([]); const stats = ref({}); const loading = ref(false)
const filter = ref('pending'); const quickFilter = ref(''); const sourceFilter = ref('')
const showForm = ref(false); const editItem = ref(null); const saving = ref(false)
const totalCount = ref(0)
const form = ref({ title: '', description: '', priority: 'M', category: 'work', due_date: '' })
const { confirm, visible, message, onConfirm, onCancel } = useConfirm()

// 子任务
const expandedTodo = ref(null)
const subtasks = ref([])
const subtasksLoading = ref(false)
const newSubtask = ref('')

const emptyMessage = computed(() => {
  if (quickFilter.value === 'today') return '今日无到期待办 🎉'
  if (quickFilter.value === 'overdue') return '无逾期待办 🎉'
  if (quickFilter.value === 'upcoming') return '无即将到期'
  return '暂无待办事项'
})

onMounted(async () => { await Promise.all([loadTodos(), loadStats()]) })

async function loadTodos() {
  loading.value = true
  try {
    let data
    if (quickFilter.value === 'today') {
      data = await todoApi.getToday()
    } else if (quickFilter.value === 'overdue') {
      data = await todoApi.getOverdue()
    } else if (quickFilter.value === 'upcoming') {
      data = await todoApi.getUpcoming()
    } else if (sourceFilter.value) {
      data = await todoApi.getBySource({ source: sourceFilter.value })
    } else {
      const params = filter.value === 'all' ? {} : { status: filter.value }
      data = await todoApi.list(params)
    }
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
function priorityLabel(p) { return { H: '高', M: '中', L: '低' }[p] || '中' }
function categoryLabel(c) { return { work: '工作', personal: '个人', follow_up: '跟进', purchase: '采购' }[c] || c }
function sourceLabel(s) { return { manual: '手动', ticket: '工单', system: '系统' }[s] || s }
function isOverdue(d) { return d && new Date(d) < new Date(new Date().toDateString()) }

async function toggleDone(t) {
  try {
    await todoApi.toggle(t.id)
    t.done = !t.done
    await loadStats()
    if (filter.value === 'pending' && t.done) await loadTodos()
  } catch (e) { console.error(e) }
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

async function cleanupDone() {
  if (!(await confirm('确认清理所有已完成的待办？'))) return
  try {
    await todoApi.cleanup()
    showToast('已完成待办已清理', 'success')
    await Promise.all([loadTodos(), loadStats()])
  } catch (e) { showToast('清理失败', 'danger') }
}

// ── 子任务 ──
async function toggleSubtasks(t) {
  if (expandedTodo.value === t.id) {
    expandedTodo.value = null
    return
  }
  expandedTodo.value = t.id
  subtasksLoading.value = true
  try {
    const data = await todoApi.listSubtasks(t.id)
    subtasks.value = Array.isArray(data) ? data : data?.subtasks || []
  } catch (e) { subtasks.value = [] }
  finally { subtasksLoading.value = false }
}

async function toggleSubtask(sub) {
  try {
    await todoApi.toggleSubtask(sub.id)
    sub.done = !sub.done
  } catch (e) { console.error(e) }
}

async function addSubtask(parentId) {
  if (!newSubtask.value.trim()) return
  try {
    await todoApi.createSubtask(parentId, { title: newSubtask.value })
    newSubtask.value = ''
    // 重新加载子任务
    const data = await todoApi.listSubtasks(parentId)
    subtasks.value = Array.isArray(data) ? data : data?.subtasks || []
  } catch (e) { showToast('添加子任务失败', 'danger') }
}
</script>

<style scoped>
.clickable { cursor: pointer; transition: transform 0.1s; }
.clickable:hover { transform: scale(1.02); }
.btn-xs { padding: 1px 6px; font-size: 11px; }
</style>
