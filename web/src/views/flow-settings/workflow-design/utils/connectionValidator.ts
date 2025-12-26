/**
 * 连接验证工具函数
 * Connection validation utilities
 */

import { NODE_TYPES } from './nodeTypes.js'

// ========== 类型定义 ==========

/** 连接点类型 */
type ConnectionPointType = 'input' | 'output'

/** 验证结果 */
interface ValidationResult {
  valid: boolean
  reason: string
}

/** 工作流验证结果 */
interface WorkflowValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

/** 循环检测结果 */
interface CycleDetectionResult {
  hasCycle: boolean
  cyclePath: string[]
}

/** 节点（临时类型） */
interface WorkflowNode {
  id: string
  type: string
  name?: string
  [key: string]: any
}

/** 连接（临时类型） */
interface Connection {
  id?: string
  fromNodeId: string
  toNodeId: string
  fromType?: string
  toType?: string
  [key: string]: any
}

/** 连接详情 */
interface ConnectionDetails extends Connection {
  fromNode?: WorkflowNode
  toNode?: WorkflowNode
  fromNodeName: string
  toNodeName: string
}

/** 图结构 */
type Graph = Record<string, string[]>

// ========== 验证函数 ==========

/**
 * 验证连接是否有效
 * @param fromNode - 起始节点
 * @param toNode - 目标节点
 * @param fromType - 起始连接点类型 'input' | 'output'
 * @param toType - 目标连接点类型 'input' | 'output'
 * @returns 验证结果 {valid, reason}
 */
export function validateConnection(
  fromNode: WorkflowNode | null,
  toNode: WorkflowNode | null,
  fromType: ConnectionPointType,
  toType: ConnectionPointType
): ValidationResult {
  // 基本规则检查
  if (!fromNode || !toNode) {
    return { valid: false, reason: '节点不存在' }
  }

  if (fromNode.id === toNode.id) {
    return { valid: false, reason: '不能连接到自身' }
  }

  // 连接点类型检查
  if (fromType === toType) {
    return { valid: false, reason: '连接点类型不匹配' }
  }

  // 确保连接方向正确（output -> input）
  if (fromType === 'input' && toType === 'output') {
    return { valid: false, reason: '连接方向错误' }
  }

  // 节点类型兼容性检查
  const compatibilityResult = checkNodeTypeCompatibility(fromNode, toNode)
  if (!compatibilityResult.valid) {
    return compatibilityResult
  }

  // 特殊节点规则检查
  const specialRulesResult = checkSpecialNodeRules(fromNode, toNode, fromType, toType)
  if (!specialRulesResult.valid) {
    return specialRulesResult
  }

  return { valid: true, reason: '' }
}

/**
 * 检查节点类型兼容性
 * @param fromNode - 起始节点
 * @param toNode - 目标节点
 * @returns 检查结果 {valid, reason}
 */
function checkNodeTypeCompatibility(
  fromNode: WorkflowNode,
  toNode: WorkflowNode
): ValidationResult {
  const fromNodeType = NODE_TYPES[fromNode.type]
  const toNodeType = NODE_TYPES[toNode.type]

  if (!fromNodeType || !toNodeType) {
    return { valid: false, reason: '未知的节点类型' }
  }

  // 检查输出兼容性
  if (fromNodeType.outputs && toNodeType.inputs) {
    const hasCompatibleOutput = fromNodeType.outputs.some((output: any) =>
      toNodeType.inputs.some((input: any) => input.type === output.type)
    )

    if (!hasCompatibleOutput) {
      return { valid: false, reason: '节点类型不兼容' }
    }
  }

  return { valid: true, reason: '' }
}

/**
 * 检查特殊节点规则
 * @param fromNode - 起始节点
 * @param toNode - 目标节点
 * @param fromType - 起始连接点类型
 * @param toType - 目标连接点类型
 * @returns 检查结果 {valid, reason}
 */
function checkSpecialNodeRules(
  fromNode: WorkflowNode,
  toNode: WorkflowNode,
  fromType: ConnectionPointType,
  toType: ConnectionPointType
): ValidationResult {
  // 开始节点只能作为起点
  if (toNode.type === 'start') {
    return { valid: false, reason: '开始节点不能作为连接终点' }
  }

  // 结束节点只能作为终点
  if (fromNode.type === 'end') {
    return { valid: false, reason: '结束节点不能作为连接起点' }
  }

  // 条件节点的特殊规则
  if (fromNode.type === 'condition') {
    // 条件节点可以有多个输出，但需要标记分支
    // 这里可以添加更复杂的逻辑
  }

  return { valid: true, reason: '' }
}

// ========== 连接检查函数 ==========

/**
 * 检查是否存在重复连接
 * @param connections - 现有连接列表
 * @param fromNodeId - 起始节点ID
 * @param toNodeId - 目标节点ID
 * @param fromType - 起始连接点类型
 * @param toType - 目标连接点类型
 * @returns 是否存在重复连接
 */
export function isDuplicateConnection(
  connections: Connection[],
  fromNodeId: string,
  toNodeId: string,
  fromType?: string,
  toType?: string
): boolean {
  return connections.some(
    (conn) =>
      conn.fromNodeId === fromNodeId &&
      conn.toNodeId === toNodeId &&
      conn.fromType === fromType &&
      conn.toType === toType
  )
}

/**
 * 检查节点是否已有输入连接
 * @param connections - 现有连接列表
 * @param nodeId - 节点ID
 * @param inputType - 输入类型
 * @returns 是否已有输入连接
 */
export function hasInputConnection(
  connections: Connection[],
  nodeId: string,
  inputType: string = 'input'
): boolean {
  return connections.some((conn) => conn.toNodeId === nodeId && conn.toType === inputType)
}

/**
 * 获取节点的所有输入连接
 * @param connections - 连接列表
 * @param nodeId - 节点ID
 * @returns 输入连接列表
 */
export function getNodeInputConnections(connections: Connection[], nodeId: string): Connection[] {
  return connections.filter((conn) => conn.toNodeId === nodeId)
}

/**
 * 获取节点的所有输出连接
 * @param connections - 连接列表
 * @param nodeId - 节点ID
 * @returns 输出连接列表
 */
export function getNodeOutputConnections(connections: Connection[], nodeId: string): Connection[] {
  return connections.filter((conn) => conn.fromNodeId === nodeId)
}

// ========== 循环检测 ==========

/**
 * 检查工作流是否有循环依赖
 * @param nodes - 节点列表
 * @param connections - 连接列表
 * @returns 检查结果 {hasCycle, cyclePath}
 */
export function detectCycle(
  nodes: WorkflowNode[],
  connections: Connection[]
): CycleDetectionResult {
  const graph = buildGraph(nodes, connections)
  const visited = new Set<string>()
  const recursionStack = new Set<string>()
  const path: string[] = []

  for (const nodeId of Object.keys(graph)) {
    if (!visited.has(nodeId)) {
      const result = dfsDetectCycle(graph, nodeId, visited, recursionStack, path)
      if (result.hasCycle) {
        return result
      }
    }
  }

  return { hasCycle: false, cyclePath: [] }
}

/**
 * 构建图结构
 * @param nodes - 节点列表
 * @param connections - 连接列表
 * @returns 图结构
 */
function buildGraph(nodes: WorkflowNode[], connections: Connection[]): Graph {
  const graph: Graph = {}

  // 初始化所有节点
  nodes.forEach((node) => {
    graph[node.id] = []
  })

  // 添加连接
  connections.forEach((conn) => {
    if (graph[conn.fromNodeId]) {
      graph[conn.fromNodeId].push(conn.toNodeId)
    }
  })

  return graph
}

/**
 * 深度优先搜索检测循环
 * @param graph - 图结构
 * @param nodeId - 当前节点ID
 * @param visited - 已访问节点集合
 * @param recursionStack - 递归栈
 * @param path - 当前路径
 * @returns 检测结果
 */
function dfsDetectCycle(
  graph: Graph,
  nodeId: string,
  visited: Set<string>,
  recursionStack: Set<string>,
  path: string[]
): CycleDetectionResult {
  visited.add(nodeId)
  recursionStack.add(nodeId)
  path.push(nodeId)

  const neighbors = graph[nodeId] || []

  for (const neighbor of neighbors) {
    if (!visited.has(neighbor)) {
      const result = dfsDetectCycle(graph, neighbor, visited, recursionStack, path)
      if (result.hasCycle) {
        return result
      }
    } else if (recursionStack.has(neighbor)) {
      // 找到循环
      const cycleStart = path.indexOf(neighbor)
      const cyclePath = path.slice(cycleStart).concat([neighbor])
      return { hasCycle: true, cyclePath }
    }
  }

  recursionStack.delete(nodeId)
  path.pop()

  return { hasCycle: false, cyclePath: [] }
}

// ========== 工作流验证 ==========

/**
 * 验证工作流的完整性
 * @param nodes - 节点列表
 * @param connections - 连接列表
 * @returns 验证结果 {valid, errors, warnings}
 */
export function validateWorkflow(
  nodes: WorkflowNode[],
  connections: Connection[]
): WorkflowValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  // 检查是否有开始节点
  const startNodes = nodes.filter((node) => node.type === 'start')
  if (startNodes.length === 0) {
    errors.push('工作流必须包含至少一个开始节点')
  } else if (startNodes.length > 1) {
    warnings.push('工作流包含多个开始节点')
  }

  // 检查是否有结束节点
  const endNodes = nodes.filter((node) => node.type === 'end')
  if (endNodes.length === 0) {
    warnings.push('工作流建议包含至少一个结束节点')
  }

  // 检查孤立节点
  const isolatedNodes = nodes.filter((node) => {
    const hasInput = connections.some((conn) => conn.toNodeId === node.id)
    const hasOutput = connections.some((conn) => conn.fromNodeId === node.id)
    return !hasInput && !hasOutput && node.type !== 'start'
  })

  if (isolatedNodes.length > 0) {
    warnings.push(`发现 ${isolatedNodes.length} 个孤立节点`)
  }

  // 检查循环依赖
  const cycleResult = detectCycle(nodes, connections)
  if (cycleResult.hasCycle) {
    errors.push(`检测到循环依赖: ${cycleResult.cyclePath.join(' -> ')}`)
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  }
}

// ========== 连接详情 ==========

/**
 * 获取连接的详细信息
 * @param connection - 连接对象
 * @param nodes - 节点列表
 * @returns 连接详细信息
 */
export function getConnectionDetails(
  connection: Connection,
  nodes: WorkflowNode[]
): ConnectionDetails {
  const fromNode = nodes.find((node) => node.id === connection.fromNodeId)
  const toNode = nodes.find((node) => node.id === connection.toNodeId)

  return {
    ...connection,
    fromNode,
    toNode,
    fromNodeName: fromNode?.name || 'Unknown',
    toNodeName: toNode?.name || 'Unknown',
  }
}

// ========== 导出类型 ==========

export type {
  ConnectionPointType,
  ValidationResult,
  WorkflowValidationResult,
  CycleDetectionResult,
  WorkflowNode,
  Connection,
  ConnectionDetails,
  Graph,
}

