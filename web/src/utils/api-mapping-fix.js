/**
 * API映射修复工具
 * 用于在运行时动态添加缺失的API路径映射
 */

import { pageApiHelper } from './api-v2-migration.js'

// 确保关键的API映射存在
const criticalMappings = {
  // API管理
  'GET /apis': 'GET /api/v2/apis',
  'POST /apis': 'POST /api/v2/apis',
  'PUT /apis/{id}': 'PUT /api/v2/apis/{id}',
  'DELETE /apis/{id}': 'DELETE /api/v2/apis/{id}',
  'POST /apis/refresh': 'POST /api/v2/apis/refresh',

  // 审计日志
  'GET /audit-logs': 'GET /api/v2/audit-logs',
  'GET /audit_logs': 'GET /api/v2/audit-logs',

  // 字典类型
  'GET /dict-types': 'GET /api/v2/dict-types',
  'POST /dict-types': 'POST /api/v2/dict-types',
  'PUT /dict-types/{id}': 'PUT /api/v2/dict-types/{id}',
  'DELETE /dict-types/{id}': 'DELETE /api/v2/dict-types/{id}',

  // 字典数据
  'GET /dict-data': 'GET /api/v2/dict-data',
  'POST /dict-data': 'POST /api/v2/dict-data',
  'PUT /dict-data/{id}': 'PUT /api/v2/dict-data/{id}',
  'DELETE /dict-data/{id}': 'DELETE /api/v2/dict-data/{id}',

  // 系统参数
  'GET /system-params': 'GET /api/v2/system/config',
  'POST /system-params': 'POST /api/v2/system/config',
  'PUT /system-params/{id}': 'PUT /api/v2/system/config/{id}',
  'DELETE /system-params/{id}': 'DELETE /api/v2/system/config/{id}',
}

// 应用修复
export function applyApiMappingFix() {
  try {
    if (!pageApiHelper) {
      console.error('pageApiHelper 未定义')
      return
    }

    const pathConverter = pageApiHelper.pathConverter

    if (!pathConverter) {
      console.error('pathConverter 未定义')
      return
    }

    if (!pathConverter.mapping) {
      console.error('pathConverter.mapping 未定义')
      return
    }

    // 添加缺失的映射
    Object.entries(criticalMappings).forEach(([key, value]) => {
      if (!pathConverter.mapping[key]) {
        pathConverter.mapping[key] = value
        console.log(`添加API映射: ${key} -> ${value}`)
      }
    })

    console.log('API映射修复完成')
  } catch (error) {
    console.error('API映射修复失败:', error)
  }
}

// 不自动应用修复，只在需要时手动调用
// applyApiMappingFix()

export default {
  applyApiMappingFix,
  criticalMappings,
}
