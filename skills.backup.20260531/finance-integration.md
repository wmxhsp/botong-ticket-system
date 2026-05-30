title: finance-integration
priority: high
tags: [finance, accounting, expense]

maintainer: TBD
version: 0.1.0
read_only_db: false

## 简介
与财务系统的集成点：费用记录、收入确认、重复收款检测与对账。

## 使用场景
- `TicketService.complete_ticket` 和 `process_payment` 的财务交互
- 审计 `application/services/finance_service.py` 或相应仓储

## 关注点
- 收入/支出的幂等性与重复检测
- 账单关联字段（related_ticket_id）的一致性
- 自动记账失败时的补偿策略

## 入口文件/函数
- `application/services/ticket_service.py::complete_ticket`
- `application/services/finance_service.py`（若存在）

## 验证用例
- 完工后自动记录物料成本与交通费（幂等性检查）

## 维护人
- TBD
