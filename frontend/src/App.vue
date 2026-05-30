<template>
  <router-view v-slot="{ Component, route }">
    <transition name="page-fade" mode="out-in">
      <KeepAlive :include="KEEP_ALIVE_NAMES">
        <component :is="Component" :key="route.path" />
      </KeepAlive>
    </transition>
  </router-view>
  <ToastContainer />
  <ConfirmDialog
    :visible="confirmVisible"
    :title="confirmConfig.title"
    :message="confirmConfig.message"
    :type="confirmConfig.type"
    :confirm-text="confirmConfig.confirmText"
    :show-input="confirmConfig.showInput"
    :input-placeholder="confirmConfig.inputPlaceholder"
    @confirm="handleConfirm"
    @cancel="handleCancel"
  />
  <CommandPalette />
  <KeyboardShortcuts ref="shortcutsRef" />
</template>

<script setup>
import { onMounted, onUnmounted, watch, ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { useRoute, useRouter } from 'vue-router'
import { fetchCsrfToken } from '@/api/client'
import ToastContainer from '@/components/common/ToastContainer.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import CommandPalette from '@/components/common/CommandPalette.vue'
import KeyboardShortcuts from '@/components/common/KeyboardShortcuts.vue'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { useCommandPalette } from '@/composables/useCommandPalette'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { KEEP_ALIVE_NAMES } from '@/constants/keepAlive'

const app = useAppStore()
const route = useRoute()
const router = useRouter()
const { show: showToast } = useToast()
const { visible: confirmVisible, config: confirmConfig, onConfirm: handleConfirm, onCancel: handleCancel } = useConfirm()
const { toggle: toggleCommandPalette } = useCommandPalette()
const { setupGlobalShortcuts, navigateTo } = useKeyboardShortcuts()
const shortcutsRef = ref(null)

const PAGE_TITLES = {
  'Login': '登录 - 博通',
  'Dashboard': '仪表盘 - 博通',
  'Tickets': '工单管理 - 博通',
  'TicketCreate': '新建工单 - 博通',
  'TicketDetail': '工单详情 - 博通',
  'Clients': '客户管理 - 博通',
  'ClientDetail': '客户详情 - 博通',
  'Equipment': '设备管理 - 博通',
  'EquipmentDetail': '设备详情 - 博通',
  'Finance': '财务管理 - 博通',
  'Settings': '系统设置 - 博通',
  'Stats': '统计分析 - 博通',
  'NotFound': '404 - 博通',
}

watch(() => route.name, (name) => {
  document.title = PAGE_TITLES[name] || '博通 - 售后管理系统'
})

onMounted(() => {
  document.documentElement.setAttribute('data-theme', app.theme)
  document.title = PAGE_TITLES[route.name] || '博通 - 售后管理系统'
  fetchCsrfToken()

  const mqHandler = () => {
    if (app.theme === 'auto') {
      document.documentElement.setAttribute('data-theme', 'auto')
    }
  }
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  mq.addEventListener('change', mqHandler)

  const apiErrorHandler = (event) => {
    showToast(event.detail.message, 'danger')
  }
  window.addEventListener('api-error', apiErrorHandler)

  setupGlobalShortcuts({
    onSearch: () => {
      toggleCommandPalette()
    },
    onNewTicket: () => {
      navigateTo('/tickets/new')
    },
    onQuickSettle: () => {
      showToast('快速结算：请先在工单列表选择工单', 'info', 3000)
    },
    onTodayView: () => {
      navigateTo('/')
    },
    onHelp: () => {
      shortcutsRef.value?.show()
    },
  })

  onUnmounted(() => {
    mq.removeEventListener('change', mqHandler)
    window.removeEventListener('api-error', apiErrorHandler)
  })
})
</script>

<style>
.page-fade-enter-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
