title: api-module-best-practices
priority: high
tags: [api, frontend, http]

maintainer: TBD
version: 0.1.0
read_only_db: false

## 简介
前端 API 模块规范：请求封装、错误处理、类型安全、模块组织与 useApi 组合式函数。

## 使用场景
- 新增前端 API 调用模块（`frontend/src/api/`）
- 统一 HTTP 请求与响应处理
- API 错误统一提示与重试

## 关注点
- 使用 `frontend/src/composables/useApi.js` 封装请求逻辑
- API 模块按业务域拆分（tickets.js、clients.js 等）
- 统一错误处理：网络错误、401 跳转登录、业务错误 toast 提示
- 请求/响应拦截器处理认证 Token 注入
- 避免在组件中直接调用 axios，统一通过 API 模块

## 入口文件/函数
- `frontend/src/api/tickets.js`（工单 API 模块参考）
- `frontend/src/composables/useApi.js`（API 调用封装）

## 验证用例
- 新增 API 应在 `frontend/src/api/` 下创建独立模块
- 组件中通过 `useApi` 或 API 模块调用，不直接使用 axios
- 401 响应应自动跳转登录页

## 维护人
- TBD
