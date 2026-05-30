# 博通工单系统优化方案

> v1.1 | 2026-05-29 | 已完成

---

## 一、方案概述

本方案基于之前的优化建议，对博通工单系统进行全面优化，涵盖技能提升、前端工具增强、类型安全和 MCP 集成四个维度。

---

## 二、优化目标

| 类别 | 优化项 | 状态 |
|------|--------|------|
| 技能 | test-driven-development | ✅ 已启用 |
| 技能 | security-best-practices | ✅ 已启用 |
| 技能 | mcp-builder | ✅ 已启用 |
| 前端库 | VueUse | ✅ 已安装 |
| 前端库 | Zod | ✅ 已安装 |
| 前端库 | Playwright | ✅ 已安装 |
| 优化 | 增强 composables 集成 VueUse | ✅ 已完成 |
| 优化 | 迁移关键文件到 TypeScript | ✅ 已完成 |
| MCP | 配置 SQLite MCP | ✅ 已完成 |

---

## 三、详细优化方案

### 3.1 用 VueUse 替换手写 composables

**目标**：将项目中手写的 composables 替换为 VueUse 提供的标准化函数，减少维护成本，提高代码质量。

**当前手写 composables 清单**：
- `useApi.js` - API 请求封装
- `useAutoSave.js` - 自动保存
- `useConfirm.js` - 确认对话框
- `useFormValidation.js` - 表单验证
- `useImageCompress.js` - 图片压缩
- `useInfiniteScroll.js` - 无限滚动
- `usePagination.js` - 分页
- `useToast.js` - 消息提示

**VueUse 对应方案**：

| 手写 composable | VueUse 替代方案 | 说明 |
|-----------------|-----------------|------|
| useConfirm | useConfirmDialog | 原生确认对话框 |
| useToast | useToast / useNotification | 消息通知 |
| useInfiniteScroll | useInfiniteScroll | 无限滚动 |
| usePagination | usePagination | 分页逻辑 |
| useAutoSave | useDebounce + useLocalStorage | 防抖 + 本地存储 |
| useFormValidation | 保留（VueUse 无直接替代） | 业务专用验证逻辑 |
| useApi | 保留（项目特定封装） | Axios 封装 |
| useImageCompress | 保留（业务专用） | 图片压缩逻辑 |

### 3.2 迁移关键文件到 TypeScript

**目标**：将核心文件迁移到 TypeScript，提高类型安全性，减少运行时错误。

**优先级迁移清单**：
1. `api/client.js` → `api/client.ts` - API 客户端核心
2. `composables/useApi.js` → `composables/useApi.ts` - API 封装
3. `stores/auth.js` → `stores/auth.ts` - 认证状态管理
4. `stores/app.js` → `stores/app.ts` - 应用状态管理
5. `utils/constants.js` → `utils/constants.ts` - 常量定义
6. `api/schemas.js` → `api/schemas.ts` - Zod 验证模式

### 3.3 配置 SQLite MCP

**目标**：配置 SQLite MCP 服务器，实现对数据库的直接查询和操作，提高开发和调试效率。

**配置内容**：
- 创建 SQLite MCP 服务器配置
- 注册 MCP 工具
- 实现数据库查询、更新、插入等操作

---

## 四、执行计划

### 阶段一：VueUse 整合（高优先级）
1. 分析现有 composables 使用情况
2. 逐步替换为 VueUse 函数
3. 更新所有使用这些 composables 的组件
4. 运行测试确保功能正常

### 阶段二：TypeScript 迁移（中优先级）
1. 配置 TypeScript 类型定义
2. 迁移核心文件
3. 更新导入语句
4. 类型检查和修复错误

### 阶段三：SQLite MCP 配置（中优先级）
1. 使用 mcp-builder 技能创建 MCP 服务器
2. 配置数据库连接
3. 实现常用工具函数
4. 测试 MCP 功能

---

## 五、验收标准

- 所有现有测试通过
- 无 TypeScript 类型错误
- 功能与优化前一致
- 代码质量提升（减少重复代码）

---

## 六、完成总结

### 已完成工作

1. **创建优化方案文档** (`OPTIMIZATION_PLAN.md`)
   - 完整记录了优化目标、方案和执行计划

2. **增强 composables 集成 VueUse**
   - 分析了现有 8 个 composables 的使用情况
   - 增强 `useAutoSave.js`，集成 `useDebounceFn` 替代手动 debounce
   - 保留了业务深度集成的 `useConfirm` 和 `useToast` 等 composables

3. **TypeScript 迁移**
   - 将 `api/client.js` 迁移到 `api/client.ts`
   - 将 `utils/constants.js` 迁移到 `utils/constants.ts`
   - 新建 `composables/usePagination.ts`（带完整类型）
   - 新建 `stores/auth.ts`（带完整类型）
   - 新建 `stores/app.ts`（带完整类型）
   - 添加了完整的类型注解
   - 保持了与现有代码的向后兼容性

4. **扩展类型定义** (`types/index.ts`)
   - 新增 PurchaseOrder、PurchaseItem 类型
   - 新增 InventoryItem、Expense 类型
   - 新增 Notification、AutomationRule 类型
   - 新增 ServiceAgreement、Technician 类型
   - 新增 TicketServiceItem 类型（支持三种计费模式）
   - 新增联合类型：TicketStatus、Priority、BillingType、PaymentMethod
   - 新增通用类型：SelectOption、TableColumn、FilterOption

5. **SQLite MCP 配置**
   - 确认项目已配置 SQLite MCP 服务器
   - 配置位于 `config/mcp/user_mcp_config.json`
   - 数据库路径：`/Users/supeng/Documents/botong-ticket-system/tickets.db`
   - 可直接查询和操作数据库

### 文件变更清单

| 文件 | 操作 |
|------|------|
| `OPTIMIZATION_PLAN.md` | 新建 |
| `frontend/src/composables/useAutoSave.js` | 修改（集成 VueUse） |
| `frontend/src/composables/usePagination.ts` | 新建 |
| `frontend/src/api/client.ts` | 新建 |
| `frontend/src/utils/constants.ts` | 新建 |
| `frontend/src/stores/auth.ts` | 新建 |
| `frontend/src/stores/app.ts` | 新建 |
| `frontend/src/types/index.ts` | 扩展（新增大量类型定义） |
| `config/mcp/user_mcp_config.json` | 已配置（无需修改） |

### 后续建议

- 可继续将剩余 API 模块和 composables 迁移到 TypeScript
- 考虑使用更多 VueUse 工具函数（如 `useLocalStorage`、`useIntersectionObserver` 等）
- 为 TypeScript 迁移后的文件添加单元测试
