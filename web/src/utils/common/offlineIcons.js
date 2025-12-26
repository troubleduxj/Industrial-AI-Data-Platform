// 离线图标映射，避免网络请求
const iconMap = {
  // Ant Design 图标
  'ant-design:appstore-outlined': '📱',
  'ant-design:bar-chart-outlined': '📊',
  'ant-design:bell-outlined': '🔔',
  'ant-design:dashboard-outlined': '📈',
  'ant-design:node-index-outlined': '🔗',
  'ant-design:robot-outlined': '🤖',
  'ant-design:setting-outlined': '⚙️',
  'ant-design:tool-outlined': '🔧',

  // MDI 图标
  'mdi:monitor-dashboard': '🖥️',
  'mdi:chart-line': '📈',
  'mdi:alert-circle': '⚠️',
  'mdi:cog': '⚙️',
  'mdi:brain': '🧠',
  'mdi:magnify': '🔍',

  // OUI 图标
  'oui:app-advanced-settings': '⚙️',

  // Outline 图标
  'outline:text-outline': '📝',
  outline: '📄',

  // Icon Park 图标

  // 默认图标
  default: '📄',
}

// 获取离线图标
export function getOfflineIcon(iconName) {
  return iconMap[iconName] || iconMap['default']
}

// 检查是否为支持的图标
export function isSupportedIcon(iconName) {
  return iconName in iconMap
}

// 获取所有支持的图标
export function getSupportedIcons() {
  return Object.keys(iconMap)
}
