/**
 * @file 设备相关的辅助函数和常量
 */

// 设备类型映射
export const deviceTypeMap = {
  server: '焊接机器人',
  network: '焊接工作站',
  storage: '焊接控制器',
  security: '焊接监测设备',
  other: '其他设备',
  welding: '焊机', // 兼容
}

// 设备类型标签映射
export const deviceTypeTagMap = {
  server: 'info',
  network: 'success',
  storage: 'warning',
  security: 'error',
  other: 'default',
  welding: 'info',
}

// 设备状态映射 (用于标准化)
const chineseStatusMap = {
  焊接: 'welding',
  待机: 'standby',
  报警: 'fault',
  关机: 'inactive',
}

const englishStatusMap = {
  active: 'welding',
  inactive: 'inactive',
  maintenance: 'standby',
  fault: 'fault',
  welding: 'welding',
  standby: 'standby',
}

// 标准化后的状态映射
export const statusMap = {
  welding: { text: '焊接', tagType: 'success', className: 'welding' },
  standby: { text: '待机', tagType: 'warning', className: 'standby' },
  fault: { text: '报警', tagType: 'error', className: 'fault' },
  inactive: { text: '关机', tagType: 'default', className: 'inactive' },
}

// 状态选项 (用于筛选)
export const statusOptions = Object.entries(statusMap).map(([value, { text }]) => ({
  label: text,
  value,
}))

// 视图切换选项
export const viewOptions = [
  {
    value: 'card',
    label: '卡片视图',
    icon: 'material-symbols:grid-view',
  },
  {
    value: 'table',
    label: '表格视图',
    icon: 'material-symbols:table-rows',
  },
]

/**
 * 获取设备类型文本
 * @param {string} type - 设备类型代码
 * @returns {string}
 */
export function getDeviceTypeText(type) {
  return deviceTypeMap[type] || '未知'
}

/**
 * 获取设备类型标签类型
 * @param {string} type - 设备类型代码
 * @returns {string}
 */
export function getDeviceTypeTagType(type) {
  return deviceTypeTagMap[type] || 'default'
}

/**
 * 标准化设备状态值
 * @param {string|number} status - 原始状态
 * @returns {string} 标准化后的状态
 */
export function normalizeDeviceStatus(status) {
  if (status === null || status === undefined) return 'inactive'

  // 处理数字状态值
  if (typeof status === 'number') {
    switch (status) {
      case 1:
        return 'welding' // 运行中/焊接中
      case 0:
        return 'inactive' // 关机/离线
      case 2:
        return 'standby' // 待机
      case 3:
        return 'fault' // 故障/报警
      default:
        return 'inactive'
    }
  }

  const statusStr = String(status).trim()

  if (chineseStatusMap.hasOwnProperty(statusStr)) {
    return chineseStatusMap[statusStr]
  }

  const statusLower = statusStr.toLowerCase()
  return englishStatusMap[statusLower] || 'inactive'
}

/**
 * 获取状态文本
 * @param {string} status - 原始状态
 * @returns {string}
 */
export function getStatusText(status) {
  const normalized = normalizeDeviceStatus(status)
  return statusMap[normalized]?.text || status || '未知'
}

/**
 * 获取状态标签类型
 * @param {string} status - 原始状态
 * @returns {string}
 */
export function getStatusTagType(status) {
  const normalized = normalizeDeviceStatus(status)
  return statusMap[normalized]?.tagType || 'default'
}

/**
 * 获取设备卡片样式类
 * @param {string} status - 原始状态
 * @returns {object}
 */
export function getDeviceCardClass(status) {
  const normalized = normalizeDeviceStatus(status)
  const className = statusMap[normalized]?.className || 'inactive'
  return { [`device-card--${className}`]: true }
}

/**
 * 获取状态指示器样式类
 * @param {string} status - 原始状态
 * @returns {object}
 */
export function getStatusClass(status) {
  const normalized = normalizeDeviceStatus(status)
  const className = statusMap[normalized]?.className || 'inactive'
  return { [`status-indicator--${className}`]: true }
}
