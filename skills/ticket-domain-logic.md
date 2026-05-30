title: ticket-domain-logic
priority: high
tags: [ticket, domain, business]

maintainer: TBD
version: 0.1.0
read_only_db: false

## 简介
工单核心业务规则与约束：创建、更新、状态流转、完工结算、收款边界条件及领域事件。

## 使用场景
- 分析/修改 `application/services/ticket_service.py` 的业务逻辑
- 编写或审计与工单相关的集成/端到端测试

## 关注点
- 状态流转合法性（`STATUS_FLOW`）
- 完工/收款的幂等与并发保护
- 事件（TicketCreated/Completed/StatusChanged）何时触发

## 入口文件/函数
- `application/services/ticket_service.py::TicketService`
- `api/v1/tickets.py`（API 层校验与幂等）

## 验证用例
- 创建工单、立即完工并收款（并发场景）
- 状态非法流转应抛出 `TicketValidationError`

## 维护人
- TBD
