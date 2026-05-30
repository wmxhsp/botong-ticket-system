---
title: task-orchestration
priority: medium
tags: [agent, orchestration, workflow]
---

## 简介
复杂多步骤任务的编排策略：任务拆分、依赖管理、并行执行、错误恢复与进度追踪。

## 使用场景
- 完工流程涉及多个步骤（更新工单 + 扣减库存 + 记录财务 + 发送通知）
- 数据迁移或批量导入
- 需要跨模块协调的复杂操作

## 关注点
- 大任务拆分为原子步骤，每步有明确的输入/输出
- 步骤间依赖通过数据流传递（上一步输出 = 下一步输入）
- 错误策略：整体回滚 vs 部分重试 vs 标记失败继续
- 进度追踪：记录当前步骤与完成比例
- 并行步骤使用 Promise.all / 队列并发执行
- 幂等设计：每步可安全重试，不产生副作用

## 入口文件/函数
- `application/services/ticket_service.py::complete_ticket`（完工编排）
- `application/services/inventory_service.py`（库存联动）
- `infrastructure/messaging/event_subscribers.py`（事件驱动编排）

## 验证用例
- 完工流程中断后重试，应从中断步骤继续而非从头开始
- 并行步骤无数据竞争
- 部分步骤失败应有明确错误信息与恢复指引

## 维护人
- TBD
