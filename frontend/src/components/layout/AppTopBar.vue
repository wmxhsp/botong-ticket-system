<template>
  <div class="bt-top-bar d-flex justify-content-between align-items-center py-1 px-2" style="border-bottom:1px solid var(--bt-gray-200)">
    <button class="bt-sidebar-toggle btn btn-sm btn-outline-secondary" @click="$emit('toggle-sidebar')" title="侧边栏">
      <i class="bi bi-list"></i>
    </button>
    <div class="flex-grow-1 d-flex justify-content-end">
      <div class="input-group input-group-sm" style="max-width:350px;position:relative" id="globalSearchWrap">
        <span class="input-group-text bg-white border-end-0"><i class="bi bi-search text-muted"></i></span>
        <input class="form-control border-start-0"
               v-model="searchQuery"
               placeholder="搜索工单号/客户/设备/序列号..."
               style="font-size:13px"
               @keydown.enter="doSearch"
               @input="onSearchInput"
               @keydown.down.prevent="highlightNext"
               @keydown.up.prevent="highlightPrev"
               @keydown.escape="showResults = false"
               @focus="onSearchFocus" />
        <kbd class="position-absolute d-none d-sm-inline-flex align-items-center"
             style="right:8px;top:50%;transform:translateY(-50%);font-size:10px;padding:1px 5px;border-radius:3px;border:1px solid var(--bt-gray-200);color:var(--bt-gray-400);pointer-events:none;background:var(--bt-gray-50);z-index:3">Ctrl+K</kbd>
        <div id="searchResults" class="list-group shadow-sm" v-show="showResults"
             style="position:absolute;top:100%;left:0;right:0;z-index:9999;max-height:400px;overflow-y:auto;border-radius:0 0 8px 8px;background:var(--card-bg);border:1px solid var(--card-border)">
          <div v-if="searchLoading" class="px-3 py-2 text-muted small">
            <i class="bi bi-arrow-repeat spin me-1"></i>搜索中...
          </div>
          <template v-else-if="searchResults.length > 0">
            <div class="dropdown-header small text-muted px-3 py-2" style="background:var(--bt-gray-50)"
                 v-for="(group, gIdx) in groupedResults" :key="gIdx">
              <i :class="group.icon" class="me-1"></i>{{ group.label }} ({{ group.items.length }})
              <a v-for="(item, idx) in group.items" :key="idx" class="list-group-item list-group-item-action px-3 py-2"
                 :class="{ active: highlightedIdx === globalIndex(gIdx, idx) }"
                 :style="{fontSize:'13px',borderLeft:0,borderRight:0,cursor:'pointer'}"
                 @click="navigateTo(item)" @mouseenter="highlightedIdx = globalIndex(gIdx, idx)"
                 v-html="formatSearchItem(item, searchQuery)">
              </a>
            </div>
            <div class="text-center py-1 border-top">
              <a class="text-decoration-none small text-primary px-3 py-2 d-block" style="font-size:12px;cursor:pointer"
                 @click="doSearch">
                查看全部结果 <i class="bi bi-arrow-right"></i>
              </a>
            </div>
          </template>
          <div v-else class="px-3 py-3 text-muted text-center" style="font-size:13px">
            <i class="bi bi-emoji-neutral me-1"></i>无匹配结果
          </div>
        </div>
      </div>

      <button class="bt-theme-toggle ms-2" @click="app.toggleTheme()" :title="themeTitle">
        <i :class="themeIcon"></i>
      </button>

      <a class="position-relative ms-2 text-decoration-none" title="通知中心" @click.prevent="checkNotif" style="cursor:pointer">
        <i class="bi bi-bell fs-6" :class="notifCount > 0 ? 'text-primary' : 'text-muted'"></i>
        <span v-if="notifCount > 0"
              class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
              style="font-size:9px">{{ notifCount > 99 ? '99+' : notifCount }}</span>
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { searchApi } from '@/api/search'
import { reminderApi } from '@/api/reminders'

const router = useRouter()
const app = useAppStore()

const searchQuery = ref('')
const searchResults = ref([])
const searchLoading = ref(false)
const showResults = ref(false)
const highlightedIdx = ref(-1)
const notifCount = ref(0)

let searchTimer = null
let notifTimer = null

const groupedResults = computed(() => {
  const groups = []
  const r = searchResults.value
  if (!r || !r.tickets || !r.tickets.length) return groups
  if (r.tickets?.length) groups.push({ label: '工单', icon: 'bi bi-ticket-perforated', items: r.tickets, type: 'ticket' })
  if (r.equipment?.length) groups.push({ label: '设备', icon: 'bi bi-pc-display', items: r.equipment, type: 'equipment' })
  if (r.clients?.length) groups.push({ label: '客户', icon: 'bi bi-people', items: r.clients, type: 'client' })
  return groups
})

const escapeHtml = (str) => {
  if (!str) return ''
  return str.replace(/[&<>"']/g, (m) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[m])
}

const highlightKeyword = (text, keyword) => {
  if (!text) return ''
  const escaped = escapeHtml(text)
  if (!keyword) return escaped
  const escapedKw = escapeHtml(keyword)
  const regex = new RegExp(escapeRegex(escapedKw), 'gi')
  return escaped.replace(regex, '<mark>$&</mark>')
}

const escapeRegex = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

const formatSearchItem = (item, keyword) => {
  if (item.type === 'ticket') {
    return `<strong>${highlightKeyword(item.ticket_no, keyword)}</strong>
            <small class="text-muted ms-2">${highlightKeyword(item.client, keyword)}</small>`
  } else if (item.type === 'equipment') {
    return `<strong>${highlightKeyword(item.name, keyword)}</strong>
            <small class="text-muted ms-2">${highlightKeyword(item.serial_no || item.model, keyword)}</small>`
  } else if (item.type === 'client') {
    return `<strong>${highlightKeyword(item.name || item.client, keyword)}</strong>`
  }
  return escapeHtml(item.name || item.title || JSON.stringify(item))
}

function globalIndex(gIdx, idx) {
  let count = 0
  for (let i = 0; i < gIdx; i++) {
    count += (groupedResults.value[i]?.items?.length || 0)
  }
  return count + idx
}

const allFlatItems = computed(() => {
  const items = []
  groupedResults.value.forEach(g => {
    g.items.forEach(item => items.push({ ...item, _type: g.type }))
  })
  return items
})

const themeIcon = computed(() => {
  if (app.theme === 'dark') return 'bi bi-moon-fill'
  if (app.theme === 'light') return 'bi bi-sun-fill'
  return 'bi bi-circle-half'
})

const themeTitle = computed(() => {
  if (app.theme === 'dark') return '切换亮色模式'
  if (app.theme === 'light') return '切换暗色模式'
  return '跟随系统'
})

onMounted(() => {
  fetchNotifCount()
  notifTimer = setInterval(fetchNotifCount, 30000)
  document.addEventListener('click', onClickOutside)
})

onUnmounted(() => {
  clearInterval(notifTimer)
  document.removeEventListener('click', onClickOutside)
})

function onClickOutside(e) {
  const wrap = document.getElementById('globalSearchWrap')
  if (wrap && !wrap.contains(e.target)) {
    showResults.value = false
  }
}

function doSearch() {
  const q = searchQuery.value.trim()
  showResults.value = false
  if (q) {
    router.push({ path: '/tickets', query: { q } })
  }
}

function onSearchInput() {
  showResults.value = true
  highlightedIdx.value = -1
  clearTimeout(searchTimer)
  const q = searchQuery.value.trim()
  if (q.length < 1) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  searchTimer = setTimeout(async () => {
    try {
      const data = await searchApi.search({ q })
      searchResults.value = data.results || {}
    } catch {
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }, 250)
}

function onSearchFocus() {
  if (searchQuery.value.trim().length > 0) {
    showResults.value = true
  }
}

function highlightNext() {
  const total = allFlatItems.value.length
  highlightedIdx.value = Math.min(highlightedIdx.value + 1, total - 1)
  scrollToHighlighted()
}

function highlightPrev() {
  highlightedIdx.value = Math.max(highlightedIdx.value - 1, -1)
  scrollToHighlighted()
}

function scrollToHighlighted() {
  setTimeout(() => {
    const el = document.querySelector('#searchResults .list-group-item.active')
    if (el) el.scrollIntoView({ block: 'nearest' })
  }, 50)
}

function navigateTo(item) {
  showResults.value = false
  if (item._type === 'ticket') {
    router.push('/tickets/' + item.id)
  } else if (item._type === 'client') {
    router.push('/clients/' + encodeURIComponent(item.name || item.client))
  } else if (item._type === 'equipment') {
    router.push('/equipment')
  }
}

async function fetchNotifCount() {
  try {
    const data = await reminderApi.getCount()
    notifCount.value = data.count || 0
  } catch {
    // Silent
  }
}

function checkNotif() {
  router.push({ name: 'Notifications' })
}
</script>

<style scoped>
.bt-sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  font-size: 18px;
  border-radius: 8px;
}
.spin { animation: rotate 1s linear infinite; }
@keyframes rotate { to { transform: rotate(360deg); } }
</style>
