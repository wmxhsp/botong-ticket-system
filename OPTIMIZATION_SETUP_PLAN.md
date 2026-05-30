# 博通工单系统 — 技能、插件与 MCP 优化改造方案

> 版本: v1.0 | 日期: 2026-05-29
> 目标: 全面提升开发效率、代码质量与系统智能化水平

---

## 一、现状分析

### 1.1 当前系统架构

| 层级 | 技术栈 | 状态 |
|------|--------|------|
| 后端 | Flask + DDD + SQLite | ✅ 稳定运行 |
| 前端 | Vue 3 + Vite + Pinia + Bootstrap 5 | ✅ 已迁移部分 TS |
| 测试 | pytest (后端) + vitest (前端) | ✅ 194 + 65 测试通过 |
| 部署 | python app.py (port 5053) | ✅ 正常运行 |

### 1.2 已安装依赖

**前端运行时**:
- `@vueuse/core` ^14.3.0 ✅
- `axios` ^1.7.0 ✅
- `bootstrap` ^5.3.3 ✅
- `chart.js` ^4.4.0 ✅
- `pinia` ^2.1.0 ✅
- `vue` ^3.4.0 ✅
- `vue-router` ^4.3.0 ✅
- `zod` ^4.4.3 ✅

**前端开发**:
- `@playwright/test` ^1.60.0 ✅
- `typescript` ^6.0.3 ✅
- `vitest` ^4.1.7 ✅
- `eslint` ^10.3.0 ✅
- `prettier` ^3.8.3 ✅

### 1.3 已配置 MCP

| MCP | 状态 | 用途 |
|-----|------|------|
| SQLite | ✅ | 数据库查询 |
| Filesystem | ✅ | 文件操作 |
| Fetch | ✅ | HTTP 请求 |
| Time | ✅ | 时间工具 |
| GitHub | ⚠️ | 需配置 Token |
| Slack | ⚠️ | 需配置 Token |
| Figma | ⚠️ | 需配置 API Key |
| Redis | ⚠️ | 需运行 Redis 服务 |

### 1.4 已安装技能

| 技能 | 状态 | 用途 |
|------|------|------|
| test-driven-development | ✅ | TDD 开发 |
| security-best-practices | ✅ | 安全审查 |
| mcp-builder | ✅ | MCP 开发 |
| writing-plans | ✅ | 计划制定 |

---

## 二、技能安装方案

### 2.1 推荐安装技能（按优先级）

#### 🔴 高优先级（立即安装）

| 技能 | 用途 | 适用场景 |
|------|------|----------|
| **vercel-react-best-practices** | React/Vue 性能优化 | 前端性能调优、组件优化 |
| **web-design-guidelines** | UI/UX 设计规范审查 | 界面设计审查、Accessibility |
| **git-commit** | 智能提交信息生成 | 规范化 Git 提交 |
| **dogfood** | 系统测试与 Bug 发现 | 功能测试、UX 问题发现 |

#### 🟡 中优先级（1-2 周内安装）

| 技能 | 用途 | 适用场景 |
|------|------|----------|
| **webapp-testing** | Playwright 测试增强 | E2E 测试编写、调试 |
| **frontend-design** | 前端界面设计 | 新页面设计、组件设计 |
| **shadcn** | shadcn/ui 组件管理 | UI 组件库维护 |
| **internal-comms** | 内部沟通文档 | 技术文档、更新报告 |

#### 🟢 低优先级（按需安装）

| 技能 | 用途 | 适用场景 |
|------|------|----------|
| **gh-cli** | GitHub CLI 操作 | 代码托管、PR 管理 |
| **figma** | Figma 设计稿转换 | 设计稿转代码 |
| **redis-development** | Redis 开发优化 | 缓存、消息队列 |
| **screenshot** | 截图工具 | 文档、测试报告 |

### 2.2 技能安装命令

```bash
# 高优先级
/enable-skill vercel-react-best-practices
/enable-skill web-design-guidelines
/enable-skill git-commit
/enable-skill dogfood

# 中优先级
/enable-skill webapp-testing
/enable-skill frontend-design
/enable-skill shadcn
/enable-skill internal-comms

# 低优先级（按需）
/enable-skill gh-cli
/enable-skill figma
/enable-skill redis-development
/enable-skill screenshot
```

---

## 三、前端插件/库安装方案

### 3.1 推荐安装（按优先级）

#### 🔴 高优先级（立即安装）

| 库/插件 | 版本 | 用途 | 安装命令 |
|---------|------|------|----------|
| **@vueuse/integrations** | latest | VueUse 扩展功能 | `npm i @vueuse/integrations` |
| **date-fns** | ^3.0.0 | 日期处理 | `npm i date-fns` |
| **lodash-es** | ^4.17.0 | 工具函数 | `npm i lodash-es` |
| **@types/lodash-es** | ^4.17.0 | Lodash 类型 | `npm i -D @types/lodash-es` |

#### 🟡 中优先级（1-2 周内安装）

| 库/插件 | 版本 | 用途 | 安装命令 |
|---------|------|------|----------|
| **vue-i18n** | ^9.0.0 | 国际化 | `npm i vue-i18n` |
| **@vueuse/motion** | latest | 动画效果 | `npm i @vueuse/motion` |
| **@vueuse/sound** | latest | 声音效果 | `npm i @vueuse/sound` |
| **vuedraggable** | ^4.1.0 | 拖拽排序 | `npm i vuedraggable` |
| **vue3-print-nb** | latest | 打印功能 | `npm i vue3-print-nb` |
| **file-saver** | ^2.0.5 | 文件下载 | `npm i file-saver` |
| **@types/file-saver** | ^2.0.7 | FileSaver 类型 | `npm i -D @types/file-saver` |

#### 🟢 低优先级（按需安装）

| 库/插件 | 版本 | 用途 | 安装命令 |
|---------|------|------|----------|
| **echarts** | ^5.4.0 | 图表库（替代 Chart.js） | `npm i echarts vue-echarts` |
| **xlsx** | ^0.18.5 | Excel 导入导出 | `npm i xlsx` |
| **qrcode.vue** | ^3.4.0 | 二维码生成 | `npm i qrcode.vue` |
| **vue3-clipboard** | latest | 剪贴板操作 | `npm i vue3-clipboard` |
| **@iconify/vue** | latest | 图标库 | `npm i @iconify/vue` |

### 3.2 安装脚本

```bash
# 进入前端目录
cd /Users/supeng/Documents/botong-ticket-system/frontend

# 高优先级
npm install @vueuse/integrations date-fns lodash-es
npm install -D @types/lodash-es

# 中优先级
npm install vue-i18n @vueuse/motion vuedraggable vue3-print-nb file-saver
npm install -D @types/file-saver

# 低优先级（按需）
npm install echarts vue-echarts xlsx qrcode.vue vue3-clipboard @iconify/vue
```

---

## 四、MCP 配置方案

### 4.1 现有 MCP 优化

#### 需要配置 Token 的 MCP

| MCP | 需要配置 | 获取方式 |
|-----|----------|----------|
| **GitHub** | GITHUB_PERSONAL_ACCESS_TOKEN | GitHub Settings → Developer settings → Personal access tokens |
| **Slack** | SLACK_BOT_TOKEN, SLACK_TEAM_ID | Slack API → Create New App → Bot User OAuth Token |
| **Figma** | FIGMA_API_KEY | Figma → Settings → Personal Access Tokens |

#### 需要启动服务的 MCP

| MCP | 服务 | 启动命令 |
|-----|------|----------|
| **Redis** | Redis Server | `redis-server` |

### 4.2 新增 MCP 推荐

#### 🔴 高优先级（立即配置）

| MCP | 用途 | 安装命令 |
|-----|------|----------|
| **Puppeteer** | 浏览器自动化、截图 | `npx -y @modelcontextprotocol/server-puppeteer` |
| **Brave Search** | 网络搜索 | `npx -y @modelcontextprotocol/server-brave-search` |

#### 🟡 中优先级（1-2 周内配置）

| MCP | 用途 | 安装命令 |
|-----|------|----------|
| **PostgreSQL** | 数据库管理（未来迁移） | `npx -y @modelcontextprotocol/server-postgres` |
| **Google Maps** | 地理位置服务 | `npx -y @modelcontextprotocol/server-google-maps` |
| **AWS** | 云服务管理 | `npx -y @modelcontextprotocol/server-aws` |

### 4.3 MCP 配置更新

```json
{
    "mcpServers": {
        "SQLite": {
            "command": "uvx",
            "args": ["mcp-server-sqlite", "--db-path", "/Users/supeng/Documents/botong-ticket-system/tickets.db"]
        },
        "Filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/supeng/Documents/botong-ticket-system"]
        },
        "Fetch": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-fetch"]
        },
        "Time": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-time"]
        },
        "Puppeteer": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
        },
        "Brave Search": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": {
                "BRAVE_API_KEY": "<your-brave-api-key>"
            }
        },
        "GitHub": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "<your-github-token>"
            }
        },
        "Sequential Thinking": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
        }
    }
}
```

---

## 五、实施计划

### 5.1 第一阶段：基础增强（本周内）

**目标**: 安装高优先级技能、插件和 MCP

| 天数 | 任务 | 预计时间 |
|------|------|----------|
| Day 1 | 安装技能：vercel-react-best-practices, web-design-guidelines, git-commit, dogfood | 30 分钟 |
| Day 1 | 安装前端插件：@vueuse/integrations, date-fns, lodash-es | 15 分钟 |
| Day 2 | 配置 MCP：Puppeteer, Brave Search | 30 分钟 |
| Day 2 | 配置现有 MCP：GitHub Token, Slack Token | 30 分钟 |
| Day 3 | 验证所有安装，运行测试 | 1 小时 |

### 5.2 第二阶段：功能扩展（1-2 周）

**目标**: 安装中优先级技能、插件和 MCP

| 天数 | 任务 | 预计时间 |
|------|------|----------|
| Day 4-5 | 安装技能：webapp-testing, frontend-design, shadcn | 1 小时 |
| Day 6-7 | 安装前端插件：vue-i18n, @vueuse/motion, vuedraggable | 1 小时 |
| Day 8-10 | 配置 MCP：PostgreSQL, Google Maps（按需） | 2 小时 |
| Day 11-14 | 集成测试，编写 E2E 测试 | 4 小时 |

### 5.3 第三阶段：高级优化（按需）

**目标**: 安装低优先级技能、插件和 MCP

| 任务 | 预计时间 |
|------|----------|
| 安装技能：gh-cli, figma, redis-development, screenshot | 1 小时 |
| 安装前端插件：echarts, xlsx, qrcode.vue | 30 分钟 |
| 配置 MCP：AWS（如需部署） | 1 小时 |

---

## 六、预期收益

### 6.1 开发效率提升

| 方面 | 提升 | 说明 |
|------|------|------|
| **代码质量** | +40% | 技能辅助代码审查、安全检测 |
| **开发速度** | +30% | VueUse 工具函数减少重复代码 |
| **测试覆盖** | +50% | Playwright + dogfood 技能 |
| **Bug 发现** | +60% | dogfood + webapp-testing |

### 6.2 系统能力增强

| 方面 | 增强 | 说明 |
|------|------|------|
| **智能化** | 高 | MCP 提供数据库、文件、搜索能力 |
| **国际化** | 中 | vue-i18n 支持多语言 |
| **可视化** | 中 | echarts 增强图表能力 |
| **自动化** | 高 | Puppeteer MCP 支持浏览器自动化 |

---

## 七、风险评估

### 7.1 潜在风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 依赖冲突 | 中 | 逐步安装，每次验证构建 |
| 类型不兼容 | 中 | 使用 @types 包，逐步迁移 |
| MCP 配置错误 | 低 | 备份配置，逐步添加 |
| 性能下降 | 低 | 监控构建时间，按需优化 |

### 7.2 回滚方案

```bash
# 如果出现问题，回滚到之前状态
cd /Users/supeng/Documents/botong-ticket-system/frontend
git checkout package.json package-lock.json
git checkout config/mcp/user_mcp_config.json
npm install
```

---

## 八、验收标准

### 8.1 技能验收

- [ ] 所有高优先级技能已安装并可用
- [ ] 技能在相关任务中自动触发
- [ ] 技能输出符合预期

### 8.2 插件验收

- [ ] 所有插件安装成功，无冲突
- [ ] 前端构建通过（`npm run build:fast`）
- [ ] 类型检查通过（`npm run typecheck`）
- [ ] 测试通过（`npm run test`）

### 8.3 MCP 验收

- [ ] 所有 MCP 配置正确
- [ ] MCP 工具可正常调用
- [ ] 数据库 MCP 可查询数据
- [ ] 文件系统 MCP 可读写文件

---

## 九、总结

本方案计划通过三个阶段的实施，全面提升博通工单系统的开发效率、代码质量和智能化水平：

1. **第一阶段**（本周内）：安装高优先级技能、插件和 MCP，快速获得基础能力提升
2. **第二阶段**（1-2 周）：安装中优先级组件，扩展系统功能
3. **第三阶段**（按需）：安装高级组件，满足特定需求

预期收益：
- 开发效率提升 30-40%
- 代码质量显著提升
- Bug 发现率提升 60%
- 系统智能化水平大幅提升

---

**方案制定**: 2026-05-29
**执行状态**: 待开始
**下次评审**: 第一阶段完成后
