<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useCommandPalette } from '@/core/composables/useCommandPalette'

const {
  isOpen,
  searchQuery,
  selectedIndex,
  results,
  isLoading,
  close,
  selectPrevious,
  selectNext,
  executeSelected
} = useCommandPalette()

const inputRef = ref<HTMLInputElement | null>(null)

// 监听打开状态，自动聚焦输入框
watch(isOpen, (newValue) => {
  if (newValue) {
    setTimeout(() => {
      inputRef.value?.focus()
    }, 100)
  }
})

// 键盘事件处理
function handleKeydown(event: KeyboardEvent) {
  if (!isOpen.value) return
  
  switch (event.key) {
    case 'ArrowUp':
      event.preventDefault()
      selectPrevious()
      break
    case 'ArrowDown':
      event.preventDefault()
      selectNext()
      break
    case 'Enter':
      event.preventDefault()
      executeSelected()
      break
    case 'Escape':
      event.preventDefault()
      close()
      break
  }
}

// 全局键盘监听
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  
  // 监听自定义事件打开命令面板
  document.addEventListener('open-command-palette', () => {
    // 通过useCommandPalette的open方法打开
  })
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// 点击遮罩关闭
function handleOverlayClick() {
  close()
}

// 阻止事件冒泡
function handleContentClick(event: Event) {
  event.stopPropagation()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="command-palette">
      <div v-if="isOpen" class="command-palette-overlay" @click="handleOverlayClick">
        <div class="command-palette-container" @click="handleContentClick">
          <!-- 搜索框 -->
          <div class="search-box">
            <span class="search-icon">🔍</span>
            <input
              ref="inputRef"
              v-model="searchQuery"
              type="text"
              placeholder="搜索工单、客户或输入命令..."
              class="search-input"
            />
            <kbd class="shortcut-hint">ESC</kbd>
          </div>
          
          <!-- 加载状态 -->
          <div v-if="isLoading" class="loading-state">
            <div class="spinner"></div>
            <span>搜索中...</span>
          </div>
          
          <!-- 搜索结果列表 -->
          <div v-else-if="results.length > 0" class="results-list">
            <div
              v-for="(item, index) in results"
              :key="item.id"
              class="result-item"
              :class="{ selected: index === selectedIndex }"
              @click="executeSelected"
              @mouseenter="selectedIndex = index"
            >
              <span class="item-icon">{{ item.icon }}</span>
              <div class="item-content">
                <div class="item-title">{{ item.title }}</div>
                <div v-if="item.subtitle" class="item-subtitle">{{ item.subtitle }}</div>
              </div>
              <span v-if="item.type === 'command'" class="item-type">命令</span>
            </div>
          </div>
          
          <!-- 无结果 -->
          <div v-else-if="searchQuery" class="no-results">
            <span class="no-results-icon">🔍</span>
            <div class="no-results-text">未找到相关结果</div>
            <div class="no-results-hint">尝试其他关键词</div>
          </div>
          
          <!-- 空状态（显示最近使用） -->
          <div v-else class="empty-state">
            <div class="empty-title">最近使用</div>
            <div class="empty-hint">输入关键词搜索工单、客户或命令</div>
          </div>
          
          <!-- 底部提示 -->
          <div class="footer-hints">
            <span><kbd>↑↓</kbd> 选择</span>
            <span><kbd>↵</kbd> 确认</span>
            <span><kbd>esc</kbd> 关闭</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* 遮罩层 */
.command-palette-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  z-index: 9999;
}

/* 容器 */
.command-palette-container {
  width: 90%;
  max-width: 640px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 搜索框 */
.search-box {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  gap: 12px;
}

.search-icon {
  font-size: 20px;
  opacity: 0.5;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  color: #1f2937;
  background: transparent;
}

.search-input::placeholder {
  color: #9ca3af;
}

.shortcut-hint {
  padding: 4px 8px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 12px;
  color: #6b7280;
  font-family: monospace;
}

/* 加载状态 */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: #6b7280;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 结果列表 */
.results-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.result-item:hover,
.result-item.selected {
  background: #f3f4f6;
}

.result-item.selected {
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
}

.item-icon {
  font-size: 20px;
  width: 32px;
  text-align: center;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-subtitle {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.item-type {
  padding: 2px 8px;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

/* 无结果 */
.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: #6b7280;
}

.no-results-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.no-results-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.no-results-hint {
  font-size: 14px;
  color: #9ca3af;
}

/* 空状态 */
.empty-state {
  padding: 32px;
  text-align: center;
  color: #6b7280;
}

.empty-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #374151;
}

.empty-hint {
  font-size: 13px;
}

/* 底部提示 */
.footer-hints {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  font-size: 12px;
  color: #6b7280;
}

.footer-hints kbd {
  padding: 2px 6px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  font-family: monospace;
  font-size: 11px;
  margin-right: 4px;
}

/* 过渡动画 */
.command-palette-enter-active,
.command-palette-leave-active {
  transition: opacity 0.2s ease;
}

.command-palette-enter-from,
.command-palette-leave-to {
  opacity: 0;
}

.command-palette-enter-active .command-palette-container,
.command-palette-leave-active .command-palette-container {
  transition: transform 0.2s ease;
}

.command-palette-enter-from .command-palette-container,
.command-palette-leave-to .command-palette-container {
  transform: translateY(-20px);
}
</style>
