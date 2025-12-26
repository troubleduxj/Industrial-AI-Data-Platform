#!/usr/bin/env node
/**
 * API权限重构辅助脚本
 * 生成重构所需的配置文件和迁移脚本
 */
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const projectRoot = path.join(__dirname, '..')

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
}

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`)
}

// API重构映射表
const API_REFACTOR_MAP = {
  // 系统管理
  'get/api/v1/user/list': 'GET /api/v1/users',
  'get/api/v1/user/get': 'GET /api/v1/users/{id}',
  'post/api/v1/user/create': 'POST /api/v1/users',
  'post/api/v1/user/update': 'PUT /api/v1/users/{id}',
  'delete/api/v1/user/delete': 'DELETE /api/v1/users/{id}',
  'post/api/v1/user/reset_password': 'POST /api/v1/users/{id}/reset-password',

  // 角色管理
  'get/api/v1/role/list': 'GET /api/v1/roles',
  'get/api/v1/role/get': 'GET /api/v1/roles/{id}',
  'post/api/v1/role/create': 'POST /api/v1/roles',
  'post/api/v1/role/update': 'PUT /api/v1/roles/{id}',
  'delete/api/v1/role/delete': 'DELETE /api/v1/roles/{id}',
  'get/api/v1/role/authorized': 'GET /api/v1/roles/{id}/permissions',
  'post/api/v1/role/authorized': 'PUT /api/v1/roles/{id}/permissions',

  // 菜单管理
  'get/api/v1/menu/list': 'GET /api/v1/menus',
  'get/api/v1/menu/get': 'GET /api/v1/menus/{id}',
  'post/api/v1/menu/create': 'POST /api/v1/menus',
  'post/api/v1/menu/update': 'PUT /api/v1/menus/{id}',
  'delete/api/v1/menu/delete': 'DELETE /api/v1/menus/{id}',

  // 部门管理
  'get/api/v1/dept/list': 'GET /api/v1/departments',
  'post/api/v1/dept/create': 'POST /api/v1/departments',
  'post/api/v1/dept/update': 'PUT /api/v1/departments/{id}',
  'delete/api/v1/dept/delete': 'DELETE /api/v1/departments/{id}',

  // API管理
  'get/api/v1/api/list': 'GET /api/v1/apis',
  'post/api/v1/api/create': 'POST /api/v1/apis',
  'post/api/v1/api/update': 'PUT /api/v1/apis/{id}',
  'delete/api/v1/api/delete': 'DELETE /api/v1/apis/{id}',
  'post/api/v1/api/refresh': 'POST /api/v1/apis/refresh',

  // 设备管理
  'get/api/v1/device/list': 'GET /api/v1/devices',
  'post/api/v1/device/create': 'POST /api/v1/devices',
  'put/api/v1/device/update': 'PUT /api/v1/devices/{id}',
  'delete/api/v1/device/delete': 'DELETE /api/v1/devices/{id}',

  // 设备类型
  'get/api/v1/device/types': 'GET /api/v1/devices/types',
  'post/api/v1/device/types': 'POST /api/v1/devices/types',
  'put/api/v1/device/types': 'PUT /api/v1/devices/types/{id}',
  'delete/api/v1/device/types': 'DELETE /api/v1/devices/types/{id}',

  // 设备监控
  'get/api/v1/device/data': 'GET /api/v1/devices/{id}/data',
  'ws/api/v1/device/ws': 'WebSocket /api/v1/devices/ws',

  // 报警管理
  'get/api/v1/alarm/list': 'GET /api/v1/alarms',
}

// 新增API配置 (当前缺失的API)
const NEW_API_CONFIG = {
  // AI监控模块
  'ai-predictions': {
    'GET /api/v1/ai/predictions': '查看预测列表',
    'POST /api/v1/ai/predictions': '开始预测',
    'GET /api/v1/ai/predictions/{id}': '获取预测结果',
    'GET /api/v1/ai/predictions/{id}/export': '导出预测报告',
  },
  'ai-models': {
    'GET /api/v1/ai/models': '查看模型列表',
    'POST /api/v1/ai/models': '上传模型',
    'PUT /api/v1/ai/models/{id}': '更新模型',
    'DELETE /api/v1/ai/models/{id}': '删除模型',
  },
  'ai-annotations': {
    'GET /api/v1/ai/annotations': '查看标注项目',
    'POST /api/v1/ai/annotations': '创建标注项目',
    'PUT /api/v1/ai/annotations/{id}': '更新标注',
    'POST /api/v1/ai/annotations/{id}/import': '导入数据',
  },
  'ai-health': {
    'GET /api/v1/ai/health-scores': '查看健康评分',
    'POST /api/v1/ai/health-scores': '计算健康评分',
    'GET /api/v1/ai/health-scores/export': '导出健康报告',
    'PUT /api/v1/ai/health-scores/config': '评分配置',
  },
  'ai-analysis': {
    'GET /api/v1/ai/analysis': '查看分析列表',
    'POST /api/v1/ai/analysis': '开始分析',
    'GET /api/v1/ai/analysis/{id}': '获取分析结果',
  },

  // 设备维护模块
  'device-maintenance': {
    'GET /api/v1/devices/{id}/maintenance': '查看维护记录',
    'POST /api/v1/devices/{id}/maintenance': '创建维护记录',
    'PUT /api/v1/devices/maintenance/{id}': '更新维护记录',
    'DELETE /api/v1/devices/maintenance/{id}': '删除维护记录',
  },

  // 工艺管理模块
  'device-processes': {
    'GET /api/v1/devices/{id}/processes': '查看工艺',
    'POST /api/v1/devices/{id}/processes': '创建工艺',
    'PUT /api/v1/devices/processes/{id}': '更新工艺',
    'DELETE /api/v1/devices/processes/{id}': '删除工艺',
  },

  // 报警管理扩展
  'alarms-extended': {
    'GET /api/v1/alarms/{id}': '获取报警详情',
    'PUT /api/v1/alarms/{id}/handle': '处理报警',
    'PUT /api/v1/alarms/batch-handle': '批量处理报警',
  },

  // 统计分析模块
  statistics: {
    'GET /api/v1/statistics/online-rate': '在线率统计',
    'GET /api/v1/statistics/weld-records': '焊接记录',
    'GET /api/v1/statistics/weld-time': '焊接时长统计',
    'GET /api/v1/statistics/welding-reports': '焊接报告',
  },

  // 仪表板模块
  dashboard: {
    'GET /api/v1/dashboard/overview': '查看概览数据',
    'GET /api/v1/dashboard/device-stats': '查看设备统计',
    'GET /api/v1/dashboard/alarm-stats': '查看报警统计',
  },
}

// 前端权限配置映射
const FRONTEND_PERMISSION_MAP = {
  // 系统管理
  users: {
    read: 'GET /api/v1/users',
    create: 'POST /api/v1/users',
    update: 'PUT /api/v1/users/{id}',
    delete: 'DELETE /api/v1/users/{id}',
    'reset-password': 'POST /api/v1/users/{id}/reset-password',
  },
  roles: {
    read: 'GET /api/v1/roles',
    create: 'POST /api/v1/roles',
    update: 'PUT /api/v1/roles/{id}',
    delete: 'DELETE /api/v1/roles/{id}',
    'assign-permissions': 'PUT /api/v1/roles/{id}/permissions',
  },
  menus: {
    read: 'GET /api/v1/menus',
    create: 'POST /api/v1/menus',
    update: 'PUT /api/v1/menus/{id}',
    delete: 'DELETE /api/v1/menus/{id}',
  },
  departments: {
    read: 'GET /api/v1/departments',
    create: 'POST /api/v1/departments',
    update: 'PUT /api/v1/departments/{id}',
    delete: 'DELETE /api/v1/departments/{id}',
  },
  apis: {
    read: 'GET /api/v1/apis',
    create: 'POST /api/v1/apis',
    update: 'PUT /api/v1/apis/{id}',
    delete: 'DELETE /api/v1/apis/{id}',
    refresh: 'POST /api/v1/apis/refresh',
  },

  // 设备管理
  devices: {
    read: 'GET /api/v1/devices',
    create: 'POST /api/v1/devices',
    update: 'PUT /api/v1/devices/{id}',
    delete: 'DELETE /api/v1/devices/{id}',
    monitor: 'GET /api/v1/devices/{id}/data',
  },
  'device-types': {
    read: 'GET /api/v1/devices/types',
    create: 'POST /api/v1/devices/types',
    update: 'PUT /api/v1/devices/types/{id}',
    delete: 'DELETE /api/v1/devices/types/{id}',
  },
  'device-maintenance': {
    read: 'GET /api/v1/devices/{id}/maintenance',
    create: 'POST /api/v1/devices/{id}/maintenance',
    update: 'PUT /api/v1/devices/maintenance/{id}',
    delete: 'DELETE /api/v1/devices/maintenance/{id}',
  },
  'device-processes': {
    read: 'GET /api/v1/devices/{id}/processes',
    create: 'POST /api/v1/devices/{id}/processes',
    update: 'PUT /api/v1/devices/processes/{id}',
    delete: 'DELETE /api/v1/devices/processes/{id}',
  },

  // 报警管理
  alarms: {
    read: 'GET /api/v1/alarms',
    handle: 'PUT /api/v1/alarms/{id}/handle',
    'batch-handle': 'PUT /api/v1/alarms/batch-handle',
  },

  // AI监控
  'ai-predictions': {
    read: 'GET /api/v1/ai/predictions',
    create: 'POST /api/v1/ai/predictions',
    export: 'GET /api/v1/ai/predictions/{id}/export',
  },
  'ai-models': {
    read: 'GET /api/v1/ai/models',
    upload: 'POST /api/v1/ai/models',
    update: 'PUT /api/v1/ai/models/{id}',
    delete: 'DELETE /api/v1/ai/models/{id}',
  },
  'ai-annotations': {
    read: 'GET /api/v1/ai/annotations',
    create: 'POST /api/v1/ai/annotations',
    update: 'PUT /api/v1/ai/annotations/{id}',
    import: 'POST /api/v1/ai/annotations/{id}/import',
  },
  'ai-health': {
    read: 'GET /api/v1/ai/health-scores',
    calculate: 'POST /api/v1/ai/health-scores',
    export: 'GET /api/v1/ai/health-scores/export',
    config: 'PUT /api/v1/ai/health-scores/config',
  },
  'ai-analysis': {
    read: 'GET /api/v1/ai/analysis',
    create: 'POST /api/v1/ai/analysis',
  },

  // 统计分析
  statistics: {
    'online-rate': 'GET /api/v1/statistics/online-rate',
    'weld-records': 'GET /api/v1/statistics/weld-records',
    'weld-time': 'GET /api/v1/statistics/weld-time',
    'welding-reports': 'GET /api/v1/statistics/welding-reports',
  },

  // 仪表板
  dashboard: {
    overview: 'GET /api/v1/dashboard/overview',
    'device-stats': 'GET /api/v1/dashboard/device-stats',
    'alarm-stats': 'GET /api/v1/dashboard/alarm-stats',
  },
}

/**
 * 生成权限配置文件
 */
function generatePermissionConfig() {
  const configPath = path.join(projectRoot, 'src/utils/permission-config.js')
  const configContent = `/**
 * 统一权限配置
 * 重构后的API权限映射
 * 
 * 使用方式：
 * import { getPermission } from '@/utils/permission-config'
 * const permission = getPermission('users', 'create') // 返回 'POST /api/v1/users'
 */

export const PERMISSION_CONFIG = ${JSON.stringify(FRONTEND_PERMISSION_MAP, null, 2)}

/**
 * 获取资源的权限配置
 * @param {string} resource - 资源名称
 * @param {string} action - 操作类型
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
  Object.values(PERMISSION_CONFIG).forEach(resourceConfig => {
    Object.values(resourceConfig).forEach(permission => {
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

export default PERMISSION_CONFIG
`

  fs.writeFileSync(configPath, configContent, 'utf8')
  log(`✅ 权限配置文件已生成: ${configPath}`, 'green')
}

/**
 * 生成权限树配置
 */
function generatePermissionTree() {
  const treePath = path.join(projectRoot, 'src/utils/permission-tree.js')
  const treeContent = `/**
 * 优化后的权限树结构
 * 用于角色管理中的权限配置界面
 */

export const PERMISSION_TREE = [
  {
    key: 'system',
    label: '系统管理',
    children: [
      {
        key: 'users',
        label: '用户管理',
        children: [
          { key: 'GET /api/v1/users', label: '查看用户列表' },
          { key: 'POST /api/v1/users', label: '创建用户' },
          { key: 'PUT /api/v1/users/{id}', label: '更新用户' },
          { key: 'DELETE /api/v1/users/{id}', label: '删除用户' },
          { key: 'POST /api/v1/users/{id}/reset-password', label: '重置密码' }
        ]
      },
      {
        key: 'roles',
        label: '角色管理',
        children: [
          { key: 'GET /api/v1/roles', label: '查看角色列表' },
          { key: 'POST /api/v1/roles', label: '创建角色' },
          { key: 'PUT /api/v1/roles/{id}', label: '更新角色' },
          { key: 'DELETE /api/v1/roles/{id}', label: '删除角色' },
          { key: 'PUT /api/v1/roles/{id}/permissions', label: '配置权限' }
        ]
      },
      {
        key: 'menus',
        label: '菜单管理',
        children: [
          { key: 'GET /api/v1/menus', label: '查看菜单列表' },
          { key: 'POST /api/v1/menus', label: '创建菜单' },
          { key: 'PUT /api/v1/menus/{id}', label: '更新菜单' },
          { key: 'DELETE /api/v1/menus/{id}', label: '删除菜单' }
        ]
      },
      {
        key: 'departments',
        label: '部门管理',
        children: [
          { key: 'GET /api/v1/departments', label: '查看部门列表' },
          { key: 'POST /api/v1/departments', label: '创建部门' },
          { key: 'PUT /api/v1/departments/{id}', label: '更新部门' },
          { key: 'DELETE /api/v1/departments/{id}', label: '删除部门' }
        ]
      },
      {
        key: 'apis',
        label: 'API管理',
        children: [
          { key: 'GET /api/v1/apis', label: '查看API列表' },
          { key: 'POST /api/v1/apis', label: '创建API' },
          { key: 'PUT /api/v1/apis/{id}', label: '更新API' },
          { key: 'DELETE /api/v1/apis/{id}', label: '删除API' },
          { key: 'POST /api/v1/apis/refresh', label: '刷新API' }
        ]
      }
    ]
  },
  {
    key: 'devices',
    label: '设备管理',
    children: [
      {
        key: 'device-info',
        label: '设备信息',
        children: [
          { key: 'GET /api/v1/devices', label: '查看设备列表' },
          { key: 'POST /api/v1/devices', label: '创建设备' },
          { key: 'PUT /api/v1/devices/{id}', label: '更新设备' },
          { key: 'DELETE /api/v1/devices/{id}', label: '删除设备' }
        ]
      },
      {
        key: 'device-types',
        label: '设备类型',
        children: [
          { key: 'GET /api/v1/devices/types', label: '查看设备类型' },
          { key: 'POST /api/v1/devices/types', label: '创建设备类型' },
          { key: 'PUT /api/v1/devices/types/{id}', label: '更新设备类型' },
          { key: 'DELETE /api/v1/devices/types/{id}', label: '删除设备类型' }
        ]
      },
      {
        key: 'device-monitor',
        label: '设备监控',
        children: [
          { key: 'GET /api/v1/devices/{id}/data', label: '查看设备数据' },
          { key: 'WebSocket /api/v1/devices/ws', label: '实时数据推送' }
        ]
      },
      {
        key: 'device-maintenance',
        label: '设备维护',
        children: [
          { key: 'GET /api/v1/devices/{id}/maintenance', label: '查看维护记录' },
          { key: 'POST /api/v1/devices/{id}/maintenance', label: '创建维护记录' },
          { key: 'PUT /api/v1/devices/maintenance/{id}', label: '更新维护记录' },
          { key: 'DELETE /api/v1/devices/maintenance/{id}', label: '删除维护记录' }
        ]
      },
      {
        key: 'device-processes',
        label: '工艺管理',
        children: [
          { key: 'GET /api/v1/devices/{id}/processes', label: '查看工艺' },
          { key: 'POST /api/v1/devices/{id}/processes', label: '创建工艺' },
          { key: 'PUT /api/v1/devices/processes/{id}', label: '更新工艺' },
          { key: 'DELETE /api/v1/devices/processes/{id}', label: '删除工艺' }
        ]
      }
    ]
  },
  {
    key: 'alarms',
    label: '报警管理',
    children: [
      { key: 'GET /api/v1/alarms', label: '查看报警列表' },
      { key: 'PUT /api/v1/alarms/{id}/handle', label: '处理报警' },
      { key: 'PUT /api/v1/alarms/batch-handle', label: '批量处理报警' }
    ]
  },
  {
    key: 'ai',
    label: 'AI监控',
    children: [
      {
        key: 'ai-predictions',
        label: '趋势预测',
        children: [
          { key: 'GET /api/v1/ai/predictions', label: '查看预测列表' },
          { key: 'POST /api/v1/ai/predictions', label: '开始预测' },
          { key: 'GET /api/v1/ai/predictions/{id}/export', label: '导出预测报告' }
        ]
      },
      {
        key: 'ai-models',
        label: '模型管理',
        children: [
          { key: 'GET /api/v1/ai/models', label: '查看模型列表' },
          { key: 'POST /api/v1/ai/models', label: '上传模型' },
          { key: 'PUT /api/v1/ai/models/{id}', label: '更新模型' },
          { key: 'DELETE /api/v1/ai/models/{id}', label: '删除模型' }
        ]
      },
      {
        key: 'ai-annotations',
        label: '数据标注',
        children: [
          { key: 'GET /api/v1/ai/annotations', label: '查看标注项目' },
          { key: 'POST /api/v1/ai/annotations', label: '创建标注项目' },
          { key: 'PUT /api/v1/ai/annotations/{id}', label: '更新标注' },
          { key: 'POST /api/v1/ai/annotations/{id}/import', label: '导入数据' }
        ]
      },
      {
        key: 'ai-health',
        label: '健康评分',
        children: [
          { key: 'GET /api/v1/ai/health-scores', label: '查看健康评分' },
          { key: 'POST /api/v1/ai/health-scores', label: '计算健康评分' },
          { key: 'GET /api/v1/ai/health-scores/export', label: '导出健康报告' },
          { key: 'PUT /api/v1/ai/health-scores/config', label: '评分配置' }
        ]
      },
      {
        key: 'ai-analysis',
        label: '智能分析',
        children: [
          { key: 'GET /api/v1/ai/analysis', label: '查看分析列表' },
          { key: 'POST /api/v1/ai/analysis', label: '开始分析' }
        ]
      }
    ]
  },
  {
    key: 'statistics',
    label: '统计分析',
    children: [
      { key: 'GET /api/v1/statistics/online-rate', label: '在线率统计' },
      { key: 'GET /api/v1/statistics/weld-records', label: '焊接记录' },
      { key: 'GET /api/v1/statistics/weld-time', label: '焊接时长统计' },
      { key: 'GET /api/v1/statistics/welding-reports', label: '焊接报告' }
    ]
  },
  {
    key: 'dashboard',
    label: '仪表板',
    children: [
      { key: 'GET /api/v1/dashboard/overview', label: '查看概览数据' },
      { key: 'GET /api/v1/dashboard/device-stats', label: '查看设备统计' },
      { key: 'GET /api/v1/dashboard/alarm-stats', label: '查看报警统计' }
    ]
  }
]

/**
 * 获取扁平化的权限列表
 * @returns {Array} 权限列表
 */
export function getFlatPermissions() {
  const permissions = []
  
  function traverse(nodes) {
    nodes.forEach(node => {
      if (node.children) {
        traverse(node.children)
      } else {
        permissions.push({
          key: node.key,
          label: node.label
        })
      }
    })
  }
  
  traverse(PERMISSION_TREE)
  return permissions
}

/**
 * 根据关键字搜索权限
 * @param {string} keyword - 搜索关键字
 * @returns {Array} 匹配的权限列表
 */
export function searchPermissions(keyword) {
  const flatPermissions = getFlatPermissions()
  return flatPermissions.filter(permission => 
    permission.label.includes(keyword) || 
    permission.key.includes(keyword)
  )
}

export default PERMISSION_TREE
`

  fs.writeFileSync(treePath, treeContent, 'utf8')
  log(`✅ 权限树配置文件已生成: ${treePath}`, 'green')
}

/**
 * 生成API重构映射文件
 */
function generateApiMigrationMap() {
  const mapPath = path.join(projectRoot, 'src/utils/api-migration-map.js')
  const mapContent = `/**
 * API重构映射表
 * 用于从旧API标识迁移到新API标识
 */

export const API_MIGRATION_MAP = ${JSON.stringify(API_REFACTOR_MAP, null, 2)}

/**
 * 获取新的API权限标识
 * @param {string} oldPermission - 旧的权限标识
 * @returns {string|null} 新的权限标识
 */
export function migratePermission(oldPermission) {
  return API_MIGRATION_MAP[oldPermission] || null
}

/**
 * 批量迁移权限标识
 * @param {string[]} oldPermissions - 旧的权限标识数组
 * @returns {string[]} 新的权限标识数组
 */
export function migratePermissions(oldPermissions) {
  return oldPermissions.map(permission => 
    migratePermission(permission) || permission
  ).filter(Boolean)
}

/**
 * 检查是否需要迁移
 * @param {string} permission - 权限标识
 * @returns {boolean} 是否需要迁移
 */
export function needsMigration(permission) {
  return !!API_MIGRATION_MAP[permission]
}

export default API_MIGRATION_MAP
`

  fs.writeFileSync(mapPath, mapContent, 'utf8')
  log(`✅ API迁移映射文件已生成: ${mapPath}`, 'green')
}

/**
 * 生成权限按钮配置示例
 */
function generatePermissionButtonExamples() {
  const examplePath = path.join(projectRoot, 'src/examples/PermissionButtonExamples.vue')
  const exampleContent = `<template>
  <div class="permission-examples">
    <h2>权限按钮使用示例</h2>
    
    <!-- 用户管理示例 -->
    <div class="example-section">
      <h3>用户管理</h3>
      <n-space>
        <PermissionButton 
          :permission="getPermission('users', 'create')"
          type="primary"
          @click="handleCreateUser"
        >
          创建用户
        </PermissionButton>
        
        <PermissionButton 
          :permission="getPermission('users', 'update')"
          type="info"
          @click="handleUpdateUser"
        >
          更新用户
        </PermissionButton>
        
        <PermissionButton 
          :permission="getPermission('users', 'delete')"
          type="error"
          @click="handleDeleteUser"
        >
          删除用户
        </PermissionButton>
        
        <PermissionButton 
          :permission="getPermission('users', 'reset-password')"
          type="warning"
          @click="handleResetPassword"
        >
          重置密码
        </PermissionButton>
      </n-space>
    </div>
    
    <!-- 设备管理示例 -->
    <div class="example-section">
      <h3>设备管理</h3>
      <n-space>
        <PermissionButton 
          :permission="getPermission('devices', 'create')"
          type="primary"
          @click="handleCreateDevice"
        >
          创建设备
        </PermissionButton>
        
        <PermissionButton 
          :permission="getPermission('devices', 'monitor')"
          type="info"
          @click="handleMonitorDevice"
        >
          设备监控
        </PermissionButton>
        
        <PermissionButton 
          :permission="getPermission('device-maintenance', 'create')"
          type="success"
          @click="handleCreateMaintenance"
        >
          创建维护记录
        </PermissionButton>
      </n-space>
    </div>
    
    <!-- AI监控示例 -->
    <div class="example-section">
      <h3>AI监控</h3>
      <n-space>
        <PermissionButton 
          :permission="getPermission('ai-predictions', 'create')"
          type="primary"
          @click="handleStartPrediction"
        >
          开始预测
        </PermissionButton>
        
        <PermissionButton 
          :permission="getPermission('ai-models', 'upload')"
          type="info"
          @click="handleUploadModel"
        >
          上传模型
        </PermissionButton>
        
        <PermissionButton 
          :permission="getPermission('ai-annotations', 'create')"
          type="success"
          @click="handleCreateAnnotation"
        >
          创建标注项目
        </PermissionButton>
      </n-space>
    </div>
    
    <!-- 多权限示例 -->
    <div class="example-section">
      <h3>多权限检查</h3>
      <n-space>
        <!-- 需要任一权限 -->
        <PermissionButton 
          :permission="[
            getPermission('users', 'create'),
            getPermission('users', 'update')
          ]"
          type="primary"
          @click="handleUserOperation"
        >
          用户操作 (创建或更新)
        </PermissionButton>
        
        <!-- 需要所有权限 -->
        <PermissionButton 
          :permission="[
            getPermission('devices', 'read'),
            getPermission('devices', 'update')
          ]"
          :require-all="true"
          type="warning"
          @click="handleDeviceManagement"
        >
          设备管理 (需要读取和更新权限)
        </PermissionButton>
      </n-space>
    </div>
    
    <!-- 权限指令示例 -->
    <div class="example-section">
      <h3>权限指令示例</h3>
      <n-space>
        <!-- 基础权限指令 -->
        <n-button 
          v-permission="getPermission('roles', 'create')"
          type="primary"
          @click="handleCreateRole"
        >
          创建角色 (v-permission)
        </n-button>
        
        <!-- 隐藏模式 -->
        <n-button 
          v-permission.hide="getPermission('roles', 'delete')"
          type="error"
          @click="handleDeleteRole"
        >
          删除角色 (隐藏)
        </n-button>
        
        <!-- 禁用模式 -->
        <n-button 
          v-permission.disable="getPermission('menus', 'update')"
          type="info"
          @click="handleUpdateMenu"
        >
          更新菜单 (禁用)
        </n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup>
import { NSpace, NButton } from 'naive-ui'
import PermissionButton from '@/components/common/PermissionButton.vue'
import { getPermission } from '@/utils/permission-config'

// 事件处理函数
const handleCreateUser = () => console.log('创建用户')
const handleUpdateUser = () => console.log('更新用户')
const handleDeleteUser = () => console.log('删除用户')
const handleResetPassword = () => console.log('重置密码')

const handleCreateDevice = () => console.log('创建设备')
const handleMonitorDevice = () => console.log('设备监控')
const handleCreateMaintenance = () => console.log('创建维护记录')

const handleStartPrediction = () => console.log('开始预测')
const handleUploadModel = () => console.log('上传模型')
const handleCreateAnnotation = () => console.log('创建标注项目')

const handleUserOperation = () => console.log('用户操作')
const handleDeviceManagement = () => console.log('设备管理')

const handleCreateRole = () => console.log('创建角色')
const handleDeleteRole = () => console.log('删除角色')
const handleUpdateMenu = () => console.log('更新菜单')
</script>

<style scoped>
.permission-examples {
  padding: 20px;
}

.example-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.example-section h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #333;
}
</style>
`

  fs.writeFileSync(examplePath, exampleContent, 'utf8')
  log(`✅ 权限按钮示例文件已生成: ${examplePath}`, 'green')
}

/**
 * 生成数据库迁移脚本
 */
function generateDatabaseMigrationScript() {
  const scriptPath = path.join(projectRoot, '../scripts/migrate_permissions.sql')
  const scriptContent = `-- API权限重构数据库迁移脚本
-- 执行前请备份数据库

-- 1. 更新现有权限标识
UPDATE role_apis SET api_path = 'GET /api/v1/users' WHERE api_path = 'get/api/v1/user/list';
UPDATE role_apis SET api_path = 'GET /api/v1/users/{id}' WHERE api_path = 'get/api/v1/user/get';
UPDATE role_apis SET api_path = 'POST /api/v1/users' WHERE api_path = 'post/api/v1/user/create';
UPDATE role_apis SET api_path = 'PUT /api/v1/users/{id}' WHERE api_path = 'post/api/v1/user/update';
UPDATE role_apis SET api_path = 'DELETE /api/v1/users/{id}' WHERE api_path = 'delete/api/v1/user/delete';
UPDATE role_apis SET api_path = 'POST /api/v1/users/{id}/reset-password' WHERE api_path = 'post/api/v1/user/reset_password';

-- 角色管理
UPDATE role_apis SET api_path = 'GET /api/v1/roles' WHERE api_path = 'get/api/v1/role/list';
UPDATE role_apis SET api_path = 'GET /api/v1/roles/{id}' WHERE api_path = 'get/api/v1/role/get';
UPDATE role_apis SET api_path = 'POST /api/v1/roles' WHERE api_path = 'post/api/v1/role/create';
UPDATE role_apis SET api_path = 'PUT /api/v1/roles/{id}' WHERE api_path = 'post/api/v1/role/update';
UPDATE role_apis SET api_path = 'DELETE /api/v1/roles/{id}' WHERE api_path = 'delete/api/v1/role/delete';
UPDATE role_apis SET api_path = 'GET /api/v1/roles/{id}/permissions' WHERE api_path = 'get/api/v1/role/authorized';
UPDATE role_apis SET api_path = 'PUT /api/v1/roles/{id}/permissions' WHERE api_path = 'post/api/v1/role/authorized';

-- 菜单管理
UPDATE role_apis SET api_path = 'GET /api/v1/menus' WHERE api_path = 'get/api/v1/menu/list';
UPDATE role_apis SET api_path = 'GET /api/v1/menus/{id}' WHERE api_path = 'get/api/v1/menu/get';
UPDATE role_apis SET api_path = 'POST /api/v1/menus' WHERE api_path = 'post/api/v1/menu/create';
UPDATE role_apis SET api_path = 'PUT /api/v1/menus/{id}' WHERE api_path = 'post/api/v1/menu/update';
UPDATE role_apis SET api_path = 'DELETE /api/v1/menus/{id}' WHERE api_path = 'delete/api/v1/menu/delete';

-- 部门管理
UPDATE role_apis SET api_path = 'GET /api/v1/departments' WHERE api_path = 'get/api/v1/dept/list';
UPDATE role_apis SET api_path = 'POST /api/v1/departments' WHERE api_path = 'post/api/v1/dept/create';
UPDATE role_apis SET api_path = 'PUT /api/v1/departments/{id}' WHERE api_path = 'post/api/v1/dept/update';
UPDATE role_apis SET api_path = 'DELETE /api/v1/departments/{id}' WHERE api_path = 'delete/api/v1/dept/delete';

-- API管理
UPDATE role_apis SET api_path = 'GET /api/v1/apis' WHERE api_path = 'get/api/v1/api/list';
UPDATE role_apis SET api_path = 'POST /api/v1/apis' WHERE api_path = 'post/api/v1/api/create';
UPDATE role_apis SET api_path = 'PUT /api/v1/apis/{id}' WHERE api_path = 'post/api/v1/api/update';
UPDATE role_apis SET api_path = 'DELETE /api/v1/apis/{id}' WHERE api_path = 'delete/api/v1/api/delete';
UPDATE role_apis SET api_path = 'POST /api/v1/apis/refresh' WHERE api_path = 'post/api/v1/api/refresh';

-- 设备管理
UPDATE role_apis SET api_path = 'GET /api/v1/devices' WHERE api_path = 'get/api/v1/device/list';
UPDATE role_apis SET api_path = 'POST /api/v1/devices' WHERE api_path = 'post/api/v1/device/create';
UPDATE role_apis SET api_path = 'PUT /api/v1/devices/{id}' WHERE api_path = 'put/api/v1/device/update';
UPDATE role_apis SET api_path = 'DELETE /api/v1/devices/{id}' WHERE api_path = 'delete/api/v1/device/delete';

-- 设备类型
UPDATE role_apis SET api_path = 'GET /api/v1/devices/types' WHERE api_path = 'get/api/v1/device/types';
UPDATE role_apis SET api_path = 'POST /api/v1/devices/types' WHERE api_path = 'post/api/v1/device/types';
UPDATE role_apis SET api_path = 'PUT /api/v1/devices/types/{id}' WHERE api_path = 'put/api/v1/device/types';
UPDATE role_apis SET api_path = 'DELETE /api/v1/devices/types/{id}' WHERE api_path = 'delete/api/v1/device/types';

-- 设备监控
UPDATE role_apis SET api_path = 'GET /api/v1/devices/{id}/data' WHERE api_path = 'get/api/v1/device/data';
UPDATE role_apis SET api_path = 'WebSocket /api/v1/devices/ws' WHERE api_path = 'ws/api/v1/device/ws';

-- 报警管理
UPDATE role_apis SET api_path = 'GET /api/v1/alarms' WHERE api_path = 'get/api/v1/alarm/list';

-- 2. 插入新的API权限 (AI监控模块)
INSERT INTO apis (path, method, description, group_name) VALUES
-- AI预测
('GET /api/v1/ai/predictions', 'GET', '查看预测列表', 'AI监控'),
('POST /api/v1/ai/predictions', 'POST', '开始预测', 'AI监控'),
('GET /api/v1/ai/predictions/{id}', 'GET', '获取预测结果', 'AI监控'),
('GET /api/v1/ai/predictions/{id}/export', 'GET', '导出预测报告', 'AI监控'),

-- AI模型
('GET /api/v1/ai/models', 'GET', '查看模型列表', 'AI监控'),
('POST /api/v1/ai/models', 'POST', '上传模型', 'AI监控'),
('PUT /api/v1/ai/models/{id}', 'PUT', '更新模型', 'AI监控'),
('DELETE /api/v1/ai/models/{id}', 'DELETE', '删除模型', 'AI监控'),

-- AI标注
('GET /api/v1/ai/annotations', 'GET', '查看标注项目', 'AI监控'),
('POST /api/v1/ai/annotations', 'POST', '创建标注项目', 'AI监控'),
('PUT /api/v1/ai/annotations/{id}', 'PUT', '更新标注', 'AI监控'),
('POST /api/v1/ai/annotations/{id}/import', 'POST', '导入数据', 'AI监控'),

-- AI健康评分
('GET /api/v1/ai/health-scores', 'GET', '查看健康评分', 'AI监控'),
('POST /api/v1/ai/health-scores', 'POST', '计算健康评分', 'AI监控'),
('GET /api/v1/ai/health-scores/export', 'GET', '导出健康报告', 'AI监控'),
('PUT /api/v1/ai/health-scores/config', 'PUT', '评分配置', 'AI监控'),

-- AI智能分析
('GET /api/v1/ai/analysis', 'GET', '查看分析列表', 'AI监控'),
('POST /api/v1/ai/analysis', 'POST', '开始分析', 'AI监控'),
('GET /api/v1/ai/analysis/{id}', 'GET', '获取分析结果', 'AI监控'),

-- 设备维护
('GET /api/v1/devices/{id}/maintenance', 'GET', '查看维护记录', '设备管理'),
('POST /api/v1/devices/{id}/maintenance', 'POST', '创建维护记录', '设备管理'),
('PUT /api/v1/devices/maintenance/{id}', 'PUT', '更新维护记录', '设备管理'),
('DELETE /api/v1/devices/maintenance/{id}', 'DELETE', '删除维护记录', '设备管理'),

-- 工艺管理
('GET /api/v1/devices/{id}/processes', 'GET', '查看工艺', '设备管理'),
('POST /api/v1/devices/{id}/processes', 'POST', '创建工艺', '设备管理'),
('PUT /api/v1/devices/processes/{id}', 'PUT', '更新工艺', '设备管理'),
('DELETE /api/v1/devices/processes/{id}', 'DELETE', '删除工艺', '设备管理'),

-- 报警管理扩展
('GET /api/v1/alarms/{id}', 'GET', '获取报警详情', '报警管理'),
('PUT /api/v1/alarms/{id}/handle', 'PUT', '处理报警', '报警管理'),
('PUT /api/v1/alarms/batch-handle', 'PUT', '批量处理报警', '报警管理'),

-- 统计分析
('GET /api/v1/statistics/online-rate', 'GET', '在线率统计', '统计分析'),
('GET /api/v1/statistics/weld-records', 'GET', '焊接记录', '统计分析'),
('GET /api/v1/statistics/weld-time', 'GET', '焊接时长统计', '统计分析'),
('GET /api/v1/statistics/welding-reports', 'GET', '焊接报告', '统计分析'),

-- 仪表板
('GET /api/v1/dashboard/overview', 'GET', '查看概览数据', '仪表板'),
('GET /api/v1/dashboard/device-stats', 'GET', '查看设备统计', '仪表板'),
('GET /api/v1/dashboard/alarm-stats', 'GET', '查看报警统计', '仪表板');

-- 3. 为超级管理员角色添加新权限
INSERT INTO role_apis (role_id, api_path)
SELECT r.id, a.path
FROM roles r, apis a
WHERE r.name = 'super_admin' 
AND a.path LIKE '/api/v1/ai/%'
AND NOT EXISTS (
    SELECT 1 FROM role_apis ra 
    WHERE ra.role_id = r.id AND ra.api_path = a.path
);

-- 4. 清理可能的重复权限
DELETE ra1 FROM role_apis ra1
INNER JOIN role_apis ra2 
WHERE ra1.id > ra2.id 
AND ra1.role_id = ra2.role_id 
AND ra1.api_path = ra2.api_path;

-- 5. 验证迁移结果
SELECT 
    '迁移完成统计' as info,
    COUNT(*) as total_permissions,
    COUNT(DISTINCT role_id) as roles_count
FROM role_apis;

SELECT 
    '新增API统计' as info,
    COUNT(*) as new_apis_count
FROM apis 
WHERE path LIKE '/api/v1/ai/%' 
   OR path LIKE '/api/v1/statistics/%'
   OR path LIKE '/api/v1/dashboard/%'
   OR path LIKE '/api/v1/devices/%/maintenance'
   OR path LIKE '/api/v1/devices/%/processes';
`

  fs.writeFileSync(scriptPath, scriptContent, 'utf8')
  log(`✅ 数据库迁移脚本已生成: ${scriptPath}`, 'green')
}

/**
 * 主函数
 */
function main() {
  log('🚀 开始生成API权限重构配置文件...', 'cyan')

  try {
    // 确保目录存在
    const utilsDir = path.join(projectRoot, 'src/utils')
    const examplesDir = path.join(projectRoot, 'src/examples')
    const scriptsDir = path.join(projectRoot, '../scripts')

    if (!fs.existsSync(utilsDir)) {
      fs.mkdirSync(utilsDir, { recursive: true })
    }
    if (!fs.existsSync(examplesDir)) {
      fs.mkdirSync(examplesDir, { recursive: true })
    }
    if (!fs.existsSync(scriptsDir)) {
      fs.mkdirSync(scriptsDir, { recursive: true })
    }

    // 生成配置文件
    generatePermissionConfig()
    generatePermissionTree()
    generateApiMigrationMap()
    generatePermissionButtonExamples()
    generateDatabaseMigrationScript()

    log('\n✅ 所有配置文件生成完成！', 'green')
    log('\n📋 生成的文件列表：', 'cyan')
    log('  - src/utils/permission-config.js (权限配置)', 'yellow')
    log('  - src/utils/permission-tree.js (权限树)', 'yellow')
    log('  - src/utils/api-migration-map.js (API迁移映射)', 'yellow')
    log('  - src/examples/PermissionButtonExamples.vue (使用示例)', 'yellow')
    log('  - ../scripts/migrate_permissions.sql (数据库迁移脚本)', 'yellow')

    log('\n🔧 下一步操作：', 'cyan')
    log('  1. 检查生成的配置文件', 'yellow')
    log('  2. 执行数据库迁移脚本', 'yellow')
    log('  3. 更新前端组件使用新的权限配置', 'yellow')
    log('  4. 测试权限功能', 'yellow')
  } catch (error) {
    log(`❌ 生成配置文件时出错: ${error.message}`, 'red')
    process.exit(1)
  }
}

// 如果直接运行此脚本
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
}

export {
  generatePermissionConfig,
  generatePermissionTree,
  generateApiMigrationMap,
  generatePermissionButtonExamples,
  generateDatabaseMigrationScript,
  API_REFACTOR_MAP,
  NEW_API_CONFIG,
  FRONTEND_PERMISSION_MAP,
}
