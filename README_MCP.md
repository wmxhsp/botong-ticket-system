# 本地部署 CodeGeeX MCP Server（示例）

说明：此文件提供一个可运行的 docker compose 示例，用于把 CodeGeeX MCP Server 与本仓库的 `tickets.db`（SQLite）挂载在一起以便技能访问项目数据。

重要：示例使用占位镜像 `codegeex/mcp-server:latest`，请替换为你实际的 MCP 镜像或启动命令，且确认 MCP 支持外部 SQLite 路径配置。

启动：
```bash
# 在仓库根目录运行（需要 Docker）
export MCP_API_KEY=YOUR_REAL_KEY
docker compose -f docker-compose.mcp.yml up -d
docker compose -f docker-compose.mcp.yml logs -f codegeex-mcp
```

验证：
```bash
curl -v http://localhost:8080/health
curl -H "Authorization: Bearer ${MCP_API_KEY}" http://localhost:8080/api/v1/skills
```

安全与注意事项：
- 挂载项目 `tickets.db` 到 MCP 容器会让 MCP 进程读取该数据库，请确保容器镜像受信任并且以只读模式挂载（compose 示例中为只读）。
- 推荐将 MCP 的数据存储与业务数据库分离；此示例仅用于开发/调试。生产建议使用独立数据库并通过 API 授权访问业务数据。

自定义：
- 若 MCP 镜像使用不同的 env 名称或需要额外配置，请编辑 `docker-compose.mcp.yml`。
