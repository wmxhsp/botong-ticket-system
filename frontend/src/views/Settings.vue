<template>
  <div>
    <div class="bt-page-title">
      <h2>系统设置</h2>
      <p class="d-none d-md-inline">管理系统配置和偏好</p>
    </div>

    <div class="row g-2">
      <!-- 外观设置 -->
      <div class="col-md-6">
        <div class="card p-2">
          <h5 class="mb-3"><i class="bi bi-palette me-2"></i>外观设置</h5>
          <div class="mb-3">
            <label class="form-label">主题模式</label>
            <div class="d-flex gap-2 flex-wrap">
              <button class="btn btn-sm" :class="app.theme === 'light' ? 'btn-primary' : 'btn-outline-secondary'"
                      @click="app.setTheme('light')">
                <i class="bi bi-sun-fill me-1"></i> 亮色
              </button>
              <button class="btn btn-sm" :class="app.theme === 'dark' ? 'btn-primary' : 'btn-outline-secondary'"
                      @click="app.setTheme('dark')">
                <i class="bi bi-moon-fill me-1"></i> 暗色
              </button>
              <button class="btn btn-sm" :class="app.theme === 'auto' ? 'btn-primary' : 'btn-outline-secondary'"
                      @click="app.setTheme('auto')">
                <i class="bi bi-circle-half me-1"></i> 跟随系统
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 安全设置 -->
      <div class="col-md-6">
        <div class="card p-2">
          <h5 class="mb-3"><i class="bi bi-shield-lock me-2"></i>安全设置</h5>
          <div class="mb-3">
            <label class="form-label">访问密码</label>
            <p class="text-muted small mb-2">修改系统的访问密码，下次登录时生效</p>
            <button class="btn btn-outline-primary btn-sm" @click="showChangePwd = true">
              <i class="bi bi-key me-1"></i> 修改密码
            </button>
          </div>
          <hr>
          <div class="mb-0">
            <label class="form-label">退出登录</label>
            <p class="text-muted small mb-2">退出当前登录状态，需要重新输入密码</p>
            <button class="btn btn-outline-danger btn-sm" @click="confirmLogout">
              <i class="bi bi-box-arrow-right me-1"></i> 退出登录
            </button>
          </div>
        </div>
      </div>

      <!-- 关于 -->
      <div class="col-md-6">
        <div class="card p-2">
          <h5 class="mb-3"><i class="bi bi-info-circle me-2"></i>关于系统</h5>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-muted">系统名称</span><span>博通 Botong</span>
          </div>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-muted">版本</span><span>v4.0.0</span>
          </div>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-muted">前端框架</span><span>Vue 3 + Vite</span>
          </div>
          <div class="d-flex justify-content-between small">
            <span class="text-muted">后端框架</span><span>Flask + SQLite</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 密码修改弹窗 (使用 Bootstrap Modal) -->
    <Teleport to="body">
      <div class="modal fade" id="pwdModal" tabindex="-1" ref="pwdModalEl">
        <div class="modal-dialog modal-sm modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title"><i class="bi bi-shield-lock me-2"></i>修改密码</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">当前密码</label>
                <input class="form-control" v-model="pwdForm.oldPwd" type="password" placeholder="输入当前密码">
              </div>
              <div class="mb-3">
                <label class="form-label">新密码 <small class="text-muted">至少6位</small></label>
                <input class="form-control" v-model="pwdForm.newPwd" type="password" placeholder="输入新密码">
              </div>
              <div class="mb-3">
                <label class="form-label">确认新密码</label>
                <input class="form-control" v-model="pwdForm.confirmPwd" type="password" placeholder="再次输入">
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
              <button class="btn btn-primary" @click="changePassword" :disabled="changingPwd">
                {{ changingPwd ? '修改中...' : '确认修改' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <div v-if="visible" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,.5);z-index:1060">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-body"><p>{{ message }}</p></div>
          <div class="modal-footer">
            <button class="btn btn-secondary btn-sm" @click="onCancel">取消</button>
            <button class="btn btn-danger btn-sm" @click="onConfirm">确定</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { Modal } from 'bootstrap'

const router = useRouter()
const app = useAppStore()
const auth = useAuthStore()
const { show: showToast } = useToast()
const { confirm, visible, message, onConfirm, onCancel } = useConfirm()

const showChangePwd = ref(false)
const changingPwd = ref(false)
const pwdModalEl = ref(null)

const pwdForm = ref({ oldPwd: '', newPwd: '', confirmPwd: '' })
let bsPwdModal = null

onMounted(() => {
  if (pwdModalEl.value) {
    bsPwdModal = new Modal(pwdModalEl.value)
    pwdModalEl.value.addEventListener('hidden.bs.modal', () => {
      showChangePwd.value = false
      pwdForm.value = { oldPwd: '', newPwd: '', confirmPwd: '' }
    })
  }
})

watch(showChangePwd, async (val) => {
  await nextTick()
  if (val) {
    bsPwdModal?.show()
  } else {
    bsPwdModal?.hide()
  }
})

async function changePassword() {
  const { oldPwd, newPwd, confirmPwd } = pwdForm.value
  if (!oldPwd || !newPwd) { showToast('请填写完整', 'warning'); return }
  if (newPwd.length < 6) { showToast('新密码至少6位', 'warning'); return }
  if (newPwd !== confirmPwd) { showToast('两次输入不一致', 'warning'); return }

  changingPwd.value = true
  try {
    const { data } = await authApi.changePassword({
      old_password: oldPwd,
      new_password: newPwd,
    })
    if (data.error) { showToast(data.error, 'danger'); return }
    showToast((data.message || '密码修改成功') + '，3秒后跳转登录页', 'success')
    if (bsPwdModal) bsPwdModal.hide()
    setTimeout(async () => { await auth.logout(); router.push({ name: 'Login' }) }, 3000)
  } catch (e) {
    showToast(e.response?.data?.error || '修改失败', 'danger')
  } finally {
    changingPwd.value = false
  }
}

async function confirmLogout() {
  if (await confirm('确定要退出登录吗？')) {
    await auth.logout()
    router.push({ name: 'Login' })
  }
}
</script>
