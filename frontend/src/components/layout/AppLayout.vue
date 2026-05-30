<template>
  <div class="app-container">
    <div class="app-sidebar">
      <AppSidebar />
    </div>
    <div class="app-main">
      <AppTopBar />
      <main class="app-content" ref="contentRef">
        <router-view />
      </main>
    </div>

    <NLPanel />

    <div class="bt-mobile-bottom-nav" id="mobileBottomNav">
      <router-link :to="{name: 'Dashboard'}" class="nav-item" title="首页">
        <i class="bi bi-speedometer2"></i><span>首页</span>
      </router-link>
      <router-link :to="{name: 'Tickets'}" class="nav-item" title="工单">
        <i class="bi bi-ticket-perforated"></i><span>工单</span>
      </router-link>
      <router-link :to="{name: 'TicketCreate'}" class="nav-item new" title="新建">
        <i class="bi bi-plus-circle-fill"></i><span>新建</span>
      </router-link>
      <router-link :to="{name: 'InventoryList'}" class="nav-item" title="配件">
        <i class="bi bi-box-seam"></i><span>配件</span>
      </router-link>
      <router-link :to="{name: 'Finance'}" class="nav-item" title="财务">
        <i class="bi bi-cash-coin"></i><span>财务</span>
      </router-link>
      <router-link :to="{name: 'SettingsPage'}" class="nav-item" title="更多">
        <i class="bi bi-grid-3x3-gap"></i><span>更多</span>
      </router-link>
    </div>

    <button class="bt-scroll-top" id="scrollTopBtn"
            :class="{ show: showScrollTop }"
            @click="scrollToTop" title="返回顶部">
      <i class="bi bi-chevron-up"></i>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import AppSidebar from './AppSidebar.vue'
import AppTopBar from './AppTopBar.vue'
import NLPanel from '@/components/common/NLPanel.vue'

const app = useAppStore()
const showScrollTop = ref(false)
const contentRef = ref(null)
let scrollHandler = null

onMounted(() => {
  scrollHandler = () => {
    showScrollTop.value = window.scrollY > 300 || (contentRef.value?.scrollTop || 0) > 300
  }
  window.addEventListener('scroll', scrollHandler, { passive: true })
  if (contentRef.value) {
    contentRef.value.addEventListener('scroll', scrollHandler, { passive: true })
  }
})

onUnmounted(() => {
  window.removeEventListener('scroll', scrollHandler)
  if (contentRef.value) {
    contentRef.value.removeEventListener('scroll', scrollHandler)
  }
})

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
  contentRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<style scoped>
.app-container { display: flex; min-height: 100vh; background: var(--bt-body-bg); }
.app-sidebar { flex-shrink: 0; }
.app-main {
  flex: 1; display: flex; flex-direction: column;
  min-width: 0;
  margin-left: 48px;
}
.app-content { flex: 1; padding: 12px 14px 14px; }

@media (max-width: 992px) {
  body { padding-bottom: 52px; }
  .app-sidebar { display: none; }
  .app-main {
    margin-left: 0;
    width: 100%;
  }
  .bt-mobile-bottom-nav {
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 9998;
    background: var(--card-bg);
    display: flex; align-items: center; justify-content: space-around;
    padding: 2px 0 6px;
    border-top: 1px solid var(--card-border);
  }
  [data-theme="dark"] .bt-mobile-bottom-nav { background: var(--card-bg); border-top-color: var(--card-border); }

  .bt-mobile-bottom-nav .nav-item {
    display: flex; flex-direction: column; align-items: center;
    text-decoration: none; color: var(--bt-gray-400);
    font-size: 10px; padding: 2px 2px; min-width: 0;
    flex: 1;
    transition: color 0.15s ease;
  }
  .bt-mobile-bottom-nav .nav-item i { font-size: 17px; margin-bottom: 1px; }
  .bt-mobile-bottom-nav .nav-item.active { color: #6366f1; }
  .bt-mobile-bottom-nav .nav-item.new i { font-size: 22px; color: #6366f1; }
  .bt-mobile-bottom-nav .nav-item.new span { color: #6366f1; font-weight: 600; }

  /* 超小屏幕进一步压缩 */
  @media (max-width: 360px) {
    .bt-mobile-bottom-nav .nav-item { font-size: 9px; padding: 2px 1px; }
    .bt-mobile-bottom-nav .nav-item i { font-size: 15px; }
    .bt-mobile-bottom-nav .nav-item.new i { font-size: 20px; }
  }
}

@media (min-width: 993px) {
  .bt-mobile-bottom-nav { display: none; }
}

.bt-scroll-top {
  position: fixed; bottom: 80px; right: 20px; z-index: 9996;
  width: 40px; height: 40px; border-radius: 50%;
  background: var(--bt-gray-700); color: white; border: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; cursor: pointer;
  opacity: 0; pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  transform: translateY(10px);
}
.bt-scroll-top.show { opacity: 0.7; pointer-events: auto; transform: translateY(0); }
.bt-scroll-top.show:hover { opacity: 1; }
[data-theme="dark"] .bt-scroll-top { background: var(--card-border); }

@media (min-width: 993px) {
  .bt-scroll-top { display: none; }
}
</style>
