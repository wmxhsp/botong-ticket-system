<template>
  <div class="bt-toast-container">
    <div v-for="t in toasts" :key="t.id"
         class="bt-toast"
         :class="[t.type, { removing: t.removing }]"
         @click="remove(t.id)">
      <div class="toast-icon">
        <i :class="'bi ' + t.icon"></i>
      </div>
      <div class="toast-content">
        <div class="toast-title">{{ t.title }}</div>
        <div class="toast-message">{{ t.message }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useToast } from '@/composables/useToast'

const { toasts, remove } = useToast()
</script>

<style scoped>
.bt-toast-container {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.bt-toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 8px;
  background: var(--card-bg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-left: 3px solid var(--bt-primary, #6366f1);
  min-width: 300px;
  max-width: 420px;
  pointer-events: auto;
  cursor: pointer;
  animation: slideIn 0.25s ease forwards;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.bt-toast.removing {
  opacity: 0;
  transform: translateX(50px);
}

.bt-toast.success { border-left-color: #10b981; }
.bt-toast.warning { border-left-color: #f59e0b; }
.bt-toast.error { border-left-color: #ef4444; }
.bt-toast.info { border-left-color: #6366f1; }

.toast-icon { font-size: 20px; flex-shrink: 0; }
.bt-toast.success .toast-icon { color: #10b981; }
.bt-toast.warning .toast-icon { color: #f59e0b; }
.bt-toast.error .toast-icon { color: #ef4444; }
.bt-toast.info .toast-icon { color: #6366f1; }

.toast-content { flex: 1; }
.toast-title { font-weight: 600; font-size: 13px; color: #1f2937; margin-bottom: 2px; }
.toast-message { font-size: 12px; color: #6b7280; line-height: 1.4; }

@keyframes slideIn {
  from { opacity: 0; transform: translateX(100%) scale(0.95); }
  to { opacity: 1; transform: translateX(0) scale(1); }
}

/* Dark mode */
[data-theme="dark"] .bt-toast {
  background: #1e293b !important;
  border-color: #334155 !important;
}
[data-theme="dark"] .toast-title { color: #f1f5f9 !important; }
[data-theme="dark"] .toast-message { color: #94a3b8 !important; }

@media (max-width: 480px) {
  .bt-toast {
    min-width: auto;
    max-width: calc(100vw - 24px);
    font-size: 13px;
    padding: 12px 14px;
  }
  .bt-toast-container {
    top: 8px;
    right: 8px;
    left: 8px;
  }
}
</style>
