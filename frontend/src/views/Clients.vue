<template>
  <div>
    <div class="bt-page-title d-flex justify-content-between align-items-center">
      <div>
        <h2>客户管理</h2>
        <p class="d-none d-md-inline">管理所有客户信息</p>
      </div>
      <button class="btn btn-sm btn-primary" @click="showForm = true">
        <i class="bi bi-plus-lg"></i> 新建
      </button>
    </div>

    <!-- 新建表单 -->
    <div v-if="showForm" class="card p-2 mb-3">
      <h5 class="mb-3"><i class="bi bi-person-plus me-2"></i>新建客户</h5>
      <div class="row g-2">
        <div class="col-md-4">
          <input class="form-control form-control-sm" v-model="formName" placeholder="客户名称 *" ref="nameInput">
        </div>
        <div class="col-md-3">
          <input class="form-control form-control-sm" v-model="formContact" placeholder="联系人">
        </div>
        <div class="col-md-3">
          <input class="form-control form-control-sm" v-model="formPhone" placeholder="电话">
        </div>
        <div class="col-md-2 d-flex gap-1">
          <button class="btn btn-sm btn-primary flex-fill" @click="createClient" :disabled="saving">
            {{ saving ? '创建中...' : '保存' }}
          </button>
          <button class="btn btn-sm btn-outline-secondary" @click="showForm = false">取消</button>
        </div>
      </div>
    </div>

    <!-- 搜索 -->
    <div class="bt-filter-bar">
      <div class="row g-2">
        <div class="col-md-4">
          <input class="form-control form-control-sm" v-model="q" placeholder="搜索客户名称/电话"
                 @keyup.enter="load()">
        </div>
        <div class="col-auto">
          <button class="btn btn-primary btn-sm" @click="load"><i class="bi bi-search"></i> 查询</button>
        </div>
        <div class="col-auto">
          <button class="btn btn-outline-secondary btn-sm" @click="load"><i class="bi bi-arrow-repeat"></i> 刷新</button>
        </div>
      </div>
    </div>

    <!-- 列表 -->
    <div class="card p-2">
      <div class="d-flex justify-content-between mb-2">
        <h5 class="mb-0"><i class="bi bi-people me-2"></i>客户列表</h5>
        <span class="text-muted small">共 {{ items.length }} 位</span>
      </div>

      <!-- 加载 -->
      <div v-if="loading" class="row g-2">
        <div class="col-md-6 col-lg-4" v-for="i in 6" :key="i">
          <div class="card p-2"><div class="bt-skeleton" style="height:80px;border-radius:8px"></div></div>
        </div>
      </div>

      <!-- 卡片 -->
      <div v-else-if="items.length > 0" class="row g-2">
        <div v-for="(c, i) in items" :key="c.id || i" class="col-md-6 col-lg-4">
          <div class="card p-2 bt-hover-lift" style="cursor:pointer"
               @click="goDetail(c)">
            <div class="d-flex gap-3 align-items-center">
              <div class="bt-avatar bt-avatar-md" :class="'bt-avatar-color-' + ((c.id || i) % 8)">
                {{ (c.name || '?')[0] }}
              </div>
              <div class="flex-grow-1 min-w-0">
                <div class="fw-semibold" style="color:var(--bt-text-heading)">{{ c.name }}</div>
                <div class="small text-muted">{{ [c.contact, c.phone].filter(Boolean).join(' · ') }}</div>
              </div>
            </div>
            <hr class="my-2">
            <div class="d-flex small text-muted gap-3">
              <span>{{ c.active_tickets || 0 }} 工单</span>
              <span>{{ c.device_count || 0 }} 设备</span>
              <span v-if="c.unpaid_amount">¥{{ (+c.unpaid_amount).toFixed(0) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 空 -->
      <div v-else class="text-center py-5 text-muted">
        <p><i class="bi bi-people" style="font-size:48px"></i></p>
        <p>{{ err || '暂无客户' }}</p>
        <button v-if="err" class="btn btn-sm btn-primary" @click="load">重试</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { clientApi } from '@/api/clients'
import { useToast } from '@/composables/useToast'

const { show: showToast } = useToast()

const router = useRouter()
const items = ref([])
const loading = ref(true)
const err = ref('')
const q = ref('')
const showForm = ref(false)
const saving = ref(false)
const formName = ref('')
const formContact = ref('')
const formPhone = ref('')
const nameInput = ref(null)

onMounted(() => { load() })

async function load() {
  loading.value = true
  err.value = ''
  try {
    const params = { page: 1, page_size: 100 }
    if (q.value.trim()) params.q = q.value.trim()
    const data = await clientApi.list(params)
    items.value = data.clients || []
  } catch (e) {
    items.value = []
    err.value = '加载失败'
  } finally {
    loading.value = false
  }
}

async function createClient() {
  const name = formName.value.trim()
  if (!name) { showToast('请输入客户名称', 'warning'); return }
  saving.value = true
  try {
    await clientApi.create({ name: name, contact: formContact.value.trim(), phone: formPhone.value.trim() })
    formName.value = ''; formContact.value = ''; formPhone.value = ''
    showForm.value = false
    load()
  } catch (e) {
    showToast('创建失败', 'danger')
  } finally {
    saving.value = false
  }
}

function goDetail(c) {
  if (c.name) router.push('/clients/' + encodeURIComponent(c.name))
}
</script>
