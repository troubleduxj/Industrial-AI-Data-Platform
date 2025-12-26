/**
 * API权限重构项目 - 权限配置核心工具 v2
 * 统一的权限配置管理，支持API v2规范
 *
 * 功能特性：
 * 1. 统一的权限标识格式：HTTP方法 /api/v2/资源路径
 * 2. 页面路径到权限资源的自动映射
 * 3. 新旧权限格式的兼容性支持
 * 4. 权限验证和批量操作
 * 5. 开发工具支持
 */

// API v2权限配置映射 - 遵循RESTful规范
export const PERMISSION_CONFIG_V2 = {
  // 系统管理模块
  users: {
    read: 'GET /api/v2/users',
    create: 'POST /api/v2/users',
    update: 'PUT /api/v2/users/{id}',
    delete: 'DELETE /api/v2/users/{id}',
    'reset-password': 'POST /api/v2/users/{id}/actions/reset-password',
    permissions: 'GET /api/v2/users/{id}/permissions',
    batch: 'POST /api/v2/users/batch',
  },

  roles: {
    read: 'GET /api/v2/roles',
    create: 'POST /api/v2/roles',
    update: 'PUT /api/v2/roles/{id}',
    delete: 'DELETE /api/v2/roles/{id}',
    permissions: 'GET /api/v2/roles/{id}/permissions',
    'assign-permissions': 'PUT /api/v2/roles/{id}/permissions',
    users: 'GET /api/v2/roles/{id}/users',
  },

  menus: {
    read: 'GET /api/v2/menus',
    create: 'POST /api/v2/menus',
    update: 'PUT /api/v2/menus/{id}',
    delete: 'DELETE /api/v2/menus/{id}',
    tree: 'GET /api/v2/menus/tree',
  },

  departments: {
    read: 'GET /api/v2/departments',
    create: 'POST /api/v2/departments',
    update: 'PUT /api/v2/departments/{id}',
    delete: 'DELETE /api/v2/departments/{id}',
    tree: 'GET /api/v2/departments/tree',
  },

  // 设备管理模块
  devices: {
    read: 'GET /api/v2/devices',
    create: 'POST /api/v2/devices',
    update: 'PUT /api/v2/devices/{id}',
    delete: 'DELETE /api/v2/devices/{id}',
    batch: 'POST /api/v2/devices/batch',
    search: 'GET /api/v2/devices/search',
    data: 'GET /api/v2/devices/{id}/data',
    status: 'GET /api/v2/devices/{id}/status',
    statistics: 'GET /api/v2/devices/statistics',
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
    schedule: 'GET /api/v2/devices/maintenance/schedule',
  },

  'device-processes': {
    read: 'GET /api/v2/devices/{id}/processes',
    create: 'POST /api/v2/devices/{id}/processes',
    update: 'PUT /api/v2/devices/processes/{id}',
    delete: 'DELETE /api/v2/devices/processes/{id}',
    execute: 'POST /api/v2/devices/processes/{id}/execute',
  },

  // AI监控模块
  'ai-predictions': {
    read: 'GET /api/v2/ai/predictions',
    create: 'POST /api/v2/ai/predictions',
    update: 'PUT /api/v2/ai/predictions/{id}',
    delete: 'DELETE /api/v2/ai/predictions/{id}',
    export: 'GET /api/v2/ai/predictions/{id}/export',
    share: 'POST /api/v2/ai/predictions/{id}/share',
  },

  'ai-models': {
    read: 'GET /api/v2/ai/models',
    create: 'POST /api/v2/ai/models',
    update: 'PUT /api/v2/ai/models/{id}',
    delete: 'DELETE /api/v2/ai/models/{id}',
    train: 'POST /api/v2/ai/models/{id}/train',
    metrics: 'GET /api/v2/ai/models/{id}/metrics',
  },

  'ai-annotations': {
    read: 'GET /api/v2/ai/annotations',
    create: 'POST /api/v2/ai/annotations',
    update: 'PUT /api/v2/ai/annotations/{id}',
    delete: 'DELETE /api/v2/ai/annotations/{id}',
    import: 'POST /api/v2/ai/annotations/{id}/import',
    export: 'GET /api/v2/ai/annotations/{id}/export',
  },

  'ai-health-scores': {
    read: 'GET /api/v2/ai/health-scores',
    create: 'POST /api/v2/ai/health-scores',
    update: 'PUT /api/v2/ai/health-scores/{id}',
    delete: 'DELETE /api/v2/ai/health-scores/{id}',
    export: 'GET /api/v2/ai/health-scores/export',
    config: 'PUT /api/v2/ai/health-scores/config',
    trends: 'GET /api/v2/ai/health-scores/trends',
  },

  'ai-analysis': {
    read: 'GET /api/v2/ai/analysis',
    create: 'POST /api/v2/ai/analysis',
    update: 'PUT /api/v2/ai/analysis/{id}',
    delete: 'DELETE /api/v2/ai/analysis/{id}',
    results: 'GET /api/v2/ai/analysis/{id}/results',
    schedule: 'POST /api/v2/ai/analysis/{id}/schedule',
  },

  // 报警管理模块
  alarms: {
    read: 'GET /api/v2/alarms',
    update: 'PUT /api/v2/alarms/{id}',
    handle: 'PUT /api/v2/alarms/{id}/handle',
    'batch-handle': 'PUT /api/v2/alarms/batch-handle',
    acknowledge: 'POST /api/v2/alarms/{id}/acknowledge',
    statistics: 'GET /api/v2/alarms/statistics',
  },

  // 统计分析模块
  statistics: {
    'online-rate': 'GET /api/v2/statistics/online-rate',
    'weld-records': 'GET /api/v2/statistics/weld-records',
    'weld-time': 'GET /api/v2/statistics/weld-time',
    'welding-reports': 'GET /api/v2/statistics/welding-reports',
    dashboard: 'GET /api/v2/statistics/dashboard',
    'custom-report': 'POST /api/v2/statistics/custom-report',
  },

  // 统计分析具体资源配置
  online_rate_statistics: {
    read: 'GET /api/v2/statistics/online-rate',
    export: 'GET /api/v2/statistics/online-rate/export',
  },

  weld_record: {
    read: 'GET /api/v2/statistics/weld-records',
    export: 'GET /api/v2/statistics/weld-records/export',
  },

  weld_time: {
    read: 'GET /api/v2/statistics/weld-time',
    export: 'GET /api/v2/statistics/weld-time/export',
  },

  welding_report: {
    read: 'GET /api/v2/statistics/welding-reports',
    export: 'GET /api/v2/statistics/welding-reports/export',
  },

  // AI监控具体资源配置
  ai_monitor_dashboard: {
    read: 'GET /api/v2/ai/dashboard',
    export: 'GET /api/v2/ai/dashboard/export',
  },

  anomaly_detection: {
    read: 'GET /api/v2/ai/anomaly-detection',
    control: 'POST /api/v2/ai/anomaly-detection/control',
    export: 'GET /api/v2/ai/anomaly-detection/export',
  },

  data_annotation: {
    read: 'GET /api/v2/ai/annotations',
    create: 'POST /api/v2/ai/annotations',
    update: 'PUT /api/v2/ai/annotations/{id}',
    delete: 'DELETE /api/v2/ai/annotations/{id}',
  },

  model_management: {
    read: 'GET /api/v2/ai/models',
    create: 'POST /api/v2/ai/models',
    update: 'PUT /api/v2/ai/models/{id}',
    delete: 'DELETE /api/v2/ai/models/{id}',
  },

  smart_analysis: {
    read: 'GET /api/v2/ai/analysis',
    create: 'POST /api/v2/ai/analysis',
    update: 'PUT /api/v2/ai/analysis/{id}',
    delete: 'DELETE /api/v2/ai/analysis/{id}',
  },

  health_scoring: {
    read: 'GET /api/v2/ai/health-scores',
    create: 'POST /api/v2/ai/health-scores',
    update: 'PUT /api/v2/ai/health-scores/{id}',
    delete: 'DELETE /api/v2/ai/health-scores/{id}',
  },

  trend_prediction: {
    read: 'GET /api/v2/ai/predictions',
    create: 'POST /api/v2/ai/predictions',
    update: 'PUT /api/v2/ai/predictions/{id}',
    delete: 'DELETE /api/v2/ai/predictions/{id}',
  },

  // 系统参数配置
  system_param: {
    read: 'GET /api/v2/system/params',
    create: 'POST /api/v2/system/params',
    update: 'PUT /api/v2/system/params/{id}',
    delete: 'DELETE /api/v2/system/params/{id}',
  },

  // 字典数据配置
  dict_data: {
    read: 'GET /api/v2/system/dict-data',
    create: 'POST /api/v2/system/dict-data',
    update: 'PUT /api/v2/system/dict-data/{id}',
    delete: 'DELETE /api/v2/system/dict-data/{id}',
  },

  // API管理配置
  api: {
    read: 'GET /api/v2/system/apis',
    create: 'POST /api/v2/system/apis',
    update: 'PUT /api/v2/system/apis/{id}',
    delete: 'DELETE /api/v2/system/apis/{id}',
  },

  'api-groups': {
    read: 'GET /api/v2/api-groups',
    create: 'POST /api/v2/api-groups',
    update: 'PUT /api/v2/api-groups/{id}',
    delete: 'DELETE /api/v2/api-groups/{id}',
    'move-apis': 'POST /api/v2/api-groups/{id}/apis',
    all: 'GET /api/v2/api-groups/all',
  },

  // 仪表板模块
  dashboard: {
    overview: 'GET /api/v2/dashboard/overview',
    'device-stats': 'GET /api/v2/dashboard/device-stats',
    'alarm-stats': 'GET /api/v2/dashboard/alarm-stats',
    widgets: 'GET /api/v2/dashboard/widgets',
    'create-widget': 'POST /api/v2/dashboard/widgets',
    'update-widget': 'PUT /api/v2/dashboard/widgets/{id}',
  },
}

// 页面路径到权限资源的映射 - 支持v2页面结构
export const PAGE_PERMISSION_MAP_V2 = {
  // 系统管理模块
  '/system/user': 'users',
  '/system/role': 'roles',
  '/system/menu': 'menus',
  '/system/dept': 'departments',
  '/system/api/groups': 'api-groups',

  // 设备管理页面
  '/device/baseinfo': 'devices',
  '/device/type': 'device-types',
  '/device-maintenance/repair-records': 'device-maintenance',
  '/process/process-card': 'device-processes',
  '/device-monitor': 'devices',

  // AI监控页面
  '/ai-monitor/trend-prediction': 'ai-predictions',
  '/ai-monitor/model-management': 'ai-models',
  '/ai-monitor/data-annotation': 'ai-annotations',
  '/ai-monitor/health-scoring': 'ai-health-scores',
  '/ai-monitor/smart-analysis': 'ai-analysis',

  // 报警管理页面
  '/alarm/alarm-info': 'alarms',

  // 统计分析页面
  '/statistics/online-rate': 'statistics',
  '/statistics/weld-record': 'statistics',
  '/statistics/weld-time': 'statistics',
  '/statistics/welding-report': 'statistics',

  // 仪表板页面
  '/dashboard': 'dashboard',
}

// v1到v2权限迁移映射
export const PERMISSION_MIGRATION_MAP_V2 = {
  // 用户管理迁移
  'GET /api/v1/users': 'GET /api/v2/users',
  'POST /api/v1/users': 'POST /api/v2/users',
  'PUT /api/v1/users/{id}': 'PUT /api/v2/users/{id}',
  'DELETE /api/v1/users/{id}': 'DELETE /api/v2/users/{id}',
  'POST /api/v1/users/{id}/reset-password': 'POST /api/v2/users/{id}/actions/reset-password',

  // 角色管理迁移
  'GET /api/v1/roles': 'GET /api/v2/roles',
  'POST /api/v1/roles': 'POST /api/v2/roles',
  'PUT /api/v1/roles/{id}': 'PUT /api/v2/roles/{id}',
  'DELETE /api/v1/roles/{id}': 'DELETE /api/v2/roles/{id}',
  'GET /api/v1/roles/{id}/permissions': 'GET /api/v2/roles/{id}/permissions',
  'PUT /api/v1/roles/{id}/permissions': 'PUT /api/v2/roles/{id}/permissions',

  // 菜单管理迁移
  'GET /api/v1/menus': 'GET /api/v2/menus',
  'POST /api/v1/menus': 'POST /api/v2/menus',
  'PUT /api/v1/menus/{id}': 'PUT /api/v2/menus/{id}',
  'DELETE /api/v1/menus/{id}': 'DELETE /api/v2/menus/{id}',

  // 部门管理迁移
  'GET /api/v1/departments': 'GET /api/v2/departments',
  'POST /api/v1/departments': 'POST /api/v2/departments',
  'PUT /api/v1/departments/{id}': 'PUT /api/v2/departments/{id}',
  'DELETE /api/v1/departments/{id}': 'DELETE /api/v2/departments/{id}',

  // 设备管理迁移
  'GET /api/v1/devices': 'GET /api/v2/devices',
  'POST /api/v1/devices': 'POST /api/v2/devices',
  'PUT /api/v1/devices/{id}': 'PUT /api/v2/devices/{id}',
  'DELETE /api/v1/devices/{id}': 'DELETE /api/v2/devices/{id}',
  'GET /api/v1/devices/{id}/data': 'GET /api/v2/devices/{id}/data',

  // 设备类型迁移
  'GET /api/v1/devices/types': 'GET /api/v2/devices/types',
  'POST /api/v1/devices/types': 'POST /api/v2/devices/types',
  'PUT /api/v1/devices/types/{id}': 'PUT /api/v2/devices/types/{id}',
  'DELETE /api/v1/devices/types/{id}': 'DELETE /api/v2/devices/types/{id}',

  // 报警管理迁移
  'GET /api/v1/alarms': 'GET /api/v2/alarms',
  'PUT /api/v1/alarms/{id}/handle': 'PUT /api/v2/alarms/{id}/handle',
  'PUT /api/v1/alarms/batch-handle': 'PUT /api/v2/alarms/batch-handle',

  // 统计分析迁移
  'GET /api/v1/statistics/online-rate': 'GET /api/v2/statistics/online-rate',
  'GET /api/v1/statistics/weld-records': 'GET /api/v2/statistics/weld-records',
  'GET /api/v1/statistics/weld-time': 'GET /api/v2/statistics/weld-time',
  'GET /api/v1/statistics/welding-reports': 'GET /api/v2/statistics/welding-reports',

  // 仪表板迁移
  'GET /api/v1/dashboard/overview': 'GET /api/v2/dashboard/overview',
  'GET /api/v1/dashboard/device-stats': 'GET /api/v2/dashboard/device-stats',
  'GET /api/v1/dashboard/alarm-stats': 'GET /api/v2/dashboard/alarm-stats',
}

/**
 * 权限配置管理器类
 * 提供统一的权限配置管理接口
 */
export class PermissionConfigManager {
  constructor() {
    this.config = PERMISSION_CONFIG_V2
    this.pageMap = PAGE_PERMISSION_MAP_V2
    this.migrationMap = PERMISSION_MIGRATION_MAP_V2
  }

  /**
   * 获取权限标识
   * @param {string} resource - 资源名称 (如: 'users', 'devices')
   * @param {string} action - 操作类型 (如: 'read', 'create', 'update', 'delete')
   * @returns {string|null} 权限标识
   */
  getPermission(resource, action) {
    return this.config[resource]?.[action] || null
  }

  /**
   * 批量获取资源的所有权限
   * @param {string} resource - 资源名称
   * @returns {Object} 权限映射对象
   */
  getResourcePermissions(resource) {
    return this.config[resource] || {}
  }

  /**
   * 根据页面路径获取对应的权限资源
   * @param {string} pagePath - 页面路径
   * @returns {string|null} 权限资源名称
   */
  getResourceByPage(pagePath) {
    return this.pageMap[pagePath] || null
  }

  /**
   * 根据页面路径和操作获取权限标识
   * @param {string} pagePath - 页面路径
   * @param {string} action - 操作类型
   * @returns {string|null} 权限标识
   */
  getPermissionByPage(pagePath, action) {
    const resource = this.getResourceByPage(pagePath)
    return resource ? this.getPermission(resource, action) : null
  }

  /**
   * 权限验证
   * @param {string[]} userPermissions - 用户权限列表
   * @param {string|string[]} requiredPermission - 需要的权限
   * @param {string} mode - 验证模式: 'any' | 'all'
   * @returns {boolean} 是否有权限
   */
  hasPermission(userPermissions, requiredPermission, mode = 'any') {
    if (!Array.isArray(userPermissions)) {
      return false
    }

    if (typeof requiredPermission === 'string') {
      return userPermissions.includes(requiredPermission)
    }

    if (Array.isArray(requiredPermission)) {
      if (mode === 'all') {
        return requiredPermission.every((perm) => userPermissions.includes(perm))
      } else {
        return requiredPermission.some((perm) => userPermissions.includes(perm))
      }
    }

    return false
  }

  /**
   * 迁移旧权限标识到新权限标识
   * @param {string} oldPermission - 旧的权限标识
   * @returns {string} 新的权限标识
   */
  migratePermission(oldPermission) {
    return this.migrationMap[oldPermission] || oldPermission
  }

  /**
   * 批量迁移权限标识
   * @param {string[]} oldPermissions - 旧的权限标识数组
   * @returns {string[]} 新的权限标识数组
   */
  migratePermissions(oldPermissions) {
    return oldPermissions.map((permission) => this.migratePermission(permission))
  }

  /**
   * 检查权限是否需要迁移
   * @param {string} permission - 权限标识
   * @returns {boolean} 是否需要迁移
   */
  needsMigration(permission) {
    return !!this.migrationMap[permission]
  }

  /**
   * 验证权限格式是否正确
   * @param {string} permission - 权限标识
   * @returns {boolean} 是否为有效格式
   */
  isValidPermissionFormat(permission) {
    // v2权限格式: HTTP方法 /api/v2/资源路径
    const v2Pattern = /^(GET|POST|PUT|DELETE|PATCH)\s+\/api\/v2\/[\w\-\/{}]+$/
    // v1权限格式兼容
    const v1Pattern = /^(GET|POST|PUT|DELETE|PATCH)\s+\/api\/v1\/[\w\-\/{}]+$/

    return v2Pattern.test(permission) || v1Pattern.test(permission)
  }

  /**
   * 获取所有权限列表
   * @returns {string[]} 权限标识列表
   */
  getAllPermissions() {
    const permissions = []
    Object.values(this.config).forEach((resourceConfig) => {
      Object.values(resourceConfig).forEach((permission) => {
        if (permission && !permissions.includes(permission)) {
          permissions.push(permission)
        }
      })
    })
    return permissions
  }

  /**
   * 按模块分组获取权限
   * @returns {Object} 按模块分组的权限
   */
  getPermissionsByModule() {
    return {
      system: {
        users: this.config.users,
        roles: this.config.roles,
        menus: this.config.menus,
        departments: this.config.departments,
      },
      device: {
        devices: this.config.devices,
        'device-types': this.config['device-types'],
        'device-maintenance': this.config['device-maintenance'],
        'device-processes': this.config['device-processes'],
      },
      ai: {
        'ai-predictions': this.config['ai-predictions'],
        'ai-models': this.config['ai-models'],
        'ai-annotations': this.config['ai-annotations'],
        'ai-health-scores': this.config['ai-health-scores'],
        'ai-analysis': this.config['ai-analysis'],
      },
      monitoring: {
        alarms: this.config.alarms,
        statistics: this.config.statistics,
        dashboard: this.config.dashboard,
      },
    }
  }

  /**
   * 兼容性检查 - 检查新旧权限格式的兼容性
   * @param {string[]} permissions - 权限列表
   * @returns {Object} 兼容性检查结果
   */
  checkCompatibility(permissions) {
    const result = {
      valid: [],
      invalid: [],
      needsMigration: [],
      migrated: [],
    }

    permissions.forEach((permission) => {
      if (this.isValidPermissionFormat(permission)) {
        result.valid.push(permission)

        if (this.needsMigration(permission)) {
          result.needsMigration.push(permission)
          result.migrated.push(this.migratePermission(permission))
        }
      } else {
        result.invalid.push(permission)
      }
    })

    return result
  }
}

// 创建全局实例
export const permissionManager = new PermissionConfigManager()

// 便捷函数导出
export const getPermission = (resource, action) => permissionManager.getPermission(resource, action)
export const getResourcePermissions = (resource) =>
  permissionManager.getResourcePermissions(resource)
export const getPermissionByPage = (pagePath, action) =>
  permissionManager.getPermissionByPage(pagePath, action)
export const getResourceByPage = (pagePath) => permissionManager.getResourceByPage(pagePath)
export const migratePermission = (oldPermission) =>
  permissionManager.migratePermission(oldPermission)
export const migratePermissions = (oldPermissions) =>
  permissionManager.migratePermissions(oldPermissions)
export const hasPermission = (userPermissions, requiredPermission, mode) =>
  permissionManager.hasPermission(userPermissions, requiredPermission, mode)
export const isValidPermissionFormat = (permission) =>
  permissionManager.isValidPermissionFormat(permission)
export const needsMigration = (permission) => permissionManager.needsMigration(permission)
export const getAllPermissions = () => permissionManager.getAllPermissions()
export const getPermissionsByModule = () => permissionManager.getPermissionsByModule()
export const checkCompatibility = (permissions) => permissionManager.checkCompatibility(permissions)

export default permissionManager
