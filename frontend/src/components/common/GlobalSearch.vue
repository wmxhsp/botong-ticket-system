<template>
  <Teleport to="body">
    <Transition name="search-fade">
      <div v-if="visible" class="global-search-overlay" @click.self="close">
        <div class="global-search-modal">
          <div class="global-search-input-wrap">
            <i class="bi bi-search"></i>
            <input
              ref="inputRef"
              v-model="query"
              type="text"
              class="global-search-input"
              placeholder="搜索工单、客户、设备..."
              @keydown.down.prevent="moveDown"
              @keydown.up.prevent="moveUp"
              @keydown.enter.prevent="selectCurrent"
              @keydown.escape.prevent="close"
            />
            <kbd class="global-search-kbd">ESC</kbd>
          </div>

          <div class="global-search-results" v-if="query && !loading">
            <template v-if="results.tickets?.length">
              <div class="global-search-group">
                <div class="global-search-group-title"><i class="bi bi-ticket-perforated me-1"></i>工单</div>
                <div v-for="item in results.tickets" :key="'t'+item.id"
                     class="global-search-item" :class="{ active: activeIndex === getIndex('tickets', item.id) }"
                     @click="navigate(item)">
                  <div class="global-search-item-title">#{{ item.id }} {{ item.client }}</div>
                  <div class="global-search-item-desc">{{ item.content?.slice(0, 50) }}</div>
                </div>
              </div>
            </template>
            <template v-if="results.clients?.length">
              <div class="global-search-group">
                <div class="global-search-group-title"><i class="bi bi-people me-1"></i>客户</div>
                <div v-for="item in results.clients" :key="'c'+item.id"
                     class="global-search-item" :class="{ active: activeIndex === getIndex('clients', item.id) }"
                     @click="navigate(item)">
                  <div class="global-search-item-title">{{ item.name }}</div>
                  <div class="global-search-item-desc">{{ item.contact || '' }} {{ item.phone || '' }}</div>
                </div>
              </div>
            </template>
            <template v-if="results.equipment?.length">
              <div class="global-search-group">
                <div class="global-search-group-title"><i class="bi bi-pc-display me-1"></i>设备</div>
                <div v-for="item in results.equipment" :key="'e'+item.id"
                     class="global-search-item" :class="{ active: activeIndex === getIndex('equipment', item.id) }"
                     @click="navigate(item)">
                  <div class="global-search-item-title">{{ item.name }}</div>
                  <div class="global-search-item-desc">{{ item.client || '' }} {{ item.model ? '- ' + item.model : '' }}</div>
                </div>
              </div>
            </template>
            <div v-if="hasNoResults" class="global-search-empty">
              <i class="bi bi-search me-1"></i>未找到相关结果
            </div>
          </div>

          <div class="global-search-results" v-else-if="query && loading">
            <div class="global-search-empty">
              <div class="bt-spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle"></div>
              <span class="ms-2">搜索中...</span>
            </div>
          </div>

          <div class="global-search-results" v-else-if="recentSearches.length && !query">
            <div class="global-search-group">
              <div class="global-search-group-title d-flex justify-content-between">
                <span><i class="bi bi-clock-history me-1"></i>最近搜索</span>
                <button class="btn btn-sm btn-link text-muted p-0" @click="clearRecent">清除</button>
              </div>
              <div v-for="(q, i) in recentSearches" :key="i"
                   class="global-search-item" @click="query = q">
                <div class="global-search-item-title">{{ q }}</div>
              </div>
            </div>
          </div>

          <div class="global-search-footer">
            <span><kbd>↑↓</kbd> 导航</span>
            <span><kbd>Enter</kbd> 选择</span>
            <span><kbd>Esc</kbd> 关闭</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { searchApi } from '@/api/search'

const router = useRouter()
const visible = ref(false)
const query = ref('')
const loading = ref(false)
const results = ref({})
const activeIndex = ref(0)
const inputRef = ref(null)
const recentSearches = ref([])

let debounceTimer = null

// Load recent searches
try {
  const saved = localStorage.getItem('bt_recent_searches')
  if (saved) recentSearches.value = JSON.parse(saved).slice(0, 5)
} catch {}

function open() {
  visible.value = true
  activeIndex.value = 0
  nextTick(() => inputRef.value?.focus())
}

function close() {
  visible.value = false
  query.value = ''
  results.value = {}
}

function getAllItems() {
  const items = []
  if (results.value.tickets) items.push(...results.value.tickets.map(i => ({ ...i, _type: 'tickets' })))
  if (results.value.clients) items.push(...results.value.clients.map(i => ({ ...i, _type: 'clients' })))
  if (results.value.equipment) items.push(...results.value.equipment.map(i => ({ ...i, _type: 'equipment' })))
  return items
}

function getIndex(type, id) {
  let idx = 0
  if (type === 'clients' && results.value.tickets) idx += results.value.tickets.length
  if (type === 'equipment') {
    if (results.value.tickets) idx += results.value.tickets.length
    if (results.value.clients) idx += results.value.clients.length
  }
  const list = results.value[type] || []
  return idx + list.findIndex(i => i.id === id)
}

function moveDown() {
  const total = getAllItems().length
  if (total === 0) return
  activeIndex.value = (activeIndex.value + 1) % total
}

function moveUp() {
  const total = getAllItems().length
  if (total === 0) return
  activeIndex.value = (activeIndex.value - 1 + total) % total
}

function selectCurrent() {
  const items = getAllItems()
  if (items[activeIndex.value]) navigate(items[activeIndex.value])
}

function navigate(item) {
  // Save to recent
  if (query.value) {
    const searches = [query.value, ...recentSearches.value.filter(s => s !== query.value)].slice(0, 5)
    recentSearches.value = searches
    localStorage.setItem('bt_recent_searches', JSON.stringify(searches))
  }

  close()
  if (item._type === 'tickets' || item.ticket_no) {
    router.push('/tickets/' + item.id)
  } else if (item._type === 'clients' || item.name && !item.model) {
    router.push('/clients/' + encodeURIComponent(item.name))
  } else if (item._type === 'equipment' || item.model) {
    router.push('/equipment/' + item.id)
  }
}

function clearRecent() {
  recentSearches.value = []
  localStorage.removeItem('bt_recent_searches')
}

const hasNoResults = computed(() => {
  const r = results.value
  return (!r.tickets || r.tickets.length === 0) && (!r.clients || r.clients.length === 0) && (!r.equipment || r.equipment.length === 0)
})

watch(query, (val) => {
  if (!val || val.length < 1) {
    results.value = {}
    return
  }
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    loading.value = true
    activeIndex.value = 0
    try {
      const data = await searchApi.search({ q: val })
      results.value = {
        tickets: data.tickets || [],
        clients: data.clients || [],
        equipment: data.equipment || [],
      }
    } catch {
      results.value = {}
    } finally {
      loading.value = false
    }
  }, 300)
})

// Listen for Ctrl+K
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    if (visible.value) close()
    else open()
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  clearTimeout(debounceTimer)
})

defineExpose({ open, close })
</script>

<style scoped>
.global-search-overlay {
  position: fixed; inset: 0; z-index: 10000;
  background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(4px);
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: min(20vh, 120px);
}
.global-search-modal {
  width: 100%; max-width: 560px; margin: 0 16px;
  background: var(--card-bg, #fff); border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  overflow: hidden; max-height: 70vh; display: flex; flex-direction: column;
}
.global-search-input-wrap {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; border-bottom: 1px solid var(--card-border, #e5e7eb);
}
.global-search-input-wrap > i { color: var(--bt-gray-400, #9ca3af); font-size: 16px; }
.global-search-input {
  flex: 1; border: none; outline: none; font-size: 16px;
  background: transparent; color: var(--bt-text-body, #1f2937);
}
.global-search-kbd {
  font-size: 11px; padding: 2px 6px; border-radius: 4px;
  background: var(--bt-gray-100, #f3f4f6); color: var(--bt-gray-500, #6b7280);
  border: 1px solid var(--bt-gray-200, #e5e7eb);
}
.global-search-results {
  overflow-y: auto; flex: 1; padding: 4px 0;
}
.global-search-group-title {
  padding: 8px 16px 4px; font-size: 12px; font-weight: 600;
  color: var(--bt-gray-500, #6b7280); text-transform: uppercase; letter-spacing: 0.5px;
}
.global-search-item {
  padding: 10px 16px; cursor: pointer; transition: background 0.1s;
}
.global-search-item:hover, .global-search-item.active {
  background: var(--bt-gray-50, #f3f4f6);
}
[data-theme="dark"] .global-search-item:hover,
[data-theme="dark"] .global-search-item.active {
  background: rgba(99, 102, 241, 0.1);
}
.global-search-item-title { font-size: 14px; font-weight: 500; color: var(--bt-text-body, #1f2937); }
.global-search-item-desc { font-size: 12px; color: var(--bt-gray-400, #9ca3af); margin-top: 2px; }
.global-search-empty {
  padding: 24px; text-align: center; color: var(--bt-gray-400, #9ca3af); font-size: 14px;
}
.global-search-footer {
  display: flex; gap: 16px; padding: 8px 16px; border-top: 1px solid var(--card-border, #e5e7eb);
  font-size: 11px; color: var(--bt-gray-400, #9ca3af);
}
.global-search-footer kbd {
  font-size: 10px; padding: 1px 4px; border-radius: 3px;
  background: var(--bt-gray-100, #f3f4f6); border: 1px solid var(--bt-gray-200, #e5e7eb);
}

/* Transitions */
.search-fade-enter-active { transition: opacity 0.15s ease; }
.search-fade-leave-active { transition: opacity 0.1s ease; }
.search-fade-enter-from, .search-fade-leave-to { opacity: 0; }
.search-fade-enter-active .global-search-modal { animation: searchIn 0.2s ease; }
@keyframes searchIn { from { transform: scale(0.96) translateY(-8px); opacity: 0; } to { transform: scale(1) translateY(0); opacity: 1; } }

@media (max-width: 576px) {
  .global-search-overlay { padding-top: 8px; }
  .global-search-modal { margin: 0 8px; max-height: 85vh; border-radius: 10px; }
}
</style>
