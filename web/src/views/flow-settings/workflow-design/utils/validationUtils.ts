/**
 * 连接验证工具函数
 * Connection validation utilities
 */

// ========== 类型定义 ==========

/** 节点类型 */
export type NodeTypeValue =
  | 'start'
  | 'end'
  | 'process'
  | 'decision'
  | 'parallel'
  | 'merge'
  | 'delay'
  | 'api'
  | 'database'
  | 'email'
  | 'webhook'
  | 'script'
  | 'condition'
  | 'loop'
  | 'switch'
  | 'transform'
  | 'filter'
  | 'aggregate'
  | 'split'
  | 'join'

/** 端口类型 */
export type PortTypeValue = 'input' | 'output' | 'success' | 'error' | 'true' | 'false' | 'default'

/** 数据类型 */
export type DataTypeValue = 'any' | 'string' | 'number' | 'boolean' | 'object' | 'array' | 'date' | 'file' | 'json' | 'xml' | 'csv'

/** 验证结果 */
interface ValidationResult {
  valid: boolean
  error?: string | null
  warning?: string | null
  suggestions?: string[]
  errors?: string[]
  warnings?: string[]
}

/** 转换规则 */
interface ConversionRule {
  possible: boolean
  message: string
  suggestions?: string[]
}

/** 连接规则 */
interface ConnectionRule {
  maxInputs: number // -1 表示无限制
  maxOutputs: number // -1 表示无限制
  allowedInputTypes?: string[]
  allowedOutputTypes?: string[]
  allowedSources?: string[]
  allowedTargets?: string[]
}

/** 节点 */
interface WorkflowNode {
  id: string
  type: string
  name?: string
  connections?: Connection[]
  ports?: Record<string, Port>
  position?: Position
  [key: string]: any
}

/** 连接 */
interface Connection {
  id?: string
  sourceNodeId: string
  sourcePort: string
  targetNodeId: string
  targetPort: string
  [key: string]: any
}

/** 端口 */
interface Port {
  dataType?: string
  [key: string]: any
}

/** 位置 */
interface Position {
  x: number
  y: number
}

/** 连接建议 */
interface ConnectionSuggestion {
  node: WorkflowNode
  confidence: number
  reason: string
}

// ========== 常量定义 ==========

/**
 * 节点类型定义
 */
export const NODE_TYPES = {
  START: 'start',
  END: 'end',
  PROCESS: 'process',
  DECISION: 'decision',
  PARALLEL: 'parallel',
  MERGE: 'merge',
  DELAY: 'delay',
  API: 'api',
  DATABASE: 'database',
  EMAIL: 'email',
  WEBHOOK: 'webhook',
  SCRIPT: 'script',
  CONDITION: 'condition',
  LOOP: 'loop',
  SWITCH: 'switch',
  TRANSFORM: 'transform',
  FILTER: 'filter',
  AGGREGATE: 'aggregate',
  SPLIT: 'split',
  JOIN: 'join',
} as const

/**
 * 端口类型定义
 */
export const PORT_TYPES = {
  INPUT: 'input',
  OUTPUT: 'output',
  SUCCESS: 'success',
  ERROR: 'error',
  TRUE: 'true',
  FALSE: 'false',
  DEFAULT: 'default',
} as const

/**
 * 数据类型定义
 */
export const DATA_TYPES = {
  ANY: 'any',
  STRING: 'string',
  NUMBER: 'number',
  BOOLEAN: 'boolean',
  OBJECT: 'object',
  ARRAY: 'array',
  DATE: 'date',
  FILE: 'file',
  JSON: 'json',
  XML: 'xml',
  CSV: 'csv',
} as const

// ========== 连接规则配置 ==========

/**
 * 节点连接规则配置
 */
export const CONNECTION_RULES: Record<string, ConnectionRule> = {
  [NODE_TYPES.START]: {
    maxInputs: 0,
    maxOutputs: 1,
    allowedOutputTypes: [PORT_TYPES.OUTPUT],
    allowedTargets: Object.values(NODE_TYPES).filter((type) => type !== NODE_TYPES.START),
  },
  [NODE_TYPES.END]: {
    maxInputs: -1, // 无限制
    maxOutputs: 0,
    allowedInputTypes: [PORT_TYPES.INPUT, PORT_TYPES.SUCCESS, PORT_TYPES.ERROR],
    allowedSources: Object.values(NODE_TYPES).filter((type) => type !== NODE_TYPES.END),
  },
  [NODE_TYPES.PROCESS]: {
    maxInputs: 1,
    maxOutputs: 2,
    allowedInputTypes: [PORT_TYPES.INPUT],
    allowedOutputTypes: [PORT_TYPES.SUCCESS, PORT_TYPES.ERROR],
    allowedTargets: Object.values(NODE_TYPES).filter((type) => type !== NODE_TYPES.START),
  },
  [NODE_TYPES.DECISION]: {
    maxInputs: 1,
    maxOutputs: 2,
    allowedInputTypes: [PORT_TYPES.INPUT],
    allowedOutputTypes: [PORT_TYPES.TRUE, PORT_TYPES.FALSE],
    allowedTargets: Object.values(NODE_TYPES).filter((type) => type !== NODE_TYPES.START),
  },
  [NODE_TYPES.PARALLEL]: {
    maxInputs: 1,
    maxOutputs: -1,
    allowedInputTypes: [PORT_TYPES.INPUT],
    allowedOutputTypes: [PORT_TYPES.OUTPUT],
    allowedTargets: Object.values(NODE_TYPES).filter((type) => type !== NODE_TYPES.START),
  },
  [NODE_TYPES.MERGE]: {
    maxInputs: -1,
    maxOutputs: 1,
    allowedInputTypes: [PORT_TYPES.INPUT],
    allowedOutputTypes: [PORT_TYPES.OUTPUT],
    allowedTargets: Object.values(NODE_TYPES).filter((type) => type !== NODE_TYPES.START),
  },
}

// ========== 验证函数 ==========

/**
 * 验证节点连接是否有效
 * @param sourceNode - 源节点
 * @param sourcePort - 源端口
 * @param targetNode - 目标节点
 * @param targetPort - 目标端口
 * @returns 验证结果 {valid, error, warning}
 */
export function validateConnection(
  sourceNode: any,
  sourcePort: any,
  targetNode: any,
  targetPort: any
): ValidationResult {
  const result: ValidationResult = {
    valid: true,
    error: null,
    warning: null,
    suggestions: [],
  }

  // 基础验证
  if (!sourceNode || !targetNode) {
    result.valid = false
    result.error = '源节点或目标节点不存在'
    return result
  }

  if (sourceNode.id === targetNode.id) {
    result.valid = false
    result.error = '不能连接到自身'
    return result
  }

  // 检查是否已存在连接
  if (isConnectionExists(sourceNode, sourcePort, targetNode, targetPort)) {
    result.valid = false
    result.error = '连接已存在'
    return result
  }

  // 检查节点类型兼容性
  const typeValidation = validateNodeTypeCompatibility(sourceNode, targetNode)
  if (!typeValidation.valid) {
    result.valid = false
    result.error = typeValidation.error || '节点类型不兼容'
    return result
  }

  // 检查端口类型兼容性
  const portValidation = validatePortCompatibility(sourceNode, sourcePort, targetNode, targetPort)
  if (!portValidation.valid) {
    result.valid = false
    result.error = portValidation.error || '端口类型不兼容'
    return result
  }

  // 检查连接数量限制
  const countValidation = validateConnectionCount(sourceNode, sourcePort, targetNode, targetPort)
  if (!countValidation.valid) {
    result.valid = false
    result.error = countValidation.error || '超出连接数量限制'
    return result
  }

  // 检查数据类型兼容性
  const dataTypeValidation = validateDataTypeCompatibility(
    sourceNode,
    sourcePort,
    targetNode,
    targetPort
  )
  if (!dataTypeValidation.valid) {
    result.warning = dataTypeValidation.warning || null
    result.suggestions = dataTypeValidation.suggestions || []
  }

  // 检查循环依赖
  const cycleValidation = validateNoCycles(sourceNode, targetNode)
  if (!cycleValidation.valid) {
    result.valid = false
    result.error = cycleValidation.error || '检测到循环依赖'
    return result
  }

  return result
}

/**
 * 检查连接是否已存在
 * @param sourceNode - 源节点
 * @param sourcePort - 源端口
 * @param targetNode - 目标节点
 * @param targetPort - 目标端口
 * @returns 是否已存在
 */
export function isConnectionExists(
  sourceNode: WorkflowNode,
  sourcePort: string,
  targetNode: WorkflowNode,
  targetPort: string
): boolean {
  if (!sourceNode.connections) return false

  return sourceNode.connections.some(
    (conn) =>
      conn.sourcePort === sourcePort &&
      conn.targetNodeId === targetNode.id &&
      conn.targetPort === targetPort
  )
}

/**
 * 验证节点类型兼容性
 * @param sourceNode - 源节点
 * @param targetNode - 目标节点
 * @returns 验证结果
 */
export function validateNodeTypeCompatibility(
  sourceNode: WorkflowNode,
  targetNode: WorkflowNode
): ValidationResult {
  const sourceType = sourceNode.type
  const targetType = targetNode.type
  const sourceRules = CONNECTION_RULES[sourceType]
  const targetRules = CONNECTION_RULES[targetType]

  if (!sourceRules || !targetRules) {
    return {
      valid: false,
      error: '未知的节点类型',
    }
  }

  // 检查源节点是否允许连接到目标节点类型
  if (sourceRules.allowedTargets && !sourceRules.allowedTargets.includes(targetType)) {
    return {
      valid: false,
      error: `${sourceType} 节点不能连接到 ${targetType} 节点`,
    }
  }

  // 检查目标节点是否允许从源节点类型连接
  if (targetRules.allowedSources && !targetRules.allowedSources.includes(sourceType)) {
    return {
      valid: false,
      error: `${targetType} 节点不能从 ${sourceType} 节点连接`,
    }
  }

  return { valid: true }
}

/**
 * 验证端口兼容性
 * @param sourceNode - 源节点
 * @param sourcePort - 源端口
 * @param targetNode - 目标节点
 * @param targetPort - 目标端口
 * @returns 验证结果
 */
export function validatePortCompatibility(
  sourceNode: WorkflowNode,
  sourcePort: string,
  targetNode: WorkflowNode,
  targetPort: string
): ValidationResult {
  const sourceRules = CONNECTION_RULES[sourceNode.type]
  const targetRules = CONNECTION_RULES[targetNode.type]

  // 检查源端口类型是否允许
  if (sourceRules.allowedOutputTypes && !sourceRules.allowedOutputTypes.includes(sourcePort)) {
    return {
      valid: false,
      error: `${sourceNode.type} 节点不支持 ${sourcePort} 输出端口`,
    }
  }

  // 检查目标端口类型是否允许
  if (targetRules.allowedInputTypes && !targetRules.allowedInputTypes.includes(targetPort)) {
    return {
      valid: false,
      error: `${targetNode.type} 节点不支持 ${targetPort} 输入端口`,
    }
  }

  // 检查端口类型匹配
  if (!isPortTypeCompatible(sourcePort, targetPort)) {
    return {
      valid: false,
      error: `端口类型不匹配：${sourcePort} -> ${targetPort}`,
    }
  }

  return { valid: true }
}

/**
 * 检查端口类型是否兼容
 * @param sourcePortType - 源端口类型
 * @param targetPortType - 目标端口类型
 * @returns 是否兼容
 */
export function isPortTypeCompatible(sourcePortType: string, targetPortType: string): boolean {
  // 基本匹配规则
  const compatibilityMap: Record<string, string[]> = {
    [PORT_TYPES.OUTPUT]: [PORT_TYPES.INPUT],
    [PORT_TYPES.SUCCESS]: [PORT_TYPES.INPUT],
    [PORT_TYPES.ERROR]: [PORT_TYPES.INPUT],
    [PORT_TYPES.TRUE]: [PORT_TYPES.INPUT],
    [PORT_TYPES.FALSE]: [PORT_TYPES.INPUT],
    [PORT_TYPES.DEFAULT]: [PORT_TYPES.INPUT],
  }

  const allowedTargets = compatibilityMap[sourcePortType]
  return allowedTargets ? allowedTargets.includes(targetPortType) : false
}

/**
 * 验证连接数量限制
 * @param sourceNode - 源节点
 * @param sourcePort - 源端口
 * @param targetNode - 目标节点
 * @param targetPort - 目标端口
 * @returns 验证结果
 */
export function validateConnectionCount(
  sourceNode: WorkflowNode,
  sourcePort: string,
  targetNode: WorkflowNode,
  targetPort: string
): ValidationResult {
  const sourceRules = CONNECTION_RULES[sourceNode.type]
  const targetRules = CONNECTION_RULES[targetNode.type]

  // 检查源节点输出连接数量
  if (sourceRules.maxOutputs !== -1) {
    const currentOutputs = getNodeOutputConnections(sourceNode).length
    if (currentOutputs >= sourceRules.maxOutputs) {
      return {
        valid: false,
        error: `${sourceNode.type} 节点最多只能有 ${sourceRules.maxOutputs} 个输出连接`,
      }
    }
  }

  // 检查目标节点输入连接数量
  if (targetRules.maxInputs !== -1) {
    const currentInputs = getNodeInputConnections(targetNode).length
    if (currentInputs >= targetRules.maxInputs) {
      return {
        valid: false,
        error: `${targetNode.type} 节点最多只能有 ${targetRules.maxInputs} 个输入连接`,
      }
    }
  }

  return { valid: true }
}

/**
 * 验证数据类型兼容性
 * @param sourceNode - 源节点
 * @param sourcePort - 源端口
 * @param targetNode - 目标节点
 * @param targetPort - 目标端口
 * @returns 验证结果
 */
export function validateDataTypeCompatibility(
  sourceNode: WorkflowNode,
  sourcePort: string,
  targetNode: WorkflowNode,
  targetPort: string
): ValidationResult {
  const sourceDataType = getPortDataType(sourceNode, sourcePort)
  const targetDataType = getPortDataType(targetNode, targetPort)

  if (!sourceDataType || !targetDataType) {
    return { valid: true } // 如果无法确定数据类型，则跳过验证
  }

  if (sourceDataType === DATA_TYPES.ANY || targetDataType === DATA_TYPES.ANY) {
    return { valid: true } // ANY 类型兼容所有类型
  }

  if (sourceDataType === targetDataType) {
    return { valid: true } // 相同类型兼容
  }

  // 检查类型转换兼容性
  const conversionResult = checkTypeConversion(sourceDataType, targetDataType)
  if (conversionResult.possible) {
    return {
      valid: true,
      warning: `数据类型不匹配：${sourceDataType} -> ${targetDataType}，${conversionResult.message}`,
      suggestions: conversionResult.suggestions || [],
    }
  }

  return {
    valid: false,
    error: `数据类型不兼容：${sourceDataType} -> ${targetDataType}`,
  }
}

/**
 * 检查类型转换可能性
 * @param sourceType - 源数据类型
 * @param targetType - 目标数据类型
 * @returns 转换结果
 */
export function checkTypeConversion(sourceType: string, targetType: string): ConversionRule {
  const conversionRules: Record<string, Record<string, ConversionRule>> = {
    [DATA_TYPES.STRING]: {
      [DATA_TYPES.NUMBER]: { possible: true, message: '可以尝试解析为数字' },
      [DATA_TYPES.BOOLEAN]: { possible: true, message: '可以转换为布尔值' },
      [DATA_TYPES.DATE]: { possible: true, message: '可以尝试解析为日期' },
      [DATA_TYPES.JSON]: { possible: true, message: '可以尝试解析为JSON' },
    },
    [DATA_TYPES.NUMBER]: {
      [DATA_TYPES.STRING]: { possible: true, message: '可以转换为字符串' },
      [DATA_TYPES.BOOLEAN]: { possible: true, message: '可以转换为布尔值' },
    },
    [DATA_TYPES.BOOLEAN]: {
      [DATA_TYPES.STRING]: { possible: true, message: '可以转换为字符串' },
      [DATA_TYPES.NUMBER]: { possible: true, message: '可以转换为数字' },
    },
    [DATA_TYPES.OBJECT]: {
      [DATA_TYPES.JSON]: { possible: true, message: '可以序列化为JSON' },
      [DATA_TYPES.STRING]: { possible: true, message: '可以序列化为字符串' },
    },
    [DATA_TYPES.ARRAY]: {
      [DATA_TYPES.JSON]: { possible: true, message: '可以序列化为JSON' },
      [DATA_TYPES.STRING]: { possible: true, message: '可以序列化为字符串' },
      [DATA_TYPES.CSV]: { possible: true, message: '可以转换为CSV格式' },
    },
  }

  const rule = conversionRules[sourceType]?.[targetType]
  if (rule) {
    return {
      possible: rule.possible,
      message: rule.message,
      suggestions: [`添加 ${sourceType} 到 ${targetType} 的转换节点`],
    }
  }

  return {
    possible: false,
    message: '无法自动转换',
    suggestions: [],
  }
}

/**
 * 验证是否存在循环依赖
 * @param sourceNode - 源节点
 * @param targetNode - 目标节点
 * @param allNodes - 所有节点
 * @returns 验证结果
 */
export function validateNoCycles(
  sourceNode: WorkflowNode,
  targetNode: WorkflowNode,
  allNodes: WorkflowNode[] = []
): ValidationResult {
  // 使用深度优先搜索检测循环
  const visited = new Set<string>()
  const recursionStack = new Set<string>()

  function hasCycle(nodeId: string): boolean {
    if (recursionStack.has(nodeId)) {
      return true // 发现循环
    }
    if (visited.has(nodeId)) {
      return false // 已访问过，无循环
    }

    visited.add(nodeId)
    recursionStack.add(nodeId)

    // 获取当前节点的所有输出连接
    const node =
      allNodes.find((n) => n.id === nodeId) || (nodeId === sourceNode.id ? sourceNode : null)

    if (node && node.connections) {
      for (const connection of node.connections) {
        if (hasCycle(connection.targetNodeId)) {
          return true
        }
      }
    }

    // 如果这是我们要添加的新连接
    if (nodeId === sourceNode.id && targetNode) {
      if (hasCycle(targetNode.id)) {
        return true
      }
    }

    recursionStack.delete(nodeId)
    return false
  }

  if (hasCycle(sourceNode.id)) {
    return {
      valid: false,
      error: '此连接会创建循环依赖',
    }
  }

  return { valid: true }
}

/**
 * 获取节点的输出连接
 * @param node - 节点
 * @returns 输出连接数组
 */
export function getNodeOutputConnections(node: WorkflowNode): Connection[] {
  return node.connections || []
}

/**
 * 获取节点的输入连接
 * @param node - 节点
 * @param allConnections - 所有连接
 * @returns 输入连接数组
 */
export function getNodeInputConnections(
  node: WorkflowNode,
  allConnections: Connection[] = []
): Connection[] {
  return allConnections.filter((conn) => conn.targetNodeId === node.id)
}

/**
 * 获取端口的数据类型
 * @param node - 节点
 * @param portName - 端口名称
 * @returns 数据类型
 */
export function getPortDataType(node: WorkflowNode, portName: string): string {
  if (!node.ports || !node.ports[portName]) {
    return DATA_TYPES.ANY // 默认为任意类型
  }

  return node.ports[portName].dataType || DATA_TYPES.ANY
}

// ========== 工作流验证 ==========

/**
 * 验证工作流完整性
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @returns 验证结果
 */
export function validateWorkflowIntegrity(
  nodes: WorkflowNode[],
  connections: Connection[]
): ValidationResult {
  const result: ValidationResult = {
    valid: true,
    errors: [],
    warnings: [],
    suggestions: [],
  }

  // 检查是否有开始节点
  const startNodes = nodes.filter((node) => node.type === NODE_TYPES.START)
  if (startNodes.length === 0) {
    result.errors!.push('工作流必须包含至少一个开始节点')
    result.valid = false
  } else if (startNodes.length > 1) {
    result.warnings!.push('工作流包含多个开始节点，可能导致执行混乱')
  }

  // 检查是否有结束节点
  const endNodes = nodes.filter((node) => node.type === NODE_TYPES.END)
  if (endNodes.length === 0) {
    result.warnings!.push('工作流建议包含至少一个结束节点')
  }

  // 检查孤立节点
  const isolatedNodes = findIsolatedNodes(nodes, connections)
  if (isolatedNodes.length > 0) {
    result.warnings!.push(
      `发现 ${isolatedNodes.length} 个孤立节点：${isolatedNodes
        .map((n) => n.name || n.id)
        .join(', ')}`
    )
  }

  // 检查无法到达的节点
  const unreachableNodes = findUnreachableNodes(nodes, connections)
  if (unreachableNodes.length > 0) {
    result.warnings!.push(
      `发现 ${unreachableNodes.length} 个无法到达的节点：${unreachableNodes
        .map((n) => n.name || n.id)
        .join(', ')}`
    )
  }

  // 检查死路节点
  const deadEndNodes = findDeadEndNodes(nodes, connections)
  if (deadEndNodes.length > 0) {
    result.warnings!.push(
      `发现 ${deadEndNodes.length} 个死路节点：${deadEndNodes
        .map((n) => n.name || n.id)
        .join(', ')}`
    )
  }

  return result
}

/**
 * 查找孤立节点（没有任何连接的节点）
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @returns 孤立节点数组
 */
export function findIsolatedNodes(
  nodes: WorkflowNode[],
  connections: Connection[]
): WorkflowNode[] {
  return nodes.filter((node) => {
    const hasOutput = connections.some((conn) => conn.sourceNodeId === node.id)
    const hasInput = connections.some((conn) => conn.targetNodeId === node.id)
    return !hasOutput && !hasInput
  })
}

/**
 * 查找无法到达的节点（从开始节点无法到达的节点）
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @returns 无法到达的节点数组
 */
export function findUnreachableNodes(
  nodes: WorkflowNode[],
  connections: Connection[]
): WorkflowNode[] {
  const startNodes = nodes.filter((node) => node.type === NODE_TYPES.START)
  if (startNodes.length === 0) return []

  const reachable = new Set<string>()
  const queue: string[] = [...startNodes.map((node) => node.id)]

  while (queue.length > 0) {
    const nodeId = queue.shift()!
    if (reachable.has(nodeId)) continue

    reachable.add(nodeId)

    // 添加所有可达的目标节点
    const outgoingConnections = connections.filter((conn) => conn.sourceNodeId === nodeId)
    for (const conn of outgoingConnections) {
      if (!reachable.has(conn.targetNodeId)) {
        queue.push(conn.targetNodeId)
      }
    }
  }

  return nodes.filter((node) => !reachable.has(node.id))
}

/**
 * 查找死路节点（没有输出连接且不是结束节点的节点）
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @returns 死路节点数组
 */
export function findDeadEndNodes(
  nodes: WorkflowNode[],
  connections: Connection[]
): WorkflowNode[] {
  return nodes.filter((node) => {
    if (node.type === NODE_TYPES.END) return false

    const hasOutput = connections.some((conn) => conn.sourceNodeId === node.id)
    return !hasOutput
  })
}

// ========== 连接建议 ==========

/**
 * 获取节点的连接建议
 * @param node - 节点
 * @param availableNodes - 可用节点数组
 * @returns 建议连接的节点数组
 */
export function getConnectionSuggestions(
  node: WorkflowNode,
  availableNodes: WorkflowNode[]
): ConnectionSuggestion[] {
  const suggestions: ConnectionSuggestion[] = []
  const nodeRules = CONNECTION_RULES[node.type]

  if (!nodeRules || !nodeRules.allowedTargets) {
    return suggestions
  }

  for (const targetNode of availableNodes) {
    if (targetNode.id === node.id) continue

    if (nodeRules.allowedTargets.includes(targetNode.type)) {
      const validation = validateConnection(node, PORT_TYPES.OUTPUT, targetNode, PORT_TYPES.INPUT)
      if (validation.valid) {
        suggestions.push({
          node: targetNode,
          confidence: calculateConnectionConfidence(node, targetNode),
          reason: getConnectionReason(node, targetNode),
        })
      }
    }
  }

  // 按置信度排序
  return suggestions.sort((a, b) => b.confidence - a.confidence)
}

/**
 * 计算连接置信度
 * @param sourceNode - 源节点
 * @param targetNode - 目标节点
 * @returns 置信度 (0-1)
 */
export function calculateConnectionConfidence(
  sourceNode: WorkflowNode,
  targetNode: WorkflowNode
): number {
  let confidence = 0.5 // 基础置信度

  // 基于节点类型的置信度调整
  const typeBonus: Record<string, Record<string, number>> = {
    [NODE_TYPES.START]: { [NODE_TYPES.PROCESS]: 0.3, [NODE_TYPES.API]: 0.2 },
    [NODE_TYPES.PROCESS]: { [NODE_TYPES.END]: 0.3, [NODE_TYPES.DECISION]: 0.2 },
    [NODE_TYPES.DECISION]: { [NODE_TYPES.PROCESS]: 0.2, [NODE_TYPES.END]: 0.1 },
    [NODE_TYPES.API]: { [NODE_TYPES.TRANSFORM]: 0.3, [NODE_TYPES.PROCESS]: 0.2 },
  }

  const bonus = typeBonus[sourceNode.type]?.[targetNode.type] || 0
  confidence += bonus

  // 基于位置的置信度调整（相近的节点更可能连接）
  if (sourceNode.position && targetNode.position) {
    const distance = Math.sqrt(
      Math.pow(targetNode.position.x - sourceNode.position.x, 2) +
        Math.pow(targetNode.position.y - sourceNode.position.y, 2)
    )
    const proximityBonus = Math.max(0, 0.2 - distance / 1000) // 距离越近，奖励越高
    confidence += proximityBonus
  }

  return Math.min(1, Math.max(0, confidence))
}

/**
 * 获取连接原因
 * @param sourceNode - 源节点
 * @param targetNode - 目标节点
 * @returns 连接原因
 */
export function getConnectionReason(sourceNode: WorkflowNode, targetNode: WorkflowNode): string {
  const reasons: Record<string, string> = {
    [`${NODE_TYPES.START}-${NODE_TYPES.PROCESS}`]: '开始节点通常连接到处理节点',
    [`${NODE_TYPES.PROCESS}-${NODE_TYPES.END}`]: '处理节点可以连接到结束节点',
    [`${NODE_TYPES.PROCESS}-${NODE_TYPES.DECISION}`]: '处理后可能需要条件判断',
    [`${NODE_TYPES.DECISION}-${NODE_TYPES.PROCESS}`]: '条件判断后执行不同的处理',
    [`${NODE_TYPES.API}-${NODE_TYPES.TRANSFORM}`]: 'API调用后通常需要数据转换',
  }

  const key = `${sourceNode.type}-${targetNode.type}`
  return reasons[key] || '节点类型兼容'
}

// ========== 连接配置验证 ==========

/**
 * 验证连接配置
 * @param connectionConfig - 连接配置
 * @returns 验证结果
 */
export function validateConnectionConfig(connectionConfig: Connection | null): ValidationResult {
  const result: ValidationResult = {
    valid: true,
    errors: [],
    warnings: [],
  }

  if (!connectionConfig) {
    result.valid = false
    result.errors!.push('连接配置不能为空')
    return result
  }

  // 验证必需字段
  const requiredFields: Array<keyof Connection> = [
    'sourceNodeId',
    'sourcePort',
    'targetNodeId',
    'targetPort',
  ]
  for (const field of requiredFields) {
    if (!connectionConfig[field]) {
      result.valid = false
      result.errors!.push(`缺少必需字段：${field}`)
    }
  }

  // 验证ID格式
  if (connectionConfig.sourceNodeId === connectionConfig.targetNodeId) {
    result.valid = false
    result.errors!.push('源节点和目标节点不能相同')
  }

  return result
}

// ========== 导出函数的别名 (向后兼容) ==========

/**
 * 获取连接规则
 * @returns 连接规则对象
 */
export function getConnectionRules(): Record<string, ConnectionRule> {
  return CONNECTION_RULES
}

// ========== 导出类型 ==========

export type {
  NodeTypeValue,
  PortTypeValue,
  DataTypeValue,
  ValidationResult,
  ConversionRule,
  ConnectionRule,
  WorkflowNode,
  Connection,
  Port,
  Position,
  ConnectionSuggestion,
}

