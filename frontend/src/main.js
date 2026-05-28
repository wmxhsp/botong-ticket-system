import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Global styles (will be replaced by our custom CSS)
import './assets/styles/main.css'

// Chart.js plugin registration (must run before any Chart usage)
import './plugins/chart.js'

const app = createApp(App)

// Global error handler — catch component errors, show toast instead of white screen
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue Error]', err, info)
  window.dispatchEvent(new CustomEvent('api-error', {
    detail: { message: '页面出现异常，请刷新重试' }
  }))
}

app.use(createPinia())
app.use(router)
app.mount('#app')
