title: idempotency-and-concurrency
priority: high
tags: [idempotent, concurrency, safety]

maintainer: TBD
version: 0.1.0
read_only_db: false

## 简介
处理 API 幂等键、并发冲突、重试与锁策略，避免重复创建/重复扣减/重复记账。

## 使用场景
- 审计 `api/v1/tickets.py` 中的幂等逻辑
- 在 `application/services/ticket_service.py` 增加并发保护测试

## 关注点
- 幂等键的持久层实现与失效策略
- 完工/收款/库存操作的并发竞态
- 使用乐观锁（版本字段）或数据库行级锁

## 入口文件/函数
- `application/services/ticket_service.py::check_idempotent` / `set_idempotent`
- 仓储层 `infrastructure/persistence/repositories/*`

## 验证用例
- 并发两次创建同一幂等键，应只创建一次
- 并发完工与收款不应出现重复支出/重复扣减

## 维护人
- TBD
