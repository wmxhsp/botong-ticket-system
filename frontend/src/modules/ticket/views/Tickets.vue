<template>
  <div class="ticket-workspace">
    <!-- 左侧列表 -->
    <div class="ticket-list" :class="{ collapsed: selectedTicket }">
      <div class="list-header">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h5 class="mb-0"><i class="bi bi-list-ul me-2"></i>工单列表</h5>
          <div class="d-flex gap-1">
            <router-link to="/tickets/new" class="btn btn-sm btn-primary">
              <i class="bi bi-plus-lg"></i>
            </router-link>
            <button class="btn btn-sm btn-outline-success" @click="exportCSV">
              <i class="bi bi-download"></i>
            </button>
          </div>
        </div>

        <div class="search-box">
          <i class="bi bi-search"></i>
          <input
            v-model="filters.keyword"
            placeholder="搜索工单号、客户、内容..."
            @input="onKeywordInput"
          />
          <button class="btn-icon" @click="showFilters = !showFilters">
            <i class="bi bi-funnel"></i>
          </button>
        </div>

        <!-- 快速筛选标签 -->
        <div class="filter-tags">
          <button
            v-for="filter in statusFilters"
            :key="filter.value"
            class="tag"
            :class="{ active: filters.status === filter.value }"
            @click="selectStatusFilter(filter.value)"
          >
            {{ filter.label }}
            <span v-if="filter.count !== undefined" class="tag-count">{{ filter.count }}</span>
          </button>
        </div>
      </div>

      <LoadingSkeleton v-if="loading" type="list" :count="8" />

      <div v-else class="list-content" ref="listRef">
        <div
          v-for="t in tickets"
          :key="t.id"
          class="ticket-item"
          :class="{ active: selectedTicket?.id === t.id, urgent: isUrgent(t) }"
          @click="selectTicket(t)"
        >
          <div class="item-header">
            <span class="ticket-id">{{ t.ticket_no || '#' + t.id }}</span>
            <StatusBadge :status="t.status" />
            <span class="time">{{ formatDate(t.created_at) }}</span>
          </div>
          <div class="client-name">{{ t.client || t.client_name || '-' }}</div>
          <div class="ticket-preview">{{ t.description || t.content || '-' }}</div>
          <div class="item-footer">
            <span class="amount" v-if="t.total || t.amount">{{ formatMoney(t.total || t.amount) }}</span>
            <span class="technician" v-if="t.technician || t.technician_name">
              <i class="bi bi-person"></i> {{ t.technician || t.technician_name }}
            </span>
          </div>
        </div>

        <div v-if="tickets.length === 0 && !loading" class="bt-empty-state">
          <div class="bt-empty-icon"><i class="bi bi-inbox"></i></div>
          <div class="bt-empty-title">暂无工单</div>
          <div class="bt-empty-desc">还没有工单记录，点击新建来创建第一张工单</div>
          <router-link to="/tickets/new" class="btn btn-primary btn-sm">新建工单</router-link>
        </div>
      </div>

      <div v-if="loadingMore" class="text-center py-3">
        <div class="d-flex align-items-center justify-content-center gap-2">
          <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
          <span class="text-muted text-sm">加载更多...</span>
        </div>
      </div>

      <div v-if="!hasMore && tickets.length > 0" class="text-center py-2">
        <span class="text-muted text-sm">已加载全部 {{ total }} 条</span>
      </div>

      <div ref="scrollTrigger"></div>
    </div>

    <!-- 右侧详情（滑出） -->
    <Transition name="slide">
      <div v-if="selectedTicket" class="ticket-detail" :class="{ 'mobile-open': isMobileOpen }">
        <div class="detail-header">
          <button class="btn-icon d-lg-none" @click="closeDetail">
            <i class="bi bi-arrow-left"></i>
          </button>
          <button class="btn-icon d-none d-lg-inline" @click="closeDetail">
            <i class="bi bi-x-lg"></i>
          </button>
          <div class="detail-title">
            <span class="ticket-no">{{ selectedTicket.ticket_no || '#' + selectedTicket.id }}</span>
            <StatusBadge :status="selectedTicket.status" />
          </div>
          <div class="header-actions">
            <router-link :to="'/tickets/' + selectedTicket.id" class="btn btn-sm btn-outline-primary">
              <i class="bi bi-box-arrow-up-right"></i> <span class="d-none d-sm-inline">全屏</span>
            </router-link>
          </div>
        </div>

        <div class="detail-content">
          <!-- 基本信息 -->
          <div class="info-section">
            <div class="info-row">
              <span class="label">客户</span>
              <router-link
                v-if="selectedTicket.client || selectedTicket.client_name"
                :to="'/clients/' + encodeURIComponent(selectedTicket.client || selectedTicket.client_name)"
                class="text-decoration-none"
              >
                {{ selectedTicket.client || selectedTicket.client_name }}
              </router-link>
              <span v-else>-</span>
            </div>
            <div class="info-row">
              <span class="label">联系人</span>
              <span>{{ selectedTicket.contact || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">电话</span>
              <a v-if="selectedTicket.phone" :href="'tel:' + selectedTicket.phone">{{ selectedTicket.phone }}</a>
              <span v-else>-</span>
            </div>
            <div class="info-row">
              <span class="label">地址</span>
              <span>{{ selectedTicket.location || selectedTicket.address || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">创建时间</span>
              <span>{{ formatDateTime(selectedTicket.created_at) }}</span>
            </div>
          </div>

          <!-- 问题描述 -->
          <div class="content-section" v-if="selectedTicket.description || selectedTicket.content">
            <h6><i class="bi bi-info-circle me-2"></i>问题描述</h6>
            <p>{{ selectedTicket.description || selectedTicket.content }}</p>
          </div>

          <!-- 服务明细 -->
          <div class="service-section" v-if="selectedTicket.service_items?.length">
            <h6><i class="bi bi-clock-history me-2"></i>服务明细</h6>
            <div v-for="item in selectedTicket.service_items" :key="item.id" class="service-item">
              <span class="service-name">{{ item.name || item.description || '服务' }}</span>
              <span class="service-amount">
                <span v-if="item.hours">{{ item.hours }}h × {{ formatMoney(item.unit_price || item.rate) }}</span>
                <span v-else-if="item.days">{{ item.days }}天 × {{ formatMoney(item.unit_price || item.rate) }}</span>
                <span v-else>{{ formatMoney(item.total || item.amount) }}</span>
              </span>
            </div>
          </div>

          <!-- 材料 -->
          <div class="materials-section" v-if="selectedTicket.materials?.length">
            <h6><i class="bi bi-box-seam me-2"></i>使用材料</h6>
            <div v-for="m in selectedTicket.materials" :key="m.id" class="material-item">
              <span>{{ m.name || m.goods_name }} x{{ m.quantity }}</span>
              <span>{{ formatMoney(m.total || m.amount || m.unit_price * m.quantity) }}</span>
            </div>
          </div>

          <!-- 金额汇总 -->
          <div class="amount-summary">
            <div class="summary-row">
              <span>劳务费</span>
              <span>{{ formatMoney(selectedTicket.labor_fee || selectedTicket.labor_amount || 0) }}</span>
            </div>
            <div class="summary-row">
              <span>材料费</span>
              <span>{{ formatMoney(selectedTicket.material_fee || selectedTicket.material_amount || 0) }}</span>
            </div>
            <div class="summary-row total">
              <span>合计</span>
              <span>{{ formatMoney(selectedTicket.total || selectedTicket.total_amount || selectedTicket.amount || 0) }}</span>
            </div>
            <div class="summary-row" v-if="selectedTicket.paid_amount">
              <span>已收款</span>
              <span class="text-success">{{ formatMoney(selectedTicket.paid_amount) }}</span>
            </div>
          </div>

          <!-- 快捷操作 -->
          <div class="detail-actions">
            <router-link :to="'/tickets/' + selectedTicket.id" class="btn btn-primary btn-sm w-100">
              <i class="bi bi-pencil me-1"></i> 编辑工单
            </router-link>
          </div>
        </div>
      </div>
    </Transition>
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
import { useToast } from '@/composables/useToast'
import { formatMoney, formatDate, formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const { show: showToast } = useToast()
const listRef = ref(null)
const scrollTrigger = ref(null)
const showFilters = ref(false)
const selectedTicket = ref(null)
const isMobileOpen = ref(false)

const filters = ref({
  status: '',
  keyword: '',
})

const statusFilters = [
  { value: '', label: '全部' },
  { value: 'open', label: '待处理' },
  { value: 'in-progress', label: '进行中' },
  { value: 'pending-payment', label: '待结算' },
  { value: 'completed', label: '已完成' },
  { value: 'closed', label: '已关闭' },
]

let debounceTimer = null

async function fetchTickets(pageNum, pageSize) {
  const params = {
    page: pageNum,
    page_size: pageSize,
  }
  if (filters.value.status) params.status = filters.value.status
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

function isUrgent(ticket) {
  return ticket.priority === 'H' || ticket.status === 'open'
}

function selectTicket(ticket) {
  selectedTicket.value = ticket
  isMobileOpen.value = true
}

function closeDetail() {
  selectedTicket.value = null
  isMobileOpen.value = false
}

function selectStatusFilter(status) {
  filters.value.status = status
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
  selectedTicket.value = null
}

async function exportCSV() {
  try {
    const params = {}
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.keyword) params.q = filters.value.keyword
    const res = await toolsApi.exportTickets(params)
    const blob = res.data || res
    downloadBlob(blob, '工单导出.csv')
    showToast('工单数据已导出', 'success')
  } catch (e) {
    showToast('导出失败: ' + (e.response?.data?.error || e.message), 'danger')
  }
}

onMounted(() => {
  if (route.query.q) {
    filters.value.keyword = route.query.q
  }
  if (route.query.status) {
    filters.value.status = route.query.status
  }

  nextTick(() => {
    if (scrollTrigger.value) {
      setTarget(scrollTrigger.value)
    }
  })
})

watch(() => filters.value.status, () => {
  handleSearch()
})
</script>

<style scoped>
.ticket-workspace {
  display: flex;
  height: calc(100vh - 120px);
  min-height: 500px;
  overflow: hidden;
  gap: 0;
}

/* 左侧列表 */
.ticket-list {
  flex: 1;
  min-width: 320px;
  max-width: 100%;
  border-right: 1px solid var(--bt-gray-200);
  display: flex;
  flex-direction: column;
  background: var(--bt-card-bg);
  transition: max-width 0.3s ease;
}

.ticket-list.collapsed {
  max-width: 400px;
}

.list-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--bt-gray-200);
  flex-shrink: 0;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bt-gray-100);
  border-radius: 8px;
  margin-top: 8px;
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: var(--bt-text-body);
}

.search-box input::placeholder {
  color: var(--bt-gray-400);
}

.btn-icon {
  background: transparent;
  border: none;
  padding: 4px 6px;
  cursor: pointer;
  color: var(--bt-gray-500);
  border-radius: 4px;
  transition: background 0.15s;
}

.btn-icon:hover {
  background: var(--bt-gray-200);
}

.filter-tags {
  display: flex;
  gap: 6px;
  margin-top: 10px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.filter-tags::-webkit-scrollbar {
  height: 2px;
}

.tag {
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  border: 1px solid var(--bt-gray-200);
  background: transparent;
  cursor: pointer;
  white-space: nowrap;
  color: var(--bt-gray-600);
  transition: all 0.15s;
}

.tag:hover {
  background: var(--bt-gray-100);
}

.tag.active {
  background: var(--bt-primary);
  color: white;
  border-color: var(--bt-primary);
}

.tag-count {
  margin-left: 4px;
  opacity: 0.8;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.ticket-item {
  padding: 14px 16px;
  border-bottom: 1px solid var(--bt-gray-100);
  cursor: pointer;
  transition: background 0.15s;
}

.ticket-item:hover {
  background: var(--bt-gray-50);
}

.ticket-item.active {
  background: rgba(99, 102, 241, 0.05);
  border-left: 3px solid var(--bt-primary);
  padding-left: 13px;
}

.ticket-item.urgent {
  border-left: 3px solid var(--bt-danger);
  padding-left: 13px;
}

.ticket-item.active.urgent {
  border-left: 3px solid var(--bt-primary);
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.ticket-id {
  font-size: 12px;
  color: var(--bt-gray-400);
  font-weight: 500;
}

.time {
  margin-left: auto;
  font-size: 12px;
  color: var(--bt-gray-400);
}

.client-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
  color: var(--bt-text-body);
}

.ticket-preview {
  font-size: 13px;
  color: var(--bt-gray-500);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-footer {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  font-size: 12px;
}

.amount {
  color: var(--bt-success);
  font-weight: 600;
}

.technician {
  color: var(--bt-gray-400);
}

/* 右侧详情 */
.ticket-detail {
  flex: 1;
  min-width: 360px;
  max-width: 520px;
  background: var(--bt-card-bg);
  border-left: 1px solid var(--bt-gray-200);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--bt-gray-200);
  flex-shrink: 0;
  background: var(--bt-card-bg);
}

.detail-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.ticket-no {
  font-weight: 600;
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.info-section {
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--bt-gray-100);
  font-size: 13px;
}

.info-row .label {
  color: var(--bt-gray-400);
  flex-shrink: 0;
}

.info-row a {
  color: var(--bt-primary);
}

.content-section,
.service-section,
.materials-section {
  margin-bottom: 20px;
}

.content-section h6,
.service-section h6,
.materials-section h6 {
  font-size: 13px;
  font-weight: 600;
  color: var(--bt-gray-600);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.content-section p {
  font-size: 13px;
  line-height: 1.6;
  color: var(--bt-text-body);
  margin: 0;
}

.service-item,
.material-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--bt-gray-100);
  font-size: 13px;
}

.service-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.service-amount {
  color: var(--bt-gray-500);
  font-size: 12px;
  flex-shrink: 0;
  margin-left: 8px;
}

.amount-summary {
  background: var(--bt-gray-50);
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 13px;
}

.summary-row.total {
  border-top: 2px solid var(--bt-gray-200);
  margin-top: 6px;
  padding-top: 10px;
  font-size: 15px;
  font-weight: 700;
}

.detail-actions {
  padding-top: 8px;
}

/* 滑出动画 */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(20px);
  opacity: 0;
}

/* 空状态 */
.bt-empty-state {
  text-align: center;
  padding: 40px 20px;
}

.bt-empty-icon {
  font-size: 40px;
  color: var(--bt-gray-300);
  margin-bottom: 12px;
}

.bt-empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--bt-gray-500);
  margin-bottom: 4px;
}

.bt-empty-desc {
  font-size: 13px;
  color: var(--bt-gray-400);
  margin-bottom: 16px;
}

/* 响应式：移动端 */
@media (max-width: 991.98px) {
  .ticket-workspace {
    height: auto;
    min-height: calc(100vh - 100px);
    position: relative;
  }

  .ticket-list {
    max-width: 100% !important;
    border-right: none;
  }

  .ticket-list.collapsed .ticket-item {
    opacity: 0.6;
  }

  .ticket-detail {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1050;
    max-width: 100%;
    min-width: auto;
    border-left: none;
    transform: translateX(100%);
    transition: transform 0.3s ease;
  }

  .ticket-detail.mobile-open {
    transform: translateX(0);
  }

  .slide-enter-active,
  .slide-leave-active {
    transition: none;
  }

  .slide-enter-from,
  .slide-leave-to {
    transform: none;
    opacity: 1;
  }
}

@media (min-width: 992px) {
  .ticket-detail {
    position: static;
    transform: none !important;
  }
}
</style>
