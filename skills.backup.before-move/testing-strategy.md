---
title: testing-strategy
priority: high
tags: [testing, vitest, playwright, pytest, e2e]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
last_updated: 2026-05-31
related_skills: [flask-testing-patterns, frontend-best-practices]
---

## 简介
完整测试策略指南：整合前端单元测试（Vitest）、组件测试（Testing Library）、E2E测试（Playwright）和后端测试（pytest），提供测试覆盖率要求和最佳实践。

## 适用场景
- 编写新的单元测试或E2E测试
- 配置CI/CD中的自动化测试
- 提升测试覆盖率
- Mock和Stub使用

---

## 一、测试金字塔

```
        /\
       /  \  E2E Tests (Playwright) - 少量
      /----\
     /      \  Integration Tests - 适量
    /--------\
   /          \  Unit Tests (Vitest/pytest) - 大量
  /------------\
```

**原则**:
- 单元测试：70% coverage
- 集成测试：20% coverage
- E2E测试：10% coverage

---

## 二、前端单元测试（Vitest）

### 2.1 测试Composables

```typescript
// tests/unit/useDebounce.test.ts
import { describe, it, expect, vi } from 'vitest'
import { ref, nextTick } from 'vue'
import { useDebounce } from '@/core/composables/useDebounce'

describe('useDebounce', () => {
  it('should debounce value changes', async () => {
    const value = ref('initial')
    const debounced = useDebounce(value, 100)
    
    value.value = 'change1'
    value.value = 'change2'
    
    await nextTick()
    expect(debounced.value).toBe('initial')
    
    // 等待100ms
    await new Promise(resolve => setTimeout(resolve, 150))
    expect(debounced.value).toBe('change2')
  })
})
```

### 2.2 测试Store Actions

```typescript
// tests/unit/tickets.store.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useTicketsStore } from '@/stores/tickets'
import { ticketApi } from '@/modules/ticket/api'

vi.mock('@/modules/ticket/api', () => ({
  ticketApi: {
    list: vi.fn()
  }
}))

describe('useTicketsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })
  
  it('should fetch tickets', async () => {
    const store = useTicketsStore()
    const mockTickets = [{ id: 1, ticket_no: 'TKT-001' }]
    
    vi.mocked(ticketApi.list).mockResolvedValue({
      items: mockTickets,
      total: 1
    })
    
    await store.fetchTickets({ page: 1 })
    
    expect(store.tickets).toHaveLength(1)
    expect(store.loading).toBe(false)
  })
})
```

---

## 三、E2E测试（Playwright）

### 3.1 测试工单创建流程

```typescript
// tests/e2e/ticket-creation.spec.ts
import { test, expect } from '@playwright/test'

test('should create a new ticket', async ({ page }) => {
  // 登录
  await page.goto('/login')
  await page.fill('input[name="username"]', 'admin')
  await page.fill('input[name="password"]', 'password')
  await page.click('button[type="submit"]')
  
  // 导航到快速创建页面
  await page.goto('/tickets/quick')
  
  // 填写表单
  await page.fill('input[placeholder="客户名称"]', '张三')
  await page.fill('textarea[placeholder="问题描述"]', '电脑无法开机')
  await page.selectOption('select[name="priority"]', 'H')
  
  // 提交
  await page.click('button:has-text("创建工单")')
  
  // 验证
  await expect(page.locator('.toast-success')).toBeVisible()
  await expect(page).toHaveURL(/\/tickets\/\d+/)
})
```

### 3.2 截图对比测试

```typescript
test('ticket list should match snapshot', async ({ page }) => {
  await page.goto('/tickets')
  
  // 等待数据加载
  await page.waitForSelector('.ticket-item')
  
  // 截图并对比
  await expect(page).toHaveScreenshot('ticket-list.png', {
    maxDiffPixels: 100
  })
})
```

---

## 四、后端测试（pytest）

### 4.1 测试API端点

```python
# tests/test_ticket_api.py
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        yield client

def test_create_ticket(client):
    response = client.post('/api/v1/tickets', json={
        'client': '张三',
        'description': '电脑故障',
        'priority': 'M'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data['data']
    assert data['data']['client'] == '张三'

def test_list_tickets(client):
    response = client.get('/api/v1/tickets?page=1&page_size=10')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'items' in data['data']
```

### 4.2 测试Service层

```python
# tests/test_ticket_service.py
def test_complete_ticket_with_materials():
    service = TicketService(uow=UnitOfWork())
    
    # 创建测试工单
    ticket_id = service.create_ticket({...})
    
    # 完工并扣减库存
    service.complete_ticket(ticket_id, [
        {'goods_id': 1, 'quantity': 2}
    ])
    
    # 验证工单状态
    ticket = service.get_ticket(ticket_id)
    assert ticket['status'] == 'completed'
    
    # 验证库存扣减
    goods = service.get_goods(1)
    assert goods['stock'] == original_stock - 2
```

---

## 五、Mock和Stub使用规范

### 5.1 何时使用Mock

- 外部API调用（支付网关、短信服务）
- 数据库操作（隔离业务逻辑测试）
- 时间相关函数（setTimeout、Date.now）

### 5.2 Vitest Mock示例

```typescript
import { vi } from 'vitest'

// Mock整个模块
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

// Mock具体函数
vi.spyOn(Date, 'now').mockReturnValue(1234567890)
```

### 5.3 pytest Mock示例

```python
from unittest.mock import patch, MagicMock

@patch('requests.post')
def test_send_notification(mock_post):
    mock_post.return_value.status_code = 200
    
    result = send_notification('user_id', 'message')
    
    assert result is True
    mock_post.assert_called_once()
```

---

## 六、测试覆盖率要求

| 层级 | 最低覆盖率 | 工具 |
|------|-----------|------|
| 前端单元测试 | 70% | vitest --coverage |
| 后端单元测试 | 80% | pytest --cov |
| E2E测试 | 关键路径100% | playwright |

**运行覆盖率检查**:
```bash
# 前端
npm run test:coverage

# 后端
pytest --cov=api --cov=application --cov-report=html
```

---

## 验收标准

- [ ] 前端单元测试覆盖率 ≥ 70%
- [ ] 后端单元测试覆盖率 ≥ 80%
- [ ] 所有关键用户流程有E2E测试
- [ ] CI/CD中自动运行测试
- [ ] 测试失败时阻止合并

---

## 常见问题

### Q1: 如何测试异步代码？
**A**: 
```typescript
it('should handle async', async () => {
  const result = await asyncFunction()
  expect(result).toBe(expected)
})
```

### Q2: Mock和Stub有什么区别？
**A**: 
- **Mock**: 模拟对象行为，验证是否被调用
- **Stub**: 提供固定返回值，不验证调用

### Q3: E2E测试太慢怎么办？
**A**: 
- 只测试关键路径
- 并行执行测试
- 使用headless模式
- Mock非关键API

---

## 相关技能
- **flask-testing-patterns**: Flask测试详细指南
- **frontend-best-practices**: Vue组件测试规范

## 维护人
AI Assistant

## 最后更新
2026-05-31
