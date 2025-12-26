/**
 * 视图切换组件的预定义选项配置
 * 提供常用的视图模式选项，保持项目中的一致性
 */

// 基础视图模式：表格和卡片
export const TABLE_CARD_OPTIONS = [
  {
    value: 'table',
    label: '表格视图',
    icon: 'material-symbols:table-chart',
  },
  {
    value: 'card',
    label: '卡片视图',
    icon: 'material-symbols:grid-view',
  },
]

// 数据展示模式：图表和表格
export const CHART_TABLE_OPTIONS = [
  {
    value: 'chart',
    label: '图表视图',
    icon: 'material-symbols:bar-chart',
  },
  {
    value: 'table',
    label: '表格视图',
    icon: 'material-symbols:table-chart',
  },
]

// 设备监控模式：卡片、表格和列表
export const DEVICE_VIEW_OPTIONS = [
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
  {
    value: 'list',
    label: '列表视图',
    icon: 'material-symbols:list',
  },
]

// 统计数据模式：图表、表格和摘要
export const STATISTICS_VIEW_OPTIONS = [
  {
    value: 'chart',
    label: '图表视图',
    icon: 'material-symbols:bar-chart',
  },
  {
    value: 'table',
    label: '表格视图',
    icon: 'material-symbols:table-chart',
  },
  {
    value: 'summary',
    label: '摘要视图',
    icon: 'material-symbols:summarize',
  },
]

// 文件管理模式：网格、列表和详情
export const FILE_VIEW_OPTIONS = [
  {
    value: 'grid',
    label: '网格视图',
    icon: 'material-symbols:grid-view',
  },
  {
    value: 'list',
    label: '列表视图',
    icon: 'material-symbols:list',
  },
  {
    value: 'detail',
    label: '详情视图',
    icon: 'material-symbols:view-list',
  },
]

// 日历视图模式：月、周、日
export const CALENDAR_VIEW_OPTIONS = [
  {
    value: 'month',
    label: '月视图',
    icon: 'material-symbols:calendar-month',
  },
  {
    value: 'week',
    label: '周视图',
    icon: 'material-symbols:calendar-week',
  },
  {
    value: 'day',
    label: '日视图',
    icon: 'material-symbols:calendar-today',
  },
]

// 地图视图模式：地图和列表
export const MAP_VIEW_OPTIONS = [
  {
    value: 'map',
    label: '地图视图',
    icon: 'material-symbols:map',
  },
  {
    value: 'list',
    label: '列表视图',
    icon: 'material-symbols:list',
  },
]

/**
 * 根据页面类型获取对应的视图选项
 * @param {string} pageType - 页面类型
 * @returns {Array} 视图选项数组
 */
export function getViewOptionsByPageType(pageType) {
  const optionsMap = {
    'device-monitor': DEVICE_VIEW_OPTIONS,
    'device-management': TABLE_CARD_OPTIONS,
    statistics: CHART_TABLE_OPTIONS,
    'file-management': FILE_VIEW_OPTIONS,
    calendar: CALENDAR_VIEW_OPTIONS,
    map: MAP_VIEW_OPTIONS,
    default: TABLE_CARD_OPTIONS,
  }

  return optionsMap[pageType] || optionsMap.default
}

/**
 * 创建自定义视图选项
 * @param {Array} customOptions - 自定义选项配置
 * @returns {Array} 格式化的视图选项
 */
export function createCustomViewOptions(customOptions) {
  return customOptions.map((option) => ({
    value: option.value,
    label: option.label,
    icon: option.icon || 'material-symbols:view-module',
  }))
}

/**
 * 验证视图选项配置
 * @param {Array} options - 视图选项数组
 * @returns {boolean} 是否有效
 */
export function validateViewOptions(options) {
  if (!Array.isArray(options) || options.length === 0) {
    return false
  }

  return options.every(
    (option) =>
      option &&
      typeof option.value === 'string' &&
      typeof option.label === 'string' &&
      typeof option.icon === 'string'
  )
}

/**
 * 获取默认视图模式
 * @param {Array} options - 视图选项数组
 * @returns {string} 默认视图模式值
 */
export function getDefaultViewMode(options) {
  if (!validateViewOptions(options)) {
    return 'table'
  }

  return options[0].value
}
