# 博通工单系统 — AI Agent 协作指南

> **版本：** v3.0.0 | **定位：** 单人运营的 IT 运维服务管理平台
> **核心利润：** 劳务差价（收费费率 − 技术员成本率）× 工时 + 商品/配件销售差价（售价 − 进价）

---

## 一、业务本质

### 1.1 一句话定位

**博通是一个人（苏鹏）雇佣多个技术员、服务多个客户、赚取工费差价和商品利润的系统。**

### 1.2 两道利润线

| 利润线 | 公式 | 举例 |
|--------|------|------|
| **劳务差价** | ∑(客户收费率 − 技术员成本率) × 工时 | 蒙中 1h：收费¥60 − 苏鹏成本¥50 = 赚¥10；蒙中 1h：收费¥60 − 小赵成本¥25 = 赚¥35 |
| **商品利润** | ∑(售价 − 进价) × 数量 | 硒鼓：卖¥350 − 成本¥280 = 赚¥70；网线：卖¥15 − 成本¥8 = 赚¥7 |

### 1.3 三种用工计费模式

技术员（`technicians` 表）通过 `billing_type` 字段区分：

| 模式 | billing_type | 含义 | 现状 |
|------|-------------|------|------|
| **时薪** | `hourly` | 按小时计费，cost_rate = ¥/h | ✅ 全部 6 人已录入 |
| **天薪** | `daily` | 按天计费，cost_rate = ¥/天 | ⚠️ 字段已建，尚未使用 |
| **包工** | `fixed` | 固定总价，cost_price 为该工单的包工费 | ⚠️ 字段已建，尚未使用 |

> **当前问题：** 6 个技术员的 `billing_type` 全为 `hourly`，天薪/包工逻辑在前端和后端尚未实现。

### 1.4 客户分类与收费模式

客户（`clients` 表）通过 `hourly_rate` / `annual_rate` 区分收费模式：

| 客户类型 | 收费方式 | 代表客户 | 费率 |
|---------|---------|---------|------|
| **学校/国企** | 按时薪 | 蒙古族中学 | ¥60/h |
| **高费率企业** | 按时薪 | 集宁京能电力 | ¥100/h |
| **网吧/电竞** | 按年费 | 寻梦/自由点/先锋/硬派 | ¥2000/年 |
| **临时客户** | 按次/按时 | — | 按服务项目费率 |

### 1.5 服务项目定价

`service_fees` 表定义可售服务目录，每种服务有收费价（`unit_price`）和参考成本价（`cost_price`）：

| 服务名 | fee_type | 收费单价 | 参考成本 |
|--------|----------|---------|---------|
| 上门维修费 | hourly | ¥60/h | — |
| 网吧包年维护费 | yearly | ¥2000/年 | — |
| 电脑故障排查 | 检测 | ¥50 | ¥20 |
| 系统重装 | 安装 | ¥80 | ¥25 |
| 网络布线 | 施工 | ¥120 | ¥35 |
| 打印机维修 | 维修 | ¥60 | ¥20 |
| 监控安装 | fixed | ¥150 | ¥40 |
| 数据恢复 | 恢复 | ¥200 | ¥30 |

### 1.6 核心数据流

```
客户报修 → 创建工单(tickets)
         → 添加服务明细行(ticket_service_items)：选技术员 + 选服务项目 + 填工时
              → 系统自动算：劳务收入 = 工时 × 客户费率
              → 系统自动算：人工成本 = 工时 × 技术员成本率
              → 利润 = 劳务收入 − 人工成本
         → 添加材料/商品(materials)：选商品 + 填数量
              → 系统自动算：材料收费 = 数量 × 售价
              → 系统自动算：材料成本 = 数量 × 进价
              → 利润 = 材料收费 − 材料成本
         → 完工 → 自动出结算单 → 收款确认
```

---

## 二、技术架构

### 2.1 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Flask + DDD 分层（api → application → domain → infrastructure） |
| 前端 | Vue 3 + Vite + Bootstrap 5 + Pinia（构建产物由 Flask 直接服务） |
| 数据库 | SQLite（`tickets.db`，44 张表） |
| 队列 | RQ（骨架）+ LocalQueue（实际使用） |
| DI | 自建 ServiceLocator + Container |
| 认证 | HMAC 签名 + Cookie 自动续期 |
| 部署 | Docker / 本地 `python app.py` |

### 2.2 后端目录结构

```
app.py                    # 入口（Flask create_app 工厂）
├── api/v1/               # API 层（Blueprint）
│   ├── tickets.py        # 工单 CRUD
│   ├── service_fees.py   # 服务项目
│   ├── clients.py        # 客户
│   ├── technicians.py    # 技术员
│   ├── goods.py          # 商品
│   ├── inventory.py      # 库存
│   ├── purchase.py       # 采购
│   ├── finance.py        # 财务
│   ├── expenses.py       # 支出
│   ├── dashboard.py      # 仪表盘
│   ├── stats.py          # 统计
│   ├── search.py         # 全局搜索
│   └── ...               # health/todos/reminders/equipment/suppliers/wecom/pushplus
├── application/services/  # 应用服务层（业务编排）
│   ├── ticket_service.py
│   ├── finance_service.py
│   ├── inventory_service.py
│   ├── purchase_service.py
│   ├── goods_service.py
│   ├── client_service.py
│   ├── dashboard_service.py
│   ├── equipment_service.py
│   ├── search_service.py
│   └── ...
├── domain/                # 领域层（纯业务规则）
│   ├── amount_calculator.py  # ⭐ 统一金额计算器
│   ├── events.py             # 领域事件
│   ├── exceptions.py         # 领域异常
│   └── repositories/interfaces.py  # 仓储接口
├── infrastructure/         # 基础设施层
│   ├── persistence/         # 持久化
│   │   ├── database.py      # DB 抽象 + UnitOfWork
│   │   ├── legacy_db.py     # SQLite 连接池
│   │   ├── repositories/    # 仓储实现（14 个 Repo）
│   │   └── migrations/      # 数据库迁移
│   ├── di/                  # 依赖注入
│   ├── messaging/           # 消息推送（PushPlus/企微）
│   └── queue/               # 任务队列
├── config/                 # 配置
│   ├── rates.json           # 客户费率
│   ├── service_types.json   # 服务类型关键词
│   ├── billing.json         # 账单配置
│   └── ...
└── web/                    # Web 层
    ├── app_factory.py       # Flask 工厂
    ├── auth_routes.py       # 认证路由
    └── middleware/          # 中间件（auth/csrf）
```

### 2.3 前端目录结构

```
frontend/
├── src/
│   ├── views/           # 页面（18 个）
│   │   ├── Dashboard.vue
│   │   ├── Tickets.vue / TicketCreate.vue / TicketDetail.vue
│   │   ├── Clients.vue / ClientDetail.vue
│   │   ├── Finance.vue / Stats.vue
│   │   ├── Inventory.vue / Warehouses.vue
│   │   ├── Staff.vue / ServiceFees.vue / Suppliers.vue
│   │   ├── Equipment.vue / EquipmentDetail.vue
│   │   ├── Todos.vue / Notifications.vue / Settings.vue / Login.vue
│   ├── components/
│   │   ├── tickets/     # 工单子组件（状态面板/服务明细/付款栏/统计卡/照片/材料）
│   │   ├── common/      # 通用组件（BtModal/ConfirmDialog/Toast/StatCard 等）
│   │   ├── layout/      # 布局（AppLayout/AppSidebar/AppTopBar）
│   │   └── selectors/   # 选择器（ClientSelector/ServiceFeeSelector/GoodsSelector）
│   ├── api/             # API 客户端（14 个模块）
│   ├── composables/     # 组合式函数（useApi/useConfirm/useToast/useFormValidation 等）
│   ├── stores/          # Pinia 状态（auth/app）
│   ├── utils/           # 工具函数（format.ts/constants）
│   └── types/           # TypeScript 类型定义
└── vite.config.js
```

### 2.4 数据库核心表

共 44 张表，核心业务表及关系：

```
clients ──1:N── tickets ──1:N── ticket_service_items ──N:1── service_fees
                  │                    │
                  │                    └── 关联 technicians（通过 technician_name）
                  │
                  ├──1:N── materials ──N:1── goods
                  │                  └── N:1── inventory_items
                  │
                  ├──1:N── ticket_photos
                  ├──1:N── ticket_reminders
                  └──1:1── service_agreements（包年协议）

technicians          # 技术员（name/cost_rate/billing_type）
goods                # 商品目录（cost_price/selling_price/retail_price）
inventory_items      # 库存实例（status/warehouse_id）
purchase_orders ──1:N── purchase_items  # 采购单
sales_records        # 销售记录（含讯闪等订阅类）
suppliers            # 供货商
warehouses           # 仓库
income_records       # 收入记录
expense_records      # 支出记录
expense_categories / expense_budgets  # 支出分类与预算
equipment / equipment_components / equipment_photos  # 设备管理
maintenance_records / maintenance_reports / inspection_plans / inspection_records  # 维保巡检
```

### 2.5 关键领域逻辑

**金额计算器**（`domain/amount_calculator.py`）是整个系统的定价核心：

- `calc_labor_fee()` — 劳务收入 = ∑(工时 × 服务费率)
- `calc_labor_cost()` — 人工成本 = ∑(工时 × 技术员成本率)，通过 `cost_rate_lookup` 回调查技术员表
- `calc_material_fee()` — 材料收费 = ∑(材料行 total)
- `calc_total()` — 工单总额 = 劳务费 + 材料费 + 交通费 − 折扣
- `calc_total_with_tax()` — 含税计算
- `get_effective_fee_rate()` — 有效费率优先级：客户专属费率 > 服务项目费率 > 默认¥60

**服务明细行**（`ticket_service_items`）是利润计算的最小单元：
- `unit_price`：向客户收费的单价
- `cost_price`：付给技术员的成本单价
- `line_total`：行收费 = hours × unit_price
- `line_cost`：行成本 = hours × cost_price
- **行利润 = line_total − line_cost**

---

## 三、已知问题与待优化项

### 3.1 🔴 严重 — 客户数据缺少唯一约束

测试数据已全部清理（clients/tickets/goods/technicians 等业务表均清空），但 **`clients.name` 缺少 UNIQUE 约束**的根本问题未修。

**历史问题：** 蒙古族中学曾重复 20+ 次、京能电力 20+ 次，根本原因是缺少唯一约束 + 创建工单时未做去重。

**修复方向：**
1. ~~`clients.name` 加 UNIQUE 约束~~ ✅ 已完成（`idx_clients_name_unique`）
2. ~~其他表同名约束~~ ✅ 已完成：
   - `technicians.name` → `idx_technicians_name_unique`
   - `suppliers.name` → `idx_suppliers_name_unique`
   - `service_fees.name` → `idx_service_fees_name_unique`
   - `goods_categories.name` → `idx_goods_categories_name_unique`
   - `goods_types(name, category_id)` → `idx_goods_types_name_category`（组合唯一）
   - `locations(name, warehouse_id)` → `idx_locations_name_warehouse`（组合唯一）
   - `goods.name` 不加（同名不同规格商品可共存）
2. 创建工单时的客户选择逻辑改为"先查后建"

### 3.2 🟡 中等 — 天薪/包工模式未实现

`technicians.billing_type` 字段已有（值域：hourly/daily/fixed），但：
- 前端技术员管理页无 billing_type 选择
- 后端金额计算器只处理小时计费
- 工单服务明细行只有 hours 字段，无 days 或 fixed_amount 字段

**需要改动：**
- `ticket_service_items` 增加计费方式字段
- `AmountCalculator` 增加 `calc_labor_cost_daily()` / `calc_labor_cost_fixed()`
- 前端服务明细行表单适配三种模式

### 3.3 🟡 中等 — 架构骨架未落地

| 组件 | 现状 |
|------|------|
| RQ 队列 | 代码存在，实际用 LocalQueue |
| PostgreSQL 适配器 | Database 抽象已有，仅 SQLite 实现 |
| Redis 缓存 | 无 |
| 迁移框架 | `infrastructure/persistence/migrations/` 存在但只有 v015 |

### 3.4 🟢 轻微 — 测试不稳定

204 通过 / 30 失败 / 6 错误，Repository 层大面积失败。

### 3.5 🟢 轻微 — 前端 TypeScript 迁移进行中

`utils/format.ts` 已迁移，其余仍为 `.js`。

---

## 四、开发规范

### 4.1 启动与构建

```bash
# 后端启动
cd /Users/supeng/Documents/botong-ticket-system
source .venv/bin/activate
python app.py            # 默认端口 5053

# 前端开发
cd frontend
npm run dev              # Vite dev server

# 前端构建（npm 不走代理）
cd frontend && ./node_modules/.bin/vite build

# 健康检查
curl http://localhost:5053/api/v1/health

# 运行测试
python -m pytest tests/ -v
```

### 4.2 代码分层原则

| 层 | 职责 | 禁止 |
|----|------|------|
| `api/v1/` | HTTP 请求/响应、参数校验 | 不写业务逻辑 |
| `application/services/` | 业务编排、事务管理 | 不直接操作 SQL |
| `domain/` | 纯业务规则、金额计算 | 不依赖任何外部模块 |
| `infrastructure/` | 数据库、消息队列、DI | 不含业务逻辑 |
| `domain/repositories/interfaces.py` | 仓储接口定义 | — |
| `infrastructure/persistence/repositories/` | 仓储实现（SQL） | 只被 Service 层调用 |

### 4.3 金额计算规则

**所有金额计算必须通过 `AmountCalculator`，禁止散落计算逻辑。**

核心公式：
```
工单利润 = 劳务利润 + 材料利润
劳务利润 = ∑(line_total − line_cost)  across service_items
材料利润 = ∑(材料售价 − 材料进价) × 数量  across materials
```

费率查找优先级：
1. 客户专属费率（`clients.hourly_rate`）
2. 服务项目费率（`service_fees.unit_price`）
3. 默认费率 ¥60/h

### 4.4 变更记录

| 日期 | 变更内容 | 关联文件 |
|------|---------|----------|
| 2026-05-27 | 清空全部测试数据（clients/tickets/goods/technicians 等业务表归零） | `tickets.db` |
| 2026-05-27 | 重写 AGENTS.md，以业务本质（劳务差价+商品利润）为核心重新组织 | `AGENTS.md` |
| 2026-05-27 | TypeScript 迁移 | `frontend/src/types/`, `frontend/src/utils/format.ts` |
| 2026-05-26 | 前端重构：BtModal/拆分 TicketDetail/统一 composables | `frontend/src/components/`, `frontend/src/views/` |
| 2026-05-26 | 安全审查：修复 45+ 问题（SQL 注入/并发/XSS/密码） | `api/v1/`, `application/`, `domain/` |
| 2026-05-25 | UI 间距全面压缩（桌面+手机+小屏） | 18 个 Vue 文件 + base.html |
| 2026-05-25 | 删除工程师面板（ticket_technicians 冗余） | TicketDetail.vue, ticketApi |

---

## 五、AI Agent 避免幻觉指南

### 5.1 核心规则

1. **先查代码再回答** — 在回答技术问题前，必须搜索/读取相关代码
2. **不猜测字段** — 数据库字段以 `sqlite_master` 或 Repository 代码为准
3. **不虚构端点** — API 端点以 `api/v1/` 目录实际文件为准
4. **不假设配置** — 配置项以 `config/` 目录实际文件为准
5. **变更必更新** — 每次代码变更后，更新本文件变更记录

### 5.2 关键事实速查

| 问题 | 答案 |
|------|------|
| 端口？ | 5053（v3.0），旧版 5052 |
| 数据库？ | `tickets.db`（SQLite），44 张表 |
| 技术员几人？ | 0（测试数据已清空，需重新录入） |
| 计费模式？ | technicians.billing_type 全为 hourly，daily/fixed 未实现 |
| 利润核心？ | 劳务差价 + 商品差价 |
| 客户数据？ | 已清空，需重新录入（UNIQUE 约束 ✅ 已加） |
| 测试状态？ | 204 pass / 30 fail / 6 error（数据清空后可能影响） |
| 队列？ | LocalQueue（RQ 仅为骨架） |
| 前端框架？ | Vue 3 + Bootstrap 5 + Pinia |
| 工程师面板？ | 已删除（5/25），服务明细行替代 |

---

_此文件定义了博通系统的业务本质和技术现状。修改代码前必读。_
