# 博通工单系统 — AI Agent 协作指南

> v3.0 | 单人运营 IT 运维服务管理平台
> **核心利润 = 劳务差价 + 商品差价**

---

## 一、业务本质

### 利润公式

| 利润线 | 公式 | 举例 |
|--------|------|------|
| **劳务差价** | ∑(收费率 − 成本率) × 工时 | ¥60/h 收 − ¥50/h 成本 = ¥10/h |
| **商品差价** | ∑(售价 − 进价) × 数量 | ¥350 售 − ¥280 成本 = ¥70 |

### 三种用工计费

| 模式 | billing_type | 计费 | 状态 |
|------|-------------|------|------|
| 时薪 | `hourly` | hours × cost_rate | ✅ 已实现 |
| 天薪 | `daily` | days × daily_cost_rate | ✅ 后端已实现，前端待适配 |
| 包工 | `package` | package_cost 固定价 | ✅ 后端已实现，前端待适配 |

### 客户收费模式

按服务项目费率

### 核心数据流

```
客户报修 → 创建工单
  ├─ 服务明细行 (ticket_service_items): 技术员 + 服务项目 + 工时 → 自动算劳务收入/成本
  ├─ 材料行 (materials): 商品 + 数量 → 自动算材料收费/成本
  └─ 现场照片→完工 → 结算单 → 收款确认
```

---

## 二、技术架构

### 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Flask + DDD 分层 (api → application → domain → infrastructure) |
| 前端 | Vue 3 + Vite + Pinia + Bootstrap 5 |
| 数据库 | SQLite (`tickets.db`，44 表) |
| 认证 | HMAC 签名 + Cookie 自动续期 |
| 部署 | `python app.py` (端口 5053) / Docker |

### 后端结构

```
app.py                         # 入口
├── api/v1/                    # 23 个 Blueprint (tickets/clients/finance/equipment/...)
├── application/services/      # 14 个业务服务
├── domain/
│   ├── amount_calculator.py   # ⭐ 统一金额计算器
│   ├── events.py / exceptions.py
│   └── repositories/interfaces.py
├── infrastructure/
│   ├── persistence/repositories/  # 15 个仓储实现
│   ├── di/                        # 依赖注入
│   └── messaging/                 # PushPlus / 企微推送
└── config/                    # rates / billing / pushplus / wecom / alert / auth
```

### 前端结构

```
frontend/src/
├── views/         # 22 个页面
├── components/    # tickets/ common/ layout/ selectors/
├── api/           # 23 个 API 模块 (client.js 为 Axios 基底)
├── composables/   # useApi / useConfirm / useToast / useFormValidation / ...
├── stores/        # auth / app (Pinia)
├── plugins/       # chart.js (Chart.js 集中注册)
├── utils/         # format / constants
└── __tests__/     # 9 文件 65 测试 (Vitest + happy-dom)
```

### 数据库核心关系

```
clients ──1:N── tickets ──1:N── ticket_service_items ──N:1── service_fees
                  │                    └── 关联 technicians (technician_name)
                  ├──1:N── materials ──N:1── goods
                  ├──1:N── ticket_photos / ticket_reminders
                  └──1:1── service_agreements (包年)

technicians (billing_type: hourly/daily/package)
equipment / equipment_components / equipment_photos / maintenance_records
purchase_orders / purchase_items / inventory_items / warehouses
income_records / expense_records / expense_categories / expense_budgets
automation_rules / ticket_templates / todos / notifications
```

### 金额计算器 (`domain/amount_calculator.py`)

**所有金额计算必须通过 AmountCalculator，禁止散落逻辑。**

| 方法 | 计算 |
|------|------|
| `calc_labor_fee()` | 劳务收入：按 billing_type 分 hourly/daily/package 三模式 |
| `calc_labor_cost()` | 人工成本：同上三模式，支持 cost_rate_lookup 回调 |
| `calc_material_fee()` | 材料收费 = ∑(材料行 total) |
| `calc_travel_fee()` | 交通费 = distance × rate |
| `calc_discount()` | 折扣：percent / fixed 两种 |
| `calc_total()` | 总额 = 劳务 + 材料 + 交通 − 折扣 |
| `get_effective_fee_rate()` | 有效费率优先级：客户专属 > 服务项目 > 默认 ¥60 |
| `apply_tier_discount()` | 客户级别折扣（可被手动折扣覆盖） |

---

## 三、当前状态

### 数据现状

| 表 | 记录数 | 说明 |
|----|--------|------|
| clients | 4 | 测试数据（hourly_rate 均为 0，待录入真实费率） |
| technicians | 2 | 测试数据（1 daily + 1 package） |
| tickets | 1 | 测试数据 |
| goods | 14 | 有数据 |
| service_fees | 0 | 空表 |
| suppliers | 0 | 空表 |
| automation_rules | 0 | 空表（前端已有管理界面） |
| ticket_templates | 0 | 空表（前端已有模板选择器） |

### 唯一约束（已加 ✅）

`clients.name` · `technicians.name` · `suppliers.name` · `service_fees.name` · `goods_categories.name`

### 测试状态

| 维度 | 结果 |
|------|------|
| 后端 (pytest) | 194 passed, 45 skipped |
| 前端 (vitest) | 65 passed (9 文件) |
| 前端构建 | ✅ 1.46s |

### 已完成 (2026-05-25~28)

- 安全审查修复 45+ 问题 (SQL 注入/并发/XSS/密码)
- 前端 UI 间距全面压缩 (桌面+手机+小屏)
- 删除工程师面板 (ticket_technicians 冗余)
- BtModal 统一、TicketDetail 拆分、composables 整合
- CSRF 统一 → `api/client.js` 为唯一来源
- 全局 errorHandler/warnHandler
- useApi AbortController 请求取消
- Chart.js 集中注册 (`plugins/chart.js`)
- API 层补全 14+ 缺失端点，新建 pushplus/wecom/tools API
- 新页面：Purchase / Expenses
- 页面增强：EquipmentDetail / Todos / Staff / ClientDetail
- 5 页统一导出 (`toolsApi.exportXxx()` + `downloadBlob()`)
- TicketCreate 模板选择器
- Settings 自动化规则管理 (CRUD + 启用/禁用 + 初始化默认)
- AmountCalculator 已支持三种计费模式 (hourly/daily/package)

### 已完成 (2026-05-28 优化)

- **P0**: CSRF Token 修复 — `fetchCsrfToken()` 返回 token + `login()` 改用 `client` 实例
- **P0**: 密码安全 — `auth_config.json` 加入 `.gitignore` + 环境变量优先读取
- **P0**: 事务原子性 — `complete_ticket()` 财务记录移入 UnitOfWork + `confirm_payment` 事务保护
- **P1**: 内存泄漏修复 — TicketDetail `onBeforeUnmount` 清理 interval + Dashboard Chart.js 销毁
- **P1**: 搜索防抖修复 — Tickets.vue 移除 watch 对 keyword 监听
- **P1**: AmountCalculator float → Decimal 精度计算
- **P1**: API 参数安全 — 批量操作上限 100 + 分页 per_page 上限 200 + N+1 查询修复
- **P1**: API 响应统一 — 拦截器 `return response.data`，移除 100 处手动解包
- **P1**: daily/package 前端适配 — calcFee 支持 + 天数输入框 + formatRate 显示
- **P1**: 暴力破解防护 — 从 JSON 文件迁移到 SQLite
- **P1**: 密码哈希升级 — 支持 bcrypt（自动降级 SHA-256）
- **P1**: 库存 API — 分页 + 数量验证 + 异常处理区分 400/500
- **P2**: App.vue 事件监听 `onUnmounted` 清理
- **P2**: Token 签名截断 16→32 位十六进制
- **P2**: ticket_service.py 直接 SQL 替换为 repo 接口
- **P2**: 本地认证跳过改为环境变量控制 `BOTO_SKIP_LOCAL_AUTH`
- **P2**: DELETE 端点改为 RESTful 路径参数
- **P2**: KeepAlive 组件名称常量化 — 补全 defineOptions
- **待完成**: Settings 模板管理 Tab — CRUD 模板 ✅
- **待完成**: Dashboard 迁移 — 已使用 `plugins/chart.js` ✅

### 待完成

1. **useAutoSave 测试** — debounce 测试改用 vi.waitFor
2. **环境变量规范化** — 前端 .env 配置
3. **真实数据录入** — 客户/技术员/服务项目/供货商

---

## 四、开发规范

### 启动与构建

```bash
# 后端
cd /Users/supeng/Documents/botong-ticket-system
source .venv/bin/activate && python app.py    # 端口 5053

# 前端开发
cd frontend && npm run dev

# 前端构建
cd frontend && npx vite build

# 测试
pytest tests/ -v                    # 后端
cd frontend && npx vitest run       # 前端

# 健康检查
curl http://localhost:5053/api/v1/health
```

### 代码分层

| 层 | 职责 | 禁止 |
|----|------|------|
| `api/v1/` | HTTP 请求/响应、参数校验 | 写业务逻辑 |
| `application/services/` | 业务编排、事务管理 | 直接操作 SQL |
| `domain/` | 纯业务规则、金额计算 | 依赖外部模块 |
| `infrastructure/` | 数据库、消息、DI | 含业务逻辑 |

### 关键约定

- **金额计算** — 必须走 AmountCalculator，禁止散落
- **CSRF** — `fetchCsrfToken()` 统一用 `api/client.js`，不用 stores
- **导出** — `toolsApi.exportXxx()` + `downloadBlob()`，不用 window.open
- **Chart.js** — 通过 `plugins/chart.js` 注册，不内联
- **Toast** — `useToast()` → `showToast(msg, type)`
- **请求取消** — `useApi()` 自带 AbortController

### 文件命名

| 类别 | 规则 | 例 |
|------|------|----|
| View | PascalCase.vue | `TicketCreate.vue` |
| API | kebab-case.js | `service-fees.js` |
| Composable | useCamelCase.js | `useFormValidation.js` |
| Component | category/PascalCase.vue | `selectors/ClientSelector.vue` |
| Test | fileName.test.js | `useApi.test.js` |

---

## 五、防幻觉规则

1. **先查代码再回答** — 搜索/读取相关代码后再做技术判断
2. **不猜测字段** — 以 `sqlite_master` 或 Repository 代码为准
3. **不虚构端点** — 以 `api/v1/` 实际文件为准
4. **不假设配置** — 以 `config/` 实际文件为准
5. **变更必更新** — 每次代码变更后更新本文件

### 速查

| 问题 | 答案 |
|------|------|
| 端口 | 5053 |
| 数据库 | tickets.db (SQLite, 44 表) |
| 后端测试 | 194 pass / 45 skip |
| 前端测试 | 65 pass (9 文件) |
| 计费模式 | hourly ✅ / daily ✅ (后端) / package ✅ (后端)，前端待适配 |
| 利润核心 | 劳务差价 + 商品差价 |
| 队列 | LocalQueue |
| 前端框架 | Vue 3 + Bootstrap 5 + Pinia |
| 推送 | PushPlus + 企微 |

---

_修改代码前必读。变更后更新此文件。_
