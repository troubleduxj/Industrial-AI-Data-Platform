/**
 * 权限迁移工具
 * 用于分析和迁移现有组件的权限控制
 */

// 按钮权限映射配置
export const BUTTON_PERMISSION_MAP = {
  // 系统管理相关
  system: {
    create: 'POST /api/v2/system-params',
    read: 'GET /api/v2/system-params',
    update: 'PUT /api/v2/system-params',
    delete: 'DELETE /api/v2/system-params',
    refresh: 'GET /api/v2/system-params',
    export: 'GET /api/v2/system-params/export',
  },

  // 用户管理相关
  user: {
    create: 'POST /api/v2/users',
    read: 'GET /api/v2/users',
    update: 'PUT /api/v2/users',
    delete: 'DELETE /api/v2/users',
    refresh: 'GET /api/v2/users',
    export: 'GET /api/v2/users/export',
  },

  // 角色管理相关
  role: {
    create: 'POST /api/v2/roles',
    read: 'GET /api/v2/roles',
    update: 'PUT /api/v2/roles',
    delete: 'DELETE /api/v2/roles',
    refresh: 'GET /api/v2/roles',
    assign: 'PUT /api/v2/roles/assign',
  },

  // 设备管理相关
  device: {
    create: 'POST /api/v1/devices',
    read: 'GET /api/v1/devices',
    update: 'PUT /api/v1/devices',
    delete: 'DELETE /api/v1/devices',
    refresh: 'GET /api/v1/devices',
    control: 'POST /api/v1/devices/control',
    monitor: 'GET /api/v1/devices/monitor',
    export: 'GET /api/v1/devices/export',
  },

  // 报警管理相关
  alarm: {
    create: 'POST /api/v1/alarms',
    read: 'GET /api/v1/alarms',
    update: 'PUT /api/v1/alarms',
    delete: 'DELETE /api/v1/alarms',
    refresh: 'GET /api/v1/alarms',
    handle: 'PUT /api/v1/alarms/handle',
    export: 'GET /api/v1/alarms/export',
  },

  // AI监控相关
  'ai-monitor': {
    create: 'POST /api/v1/ai-monitor',
    read: 'GET /api/v1/ai-monitor',
    update: 'PUT /api/v1/ai-monitor',
    delete: 'DELETE /api/v1/ai-monitor',
    refresh: 'GET /api/v1/ai-monitor',
    predict: 'POST /api/v1/ai-monitor/predict',
    train: 'POST /api/v1/ai-monitor/train',
    export: 'GET /api/v1/ai-monitor/export',
  },

  // 数据分析相关
  analysis: {
    create: 'POST /api/v1/analysis',
    read: 'GET /api/v1/analysis',
    update: 'PUT /api/v1/analysis',
    delete: 'DELETE /api/v1/analysis',
    refresh: 'GET /api/v1/analysis',
    export: 'GET /api/v1/analysis/export',
  },

  // 工作流相关
  workflow: {
    create: 'POST /api/v1/workflows',
    read: 'GET /api/v1/workflows',
    update: 'PUT /api/v1/workflows',
    delete: 'DELETE /api/v1/workflows',
    refresh: 'GET /api/v1/workflows',
    execute: 'POST /api/v1/workflows/execute',
    export: 'GET /api/v1/workflows/export',
  },
}

// 页面权限映射
export const PAGE_PERMISSION_MAP = {
  '/system': 'system:read',
  '/system/users': 'user:read',
  '/system/roles': 'role:read',
  '/device': 'device:read',
  '/device-monitor': 'device:monitor',
  '/alarm': 'alarm:read',
  '/ai-monitor': 'ai-monitor:read',
  '/dashboard': 'dashboard:read',
  '/statistics': 'analysis:read',
  '/workflow': 'workflow:read',
}

// 按钮类型识别
export const BUTTON_TYPE_PATTERNS = {
  create: /新建|创建|添加|新增|add|create|new/i,
  update: /编辑|修改|更新|保存|edit|update|save|modify/i,
  delete: /删除|移除|remove|delete/i,
  refresh: /刷新|重新加载|refresh|reload/i,
  export: /导出|下载|export|download/i,
  import: /导入|上传|import|upload/i,
  view: /查看|详情|view|detail/i,
  search: /搜索|查询|search|query/i,
  reset: /重置|清空|reset|clear/i,
  submit: /提交|确认|submit|confirm/i,
  cancel: /取消|关闭|cancel|close/i,
  execute: /执行|运行|启动|execute|run|start/i,
  stop: /停止|暂停|stop|pause/i,
  config: /配置|设置|config|setting/i,
  monitor: /监控|监视|monitor|watch/i,
  analyze: /分析|analyze/i,
  predict: /预测|predict/i,
  train: /训练|train/i,
}

/**
 * 根据按钮文本和上下文推断权限
 * @param {string} buttonText - 按钮文本
 * @param {string} pagePath - 页面路径
 * @param {string} context - 上下文信息
 * @returns {Object} 权限配置
 */
export function inferButtonPermission(buttonText, pagePath, context = '') {
  // 确定资源类型
  let resource = 'common'

  if (pagePath.includes('/system/user')) resource = 'user'
  else if (pagePath.includes('/system/role')) resource = 'role'
  else if (pagePath.includes('/system')) resource = 'system'
  else if (pagePath.includes('/device')) resource = 'device'
  else if (pagePath.includes('/alarm')) resource = 'alarm'
  else if (pagePath.includes('/ai-monitor')) resource = 'ai-monitor'
  else if (pagePath.includes('/analysis') || pagePath.includes('/statistics')) resource = 'analysis'
  else if (pagePath.includes('/workflow')) resource = 'workflow'

  // 确定操作类型
  let action = 'read'
  const text = (buttonText + ' ' + context).toLowerCase()

  for (const [actionType, pattern] of Object.entries(BUTTON_TYPE_PATTERNS)) {
    if (pattern.test(text)) {
      action = actionType
      break
    }
  }

  // 生成权限配置
  const permissionMap = BUTTON_PERMISSION_MAP[resource]
  if (permissionMap && permissionMap[action]) {
    return {
      type: 'api',
      permission: permissionMap[action],
      resource,
      action,
    }
  }

  // 默认权限配置
  return {
    type: 'button',
    resource,
    action,
    permission: `${resource}:${action}`,
  }
}

/**
 * 生成PermissionButton组件代码
 * @param {Object} buttonConfig - 按钮配置
 * @param {string} originalProps - 原始属性
 * @param {string} content - 按钮内容
 * @returns {string} 组件代码
 */
export function generatePermissionButton(buttonConfig, originalProps, content) {
  const { type, permission, resource, action } = buttonConfig

  let permissionProps = ''

  if (type === 'api') {
    permissionProps = `permission="${permission}"`
  } else if (type === 'button') {
    permissionProps = `resource="${resource}" action="${action}"`
  }

  // 保留原始属性，但移除@click（如果需要的话）
  const cleanProps = originalProps.replace(/@click="[^"]*"/g, '').trim()

  return `<PermissionButton ${permissionProps} ${cleanProps}>${content}</PermissionButton>`
}

/**
 * 分析需要权限控制的按钮
 * @param {string} vueFileContent - Vue文件内容
 * @param {string} filePath - 文件路径
 * @returns {Array} 需要修改的按钮列表
 */
export function analyzeButtonsForPermission(vueFileContent, filePath) {
  const buttons = []

  // 匹配n-button标签
  const buttonRegex = /<n-button([^>]*?)>([\s\S]*?)<\/n-button>/g
  let match

  while ((match = buttonRegex.exec(vueFileContent)) !== null) {
    const [fullMatch, props, content] = match
    const buttonText = content.replace(/<[^>]*>/g, '').trim()

    // 跳过一些不需要权限控制的按钮
    if (shouldSkipButton(buttonText, props, filePath)) {
      continue
    }

    const permissionConfig = inferButtonPermission(buttonText, filePath, props)

    buttons.push({
      original: fullMatch,
      props: props.trim(),
      content,
      text: buttonText,
      permissionConfig,
      startIndex: match.index,
      endIndex: match.index + fullMatch.length,
    })
  }

  return buttons
}

/**
 * 判断是否应该跳过某个按钮的权限控制
 * @param {string} buttonText - 按钮文本
 * @param {string} props - 按钮属性
 * @param {string} filePath - 文件路径
 * @returns {boolean} 是否跳过
 */
function shouldSkipButton(buttonText, props, filePath) {
  // 错误页面的按钮不需要权限控制
  if (filePath.includes('/error-page/')) {
    return true
  }

  // 登录页面的按钮不需要权限控制
  if (filePath.includes('/login/')) {
    return true
  }

  // 模态框的取消、关闭按钮通常不需要权限控制
  if (/取消|关闭|cancel|close/i.test(buttonText) && !props.includes('type="primary"')) {
    return true
  }

  // 纯展示性的按钮（如"更多"）
  if (/更多|more/i.test(buttonText) && props.includes('text')) {
    return true
  }

  return false
}

export default {
  BUTTON_PERMISSION_MAP,
  PAGE_PERMISSION_MAP,
  BUTTON_TYPE_PATTERNS,
  inferButtonPermission,
  generatePermissionButton,
  analyzeButtonsForPermission,
}
