# 博通工单系统 - 优化建议报告

> v1.0 | 2026-05-29

---

## 一、测试数据生成问题修复

### 1.1 发现的问题

在运行 `scripts/seed_test_data.py` 时发现以下数据库表结构不匹配问题：

| 表名 | 脚本使用字段 | 实际表字段 | 状态 |
|------|-------------|-----------|------|
| equipment | brand, model, install_date, created_at | 只有 name, type, client, model, serial_no, warranty_expire | ❌ 需修复 |
| goods | category | category_id | ❌ 需修复 |
| suppliers | email | contact, phone | ❌ 需修复 |
| technicians | email, hourly_rate, skill_level | name, phone, skills, cost_rate, billing_type | ❌ 需修复 |
| inventory_items | goods_id | product_id | ❌ 需修复 |
| todos | remind_at | reminder_at | ❌ 需修复 |

### 1.2 解决方案

1. **创建了修正版测试数据生成脚本**：
   - `scripts/generate_test_data_v2.py` - 根据实际表结构修正
   - `scripts/generate_minimal_test_data.py` - 最小化测试数据生成器

2. **建议**：
   - 更新 `scripts/seed_test_data.py` 以匹配当前数据库结构
   - 或创建数据库迁移脚本统一表结构

---

## 二、代码质量问题

### 2.1 依赖版本问题

发现多个已弃用的 API 调用：

```python
# 弃用警告
resolve_service()  # 改用 inject_service()
```

**建议**：统一使用 `inject_service()` 替换所有 `resolve_service()` 调用

### 2.2 服务注册问题

测试数据生成脚本中发现以下服务未注册：
- `inventory_svc` - 库存服务

**建议**：检查 `infrastructure/di/service_locator.py` 中的服务注册

### 2.3 事件推送问题

```python
WeCom status change push failed: 'TicketStatusChanged' object has no attribute 'get'
```

**建议**：修复事件对象的方法调用

---

## 三、前端优化建议

### 3.1 TypeScript 迁移

已完成：
- ✅ `api/client.ts`
- ✅ `utils/constants.ts`
- ✅ `composables/usePagination.ts`
- ✅ `stores/auth.ts`
- ✅ `stores/app.ts`
- ✅ 扩展 `types/index.ts`

待完成：
- ⏳ 其他 API 模块（clients, dashboard, tickets 等）
- ⏳ 其他 composables（useApi, useToast, useConfirm 等）
- ⏳ 模块 API 文件（modules/*/api.js）

### 3.2 VueUse 集成

已完成：
- ✅ `useAutoSave.js` 集成 `useDebounceFn`

建议增强：
- 使用 `useLocalStorage` 替代部分 `localStorage` 操作
- 使用 `useIntersectionObserver` 增强 `useInfiniteScroll`

### 3.3 组件拆分建议

部分组件文件过大，建议拆分：

| 文件 | 行数 | 建议 |
|------|------|------|
| TicketDetail.vue | 800+ | 拆分为 TicketTimeline, TicketMaterials, TicketPhotos 等 |
| Dashboard.vue | 500+ | 拆分为 StatCards, RecentTickets, Charts 等 |

---

## 四、后端优化建议

### 4.1 服务分层检查

建议确认以下分层规范是否遵守：

- ❓ API 层 (`api/v1/`) - 只做 HTTP 处理，不含业务逻辑
- ❓ Application 层 (`application/services/`) - 业务编排和事务管理
- ❓ Domain 层 (`domain/`) - 纯业务规则（如 AmountCalculator）
- ❓ Infrastructure 层 (`infrastructure/`) - 数据库、消息推送、依赖注入

### 4.2 数据库 Schema 统一

发现多个表的字段不一致：
- 部分表有 `created_at`，部分没有
- 部分表用 `goods_id`，部分用 `product_id`

**建议**：创建数据库 schema 文档，统一字段命名规范

### 4.3 事务管理检查

确认以下关键操作是否在事务中：
- ✅ `complete_ticket()` - 已确认在事务中（根据 AGENTS.md）

待检查：
- ⏳ 采购单创建 + 库存入库
- ⏳ 销售记录创建 + 库存出库
- ⏳ 工单状态流转 + 财务记录

---

## 五、安全和性能建议

### 5.1 安全性

根据 AGENTS.md，已完成：
- ✅ SQL 注入防护
- ✅ XSS 防护
- ✅ CSRF 防护
- ✅ 暴力破解防护
- ✅ 密码哈希升级（bcrypt）

待完成：
- ⏳ API 频率限制
- ⏳ 敏感数据脱敏（日志中的手机号等）
- ⏳ 文件上传安全检查

### 5.2 性能

待优化：
- ⏳ 数据库索引检查（特别是频繁查询的字段）
- ⏳ N+1 查询问题（工单列表 + 技术员 + 客户）
- ⏳ 大表分页优化

---

## 六、测试覆盖建议

### 6.1 当前测试状态

| 类型 | 数量 | 状态 |
|------|------|------|
| 后端 pytest | 194 passed, 45 skipped | ✅ 良好 |
| 前端 vitest | 65 passed (9 文件) | ✅ 良好 |
| E2E Playwright | 1 文件（smoke.spec.js） | ⏳ 待扩展 |

### 6.2 测试增强建议

1. **单元测试增强**：
   - 为 AmountCalculator 添加更多边界测试
   - 为三种计费模式添加测试用例
   - 添加错误处理测试

2. **集成测试**：
   - 工单完整生命周期测试（创建 → 进行 → 完成 → 收款）
   - 采购 → 入库 → 销售 → 出库流程测试

3. **E2E 测试扩展**：
   - 登录流程
   - 工单创建和编辑
   - 财务记录管理
   - 库存管理

---

## 七、文档和知识管理

### 7.1 现有文档

- ✅ `AGENTS.md` - AI Agent 协作指南（最新）
- ✅ `CODE_WIKI.md` - 代码百科全书
- ✅ `OPTIMIZATION_PLAN.md` - 优化方案

### 7.2 文档维护建议

1. **API 文档自动化**：
   - 使用 Flask-RESTX 或 Swagger 自动生成 API 文档
   - 确保 `/docs` 端点始终可用

2. **数据库 Schema 文档**：
   - 创建 `SCHEMA.md` 记录所有表结构
   - 使用工具自动从 SQLite 生成

3. **业务规则文档**：
   - 三种计费模式的详细说明
   - 利润计算公式
   - 工单状态流转图

---

## 八、优先级排序

### 高优先级（影响核心功能）

1. 🔴 **修复 seed_test_data.py 脚本** - 确保测试数据生成正常
2. 🔴 **统一数据库表结构** - 解决字段命名不一致
3. 🔴 **完善错误处理** - 特别是 WeCom 推送错误

### 中优先级（提升开发效率）

4. 🟡 **继续 TypeScript 迁移** - 核心 API 模块
5. 🟡 **扩展 Playwright E2E 测试** - 关键业务流程
6. 🟡 **组件拆分** - TicketDetail.vue 等大文件

### 低优先级（长期优化）

7. 🟢 **性能优化** - 索引、N+1 查询
8. 🟢 **安全增强** - 频率限制、数据脱敏
9. 🟢 **文档完善** - Schema、业务规则

---

## 九、总结

本次审计发现的主要问题：

1. **测试数据生成脚本与数据库结构不匹配** - 已创建修正版脚本
2. **弃用 API 使用** - 需要统一替换
3. **服务注册缺失** - inventory_svc 未注册
4. **前端 TypeScript 迁移未完成** - 核心模块待迁移
5. **测试覆盖不够全面** - E2E 测试待扩展

建议按照上述优先级逐步解决，以提升系统稳定性和开发效率。
