<template>
  <Teleport to="body">
    <!-- Toggle button -->
    <button class="bt-nl-toggle" @click="togglePanel" :title="open ? '关闭AI助手' : 'AI助手'">
      <i :class="open ? 'bi bi-x-lg' : 'bi bi-robot'"></i>
    </button>

    <!-- Panel -->
    <div class="bt-nl-panel" :class="{ open }">
      <div class="bt-nl-header">
        <i class="bi bi-robot me-2"></i>AI 助手
        <button class="btn-close" @click="open = false"></button>
      </div>

      <div class="bt-nl-messages" ref="messagesRef">
        <div v-for="(msg, i) in messages" :key="i" class="bt-nl-msg" :class="msg.role">
          <div class="bt-nl-msg-bubble" v-if="msg.html" v-html="msg.html"></div>
          <div class="bt-nl-msg-bubble" v-else>{{ msg.content }}</div>
        </div>
        <div v-if="processing" class="bt-nl-msg assistant">
          <div class="bt-nl-msg-bubble">
            <span class="bt-nl-typing">
              <span>.</span><span>.</span><span>.</span>
            </span>
          </div>
        </div>
      </div>

      <div class="bt-nl-input">
        <input v-model="input" @keydown.enter="send" placeholder="输入命令... (如：查看待处理工单)"
               :disabled="processing" class="form-control form-control-sm">
        <button class="btn btn-primary btn-sm" @click="send" :disabled="processing || !input.trim()">
          <i class="bi bi-send"></i>
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { nlApi } from '@/api/nl'

const router = useRouter()
const open = ref(false)
const input = ref('')
const processing = ref(false)
const messages = ref([
  { role: 'assistant', content: '你好！我是AI助手。\n你可以这样跟我说话：\n• "查看待处理的工单"\n• "创建工单 客户张三 维修电脑"\n• "本月收入多少"\n• "最近有什么通知"' },
])
const messagesRef = ref(null)

// Keyboard shortcut: Ctrl+Shift+A to toggle
let keyHandler = null
onMounted(() => {
  keyHandler = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
      togglePanel()
    }
  }
  document.addEventListener('keydown', keyHandler)
})
onUnmounted(() => {
  if (keyHandler) document.removeEventListener('keydown', keyHandler)
})

watch(open, async () => {
  await nextTick()
  scrollToBottom()
})

function togglePanel() {
  open.value = !open.value
}

const sanitizeUrl = (url) => {
  if (!url) return ''
  const allowed = /^[a-zA-Z0-9/_-]+$/
  const cleaned = url.replace(/[<>"'&]/g, '').trim()
  return allowed.test(cleaned) ? cleaned : ''
}

async function send() {
  const text = input.value.trim()
  if (!text || processing.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  processing.value = true
  await nextTick()
  scrollToBottom()

  try {
    const data = await nlApi.command({ command: text }).then(r => r.data)
    if (data.error) {
      messages.value.push({ role: 'assistant', content: '❌ ' + data.error })
    } else {
      let reply = data.message || data.summary || ''
      const safeUrl = sanitizeUrl(data.action_url)
      if (safeUrl) {
        messages.value.push({
          role: 'assistant',
          content: reply || '✅ 操作完成',
          html: reply + `<br><br><a href="${safeUrl}" class="btn btn-sm btn-primary mt-1" target="_blank" rel="noopener noreferrer">查看详情 &rarr;</a>`
        })
      } else if (data.data && Array.isArray(data.data) && data.data.length > 0) {
        messages.value.push({ role: 'assistant', content: reply + '\n共 ' + data.data.length + ' 条记录' })
      } else {
        messages.value.push({ role: 'assistant', content: reply || '✅ 操作完成' })
      }
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '❌ 请求失败: ' + e.message })
  } finally {
    processing.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}
</script>

<style scoped>
/* Toggle button */
.bt-nl-toggle {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 10001;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: white;
  border: none;
  box-shadow: 0 4px 16px rgba(99,102,241,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.bt-nl-toggle:hover { transform: scale(1.1); box-shadow: 0 6px 20px rgba(99,102,241,0.5); }

/* Panel */
.bt-nl-panel {
  position: fixed;
  bottom: 84px;
  right: 24px;
  z-index: 10000;
  width: 380px;
  max-width: calc(100vw - 48px);
  height: 500px;
  max-height: calc(100vh - 140px);
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  border: 1px solid var(--bt-gray-200);
  display: flex;
  flex-direction: column;
  transform: translateY(20px);
  opacity: 0;
  pointer-events: none;
  transition: all 0.25s ease;
}
.bt-nl-panel.open { transform: translateY(0); opacity: 1; pointer-events: auto; }
[data-theme="dark"] .bt-nl-panel { background: var(--card-bg); border-color: var(--card-border); }

.bt-nl-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--bt-gray-200);
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  color: var(--bt-text-heading);
}
.bt-nl-header .btn-close { margin-left: auto; }

.bt-nl-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bt-nl-msg { display: flex; }
.bt-nl-msg.user { justify-content: flex-end; }
.bt-nl-msg.assistant { justify-content: flex-start; }

.bt-nl-msg-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
}
.bt-nl-msg.user .bt-nl-msg-bubble {
  background: #6366f1;
  color: white;
  border-bottom-right-radius: 4px;
}
.bt-nl-msg.assistant .bt-nl-msg-bubble {
  background: var(--bt-gray-50);
  color: var(--bt-text-body);
  border-bottom-left-radius: 4px;
}
[data-theme="dark"] .bt-nl-msg.assistant .bt-nl-msg-bubble { background: var(--card-bg); }

.bt-nl-input {
  padding: 10px 12px;
  border-top: 1px solid var(--bt-gray-200);
  display: flex;
  gap: 8px;
}
.bt-nl-input input { flex: 1; }

.bt-nl-typing span {
  animation: btTyping 1.4s ease-in-out infinite;
  font-size: 24px;
  line-height: 0;
}
.bt-nl-typing span:nth-child(2) { animation-delay: 0.2s; }
.bt-nl-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes btTyping {
  0%,60%,100% { opacity: 0.3; }
  30% { opacity: 1; }
}

@media (max-width: 480px) {
  .bt-nl-toggle { bottom: 80px; right: 16px; }
  .bt-nl-panel { right: 8px; left: 8px; width: auto; height: 60vh; }
}
</style>
