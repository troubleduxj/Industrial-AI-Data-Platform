/**
 * 优化后的权限配置
 * 统一的API权限映射，解决当前权限配置混乱的问题
 */

// 统一的权限配置映射
export const PERMISSION_CONFIG = {
  // 系统管理模块
  users: {
    read: 'GET /api/v2/users',
    create: 'POST /api/v2/users',
    update: 'PUT /api/v2/users/{id}',
    delete: 'DELETE /api/v2/users/{id}',
    'reset-password': 'POST /api/v2/users/{id}/actions/reset-password',
  },

  roles: {
    read: 'GET /api/v2/roles',
    create: 'POST /api/v2/roles',
    update: 'PUT /api/v2/roles/{id}',
    delete: 'DELETE /api/v2/roles/{id}',
    'assign-permissions': 'PUT /api/v2/roles/{id}/permissions',
  },

  menus: {
    read: 'GET /api/v2/menus',
    create: 'POST /api/v2/menus',
    update: 'PUT /api/v2/menus/{id}',
    delete: 'DELETE /api/v2/menus/{id}',
  },

  departments: {
    read: 'GET /api/v2/departments',
    create: 'POST /api/v2/departments',
    update: 'PUT /api/v2/departments/{id}',
    delete: 'DELETE /api/v2/departments/{id}',
  },

  apis: {
    read: 'GET /api/v2/apis',
    create: 'POST /api/v2/apis',
    update: 'PUT /api/v2/apis/{id}',
    delete: 'DELETE /api/v2/apis/{id}',
    refresh: 'POST /api/v2/apis/refresh',
  },

  // 设备管理模块
  devices: {
    read: 'GET /api/v2/devices',
    create: 'POST /api/v2/devices',
    update: 'PUT /api/v2/devices/{id}',
    delete: 'DELETE /api/v2/devices/{id}',
    monitor: 'GET /api/v2/devices/{id}/data',
  },

  'device-types': {
    read: 'GET /api/v2/devices/types',
    create: 'POST /api/v2/devices/types',
    update: 'PUT /api/v2/devices/types/{id}',
    delete: 'DELETE /api/v2/devices/types/{id}',
  },

  'device-maintenance': {
    read: 'GET /api/v2/devices/{id}/maintenance',
    create: 'POST /api/v2/devices/{id}/maintenance',
    update: 'PUT /api/v2/devices/maintenance/{id}',
    delete: 'DELETE /api/v2/devices/maintenance/{id}',
  },

  'device-processes': {
    read: 'GET /api/v2/devices/{id}/processes',
    create: 'POST /api/v2/devices/{id}/processes',
    update: 'PUT /api/v2/devices/processes/{id}',
    delete: 'DELETE /api/v2/devices/processes/{id}',
  },

  // 报警管理模块
  alarms: {
    read: 'GET /api/v2/alarms',
    handle: 'PUT /api/v2/alarms/{id}/handle',
    'batch-handle': 'PUT /api/v2/alarms/batch-handle',
  },

  // AI监控模块
  'ai-predictions': {
    read: 'GET /api/v2/ai/predictions',
    create: 'POST /api/v2/ai/predictions',
    export: 'GET /api/v2/ai/predictions/{id}/export',
  },

  'ai-models': {
    read: 'GET /api/v2/ai/models',
    upload: 'POST /api/v2/ai/models',
    update: 'PUT /api/v2/ai/models/{id}',
    delete: 'DELETE /api/v2/ai/models/{id}',
  },

  'ai-annotations': {
    read: 'GET /api/v2/ai/annotations',
    create: 'POST /api/v2/ai/annotations',
    update: 'PUT /api/v2/ai/annotations/{id}',
    import: 'POST /api/v2/ai/annotations/{id}/import',
  },

  'ai-health': {
    read: 'GET /api/v2/ai/health-scores',
    calculate: 'POST /api/v2/ai/health-scores',
    export: 'GET /api/v2/ai/health-scores/export',
    config: 'PUT /api/v2/ai/health-scores/config',
  },

  'ai-analysis': {
    read: 'GET /api/v2/ai/analysis',
    create: 'POST /api/v2/ai/analysis',
  },

  // 统计分析模块
  statistics: {
    'online-rate': 'GET /api/v2/statistics/online-rate',
    'weld-records': 'GET /api/v2/statistics/weld-records',
    'weld-time': 'GET /api/v2/statistics/weld-time',
    'welding-reports': 'GET /api/v2/statistics/welding-reports',
  },

  // 仪表板模块
  dashboard: {
    overview: 'GET /api/v2/dashboard/overview',
    'device-stats': 'GET /api/v2/dashboard/device-stats',
    'alarm-stats': 'GET /api/v2/dashboard/alarm-stats',
  },
}

// 旧权限到新权限的映射表 (用于兼容性)
export const LEGACY_PERMISSION_MAP = {
  // 用户管理
  'get/api/v1/user/list': 'GET /api/v2/users',
  'get/api/v1/user/get': 'GET /api/v2/users/{id}',
  'post/api/v1/user/create': 'POST /api/v2/users',
  'post/api/v1/user/update': 'PUT /api/v2/users/{id}',
  'delete/api/v1/user/delete': 'DELETE /api/v2/users/{id}',
  'post/api/v1/user/reset_password': 'POST /api/v2/users/{id}/actions/reset-password',

  // 角色管理
  'get/api/v1/role/list': 'GET /api/v2/roles',
  'get/api/v1/role/get': 'GET /api/v2/roles/{id}',
  'post/api/v1/role/create': 'POST /api/v2/roles',
  'post/api/v1/role/update': 'PUT /api/v2/roles/{id}',
  'delete/api/v1/role/delete': 'DELETE /api/v2/roles/{id}',
  'get/api/v1/role/authorized': 'GET /api/v2/roles/{id}/permissions',
  'post/api/v1/role/authorized': 'PUT /api/v2/roles/{id}/permissions',

  // 菜单管理
  'get/api/v1/menu/list': 'GET /api/v2/menus',
  'post/api/v1/menu/create': 'POST /api/v2/menus',
  'post/api/v1/menu/update': 'PUT /api/v2/menus/{id}',
  'delete/api/v1/menu/delete': 'DELETE /api/v2/menus/{id}',

  // 部门管理
  'get/api/v1/dept/list': 'GET /api/v2/departments',
  'post/api/v1/dept/create': 'POST /api/v2/departments',
  'post/api/v1/dept/update': 'PUT /api/v2/departments/{id}',
  'delete/api/v1/dept/delete': 'DELETE /api/v2/departments/{id}',

  // API管理
  'get/api/v1/api/list': 'GET /api/v2/apis',
  'post/api/v1/api/create': 'POST /api/v2/apis',
  'post/api/v1/api/update': 'PUT /api/v2/apis/{id}',
  'delete/api/v1/api/delete': 'DELETE /api/v2/apis/{id}',
  'post/api/v1/api/refresh': 'POST /api/v2/apis/refresh',

  // 设备管理
  'get/api/v1/device/list': 'GET /api/v2/devices',
  'post/api/v1/device/create': 'POST /api/v2/devices',
  'put/api/v1/device/update': 'PUT /api/v2/devices/{id}',
  'delete/api/v1/device/delete': 'DELETE /api/v2/devices/{id}',
  'get/api/v1/device/data': 'GET /api/v2/devices/{id}/data',

  // 设备类型
  'get/api/v1/device/types': 'GET /api/v2/devices/types',
  'post/api/v1/device/types': 'POST /api/v2/devices/types',
  'put/api/v1/device/types': 'PUT /api/v2/devices/types/{id}',
  'delete/api/v1/device/types': 'DELETE /api/v2/devices/types/{id}',

  // 报警管理
  'get/api/v1/alarm/list': 'GET /api/v2/alarms',
}

/**
 * 获取资源的权限配置
 * @param {string} resource - 资源名称 (如: 'users', 'devices')
 * @param {string} action - 操作类型 (如: 'read', 'create', 'update', 'delete')
 * @returns {string|null} 权限标识
 */
export function getPermission(resource, action) {
  return PERMISSION_CONFIG[resource]?.[action] || null
}

/**
 * 检查是否为有效的权限配置
 * @param {string} resource - 资源名称
 * @param {string} action - 操作类型
 * @returns {boolean} 是否有效
 */
export function isValidPermission(resource, action) {
  return !!getPermission(resource, action)
}

/**
 * 获取所有权限列表
 * @returns {string[]} 权限标识列表
 */
export function getAllPermissions() {
  const permissions = []
  Object.values(PERMISSION_CONFIG).forEach((resourceConfig) => {
    Object.values(resourceConfig).forEach((permission) => {
      if (permission && !permissions.includes(permission)) {
        permissions.push(permission)
      }
    })
  })
  return permissions
}

/**
 * 根据资源获取所有操作权限
 * @param {string} resource - 资源名称
 * @returns {Object} 操作权限映射
 */
export function getResourcePermissions(resource) {
  return PERMISSION_CONFIG[resource] || {}
}

/**
 * 迁移旧权限标识到新权限标识
 * @param {string} oldPermission - 旧的权限标识
 * @returns {string} 新的权限标识
 */
export function migratePermission(oldPermission) {
  return LEGACY_PERMISSION_MAP[oldPermission] || oldPermission
}

/**
 * 批量迁移权限标识
 * @param {string[]} oldPermissions - 旧的权限标识数组
 * @returns {string[]} 新的权限标识数组
 */
export function migratePermissions(oldPermissions) {
  return oldPermissions.map((permission) => migratePermission(permission))
}

/**
 * 检查权限是否需要迁移
 * @param {string} permission - 权限标识
 * @returns {boolean} 是否需要迁移
 */
export function needsMigration(permission) {
  return !!LEGACY_PERMISSION_MAP[permission]
}

// 页面路径到权限资源的映射
export const PAGE_PERMISSION_MAP = {
  '/system/user': 'users',
  '/system/role': 'roles',
  '/system/menu': 'menus',
  '/system/dept': 'departments',
  '/system/api': 'apis',
  '/device/baseinfo': 'devices',
  '/device/type': 'device-types',
  '/device-maintenance/repair-records': 'device-maintenance',
  '/process/process-card': 'device-processes',
  '/device-monitor': 'devices',
  '/alarm/alarm-info': 'alarms',
  '/ai-monitor/trend-prediction': 'ai-predictions',
  '/ai-monitor/model-management': 'ai-models',
  '/ai-monitor/data-annotation': 'ai-annotations',
  '/ai-monitor/health-scoring': 'ai-health',
  '/ai-monitor/smart-analysis': 'ai-analysis',
  '/statistics/online-rate': 'statistics',
  '/statistics/weld-record': 'statistics',
  '/statistics/weld-time': 'statistics',
  '/statistics/welding-report': 'statistics',
  '/dashboard': 'dashboard',
}

/**
 * 根据页面路径获取对应的权限资源
 * @param {string} pagePath - 页面路径
 * @returns {string|null} 权限资源名称
 */
export function getResourceByPage(pagePath) {
  return PAGE_PERMISSION_MAP[pagePath] || null
}

/**
 * 根据页面路径和操作获取权限标识
 * @param {string} pagePath - 页面路径
 * @param {string} action - 操作类型
 * @returns {string|null} 权限标识
 */
export function getPermissionByPage(pagePath, action) {
  const resource = getResourceByPage(pagePath)
  return resource ? getPermission(resource, action) : null
}

export default PERMISSION_CONFIG
