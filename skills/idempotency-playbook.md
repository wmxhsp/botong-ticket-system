---
title: idempotency-playbook
priority: high
tags: [idempotency, concurrency, ticket]
maintainer: TBD
version: 0.1.0
read_only_db: false
---

## 简介
幂等性实务手册：工单场景下常见幂等问题、实现模式、冲突解决与测试示例（配合现有 `idempotency-and-concurrency` 文档）。

## 适用场景
- 处理重复请求或客户端重试导致的重复创建/收款问题
- 设计幂等键、TTL 与清理策略

## 内容要点
- 幂等键设计建议（范围、TTL、唯一性）
- 读写冲突与乐观锁策略
- 常见错误示例与防御模式

## 验证用例
- 使用相同 `X-Idempotency-Key` 多次创建工单只会成功一次
- 清理过期幂等记录后新的相同键可再次生效

## 维护人
TBD
