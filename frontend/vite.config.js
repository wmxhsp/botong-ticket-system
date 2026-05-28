import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  test: {
    environment: 'happy-dom',
    globals: true,
    include: ['src/**/*.{test,spec}.{js,ts}'],
    coverage: {
      provider: 'v8',
      include: ['src/composables/**', 'src/api/client.js'],
    },
  },
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/app': {
        target: 'http://localhost:5053',
        changeOrigin: true,
        ws: true,
      },
      '/api': {
        target: 'http://localhost:5053',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:5053',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://localhost:5053',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          chart: ['chart.js'],
          axios: ['axios'],
        },
      },
    },
    cssCodeSplit: true,
    sourcemap: 'hidden',
    chunkSizeWarningLimit: 500,
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios', 'chart.js'],
  },
})
