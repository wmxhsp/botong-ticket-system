---
title: mcp-deployment-security
priority: high
tags: [mcp, security, deployment]
maintainer: TBD
version: 0.1.0
read_only_db: true
---

## 简介
MCP 部署与注册安全指南：包含 API Key 管理、最小权限、技能入口校验、审计与只读数据库挂载策略。

## 适用场景
- 在本地或 CI 环境向 MCP 注册技能前的安全审计
- 指导如何以只读方式将 `tickets.db` 挂载给第三方代理

## 内容要点
- MCP API Key 管理与轮换策略
- 技能入口（`entrypoint`）校验和约束
- 数据库只读挂载示例（Docker Compose）
- 注册/更新操作的审计记录规范

## 验证用例
- 使用只读挂载注册技能后尝试写入 DB 应被拒绝
- 注册时 `entrypoint` 不应包含凭证或绝对敏感路径

## 入口文件/命令
- scripts/register_mcp_skills.py

## 维护人
TBD
