import { defineStore } from 'pinia'
import { ref, Ref } from 'vue'

export type Theme = 'light' | 'dark' | 'auto'

export interface AppState {
  sidebarMobileOpen: Ref<boolean>
  theme: Ref<Theme>
  pageTitle: Ref<string>
  toggleSidebar: () => void
  setTheme: (newTheme: Theme) => void
  toggleTheme: () => void
}

export const useAppStore = defineStore('app', (): AppState => {
  const sidebarMobileOpen = ref(false)
  const theme = ref<Theme>((localStorage.getItem('bt_theme') as Theme) || 'auto')
  const pageTitle = ref('仪表盘')

  function toggleSidebar(): void {
    if (window.innerWidth < 993) {
      sidebarMobileOpen.value = !sidebarMobileOpen.value
    }
  }

  function setTheme(newTheme: Theme): void {
    theme.value = newTheme
    localStorage.setItem('bt_theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  function toggleTheme(): void {
    if (theme.value === 'dark') setTheme('light')
    else if (theme.value === 'light') setTheme('auto')
    else setTheme('dark')
  }

  return { sidebarMobileOpen, theme, pageTitle, toggleSidebar, setTheme, toggleTheme }
})
