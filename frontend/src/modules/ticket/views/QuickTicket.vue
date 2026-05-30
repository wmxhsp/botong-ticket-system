<template>
  <div class="quick-ticket">
    <!-- 顶部进度指示器 -->
    <div class="step-indicator">
      <div
        v-for="s in 3"
        :key="s"
        class="step-dot"
        :class="{ active: s === step, completed: s < step }"
      ></div>
    </div>

    <!-- 步骤标题 -->
    <div class="step-header">
      <h3>{{ stepTitle }}</h3>
      <p class="step-subtitle">{{ stepSubtitle }}</p>
    </div>

    <!-- 步骤1：选择客户 -->
    <div v-if="step === 1" class="step-content">
      <!-- 搜索客户 -->
      <div class="search-box">
        <i class="bi bi-search"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索客户名称..."
          @input="onSearchInput"
        />
        <button
          v-if="searchQuery"
          class="clear-btn"
          @click="searchQuery = ''; filteredClients = []"
        >
          <i class="bi bi-x-circle-fill"></i>
        </button>
      </div>

      <!-- 语音输入客户 -->
      <button
        class="voice-btn"
        :class="{ recording: isRecording }"
        @touchstart.prevent="startVoice('client')"
        @touchend.prevent="stopVoice"
        @mousedown.prevent="startVoice('client')"
        @mouseup.prevent="stopVoice"
        @mouseleave.prevent="stopVoice"
      >
        <i class="bi bi-mic-fill"></i>
        <span>{{ isRecording ? '录音中...' : '长按语音输入客户' }}</span>
      </button>

      <!-- 最近客户 -->
      <div v-if="recentClients.length" class="section">
        <div class="section-title">最近客户</div>
        <div class="client-grid">
          <button
            v-for="client in recentClients"
            :key="client.name"
            class="client-chip"
            :class="{ selected: form.client === client.name }"
            @click="selectClient(client)"
          >
            <div class="client-name">{{ client.name }}</div>
            <div class="client-phone">{{ client.phone || '无电话' }}</div>
          </button>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div v-if="filteredClients.length" class="section">
        <div class="section-title">搜索结果</div>
        <div class="client-list">
          <button
            v-for="client in filteredClients"
            :key="client.name"
            class="client-item"
            :class="{ selected: form.client === client.name }"
            @click="selectClient(client)"
          >
            <div class="client-info">
              <div class="client-name">{{ client.name }}</div>
              <div class="client-meta">{{ client.phone || '' }} {{ client.contact || '' }}</div>
            </div>
            <i v-if="form.client === client.name" class="bi bi-check-circle-fill text-primary"></i>
          </button>
        </div>
      </div>

      <!-- 新建客户快捷入口 -->
      <div v-if="searchQuery && !filteredClients.length" class="section">
        <button class="create-client-btn" @click="createNewClient">
          <i class="bi bi-plus-lg"></i>
          <span>新建客户「{{ searchQuery }}」</span>
        </button>
      </div>
    </div>

    <!-- 步骤2：描述问题 -->
    <div v-if="step === 2" class="step-content">
      <!-- 问题描述输入 -->
      <div class="textarea-box">
        <textarea
          v-model="form.content"
          rows="4"
          placeholder="描述客户的问题..."
          autofocus
        ></textarea>
        <div class="textarea-actions">
          <button
            class="mic-btn"
            :class="{ recording: isRecording }"
            @touchstart.prevent="startVoice('content')"
            @touchend.prevent="stopVoice"
            @mousedown.prevent="startVoice('content')"
            @mouseup.prevent="stopVoice"
            @mouseleave.prevent="stopVoice"
          >
            <i class="bi bi-mic-fill"></i>
          </button>
        </div>
      </div>

      <!-- 语音按钮（大） -->
      <button
        class="voice-btn large"
        :class="{ recording: isRecording }"
        @touchstart.prevent="startVoice('content')"
        @touchend.prevent="stopVoice"
        @mousedown.prevent="startVoice('content')"
        @mouseup.prevent="stopVoice"
        @mouseleave.prevent="stopVoice"
      >
        <i class="bi bi-mic-fill"></i>
        <span>{{ isRecording ? '录音中，松手结束' : '长按语音描述问题' }}</span>
      </button>

      <!-- 常见问题标签 -->
      <div class="section">
        <div class="section-title">常见问题</div>
        <div class="tag-grid">
          <button
            v-for="tag in commonIssues"
            :key="tag"
            class="issue-tag"
            :class="{ selected: form.content.includes(tag) }"
            @click="appendIssue(tag)"
          >
            {{ tag }}
          </button>
        </div>
      </div>

      <!-- 快捷设置 -->
      <div class="quick-settings">
        <div class="setting-row">
          <span>优先级</span>
          <div class="priority-btns">
            <button
              v-for="p in priorities"
              :key="p.value"
              class="priority-btn"
              :class="{ selected: form.priority === p.value, [p.class]: true }"
              @click="form.priority = p.value"
            >
              {{ p.label }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 步骤3：确认创建 -->
    <div v-if="step === 3" class="step-content">
      <div class="summary-card">
        <div class="summary-row">
          <span class="summary-label">客户</span>
          <span class="summary-value">{{ form.client }}</span>
        </div>
        <div class="summary-row">
          <span class="summary-label">问题</span>
          <span class="summary-value">{{ form.content || '未填写' }}</span>
        </div>
        <div class="summary-row">
          <span class="summary-label">优先级</span>
          <span class="summary-value" :class="priorityClass">{{ priorityLabel }}</span>
        </div>
        <div class="summary-row" v-if="form.phone">
          <span class="summary-label">电话</span>
          <span class="summary-value">{{ form.phone }}</span>
        </div>
      </div>

      <div class="tip-box">
        <i class="bi bi-lightbulb"></i>
        <span>创建后可补充工时、材料、照片等详细信息</span>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="action-bar">
      <button
        v-if="step > 1"
        class="btn-back"
        @click="prevStep"
      >
        <i class="bi bi-arrow-left"></i>
        上一步
      </button>
      <button
        v-if="step < 3"
        class="btn-next"
        :disabled="!canNext"
        @click="nextStep"
      >
        下一步
        <i class="bi bi-arrow-right"></i>
      </button>
      <button
        v-if="step === 3"
        class="btn-create"
        :disabled="submitting"
        @click="submitTicket"
      >
        <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
        <i v-else class="bi bi-plus-lg me-1"></i>
        {{ submitting ? '创建中...' : '创建工单' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ticketApi } from '@/api/tickets'
import { clientApi } from '@/api/clients'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { show: showToast } = useToast()

const step = ref(1)
const submitting = ref(false)
const searchQuery = ref('')
const filteredClients = ref([])
const recentClients = ref([])
const isRecording = ref(false)
const voiceTarget = ref('')
let voiceTimer = null
let searchTimer = null

const VOICE_NS = Symbol.for('bt.quickticket.voice')
if (!window[VOICE_NS]) {
  window[VOICE_NS] = null
}

onUnmounted(() => {
  clearTimeout(searchTimer)
  clearTimeout(voiceTimer)
  const rec = window[VOICE_NS]
  if (rec) {
    try {
      rec.stop()
      rec.onresult = null
      rec.onerror = null
      rec.onend = null
    } catch (e) {
      /* ignore */
    }
    window[VOICE_NS] = null
  }
})

const form = ref({
  client: '',
  content: '',
  priority: 'M',
  phone: '',
  contact: '',
})

const priorities = [
  { value: 'L', label: '低', class: 'priority-low' },
  { value: 'M', label: '中', class: 'priority-mid' },
  { value: 'H', label: '高', class: 'priority-high' },
  { value: 'U', label: '急', class: 'priority-urgent' },
]

const commonIssues = [
  '无法上网', '电脑卡顿', '打印机故障', '系统重装',
  '网络布线', '监控维修', '数据恢复', '病毒清理',
  '软件安装', '硬件升级', '密码重置', '邮箱配置',
]

const stepTitle = computed(() => {
  const titles = ['', '选择客户', '描述问题', '确认创建']
  return titles[step.value]
})

const stepSubtitle = computed(() => {
  const subtitles = [
    '',
    '搜索或语音输入客户名称',
    '语音或选择常见问题',
    '核对信息后一键创建',
  ]
  return subtitles[step.value]
})

const canNext = computed(() => {
  if (step.value === 1) return !!form.value.client
  if (step.value === 2) return !!form.value.content
  return true
})

const priorityLabel = computed(() => {
  const p = priorities.find(p => p.value === form.value.priority)
  return p ? p.label : '中'
})

const priorityClass = computed(() => {
  const map = {
    L: 'text-success',
    M: 'text-warning',
    H: 'text-danger',
    U: 'text-danger fw-bold',
  }
  return map[form.value.priority] || 'text-warning'
})

function nextStep() {
  if (step.value < 3) step.value++
}

function prevStep() {
  if (step.value > 1) step.value--
}

function selectClient(client) {
  form.value.client = client.name
  form.value.phone = client.phone || ''
  form.value.contact = client.contact || ''
  nextStep()
}

function onSearchInput() {
  clearTimeout(searchTimer)
  if (!searchQuery.value.trim()) {
    filteredClients.value = []
    return
  }
  searchTimer = setTimeout(() => {
    searchClients(searchQuery.value)
  }, 300)
}

async function searchClients(q) {
  try {
    const data = await clientApi.list({ q })
    const list = Array.isArray(data) ? data : data?.clients || data?.data || []
    filteredClients.value = list.slice(0, 10)
  } catch (e) {
    filteredClients.value = []
  }
}

async function createNewClient() {
  const name = searchQuery.value.trim()
  if (!name) return
  try {
    await clientApi.create({ name })
    showToast(`客户「${name}」创建成功`, 'success')
    selectClient({ name, phone: '', contact: '' })
  } catch (e) {
    showToast('创建客户失败', 'danger')
  }
}

function appendIssue(tag) {
  const current = form.value.content || ''
  if (current.includes(tag)) {
    form.value.content = current.replace(tag, '').replace(/\s+/g, ' ').trim()
  } else {
    form.value.content = current ? `${current}，${tag}` : tag
  }
}

function startVoice(target) {
  voiceTarget.value = target
  isRecording.value = true
  voiceTimer = setTimeout(() => {
    if (isRecording.value) stopVoice()
  }, 10000)

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.lang = 'zh-CN'
    recognition.continuous = false
    recognition.interimResults = false
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      if (target === 'client') {
        searchQuery.value = transcript
        searchClients(transcript)
      } else if (target === 'content') {
        form.value.content = form.value.content
          ? `${form.value.content}，${transcript}`
          : transcript
      }
    }
    recognition.onerror = () => {
      showToast('语音识别失败，请重试', 'warning')
    }
    recognition.onend = () => {
      window[VOICE_NS] = null
    }
    recognition.start()
    window[VOICE_NS] = recognition
  } else {
    showToast('浏览器不支持语音识别', 'warning')
  }
}

function stopVoice() {
  isRecording.value = false
  clearTimeout(voiceTimer)
  const rec = window[VOICE_NS]
  if (rec) {
    try {
      rec.stop()
    } catch (e) {
      /* ignore */
    }
    window[VOICE_NS] = null
  }
}

function buildPayload() {
  return {
    client: form.value.client,
    content: form.value.content,
    priority: form.value.priority,
    phone: form.value.phone || undefined,
    contact: form.value.contact || undefined,
  }
}

async function submitTicket() {
  if (!form.value.client || !form.value.content) {
    showToast('请填写完整信息', 'warning')
    return
  }

  submitting.value = true
  try {
    const payload = buildPayload()
    const res = await ticketApi.create(payload)
    showToast('工单创建成功', 'success')
    const ticket = res?.ticket || res?.data || res
    if (ticket && ticket.id) {
      router.push('/tickets/' + ticket.id)
    } else {
      router.push('/tickets')
    }
  } catch (e) {
    console.error('创建失败:', e)
    showToast('创建失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    submitting.value = false
  }
}

async function loadRecentClients() {
  try {
    const data = await clientApi.list({ limit: 8 })
    const list = Array.isArray(data) ? data : data?.clients || data?.data || []
    recentClients.value = list.slice(0, 8)
  } catch (e) {
    recentClients.value = []
  }
}

onMounted(() => {
  loadRecentClients()
})
</script>

<style scoped>
.quick-ticket {
  max-width: 480px;
  margin: 0 auto;
  padding: 16px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bt-body-bg, #f8f9fa);
}

/* 步骤指示器 */
.step-indicator {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 16px 0;
}

.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--bt-gray-300, #dee2e6);
  transition: all 0.3s ease;
}

.step-dot.active {
  width: 32px;
  border-radius: 5px;
  background: var(--bt-primary, #0d6efd);
}

.step-dot.completed {
  background: var(--bt-success, #198754);
}

/* 步骤标题 */
.step-header {
  text-align: center;
  margin-bottom: 20px;
}

.step-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--bt-body-color, #212529);
}

.step-subtitle {
  font-size: 0.875rem;
  color: var(--bt-gray-500, #adb5bd);
  margin: 0;
}

/* 步骤内容 */
.step-content {
  flex: 1;
  overflow-y: auto;
}

/* 搜索框 */
.search-box {
  position: relative;
  margin-bottom: 16px;
}

.search-box input {
  width: 100%;
  height: 52px;
  padding: 0 44px;
  border: 1.5px solid var(--bt-gray-200, #e9ecef);
  border-radius: 14px;
  font-size: 1rem;
  background: var(--bt-white, #fff);
  transition: border-color 0.2s;
}

.search-box input:focus {
  outline: none;
  border-color: var(--bt-primary, #0d6efd);
}

.search-box .bi-search {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--bt-gray-400, #ced4da);
  font-size: 1.1rem;
}

.clear-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--bt-gray-400, #ced4da);
  font-size: 1.1rem;
  padding: 8px;
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 语音按钮 */
.voice-btn {
  width: 100%;
  height: 56px;
  border: 2px dashed var(--bt-gray-300, #dee2e6);
  border-radius: 14px;
  background: var(--bt-white, #fff);
  color: var(--bt-gray-600, #6c757d);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 1rem;
  margin-bottom: 20px;
  transition: all 0.2s;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
  touch-action: manipulation;
}

.voice-btn:active,
.voice-btn.recording {
  border-color: var(--bt-danger, #dc3545);
  background: rgba(220, 53, 69, 0.08);
  color: var(--bt-danger, #dc3545);
  transform: scale(0.98);
}

.voice-btn.large {
  height: 72px;
  font-size: 1.05rem;
}

.voice-btn .bi-mic-fill {
  font-size: 1.3rem;
}

.voice-btn.recording .bi-mic-fill {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 区域标题 */
.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--bt-gray-500, #adb5bd);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 客户网格 */
.client-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.client-chip {
  padding: 14px 12px;
  border: 1.5px solid var(--bt-gray-200, #e9ecef);
  border-radius: 12px;
  background: var(--bt-white, #fff);
  text-align: left;
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  min-height: 64px;
}

.client-chip:active {
  transform: scale(0.97);
  background: var(--bt-gray-50, #f8f9fa);
}

.client-chip.selected {
  border-color: var(--bt-primary, #0d6efd);
  background: rgba(13, 110, 253, 0.06);
}

.client-chip .client-name {
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--bt-body-color, #212529);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.client-chip .client-phone {
  font-size: 0.75rem;
  color: var(--bt-gray-500, #adb5bd);
  margin-top: 2px;
}

/* 客户列表 */
.client-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.client-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border: 1.5px solid var(--bt-gray-200, #e9ecef);
  border-radius: 12px;
  background: var(--bt-white, #fff);
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  min-height: 56px;
}

.client-item:active {
  transform: scale(0.98);
  background: var(--bt-gray-50, #f8f9fa);
}

.client-item.selected {
  border-color: var(--bt-primary, #0d6efd);
  background: rgba(13, 110, 253, 0.06);
}

.client-item .client-name {
  font-weight: 500;
  font-size: 0.9375rem;
}

.client-item .client-meta {
  font-size: 0.75rem;
  color: var(--bt-gray-500, #adb5bd);
  margin-top: 2px;
}

/* 新建客户按钮 */
.create-client-btn {
  width: 100%;
  padding: 16px;
  border: 2px dashed var(--bt-primary, #0d6efd);
  border-radius: 12px;
  background: rgba(13, 110, 253, 0.04);
  color: var(--bt-primary, #0d6efd);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 0.9375rem;
  font-weight: 500;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  min-height: 56px;
}

.create-client-btn:active {
  background: rgba(13, 110, 253, 0.1);
  transform: scale(0.98);
}

/* 文本域 */
.textarea-box {
  position: relative;
  margin-bottom: 16px;
}

.textarea-box textarea {
  width: 100%;
  padding: 16px;
  padding-right: 52px;
  border: 1.5px solid var(--bt-gray-200, #e9ecef);
  border-radius: 14px;
  font-size: 1rem;
  line-height: 1.5;
  background: var(--bt-white, #fff);
  resize: none;
  transition: border-color 0.2s;
}

.textarea-box textarea:focus {
  outline: none;
  border-color: var(--bt-primary, #0d6efd);
}

.textarea-actions {
  position: absolute;
  right: 12px;
  bottom: 12px;
}

.mic-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: var(--bt-gray-100, #f8f9fa);
  color: var(--bt-gray-600, #6c757d);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  transition: all 0.2s;
}

.mic-btn:active,
.mic-btn.recording {
  background: var(--bt-danger, #dc3545);
  color: var(--bt-white, #fff);
}

/* 问题标签 */
.tag-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.issue-tag {
  padding: 12px 8px;
  border: 1.5px solid var(--bt-gray-200, #e9ecef);
  border-radius: 10px;
  background: var(--bt-white, #fff);
  font-size: 0.8125rem;
  color: var(--bt-gray-700, #495057);
  text-align: center;
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.issue-tag:active {
  transform: scale(0.95);
}

.issue-tag.selected {
  border-color: var(--bt-primary, #0d6efd);
  background: rgba(13, 110, 253, 0.08);
  color: var(--bt-primary, #0d6efd);
  font-weight: 500;
}

/* 快捷设置 */
.quick-settings {
  margin-top: 20px;
  padding: 16px;
  background: var(--bt-white, #fff);
  border-radius: 14px;
  border: 1.5px solid var(--bt-gray-200, #e9ecef);
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.setting-row span {
  font-size: 0.9375rem;
  color: var(--bt-gray-700, #495057);
}

.priority-btns {
  display: flex;
  gap: 8px;
}

.priority-btn {
  padding: 8px 16px;
  border: 1.5px solid var(--bt-gray-200, #e9ecef);
  border-radius: 8px;
  background: var(--bt-white, #fff);
  font-size: 0.8125rem;
  color: var(--bt-gray-600, #6c757d);
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  min-height: 40px;
  min-width: 44px;
}

.priority-btn:active {
  transform: scale(0.95);
}

.priority-btn.selected.priority-low {
  border-color: var(--bt-success, #198754);
  background: rgba(25, 135, 84, 0.08);
  color: var(--bt-success, #198754);
  font-weight: 500;
}

.priority-btn.selected.priority-mid {
  border-color: var(--bt-warning, #ffc107);
  background: rgba(255, 193, 7, 0.08);
  color: #b38600;
  font-weight: 500;
}

.priority-btn.selected.priority-high,
.priority-btn.selected.priority-urgent {
  border-color: var(--bt-danger, #dc3545);
  background: rgba(220, 53, 69, 0.08);
  color: var(--bt-danger, #dc3545);
  font-weight: 500;
}

/* 摘要卡片 */
.summary-card {
  background: var(--bt-white, #fff);
  border-radius: 14px;
  border: 1.5px solid var(--bt-gray-200, #e9ecef);
  padding: 20px;
  margin-bottom: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 10px 0;
  border-bottom: 1px solid var(--bt-gray-100, #f8f9fa);
}

.summary-row:last-child {
  border-bottom: none;
}

.summary-label {
  font-size: 0.875rem;
  color: var(--bt-gray-500, #adb5bd);
  flex-shrink: 0;
  margin-right: 16px;
}

.summary-value {
  font-size: 0.9375rem;
  color: var(--bt-body-color, #212529);
  text-align: right;
  word-break: break-all;
}

/* 提示框 */
.tip-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  background: rgba(13, 110, 253, 0.06);
  border-radius: 12px;
  color: var(--bt-primary, #0d6efd);
  font-size: 0.8125rem;
}

.tip-box i {
  font-size: 1rem;
  flex-shrink: 0;
}

/* 底部操作栏 */
.action-bar {
  display: flex;
  gap: 12px;
  padding: 16px 0 24px;
  margin-top: auto;
}

.btn-back {
  flex: 0 0 auto;
  padding: 0 20px;
  height: 56px;
  border: 1.5px solid var(--bt-gray-300, #dee2e6);
  border-radius: 14px;
  background: var(--bt-white, #fff);
  color: var(--bt-gray-700, #495057);
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 6px;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  transition: all 0.15s;
  min-width: 48px;
}

.btn-back:active {
  background: var(--bt-gray-100, #f8f9fa);
  transform: scale(0.97);
}

.btn-next,
.btn-create {
  flex: 1;
  height: 56px;
  border: none;
  border-radius: 14px;
  background: var(--bt-primary, #0d6efd);
  color: var(--bt-white, #fff);
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  transition: all 0.15s;
  min-width: 48px;
}

.btn-next:active:not(:disabled),
.btn-create:active:not(:disabled) {
  background: #0b5ed7;
  transform: scale(0.97);
}

.btn-next:disabled,
.btn-create:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-create {
  background: var(--bt-success, #198754);
}

.btn-create:active:not(:disabled) {
  background: #157347;
}

/* 响应式：桌面端居中显示 */
@media (min-width: 768px) {
  .quick-ticket {
    padding: 24px;
    min-height: auto;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
    margin: 24px auto;
  }
}
</style>
