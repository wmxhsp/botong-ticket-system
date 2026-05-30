# 知识库查询辅助功能部署计划

> 创建日期: 2026-05-29
> 状态: 待部署
> 优先级: 中

---

## 一、需求背景

当 Brave Search API 免费额度用尽后，需要部署一个**免费的国内替代方案**来实现知识库查询辅助功能。

**核心需求**:
- 免费使用，无额度限制
- 支持中文搜索
- 可查询技术文档、故障解决方案
- 可集成到 MCP 系统

---

## 二、推荐方案: SearXNG

### 2.1 方案概述

SearXNG 是一个开源的元搜索引擎，聚合 70+ 搜索引擎结果，支持本地部署。

**优势**:
- ✅ 完全免费，无使用限制
- ✅ 聚合多引擎（百度、必应、Google 等）
- ✅ 支持 JSON API 输出
- ✅ 隐私保护，不追踪用户
- ✅ 可通过 Docker 快速部署

### 2.2 部署步骤

#### 前提条件
- Docker 已安装
- 端口 8080 可用

#### 部署命令

```bash
# 1. 创建配置目录
mkdir -p /Users/supeng/searxng

# 2. 部署 SearXNG 容器
docker run -d \
  --name searxng \
  --restart unless-stopped \
  -p 8080:8080 \
  -v /Users/supeng/searxng:/etc/searxng \
  searxng/searxng

# 3. 验证部署
curl http://localhost:8080

# 4. 测试搜索 API
curl "http://localhost:8080/search?q=工单系统故障排查&format=json"
```

#### 配置优化

编辑 `/Users/supeng/searxng/settings.yml`:

```yaml
# 启用中文搜索引擎
engines:
  - name: baidu
    engine: baidu
    shortcut: bd
    enabled: true

  - name: bing
    engine: bing
    shortcut: bi
    enabled: true

  - name: google
    engine: google
    shortcut: go
    enabled: true

# 设置默认语言
search:
  language: zh-CN
  locale: zh
```

### 2.3 MCP 集成

#### 配置更新

在 `config/mcp/user_mcp_config.json` 中添加:

```json
{
  "mcpServers": {
    "SearXNG": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {
        "SEARXNG_URL": "http://localhost:8080"
      }
    }
  }
}
```

#### 使用示例

```javascript
// 查询知识库
const searchResults = await fetch(
  'http://localhost:8080/search?q=打印机故障代码&format=json'
);

// 解析结果
const data = await searchResults.json();
const solutions = data.results.map(r => ({
  title: r.title,
  url: r.url,
  content: r.content
}));
```

---

## 三、应用场景

### 3.1 工单系统知识库查询

| 场景 | 查询示例 | 预期结果 |
|------|----------|----------|
| 设备故障排查 | "HP LaserJet 错误代码 49" | 故障原因和解决方案 |
| 配件价格参考 | "佳能墨盒 PG-845 价格" | 市场价格范围 |
| 技术文档查询 | "Windows 11 打印机共享设置" | 官方文档链接 |
| 常见问题解答 | "打印机卡纸怎么处理" | 解决步骤 |

### 3.2 集成到工单处理流程

```
用户提交工单
    ↓
系统自动识别关键词（设备型号、错误代码）
    ↓
SearXNG 查询相关知识库
    ↓
返回可能的解决方案
    ↓
技术员参考解决方案处理工单
    ↓
记录解决方案到知识库
```

---

## 四、备选方案

### 4.1 方案对比

| 方案 | 费用 | 部署难度 | 稳定性 | 适用场景 |
|------|------|----------|--------|----------|
| **SearXNG** | 免费 | 低 | 中 | 个人/小团队 |
| 百度搜索 API | 按量 | 中 | 高 | 企业级应用 |
| 必应 API | 按量 | 低 | 高 | 企业级应用 |
| Elasticsearch | 免费 | 高 | 高 | 自建知识库 |

### 4.2 长期方案: 自建知识库

**技术栈**:
- Elasticsearch: 搜索引擎
- Kibana: 可视化界面
- Logstash: 数据导入

**优势**:
- 完全自主可控
- 可索引内部文档
- 搜索精度高

**部署成本**:
- 服务器资源
- 维护成本

---

## 五、实施计划

### 5.1 短期（本周）

- [ ] 部署 SearXNG
- [ ] 配置 MCP 集成
- [ ] 测试搜索功能
- [ ] 验证中文搜索效果

### 5.2 中期（1-2 周）

- [ ] 优化搜索引擎配置
- [ ] 集成到工单处理流程
- [ ] 添加常用查询模板
- [ ] 记录查询日志

### 5.3 长期（按需）

- [ ] 评估自建知识库需求
- [ ] 迁移到 Elasticsearch
- [ ] 建立内部知识库索引

---

## 六、注意事项

### 6.1 法律合规

- 遵守搜索引擎使用条款
- 不用于商业爬虫
- 尊重版权和隐私

### 6.2 性能优化

- 设置合理的请求频率
- 启用缓存机制
- 监控服务状态

### 6.3 安全考虑

- 限制访问 IP
- 启用 HTTPS（生产环境）
- 定期更新容器

---

## 七、相关文件

- [MCP 配置文件](../config/mcp/user_mcp_config.json)
- [部署脚本](../scripts/deploy_searxng.sh) (待创建)
- [使用文档](../docs/SEARXNG_USAGE.md) (待创建)

---

**记录人**: AI Assistant
**记录日期**: 2026-05-29
**状态**: 待部署
