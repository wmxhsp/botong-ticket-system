---
title: vue-frontend-optimization
priority: medium
tags: [vue, performance, optimization]
---

## 简介
Vue 前端性能优化：组件懒加载、虚拟滚动、缓存策略、Bundle 分析与代码分割。

## 使用场景
- 页面加载速度优化
- 大列表/大表格渲染性能优化
- 构建产物体积分析与优化
- 首屏加载时间优化

## 关注点
- 路由级组件懒加载（`() => import()`）
- 大列表使用虚拟滚动或分页加载
- 图片懒加载 + 合理尺寸（thumbnail / full）
- Chart.js 按需导入，避免全量引入
- `v-if` vs `v-show` 选择：频繁切换用 `v-show`，条件渲染用 `v-if`
- `computed` 缓存计算结果，避免模板中复杂表达式
- 使用 `key` 优化 `v-for` 列表渲染
- Vite 构建分析：`rollupOptions.output.manualChunks` 拆分第三方库

## 入口文件/函数
- `frontend/vite.config.js`（构建配置）
- `frontend/src/router/index.js`（路由懒加载）

## 验证用例
- Lighthouse 性能评分 ≥ 80
- 首屏加载 < 2s（本地网络）
- 单 chunk 不超过 500KB

## 维护人
- TBD
