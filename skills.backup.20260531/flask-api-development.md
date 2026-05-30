---
title: flask-api-development
priority: high
tags: [flask, api, backend, ddd, security]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
last_updated: 2026-05-31
related_skills: [flask-testing-patterns, ticket-domain-logic, task-orchestration]
---

## 简介
Flask REST API 完整开发指南：涵盖 DDD 分层架构、路由定义、请求校验、响应格式、错误处理、安全加固与蓝图组织。

## 使用场景
- 新增或修改 API 端点（`api/v1/` 目录）
- 统一响应格式与错误码设计
- API 版本控制与蓝图注册

## 关注点
- 使用 `api/v1/responses.py` 中的统一响应工具（success_response / error_response）
- 请求参数校验使用 `api/validators/schemas.py`
- 路由蓝图在 `web/app_factory.py` 中注册
- 错误处理遵循 HTTP 语义，业务错误使用 4xx，服务端错误使用 5xx

## 入口文件/函数
- `api/v1/tickets.py`（工单 API 参考）
- `api/v1/responses.py`（响应工具）
- `api/validators/schemas.py`（校验模式）
- `web/app_factory.py`（蓝图注册）

## 验证用例
- 新增 API 应返回统一 JSON 格式 `{code, data, message}`
- 缺少必填字段应返回 400 + 明确错误信息
- 未认证请求应返回 401

## 维护人
- TBD
