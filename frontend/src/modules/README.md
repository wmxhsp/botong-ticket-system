# 前端功能模块规范

## 目录结构

每个模块是一个独立目录，包含：

```
modules/{module-name}/
├── index.js          # 模块入口：导出 name, routes, nav, features, api
├── api.js            # 模块专属 API 封装（从 api/xxx.js 迁移）
├── routes.js         # 模块路由定义
├── views/            # 模块页面
│   ├── List.vue
│   ├── Detail.vue
│   └── ...
├── components/       # 模块私有组件
│   └── ...
└── composables/      # 模块私有组合式函数（可选）
    └── ...
```

## 模块入口规范

```javascript
// modules/{name}/index.js
import routes from './routes'
import * as api from './api'

export default {
  // 模块标识
  name: 'moduleName',

  // 导航菜单配置（可选）
  nav: {
    title: '菜单标题',
    icon: 'bi-icon-name',
    path: '/path',
    order: 10,              // 排序权重，越小越靠前
    children: [             // 子菜单（可选）
      { title: '子菜单1', path: '/path/sub1' },
    ],
  },

  // 路由配置
  routes,

  // API 导出
  api,

  // 功能清单：与后端端点对应，用于功能地图
  features: [
    {
      id: 'module.action',           // 唯一标识
      name: '功能名称',               // 显示名称
      endpoint: 'GET /api/v1/...',   // 后端端点
      view: 'ViewName.vue',          // 前端视图文件
      status: 'done',                // done / todo / partial
      description: '功能描述',
    },
  ],
}
```

## 路由规范

```javascript
// modules/{name}/routes.js
export default [
  {
    path: 'entities',               // 相对路径（无前导/）
    name: 'EntityList',
    component: () => import('./views/List.vue'),
    meta: { title: '列表', icon: 'bi-list' },
  },
  {
    path: 'entities/:id',
    name: 'EntityDetail',
    component: () => import('./views/Detail.vue'),
    meta: { title: '详情', hideInMenu: true },
  },
]
```

## API 规范

```javascript
// modules/{name}/api.js
import client from '@/api/client'

const BASE = '/api/v1/entities'

export function list(params = {}) {
  return client.get(BASE, { params })
}

export function getById(id) {
  return client.get(`${BASE}/${id}`)
}

// ...
```

## 迁移原则

1. **复制而非移动**：先复制文件到新位置，保留原文件，验证通过后再删除
2. **路径别名**：新模块内使用 `@/` 别名引用核心资源
3. **API 迁移**：将 `api/xxx.js` 内容复制到 `modules/xxx/api.js`，调整 import 路径
4. **视图迁移**：将 `views/Xxx.vue` 复制到 `modules/xxx/views/`，调整 import 路径
5. **逐步验证**：每迁移一个模块，验证路由和页面正常

## 模块列表

| 模块 | 状态 | 说明 |
|------|------|------|
| dashboard | 待迁移 | 仪表盘 |
| ticket | 待迁移 | 工单管理 |
| client | 待迁移 | 客户管理 |
| finance | 待迁移 | 财务管理 |
| inventory | 待迁移 | 库存管理 |
| equipment | 待迁移 | 设备管理 |
| purchase | 待迁移 | 采购管理 |
| expense | 待迁移 | 支出管理 |
| staff | 待迁移 | 员工管理 |
| supplier | 待迁移 | 供应商 |
| warehouse | 待迁移 | 仓库管理 |
| serviceFee | 待迁移 | 服务费率 |
| todo | 待迁移 | 待办事项 |
| setting | 待迁移 | 系统设置 |
| stats | 待迁移 | 统计分析 |
| notification | 待迁移 | 通知中心 |
