<template>
  <Teleport to="body">
    <Transition name="cmd-fade">
      <div
        v-if="isOpen"
        class="cmd-overlay"
        role="dialog"
        aria-modal="true"
        aria-label="命令面板"
        @click.self="close"
      >
        <div class="cmd-modal" ref="modalRef">
          <div class="cmd-input-wrap">
            <i class="bi bi-search"></i>
            <input
              ref="inputRef"
              v-model="query"
              type="text"
              class="cmd-input"
              placeholder="搜索工单、客户、命令..."
              role="combobox"
              aria-autocomplete="list"
              aria-controls="cmd-listbox"
              :aria-activedescendant="activeId"
              aria-expanded="true"
              @keydown.down.prevent="moveDown"
              @keydown.up.prevent="moveUp"
              @keydown.enter.prevent="selectCurrent"
              @keydown.escape.prevent="close"
              @keydown.home.prevent="moveToFirst"
              @keydown.end.prevent="moveToLast"
            />
            <kbd class="cmd-kbd">ESC</kbd>
          </div>

          <div
            id="cmd-listbox"
            class="cmd-results"
            role="listbox"
            v-if="filteredItems.length"
          >
            <div
              v-for="(item, index) in filteredItems"
              :key="item.id"
              :id="`cmd-item-${index}`"
              class="cmd-item"
              role="option"
              :aria-selected="activeIndex === index"
              :class="{ active: activeIndex === index }"
              @click="executeItem(item)"
              @mouseenter="activeIndex = index"
              ref="itemRefs"
            >
              <div class="cmd-item-icon">
                <i :class="item.icon || getDefaultIcon(item.type)"></i>
              </div>
              <div class="cmd-item-content">
                <div class="cmd-item-title">{{ item.title }}</div>
                <div v-if="item.subtitle" class="cmd-item-subtitle">{{ item.subtitle }}</div>
              </div>
              <div class="cmd-item-badge">
                <span :class="['badge', getBadgeClass(item.type)]">{{ getBadgeLabel(item.type) }}</span>
              </div>
            </div>
          </div>

          <div class="cmd-results" v-else-if="query && loading">
            <div class="cmd-empty">
              <div class="bt-spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle"></div>
              <span class="ms-2">搜索中...</span>
            </div>
          </div>

          <div class="cmd-results" v-else-if="query && !loading">
            <div class="cmd-empty">
              <i class="bi bi-search me-1"></i>未找到相关结果
            </div>
          </div>

          <div class="cmd-footer">
            <span><kbd>↑↓</kbd> 导航</span>
            <span><kbd>Enter</kbd> 选择</span>
            <span><kbd>Esc</kbd> 关闭</span>
            <span><kbd>Home/End</kbd> 首尾</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { useCommandPalette } from '@/composables/useCommandPalette'

const {
  isOpen,
  query,
  loading,
  activeIndex,
  filteredItems,
  close,
  moveDown,
  moveUp,
  moveToFirst,
  moveToLast,
  selectCurrent,
  executeItem,
} = useCommandPalette()

const inputRef = ref(null)
const modalRef = ref(null)
const itemRefs = ref([])

const activeId = computed(() => {
  if (!filteredItems.value.length) return undefined
  return `cmd-item-${activeIndex.value}`
})

watch(isOpen, (val) => {
  if (val) {
    nextTick(() => {
      inputRef.value?.focus()
      scrollActiveIntoView()
    })
  }
})

watch(activeIndex, () => {
  nextTick(() => scrollActiveIntoView())
})

function scrollActiveIntoView() {
  const el = itemRefs.value?.[activeIndex.value]
  if (el && typeof el.scrollIntoView === 'function') {
    el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }
}

function getDefaultIcon(type) {
  const map = {
    ticket: 'bi-ticket-perforated',
    client: 'bi-person',
    command: 'bi-command',
    recent: 'bi-clock-history',
  }
  return map[type] || 'bi-circle'
}

function getBadgeClass(type) {
  const map = {
    ticket: 'bg-primary',
    client: 'bg-success',
    command: 'bg-secondary',
    recent: 'bg-info',
  }
  return map[type] || 'bg-secondary'
}

function getBadgeLabel(type) {
  const map = {
    ticket: '工单',
    client: '客户',
    command: '命令',
    recent: '最近',
  }
  return map[type] || type
}
</script>

<style scoped>
.cmd-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: min(20vh, 120px);
}

.cmd-modal {
  width: 100%;
  max-width: 600px;
  margin: 0 16px;
  background: var(--card-bg, #fff);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}

.cmd-input-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--card-border, #e5e7eb);
}

.cmd-input-wrap > i {
  color: var(--bt-gray-400, #9ca3af);
  font-size: 16px;
}

.cmd-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  background: transparent;
  color: var(--bt-text-body, #1f2937);
}

.cmd-kbd {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bt-gray-100, #f3f4f6);
  color: var(--bt-gray-500, #6b7280);
  border: 1px solid var(--bt-gray-200, #e5e7eb);
}

.cmd-results {
  overflow-y: auto;
  flex: 1;
  padding: 4px 0;
}

.cmd-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.1s;
}

.cmd-item:hover,
.cmd-item.active {
  background: var(--bt-gray-50, #f3f4f6);
}

[data-theme="dark"] .cmd-item:hover,
[data-theme="dark"] .cmd-item.active {
  background: rgba(99, 102, 241, 0.1);
}

.cmd-item-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: var(--bt-gray-100, #f3f4f6);
  color: var(--bt-gray-500, #6b7280);
  font-size: 14px;
  flex-shrink: 0;
}

.cmd-item.active .cmd-item-icon {
  background: rgba(99, 102, 241, 0.15);
  color: var(--bt-primary, #6366f1);
}

.cmd-item-content {
  flex: 1;
  min-width: 0;
}

.cmd-item-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--bt-text-body, #1f2937);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cmd-item-subtitle {
  font-size: 12px;
  color: var(--bt-gray-400, #9ca3af);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cmd-item-badge .badge {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.cmd-empty {
  padding: 24px;
  text-align: center;
  color: var(--bt-gray-400, #9ca3af);
  font-size: 14px;
}

.cmd-footer {
  display: flex;
  gap: 16px;
  padding: 8px 16px;
  border-top: 1px solid var(--card-border, #e5e7eb);
  font-size: 11px;
  color: var(--bt-gray-400, #9ca3af);
}

.cmd-footer kbd {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 3px;
  background: var(--bt-gray-100, #f3f4f6);
  border: 1px solid var(--bt-gray-200, #e5e7eb);
}

/* Transitions */
.cmd-fade-enter-active {
  transition: opacity 0.15s ease;
}
.cmd-fade-leave-active {
  transition: opacity 0.1s ease;
}
.cmd-fade-enter-from,
.cmd-fade-leave-to {
  opacity: 0;
}
.cmd-fade-enter-active .cmd-modal {
  animation: cmdIn 0.2s ease;
}
@keyframes cmdIn {
  from {
    transform: scale(0.96) translateY(-8px);
    opacity: 0;
  }
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

@media (max-width: 576px) {
  .cmd-overlay {
    padding-top: 8px;
  }
  .cmd-modal {
    margin: 0 8px;
    max-height: 85vh;
    border-radius: 10px;
  }
}
</style>
