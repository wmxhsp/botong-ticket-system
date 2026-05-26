<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" @click.self="handleCancel">
      <div class="confirm-dialog">
        <div class="confirm-header">
          <div class="confirm-icon" :class="iconClass">
            <i :class="iconName"></i>
          </div>
          <h4 class="confirm-title">{{ title }}</h4>
        </div>
        <div class="confirm-body">
          <p>{{ message }}</p>
          <div v-if="showInput" class="confirm-input">
            <input 
              v-model="inputValue" 
              type="text" 
              class="form-control" 
              :placeholder="inputPlaceholder"
              @keydown.enter="handleConfirm"
              ref="inputRef"
            />
          </div>
        </div>
        <div class="confirm-footer">
          <button class="btn btn-outline-secondary btn-sm" @click="handleCancel">取消</button>
          <button 
            class="btn btn-primary btn-sm" 
            @click="handleConfirm"
            :disabled="loading"
          >
            <span v-if="loading" class="btn-spinner"></span>
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '确认操作' },
  message: { type: String, default: '' },
  type: { type: String, default: 'confirm' },
  confirmText: { type: String, default: '确认' },
  showInput: { type: Boolean, default: false },
  inputPlaceholder: { type: String, default: '请输入确认信息' },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'cancel'])

const inputValue = ref('')
const inputRef = ref(null)

const iconClass = computed(() => {
  const classes = {
    confirm: 'confirm-icon-info',
    warning: 'confirm-icon-warning',
    danger: 'confirm-icon-danger',
  }
  return classes[props.type] || classes.confirm
})

const iconName = computed(() => {
  const icons = {
    confirm: 'bi bi-info-circle',
    warning: 'bi bi-exclamation-triangle',
    danger: 'bi bi-trash',
  }
  return icons[props.type] || icons.confirm
})

watch(() => props.visible, (val) => {
  if (val && props.showInput) {
    inputValue.value = ''
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

function handleConfirm() {
  emit('confirm', inputValue.value)
}

function handleCancel() {
  inputValue.value = ''
  emit('cancel')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.confirm-dialog {
  background: var(--card-bg);
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  border: 1px solid var(--card-border);
  animation: dialogIn 0.2s ease;
}

@keyframes dialogIn {
  from { opacity: 0; transform: scale(0.95) translateY(-10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.confirm-header {
  padding: 20px;
  border-bottom: 1px solid var(--card-border);
  text-align: center;
}

.confirm-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  font-size: 24px;
}

.confirm-icon-info {
  background: var(--bt-primary-bg);
  color: var(--bt-primary);
}

.confirm-icon-warning {
  background: #fffbeb;
  color: #d97706;
}

.confirm-icon-danger {
  background: #fef2f2;
  color: #dc2626;
}

.confirm-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--bt-text-heading);
}

.confirm-body {
  padding: 20px;
}

.confirm-body p {
  margin: 0;
  color: var(--bt-text-body);
  line-height: 1.6;
  text-align: center;
}

.confirm-input {
  margin-top: 16px;
}

.confirm-input .form-control {
  height: 42px;
  border-radius: 8px;
  border-color: var(--card-border);
  font-size: 14px;
}

.confirm-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--card-border);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.confirm-footer .btn {
  min-width: 80px;
  padding: 8px 16px;
  border-radius: 8px;
}

.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
