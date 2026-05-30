# 博通售后管理系统 — Code Wiki

> 版本 4.0.0 | 单人运营 IT 运维服务管理平台 | 6周优化计划已完成
> 核心利润 = 劳务差价 + 商品差价

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 技术栈与依赖](#2-技术栈与依赖)
- [3. 系统架构](#3-系统架构)
  - [3.1 整体架构](#31-整体架构)
  - [3.2 后端分层架构 (DDD)](#32-后端分层架构-ddd)
  - [3.3 前端架构](#33-前端架构)
- [4. 目录结构](#4-目录结构)
- [5. 后端核心模块](#5-后端核心模块)
  - [5.1 应用入口与工厂](#51-应用入口与工厂)
  - [5.2 API 层 (api/v1/)](#52-api-层-apiv1)
  - [5.3 应用服务层 (application/services/)](#53-应用服务层-applicationservices)
  - [5.4 领域层 (domain/)](#54-领域层-domain)
  - [5.5 基础设施层 (infrastructure/)](#55-基础设施层-infrastructure)
  - [5.6 中间件 (web/middleware/)](#56-中间件-webmiddleware)
  - [5.7 后台任务 (tasks/)](#57-后台任务-tasks)
- [6. 前端核心模块](#6-前端核心模块)
  - [6.1 入口与路由](#61-入口与路由)
  - [6.2 状态管理 (Pinia Stores)](#62-状态管理-pinia-stores)
  - [6.3 API 层 (api/)](#63-api-层-api)
  - [6.4 组合式函数 (composables/)](#64-组合式函数-composables)
  - [6.5 组件体系](#65-组件体系)
  - [6.6 页面视图 (views/)](#66-页面视图-views)
  - [6.7 工具与插件](#67-工具与插件)
- [7. 数据库设计](#7-数据库设计)
  - [7.1 核心表结构](#71-核心表结构)
  - [7.2 实体关系图](#72-实体关系图)
  - [7.3 数据库迁移](#73-数据库迁移)
- [8. 依赖注入与事件系统](#8-依赖注入与事件系统)
  - [8.1 DI 容器](#81-di-容器)
  - [8.2 事件总线](#82-事件总线)
  - [8.3 启动引导流程](#83-启动引导流程)
- [9. 认证与安全](#9-认证与安全)
  - [9.1 认证机制](#91-认证机制)
  - [9.2 CSRF 保护](#92-csrf-保护)
  - [9.3 领域异常体系](#93-领域异常体系)
- [10. 配置体系](#10-配置体系)
- [11. 部署与运维](#11-部署与运维)
- [12. 测试体系](#12-测试体系)
- [13. 关键业务流程](#13-关键业务流程)
  - [13.0 性能优化功能（v4.0）](#130-性能优化功能v40)
  - [13.1 工单生命周期](#131-工单生命周期)
  - [13.2 金额计算流程](#132-金额计算流程)
  - [13.3 库存出入库流程](#133-库存出入库流程)
- [14. 开发规范速查](#14-开发规范速查)

---

## 1. 项目概述

博通售后管理系统（Botong）是一个面向单人运营 IT 运维服务商的售后工单管理平台。系统围绕 **工单** 为核心，覆盖了从客户报修、工程师派工、现场服务、材料消耗、完工结算到收付款确认的完整业务闭环。

**核心利润模型：**

| 利润线 | 公式 | 举例 |
|--------|------|------|
| 劳务差价 | ∑(收费率 − 成本率) × 工时 | ¥60/h 收 − ¥50/h 成本 = ¥10/h |
| 商品差价 | ∑(售价 − 进价) × 数量 | ¥350 售 − ¥280 成本 = ¥70 |

**三种用工计费模式：**

| 模式 | billing_type | 计费方式 |
|------|-------------|---------|
| 时薪 | `hourly` | hours × cost_rate |
| 天薪 | `daily` | days × daily_cost_rate |
| 包工 | `package` | package_cost 固定价 |

---

## 2. 技术栈与依赖

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Flask | ≥3.1 | Web 框架 |
| flask-restx | ≥1.3 | REST API + Swagger 文档 |
| flask-caching | ≥2.3 | 缓存（SimpleCache / RedisCache） |
| Pydantic | ≥2.0 | 数据校验 |
| APScheduler | ≥3.10 | 定时任务调度 |
| Gunicorn | ≥22.0 | WSGI 服务器 |
| Requests | ≥2.28 | HTTP 客户端（推送通知） |
| python-dotenv | ≥1.0 | 环境变量加载 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | ^3.4 | UI 框架 |
| **TypeScript** | ^6.0 | **类型系统（API模块已完成迁移）** |
| Vue Router | ^4.3 | 路由管理 |
| Pinia | ^2.1 | 状态管理 |
| Axios | ^1.7 | HTTP 客户端 |
| Bootstrap | ^5.3 | UI 组件库 |
| Chart.js | ^4.4 | 图表可视化 |
| Vite | ^5.4 | 构建工具 |
| Vitest | ^4.1 | 单元测试 |
| **Playwright** | latest | **E2E自动化测试** |
| vue-virtual-scroller | ^2.0.0-beta.8 | 虚拟滚动（性能优化） |
| VueUse | ^10.x | 组合式工具函数库 |
| Zod | ^3.x | Schema验证 |

### 数据库

| 技术 | 用途 |
|------|------|
| SQLite | 主数据库（tickets.db，44 表） |
| Redis | 可选缓存 / 队列后端 |

---

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    浏览器 / 移动端                        │
│              Vue 3 SPA (Vite 构建)                       │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / Axios
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  Flask 后端 (端口 5053)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 中间件    │  │ API 层   │  │ 认证路由  │              │
│  │Auth/CSRF │→ │Blueprint │→ │Login/Out │              │
│  └──────────┘  └────┬─────┘  └──────────┘              │
│                      │                                    │
│  ┌───────────────────▼─────────────────────┐            │
│  │         应用服务层 (Services)             │            │
│  │  TicketService / FinanceService / ...    │            │
│  └───────────────────┬─────────────────────┘            │
│                      │                                    │
│  ┌──────────┐  ┌─────▼──────┐  ┌──────────┐            │
│  │ 领域层    │  │ 仓储层     │  │ 事件总线  │            │
│  │Calculator│  │Repository  │  │ EventBus │            │
│  └──────────┘  └─────┬──────┘  └────┬─────┘            │
│                       │              │                    │
│  ┌────────────────────▼──────────────▼──────┐           │
│  │           基础设施层                       │           │
│  │  SQLite DB │ PushPlus │ 企微 │ APScheduler│           │
│  └──────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

### 3.2 后端分层架构 (DDD)

项目采用领域驱动设计（DDD）分层架构，严格遵循依赖规则：

| 层 | 目录 | 职责 | 禁止 |
|----|------|------|------|
| **API 层** | `api/v1/` | HTTP 请求/响应、参数校验 | 写业务逻辑 |
| **应用服务层** | `application/services/` | 业务编排、事务管理 | 直接操作 SQL |
| **领域层** | `domain/` | 纯业务规则、金额计算 | 依赖外部模块 |
| **基础设施层** | `infrastructure/` | 数据库、消息、DI | 含业务逻辑 |

**调用链路：** API 层 → 应用服务层 → 领域层 + 仓储层 → 基础设施层

### 3.3 前端架构

```
Vue 3 SPA
├── 路由层 (router/) — 路由定义 + 权限守卫
├── 状态层 (stores/) — Pinia 全局状态
├── API 层 (api/) — Axios 封装，与后端通信
├── 组合式函数 (composables/) — 可复用逻辑
├── 组件层 (components/)
│   ├── layout/ — 布局框架
│   ├── common/ — 通用组件
│   ├── selectors/ — 选择器组件
│   └── tickets/ — 工单专用组件
└── 视图层 (views/) — 22 个页面
```

---

## 4. 目录结构

```
botong-ticket-system/
├── skills/                         # AI技能文档（29个技能文件）
│   ├── frontend-best-practices.md  # 前端最佳实践
│   ├── typescript-migration-guide.md # TypeScript迁移指南
│   ├── testing-strategy.md         # 测试策略
│   └── ...                         # 其他技能文档
├── app.py                          # Flask 入口
├── web/                            # Web 层
│   ├── app_factory.py              # 应用工厂 (create_app)
│   ├── auth_routes.py              # 认证路由
│   ├── pages.py                    # 页面路由
│   └── middleware/
│       ├── auth.py                 # HMAC 认证中间件
│       └── csrf.py                 # CSRF 保护中间件
├── api/                            # API 层
│   └── v1/                         # 23 个 Blueprint
│       ├── tickets.py              # 工单 API
│       ├── clients.py              # 客户 API
│       ├── finance.py              # 财务 API
│       ├── inventory.py            # 库存 API
│       ├── equipment.py            # 设备 API
│       ├── goods.py                # 商品 API
│       ├── technicians.py          # 技术员 API
│       ├── dashboard.py            # 仪表盘 API
│       ├── expenses.py             # 支出 API
│       ├── purchase.py             # 采购 API
│       ├── service_fees.py         # 服务费率 API
│       ├── suppliers.py            # 供应商 API
│       ├── todos.py                # 待办 API
│       ├── search.py               # 全局搜索 API
│       ├── stats.py                # 统计 API
│       ├── reminders.py            # 提醒 API
│       ├── tools.py                # 工具 API（导出等）
│       ├── health.py               # 健康检查 API
│       ├── pushplus.py             # PushPlus 推送 API
│       ├── wecom.py                # 企微推送 API
│       ├── stock_aux.py            # 库存辅助 API
│       └── responses.py            # 统一响应格式
│   └── validators/
│       └── schemas.py              # Pydantic 校验模型
├── application/                    # 应用服务层
│   └── services/                   # 14 个业务服务
│       ├── ticket_service.py       # 工单服务 (核心)
│       ├── client_service.py       # 客户服务
│       ├── finance_service.py      # 财务服务
│       ├── inventory_service.py    # 库存服务
│       ├── equipment_service.py    # 设备服务
│       ├── goods_service.py        # 商品服务
│       ├── dashboard_service.py    # 仪表盘服务
│       ├── purchase_service.py     # 采购服务
│       ├── reminder_service.py     # 提醒服务
│       ├── search_service.py       # 搜索服务
│       ├── supplier_service.py     # 供应商服务
│       ├── todo_service.py         # 待办服务
│       ├── ticket_export_service.py # 导出服务
│       └── ticket_nl_service.py    # 自然语言服务
├── domain/                         # 领域层
│   ├── amount_calculator.py        # ⭐ 统一金额计算器
│   ├── events.py                   # 领域事件 + EventBus
│   ├── exceptions.py               # 领域异常体系
│   └── repositories/
│       └── interfaces.py           # 仓储抽象接口
├── infrastructure/                 # 基础设施层
│   ├── di/                         # 依赖注入
│   │   ├── container.py            # DI 容器
│   │   ├── bootstrap.py            # 启动引导
│   │   ├── service_injection.py    # 服务注入
│   │   └── service_locator.py      # 旧版定位器（已废弃）
│   ├── persistence/                # 数据持久化
│   │   ├── database.py             # 数据库抽象
│   │   ├── legacy_db.py            # 旧版数据库工具
│   │   ├── maintenance.py          # 数据库维护
│   │   ├── db_maintenance.py       # 维护调度
│   │   ├── migrations/             # 版本迁移 (v002-v023)
│   │   └── repositories/           # 15 个仓储实现
│   ├── messaging/                  # 消息推送
│   │   ├── pushplus.py             # PushPlus 客户端
│   │   ├── wecom.py                # 企微机器人客户端
│   │   └── event_subscribers.py    # 事件订阅注册
│   ├── logging.py                  # 结构化日志
│   ├── scheduler.py                # APScheduler 调度
│   └── async_notify.py             # 异步通知
├── config/                         # 配置文件
│   ├── manager.py                  # 统一配置管理
│   ├── billing.json                # 收费配置
│   ├── rates.json                  # 费率配置
│   ├── service_types.json          # 服务类型配置
│   ├── alert.json                  # 告警配置
│   ├── pushplus.json               # PushPlus 配置
│   └── wecom.json                  # 企微配置
├── tasks/                          # 后台任务
│   ├── maintenance_tasks.py        # 数据库维护任务
│   ├── photo_tasks.py              # 照片处理任务
│   └── reminder_tasks.py           # 提醒任务
├── mcp/                            # MCP 协议支持
│   ├── server/                     # MCP 服务端
│   ├── shared/                     # 共享异常
│   └── types.py                    # 类型定义
├── frontend/                       # 前端项目
│   └── src/
│       ├── main.js                 # Vue 入口
│       ├── App.vue                 # 根组件
│       ├── router/index.js         # 路由配置
│       ├── stores/                 # Pinia 状态
│       ├── api/                    # API 封装 (24个TypeScript模块)
│       ├── types/                  # 类型定义 (index.ts + api.ts)
│       ├── composables/            # 组合式函数 (8 个)
│       ├── components/             # 组件库
│       ├── views/                  # 页面视图 (22 个)
│       ├── utils/                  # 工具函数
│       ├── plugins/                # 插件注册
│       └── constants/              # 常量定义
│   └── e2e/                        # E2E测试 (6个Playwright场景)
├── tests/                          # 后端测试
├── scripts/                        # 运维脚本
├── static/                         # 静态资源
├── templates/                      # Jinja2 模板
├── Dockerfile                      # Docker 构建
├── docker-compose.yml              # Docker Compose
├── gunicorn_config.py              # Gunicorn 配置
├── requirements.txt                # Python 依赖
├── VERSION.json                    # 版本信息
└── tickets.db                      # SQLite 数据库
```

---

## 5. 后端核心模块

### 5.1 应用入口与工厂

#### [app.py](file:///Users/supeng/Documents/botong-ticket-system/app.py)

应用入口文件，采用工厂模式创建 Flask 应用：

```python
from web.app_factory import create_app
app = create_app()
if __name__ == '__main__':
    app.run(port=5053)
```

#### [web/app_factory.py](file:///Users/supeng/Documents/botong-ticket-system/web/app_factory.py)

Flask 应用工厂，`create_app(testing=False)` 按顺序执行：

1. **Flask 实例 + 配置** — 加载 `.env`，设置 `BOTO_SECRET_KEY`（必须）、端口、调试模式
2. **日志系统** — `TimedRotatingFileHandler`，日志文件 `/tmp/boto-app.log`
3. **速率限制** — `flask_limiter`，默认 200000/day、30000/hour
4. **中间件** — 认证 (`init_auth`) + CSRF (`init_csrf`)
5. **Flask-Caching** — SimpleCache 或 RedisCache
6. **Flask-RESTx API** — Swagger 文档在 `/docs/`，API 前缀 `/api`
7. **DI 容器引导** — `bootstrap()` 注册所有服务和事件
8. **路由注册** — SPA 静态文件、认证路由、Web 页面路由
9. **全局错误处理器** — 领域异常 → HTTP 状态码映射

**关键配置项：**

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `BOTO_SECRET_KEY` | 无（必须设置） | Flask 密钥 |
| `BOTO_PORT` | 5053 | 服务端口 |
| `BOTO_DEBUG` | 0 | 调试模式 |
| `BOTO_NO_RATE_LIMIT` | 空 | 关闭限流 |
| `BOTO_CACHE_TYPE` | SimpleCache | 缓存类型 |
| `MAX_CONTENT_LENGTH` | 10MB | 上传限制 |

### 5.2 API 层 (api/v1/)

所有 API 端点以 Blueprint 形式注册，统一前缀 `/api/v1/`。每个模块通过 `register_blueprint(flask_app)` 函数注册路由。

#### 统一响应格式 — [responses.py](file:///Users/supeng/Documents/botong-ticket-system/api/v1/responses.py)

```python
class ApiResponse:
    @staticmethod
    def success(data=None, message="操作成功")     # 200
    @staticmethod
    def created(data=None, message="创建成功")      # 201
    @staticmethod
    def error(message="操作失败", code=400)         # 4xx/5xx
    @staticmethod
    def paginated(data, total, page, per_page)      # 分页
```

#### API 端点一览

| 模块 | 文件 | 主要端点 |
|------|------|---------|
| **工单** | `tickets.py` | CRUD、状态流转、服务项、物料、照片、计时器、折扣、NLP解析、批量操作、利润查询 |
| **客户** | `clients.py` | CRUD、客户画像、级别配置 |
| **财务** | `finance.py` | 收入记录、收款(单笔/批量)、快捷记账、销售报表、利润分析、应收款、对账单、支出 |
| **库存** | `inventory.py` | 库存概览、变动记录、调整、调拨、盘点、销售记录、预警 |
| **设备** | `equipment.py` | CRUD、照片、关联工单、维保记录、组件、QR码、导入模板 |
| **商品** | `goods.py` | CRUD、分类管理、类型管理 |
| **技术员** | `technicians.py` | CRUD、汇总、统计、利润排行、参与工单 |
| **仪表盘** | `dashboard.py` | 汇总统计、库存预警 |
| **支出** | `expenses.py` | 分类、记录、个人费用、预算、循环支出 |
| **采购** | `purchase.py` | CRUD、收货、付款、未付款列表 |
| **服务费率** | `service_fees.py` | CRUD |
| **供应商** | `suppliers.py` | CRUD |
| **待办** | `todos.py` | CRUD、完成、重复规则 |
| **搜索** | `search.py` | 全局搜索（工单/设备/客户/商品/供应商/服务项目） |
| **统计** | `stats.py` | 数据统计与分析 |
| **提醒** | `reminders.py` | CRUD、激活/停用 |
| **工具** | `tools.py` | 文件导出（CSV/Excel） |
| **健康** | `health.py` | 系统健康检查 |
| **PushPlus** | `pushplus.py` | 推送配置与测试 |
| **企微** | `wecom.py` | 企微推送配置与测试 |
| **库存辅助** | `stock_aux.py` | 库存策略与分析 |

#### 参数校验 — [validators/schemas.py](file:///Users/supeng/Documents/botong-ticket-system/api/validators/schemas.py)

使用 Pydantic v2 模型进行请求参数校验，主要模型包括：

- `TicketCreateSchema` — 工单创建校验
- `ClientCreateSchema` — 客户创建校验
- 其他各模块对应的 Schema

### 5.3 应用服务层 (application/services/)

服务层是业务逻辑的核心编排层，每个服务通过构造函数注入依赖（仓储 + 事件总线 + 其他服务）。

#### [ticket_service.py](file:///Users/supeng/Documents/botong-ticket-system/application/services/ticket_service.py) — ⭐ 核心服务

**TicketService** 是系统最核心的服务，管理工单的完整生命周期。

| 方法 | 功能 |
|------|------|
| `create_ticket(data)` | 创建工单，发布 `TicketCreated` 事件 |
| `update_ticket(ticket_id, data)` | 更新工单信息 |
| `delete_ticket(ticket_id)` | 安全删除（软删除），发布 `TicketDeleted` 事件 |
| `complete_ticket(ticket_id)` | 完工结算，计算金额，生成财务记录，发布 `TicketCompleted` 事件 |
| `list_tickets(filters, page, per_page)` | 工单列表（分页+筛选） |
| `get_ticket(ticket_id)` | 工单详情 |
| `add_service_item(ticket_id, data)` | 添加服务明细行 |
| `update_service_item(item_id, data)` | 更新服务明细行 |
| `remove_service_item(item_id)` | 删除服务明细行 |
| `add_material(ticket_id, data)` | 添加材料行 |
| `update_material(material_id, data)` | 更新材料行 |
| `remove_material(material_id)` | 删除材料行 |
| `change_status(ticket_id, new_status)` | 状态流转，发布 `TicketStatusChanged` 事件 |
| `confirm_payment(ticket_id, data)` | 收款确认，发布 `TicketPaymentConfirmed` 事件 |
| `set_discount(ticket_id, discount_type, discount_value)` | 设置折扣 |
| `start_timer(ticket_id)` / `stop_timer(ticket_id)` | 计时器控制 |
| `recalculate(ticket_id)` | 重新计算工单金额 |

**依赖注入：**
```python
TicketService(
    repo=TicketRepository,
    event_bus=EventBus,
    config=Settings,
    client_service=ClientService,
    finance_service=FinanceService,      # setter 注入（循环依赖）
    goods_service=GoodsService,
    inventory_service=InventoryService,
    equipment_service=EquipmentService,
    technician_service=TechnicianService,
    reminder_service=ReminderService,    # setter 注入
    todo_service=TodoService,            # setter 注入
)
```

#### [client_service.py](file:///Users/supeng/Documents/botong-ticket-system/application/services/client_service.py)

| 方法 | 功能 |
|------|------|
| `create_client(data)` | 创建客户 |
| `update_client(name, data)` | 更新客户 |
| `delete_client(name)` | 删除客户 |
| `get_client_profile(name)` | 客户画像（交易统计、信用评分、活跃度） |
| `list_clients(filters)` | 客户列表 |

#### [finance_service.py](file:///Users/supeng/Documents/botong-ticket-system/application/services/finance_service.py)

| 方法 | 功能 |
|------|------|
| `record_income(data)` | 记录收入 |
| `record_expense(data)` | 记录支出 |
| `confirm_payment(ticket_id, data)` | 工单收款确认 |
| `batch_confirm_payments(items)` | 批量收款 |
| `get_receivables(filters)` | 应收款查询 |
| `get_monthly_summary(start, end)` | 月度财务汇总 |
| `get_profit_analysis(filters)` | 利润分析 |
| `get_client_statement(client, start, end)` | 客户对账单 |
| `quick_entry(data)` | 快捷记账 |

#### [inventory_service.py](file:///Users/supeng/Documents/botong-ticket-system/application/services/inventory_service.py)

| 方法 | 功能 |
|------|------|
| `get_inventory_overview(filters)` | 库存概览 |
| `stock_in(data)` | 入库 |
| `stock_out(data)` | 出库 |
| `adjust_stock(data)` | 库存调整 |
| `transfer_stock(data)` | 库存调拨 |
| `check_stock(data)` | 库存盘点 |
| `get_stock_alerts()` | 库存预警 |
| `record_sale(data)` | 销售记录 |

#### [equipment_service.py](file:///Users/supeng/Documents/botong-ticket-system/application/services/equipment_service.py)

| 方法 | 功能 |
|------|------|
| `create_equipment(data)` | 创建设备 |
| `update_equipment(equip_id, data)` | 更新设备 |
| `delete_equipment(equip_id)` | 删除设备（软删除） |
| `list_equipment(filters)` | 设备列表 |
| `get_equipment(equip_id)` | 设备详情 |
| `add_photo(equip_id, data)` | 添加照片 |
| `add_maintenance_record(equip_id, data)` | 添加维保记录 |
| `link_ticket(equip_id, ticket_id)` | 关联工单 |

#### 其他服务

| 服务 | 文件 | 核心功能 |
|------|------|---------|
| DashboardService | `dashboard_service.py` | 汇总统计、工单状态分布、财务概览、库存预警 |
| PurchaseService | `purchase_service.py` | 采购订单 CRUD、收货、付款 |
| ReminderService | `reminder_service.py` | 预约提醒、待办提醒、库存预警、逾期催收 |
| SearchService | `search_service.py` | 全局搜索（6 个维度） |
| SupplierService | `supplier_service.py` | 供应商 CRUD |
| GoodsService | `goods_service.py` | 商品 CRUD |
| TodoService | `todo_service.py` | 待办 CRUD、完成、重复规则 |
| TicketExportService | `ticket_export_service.py` | CSV/Excel 导出 |
| TicketNlService | `ticket_nl_service.py` | 自然语言指令解析 |

### 5.4 领域层 (domain/)

#### [amount_calculator.py](file:///Users/supeng/Documents/botong-ticket-system/domain/amount_calculator.py) — ⭐ 金额计算器

**所有金额计算必须通过 `AmountCalculator`，禁止散落逻辑。** 内部使用 `Decimal` 类型确保精度，最终输出转 `float`。

```python
class AmountCalculator:
    @staticmethod
    def calc_labor_fee(techs_data, fee_rate=60.0) -> float
        # 劳务收入：按 billing_type 分 hourly/daily/package 三模式

    @staticmethod
    def calc_labor_cost(techs_data, cost_rate_lookup=None,
                        daily_cost_lookup=None,
                        package_cost_lookup=None) -> float
        # 人工成本：同上三模式，支持回调查找技术员费率

    @staticmethod
    def calc_material_fee(materials) -> float
        # 材料收费 = ∑(材料行 total)

    @staticmethod
    def calc_travel_fee(distance, rate) -> float
        # 交通费 = distance × rate

    @staticmethod
    def calc_discount(total, discount_type="", discount_value=0) -> tuple
        # 折扣：percent 百分比 / fixed 固定金额
        # 返回 (discount_amount, final_total)

    @staticmethod
    def calc_total(labor_fee, material_fee, travel_fee=0.0,
                   discount_type="", discount_value=0) -> float
        # 总额 = 劳务 + 材料 + 交通 − 折扣

    @staticmethod
    def calc_total_with_tax(total, tax_rate=0) -> tuple
        # 含税总金额，返回 (tax_amount, total_with_tax)

    @staticmethod
    def get_effective_fee_rate(ticket, client_rate_lookup=None,
                                service_fee_lookup=None) -> float
        # 有效费率优先级：客户专属 > 服务项目 > 默认 ¥60

    @staticmethod
    def apply_tier_discount(client_name, discount_override=None,
                            client_profile_lookup=None) -> Optional[Dict]
        # 客户级别折扣（可被手动折扣覆盖）
```

**辅助函数：**
- `_d(value)` — 安全转换为 Decimal
- `_f(value)` — Decimal 转为 float（四舍五入到 2 位）

#### [events.py](file:///Users/supeng/Documents/botong-ticket-system/domain/events.py) — 领域事件

**事件定义：**

| 事件类 | event_name | 触发场景 |
|--------|-----------|---------|
| `TicketCreated` | `ticket.created` | 创建工单 |
| `TicketStatusChanged` | `ticket.status_changed` | 工单状态变更 |
| `TicketCompleted` | `ticket.completed` | 工单完工 |
| `TicketPaymentConfirmed` | `ticket.payment_confirmed` | 收款确认 |
| `TicketDeleted` | `ticket.deleted` | 删除工单 |
| `TicketSettled` | `ticket.settled` | 工单结算 |
| `TicketCostSyncRequired` | `ticket.cost_sync_required` | 成本同步 |
| `TicketTaxUpdated` | `ticket.tax_updated` | 税额更新 |
| `ClientCreated` | `client.created` | 创建客户 |
| `ClientCreditFrozen` | `client.credit_frozen` | 客户信用冻结 |
| `IncomeRecorded` | `finance.income_recorded` | 记录收入 |
| `ExpenseRecorded` | `finance.expense_recorded` | 记录支出 |
| `TodoDue` | `todo.due` | 待办到期 |
| `EquipmentMaintenanceDue` | `equipment.maintenance_due` | 设备维保到期 |
| `InspectionPlanExecuted` | `inspection_plan.executed` | 巡检计划执行 |

**EventBus 类：**

```python
class EventBus:
    def register(event_name, handler)     # 注册处理器（支持装饰器模式）
    def unregister(event_name, handler)   # 取消注册
    def dispatch(event)                   # 分发事件（同步，处理器间隔离）
    def clear()                           # 清理（测试用）
```

**全局单例：** `get_event_bus()` / `reset_event_bus()`

#### [exceptions.py](file:///Users/supeng/Documents/botong-ticket-system/domain/exceptions.py) — 领域异常

异常继承体系：

```
TicketSystemError (基类)
├── TicketNotFoundError          # 404
├── TicketValidationError        # 400
├── TicketStatusError            # 400
├── TicketAssignmentError        # 400
├── InventoryError               # 400
│   ├── InventoryNotEnoughError
│   └── InventoryLockError
├── EquipmentError               # 400
│   └── EquipmentMaintenanceError
├── DatabaseError                # 500
├── ConfigError                  # 500
├── BillingError                 # 400
│   └── DuplicateBillingError
├── SaleError / PriceError / PaymentError / RefundError  # 400
├── TechnicianNotFoundError      # 404
├── TechnicianRateError          # 400
├── ClientNotFoundError          # 404
├── ClientCreditError            # 400
├── GoodsNotFoundError           # 404
├── GoodsStockError              # 400
├── SupplierNotFoundError        # 404
├── PurchaseOrderError           # 400
│   └── PurchaseOrderStatusError
├── WarehouseError / WarehouseStockError / StockTransferError  # 400
├── AuthorizationError           # 403
├── RateLimitError               # 403
├── ValidationError              # 400
├── ConcurrencyError             # 500
└── IdempotencyError             # 500
```

#### [repositories/interfaces.py](file:///Users/supeng/Documents/botong-ticket-system/domain/repositories/interfaces.py) — 仓储接口

定义了核心仓储的抽象基类：

| 接口 | 方法 |
|------|------|
| `TicketRepository` | `find_by_id`, `find_list`, `save`, `update`, `delete`, `add_history`, `link_equipment`, `add_technician` |
| `ClientRepository` | `find_by_name`, `find_list`, `save`, `update`, `delete` |
| `FinanceRepository` | `record_income`, `record_expense`, `get_monthly_income`, `get_monthly_expense` |
| `TodoRepository` | `find_by_id`, `find_list`, `save`, `update`, `delete` |

### 5.5 基础设施层 (infrastructure/)

#### 依赖注入 — `di/`

| 文件 | 类/函数 | 功能 |
|------|---------|------|
| `container.py` | `Container` | 轻量级 DI 容器，支持 `register`/`register_instance`/`register_lazy`/`resolve` |
| `bootstrap.py` | `bootstrap(flask_app)` | 启动引导：注册所有仓储→服务→事件→调度器→路由 |
| `service_injection.py` | `inject_service(name)` | 从 Flask app context 获取服务实例 |
| `service_locator.py` | `reg` | 旧版全局定位器（已废弃） |

#### 数据持久化 — `persistence/`

| 文件 | 功能 |
|------|------|
| `database.py` | 数据库抽象接口 + 工作单元 |
| `legacy_db.py` | 旧版数据库工具（连接池、快捷查询、迁移支持） |
| `maintenance.py` | 数据库维护（VACUUM / ANALYZE / REINDEX） |
| `db_maintenance.py` | 维护调度（每日/每周维护 + 备份） |
| `migrations/` | 版本迁移脚本（v002 ~ v023） |

**仓储实现（15 个）：**

| 仓储 | 文件 | 核心表 |
|------|------|--------|
| `SqliteTicketRepository` | `ticket_repo.py` | tickets, history, ticket_service_items, materials, ticket_photos |
| `SqliteClientRepository` | `client_repo.py` | clients |
| `SqliteFinanceRepository` | `finance_repo.py` | income_records, expense_records |
| `SqliteInventoryRepository` | `inventory_repo.py` | inventory_items, inventory_logs |
| `SqliteEquipmentRepository` | `equipment_repo.py` | equipment, equipment_components, equipment_photos, maintenance_records |
| `GoodsRepo` | `goods_repo.py` | goods, goods_categories, goods_types |
| `TechnicianRepo` | `technician_repo.py` | technicians |
| `SupplierRepo` | `supplier_repo.py` | suppliers |
| `ServiceFeeRepo` | `service_fee_repo.py` | service_fees |
| `SqliteDashboardRepository` | `dashboard_repo.py` | 聚合查询 |
| `SqliteTodoRepository` | `todo_repo.py` | todos |
| `SqliteNotificationRepository` | `notification_repo.py` | notifications |
| `SqliteReminderRepository` | `reminder_repo.py` | ticket_reminders |
| `StatsRepo` | `stats_repo.py` | 统计聚合查询 |
| `PurchaseRepo` | `purchase_repo.py` | purchase_orders, purchase_items |

#### 消息推送 — `messaging/`

| 文件 | 类 | 功能 |
|------|-----|------|
| `pushplus.py` | `PushPlusClient` | PushPlus 微信推送，支持 Markdown/文本消息 |
| `wecom.py` | `WeComBotClient` | 企业微信机器人推送，支持 Markdown/文本消息 |
| `event_subscribers.py` | `register_all_subscribers()` | 将事件处理器绑定到 EventBus |

**事件订阅映射：**

| 事件 | 处理器 | 动作 |
|------|--------|------|
| `ticket.created` | `_on_ticket_created` | 创建待办、发送通知 |
| `ticket.status_changed` | `_on_status_changed` | 状态变更通知 |
| `ticket.completed` | `_on_ticket_completed` | 完工通知 |
| `ticket.payment_confirmed` | `_on_payment_confirmed` | 收款通知 |
| `finance.income_recorded` | `_on_income_recorded` | 收入通知 |
| `equipment.maintenance_due` | `_on_maintenance_due` | 维保提醒 |

#### 其他基础设施

| 文件 | 功能 |
|------|------|
| `scheduler.py` | APScheduler 定时任务调度器，注册 cron 任务 |
| `async_notify.py` | 异步通知发送（fire-and-forget） |
| `logging.py` | 结构化日志配置（JSON 格式 + 上下文绑定） |

### 5.6 中间件 (web/middleware/)

#### [auth.py](file:///Users/supeng/Documents/botong-ticket-system/web/middleware/auth.py) — 认证中间件

**机制：** HMAC 签名 Token + Cookie 自动续期

| 功能 | 说明 |
|------|------|
| Token 生成 | HMAC-SHA256 签名，包含时间戳 |
| Cookie 认证 | `bt_auth` Cookie，自动续期 |
| 暴力破解防护 | SQLite 存储 `login_attempts`，锁定机制 |
| 密码哈希 | 支持 bcrypt（自动降级 SHA-256） |
| 运行时改密 | `change_password()` 支持 |
| API/页面区分 | `_is_api_request()` 未认证 API 返回 401 JSON |

**公开路径白名单：** `/api/v1/csrf-token`、`/api/v1/login`、`/api/v1/logout`

#### [csrf.py](file:///Users/supeng/Documents/botong-ticket-system/web/middleware/csrf.py) — CSRF 保护

| 功能 | 说明 |
|------|------|
| Token 生成 | 随机 Token，绑定 Session |
| Token 验证 | 请求头 `X-CSRF-Token` 或表单字段 |
| 自动过期 | 定期清理过期 Token |
| 存储降级 | 内存 → Redis |
| API 接口 | `GET /api/v1/csrf-token` 获取 Token |

### 5.7 后台任务 (tasks/)

| 文件 | 任务 | 调度 |
|------|------|------|
| `maintenance_tasks.py` | `vacuum_database` — VACUUM + ANALYZE | 每周日 03:00 |
| `photo_tasks.py` | `process_photo` — 添加水印 + 保存记录 | 按需触发 |
| `reminder_tasks.py` | `check_reminders` — 检查并发送提醒 | 每分钟 |

---

## 6. 前端核心模块

### 6.1 入口与路由

#### [main.js](file:///Users/supeng/Documents/botong-ticket-system/frontend/src/main.js)

Vue 应用入口，初始化顺序：
1. 创建 Vue 应用
2. 安装 Pinia 状态管理
3. 安装 Vue Router
4. 注册全局错误处理器（`errorHandler` / `warnHandler`）
5. 挂载到 `#app`

#### [router/index.js](file:///Users/supeng/Documents/botong-ticket-system/frontend/src/router/index.js)

路由配置，基础路径 `/app/`，所有页面路由嵌套在 `AppLayout` 下：

| 路径 | 名称 | 组件 | 说明 |
|------|------|------|------|
| `/login` | Login | Login.vue | 登录页（公开） |
| `/` | Dashboard | Dashboard.vue | 仪表盘 |
| `/tickets` | Tickets | Tickets.vue | 工单列表 |
| `/tickets/new` | TicketCreate | TicketCreate.vue | 创建工单 |
| `/tickets/:id` | TicketDetail | TicketDetail.vue | 工单详情 |
| `/clients` | Clients | Clients.vue | 客户列表 |
| `/clients/:name` | ClientDetail | ClientDetail.vue | 客户详情 |
| `/equipment` | Equipment | Equipment.vue | 设备列表 |
| `/equipment/:id` | EquipmentDetail | EquipmentDetail.vue | 设备详情 |
| `/finance` | Finance | Finance.vue | 财务管理 |
| `/inventory` | Inventory | Inventory.vue | 库存管理 |
| `/purchase` | Purchase | Purchase.vue | 采购管理 |
| `/expenses` | Expenses | Expenses.vue | 支出管理 |
| `/todos` | Todos | Todos.vue | 待办事项 |
| `/warehouses` | Warehouses | Warehouses.vue | 仓库管理 |
| `/suppliers` | Suppliers | Suppliers.vue | 供应商 |
| `/service-fees` | ServiceFees | ServiceFees.vue | 服务费率 |
| `/staff` | Staff | Staff.vue | 员工管理 |
| `/notifications` | Notifications | Notifications.vue | 通知中心 |
| `/settings` | Settings | Settings.vue | 系统设置 |
| `/stats` | Stats | Stats.vue | 统计分析 |

**路由守卫：** `beforeEach` 检查认证状态，未认证重定向到登录页。

### 6.2 状态管理 (Pinia Stores)

#### [stores/auth.js](file:///Users/supeng/Documents/botong-ticket-system/frontend/src/stores/auth.js)

| 属性/方法 | 类型 | 说明 |
|----------|------|------|
| `isAuthenticated` | state | 认证状态 |
| `checkAuth()` | action | 检测 cookie 中 `bt_auth` 判断认证状态 |
| `login(password)` | action | 登录 |
| `logout()` | action | 登出 |

#### [stores/app.js](file:///Users/supeng/Documents/botong-ticket-system/frontend/src/stores/app.js)

| 属性/方法 | 类型 | 说明 |
|----------|------|------|
| `sidebarCollapsed` | state | 侧边栏折叠状态 |
| `theme` | state | 主题（亮/暗） |
| `toggleSidebar()` | action | 切换侧边栏 |
| `toggleTheme()` | action | 切换主题 |

### 6.3 API 层 (api/)

#### [api/client.js](file:///Users/supeng/Documents/botong-ticket-system/frontend/src/api/client.js) — ⭐ Axios 基底

```javascript
// 核心功能：
// 1. Axios 实例配置（baseURL、timeout、withCredentials）
// 2. 请求拦截器：自动附加 CSRF Token（fetchCsrfToken 统一来源）
// 3. 响应拦截器：401 重定向到 /login
// 4. 统一返回 response.data（API 响应解包）
```

#### API 模块一览

| 模块 | 文件 | 核心接口 |
|------|------|---------|
| 工单 | `tickets.js` | CRUD、状态变更、服务项、物料、照片、计时器、折扣 |
| 客户 | `clients.js` | CRUD、画像 |
| 财务 | `finance.js` | 收支记录、收款、对账单、利润 |
| 库存 | `inventory.js` | 出入库、调拨、盘点、预警、销售 |
| 设备 | `equipment.js` | CRUD、照片、维保、关联工单 |
| 商品 | `goods.js` | CRUD、分类、类型 |
| 仪表盘 | `dashboard.js` | 汇总统计、库存预警 |
| 支出 | `expenses.js` | 分类、记录、预算、循环支出 |
| 采购 | `purchase.js` | CRUD、收货、付款 |
| 服务费率 | `service-fees.js` | CRUD |
| 员工 | `staff.js` | 技术员管理 |
| 供应商 | `suppliers.js` | CRUD |
| 待办 | `todos.js` | CRUD |
| 搜索 | `search.js` | 全局搜索 |
| 工具 | `tools.js` | 导出（`exportXxx()` + `downloadBlob()`） |
| 统计 | `stats.js` | 数据统计 |
| 提醒 | `reminders.js` | CRUD |
| PushPlus | `pushplus.js` | 推送配置 |
| 企微 | `wecom.js` | 推送配置 |
| 仓库 | `warehouses.js` | CRUD |
| 自然语言 | `nl.js` | NLP 指令 |
| 认证 | `auth.js` | 修改密码 |

### 6.4 组合式函数 (composables/)

#### 基础 Composables

| 函数 | 文件 | 功能 |
|------|------|------|
| `useApi(apiFn)` | `useApi.js` | 通用 API 请求封装，自带 AbortController 请求取消、loading/error 状态 |
| `useAutoSave(ref, saveFn)` | `useAutoSave.js` | 表单自动保存（debounce） |
| `useConfirm()` | `useConfirm.js` | 统一确认弹窗 |
| `useFormValidation(rules)` | `useFormValidation.js` | 表单校验逻辑 |
| `useImageCompress()` | `useImageCompress.js` | 图片压缩 |
| `useInfiniteScroll(loadFn)` | `useInfiniteScroll.js` | 无限滚动加载 |
| `usePagination(apiFn)` | `usePagination.js` | 分页逻辑封装 |
| `useToast()` | `useToast.js` | Toast 消息通知（`showToast(msg, type)`） |

#### 优化功能 Composables（v4.0）

**核心层 TypeScript Composables** (`core/composables/`):

| 函数 | 文件 | 功能 | 完成日期 |
|------|------|------|----------|
| `useCommandPalette()` | `useCommandPalette.ts` | 命令面板（Cmd+K），全局搜索工单/客户/快捷命令 | 2026-05-31 |
| `useKeyboardShortcuts()` | `useKeyboardShortcuts.ts` | 全局快捷键系统（Ctrl+N/S/T等） | 2026-05-31 |
| `useDebounce()` | `useDebounce.ts` | 统一防抖机制（300ms延迟） | 2026-05-31 |
| `useHapticFeedback()` | `useHapticFeedback.ts` | 触觉反馈（移动端震动） | 2026-05-31 |
| `useOfflineSync()` | `useOfflineSync.ts` | 离线同步机制（网络检测+自动同步） | 2026-05-31 |
| `useVoiceInput()` | `useVoiceInput.ts` | 语音输入（Web Speech API，支持中文） | 2026-05-31 |
| `useBatchOperations()` | `useBatchOperations.ts` | 批量操作（多选/全选/批量删除/更新） | 2026-05-31 |

**使用示例**:

```typescript
// 命令面板
import { useCommandPalette } from '@/core/composables/useCommandPalette'
const { open, close, search } = useCommandPalette()

// 防抖
import { useDebounce } from '@/core/composables/useDebounce'
const { debouncedValue, setValue } = useDebounce(300)

// 离线同步
import { useOfflineSync } from '@/core/composables/useOfflineSync'
const { isOnline, syncPendingChanges, setupNetworkListeners } = useOfflineSync()

// 语音输入
import { useVoiceInput } from '@/core/composables/useVoiceInput'
const { isListening, transcript, startListening, stopListening } = useVoiceInput({ lang: 'zh-CN' })

// 批量操作
import { useBatchOperations } from '@/core/composables/useBatchOperations'
const { selectedIds, hasSelection, toggleSelection, batchDelete } = useBatchOperations<Ticket>()
```

### 6.5 组件体系

#### 布局组件 (components/layout/)

| 组件 | 功能 |
|------|------|
| `AppLayout.vue` | 主布局框架：侧边栏 + 顶栏 + 内容区 + 返回顶部 + 移动端底栏 |
| `AppSidebar.vue` | 侧边导航菜单：折叠/展开、分组、子菜单、路由高亮 |
| `AppTopBar.vue` | 顶部导航栏：全局搜索、主题切换、通知图标 |

#### 通用组件 (components/common/)

| 组件 | 功能 |
|------|------|
| `BtModal.vue` | 通用模态框（Teleport、暗色主题、自定义按钮） |
| `ConfirmDialog.vue` | 确认对话框（确认/警告/危险类型） |
| `GlobalSearch.vue` | 全局搜索弹窗（Ctrl+K、键盘导航、搜索历史） |
| `KeyboardShortcuts.vue` | 快捷键帮助面板 |
| `LoadingSkeleton.vue` | 加载骨架屏（内联/页面/卡片/表格） |
| `NLPanel.vue` | AI 助手面板（Ctrl+Shift+A） |
| `PhotoPreview.vue` | 照片预览（上/下导航、缩略图指示器） |
| `StatCard.vue` | 统计数据卡片 |
| `StatusBadge.vue` | 状态标签（多类型） |
| `ToastContainer.vue` | Toast 通知容器（自动消失、手动关闭） |

#### 选择器组件 (components/selectors/)

| 组件 | 功能 |
|------|------|
| `SearchableSelect.vue` | 可搜索下拉选择（异步搜索、自定义渲染、创建新条目） |
| `ClientSelector.vue` | 客户选择器（基于 SearchableSelect） |
| `GoodsSelector.vue` | 商品选择器（显示库存+单价、缓存优化） |
| `ServiceFeeSelector.vue` | 服务费率选择器 |

#### 工单组件 (components/tickets/)

| 组件 | 功能 |
|------|------|
| `TicketMaterials.vue` | 工单材料管理 |
| `TicketPaymentBar.vue` | 工单支付信息栏 |
| `TicketPhotos.vue` | 工单照片管理 |
| `TicketServiceItems.vue` | 工单服务项目 |
| `TicketStatCards.vue` | 工单统计卡片 |
| `TicketStatusPanel.vue` | 工单状态面板（状态变更） |

### 6.6 页面视图 (views/)

| 视图 | 功能 | 关键特性 |
|------|------|---------|
| `Dashboard.vue` | 仪表盘 | 工单统计、财务概览、库存预警、待办 |
| `Tickets.vue` | 工单列表 | 筛选、排序、分页、批量操作 |
| `TicketCreate.vue` | 创建工单 | 模板选择器、客户/技术员/服务项目选择 |
| `TicketDetail.vue` | 工单详情 | 状态流转、服务项、物料、照片、计时器、折扣 |
| `Clients.vue` | 客户列表 | 搜索、创建、编辑 |
| `ClientDetail.vue` | 客户详情 | 画像、工单历史、财务记录 |
| `Equipment.vue` | 设备列表 | 搜索、筛选、QR码 |
| `EquipmentDetail.vue` | 设备详情 | 组件、照片、维保记录、关联工单 |
| `Finance.vue` | 财务管理 | 收支记录、利润分析、对账单 |
| `Inventory.vue` | 库存管理 | 出入库、调拨、盘点、预警 |
| `Purchase.vue` | 采购管理 | 采购单、收货、付款 |
| `Expenses.vue` | 支出管理 | 分类、记录、预算 |
| `Staff.vue` | 员工管理 | 技术员信息、绩效 |
| `ServiceFees.vue` | 服务费率 | 费率 CRUD |
| `Suppliers.vue` | 供应商 | CRUD |
| `Todos.vue` | 待办事项 | 创建、完成、重复规则 |
| `Warehouses.vue` | 仓库管理 | CRUD |
| `Notifications.vue` | 通知中心 | 通知列表、已读标记 |
| `Settings.vue` | 系统设置 | 自动化规则、推送配置、密码修改 |
| `Stats.vue` | 统计分析 | 图表、报表 |
| `Login.vue` | 登录页 | 密码登录 |
| `NotFound.vue` | 404 页面 | 友好提示 + 返回链接 |

### 6.7 工具与插件

| 文件 | 功能 |
|------|------|
| `utils/constants.js` | 全局常量（页面标题映射、状态定义） |
| `utils/format.ts` | 数据格式化（金额、日期、费率显示 `formatRate`） |
| `plugins/chart.js` | Chart.js 集中注册（不内联） |
| `constants/keepAlive.js` | KeepAlive 缓存页面列表 |

---

## 7. 数据库设计

### 7.1 核心表结构

数据库使用 SQLite（`tickets.db`），共 44 张表。

#### 工单核心表

**tickets** — 工单主表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| ticket_no | TEXT | 工单编号 |
| title | TEXT | 标题 |
| client | TEXT | 客户名称 |
| description | TEXT | 描述 |
| status | TEXT | 状态（open/in_progress/completed/closed） |
| priority | TEXT | 优先级（H/M/L） |
| assignee | TEXT | 指派人 |
| billing_model | TEXT | 计费模式（hourly/daily/package） |
| billing_status | TEXT | 结算状态（unpaid/partially_paid/paid） |
| total | REAL | 总金额 |
| total_labor | REAL | 劳务金额 |
| total_material | REAL | 材料金额 |
| discount_type | TEXT | 折扣类型（percent/fixed） |
| discount_value | REAL | 折扣值 |
| tax_rate | REAL | 税率 |
| tax_amount | REAL | 税额 |
| total_with_tax | REAL | 含税总额 |
| travel_distance | REAL | 交通距离 |
| travel_rate | REAL | 交通费率 |
| service_fee_id | INTEGER | 关联服务费率 |
| timer_started_at | TEXT | 计时器启动时间 |
| appointment_at | TEXT | 预约时间 |
| created_at / updated_at / closed_at | TEXT | 时间戳 |

**ticket_service_items** — 服务明细行

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| ticket_id | INTEGER | 关联工单 |
| technician_name | TEXT | 技术员名称 |
| service_fee_id | INTEGER | 关联服务费率 |
| hours | REAL | 工时 |
| unit_price | REAL | 单价 |
| cost_price | REAL | 成本价 |
| line_total | REAL | 行收入 |
| line_cost | REAL | 行成本 |

**materials** — 材料行

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| ticket_id | INTEGER | 关联工单 |
| name / product_name | TEXT | 材料名称 |
| product_id / goods_id | INTEGER | 关联商品 |
| quantity | REAL | 数量 |
| unit_price | REAL | 单价 |
| total_cost | REAL | 成本合计 |
| total | REAL | 收费合计 |
| inventory_item_ids | TEXT | 关联库存项 IDs |
| sale_id | INTEGER | 关联销售记录 |

**history** — 操作日志

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| ticket_id | INTEGER | 关联工单 |
| action | TEXT | 操作类型 |
| note | TEXT | 备注 |
| operator | TEXT | 操作人 |
| timestamp | TEXT | 时间戳 |
| changes | TEXT | 变更内容 |

#### 客户表

**clients**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT UNIQUE | 客户名称 |
| contact / phone / email / address | TEXT | 联系信息 |
| hourly_rate | REAL | 小时费率 |
| annual_rate | REAL | 年费率 |
| payment_terms | INTEGER | 账期（天） |
| client_type / scope | TEXT | 客户类型/范围 |

#### 技术员表

**technicians**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT UNIQUE | 技术员名称 |
| billing_type | TEXT | 计费模式（hourly/daily/package） |
| cost_rate | REAL | 时薪成本率 |
| daily_rate | REAL | 天薪收费率 |
| daily_cost_rate | REAL | 天薪成本率 |
| package_rate | REAL | 包工收费率 |
| package_cost | REAL | 包工成本 |
| skills | TEXT | 技能 |
| status | TEXT | 状态 |

#### 财务表

**income_records** — 收入记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| source_type | TEXT | 来源类型 |
| source_id | INTEGER | 来源 ID |
| client | TEXT | 客户 |
| amount | REAL | 金额 |
| total_amount | REAL | 总金额 |
| tax_amount | REAL | 税额 |
| payment_method | TEXT | 支付方式 |
| received_at | TEXT | 收款时间 |

**expense_records** — 支出记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| related_ticket_id | INTEGER | 关联工单 |
| category | TEXT | 分类 |
| description | TEXT | 描述 |
| amount | REAL | 金额 |
| is_personal | INTEGER | 是否个人支出 |
| is_recurring | INTEGER | 是否循环支出 |

#### 库存表

**inventory_items** — 库存项

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| product_id | INTEGER FK | 关联商品 |
| warehouse_id | INTEGER FK | 关联仓库 |
| status | TEXT | 状态（in_stock/out_sold/out_used/reserved） |
| unit_cost | REAL | 单位成本 |
| bulk_quantity | REAL | 批量数量 |
| ticket_id | INTEGER FK | 关联工单 |
| sale_id | INTEGER | 关联销售 |
| is_deleted | INTEGER | 软删除标记 |

**inventory_logs** — 库存流水

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| product_id | INTEGER FK | 关联商品 |
| item_id | INTEGER | 关联库存项 |
| type | TEXT | 变动类型 |
| quantity | REAL | 变动数量 |
| from_location / to_location | TEXT | 位置变更 |

#### 设备表

**equipment** — 设备主表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name / type / model | TEXT | 设备信息 |
| client | TEXT | 所属客户 |
| serial_no | TEXT | 序列号 |
| warranty_expire | TEXT | 保修到期 |
| maintenance_cycle | TEXT | 维保周期 |
| next_maintenance | TEXT | 下次维保 |
| is_deleted | INTEGER | 软删除标记 |

#### 商品表

**goods** — 商品主表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT | 商品名称 |
| category_id | INTEGER FK | 分类 |
| type_id | INTEGER FK | 类型 |
| retail_price / selling_price / cost_price | REAL | 价格体系 |
| min_stock | INTEGER | 最低库存 |
| is_subscription | INTEGER | 是否订阅商品 |
| sale_mode | TEXT | 销售模式 |

#### 采购表

**purchase_orders** — 采购订单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| po_no | TEXT UNIQUE | 采购单号 |
| supplier_id | INTEGER FK | 供应商 |
| status | TEXT | 状态（pending/received/partially_received/cancelled） |
| total_amount | REAL | 总金额 |
| payment_status | TEXT | 付款状态 |

**purchase_items** — 采购明细

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| po_id | INTEGER FK | 采购订单 |
| goods_id | INTEGER FK | 商品 |
| quantity / received_qty | REAL | 数量/已收数量 |
| unit_cost / total_cost | REAL | 成本 |

#### 其他表

| 表名 | 说明 |
|------|------|
| `service_fees` | 服务费率定义 |
| `suppliers` | 供应商信息 |
| `warehouses` | 仓库信息 |
| `locations` | 仓库库位 |
| `goods_categories` | 商品分类 |
| `goods_types` | 商品类型 |
| `ticket_photos` | 工单照片 |
| `ticket_reminders` | 工单提醒 |
| `ticket_equipment` | 工单-设备关联 |
| `ticket_technicians` | 工单-技术员关联（冗余） |
| `ticket_templates` | 工单模板 |
| `todos` | 待办事项 |
| `notifications` | 通知 |
| `expense_categories` | 支出分类 |
| `expense_budgets` | 支出预算 |
| `sales_records` | 销售记录 |
| `service_agreements` | 包年协议 |
| `inspection_plans` | 巡检计划 |
| `inspection_records` | 巡检记录 |
| `maintenance_reports` | 维保报告 |
| `automation_rules` | 自动化规则 |
| `audit_log` / `audit_log_archive` | 审计日志 |
| `login_attempts` | 登录尝试（暴力破解防护） |
| `mcp_config` | MCP 配置 |
| `_schema_version` | 数据库版本 |
| `_idempotent_cache` | 幂等性缓存 |

### 7.2 实体关系图

```
clients ──1:N── tickets ──1:N── ticket_service_items ──N:1── service_fees
                  │                    └── 关联 technicians (technician_name)
                  ├──1:N── materials ──N:1── goods
                  ├──1:N── ticket_photos
                  ├──1:N── ticket_reminders
                  ├──1:N── ticket_equipment ──N:1── equipment
                  └──1:1── service_agreements

equipment ──1:N── equipment_components
           ├──1:N── equipment_photos
           ├──1:N── maintenance_records
           └──1:N── ticket_equipment

goods ──N:1── goods_categories
       ├──N:1── goods_types
       ├──1:N── inventory_items ──N:1── warehouses
       │                  └──1:N── inventory_logs
       └──1:N── purchase_items ──N:1── purchase_orders ──N:1── suppliers

income_records ── 关联 tickets / clients
expense_records ── 关联 tickets / expense_categories
sales_records ── 关联 tickets / goods / clients
```

### 7.3 数据库迁移

迁移脚本位于 `infrastructure/persistence/migrations/versions/`，版本从 v002 到 v023。

迁移框架通过 `_schema_version` 表跟踪已应用的版本。每个迁移脚本包含 `upgrade()` 和 `downgrade()` 方法。

---

## 8. 依赖注入与事件系统

### 8.1 DI 容器

[Container](file:///Users/supeng/Documents/botong-ticket-system/infrastructure/di/container.py) 是一个轻量级依赖注入容器，线程安全（`threading.RLock`）。

**核心 API：**

```python
Container.register(name, factory, singleton=True)   # 注册工厂
Container.register_instance(name, instance)          # 注册实例
Container.register_lazy(name, module_path, class_name) # 懒加载注册
Container.resolve(name)                              # 解析服务
Container.has(name)                                  # 检查注册
Container.set_config(key, value)                     # 设置配置
Container.get_config(key, default)                   # 获取配置
Container.reset()                                    # 重置（测试用）
```

**解析优先级：** 实例缓存 → 工厂创建 → 懒加载 → 抛出 KeyError

### 8.2 事件总线

[EventBus](file:///Users/supeng/Documents/botong-ticket-system/domain/events.py) 是同步事件总线，支持装饰器模式注册：

```python
event_bus = get_event_bus()

# 装饰器模式
@event_bus.register("ticket.created")
def on_ticket_created(event):
    ...

# 直接注册
event_bus.register("ticket.created", handler)

# 分发事件
event_bus.dispatch(TicketCreated(ticket_id=1, ticket_no="T001"))
```

**特性：** 处理器间隔离（一个失败不影响其他），支持异步模式（通过任务队列代理）。

### 8.3 启动引导流程

[bootstrap()](file:///Users/supeng/Documents/botong-ticket-system/infrastructure/di/bootstrap.py) 按以下顺序初始化：

```
1. 初始化数据库表与索引 (init_indexes)
2. 注册配置 (settings)
3. 注册事件总线 (event_bus)
4. 注册仓储 (15 个 Repository)
5. 注册服务 (14 个 Service)
   ├── 解决循环依赖（setter 注入）
   └── TicketService ← FinanceService / ReminderService / TodoService
6. 注册消息推送 (WeComBot / PushPlus)
7. 注册缓存 (SimpleCache / RedisCache)
8. 启动 APScheduler 调度器
9. 注册事件订阅 (event_subscribers)
10. 注册 API 路由 (21 个 Blueprint)
11. 注入服务到 Flask app context
```

**循环依赖处理：** TicketService 与 FinanceService/ReminderService/TodoService 之间存在循环依赖，通过 setter 方法延迟注入解决：

```python
_ts = Container.resolve("ticket_service")
_ts.set_finance_service(Container.resolve("finance_service"))
_ts.set_reminder_service(Container.resolve("reminder_service"))
_ts.set_todo_service(Container.resolve("todo_service"))
```

---

## 9. 认证与安全

### 9.1 认证机制

系统采用 **HMAC 签名 Token + Cookie** 的认证方式：

1. **登录：** `POST /api/v1/login`，验证密码后生成 HMAC-SHA256 签名 Token
2. **Cookie：** 设置 `bt_auth` Cookie，包含签名 Token
3. **自动续期：** 每次请求自动检查并续期 Cookie
4. **暴力破解防护：** 基于 SQLite 的 `login_attempts` 表，记录失败次数和锁定时间
5. **密码存储：** 支持 bcrypt（优先）和 SHA-256（降级）

### 9.2 CSRF 保护

- Token 通过 `GET /api/v1/csrf-token` 获取
- 请求通过 `X-CSRF-Token` 头或表单字段提交
- Token 绑定 Session，自动过期清理
- 前端统一通过 `api/client.js` 的 `fetchCsrfToken()` 获取

### 9.3 领域异常体系

所有业务异常继承自 `TicketSystemError`，在 `app_factory.py` 中注册全局错误处理器，自动映射为 HTTP 状态码：

| 异常类别 | HTTP 状态码 |
|---------|------------|
| NotFound 类 | 404 |
| Validation / Status / Business 类 | 400 |
| Authorization / RateLimit 类 | 403 |
| Database / Config / Concurrency 类 | 500 |

---

## 10. 配置体系

### 统一配置管理 — [config/manager.py](file:///Users/supeng/Documents/botong-ticket-system/config/manager.py)

合并了 `settings.py` 和 `manager.py`，提供统一配置访问接口。

### JSON 配置文件

| 文件 | 内容 |
|------|------|
| `billing.json` | 收费配置：自动发票、税务计算、默认税率 |
| `rates.json` | 客户费率：按客户设置小时费率或年费率 |
| `service_types.json` | 服务类型：关键词匹配规则用于自动识别 |
| `alert.json` | 告警配置：临界阈值、警告阈值 |
| `pushplus.json` | PushPlus 推送：Token、推送事件开关 |
| `wecom.json` | 企微推送：Webhook URL、推送事件开关 |

### 环境变量

| 变量 | 必须 | 默认值 | 说明 |
|------|------|--------|------|
| `BOTO_SECRET_KEY` | ✅ | — | Flask 密钥 |
| `BOTO_ACCESS_PASSWORD` | ✅ | — | 登录密码 |
| `BOTO_PORT` | ❌ | 5053 | 服务端口 |
| `BOTO_DEBUG` | ❌ | 0 | 调试模式 |
| `REDIS_URL` | ❌ | — | Redis 连接 |
| `BOTO_CACHE_TYPE` | ❌ | SimpleCache | 缓存类型 |
| `BOTO_NO_RATE_LIMIT` | ❌ | — | 关闭限流 |
| `BOTO_LOG_LEVEL` | ❌ | info | 日志级别 |
| `BOTO_WORKERS` | ❌ | 2 | Gunicorn Worker 数 |
| `BOTO_THREADS` | ❌ | 4 | Gunicorn 线程数 |

---

## 11. 部署与运维

### 本地开发

```bash
# 后端
source .venv/bin/activate
python app.py                    # 端口 5053

# 前端
cd frontend
npm install
npm run dev                      # Vite 自动分配端口

# 前端构建
cd frontend && npx vite build    # 输出到 frontend/dist/
```

### Docker 部署

**Dockerfile** — 多阶段构建：

1. 前端构建阶段：Node.js 构建 Vue 应用
2. 后端运行阶段：Python + Gunicorn

**docker-compose.yml** 服务：

| 服务 | 说明 |
|------|------|
| `web` | Flask + Gunicorn 主服务 |
| `worker` | 后台任务 Worker |
| `redis` | 可选缓存/队列 |
| `nginx` | 反向代理 |

### Gunicorn 配置 — [gunicorn_config.py](file:///Users/supeng/Documents/botong-ticket-system/gunicorn_config.py)

```python
bind = "0.0.0.0:5053"
workers = int(os.environ.get("BOTO_WORKERS", 2))
threads = int(os.environ.get("BOTO_THREADS", 4))
```

### 运维脚本

| 脚本 | 功能 |
|------|------|
| `scripts/backup_db.sh` | 数据库备份 |
| `scripts/setup.sh` | 初始安装 |
| `scripts/manage.sh` | 管理命令 |
| `scripts/seed_test_data.py` | 填充测试数据 |
| `scripts/clear_test_data.py` | 清理测试数据 |
| `scripts/pre_launch_check.py` | 启动前检查 |
| `scripts/migrate.py` | 数据库迁移 |
| `scripts/check_sqlite.py` | SQLite 检查 |
| `scripts/sync-repowiki.sh` | 同步 RepoWiki 文档 |

### macOS LaunchAgent

`scripts/com.boto.ticket.plist` — macOS 开机自启配置。

---

## 12. 测试体系

### 后端测试

```bash
pytest tests/ -v
```

| 测试文件 | 覆盖模块 |
|---------|---------|
| `test_amount_calculator.py` | 金额计算器 |
| `test_api.py` | API 端点 |
| `test_app_factory.py` | 应用工厂 |
| `test_equipment_service.py` | 设备服务 |
| `test_finance_service.py` | 财务服务 |
| `test_inventory_service.py` | 库存服务 |
| `test_new_architecture.py` | DDD 架构 |
| `test_purchase_service.py` | 采购服务 |
| `test_ticket_api.py` | 工单 API |
| `test_validators.py` | 参数校验 |

**当前状态：** 194 passed, 45 skipped

### 前端测试

```bash
cd frontend && npx vitest run
```

| 测试文件 | 覆盖模块 |
|---------|---------|
| `client.test.js` | Axios 客户端 |
| `useApi.test.js` | useApi 组合式函数 |
| `useAutoSave.test.js` | 自动保存 |
| `useConfirm.test.js` | 确认弹窗 |
| `useFormValidation.test.js` | 表单校验 |
| `useImageCompress.test.js` | 图片压缩 |
| `useInfiniteScroll.test.js` | 无限滚动 |
| `usePagination.test.js` | 分页 |
| `useToast.test.js` | Toast 通知 |

**当前状态：** 65 passed (9 文件)

---

## 13. 关键业务流程

### 13.0 性能优化功能（v4.0）

#### 核心优化成果

**阶段1: P0核心瓶颈修复**
- **命令面板**: Cmd+K全局搜索，支持工单/客户/快捷命令
- **快捷键系统**: Ctrl+N/S/T等全局快捷键，提升操作效率
- **虚拟滚动**: vue-virtual-scroller，DOM节点减少90%，渲染速度提升10倍
- **API字段过滤**: fields参数支持，响应体积减少60%
- **防抖机制**: 统一300ms防抖，减少无效API调用

**阶段2: P1体验增强**
- **骨架屏**: LoadingSkeleton组件增强，shimmer动画，加载感知速度提升80%
- **触觉反馈**: useHapticFeedback，移动端震动反馈
- **深色模式**: CSS Transition平滑切换，0.3s过渡动画
- **加载状态**: 完善的loading和error处理
- **移动端布局**: 响应式优化，触摸区域≥44px

**阶段3: P2高级功能**
- **离线同步**: useOfflineSync，网络检测+自动同步，弱网环境可用
- **语音输入**: useVoiceInput，Web Speech API，支持中文识别
- **批量操作**: useBatchOperations，多选/全选/批量删除/更新
- **数据导出**: CSV格式导出，UTF-8 BOM编码
- **性能监控**: API平均响应时间4.6ms，数据库查询0.45ms

#### 新增依赖

```json
{
  "vue-virtual-scroller": "^2.0.0-beta.8"
}
```

#### 性能指标

| 指标 | 优化前 | 优化后 | 提升幅度 |
|------|--------|--------|----------|
| 工单列表渲染时间 | ~5000ms | ~500ms | 10倍 |
| DOM节点数（100条） | ~100个 | ~10个 | 90%减少 |
| API响应体积 | 100% | 40% | 60%减少 |
| API平均响应时间 | - | 4.6ms | <500ms目标 |
| 数据库查询时间 | - | 0.45ms | 优秀 |
| FCP (首屏内容) | - | <1.5s | 达标 |
| LCP (最大内容) | - | <2.5s | 达标 |

#### 测试验证

自动化测试脚本：`tests/test_optimizations.py`
- 测试通过率：91.7% (11/12)
- 详细报告：[tests/OPTIMIZATION_TEST_REPORT.md](tests/OPTIMIZATION_TEST_REPORT.md)

---

### 13.1 工单生命周期

```
创建 (open)
  │
  ├── 添加服务明细行 (technician + service_fee + hours)
  ├── 添加材料行 (goods + quantity)
  ├── 上传现场照片
  ├── 设置折扣
  │
  ▼
进行中 (in_progress)
  │
  ├── 计时器 start/stop
  ├── 修改服务项/材料
  │
  ▼
完工 (completed)
  │
  ├── 自动计算金额 (AmountCalculator)
  │   ├── 劳务收入 = ∑(hours × fee_rate)  [按 billing_type]
  │   ├── 劳务成本 = ∑(hours × cost_rate) [按 billing_type]
  │   ├── 材料收费 = ∑(materials.total)
  │   ├── 交通费 = distance × rate
  │   ├── 折扣 = percent / fixed
  │   └── 总额 = 劳务 + 材料 + 交通 − 折扣
  ├── 生成财务记录 (UnitOfWork 事务)
  ├── 发布 TicketCompleted 事件
  │   └── 通知推送 (WeCom / PushPlus)
  │
  ▼
结算 (settled/paid)
  │
  ├── 收款确认
  ├── 发布 TicketPaymentConfirmed 事件
  │
  ▼
关闭 (closed)
```

### 13.2 金额计算流程

```
TicketService.recalculate(ticket_id)
  │
  ├── 1. 获取有效费率
  │   └── AmountCalculator.get_effective_fee_rate()
  │       ├── 客户专属费率 (client_rate_lookup)  ← 最高优先
  │       ├── 服务项目费率 (service_fee_lookup)
  │       └── 默认费率 ¥60/h
  │
  ├── 2. 计算劳务收入
  │   └── AmountCalculator.calc_labor_fee(techs_data, fee_rate)
  │       ├── hourly: hours × fee_rate
  │       ├── daily: days × daily_fee_rate
  │       └── package: package_fee
  │
  ├── 3. 计算人工成本
  │   └── AmountCalculator.calc_labor_cost(techs_data, cost_rate_lookup)
  │       ├── hourly: hours × cost_rate
  │       ├── daily: days × daily_cost_rate
  │       └── package: package_cost
  │
  ├── 4. 计算材料费
  │   └── AmountCalculator.calc_material_fee(materials)
  │
  ├── 5. 计算交通费
  │   └── AmountCalculator.calc_travel_fee(distance, rate)
  │
  ├── 6. 应用折扣
  │   ├── 客户级别折扣 (apply_tier_discount)
  │   └── 手动折扣 (calc_discount)
  │
  ├── 7. 计算总额
  │   └── AmountCalculator.calc_total(...)
  │
  └── 8. 计算税额
      └── AmountCalculator.calc_total_with_tax(total, tax_rate)
```

### 13.3 库存出入库流程

```
入库 (stock_in):
  采购收货 → purchase_items.received_qty 更新
           → inventory_items 创建 (status=in_stock)
           → inventory_logs 记录

出库 (stock_out):
  工单使用材料 → materials 创建
              → inventory_items 状态变更 (out_used/out_sold)
              → inventory_logs 记录

调拨 (transfer_stock):
  inventory_items 位置变更
  inventory_logs 记录 from_location → to_location

盘点 (check_stock):
  inventory_items 数量校准
  inventory_logs 记录差异
```

---

## 14. 开发规范速查

### 启动与构建

```bash
source .venv/bin/activate && python app.py    # 后端 端口 5053
cd frontend && npm run dev                     # 前端开发
cd frontend && npx vite build                  # 前端构建
pytest tests/ -v                               # 后端测试
cd frontend && npx vitest run                  # 前端测试
```

### 代码分层规则

| 层 | 职责 | 禁止 |
|----|------|------|
| `api/v1/` | HTTP 请求/响应、参数校验 | 写业务逻辑 |
| `application/services/` | 业务编排、事务管理 | 直接操作 SQL |
| `domain/` | 纯业务规则、金额计算 | 依赖外部模块 |
| `infrastructure/` | 数据库、消息、DI | 含业务逻辑 |

### 关键约定

| 场景 | 规范 |
|------|------|
| 金额计算 | 必须走 `AmountCalculator`，禁止散落 |
| CSRF | `fetchCsrfToken()` 统一用 `api/client.js` |
| 导出 | `toolsApi.exportXxx()` + `downloadBlob()`，不用 `window.open` |
| Chart.js | 通过 `plugins/chart.js` 注册，不内联 |
| Toast | `useToast()` → `showToast(msg, type)` |
| 请求取消 | `useApi()` 自带 AbortController |
| 事件处理 | 通过 EventBus 发布/订阅，不直接调用 |

### 文件命名

| 类别 | 规则 | 示例 |
|------|------|------|
| View | PascalCase.vue | `TicketCreate.vue` |
| API | kebab-case.js | `service-fees.js` |
| Composable | useCamelCase.js | `useFormValidation.js` |
| Component | category/PascalCase.vue | `selectors/ClientSelector.vue` |
| Test | fileName.test.js | `useApi.test.js` |

### 唯一约束

`clients.name` · `technicians.name` · `suppliers.name` · `service_fees.name` · `goods_categories.name`

---

> 本文档基于项目代码自动分析生成，最后更新：2026-05-28
