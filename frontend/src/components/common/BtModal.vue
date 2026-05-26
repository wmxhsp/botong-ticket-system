<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="modal-backdrop" @click.self="handleClose">
        <div class="bt-modal-container" :style="{ maxWidth: maxWidth }">
          <div class="bt-modal-content">
            <div v-if="title || $slots.header" class="bt-modal-header">
              <slot name="header">
                <h5 class="bt-modal-title">
                  <i v-if="icon" :class="icon" class="me-2"></i>
                  {{ title }}
                </h5>
              </slot>
              <button v-if="showClose" class="bt-modal-close" @click="handleClose" type="button">
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
            <div class="bt-modal-body">
              <slot name="body"></slot>
            </div>
            <div v-if="showFooter || $slots.footer" class="bt-modal-footer">
              <slot name="footer">
                <button v-if="cancelText" class="btn btn-outline-secondary btn-sm" @click="handleClose" type="button">
                  {{ cancelText }}
                </button>
                <button v-if="confirmText" class="btn btn-primary btn-sm" @click="handleConfirm" :disabled="loading">
                  <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
                  {{ confirmText }}
                </button>
              </slot>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
  icon: { type: String, default: '' },
  maxWidth: { type: String, default: '500px' },
  showClose: { type: Boolean, default: true },
  showFooter: { type: Boolean, default: true },
  confirmText: { type: String, default: '确认' },
  cancelText: { type: String, default: '取消' },
  loading: { type: Boolean, default: false },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'xl'].includes(v)
  }
})

const emit = defineEmits(['close', 'confirm', 'update:visible'])

const sizeMap = { sm: '400px', md: '500px', lg: '700px', xl: '900px' }

function handleClose() {
  emit('update:visible', false)
  emit('close')
}

function handleConfirm() {
  emit('confirm')
}
</script>

<style scoped>
.bt-modal-container {
  width: 100%;
  margin: 1.5rem auto;
  pointer-events: none;
}

.bt-modal-content {
  pointer-events: auto;
  background: var(--card-bg, #fff);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--card-border, #e5e7eb);
  overflow: hidden;
  animation: bt-modal-in 0.2s ease;
}

@keyframes bt-modal-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.bt-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--card-border, #e5e7eb);
  background: var(--card-bg, #fff);
}

.bt-modal-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--bt-text-heading, #1f2937);
}

.bt-modal-close {
  background: none;
  border: none;
  padding: 4px 8px;
  cursor: pointer;
  color: var(--bt-text-muted, #6b7280);
  font-size: 18px;
  line-height: 1;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.bt-modal-close:hover {
  background: var(--bt-gray-100, #f3f4f6);
  color: var(--bt-text-body, #374151);
}

.bt-modal-body {
  padding: 20px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.bt-modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--card-border, #e5e7eb);
  background: var(--bt-gray-50, #f9fafb);
}

/* Dark mode */
[data-theme="dark"] .bt-modal-content {
  background: var(--card-bg, #1f2937);
  border-color: var(--card-border, #374151);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

[data-theme="dark"] .bt-modal-header {
  background: var(--card-bg, #1f2937);
  border-bottom-color: var(--card-border, #374151);
}

[data-theme="dark"] .bt-modal-title {
  color: var(--bt-text-heading, #f3f4f6);
}

[data-theme="dark"] .bt-modal-close:hover {
  background: var(--bt-gray-100, #374151);
}

[data-theme="dark"] .bt-modal-footer {
  background: var(--bt-gray-100, #111827);
  border-top-color: var(--card-border, #374151);
}

/* Animation */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 576px) {
  .bt-modal-container {
    margin: 0;
    max-width: 100%;
    height: 100vh;
    display: flex;
    align-items: flex-end;
  }
  
  .bt-modal-content {
    border-radius: 16px 16px 0 0;
    max-height: 90vh;
    width: 100%;
  }
}
</style>
