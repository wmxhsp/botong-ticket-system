---
title: flask-testing-patterns
priority: medium
tags: [flask, testing, pytest]
---

## 简介
Flask 测试模式：单元测试、集成测试、API 测试、Fixture 组织与覆盖率策略。

## 使用场景
- 编写或维护 `tests/` 下的测试用例
- 新增 API 端点后补充对应测试
- CI 流水线中的测试配置

## 关注点
- 使用 `pytest` + `fixtures` 组织测试（`tests/conftest.py`）
- Flask 测试客户端 `app.test_client()` 进行 API 集成测试
- 每个测试独立数据库事务，测试结束后回滚（避免测试间污染）
- Mock 外部依赖（Redis、RQ 队列），隔离测试
- Service 层测试通过 Repository 接口 mock 数据库
- 测试覆盖率目标：核心业务逻辑 ≥ 80%

## 入口文件/函数
- `tests/conftest.py`（测试 Fixture）
- `tests/test_ticket_api.py`（API 测试参考）
- `tests/test_new_architecture.py`（架构测试参考）

## 验证用例
- `pytest tests/` 应通过所有测试
- 新增 API 应有对应的测试文件
- 测试不应依赖外部服务（Redis/网络）

## 维护人
- TBD
