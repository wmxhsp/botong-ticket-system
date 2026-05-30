---
title: keyboard-shortcuts-implementation
priority: high
tags: [keyboard, shortcuts, accessibility]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
---

## 简介
全局快捷键系统实现指南，提供高效的键盘操作能力，减少鼠标依赖，提升重度用户工作效率。

## 适用场景
- 实现全局快捷键监听和管理
- 为特定页面注册局部快捷键
- 提供快捷键帮助面板（按?键）
- 允许用户在设置中禁用特定快捷键

## 快捷键设计规范

### 设计原则
1. **避免冲突**: 不与浏览器默认快捷键冲突（如Ctrl+T新建标签页、Ctrl+W关闭标签页）
2. **一致性**: 相同功能在不同页面使用相同快捷键
3. **可发现性**: 提供快捷键帮助面板，新用户可按?查看
4. **可配置**: 允许用户禁用或自定义快捷键
5. **上下文感知**: 输入框内禁用全局快捷键，避免干扰文本输入

### 修饰键约定
- **Ctrl/Cmd**: 主要修饰键（跨平台兼容）
- **Alt/Option**: 辅助功能
- **Shift**: 反向操作或扩展功能
- **单键**: 仅在非输入状态下生效（如列表页的N、R）

---

## 核心快捷键映射

### 全局快捷键（任何页面可用）

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `Ctrl/Cmd + K` | 打开命令面板 | 全局搜索、快速导航 |
| `Ctrl/Cmd + /` | 显示快捷键帮助 | 弹出当前页面可用快捷键列表 |
| `Esc` | 取消/关闭 | 关闭弹窗、返回上一级、取消选择 |

### 工单列表页快捷键 (`/tickets`)

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `N` | 新建工单 | 跳转到QuickTicket页面 |
| `R` | 刷新列表 | 重新加载当前列表 |
| `Ctrl/Cmd + F` | 聚焦搜索框 | 快速筛选工单 |
| `↑` | 上一个工单 | 在列表中向上移动选中项 |
| `↓` | 下一个工单 | 在列表中向下移动选中项 |
| `Enter` | 打开详情 | 在右侧滑出面板显示选中工单详情 |
| `Ctrl/Cmd + E` | 编辑工单 | 进入编辑模式 |
| `Ctrl/Cmd + D` | 删除工单 | 弹出确认对话框 |

### 快速创建页快捷键 (`/tickets/quick`)

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `Enter` | 下一步/提交 | 根据当前步骤执行 |
| `Esc` | 取消 | 返回上一页，丢失未保存数据 |
| `Ctrl/Cmd + Enter` | 直接提交 | 跳过确认页，立即创建 |

### 快速结算页快捷键 (`/tickets/:id/settle`)

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `Ctrl/Cmd + S` | 确认结算 | 保存工时、材料、收款信息 |
| `Esc` | 取消 | 返回工单详情页 |
| `↑/↓` | 调整数值 | 在工时输入框中增减 |

### 工单详情页快捷键 (`/tickets/:id`)

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `E` | 编辑 | 进入编辑模式 |
| `D` | 删除 | 弹出确认对话框 |
| `P` | 打印 | 生成PDF结算单 |
| `Ctrl/Cmd + C` | 复制工单号 | 复制到剪贴板 |

---

## 实现模式

### 1. 全局快捷键管理器

**位置**: `frontend/src/core/composables/useKeyboardShortcuts.ts`

**核心代码结构**:
```typescript
import { ref, onMounted, onUnmounted } from 'vue'

interface ShortcutConfig {
  key: string
  modifiers?: ('ctrl' | 'meta' | 'alt' | 'shift')[]
  handler: () => void
  description: string
  preventDefault?: boolean
  enabled?: boolean  // 是否启用，支持动态禁用
}

export function useKeyboardShortcuts() {
  const shortcuts = ref<Map<string, ShortcutConfig>>(new Map())
  
  function register(config: ShortcutConfig) {
    const shortcutKey = buildShortcutKey(config.key, config.modifiers)
    shortcuts.value.set(shortcutKey, config)
  }
  
  function unregister(key: string, modifiers?: string[]) {
    const shortcutKey = buildShortcutKey(key, modifiers)
    shortcuts.value.delete(shortcutKey)
  }
  
  function handleKeydown(event: KeyboardEvent) {
    // 检查是否在输入框内
    const target = event.target as HTMLElement
    const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) ||
                    target.isContentEditable
    
    const shortcutKey = buildShortcutKey(event.key, getActiveModifiers(event))
    const shortcut = shortcuts.value.get(shortcutKey)
    
    if (shortcut) {
      // 输入框内禁用单键快捷键，但保留组合键
      if (isInput && !shortcut.modifiers?.length) {
        return
      }
      
      if (shortcut.preventDefault) {
        event.preventDefault()
      }
      shortcut.handler()
    }
  }
  
  function buildShortcutKey(key: string, modifiers?: string[]): string {
    const mods = modifiers?.sort().join('+') || ''
    return mods ? `${mods}+${key.toLowerCase()}` : key.toLowerCase()
  }
  
  function getActiveModifiers(event: KeyboardEvent): string[] {
    const modifiers: string[] = []
    if (event.ctrlKey) modifiers.push('ctrl')
    if (event.metaKey) modifiers.push('meta')
    if (event.altKey) modifiers.push('alt')
    if (event.shiftKey) modifiers.push('shift')
    return modifiers
  }
  
  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
  })
  
  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })
  
  return { register, unregister }
}
```

---

### 2. 在App.vue中全局注册

**位置**: `frontend/src/App.vue`

```vue
<script setup lang="ts">
import { useKeyboardShortcuts } from '@/core/composables/useKeyboardShortcuts'
import { useRouter } from 'vue-router'
import CommandPalette from '@/core/components/CommandPalette.vue'

const router = useRouter()
const { register } = useKeyboardShortcuts()

// 注册全局快捷键
register({
  key: 'k',
  modifiers: ['ctrl', 'meta'],
  handler: () => {
    // 打开命令面板
    document.dispatchEvent(new CustomEvent('open-command-palette'))
  },
  description: '打开命令面板',
  preventDefault: true
})

register({
  key: '/',
  modifiers: ['ctrl', 'meta'],
  handler: () => {
    // 显示快捷键帮助
    document.dispatchEvent(new CustomEvent('show-shortcuts-help'))
  },
  description: '显示快捷键帮助',
  preventDefault: true
})
</script>
```

---

### 3. 在特定页面注册局部快捷键

**示例**: `frontend/src/modules/ticket/views/Tickets.vue`

```vue
<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useKeyboardShortcuts } from '@/core/composables/useKeyboardShortcuts'
import { useRouter } from 'vue-router'

const router = useRouter()
const { register, unregister } = useKeyboardShortcuts()

onMounted(() => {
  // 注册列表页快捷键
  register({
    key: 'n',
    handler: () => router.push('/tickets/quick'),
    description: '新建工单',
    preventDefault: true
  })
  
  register({
    key: 'r',
    handler: () => refreshList(),
    description: '刷新列表',
    preventDefault: true
  })
  
  register({
    key: 'ArrowUp',
    handler: () => selectPreviousTicket(),
    description: '上一个工单'
  })
  
  register({
    key: 'ArrowDown',
    handler: () => selectNextTicket(),
    description: '下一个工单'
  })
})

onUnmounted(() => {
  // 清理快捷键
  unregister('n')
  unregister('r')
  unregister('ArrowUp')
  unregister('ArrowDown')
})
</script>
```

---

### 4. 快捷键帮助面板

**位置**: `frontend/src/components/common/KeyboardShortcutsHelp.vue`

**功能**:
- 按`Ctrl/Cmd + /`或`?`触发
- 显示当前页面可用的快捷键列表
- 分组展示（全局、当前页面）
- 提供"禁用所有快捷键"开关

**UI设计**:
```
┌─────────────────────────────────────┐
│         快捷键帮助                   │
├─────────────────────────────────────┤
│ 全局快捷键                           │
│ Ctrl+K    打开命令面板               │
│ Ctrl+/    显示此帮助                 │
│ Esc       取消/关闭                  │
├─────────────────────────────────────┤
│ 工单列表页                            │
│ N         新建工单                   │
│ R         刷新列表                   │
│ ↑/↓       选择上一个/下一个          │
│ Enter     打开详情                   │
├─────────────────────────────────────┤
│ ☐ 禁用所有快捷键                     │
└─────────────────────────────────────┘
```

---

## 测试用例

### 功能测试
- [ ] 在任何页面按Ctrl+K都能打开命令面板
- [ ] 在输入框中输入时不触发全局单键快捷键（如N、R）
- [ ] 在输入框中可以使用组合键（如Ctrl+K）
- [ ] 按?显示当前页面可用快捷键
- [ ] 快捷键帮助面板可通过Esc关闭
- [ ] 在设置中禁用快捷键后，所有快捷键失效

### 兼容性测试
- [ ] Windows/Linux: Ctrl键正常工作
- [ ] macOS: Cmd键正常工作
- [ ] 不与浏览器默认快捷键冲突
- [ ] 不与输入法快捷键冲突

### 性能测试
- [ ] 按键响应延迟 < 50ms
- [ ] 同时注册50+个快捷键不影响性能
- [ ] 页面切换时正确清理快捷键监听器

---

## 常见问题

### Q1: 如何处理与浏览器快捷键的冲突？
**A**: 
- 避免使用Ctrl+T、Ctrl+W、Ctrl+N等浏览器保留快捷键
- 使用`event.preventDefault()`阻止默认行为（谨慎使用）
- 提供禁用选项，让用户自行决定

### Q2: 如何在输入框内禁用快捷键但不影响组合键？
**A**: 
```typescript
const isInput = ['INPUT', 'TEXTAREA'].includes(target.tagName)
if (isInput && !shortcut.modifiers?.length) {
  return  // 输入框内禁用单键，但允许组合键
}
```

### Q3: 如何实现快捷键的可配置化？
**A**: 
- 将快捷键配置存储在localStorage或后端API
- 启动时从存储加载配置
- 提供设置页面修改快捷键映射

### Q4: 如何调试快捷键冲突？
**A**: 
- 在handleKeydown中添加console.log输出触发的快捷键
- 使用Chrome DevTools的Event Listener Breakpoints
- 创建快捷键冲突检测工具（开发环境）

---

## 维护人
AI Assistant

## 最后更新
2026-05-31

## 相关技能
- ticket-system-optimization
- frontend-best-practices
- vue-frontend-optimization
