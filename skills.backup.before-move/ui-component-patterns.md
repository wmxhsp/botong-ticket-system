---
title: ui-component-patterns
priority: medium
tags: [ui, components, loading, skeleton, dark-mode]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
last_updated: 2026-05-31
related_skills: [frontend-best-practices, vue-frontend-optimization]
---

## 简介
UI组件设计规范与最佳实践：骨架屏、加载状态管理、移动端触觉反馈、深色模式主题切换、响应式布局。

## 适用场景
- 设计页面加载状态和骨架屏
- 实现移动端触摸反馈
- 添加深色模式支持
- 优化用户操作体验

---

## 一、骨架屏设计规范

### 1.1 骨架屏类型

根据页面类型选择合适的骨架屏：

**列表页骨架屏**:
```vue
<template>
  <div class="skeleton-list">
    <div v-for="i in 5" :key="i" class="skeleton-item">
      <div class="skeleton-avatar"></div>
      <div class="skeleton-content">
        <div class="skeleton-line short"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line long"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-content {
  flex: 1;
}

.skeleton-line {
  height: 16px;
  margin-bottom: 8px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-line.short { width: 30%; }
.skeleton-line.long { width: 80%; }

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>
```

**详情页骨架屏**:
```vue
<template>
  <div class="skeleton-detail">
    <div class="skeleton-header">
      <div class="skeleton-title"></div>
      <div class="skeleton-meta"></div>
    </div>
    <div class="skeleton-body">
      <div class="skeleton-section">
        <div class="skeleton-label"></div>
        <div class="skeleton-value"></div>
      </div>
    </div>
  </div>
</template>
```

**表单骨架屏**:
```vue
<template>
  <div class="skeleton-form">
    <div v-for="i in 4" :key="i" class="skeleton-field">
      <div class="skeleton-label"></div>
      <div class="skeleton-input"></div>
    </div>
  </div>
</template>
```

### 1.2 骨架屏使用原则

**何时显示骨架屏**:
- 数据加载时间预计 > 300ms
- 首屏内容加载
- 关键交互反馈（如提交后）

**何时使用Loading Spinner**:
- 数据加载时间 < 300ms
- 次要操作（如刷新列表）
- 后台异步任务

**超时提示**:
```typescript
const loading = ref(false)
const showTimeoutWarning = ref(false)
let timeoutTimer: ReturnType<typeof setTimeout>

async function fetchData() {
  loading.value = true
  showTimeoutWarning.value = false
  
  // 5秒后显示超时提示
  timeoutTimer = setTimeout(() => {
    showTimeoutWarning.value = true
  }, 5000)
  
  try {
    data.value = await api.get()
  } finally {
    loading.value = false
    clearTimeout(timeoutTimer)
  }
}
```

---

## 二、加载状态管理

### 2.1 三种加载状态

**Loading（加载中）**:
- 显示骨架屏或Spinner
- 禁用相关操作按钮
- 显示进度百分比（如果可知）

**Success（成功）**:
- 显示实际内容
- Toast提示成功（可选）
- 启用所有操作

**Error（错误）**:
- 显示错误信息和图标
- 提供重试按钮
- 保留用户已输入的内容

### 2.2 统一Loading组件

```vue
<!-- frontend/src/components/common/LoadingState.vue -->
<script setup lang="ts">
interface Props {
  loading: boolean
  error?: string | null
  empty?: boolean
  emptyText?: string
}

const props = withDefaults(defineProps<Props>(), {
  error: null,
  empty: false,
  emptyText: '暂无数据'
})

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <div v-if="loading" class="loading-state">
    <slot name="skeleton">
      <div class="spinner"></div>
      <p>加载中...</p>
    </slot>
  </div>
  
  <div v-else-if="error" class="error-state">
    <icon-error />
    <p>{{ error }}</p>
    <button @click="emit('retry')">重试</button>
  </div>
  
  <div v-else-if="empty" class="empty-state">
    <icon-empty />
    <p>{{ emptyText }}</p>
  </div>
  
  <slot v-else></slot>
</template>
```

**使用示例**:
```vue
<template>
  <LoadingState
    :loading="loading"
    :error="error"
    :empty="!tickets.length"
    @retry="fetchTickets"
  >
    <template #skeleton>
      <SkeletonList />
    </template>
    
    <TicketList :tickets="tickets" />
  </LoadingState>
</template>
```

---

## 三、移动端触觉反馈

### 3.1 Vibration API

**基础用法**:
```typescript
// frontend/src/core/utils/haptic.ts

export function hapticFeedback(pattern: number | number[] = [50]) {
  if ('vibrate' in navigator) {
    navigator.vibrate(pattern)
  }
}

// 不同场景的震动模式
export const HapticPatterns = {
  click: [50],                    // 轻点击
  success: [50, 100, 50],         // 成功
  error: [100, 50, 100],          // 错误
  warning: [100],                 // 警告
  longPress: [200],               // 长按
}
```

**在组件中使用**:
```vue
<script setup lang="ts">
import { hapticFeedback, HapticPatterns } from '@/core/utils/haptic'

function handleSuccess() {
  hapticFeedback(HapticPatterns.success)
  showToast('操作成功', 'success')
}

function handleError() {
  hapticFeedback(HapticPatterns.error)
  showToast('操作失败', 'error')
}
</script>

<template>
  <button @click="handleSuccess">提交</button>
</template>
```

### 3.2 视觉反馈增强

**按钮按压效果**:
```css
.btn {
  transition: transform 0.1s, box-shadow 0.1s;
}

.btn:active {
  transform: scale(0.95);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

**Ripple效果**:
```vue
<template>
  <button class="btn-ripple" @click="handleClick">
    <span class="ripple" v-if="showRipple"></span>
    点击我
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const showRipple = ref(false)

function handleClick(event: MouseEvent) {
  showRipple.value = true
  setTimeout(() => {
    showRipple.value = false
  }, 600)
}
</script>

<style scoped>
.btn-ripple {
  position: relative;
  overflow: hidden;
}

.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  transform: scale(0);
  animation: ripple-animation 0.6s linear;
}

@keyframes ripple-animation {
  to {
    transform: scale(4);
    opacity: 0;
  }
}
</style>
```

### 3.3 设置中关闭触觉反馈

```typescript
// frontend/src/stores/settings.ts
import { defineStore } from 'pinia'
import { useStorage } from '@vueuse/core'

export const useSettingsStore = defineStore('settings', () => {
  const hapticEnabled = useStorage('haptic_enabled', true)
  
  function toggleHaptic() {
    hapticEnabled.value = !hapticEnabled.value
  }
  
  return { hapticEnabled, toggleHaptic }
})
```

---

## 四、深色模式主题切换

### 4.1 CSS变量定义

```css
/* frontend/src/styles/theme.css */

:root {
  /* 浅色主题 */
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --border-color: #dee2e6;
  --card-bg: #ffffff;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

[data-theme="dark"] {
  /* 深色主题 */
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0a0;
  --border-color: #404040;
  --card-bg: #2d2d2d;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
```

### 4.2 主题切换Store

```typescript
// frontend/src/core/stores/theme.ts
import { defineStore } from 'pinia'
import { ref, onMounted } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<'light' | 'dark'>('light')
  
  function toggle() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    applyTheme()
  }
  
  function applyTheme() {
    document.documentElement.setAttribute('data-theme', theme.value)
    localStorage.setItem('bt_theme', theme.value)
  }
  
  onMounted(() => {
    // 从localStorage恢复主题
    const savedTheme = localStorage.getItem('bt_theme') as 'light' | 'dark'
    if (savedTheme) {
      theme.value = savedTheme
      applyTheme()
    } else {
      // 跟随系统偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      theme.value = prefersDark ? 'dark' : 'light'
      applyTheme()
    }
  })
  
  return { theme, toggle }
})
```

### 4.3 主题切换组件

```vue
<!-- frontend/src/components/common/ThemeToggle.vue -->
<script setup lang="ts">
import { useThemeStore } from '@/core/stores/theme'

const themeStore = useThemeStore()
</script>

<template>
  <button 
    class="theme-toggle"
    @click="themeStore.toggle"
    :aria-label="`切换到${themeStore.theme === 'light' ? '深色' : '浅色'}模式`"
  >
    <icon-sun v-if="themeStore.theme === 'dark'" />
    <icon-moon v-else />
  </button>
</template>
```

---

## 五、响应式布局最佳实践

### 5.1 断点定义

```css
/* frontend/src/styles/responsive.css */

:root {
  --breakpoint-sm: 576px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 992px;
  --breakpoint-xl: 1200px;
}

/* 手机优先策略 */
.container {
  width: 100%;
  padding: 0 16px;
}

@media (min-width: 576px) {
  .container { max-width: 540px; margin: 0 auto; }
}

@media (min-width: 768px) {
  .container { max-width: 720px; }
}

@media (min-width: 992px) {
  .container { max-width: 960px; }
}

@media (min-width: 1200px) {
  .container { max-width: 1140px; }
}
```

### 5.2 响应式组件示例

```vue
<template>
  <div class="ticket-card">
    <!-- 手机版：垂直布局 -->
    <div class="ticket-mobile">
      <div class="ticket-header">{{ ticket.title }}</div>
      <div class="ticket-meta">{{ ticket.client }}</div>
    </div>
    
    <!-- 桌面版：水平布局 -->
    <div class="ticket-desktop">
      <div class="ticket-info">
        <h3>{{ ticket.title }}</h3>
        <p>{{ ticket.client }}</p>
      </div>
      <div class="ticket-actions">
        <button>编辑</button>
        <button>删除</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ticket-mobile { display: block; }
.ticket-desktop { display: none; }

@media (min-width: 768px) {
  .ticket-mobile { display: none; }
  .ticket-desktop { 
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
```

---

## 验收标准

### 骨架屏
- [ ] 所有列表页都有骨架屏
- [ ] 骨架屏样式与实际内容布局一致
- [ ] 有shimmer动画效果
- [ ] 加载超过5秒显示超时提示

### 加载状态
- [ ] Loading/Error/Success三种状态完整
- [ ] 错误状态提供重试按钮
- [ ] 空状态有友好提示

### 触觉反馈
- [ ] 移动端按钮点击有震动反馈
- [ ] 成功/失败有不同震动模式
- [ ] 可在设置中关闭触觉反馈

### 深色模式
- [ ] 所有页面适配深色主题
- [ ] 主题切换流畅无闪烁
- [ ] 主题偏好持久化
- [ ] 首次访问跟随系统偏好

---

## 常见问题

### Q1: 骨架屏会影响性能吗？
**A**: 
- 轻微影响（额外DOM节点）
- 但提升用户体验，值得
- 避免过度复杂的骨架屏结构

### Q2: 如何测试触觉反馈？
**A**: 
- Chrome DevTools → Sensors → 模拟触摸设备
- 真机测试最佳
- 注意iOS Safari不支持Vibration API

### Q3: 深色模式如何适配第三方组件库？
**A**: 
- Element Plus等主流库已支持深色模式
- 通过CSS变量覆盖自定义样式
- 使用`data-theme`属性选择器

### Q4: 响应式布局的最佳实践是什么？
**A**: 
- 手机优先（Mobile First）
- 使用相对单位（rem、%、vw）
- 避免固定宽度
- 测试多种屏幕尺寸

---

## 相关技能
- **frontend-best-practices**: Vue 3组件开发规范
- **vue-frontend-optimization**: 前端性能优化高级主题

## 维护人
AI Assistant

## 最后更新
2026-05-31
