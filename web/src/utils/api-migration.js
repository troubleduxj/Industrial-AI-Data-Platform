/**
 * API迁移工具
 * 帮助前端代码从v1平滑迁移到v2
 */

// API版本检测
export function detectApiVersion(response) {
  // v2版本响应包含success字段
  if (response && typeof response.success === 'boolean') {
    return 'v2'
  }
  // v1版本响应包含code和msg字段
  if (response && typeof response.code === 'number' && response.msg !== undefined) {
    return 'v1'
  }
  return 'unknown'
}

// 响应格式标准化
export function normalizeResponse(response) {
  const version = detectApiVersion(response)

  if (version === 'v2') {
    return {
      // 标准化字段
      success: response.success,
      code: response.code,
      message: response.message,
      data: response.data,
      timestamp: response.timestamp,

      // 分页信息（如果存在）
      total: response.total,
      page: response.page,
      page_size: response.page_size,
      total_pages: response.total_pages,

      // v1兼容字段
      msg: response.message,

      // 元信息
      _version: 'v2',
      _details: response.details,
    }
  } else if (version === 'v1') {
    return {
      // 标准化字段
      success: response.code === 200,
      code: response.code,
      message: response.msg,
      data: response.data,
      timestamp: new Date().toISOString(),

      // v1兼容字段
      msg: response.msg,

      // 元信息
      _version: 'v1',
    }
  }

  return response
}

// 错误格式标准化
export function normalizeError(error) {
  if (error.details) {
    // v2版本错误
    return {
      success: false,
      code: error.code,
      message: error.message,
      details: error.details,
      error_code: error.details.error_code,
      _version: 'v2',
    }
  } else {
    // v1版本错误
    return {
      success: false,
      code: error.code,
      message: error.message || error.msg,
      _version: 'v1',
    }
  }
}

// 创建迁移包装器
export function createMigrationWrapper(apiFunction, options = {}) {
  const { enableV2 = false, fallbackToV1 = true, logMigration = false } = options

  return async (...args) => {
    try {
      const response = await apiFunction(...args)
      const normalized = normalizeResponse(response)

      if (logMigration) {
        console.log(`API Migration: ${normalized._version} response`, normalized)
      }

      return normalized
    } catch (error) {
      const normalized = normalizeError(error)

      if (logMigration) {
        console.error(`API Migration: ${normalized._version} error`, normalized)
      }

      throw normalized
    }
  }
}

// 批量迁移API对象
export function migrateApiObject(apiObject, options = {}) {
  const migratedApi = {}

  for (const [key, apiFunction] of Object.entries(apiObject)) {
    if (typeof apiFunction === 'function') {
      migratedApi[key] = createMigrationWrapper(apiFunction, options)
    } else {
      migratedApi[key] = apiFunction
    }
  }

  return migratedApi
}

// 渐进式迁移配置
export const migrationConfig = {
  // 已迁移到v2的API列表
  migratedApis: ['getUserList', 'getUserById', 'healthCheck'],

  // 计划迁移的API列表
  plannedMigrations: ['createUser', 'updateUser', 'deleteUser', 'getRoleList', 'getMenus'],

  // 检查API是否已迁移
  isMigrated(apiName) {
    return this.migratedApis.includes(apiName)
  },

  // 检查API是否计划迁移
  isPlannedForMigration(apiName) {
    return this.plannedMigrations.includes(apiName)
  },

  // 标记API为已迁移
  markAsMigrated(apiName) {
    if (!this.migratedApis.includes(apiName)) {
      this.migratedApis.push(apiName)
    }

    const index = this.plannedMigrations.indexOf(apiName)
    if (index > -1) {
      this.plannedMigrations.splice(index, 1)
    }
  },
}

// 迁移状态报告
export function getMigrationReport() {
  return {
    migrated: migrationConfig.migratedApis.length,
    planned: migrationConfig.plannedMigrations.length,
    total: migrationConfig.migratedApis.length + migrationConfig.plannedMigrations.length,
    progress:
      (migrationConfig.migratedApis.length /
        (migrationConfig.migratedApis.length + migrationConfig.plannedMigrations.length)) *
      100,
    migratedApis: [...migrationConfig.migratedApis],
    plannedApis: [...migrationConfig.plannedMigrations],
  }
}

// 开发环境下的迁移提示
export function logMigrationStatus() {
  if (process.env.NODE_ENV === 'development') {
    const report = getMigrationReport()
    console.group('🚀 API Migration Status')
    console.log(`Progress: ${report.progress.toFixed(1)}% (${report.migrated}/${report.total})`)
    console.log('Migrated APIs:', report.migratedApis)
    console.log('Planned APIs:', report.plannedApis)
    console.groupEnd()
  }
}
