<template>
  <div class="login-page">
    <div class="login-bg-circle c1"></div>
    <div class="login-bg-circle c2"></div>
    <div class="login-bg-circle c3"></div>

    <div class="login-wrapper">
      <div class="login-card">
        <div class="login-brand">
          <div class="login-brand-icon">捷</div>
          <h4>博通 Botong</h4>
          <p>售后管理系统 · 请输入访问密码</p>
        </div>

        <div v-if="error" class="login-error">
          <i class="bi bi-shield-exclamation"></i>
          <span>{{ error }}</span>
        </div>

        <form class="login-form" @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="pwdInput">访问密码</label>
            <div class="input-wrapper">
              <input
                class="form-control"
                id="pwdInput"
                v-model="password"
                :type="showPwd ? 'text' : 'password'"
                placeholder="请输入系统密码"
                required
                autofocus
              />
              <button type="button" class="toggle-pwd" @click="showPwd = !showPwd">
                <i :class="showPwd ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
              </button>
            </div>
          </div>
          <button type="submit" class="btn-submit" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            <span v-else class="btn-text"><i class="bi bi-box-arrow-in-right me-1"></i>进入系统</span>
          </button>
        </form>

        <div class="login-footer">
          <small><i class="bi bi-lock"></i>仅限内部网络访问</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const password = ref('')
const showPwd = ref(false)
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!password.value) {
    error.value = '请输入密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const data = await auth.login(password.value)
    if (data.ok) {
      router.push({ name: 'Dashboard' })
    } else {
      error.value = data.error || '密码错误，请重试'
    }
  } catch (e) {
    error.value = '登录失败: ' + (e.response?.data?.error || e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bt-body-bg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  padding: 16px;
  position: relative;
  overflow-x: hidden;
}

.login-bg-circle {
  position: fixed;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}
.c1 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
  top: -100px; right: -100px;
  animation: float1 8s ease-in-out infinite;
}
.c2 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(16,185,129,0.08) 0%, transparent 70%);
  bottom: -80px; left: -80px;
  animation: float2 10s ease-in-out infinite;
}
.c3 {
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(245,158,11,0.06) 0%, transparent 70%);
  top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  animation: float3 12s ease-in-out infinite;
}
@keyframes float1 {
  0%,100% { transform: translate(0,0); }
  50% { transform: translate(-30px,30px); }
}
@keyframes float2 {
  0%,100% { transform: translate(0,0); }
  50% { transform: translate(30px,-30px); }
}
@keyframes float3 {
  0%,100% { transform: translate(-50%,-50%) scale(1); }
  50% { transform: translate(-50%,-50%) scale(1.1); }
}

.login-wrapper { position: relative; z-index: 1; width: 100%; max-width: 400px; }
.login-card {
  background: var(--card-bg); border-radius: 16px; padding: 40px 36px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 10px 40px -5px rgba(0,0,0,0.08);
  border: 1px solid var(--bt-gray-200);
  animation: loginIn 0.5s ease;
}
@keyframes loginIn {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.login-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--bt-primary-400), var(--bt-primary), var(--bt-primary-600));
}

.login-brand { text-align: center; margin-bottom: 32px; }
.login-brand-icon {
  width: 64px; height: 64px; border-radius: 16px;
  background: linear-gradient(135deg, var(--bt-primary), var(--bt-primary-600));
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px; font-size: 28px; color: white; font-weight: 700;
  box-shadow: 0 4px 16px rgba(99,102,241,0.25);
}
.login-brand h4 { font-weight: 700; color: var(--bt-text-heading); font-size: 20px; margin-bottom: 4px; }
.login-brand p { color: var(--bt-text-muted); font-size: 13px; margin: 0; }

.login-form .form-group { margin-bottom: 20px; }
.login-form label { font-size: 13px; font-weight: 500; color: var(--bt-text-body); margin-bottom: 6px; display: block; }
.login-form .input-wrapper { position: relative; }
.login-form .input-wrapper .form-control {
  height: 48px; padding: 10px 40px 10px 14px; border-radius: 10px;
  border: 1.5px solid var(--bt-gray-200); font-size: 15px;
  transition: all 0.2s ease; background: var(--bt-gray-50);
  color: var(--bt-text-body);
}
.login-form .input-wrapper .form-control:focus {
  border-color: var(--bt-primary); background: var(--card-bg);
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
}
.login-form .input-wrapper .form-control::placeholder {
  color: var(--bt-gray-400);
}
.login-form .input-wrapper .toggle-pwd {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: var(--bt-gray-400);
  cursor: pointer; padding: 8px; font-size: 16px;
}

.btn-submit {
  width: 100%; height: 48px; border-radius: 10px;
  background: linear-gradient(135deg, var(--bt-primary), var(--bt-primary-600));
  border: none; color: white; font-size: 15px; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-submit:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(99,102,241,0.35); }
.btn-submit:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
.spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
  border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.login-error {
  background: var(--bt-danger-light); border: 1px solid var(--bt-danger); border-radius: 10px;
  padding: 12px 16px; margin-bottom: 20px; display: flex;
  align-items: center; gap: 10px; font-size: 13px; color: var(--bt-danger-dark);
}
.login-error i { font-size: 18px; color: var(--bt-danger); }

.login-footer { text-align: center; margin-top: 24px; }
.login-footer small { color: var(--bt-text-muted); font-size: 11px; }

[data-theme="dark"] .login-bg-circle.c1 {
  background: radial-gradient(circle, rgba(129,140,248,0.15) 0%, transparent 70%);
}
[data-theme="dark"] .login-bg-circle.c2 {
  background: radial-gradient(circle, rgba(34,197,94,0.1) 0%, transparent 70%);
}
[data-theme="dark"] .login-bg-circle.c3 {
  background: radial-gradient(circle, rgba(245,158,11,0.08) 0%, transparent 70%);
}
[data-theme="dark"] .login-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.3), 0 10px 40px -5px rgba(0,0,0,0.3);
}
[data-theme="dark"] .login-card::before {
  background: linear-gradient(90deg, var(--bt-primary-300), var(--bt-primary), var(--bt-primary-500));
}
[data-theme="dark"] .login-brand-icon {
  background: linear-gradient(135deg, var(--bt-primary), var(--bt-primary-500));
  box-shadow: 0 4px 16px rgba(129,140,248,0.3);
}
[data-theme="dark"] .login-form .input-wrapper .form-control {
  background: var(--bt-gray-100);
}
[data-theme="dark"] .btn-submit {
  background: linear-gradient(135deg, var(--bt-primary), var(--bt-primary-500));
}
[data-theme="dark"] .btn-submit:hover {
  box-shadow: 0 4px 16px rgba(129,140,248,0.4);
}
</style>