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

      <!-- PushPlus 推送 -->
      <div class="col-md-6">
        <div class="card p-2">
          <h5 class="mb-3"><i class="bi bi-send me-2"></i>PushPlus 推送</h5>
          <div class="mb-2">
            <label class="form-label small">Token</label>
            <input v-model="pushplusForm.token" class="form-control form-control-sm" placeholder="PushPlus Token">
          </div>
          <div class="mb-2">
            <label class="form-label small">主题（可选）</label>
            <input v-model="pushplusForm.topic" class="form-control form-control-sm" placeholder="推送主题">
          </div>
          <div class="d-flex gap-2">
            <button class="btn btn-sm btn-primary" @click="savePushplus" :disabled="savingPushplus">
              {{ savingPushplus ? '保存中...' : '保存' }}
            </button>
            <button class="btn btn-sm btn-outline-secondary" @click="testPushplus" :disabled="testingPushplus">
              {{ testingPushplus ? '发送中...' : '测试' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 企业微信推送 -->
      <div class="col-md-6">
        <div class="card p-2">
          <h5 class="mb-3"><i class="bi bi-chat-dots me-2"></i>企业微信推送</h5>
          <div class="mb-2">
            <label class="form-label small">Webhook Key</label>
            <input v-model="wecomForm.key" class="form-control form-control-sm" placeholder="企微 Webhook Key">
          </div>
          <div class="mb-2">
            <label class="form-label small">备注（可选）</label>
            <input v-model="wecomForm.remark" class="form-control form-control-sm" placeholder="配置备注">
          </div>
          <div class="d-flex gap-2">
            <button class="btn btn-sm btn-primary" @click="saveWecom" :disabled="savingWecom">
              {{ savingWecom ? '保存中...' : '保存' }}
            </button>
            <button class="btn btn-sm btn-outline-secondary" @click="testWecom" :disabled="testingWecom">
              {{ testingWecom ? '发送中...' : '测试' }}
            </button>
          </div>
        </div>
      </div>

      <div class="col-12">
        <div class="card p-2">
          <ul class="nav nav-tabs mb-3" role="tablist">
            <li class="nav-item" role="presentation">
              <button class="nav-link" :class="activeTab === 'rules' ? 'active' : ''"
                      @click="activeTab = 'rules'" role="tab">
                <i class="bi bi-lightning me-1"></i>自动化规则
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" :class="activeTab === 'templates' ? 'active' : ''"
                      @click="activeTab = 'templates'; loadTemplates()" role="tab">
                <i class="bi bi-file-earmark-text me-1"></i>模板管理
              </button>
            </li>
          </ul>

          <div v-if="activeTab === 'rules'">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="mb-0"><i class="bi bi-lightning me-2"></i>自动化规则</h5>
              <div class="d-flex gap-2">
                <button class="btn btn-sm btn-outline-secondary" @click="seedRules" :disabled="rulesLoading">
                  <i class="bi bi-magic me-1"></i>初始化默认
                </button>
                <button class="btn btn-sm btn-primary" @click="openRuleForm()">
                  <i class="bi bi-plus-lg me-1"></i>新建规则
                </button>
              </div>
            </div>

            <div v-if="rulesLoading" class="text-center py-3">
              <div class="spinner-border spinner-border-sm text-primary"></div>
            </div>

            <div v-else-if="rules.length === 0" class="text-center py-4 text-muted">
              <i class="bi bi-lightning" style="font-size:32px"></i>
              <p class="mt-2 mb-1">暂无自动化规则</p>
              <small>点击「初始化默认」生成常用规则，或手动新建</small>
            </div>

            <div v-else class="table-responsive">
              <table class="bt-table">
                <thead>
                  <tr>
                    <th>规则名称</th>
                    <th>触发事件</th>
                    <th>动作</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="rule in rules" :key="rule.id">
                    <td><strong>{{ rule.name }}</strong><br><small class="text-muted">{{ rule.description || '' }}</small></td>
                    <td><span class="badge bg-info">{{ rule.event_type }}</span></td>
                    <td><span class="badge bg-secondary">{{ rule.action_type }}</span></td>
                    <td>
                      <button class="btn btn-sm" :class="rule.enabled !== false ? 'btn-success' : 'btn-outline-secondary'"
                              @click="toggleRule(rule)">
                        {{ rule.enabled !== false ? '已启用' : '已禁用' }}
                      </button>
                    </td>
                    <td>
                      <div class="d-flex gap-1">
                        <button class="btn btn-sm btn-outline-primary" @click="openRuleForm(rule)"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger" @click="deleteRuleConfirm(rule)"><i class="bi bi-trash"></i></button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="activeTab === 'templates'">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="mb-0"><i class="bi bi-file-earmark-text me-2"></i>模板管理</h5>
              <button class="btn btn-sm btn-primary" @click="openTemplateForm()">
                <i class="bi bi-plus-lg me-1"></i>新建模板
              </button>
            </div>

            <div v-if="templatesLoading" class="text-center py-3">
              <div class="spinner-border spinner-border-sm text-primary"></div>
            </div>

            <div v-else-if="templates.length === 0" class="text-center py-4 text-muted">
              <i class="bi bi-file-earmark-text" style="font-size:32px"></i>
              <p class="mt-2 mb-1">暂无工单模板</p>
              <small>点击「新建模板」创建常用工单模板</small>
            </div>

            <div v-else class="table-responsive">
              <table class="bt-table">
                <thead>
                  <tr>
                    <th>模板名称</th>
                    <th>描述</th>
                    <th>状态</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="tpl in templates" :key="tpl.id">
                    <td><strong>{{ tpl.name }}</strong></td>
                    <td><small class="text-muted">{{ tpl.description || '-' }}</small></td>
                    <td>
                      <button class="btn btn-sm" :class="tpl.is_active !== false ? 'btn-success' : 'btn-outline-secondary'"
                              @click="toggleTemplate(tpl)">
                        {{ tpl.is_active !== false ? '已启用' : '已禁用' }}
                      </button>
                    </td>
                    <td><small class="text-muted">{{ tpl.created_at ? tpl.created_at.slice(0, 10) : '-' }}</small></td>
                    <td>
                      <div class="d-flex gap-1">
                        <button class="btn btn-sm btn-outline-primary" @click="openTemplateForm(tpl)"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger" @click="deleteTemplateConfirm(tpl)"><i class="bi bi-trash"></i></button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 规则编辑弹窗 -->
    <Teleport to="body">
      <div class="modal fade" id="ruleModal" tabindex="-1" ref="ruleModalEl">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title"><i class="bi bi-lightning me-2"></i>{{ ruleForm.id ? '编辑规则' : '新建规则' }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">规则名称 <span class="text-danger">*</span></label>
                <input class="form-control" v-model="ruleForm.name" placeholder="如：工单超时提醒">
              </div>
              <div class="mb-3">
                <label class="form-label">描述</label>
                <input class="form-control" v-model="ruleForm.description" placeholder="规则说明（可选）">
              </div>
              <div class="row g-2 mb-3">
                <div class="col-6">
                  <label class="form-label">触发事件 <span class="text-danger">*</span></label>
                  <select class="form-select" v-model="ruleForm.event_type">
                    <option value="">选择事件...</option>
                    <option value="ticket_created">工单创建</option>
                    <option value="ticket_completed">工单完工</option>
                    <option value="ticket_overdue">工单超时</option>
                    <option value="payment_received">收款确认</option>
                    <option value="equipment_maintenance">设备维保到期</option>
                    <option value="inventory_low">库存预警</option>
                    <option value="daily_digest">每日摘要</option>
                  </select>
                </div>
                <div class="col-6">
                  <label class="form-label">执行动作 <span class="text-danger">*</span></label>
                  <select class="form-select" v-model="ruleForm.action_type">
                    <option value="">选择动作...</option>
                    <option value="send_notification">发送通知</option>
                    <option value="update_status">更新状态</option>
                    <option value="create_reminder">创建提醒</option>
                    <option value="send_pushplus">PushPlus推送</option>
                    <option value="send_wecom">企微推送</option>
                  </select>
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">条件（JSON，可选）</label>
                <textarea class="form-control font-monospace" v-model="ruleForm.condition" rows="3"
                          placeholder='{"priority": "H"}'></textarea>
                <small class="text-muted">留空表示无条件触发</small>
              </div>
              <div class="mb-3">
                <label class="form-label">动作配置（JSON，可选）</label>
                <textarea class="form-control font-monospace" v-model="ruleForm.action_config" rows="3"
                          placeholder='{"template": "工单{{ticket_no}}需要处理"}'></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
              <button class="btn btn-primary" @click="saveRule" :disabled="savingRule">
                {{ savingRule ? '保存中...' : '保存规则' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 模板编辑弹窗 -->
    <Teleport to="body">
      <div class="modal fade" id="templateModal" tabindex="-1" ref="templateModalEl">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title"><i class="bi bi-file-earmark-text me-2"></i>{{ templateForm.id ? '编辑模板' : '新建模板' }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">模板名称 <span class="text-danger">*</span></label>
                <input class="form-control" v-model="templateForm.name" placeholder="如：网络故障模板">
              </div>
              <div class="mb-3">
                <label class="form-label">描述</label>
                <input class="form-control" v-model="templateForm.description" placeholder="模板说明（可选）">
              </div>
              <div class="mb-3">
                <label class="form-label">模板内容 <span class="text-danger">*</span></label>
                <textarea class="form-control font-monospace" v-model="templateForm.content" rows="6"
                          placeholder="工单模板内容，支持变量如 {{client_name}}、{{description}} 等"></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
              <button class="btn btn-primary" @click="saveTemplate" :disabled="savingTemplate">
                {{ savingTemplate ? '保存中...' : '保存模板' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

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
import { pushplusApi } from '@/api/pushplus'
import { wecomApi } from '@/api/wecom'
import { toolsApi } from '@/api/tools'
import { Modal } from 'bootstrap'

const router = useRouter()
const app = useAppStore()
const auth = useAuthStore()
const { show: showToast } = useToast()
const { confirm, visible, message, onConfirm, onCancel } = useConfirm()

const activeTab = ref('rules')

const showChangePwd = ref(false)
const changingPwd = ref(false)
const pwdModalEl = ref(null)

const pwdForm = ref({ oldPwd: '', newPwd: '', confirmPwd: '' })
let bsPwdModal = null

// PushPlus
const pushplusForm = ref({ token: '', topic: '' })
const savingPushplus = ref(false)
const testingPushplus = ref(false)

// WeCom
const wecomForm = ref({ key: '', remark: '' })
const savingWecom = ref(false)
const testingWecom = ref(false)

// Rules
const rules = ref([])
const rulesLoading = ref(false)
const savingRule = ref(false)
const ruleModalEl = ref(null)
const ruleForm = ref({ id: null, name: '', description: '', event_type: '', action_type: '', condition: '', action_config: '' })
let bsRuleModal = null

const templates = ref([])
const templatesLoading = ref(false)
const savingTemplate = ref(false)
const templateModalEl = ref(null)
const templateForm = ref({ id: null, name: '', description: '', content: '' })
let bsTemplateModal = null
let templatesLoaded = false

onMounted(() => {
  if (pwdModalEl.value) {
    bsPwdModal = new Modal(pwdModalEl.value)
    pwdModalEl.value.addEventListener('hidden.bs.modal', () => {
      showChangePwd.value = false
      pwdForm.value = { oldPwd: '', newPwd: '', confirmPwd: '' }
    })
  }
  loadPushplusConfig()
  loadWecomConfig()
  loadRules()

  if (ruleModalEl.value) {
    bsRuleModal = new Modal(ruleModalEl.value)
  }

  if (templateModalEl.value) {
    bsTemplateModal = new Modal(templateModalEl.value)
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
    const result = await authApi.changePassword({
      old_password: oldPwd,
      new_password: newPwd,
    })
    if (result.error) { showToast(result.error, 'danger'); return }
    showToast((result.message || '密码修改成功') + '，3秒后跳转登录页', 'success')
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

// ── PushPlus ──
async function loadPushplusConfig() {
  try {
    const data = await pushplusApi.getConfig()
    pushplusForm.value = { token: data?.token || '', topic: data?.topic || '' }
  } catch (e) { /* 404 = 未配置，忽略 */ }
}

async function savePushplus() {
  savingPushplus.value = true
  try {
    await pushplusApi.updateConfig(pushplusForm.value)
    showToast('PushPlus 配置已保存', 'success')
  } catch (e) { showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { savingPushplus.value = false }
}

async function testPushplus() {
  testingPushplus.value = true
  try {
    await pushplusApi.sendTest()
    showToast('测试消息已发送', 'success')
  } catch (e) { showToast('发送失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { testingPushplus.value = false }
}

// ── WeCom ──
async function loadWecomConfig() {
  try {
    const data = await wecomApi.getConfig()
    wecomForm.value = { key: data?.key || '', remark: data?.remark || '' }
  } catch (e) { /* 404 = 未配置 */ }
}

async function saveWecom() {
  savingWecom.value = true
  try {
    await wecomApi.updateConfig(wecomForm.value)
    showToast('企业微信配置已保存', 'success')
  } catch (e) { showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { savingWecom.value = false }
}

async function testWecom() {
  testingWecom.value = true
  try {
    await wecomApi.sendTest()
    showToast('测试消息已发送', 'success')
  } catch (e) { showToast('发送失败: ' + (e.response?.data?.error || e.message), 'danger') }
  finally { testingWecom.value = false }
}

// ── Automation Rules ──
async function loadRules() {
  rulesLoading.value = true
  try {
    const data = await toolsApi.listRules()
    rules.value = data.rules || data || []
  } catch (e) { rules.value = [] }
  finally { rulesLoading.value = false }
}

function openRuleForm(rule = null) {
  if (rule) {
    ruleForm.value = {
      id: rule.id,
      name: rule.name || '',
      description: rule.description || '',
      event_type: rule.event_type || '',
      action_type: rule.action_type || '',
      condition: typeof rule.condition === 'string' ? rule.condition : JSON.stringify(rule.condition || {}, null, 2),
      action_config: typeof rule.action_config === 'string' ? rule.action_config : JSON.stringify(rule.action_config || {}, null, 2),
    }
  } else {
    ruleForm.value = { id: null, name: '', description: '', event_type: '', action_type: '', condition: '', action_config: '' }
  }
  if (!bsRuleModal && ruleModalEl.value) {
    bsRuleModal = new Modal(ruleModalEl.value)
  }
  bsRuleModal?.show()
}

async function saveRule() {
  const f = ruleForm.value
  if (!f.name || !f.event_type || !f.action_type) {
    showToast('请填写规则名称、触发事件和执行动作', 'warning')
    return
  }
  savingRule.value = true
  try {
    const payload = {
      name: f.name,
      description: f.description || undefined,
      event_type: f.event_type,
      action_type: f.action_type,
      condition: f.condition ? JSON.parse(f.condition) : undefined,
      action_config: f.action_config ? JSON.parse(f.action_config) : undefined,
    }
    if (f.id) {
      await toolsApi.updateRule(f.id, payload)
    } else {
      await toolsApi.createRule(payload)
    }
    showToast(f.id ? '规则已更新' : '规则已创建', 'success')
    bsRuleModal?.hide()
    loadRules()
  } catch (e) {
    const msg = e instanceof SyntaxError ? 'JSON 格式错误' : (e.response?.data?.error || e.message)
    showToast('保存失败: ' + msg, 'danger')
  } finally {
    savingRule.value = false
  }
}

async function toggleRule(rule) {
  try {
    await toolsApi.toggleRule(rule.id)
    showToast(rule.enabled !== false ? '规则已禁用' : '规则已启用', 'success')
    loadRules()
  } catch (e) { showToast('操作失败', 'danger') }
}

async function deleteRuleConfirm(rule) {
  if (await confirm(`确定要删除规则「${rule.name}」吗？`)) {
    try {
      await toolsApi.deleteRule(rule.id)
      showToast('规则已删除', 'success')
      loadRules()
    } catch (e) { showToast('删除失败', 'danger') }
  }
}

async function seedRules() {
  rulesLoading.value = true
  try {
    const data = await toolsApi.seedRules()
    showToast(data.message || '默认规则已初始化', 'success')
    loadRules()
  } catch (e) {
    showToast('初始化失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    rulesLoading.value = false
  }
}

async function loadTemplates() {
  if (templatesLoaded) return
  templatesLoading.value = true
  try {
    const data = await toolsApi.listTemplates()
    templates.value = data.templates || data || []
    templatesLoaded = true
  } catch (e) { templates.value = [] }
  finally { templatesLoading.value = false }
}

function openTemplateForm(tpl = null) {
  if (tpl) {
    templateForm.value = {
      id: tpl.id,
      name: tpl.name || '',
      description: tpl.description || '',
      content: tpl.content || '',
    }
  } else {
    templateForm.value = { id: null, name: '', description: '', content: '' }
  }
  if (!bsTemplateModal && templateModalEl.value) {
    bsTemplateModal = new Modal(templateModalEl.value)
  }
  bsTemplateModal?.show()
}

async function saveTemplate() {
  const f = templateForm.value
  if (!f.name || !f.content) {
    showToast('请填写模板名称和内容', 'warning')
    return
  }
  savingTemplate.value = true
  try {
    const payload = {
      name: f.name,
      description: f.description || undefined,
      content: f.content,
    }
    if (f.id) {
      await toolsApi.updateTemplate(f.id, payload)
    } else {
      await toolsApi.createTemplate(payload)
    }
    showToast(f.id ? '模板已更新' : '模板已创建', 'success')
    bsTemplateModal?.hide()
    templatesLoaded = false
    loadTemplates()
  } catch (e) {
    showToast('保存失败: ' + (e.response?.data?.error || e.message), 'danger')
  } finally {
    savingTemplate.value = false
  }
}

async function toggleTemplate(tpl) {
  try {
    await toolsApi.updateTemplate(tpl.id, { is_active: !tpl.is_active })
    showToast(tpl.is_active !== false ? '模板已禁用' : '模板已启用', 'success')
    templatesLoaded = false
    loadTemplates()
  } catch (e) { showToast('操作失败', 'danger') }
}

async function deleteTemplateConfirm(tpl) {
  if (await confirm(`确定要删除模板「${tpl.name}」吗？`)) {
    try {
      await toolsApi.deleteTemplate(tpl.id)
      showToast('模板已删除', 'success')
      templatesLoaded = false
      loadTemplates()
    } catch (e) { showToast('删除失败', 'danger') }
  }
}
</script>
