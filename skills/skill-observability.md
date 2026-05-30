---
title: skill-observability
priority: high
tags: [observability, monitoring, mcp]
maintainer: TBD
version: 0.1.0
read_only_db: false
---

## 简介
技能可观测性指南：调用埋点、日志结构、超时与错误率监控、与后端日志关联（trace id）。

## 适用场景
- 跟踪技能调用性能与失败率
- 故障排查（链路追踪）

## 内容要点
- 在技能调用入口记录标准化日志（包含 trace_id、skill_name、duration、status）
- 设置合理的超时与重试策略，避免放大风暴
- 将技能错误上报到统一监控/告警系统

## 验证用例
- 当技能响应超时时生成告警并记录 trace id
- 能够从后端日志关联到触发技能的请求

## 入口文件/函数
- skills 的运行时启动脚本（自定义）

## 维护人
TBD
