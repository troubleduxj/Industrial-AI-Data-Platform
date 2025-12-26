/**
 * 节点类型定义和配置
 * Node types definition and configuration
 */

// ========== 类型定义 ==========

/** 节点类别 */
type NodeCategory = 'basic' | 'control' | 'integration' | 'device' | 'alarm' | 'notification'

/** 节点状态 */
type NodeStatus = 'idle' | 'running' | 'success' | 'error' | 'warning'

/** 节点类型字符串 */
type NodeType = 'start' | 'end' | 'process' | 'transform' | 'filter' | 'condition' | 'loop' | 'timer' | 'parallel' | 'merge' | 'delay' | 'api' | 'database' | 'metadata_analysis'

/** 位置信息 */
interface Position {
  x: number
  y: number
}

/** 节点定义 */
interface NodeDefinition {
  type: string
  label: string
  icon: string
  color: string
  description: string
  category: NodeCategory
}

/** 节点输入参数 */
interface NodeInput {
  name: string
  type: string
  required: boolean
}

/** 节点输出参数 */
interface NodeOutput {
  name: string
  type: string
}

/** 节点属性配置 */
interface NodePropertyConfig {
  label: string
  type: 'string' | 'number' | 'boolean' | 'select' | 'textarea'
  required: boolean
  description?: string
  options?: string[]
}

/** 节点属性集合 */
type NodeProperties = Record<string, NodePropertyConfig>

/** 节点类型配置 */
interface NodeTypeConfig {
  type: string
  name: string
  label: string
  icon: string
  color: string
  description: string
  category: NodeCategory
  tags: string[]
  inputs: NodeInput[]
  outputs: NodeOutput[]
  properties: NodeProperties
  configurable: boolean
  disabled: boolean
  defaultProperties: Record<string, any>
}

/** 节点状态配置 */
interface NodeStatusConfig {
  label: string
  color: string
  icon: string
}

/** 节点数据 */
interface WorkflowNode {
  id: string
  type: string
  label: string
  icon: string
  color: string
  x: number
  y: number
  description?: string
  enabled?: boolean
  status?: NodeStatus
  condition?: string
  conditionType?: string
  schedule?: string
  repeatCount?: number
  apiUrl?: string
  method?: string
  timeout?: number
  headers?: Record<string, string>
  dbOperation?: string
  sql?: string
  loopType?: string
  loopCount?: number
  delayTime?: number
  [key: string]: any
}

// ========== 节点类型定义 ==========

// 基础节点类型
export const basicNodes: NodeDefinition[] = [
  {
    type: 'start',
    label: '开始',
    icon: 'material-symbols:play-circle-outline',
    color: '#4caf50',
    description: '工作流开始节点',
    category: 'basic',
  },
  {
    type: 'end',
    label: '结束',
    icon: 'material-symbols:stop-circle-outline',
    color: '#f44336',
    description: '工作流结束节点',
    category: 'basic',
  },
  {
    type: 'process',
    label: '处理',
    icon: 'material-symbols:settings-outline',
    color: '#2196f3',
    description: '处理数据和业务逻辑',
    category: 'basic',
  },
  {
    type: 'transform',
    label: '转换',
    icon: 'material-symbols:transform',
    color: '#9c27b0',
    description: '转换数据格式',
    category: 'basic',
  },
  {
    type: 'filter',
    label: '过滤',
    icon: 'material-symbols:filter-alt-outline',
    color: '#ff9800',
    description: '过滤和筛选数据',
    category: 'basic',
  },
]

// 控制节点类型
export const controlNodes: NodeDefinition[] = [
  {
    type: 'condition',
    label: '条件判断',
    icon: 'material-symbols:fork-right',
    color: '#ff5722',
    description: '根据条件分支执行',
    category: 'control',
  },
  {
    type: 'loop',
    label: '循环',
    icon: 'material-symbols:loop',
    color: '#607d8b',
    description: '循环执行操作',
    category: 'control',
  },
  {
    type: 'timer',
    label: '定时器',
    icon: 'material-symbols:schedule',
    color: '#795548',
    description: '定时触发任务',
    category: 'control',
  },
  {
    type: 'parallel',
    label: '并行',
    icon: 'material-symbols:call-split',
    color: '#3f51b5',
    description: '并行处理多个任务',
    category: 'control',
  },
  {
    type: 'merge',
    label: '合并',
    icon: 'material-symbols:call-merge',
    color: '#009688',
    description: '合并多个数据源',
    category: 'control',
  },
  {
    type: 'delay',
    label: '延时',
    icon: 'material-symbols:hourglass-empty',
    color: '#ffc107',
    description: '延时等待执行',
    category: 'control',
  },
]

// 集成节点类型
export const integrationNodes: NodeDefinition[] = [
  {
    type: 'api',
    label: 'API调用',
    icon: 'material-symbols:api',
    color: '#e91e63',
    description: '调用外部API接口',
    category: 'integration',
  },
  {
    type: 'database',
    label: '数据库',
    icon: 'material-symbols:database',
    color: '#673ab7',
    description: '执行数据库操作',
    category: 'integration',
  },
  {
    type: 'script',
    label: '脚本执行',
    icon: 'material-symbols:code',
    color: '#00bcd4',
    description: '执行自定义脚本代码',
    category: 'integration',
  },
  {
    type: 'email',
    label: '邮件发送',
    icon: 'material-symbols:mail-outline',
    color: '#ff5722',
    description: '发送邮件通知',
    category: 'integration',
  },
  {
    type: 'webhook',
    label: 'Webhook',
    icon: 'material-symbols:webhook',
    color: '#795548',
    description: '调用Webhook接口',
    category: 'integration',
  },
  {
    type: 'metadata_analysis',
    label: '模型分析',
    icon: 'material-symbols:chart-data',
    color: '#673ab7',
    description: '执行元数据模型分析',
    category: 'integration',
  },
]

// 设备节点类型
export const deviceNodes: NodeDefinition[] = [
  {
    type: 'device_query',
    label: '设备查询',
    icon: 'material-symbols:search',
    color: '#2196f3',
    description: '查询设备信息和状态',
    category: 'device' as NodeCategory,
  },
  {
    type: 'device_control',
    label: '设备控制',
    icon: 'material-symbols:settings-remote',
    color: '#4caf50',
    description: '发送设备控制指令',
    category: 'device' as NodeCategory,
  },
  {
    type: 'device_data',
    label: '数据采集',
    icon: 'material-symbols:analytics',
    color: '#9c27b0',
    description: '采集设备实时数据',
    category: 'device' as NodeCategory,
  },
  {
    type: 'device_status',
    label: '状态检测',
    icon: 'material-symbols:monitor-heart',
    color: '#ff9800',
    description: '检测设备运行状态',
    category: 'device' as NodeCategory,
  },
]

// 报警节点类型
export const alarmNodes: NodeDefinition[] = [
  {
    type: 'alarm_trigger',
    label: '触发报警',
    icon: 'material-symbols:notification-important',
    color: '#f44336',
    description: '触发报警通知',
    category: 'alarm' as NodeCategory,
  },
  {
    type: 'alarm_check',
    label: '报警检测',
    icon: 'material-symbols:fact-check',
    color: '#ff5722',
    description: '检测是否满足报警条件',
    category: 'alarm' as NodeCategory,
  },
  {
    type: 'alarm_clear',
    label: '清除报警',
    icon: 'material-symbols:notifications-off',
    color: '#4caf50',
    description: '清除已有报警',
    category: 'alarm' as NodeCategory,
  },
]

// 通知节点类型
export const notificationNodes: NodeDefinition[] = [
  {
    type: 'notification',
    label: '站内通知',
    icon: 'material-symbols:notifications',
    color: '#2196f3',
    description: '发送站内消息通知',
    category: 'notification' as NodeCategory,
  },
  {
    type: 'sms',
    label: '短信通知',
    icon: 'material-symbols:sms',
    color: '#4caf50',
    description: '发送短信通知',
    category: 'notification' as NodeCategory,
  },
]

// 所有节点类型
export const allNodes: NodeDefinition[] = [
  ...basicNodes, 
  ...controlNodes, 
  ...integrationNodes,
  ...deviceNodes,
  ...alarmNodes,
  ...notificationNodes,
]

// NODE_TYPES 对象，以类型为键
export const NODE_TYPES: Record<string, NodeTypeConfig> = {}
allNodes.forEach((node) => {
  NODE_TYPES[node.type] = {
    type: node.type,
    name: node.label,
    label: node.label,
    icon: getNodeDisplayIcon(node.icon),
    color: node.color,
    description: node.description,
    category: node.category,
    tags: getNodeTags(node.category, node.type),
    inputs: getNodeInputs(node.type),
    outputs: getNodeOutputs(node.type),
    properties: getNodeProperties(node.type),
    configurable: true,
    disabled: false,
    defaultProperties: {},
  }
})

// ========== 辅助函数 ==========

// 获取节点显示图标（简化版）
function getNodeDisplayIcon(iconName: string): string {
  const iconMap: Record<string, string> = {
    'material-symbols:play-circle-outline': '▶️',
    'material-symbols:stop-circle-outline': '⏹️',
    'material-symbols:settings-outline': '⚙️',
    'material-symbols:transform': '🔄',
    'material-symbols:filter-alt-outline': '🔍',
    'material-symbols:fork-right': '🔀',
    'material-symbols:loop': '🔁',
    'material-symbols:schedule': '⏰',
    'material-symbols:call-split': '📡',
    'material-symbols:call-merge': '🔗',
    'material-symbols:hourglass-empty': '⏳',
    'material-symbols:api': '🌐',
    'material-symbols:database': '🗄️',
    'material-symbols:chart-data': '📈',
    // 新增节点图标
    'material-symbols:code': '💻',
    'material-symbols:mail-outline': '📧',
    'material-symbols:webhook': '🔗',
    'material-symbols:search': '🔍',
    'material-symbols:settings-remote': '🎮',
    'material-symbols:analytics': '📊',
    'material-symbols:monitor-heart': '💓',
    'material-symbols:notification-important': '🚨',
    'material-symbols:fact-check': '✅',
    'material-symbols:notifications-off': '🔕',
    'material-symbols:notifications': '🔔',
    'material-symbols:sms': '📱',
  }
  return iconMap[iconName] || '📦'
}

// 获取节点标签
function getNodeTags(category: NodeCategory, type: string): string[] {
  const categoryTags: Record<string, string[]> = {
    basic: ['基础', '核心'],
    control: ['控制', '流程'],
    integration: ['集成', '外部'],
    device: ['设备', 'IoT'],
    alarm: ['报警', '监控'],
    notification: ['通知', '消息'],
  }

  const typeTags: Record<string, string[]> = {
    start: ['入口'],
    end: ['出口'],
    condition: ['判断'],
    api: ['网络'],
    database: ['存储'],
    script: ['代码'],
    email: ['邮件'],
    device_query: ['查询'],
    device_control: ['控制'],
    alarm_trigger: ['触发'],
    notification: ['站内'],
    sms: ['短信'],
  }

  return [...(categoryTags[category] || []), ...(typeTags[type] || [])]
}

// 获取节点输入参数
function getNodeInputs(type: string): NodeInput[] {
  const inputsMap: Record<string, NodeInput[]> = {
    start: [],
    end: [{ name: 'input', type: 'any', required: true }],
    process: [{ name: 'data', type: 'object', required: true }],
    transform: [{ name: 'input', type: 'any', required: true }],
    filter: [{ name: 'data', type: 'array', required: true }],
    condition: [{ name: 'value', type: 'any', required: true }],
    loop: [{ name: 'items', type: 'array', required: true }],
    timer: [],
    parallel: [{ name: 'input', type: 'any', required: true }],
    merge: [
      { name: 'input1', type: 'any', required: true },
      { name: 'input2', type: 'any', required: true },
    ],
    delay: [{ name: 'input', type: 'any', required: true }],
    api: [{ name: 'params', type: 'object', required: false }],
    database: [{ name: 'query', type: 'string', required: true }],
    metadata_analysis: [
      { name: 'data', type: 'json', required: true },
      { name: 'device_id', type: 'string', required: true }
    ],
  }
  return inputsMap[type] || []
}

// 获取节点输出参数
function getNodeOutputs(type: string): NodeOutput[] {
  const outputsMap: Record<string, NodeOutput[]> = {
    start: [{ name: 'output', type: 'any' }],
    end: [],
    process: [{ name: 'result', type: 'object' }],
    transform: [{ name: 'output', type: 'any' }],
    filter: [{ name: 'filtered', type: 'array' }],
    condition: [
      { name: 'true', type: 'any' },
      { name: 'false', type: 'any' },
    ],
    loop: [{ name: 'output', type: 'array' }],
    timer: [{ name: 'trigger', type: 'event' }],
    parallel: [{ name: 'output', type: 'any' }],
    merge: [{ name: 'merged', type: 'any' }],
    delay: [{ name: 'output', type: 'any' }],
    api: [{ name: 'response', type: 'object' }],
    database: [{ name: 'result', type: 'array' }],
    metadata_analysis: [{ name: 'result', type: 'json' }],
  }
  return outputsMap[type] || []
}

// 获取节点属性配置
function getNodeProperties(type: string): NodeProperties {
  const propertiesMap: Record<string, NodeProperties> = {
    condition: {
      condition: {
        label: '条件表达式',
        type: 'string',
        required: true,
        description: '用于判断的条件表达式',
      },
      conditionType: {
        label: '条件类型',
        type: 'select',
        options: ['number', 'string', 'boolean'],
        required: true,
      },
    },
    timer: {
      schedule: {
        label: '调度表达式',
        type: 'string',
        required: true,
        description: 'Cron表达式或时间间隔',
      },
      repeatCount: {
        label: '重复次数',
        type: 'number',
        required: false,
        description: '0表示无限重复',
      },
    },
    api: {
      apiUrl: {
        label: 'API地址',
        type: 'string',
        required: true,
        description: '要调用的API接口地址',
      },
      method: {
        label: '请求方法',
        type: 'select',
        options: ['GET', 'POST', 'PUT', 'DELETE'],
        required: true,
      },
      timeout: {
        label: '超时时间',
        type: 'number',
        required: false,
        description: '请求超时时间（秒）',
      },
    },
    database: {
      dbOperation: {
        label: '数据库操作',
        type: 'select',
        options: ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
        required: true,
      },
      sql: { label: 'SQL语句', type: 'textarea', required: true, description: '要执行的SQL语句' },
    },
    metadata_analysis: {
      model_code: {
        label: '选择模型',
        type: 'select',
        options: ['API:/api/v2/metadata/models'], // Front-end should handle this special prefix to load from API
        required: true,
        description: '要执行的元数据模型',
      },
    },
    loop: {
      loopType: {
        label: '循环类型',
        type: 'select',
        options: ['count', 'condition'],
        required: true,
      },
      loopCount: { label: '循环次数', type: 'number', required: false },
    },
    delay: {
      delayTime: {
        label: '延时时间',
        type: 'number',
        required: true,
        description: '延时时间（秒）',
      },
    },
  }
  return propertiesMap[type] || {}
}

// ========== 公开API ==========

// 根据类型获取节点配置
export function getNodeConfig(type: string): NodeDefinition | undefined {
  return allNodes.find((node) => node.type === type)
}

// 根据分类获取节点
export function getNodesByCategory(category: NodeCategory): NodeDefinition[] {
  return allNodes.filter((node) => node.category === category)
}

// 节点默认属性
export const defaultNodeProps: Partial<WorkflowNode> = {
  // 通用属性
  description: '',
  enabled: true,
  status: 'idle',

  // 条件节点属性
  condition: '',
  conditionType: 'number',

  // 定时器属性
  schedule: '',
  repeatCount: 0,

  // API节点属性
  apiUrl: '',
  method: 'GET',
  timeout: 30,
  headers: {},

  // 数据库节点属性
  dbOperation: 'SELECT',
  sql: '',

  // 循环节点属性
  loopType: 'count',
  loopCount: 1,

  // 延时节点属性
  delayTime: 1,
}

// 创建新节点
export function createNode(type: string, position: Position | WorkflowNode = { x: 0, y: 0 }): WorkflowNode {
  const config = getNodeConfig(type)
  if (!config) {
    throw new Error(`Unknown node type: ${type}`)
  }

  // 支持传入完整的节点数据或仅位置
  const isFullNodeData = 'id' in position
  if (isFullNodeData) {
    // 如果传入完整节点数据，直接返回
    return position as WorkflowNode
  }

  return {
    id: `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type: config.type,
    label: config.label,
    icon: config.icon,
    color: config.color,
    x: (position as Position).x,
    y: (position as Position).y,
    ...defaultNodeProps,
  }
}

// 节点状态定义
export const nodeStatuses: Record<NodeStatus, NodeStatusConfig> = {
  idle: { label: '空闲', color: '#9e9e9e', icon: 'material-symbols:pause-circle-outline' },
  running: { label: '运行中', color: '#2196f3', icon: 'material-symbols:play-circle-outline' },
  success: { label: '成功', color: '#4caf50', icon: 'material-symbols:check-circle-outline' },
  error: { label: '错误', color: '#f44336', icon: 'material-symbols:error-outline' },
  warning: { label: '警告', color: '#ff9800', icon: 'material-symbols:warning-outline' },
}

// 获取节点状态配置
export function getNodeStatus(status: NodeStatus): NodeStatusConfig {
  return nodeStatuses[status] || nodeStatuses.idle
}

// 获取节点图标
export function getNodeIcon(type: string): string {
  const config = getNodeConfig(type)
  return config ? config.icon : 'material-symbols:help-outline'
}

// 获取节点类型名称
export function getNodeTypeName(type: string): string {
  const config = getNodeConfig(type)
  return config ? config.label : '未知节点'
}

// 获取节点类型描述
export function getNodeTypeDescription(type: string): string {
  const config = getNodeConfig(type)
  return config ? config.description : '未知节点类型'
}

// 验证节点数据
export function validateNodeData(node: WorkflowNode): { isValid: boolean; errors: string[] } {
  const errors: string[] = []

  if (!node.id) errors.push('节点缺少ID')
  if (!node.type) errors.push('节点缺少类型')
  
  const config = getNodeConfig(node.type)
  if (!config) {
    errors.push(`未知的节点类型: ${node.type}`)
    return { isValid: false, errors }
  }

  // 验证必需的属性
  const properties = getNodeProperties(node.type)
  Object.entries(properties).forEach(([key, prop]) => {
    if (prop.required && !node[key]) {
      errors.push(`节点缺少必需属性: ${prop.label}`)
    }
  })

  return {
    isValid: errors.length === 0,
    errors,
  }
}

// ========== 导出类型 ==========

export type {
  NodeCategory,
  NodeStatus,
  NodeType,
  Position,
  NodeDefinition,
  NodeInput,
  NodeOutput,
  NodePropertyConfig,
  NodeProperties,
  NodeTypeConfig,
  NodeStatusConfig,
  WorkflowNode,
}

