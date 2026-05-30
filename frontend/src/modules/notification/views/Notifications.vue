<template>
  <div class="page-notifications">
    <div class="bt-page-title">
      <h2><i class="bi bi-bell me-2"></i>通知中心</h2>
      <p class="d-none d-md-inline">查看所有系统通知 · 共 {{ totalCount }} 条</p>
    </div>

    <div class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <div class="d-flex gap-2">
          <button class="btn btn-sm" :class="filter === 'all' ? 'btn-primary' : 'btn-outline-secondary'" @click="filter = 'all'; loadNotifs()">全部</button>
          <button class="btn btn-sm" :class="filter === 'unread' ? 'btn-primary' : 'btn-outline-secondary'" @click="filter = 'unread'; loadNotifs()">未读</button>
        </div>
        <button class="btn btn-sm btn-outline-success" @click="markAllRead"><i class="bi bi-check-all"></i> 全部已读</button>
      </div>

      <div v-if="loading" class="text-center py-4"><div class="spinner"></div><p class="mt-2 text-muted">加载中...</p></div>
      <div v-else-if="notifs.length === 0" class="text-center py-5 text-muted"><i class="bi bi-inbox" style="font-size:48px"></i><p class="mt-2">暂无通知</p></div>
      <div v-else class="table-responsive">
        <table class="bt-table">
          <thead><tr><th style="width:40px">状态</th><th>内容</th><th style="width:160px">时间</th><th style="width:100px">操作</th></tr></thead>
          <tbody>
            <tr v-for="n in notifs" :key="n.id" :class="{ 'fw-bold': !n.read }">
              <td><span class="badge" :class="n.read ? 'bg-secondary' : 'bg-primary'">{{ n.read ? '已读' : '未读' }}</span></td>
              <td>{{ n.content || n.title }}</td>
              <td class="text-muted small">{{ formatTime(n.created_at) }}</td>
              <td><button v-if="!n.read" class="btn btn-sm btn-outline-primary" @click="markRead(n.id)"><i class="bi bi-check"></i></button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reminderApi } from '@/api/reminders'

const notifs = ref([])
const filter = ref('all')
const loading = ref(false)
const totalCount = ref(0)

onMounted(() => loadNotifs())

async function loadNotifs() {
  loading.value = true
  try {
    const data = filter.value === 'all' ? await reminderApi.getAll() : await reminderApi.getPending()
    notifs.value = Array.isArray(data) ? data : data?.notifications || data?.data || []
    totalCount.value = notifs.value.length
  } catch (e) {
    console.error('加载通知失败:', e)
    notifs.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

async function markRead(id) {
  try {
    await reminderApi.markRead(id)
    const n = notifs.value.find(x => x.id === id)
    if (n) n.read = true
  } catch (e) { console.error('标记已读失败:', e) }
}

async function markAllRead() {
  try {
    await reminderApi.markAllRead()
    notifs.value.forEach(n => { n.read = true })
  } catch (e) { console.error('全部标记已读失败:', e) }
}

function formatTime(t) { return t ? t.slice(0, 16).replace('T', ' ') : '' }
</script>