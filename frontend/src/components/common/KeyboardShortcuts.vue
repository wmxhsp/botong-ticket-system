<template>
  <BtModal v-model:visible="visible" title="键盘快捷键" icon="bi-keyboard" max-width="500px">
    <template #body>
      <div class="shortcuts-list">
        <div class="shortcuts-section">
          <h6 class="shortcuts-title">全局快捷键</h6>
          <div class="shortcuts-grid">
            <div class="shortcut-item">
              <kbd>Ctrl</kbd> + <kbd>K</kbd>
              <span class="shortcut-desc">全局搜索</span>
            </div>
            <div class="shortcut-item">
              <kbd>Ctrl</kbd> + <kbd>?</kbd>
              <span class="shortcut-desc">显示此帮助</span>
            </div>
            <div class="shortcut-item">
              <kbd>Esc</kbd>
              <span class="shortcut-desc">关闭弹窗</span>
            </div>
          </div>
        </div>

        <div class="shortcuts-section">
          <h6 class="shortcuts-title">列表页快捷键</h6>
          <div class="shortcuts-grid">
            <div class="shortcut-item">
              <kbd>↑</kbd> / <kbd>↓</kbd>
              <span class="shortcut-desc">选择列表项</span>
            </div>
            <div class="shortcut-item">
              <kbd>Enter</kbd>
              <span class="shortcut-desc">查看详情</span>
            </div>
            <div class="shortcut-item">
              <kbd>N</kbd>
              <span class="shortcut-desc">新建记录</span>
            </div>
            <div class="shortcut-item">
              <kbd>R</kbd>
              <span class="shortcut-desc">刷新列表</span>
            </div>
          </div>
        </div>

        <div class="shortcuts-section">
          <h6 class="shortcuts-title">工单操作</h6>
          <div class="shortcuts-grid">
            <div class="shortcut-item">
              <kbd>S</kbd>
              <span class="shortcut-desc">开始计时</span>
            </div>
            <div class="shortcut-item">
              <kbd>E</kbd>
              <span class="shortcut-desc">编辑工单</span>
            </div>
            <div class="shortcut-item">
              <kbd>P</kbd>
              <span class="shortcut-desc">确认收款</span>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <button class="btn btn-primary btn-sm" @click="visible = false">知道了</button>
    </template>
  </BtModal>
</template>

<script setup>
import { ref, provide } from 'vue'
import BtModal from '@/components/common/BtModal.vue'

const visible = ref(false)

function show() {
  visible.value = true
}

function hide() {
  visible.value = false
}

defineExpose({ show, hide })
provide('keyboardShortcuts', { show, hide })
</script>

<style scoped>
.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.shortcuts-section {
  border-bottom: 1px solid var(--bt-gray-200);
  padding-bottom: 16px;
}

.shortcuts-section:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.shortcuts-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--bt-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.shortcuts-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.shortcut-desc {
  color: var(--bt-text-muted);
  margin-left: auto;
}

kbd {
  display: inline-block;
  padding: 2px 6px;
  font-size: 11px;
  font-family: monospace;
  font-weight: 600;
  color: var(--bt-text-body);
  background: var(--bt-gray-100);
  border: 1px solid var(--bt-gray-300);
  border-radius: 4px;
  box-shadow: 0 1px 0 var(--bt-gray-300);
}

[data-theme="dark"] kbd {
  background: var(--bt-gray-700);
  border-color: var(--bt-gray-600);
  color: var(--bt-text-body);
  box-shadow: 0 1px 0 var(--bt-gray-600);
}

@media (max-width: 576px) {
  .shortcuts-grid {
    gap: 12px;
  }
  
  .shortcut-item {
    flex-wrap: wrap;
  }
  
  .shortcut-desc {
    width: 100%;
    margin-left: 24px;
    margin-top: -4px;
  }
}
</style>
