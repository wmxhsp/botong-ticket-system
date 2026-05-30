// 核心基础设施模块
import dashboardModule from './dashboard'

// 业务模块
import ticketModule from './ticket'
import clientModule from './client'
import financeModule from './finance'
import inventoryModule from './inventory'
import equipmentModule from './equipment'
import purchaseModule from './purchase'
import expenseModule from './expense'
import staffModule from './staff'
import supplierModule from './supplier'
import warehouseModule from './warehouse'
import serviceFeeModule from './serviceFee'
import todoModule from './todo'
import settingModule from './setting'
import statsModule from './stats'
import notificationModule from './notification'

/**
 * 所有功能模块
 * 顺序决定导航菜单排列顺序
 */
export const modules = [
  dashboardModule,
  ticketModule,
  clientModule,
  equipmentModule,
  financeModule,
  inventoryModule,
  purchaseModule,
  expenseModule,
  staffModule,
  supplierModule,
  warehouseModule,
  serviceFeeModule,
  todoModule,
  statsModule,
  notificationModule,
  settingModule,
]

/**
 * 聚合所有模块的路由
 * 用于 router/index.js 动态注册
 */
export const moduleRoutes = modules.flatMap(m => m.routes || [])

/**
 * 聚合所有模块的导航菜单
 * 用于 AppSidebar 动态生成
 */
export const moduleNavItems = modules
  .filter(m => m.nav)
  .sort((a, b) => (a.nav.order || 99) - (b.nav.order || 99))
  .map(m => m.nav)

/**
 * 功能地图：所有模块声明的功能清单
 * 用于 FeatureMap 页面展示前后端功能对齐情况
 */
export const moduleFeatures = modules.flatMap(m =>
  (m.features || []).map(f => ({
    module: m.name,
    moduleTitle: m.nav?.title || m.name,
    ...f,
  }))
)

/**
 * 按模块分组的功能地图
 */
export const moduleFeaturesByModule = modules.reduce((acc, m) => {
  if (m.features && m.features.length > 0) {
    acc[m.name] = {
      title: m.nav?.title || m.name,
      features: m.features,
    }
  }
  return acc
}, {})

/**
 * 获取指定模块
 */
export function getModule(name) {
  return modules.find(m => m.name === name)
}

/**
 * 获取指定模块的 API
 */
export function getModuleApi(name) {
  const m = getModule(name)
  return m?.api || {}
}
