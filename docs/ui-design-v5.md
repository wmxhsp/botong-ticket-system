# 博通工单系统 — UI 设计 v5.0 方案

> 目标：打造适合1人公司的极致效率工具
> 设计原则：**极简、快速、移动端优先**

---

## 一、当前UI分析

### 1.1 现有优点

| 方面 | 现状 | 评价 |
|------|------|------|
| 侧边栏设计 | 深色渐变 + 图标导航 | ⭐⭐⭐⭐⭐ 专业感强 |
| 移动端适配 | 底部导航栏 + 响应式布局 | ⭐⭐⭐⭐☆ 已有基础 |
| 状态标签 | 颜色区分清晰 | ⭐⭐⭐⭐☆ 直观 |
| 统计卡片 | 网格布局，自适应 | ⭐⭐⭐⭐☆ 信息密度高 |

### 1.2 存在的问题

| 问题 | 具体表现 | 影响 |
|------|----------|------|
| **信息密度过高** | Dashboard 6个统计卡片 + 4个面板 | 手机端拥挤，关键信息不突出 |
| **操作流程复杂** | 创建工单需填写10+字段 | 手机上难以完成 |
| **视觉层次不清** | 所有卡片同等重要 | 无法快速定位关键信息 |
| **缺少快捷操作** | 没有语音输入、扫码等快捷方式 | 录入效率低 |
| **图表加载慢** | Chart.js 全量加载 | 首屏慢 |
| **主题切换突兀** | 深色/浅色切换无过渡 | 体验不流畅 |

---

## 二、新UI设计方案

### 2.1 设计系统

#### 色彩体系

```css
:root {
  /* 主色 */
  --bt-primary: #6366f1;        /* 靛蓝 - 品牌色 */
  --bt-primary-light: #818cf8;  /* 浅靛蓝 */
  --bt-primary-dark: #4f46e5;   /* 深靛蓝 */
  
  /* 状态色 */
  --bt-success: #22c55e;        /* 成功/收入 */
  --bt-warning: #f59e0b;        /* 警告/待办 */
  --bt-danger: #ef4444;         /* 危险/支出 */
  --bt-info: #3b82f6;           /* 信息/提示 */
  
  /* 中性色 */
  --bt-gray-50: #f8fafc;
  --bt-gray-100: #f1f5f9;
  --bt-gray-200: #e2e8f0;
  --bt-gray-300: #cbd5e1;
  --bt-gray-400: #94a3b8;
  --bt-gray-500: #64748b;
  --bt-gray-600: #475569;
  --bt-gray-700: #334155;
  --bt-gray-800: #1e293b;
  --bt-gray-900: #0f172a;
  
  /* 背景 */
  --bt-bg: #f8fafc;
  --bt-card-bg: #ffffff;
  --bt-sidebar-bg: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
}

[data-theme="dark"] {
  --bt-bg: #0f172a;
  --bt-card-bg: #1e293b;
}
```

#### 字体规范

| 层级 | 大小 | 字重 | 用途 |
|------|------|------|------|
| 标题 H1 | 24px | 700 | 页面标题 |
| 标题 H2 | 20px | 600 | 区块标题 |
| 标题 H3 | 16px | 600 | 卡片标题 |
| 正文 | 14px | 400 | 常规内容 |
| 辅助 | 12px | 400 | 时间、备注 |
| 数据 | 28px | 700 | 统计数字 |

#### 间距规范

```css
--bt-space-1: 4px;
--bt-space-2: 8px;
--bt-space-3: 12px;
--bt-space-4: 16px;
--bt-space-5: 24px;
--bt-space-6: 32px;

--bt-radius-sm: 6px;
--bt-radius-md: 8px;
--bt-radius-lg: 12px;
--bt-radius-xl: 16px;
```

### 2.2 布局重构

#### 桌面端布局

```
+------------------------------------------+
|  Sidebar  |  TopBar (标题 + 快捷操作)    |
|  (200px)  +------------------------------+
|           |                              |
|  导航      |        Main Content          |
|           |                              |
|           |  [今日重点] [快捷操作]        |
|           |                              |
|           |  [工单列表] [统计图表]        |
|           |                              |
+------------------------------------------+
```

#### 移动端布局

```
+------------------------------------------+
|  Header (标题 + 用户头像)                 |
+------------------------------------------+
|                                          |
|  [今日收入] [待办工单] [本月利润]         |
|                                          |
|  [快速创建工单] 大按钮                     |
|                                          |
|  [最近工单列表]                           |
|                                          |
|  [待办事项]                               |
|                                          |
+------------------------------------------+
|  [首页] [工单] [+] [客户] [财务]         |
+------------------------------------------+
```

### 2.3 关键页面设计

#### Dashboard（仪表盘）— 重构

**桌面端**：
```vue
<template>
  <div class="dashboard">
    <!-- 顶部快捷操作栏 -->
    <div class="quick-actions">
      <button class="btn-primary" @click="createTicket">
        <i class="bi bi-plus-lg"></i> 新建工单
      </button>
      <button class="btn-outline" @click="quickSettle">
        <i class="bi bi-check-circle"></i> 快速结算
      </button>
      <button class="btn-outline" @click="voiceInput">
        <i class="bi bi-mic"></i> 语音录入
      </button>
    </div>
    
    <!-- 今日重点（大卡片） -->
    <div class="today-focus">
      <div class="focus-card income">
        <div class="label">今日收入</div>
        <div class="value">¥{{ todayIncome }}</div>
        <div class="trend">+12% 较昨日</div>
      </div>
      <div class="focus-card tickets">
        <div class="label">待处理工单</div>
        <div class="value">{{ pendingTickets }}</div>
        <div class="detail">2个预约今日</div>
      </div>
      <div class="focus-card profit">
        <div class="label">本月利润</div>
        <div class="value">¥{{ monthlyProfit }}</div>
        <div class="progress">目标完成 65%</div>
      </div>
    </div>
    
    <!-- 两列布局 -->
    <div class="two-column">
      <div class="column">
        <h3>最近工单</h3>
        <TicketListCompact :tickets="recentTickets" />
      </div>
      <div class="column">
        <h3>待办事项</h3>
        <TodoListCompact :todos="recentTodos" />
      </div>
    </div>
  </div>
</template>
```

**移动端**：
```vue
<template>
  <div class="dashboard-mobile">
    <!-- 顶部用户信息 -->
    <div class="user-header">
      <div class="greeting">早上好，{{ userName }}</div>
      <div class="date">{{ currentDate }}</div>
    </div>
    
    <!-- 核心数据（大字体） -->
    <div class="core-stats">
      <div class="stat-item">
        <div class="value">¥{{ todayIncome }}</div>
        <div class="label">今日收入</div>
      </div>
      <div class="stat-item">
        <div class="value">{{ pendingTickets }}</div>
        <div class="label">待处理</div>
      </div>
    </div>
    
    <!-- 快速操作（大按钮） -->
    <div class="quick-actions">
      <button class="action-btn primary" @click="createTicket">
        <i class="bi bi-plus-lg"></i>
        <span>新建工单</span>
      </button>
      <button class="action-btn secondary" @click="quickSettle">
        <i class="bi bi-check-circle"></i>
        <span>快速结算</span>
      </button>
    </div>
    
    <!-- 最近工单列表 -->
    <div class="recent-section">
      <h3>最近工单 <span class="count">({{ recentTickets.length }})</span></h3>
      <TicketCardMobile 
        v-for="t in recentTickets.slice(0, 5)" 
        :key="t.id" 
        :ticket="t" 
      />
    </div>
  </div>
</template>

<style scoped>
.dashboard-mobile {
  padding: 16px;
  padding-bottom: 80px; /* 底部导航 */
}

.user-header {
  margin-bottom: 20px;
}

.greeting {
  font-size: 20px;
  font-weight: 600;
  color: var(--bt-gray-800);
}

.date {
  font-size: 14px;
  color: var(--bt-gray-400);
  margin-top: 4px;
}

.core-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.stat-item {
  flex: 1;
  background: var(--bt-card-bg);
  border-radius: var(--bt-radius-lg);
  padding: 20px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-item .value {
  font-size: 28px;
  font-weight: 700;
  color: var(--bt-primary);
}

.stat-item .label {
  font-size: 12px;
  color: var(--bt-gray-400);
  margin-top: 4px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.action-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  border-radius: var(--bt-radius-lg);
  border: none;
  font-size: 14px;
  font-weight: 500;
}

.action-btn.primary {
  background: var(--bt-primary);
  color: white;
}

.action-btn.secondary {
  background: var(--bt-gray-100);
  color: var(--bt-gray-700);
}

.action-btn i {
  font-size: 24px;
}

.recent-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.recent-section .count {
  font-size: 12px;
  color: var(--bt-gray-400);
  font-weight: 400;
}
</style>
```

#### 快速创建工单（移动端专用）

```vue
<template>
  <div class="quick-ticket-page">
    <!-- 步骤指示器 -->
    <div class="steps">
      <div class="step" :class="{ active: step >= 1 }">1.客户</div>
      <div class="step" :class="{ active: step >= 2 }">2.问题</div>
      <div class="step" :class="{ active: step >= 3 }">3.确认</div>
    </div>
    
    <!-- 步骤1：选择客户 -->
    <div v-if="step === 1" class="step-content">
      <h2>选择客户</h2>
      <div class="search-box">
        <i class="bi bi-search"></i>
        <input v-model="searchQuery" placeholder="搜索客户..." />
      </div>
      <div class="client-list">
        <div 
          v-for="client in filteredClients" 
          :key="client.id"
          class="client-card"
          :class="{ selected: selectedClient?.id === client.id }"
          @click="selectClient(client)"
        >
          <div class="client-name">{{ client.name }}</div>
          <div class="client-info">{{ client.phone }} · {{ client.address }}</div>
        </div>
      </div>
      <button class="btn-new-client" @click="showNewClient = true">
        <i class="bi bi-plus"></i> 新客户
      </button>
    </div>
    
    <!-- 步骤2：描述问题 -->
    <div v-if="step === 2" class="step-content">
      <h2>描述问题</h2>
      <div class="voice-input" @touchstart="startVoice" @touchend="stopVoice">
        <i class="bi bi-mic"></i>
        <span>{{ isRecording ? '录音中...' : '按住说话描述问题' }}</span>
      </div>
      <textarea 
        v-model="form.content" 
        placeholder="或手动输入问题描述..."
        rows="4"
      />
      <div class="quick-tags">
        <span class="tag" @click="addTag('无法开机')">无法开机</span>
        <span class="tag" @click="addTag('网络故障')">网络故障</span>
        <span class="tag" @click="addTag('系统重装')">系统重装</span>
        <span class="tag" @click="addTag('数据恢复')">数据恢复</span>
      </div>
    </div>
    
    <!-- 步骤3：确认创建 -->
    <div v-if="step === 3" class="step-content">
      <h2>确认信息</h2>
      <div class="summary-card">
        <div class="summary-item">
          <span class="label">客户</span>
          <span class="value">{{ selectedClient?.name }}</span>
        </div>
        <div class="summary-item">
          <span class="label">问题</span>
          <span class="value">{{ form.content }}</span>
        </div>
        <div class="summary-item">
          <span class="label">预约时间</span>
          <span class="value">{{ form.appointment || '尽快' }}</span>
        </div>
      </div>
    </div>
    
    <!-- 底部操作 -->
    <div class="actions">
      <button v-if="step > 1" class="btn-secondary" @click="step--">上一步</button>
      <button v-if="step < 3" class="btn-primary" @click="step++">下一步</button>
      <button v-if="step === 3" class="btn-primary" @click="createTicket">创建工单</button>
    </div>
  </div>
</template>

<style scoped>
.quick-ticket-page {
  padding: 16px;
  padding-bottom: 80px;
}

.steps {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}

.step {
  flex: 1;
  text-align: center;
  padding: 8px;
  border-radius: var(--bt-radius-md);
  background: var(--bt-gray-100);
  color: var(--bt-gray-400);
  font-size: 12px;
}

.step.active {
  background: var(--bt-primary);
  color: white;
}

.step-content h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--bt-gray-100);
  border-radius: var(--bt-radius-md);
  margin-bottom: 16px;
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
}

.client-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.client-card {
  padding: 16px;
  background: var(--bt-card-bg);
  border-radius: var(--bt-radius-md);
  border: 2px solid transparent;
  cursor: pointer;
}

.client-card.selected {
  border-color: var(--bt-primary);
}

.client-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.client-info {
  font-size: 12px;
  color: var(--bt-gray-400);
}

.voice-input {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  background: var(--bt-gray-100);
  border-radius: var(--bt-radius-lg);
  margin-bottom: 16px;
}

.voice-input i {
  font-size: 48px;
  color: var(--bt-primary);
}

.quick-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.tag {
  padding: 6px 12px;
  background: var(--bt-gray-100);
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
}

.tag:hover {
  background: var(--bt-primary-light);
  color: white;
}

.actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: var(--bt-card-bg);
  border-top: 1px solid var(--bt-gray-200);
  display: flex;
  gap: 12px;
}

.actions button {
  flex: 1;
  padding: 14px;
  border-radius: var(--bt-radius-md);
  border: none;
  font-size: 16px;
  font-weight: 500;
}

.btn-primary {
  background: var(--bt-primary);
  color: white;
}

.btn-secondary {
  background: var(--bt-gray-100);
  color: var(--bt-gray-700);
}
</style>
```

### 2.4 组件设计

#### 移动端专用组件

```vue
<!-- components/mobile/TicketCardMobile.vue -->
<template>
  <div class="ticket-card-mobile" @click="goToDetail">
    <div class="card-header">
      <div class="ticket-id">#{{ ticket.id }}</div>
      <StatusBadge :status="ticket.status" />
    </div>
    <div class="client-name">{{ ticket.client }}</div>
    <div class="ticket-content">{{ ticket.content }}</div>
    <div class="card-footer">
      <div class="time">
        <i class="bi bi-clock"></i>
        {{ formatTime(ticket.created_at) }}
      </div>
      <div class="amount" v-if="ticket.amount">
        ¥{{ ticket.amount }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.ticket-card-mobile {
  background: var(--bt-card-bg);
  border-radius: var(--bt-radius-md);
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ticket-id {
  font-size: 12px;
  color: var(--bt-gray-400);
}

.client-name {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 4px;
}

.ticket-content {
  font-size: 14px;
  color: var(--bt-gray-500);
  margin-bottom: 12px;
  line-height: 1.5;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--bt-gray-400);
}

.amount {
  font-weight: 600;
  color: var(--bt-success);
}
</style>
```

### 2.5 交互优化

#### 1. 触摸反馈
```css
/* 所有可点击元素添加触摸反馈 */
.btn, .card, .nav-item {
  transition: transform 0.1s ease, opacity 0.1s ease;
}

.btn:active, .card:active, .nav-item:active {
  transform: scale(0.98);
  opacity: 0.9;
}
```

#### 2. 加载状态
```vue
<!-- 骨架屏 -->
<template>
  <div class="skeleton" v-if="loading">
    <div class="skeleton-line" style="width: 60%"></div>
    <div class="skeleton-line" style="width: 80%"></div>
    <div class="skeleton-line" style="width: 40%"></div>
  </div>
</template>

<style>
.skeleton-line {
  height: 16px;
  background: linear-gradient(90deg, var(--bt-gray-100) 25%, var(--bt-gray-200) 50%, var(--bt-gray-100) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

#### 3. 手势支持
```javascript
// 左滑删除/归档
import { useGesture } from '@/composables/useGesture'

const { onSwipeLeft } = useGesture(ticketCardRef)
onSwipeLeft(() => {
  showActionSheet([
    { label: '归档', action: () => archiveTicket() },
    { label: '删除', action: () => deleteTicket(), danger: true }
  ])
})
```

---

## 三、主题系统

### 3.1 自动主题切换

```javascript
// 根据时间自动切换主题
function autoTheme() {
  const hour = new Date().getHours()
  const isDark = hour < 6 || hour >= 20  // 晚上8点到早上6点
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
}

// 每小时检查一次
setInterval(autoTheme, 3600000)
autoTheme()
```

### 3.2 主题过渡动画

```css
/* 主题切换过渡 */
* {
  transition: background-color 0.3s ease, color 0.3s ease;
}
```

---

## 四、性能优化

### 4.1 图表优化

```javascript
// 使用轻量级图表替代 Chart.js
import { createPieChart } from '@/utils/lite-chart'

// 纯CSS实现简单图表
function createPieChart(data, colors) {
  const total = data.reduce((a, b) => a + b, 0)
  let currentAngle = 0
  
  return data.map((value, i) => {
    const angle = (value / total) * 360
    const gradient = `conic-gradient(from ${currentAngle}deg, ${colors[i]} 0deg, ${colors[i]} ${angle}deg, transparent ${angle}deg)`
    currentAngle += angle
    return gradient
  })
}
```

### 4.2 图片优化

```javascript
// 上传时自动压缩
async function compressImage(file, maxWidth = 1200) {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const scale = Math.min(1, maxWidth / img.width)
      canvas.width = img.width * scale
      canvas.height = img.height * scale
      
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      
      canvas.toBlob((blob) => {
        resolve(new File([blob], file.name, { type: 'image/jpeg' }))
      }, 'image/jpeg', 0.8)
    }
    img.src = URL.createObjectURL(file)
  })
}
```

---

## 五、实施计划

| 阶段 | 时间 | 内容 |
|------|------|------|
| 第1周 | 设计系统 | 搭建CSS变量、字体、间距规范 |
| 第2周 | 布局重构 | 重构AppLayout、Sidebar、Dashboard |
| 第3周 | 移动端 | 实现QuickTicket、QuickSettle页面 |
| 第4周 | 组件库 | 开发移动端专用组件 |
| 第5周 | 优化 | 性能优化、主题系统、测试 |

---

## 六、预期效果

| 指标 | 当前 | 目标 |
|------|------|------|
| 移动端操作步骤 | 8步创建工单 | 3步创建工单 |
| 首屏加载时间 | 3s | 1.5s |
| 信息层级清晰度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 触摸反馈 | 无 | 全局支持 |
| 主题切换 | 手动 | 自动+手动 |

---

> **决策点**：是否采用此UI设计方案？
> 
> 如果确认，我将开始编写详细的实现计划，包括：
> 1. CSS设计系统代码
> 2. 移动端页面组件
> 3. 交互优化代码
> 4. 主题系统实现
