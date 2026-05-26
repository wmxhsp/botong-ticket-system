import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const sidebarMobileOpen = ref(false)
  const theme = ref(localStorage.getItem('bt_theme') || 'auto')
  const pageTitle = ref('仪表盘')

  function toggleSidebar() {
    if (window.innerWidth < 993) {
      sidebarMobileOpen.value = !sidebarMobileOpen.value
    } else {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }
  }

  function setTheme(newTheme) {
    theme.value = newTheme
    localStorage.setItem('bt_theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  function toggleTheme() {
    if (theme.value === 'dark') setTheme('light')
    else if (theme.value === 'light') setTheme('auto')
    else setTheme('dark')
  }

  return { sidebarCollapsed, sidebarMobileOpen, theme, pageTitle, toggleSidebar, setTheme, toggleTheme }
})
