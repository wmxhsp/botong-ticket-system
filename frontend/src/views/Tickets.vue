<template>
  <div>
    <div class="bt-page-title">
      <h2>工单管理</h2>
      <p class="d-none d-md-inline">查看、筛选和管理所有工单</p>
    </div>

    <div class="bt-filter-bar">
      <div class="row g-2 align-items-end">
        <div class="col-6 col-md-2">
          <label class="form-label small text-muted">状态</label>
          <select class="form-select form-select-sm" v-model="filters.status" @change="onFilterChange">
            <option value="">全部工单</option>
            <option value="open">待处理</option>
            <option value="in-progress">进行中</option>
            <option value="pending-parts">待配件</option>
            <option value="pending-client">待确认</option>
            <option value="pending-payment">待结算</option>
            <option value="completed">已完成</option>
            <option value="closed">已关闭</option>
            <option value="cancelled">已取消</option>
            <option value="archived">已归档</option>
          </select>
        </div>
        <div class="col-6 col-md-2">
          <label class="form-label small text-muted">客户</label>
          <ClientSelector v-model="filters.client" @select="onClientFilterSelect" />
        </div>
        <div class="col-6 col-md-2">
          <label class="form-label small text-muted">关键词</label>
          <input class="form-control form-control-sm" v-model="filters.keyword" placeholder="工单号/内容" @input="onKeywordInput">
        </div>
        <div class="col-6 col-md-2 d-flex gap-1 align-items-end">
          <button class="btn btn-primary btn-sm flex-fill" @click="handleSearch"><i class="bi bi-search"></i> 查询</button>
        </div>
      </div>
    </div>

    <div class="card p-2">
      <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
        <h5 class="mb-0"><i class="bi bi-list-ul me-2"></i>工单列表</h5>
        <div class="d-flex align-items-center gap-2">
          <router-link to="/tickets/new" class="btn btn-sm btn-primary">
            <i class="bi bi-plus-lg"></i> 新建
          </router-link>
          <button class="btn btn-sm btn-outline-success" @click="exportCSV">
            <i class="bi bi-download"></i> 导出CSV
          </button>
        </div>
      </div>

      <div v-if="selectedIds.length > 0" class="d-flex align-items-center gap-2 mb-2 p-2 rounded" style="background:var(--bt-gray-100)">
        <span class="text-muted small me-2">已选 {{ selectedIds.length }} 条</span>
        <button class="btn btn-sm btn-success me-1" @click="batchComplete">批量完工</button>
        <div class="btn-group">
          <button class="btn btn-sm btn-outline-primary dropdown-toggle" data-bs-toggle="dropdown">批量状态</button>
          <ul class="dropdown-menu" style="font-size:13px;min-width:120px">
            <li><a class="dropdown-item" href="#" @click.prevent="batchStatus('in-progress')">进行中</a></li>
            <li><a class="dropdown-item" href="#" @click.prevent="batchStatus('pending-payment')">待结算</a></li>
            <li><a class="dropdown-item" href="#" @click.prevent="batchStatus('completed')">已完成</a></li>
            <li><a class="dropdown-item" href="#" @click.prevent="batchStatus('closed')">已关闭</a></li>
            <li><a class="dropdown-item" href="#" @click.prevent="batchStatus('archived')">已归档</a></li>
          </ul>
        </div>
        <button class="btn btn-sm btn-outline-secondary ms-auto" @click="clearSelection">取消选择</button>
      </div>

      <LoadingSkeleton v-if="loading" type="table" :count="8" />

      <div v-else class="table-responsive" ref="scrollContainer">
        <table class="bt-table">
          <thead>
            <tr>
              <th style="width:36px">
                <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" style="cursor:pointer">
              </th>
              <th>工单号</th>
              <th>客户名称</th>
              <th>内容</th>
              <th>状态</th>
              <th>金额</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tickets" :key="t.id" :class="{ 'bt-table-selected': selectedIds.includes(t.id) }" class="bt-clickable" @click="goToTicket(t.id)">
              <td data-label="">
                <input type="checkbox" :checked="selectedIds.includes(t.id)" @click.stop @change="toggleSelect(t.id)" style="cursor:pointer">
              </td>
              <td data-label="工单号"><strong>{{ t.ticket_no || '-' }}</strong></td>
              <td data-label="客户">{{ t.client || '-' }}</td>
              <td data-label="内容" class="bt-ellipsis" style="max-width:200px">
                {{ t.description || t.content || '-' }}
              </td>
              <td data-label="状态"><StatusBadge :status="t.status" /></td>
              <td data-label="金额">{{ formatMoney(t.total || t.amount) }}</td>
              <td data-label="时间">{{ formatDate(t.created_at) }}</td>
              <td data-label="操作">
                <router-link :to="'/tickets/' + t.id" class="btn btn-sm btn-outline-primary" @click.stop>
                  详情
                </router-link>
              </td>
            </tr>
            <tr v-if="tickets.length === 0 && !loading">
              <td colspan="8" class="text-center py-5">
                <div class="bt-empty-state">
                  <div class="bt-empty-icon"><i class="bi bi-inbox"></i></div>
                  <div class="bt-empty-title">暂无工单</div>
                  <div class="bt-empty-desc">还没有工单记录，点击新建来创建第一张工单</div>
                  <router-link to="/tickets/new" class="btn btn-primary btn-sm">新建工单</router-link>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="loadingMore" class="text-center py-3">
        <div class="d-flex align-items-center justify-content-center gap-2">
          <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
          <span class="text-muted text-sm">加载更多...</span>
        </div>
      </div>

      <div v-if="!hasMore && tickets.length > 0" class="text-center py-3">
        <span class="text-muted text-sm">已加载全部数据</span>
      </div>

      <div class="d-flex justify-content-between align-items-center mt-3" v-if="!hasMore && total > 0">
        <small class="text-muted">共 {{ total }} 条</small>
        <button class="btn btn-sm btn-outline-secondary" @click="resetScroll">
          <i class="bi bi-arrow-up"></i> 返回顶部
        </button>
      </div>
    </div>

    <div ref="scrollTrigger"></div>
  </div>
</template>

<script setup>
defineOptions({ name: 'Tickets' })

import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ticketApi } from '@/api/tickets'
import { toolsApi, downloadBlob } from '@/api/tools'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ClientSelector from '@/components/selectors/ClientSelector.vue'
import { useToast } from '@/composables/useToast'
import { formatMoney } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const { show: showToast } = useToast()
const selectedIds = ref([])
const scrollContainer = ref(null)

const filters = ref({
  status: '',
  client: '',
  keyword: '',
})

let debounceTimer = null

async function fetchTickets(pageNum, pageSize) {
  const params = {
    page: pageNum,
    page_size: pageSize,
  }
  if (filters.value.status) params.status = filters.value.status
  if (filters.value.client) params.client = filters.value.client
  if (filters.value.keyword) params.q = filters.value.keyword

  const data = await ticketApi.list(params)
  return {
    items: data.tickets || data.data || data.records || [],
    total: data.total || data.count || 0
  }
}

function hasMoreChecker(data) {
  const currentCount = data.items?.length || 0
  return currentCount > 0 && currentCount >= 20
}

const {
  items: tickets,
  loading,
  loadingMore,
  hasMore,
  total,
  setTarget,
  reset
} = useInfiniteScroll({
  fetchFn: fetchTickets,
  hasMore: hasMoreChecker,
  threshold: 300,
  pageSize: 20
})

const allSelected = computed(() =>
  tickets.value.length > 0 && selectedIds.value.length === tickets.value.length
)

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = tickets.value.map(t => t.id)
  }
}

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function clearSelection() {
  selectedIds.value = []
}

function goToTicket(id) {
  router.push('/tickets/' + id)
}

function onClientFilterSelect(item) {
  if (item) {
    filters.value.client = item.name || ''
  }
  handleSearch()
}

function onFilterChange() {
  handleSearch()
}

function onKeywordInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    handleSearch()
  }, 300)
}

function handleSearch() {
  reset()
  clearSelection()
}

async function batchStatus(status) {
  const ids = selectedIds.value
  if (ids.length === 0) return
  try {
    const result = await ticketApi.batchAction('status', ids, { target_status: status })
    showToast(result.message || `完成 ${result.success} 条`, 'success')
    selectedIds.value = []
    reset()
  } catch { /* error handled globally */ }
}

async function batchComplete() {
  const ids = selectedIds.value
  if (ids.length === 0) return
  try {
    const result = await ticketApi.batchAction('complete', ids)
    showToast(result.message || `完成 ${result.success} 条`, 'success')
    selectedIds.value = []
    reset()
  } catch { /* error handled globally */ }
}

async function exportCSV() {
  try {
    const params = {}
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.client) params.client = filters.value.client
    if (filters.value.keyword) params.q = filters.value.keyword
    const res = await toolsApi.exportTickets(params)
    const blob = res.data || res
    downloadBlob(blob, '工单导出.csv')
    showToast('工单数据已导出', 'success')
  } catch (e) {
    showToast('导出失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return dateStr.slice(0, 10)
}

function resetScroll() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  if (route.query.q) {
    filters.value.keyword = route.query.q
  }
  
  nextTick(() => {
    const trigger = document.querySelector('[ref="scrollTrigger"]')
    if (trigger) {
      setTarget(trigger)
    }
  })
})

watch(() => filters.value.status, () => {
  handleSearch()
})
</script>

<style scoped>
.bt-table-selected {
  background-color: var(--bt-table-hover) !important;
}
</style>
