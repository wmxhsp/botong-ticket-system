# 博通工单系统 — 个人运营指南

> v4.0 | 1人公司 IT 运维服务管理工具
> **核心利润 = 个人劳务收入 + 商品销售差价**

---

## 一、业务本质（1人运营版）

### 利润公式

| 利润线 | 公式 | 场景举例 |
|--------|------|----------|
| **个人劳务收入** | ∑收费单价 × 工时 | 上门修电脑，¥80/h × 2h = ¥160 |
| **用工劳务差价** | ∑(收费单价 − 成本单价) × 工时 | 派技术员上门，收¥80/h − 成本¥50/h = ¥30/h |
| **商品销售差价** | ∑(售价 − 进价) × 数量 | 卖网线 ¥15 − 进价 ¥8 = ¥7/根 |

> **用工合作说明**：忙不过来或技术不匹配时，按**时薪/包天/包工**方式雇佣合作技术员，赚取劳务差价。系统支持在工单中指定技术员并自动计算成本与利润。

### 计费模式（当前使用）

| 模式 | billing_type | 适用场景 | 状态 |
|------|-------------|----------|------|
| 时薪 | `hourly` | 上门维修、技术支持 | ✅ 主要使用 |
| 天薪 | `daily` | 驻场服务、长期项目 | ✅ 偶尔使用 |
| 包工 | `package` | 固定总价项目 | ✅ 偶尔使用 |

### 核心工作流（1人闭环）

```
客户报修 → 创建工单
  ├─ 服务明细：记录服务内容 + 工时 → 自动算劳务收入
  │         └─ 如派技术员：指定 technician + 计费模式 → 自动算成本与差价
  ├─ 材料记录：使用配件 + 数量 → 自动算材料收费
  ├─ 现场拍照 → 完工 → 生成结算单
  └─ 收款确认 → 收入入账
```

### 用工合作工作流

```
接到工单 → 评估是否自干
  ├─ 自干 → 按个人劳务收入结算
  └─ 外派 → 选择技术员 + 确定合作模式
            ├─ 时薪：记录工时，系统自动算 ¥收费 − ¥成本 = 差价
            ├─ 包天：记录天数，固定日薪成本
            └─ 包工：固定总价，利润 = 客户收费 − 包工费
```

### 1人运营关键指标

| 指标 | 计算方式 | 关注目的 |
|------|----------|----------|
| 日收入 | 当日完工工单收入合计 | 每日复盘 |
| 客单价 | 月收入 ÷ 完工工单数 | 定价策略 |
| 材料占比 | 材料收入 ÷ 总收入 | 是否需要增加配件销售 |
| 响应时效 | 接单到上门平均时间 | 服务质量 |
| 外派利润率 | 外派工单差价 ÷ 外派工单收入 | 评估合作技术员收益 |

---

## 二、技术架构（轻量级部署）

### 技术选型理由

| 技术 | 选择理由 |
|------|----------|
| Flask + SQLite | 零配置、单文件数据库、备份简单 |
| Vue 3 + Vite | 单页面应用、构建快速、学习成本低 |
| Bootstrap 5 | 无需设计基础，组件即用 |
| 本地部署 | 数据自主、无服务器成本、离线可用 |

### 后端结构

```
app.py                         # 入口（python app.py 启动）
├── api/v1/                    # API 接口
├── application/services/      # 业务逻辑
├── domain/
│   ├── amount_calculator.py   # 金额计算核心
│   └── repositories/          # 数据访问
├── infrastructure/
│   ├── persistence/           # 数据库操作
│   └── messaging/             # 企微机器人推送
└── config/                    # 配置文件
```

### 前端结构

```
frontend/src/
├── core/          # 核心基础设施（TS）
│   ├── api/       # API 客户端（统一响应格式）
│   ├── types/     # 统一类型定义
│   ├── stores/    # 全局状态（Pinia）
│   └── composables/  # 组合式函数（命令面板、快捷键、离线同步）
├── components/    # 通用组件
│   └── common/    # 公共组件（CommandPalette、QuickStats、ActivityStream）
├── modules/       # 业务模块（16个）
│   └── ticket/
│       └── views/ # QuickTicket（3秒创建）、QuickSettle（一键结算）
├── views/         # 页面
├── api/           # API 封装
└── stores/        # 状态管理
```

### 数据库核心关系

```
clients ──1:N── tickets ──1:N── ticket_service_items
                  ├──1:N── materials
                  ├──1:N── ticket_photos
                  └──1:1── service_agreements
```

### 金额计算器

**所有金额计算统一入口**：`domain/amount_calculator.py`

| 方法 | 功能 |
|------|------|
| `calc_labor_fee()` | 劳务收入（时薪/天薪/包工） |
| `calc_material_fee()` | 材料收费 |
| `calc_total()` | 工单总额 |

---

## 三、当前状态

### 数据现状

| 表 | 记录数 | 说明 |
|----|--------|------|
| clients | 4 | 测试客户（需录入真实费率） |
| technicians | 2 | 测试数据 |
| tickets | 1 | 测试工单 |
| goods | 14 | 配件商品库 |
| service_fees | 0 | 服务项目空（需配置常用服务） |
| suppliers | 0 | 供应商空 |

### 测试状态

| 维度 | 结果 |
|------|------|
| 后端测试 | 194 passed |
| 前端测试 | 65 passed |
| 前端构建 | ✅ 成功 |
| 类型检查 | ✅ 零错误 |

### UI v5 重构（2026-05-30）

**目标**：从重度使用者视角（每天50+次操作，每次<3秒）提升效率

**新增功能**：

| 功能 | 路径 | 说明 |
|------|------|------|
| 命令面板 | `Cmd+K` | 全局搜索工单、客户、快捷命令 |
| 快捷键系统 | `Ctrl+N/S/T` | 新建/结算/今日视图 |
| 双栏工单列表 | `/tickets` | 左侧列表+右侧详情滑出面板 |
| 快速创建 | `/tickets/quick` | 移动端3步流程，语音输入 |
| 一键结算 | `/tickets/:id/settle` | 大按钮调工时，扫码加材料 |
| 离线同步 | `core/stores/sync.ts` | 断网保存本地，恢复后自动同步 |

**技术改进**：
- 核心层 TypeScript 化（API、类型、状态、组合式函数）
- 统一 API 响应格式 `ApiResponse<T>`
- 统一类型定义，消除字段冗余
- 可访问性增强（ARIA 属性、键盘导航、焦点管理）

### MCP 服务配置（6个）

| 服务 | 功能 | 个人使用场景 |
|------|------|-------------|
| **SearXNG** | 网络搜索 | 查技术资料、找解决方案 |
| **SQLite** | 数据库查询 | 直接查业务数据、生成报表 |
| **Filesystem** | 文件访问 | 读取配置、查看日志 |
| **Fetch** | HTTP 请求 | 测试 API、查在线服务 |
| **Sequential Thinking** | 思维链 | 复杂问题分析、决策辅助 |
| **Puppeteer** | 浏览器自动化 | 截图、网页抓取 |

### Tailscale 远程访问

**用途**：通过 Tailscale VPN 网络安全访问工单系统

**配置方式**：

| 方式 | 说明 |
|------|------|
| **环境变量** | 在 `.env` 文件中设置 `BOTO_TAILSCALE_HOST` 和 `BOTO_HOST` |
| **配置文件** | 复制 `config/tailscale.example.json` 为 `config/tailscale.json` 并修改 |
| **启动脚本** | 使用 `scripts/start_tailscale.sh` 启动，自动检测并配置 |

**快速开始**：
```bash
# 1. 检查 Tailscale 状态
./scripts/check_tailscale.sh

# 2. 配置环境变量（或使用配置文件）
cp .env.example .env
# 编辑 .env，设置 BOTO_TAILSCALE_HOST 和 BOTO_HOST

# 3. 使用 Tailscale 模式启动
./scripts/start_tailscale.sh
```

**访问地址**：
- 本地访问：`http://localhost:5053`
- Tailscale 网络：`http://your-machine-name.tailxxxxx.ts.net:5053`

**安全提示**：
- 系统已有 HMAC 密码保护，无需额外配置
- 确保访问密码（`BOTO_ACCESS_PASSWORD`）足够强
- 建议启用 Tailscale 的 ACL 规则限制访问

### 开机启动

**一键安装**：

```bash
# 运行安装脚本（支持 macOS / Linux）
./scripts/install-boot.sh
```

**macOS 手动安装**：

```bash
# 1. 复制配置文件
cp scripts/com.boto.ticket.system.plist ~/Library/LaunchAgents/

# 2. 加载服务
launchctl load ~/Library/LaunchAgents/com.boto.ticket.system.plist

# 3. 查看状态
launchctl list | grep boto
```

**Linux 手动安装**：

```bash
# 1. 配置并安装服务
sed -e "s|%USER%|$(whoami)|g" \
    -e "s|%APP_DIR%|$(pwd)|g" \
    scripts/botong.service | sudo tee /etc/systemd/system/botong.service

# 2. 启用并启动
sudo systemctl daemon-reload
sudo systemctl enable --now botong

# 3. 查看状态
sudo systemctl status botong
```

**Windows 启动**：

```batch
# 直接双击运行
scripts\botong-start.bat

# 或者将快捷方式放入：
# C:\Users\你的用户名\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

**管理命令**：

| 平台 | 查看状态 | 启动 | 停止 | 重启 | 日志 |
|------|----------|------|------|------|------|
| macOS | `launchctl list \| grep boto` | `launchctl load ~/Library/LaunchAgents/com.boto.ticket.system.plist` | `launchctl unload ~/Library/LaunchAgents/com.boto.ticket.system.plist` | unload + load | `/tmp/boto-system.log` |
| Linux | `sudo systemctl status botong` | `sudo systemctl start botong` | `sudo systemctl stop botong` | `sudo systemctl restart botong` | `sudo journalctl -u botong -f` |
| Windows | 任务管理器 | 双击 bat | Ctrl+C | 重新双击 | 控制台输出 |

### 企业微信机器人

**用途**：向自己的微信发送通知提醒

**支持提醒**：
- 工单预约提醒（提前通知准备上门）
- 待办到期提醒（避免遗漏）
- 订阅到期提醒（客户包年服务续费）

---

## 四、1人运营效率指南

### 每日工作流建议

```
早上 5分钟    查看今日待办（todos + 预约工单）
      ↓
上门服务      手机拍照 → 完工后填工单 → 现场收款
      ↓
晚上 10分钟   补全工单详情 → 确认收入 → 查看今日统计
```

### 必配基础数据（首次使用）

1. **客户费率** - 在 clients 表设置 `hourly_rate`（默认¥60）
2. **服务项目** - 在 service_fees 配置常用服务（如"系统重装¥150"）
3. **商品库存** - 在 goods 录入常用配件（网线、水晶头、路由器等）
4. **供应商** - 在 suppliers 录入进货渠道
5. **合作技术员** - 在 technicians 配置合作人员及成本费率：
   - 时薪合作：`cost_rate` = 每小时支付费用（如¥50/h）
   - 包天合作：`daily_cost_rate` = 每天支付费用（如¥400/天）
   - 包工合作：`package_cost` = 固定总价（如¥800/项目）

### 自动化推荐（减少重复劳动）

| 功能 | 配置位置 | 效果 |
|------|----------|------|
| 工单预约提醒 | 企业微信机器人 | 提前30分钟微信通知 |
| 待办到期提醒 | 企业微信机器人 | 避免遗漏跟进 |
| 订阅到期提醒 | 企业微信机器人 | 提前催续费 |

### 数据备份策略

```bash
# 每日备份（建议加入定时任务）
cp tickets.db backups/tickets_$(date +%Y%m%d).db

# 关键数据导出
sqlite3 tickets.db ".dump" > backups/tickets_$(date +%Y%m%d).sql
```

---

## 五、AI 协作规范

### 5.1 信息溯源原则

**所有技术判断必须基于实际代码，禁止猜测。**

| 场景 | 正确做法 |
|------|----------|
| 数据库字段 | 查询 `sqlite_master` 或 Repository 代码 |
| API 端点 | 查看 `api/v1/` 目录下的实际文件 |
| 业务逻辑 | 查看 `domain/` 或 `application/` 代码 |
| 前端路由 | 查看 `router/index.js` 或模块 `routes.js` |

### 5.2 文档维护规则

**AGENTS.md 是系统的唯一真相源。**

**触发更新的场景：**
- [ ] 新增/修改数据库表或字段
- [ ] 新增/修改 API 端点
- [ ] 新增/修改业务逻辑（计费、折扣等）
- [ ] 新增/修改前端页面
- [ ] 新增/修改 MCP 服务器配置
- [ ] 技术栈变更

**更新流程：**
1. 代码变更完成后，立即检查 AGENTS.md 相关章节
2. 删除过时信息
3. 更新当前状态

### 5.3 变更影响检查

**任何变更前，评估影响范围：**

- [ ] 数据库变更 → 检查 Repository / Service / API
- [ ] API 变更 → 检查前端调用 / 测试用例
- [ ] 计费逻辑变更 → 检查 AmountCalculator / 历史工单

### 5.4 代码风格

- **后端**：Flask 蓝图、DDD 分层、Repository 模式
- **前端**：Vue 3 Composition API、模块自治
- **数据库**：snake_case、软删除（is_deleted）

### 5.5 安全红线

- ❌ 硬编码密码、密钥
- ❌ 将配置文件提交到版本控制
- ❌ 字符串拼接 SQL（必须用参数化查询）

### 5.6 测试验证

**变更后必须验证：**
- [ ] 后端：`pytest` 通过
- [ ] 前端：`npm run build` 成功
- [ ] API：手动测试新增/修改的端点
