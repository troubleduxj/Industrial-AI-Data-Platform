/**
 * 工作流验证逻辑
 * Workflow validation composable
 */

import { ref, computed, watch, type Ref, type ComputedRef } from 'vue'
import { useWorkflowStore } from '../stores/workflowStore.js'

// ========== 类型定义 ==========

/** 验证问题 */
interface ValidationIssue {
  type: string
  message: string
  severity: 'error' | 'warning' | 'info'
  nodeId?: string | null
  nodeIds?: string[]
  connectionId?: string
}

/** 验证结果 */
interface ValidationResults {
  isValid: boolean
  errors: ValidationIssue[]
  warnings: ValidationIssue[]
  info: ValidationIssue[]
}

/** 验证规则 */
interface ValidationRules {
  requireStartNode: boolean
  requireEndNode: boolean
  allowMultipleStartNodes: boolean
  allowMultipleEndNodes: boolean
  allowDisconnectedNodes: boolean
  allowCyclicConnections: boolean
  maxNodeCount: number
  maxConnectionCount: number
  validateNodeProperties: boolean
  validateConnectionTypes: boolean
}

/** 验证摘要 */
interface ValidationSummary {
  total: number
  errors: number
  warnings: number
  info: number
  isValid: boolean
}

/** 边界范围 */
interface Bounds {
  width: number
  height: number
}

/** 位置坐标 */
interface Position {
  x: number
  y: number
}

// ========== Composable ==========

export function useWorkflowValidation() {
  const workflowStore = useWorkflowStore()

  // 验证状态
  const validationResults: Ref<ValidationResults> = ref({
    isValid: true,
    errors: [],
    warnings: [],
    info: [],
  })

  const isValidating: Ref<boolean> = ref(false)
  const lastValidationTime: Ref<Date | null> = ref(null)

  // 验证规则配置
  const validationRules: Ref<ValidationRules> = ref({
    requireStartNode: true,
    requireEndNode: true,
    allowMultipleStartNodes: false,
    allowMultipleEndNodes: true,
    allowDisconnectedNodes: false,
    allowCyclicConnections: false,
    maxNodeCount: 1000,
    maxConnectionCount: 2000,
    validateNodeProperties: true,
    validateConnectionTypes: true,
  })

  // 计算属性
  const hasErrors: ComputedRef<boolean> = computed(() => validationResults.value.errors.length > 0)
  const hasWarnings: ComputedRef<boolean> = computed(() => validationResults.value.warnings.length > 0)
  const hasIssues: ComputedRef<boolean> = computed(() => hasErrors.value || hasWarnings.value)

  const errorCount: ComputedRef<number> = computed(() => validationResults.value.errors.length)
  const warningCount: ComputedRef<number> = computed(() => validationResults.value.warnings.length)
  const infoCount: ComputedRef<number> = computed(() => validationResults.value.info.length)

  const validationSummary: ComputedRef<ValidationSummary> = computed(() => {
    const { errors, warnings, info } = validationResults.value
    return {
      total: errors.length + warnings.length + info.length,
      errors: errors.length,
      warnings: warnings.length,
      info: info.length,
      isValid: errors.length === 0,
    }
  })

  // 验证函数
  function validateWorkflow(nodes: any[] | null = null, connections: any[] | null = null): ValidationResults {
    isValidating.value = true

    const nodesToValidate = nodes || workflowStore.nodes
    const connectionsToValidate = connections || workflowStore.connections

    const results: ValidationResults = {
      isValid: true,
      errors: [],
      warnings: [],
      info: [],
    }

    try {
      // 基础结构验证
      validateBasicStructure(nodesToValidate, connectionsToValidate, results)

      // 节点验证
      validateNodes(nodesToValidate, results)

      // 连接验证
      validateConnections(nodesToValidate, connectionsToValidate, results)

      // 流程逻辑验证
      validateWorkflowLogic(nodesToValidate, connectionsToValidate, results)

      // 性能验证
      validatePerformance(nodesToValidate, connectionsToValidate, results)

      results.isValid = results.errors.length === 0
    } catch (error: any) {
      results.errors.push({
        type: 'system',
        message: `验证过程中发生错误: ${error.message}`,
        severity: 'error',
      })
      results.isValid = false
    }

    validationResults.value = results
    lastValidationTime.value = new Date()
    isValidating.value = false

    return results
  }

  // 基础结构验证
  function validateBasicStructure(nodes: any[], connections: any[], results: ValidationResults): void {
    // 检查是否有开始节点
    if (validationRules.value.requireStartNode) {
      const startNodes = nodes.filter((node: any) => node.type === 'start')
      if (startNodes.length === 0) {
        results.errors.push({
          type: 'structure',
          message: '工作流必须包含至少一个开始节点',
          severity: 'error',
          nodeId: null,
        })
      } else if (!validationRules.value.allowMultipleStartNodes && startNodes.length > 1) {
        results.warnings.push({
          type: 'structure',
          message: `发现多个开始节点 (${startNodes.length}个)，建议只使用一个`,
          severity: 'warning',
          nodeIds: startNodes.map((n: any) => n.id),
        })
      }
    }

    // 检查是否有结束节点
    if (validationRules.value.requireEndNode) {
      const endNodes = nodes.filter((node: any) => node.type === 'end')
      if (endNodes.length === 0) {
        results.errors.push({
          type: 'structure',
          message: '工作流必须包含至少一个结束节点',
          severity: 'error',
          nodeId: null,
        })
      }
    }

    // 检查节点数量限制
    if (nodes.length > validationRules.value.maxNodeCount) {
      results.warnings.push({
        type: 'performance',
        message: `节点数量 (${nodes.length}) 超过建议限制 (${validationRules.value.maxNodeCount})`,
        severity: 'warning',
      })
    }

    // 检查连接数量限制
    if (connections.length > validationRules.value.maxConnectionCount) {
      results.warnings.push({
        type: 'performance',
        message: `连接数量 (${connections.length}) 超过建议限制 (${validationRules.value.maxConnectionCount})`,
        severity: 'warning',
      })
    }
  }

  // 节点验证
  function validateNodes(nodes: any[], results: ValidationResults): void {
    const nodeIds = new Set<string>()

    nodes.forEach((node: any) => {
      // 检查节点ID唯一性
      if (nodeIds.has(node.id)) {
        results.errors.push({
          type: 'node',
          message: `节点ID重复: ${node.id}`,
          severity: 'error',
          nodeId: node.id,
        })
      }
      nodeIds.add(node.id)

      // 检查必需属性
      if (!node.name || node.name.trim() === '') {
        results.warnings.push({
          type: 'node',
          message: '节点名称为空',
          severity: 'warning',
          nodeId: node.id,
        })
      }

      // 检查节点位置
      if (typeof node.x !== 'number' || typeof node.y !== 'number') {
        results.errors.push({
          type: 'node',
          message: '节点位置信息无效',
          severity: 'error',
          nodeId: node.id,
        })
      }

      // 检查节点类型特定的属性
      validateNodeTypeSpecific(node, results)
    })
  }

  // 节点类型特定验证
  function validateNodeTypeSpecific(node: any, results: ValidationResults): void {
    switch (node.type) {
      case 'decision':
        if (!node.condition || !node.condition.field) {
          results.errors.push({
            type: 'node',
            message: '决策节点缺少条件配置',
            severity: 'error',
            nodeId: node.id,
          })
        }
        break

      case 'action':
        if (!node.actionType) {
          results.errors.push({
            type: 'node',
            message: '动作节点缺少动作类型配置',
            severity: 'error',
            nodeId: node.id,
          })
        }
        break

      case 'process':
        if (!node.processType) {
          results.warnings.push({
            type: 'node',
            message: '处理节点缺少处理类型配置',
            severity: 'warning',
            nodeId: node.id,
          })
        }
        break
    }
  }

  // 连接验证
  function validateConnections(nodes: any[], connections: any[], results: ValidationResults): void {
    const nodeMap = new Map<string, any>(nodes.map((node: any) => [node.id, node]))
    const connectionIds = new Set<string>()

    connections.forEach((connection: any) => {
      // 检查连接ID唯一性
      if (connectionIds.has(connection.id)) {
        results.errors.push({
          type: 'connection',
          message: `连接ID重复: ${connection.id}`,
          severity: 'error',
          connectionId: connection.id,
        })
      }
      connectionIds.add(connection.id)

      // 检查源节点存在性
      if (!nodeMap.has(connection.fromNodeId)) {
        results.errors.push({
          type: 'connection',
          message: `连接的源节点不存在: ${connection.fromNodeId}`,
          severity: 'error',
          connectionId: connection.id,
        })
      }

      // 检查目标节点存在性
      if (!nodeMap.has(connection.toNodeId)) {
        results.errors.push({
          type: 'connection',
          message: `连接的目标节点不存在: ${connection.toNodeId}`,
          severity: 'error',
          connectionId: connection.id,
        })
      }

      // 检查自连接
      if (connection.fromNodeId === connection.toNodeId) {
        results.warnings.push({
          type: 'connection',
          message: '节点不应连接到自身',
          severity: 'warning',
          connectionId: connection.id,
          nodeId: connection.fromNodeId,
        })
      }

      // 检查连接类型兼容性
      if (validationRules.value.validateConnectionTypes) {
        validateConnectionTypes(connection, nodeMap, results)
      }
    })
  }

  // 连接类型验证
  function validateConnectionTypes(connection: any, nodeMap: Map<string, any>, results: ValidationResults): void {
    const fromNode = nodeMap.get(connection.fromNodeId)
    const toNode = nodeMap.get(connection.toNodeId)

    if (!fromNode || !toNode) return

    // 检查输出端口类型
    const fromPortType = connection.fromPort || 'output'
    const toPortType = connection.toPort || 'input'

    // 开始节点只能有输出
    if (fromNode.type === 'start' && fromPortType !== 'output') {
      results.errors.push({
        type: 'connection',
        message: '开始节点只能作为连接的输出端',
        severity: 'error',
        connectionId: connection.id,
        nodeId: fromNode.id,
      })
    }

    // 结束节点只能有输入
    if (toNode.type === 'end' && toPortType !== 'input') {
      results.errors.push({
        type: 'connection',
        message: '结束节点只能作为连接的输入端',
        severity: 'error',
        connectionId: connection.id,
        nodeId: toNode.id,
      })
    }
  }

  // 工作流逻辑验证
  function validateWorkflowLogic(nodes: any[], connections: any[], results: ValidationResults): void {
    // 检查孤立节点
    if (!validationRules.value.allowDisconnectedNodes) {
      const connectedNodeIds = new Set<string>()
      connections.forEach((conn: any) => {
        connectedNodeIds.add(conn.fromNodeId)
        connectedNodeIds.add(conn.toNodeId)
      })

      const disconnectedNodes = nodes.filter(
        (node: any) => !connectedNodeIds.has(node.id) && node.type !== 'start'
      )

      disconnectedNodes.forEach((node: any) => {
        results.warnings.push({
          type: 'logic',
          message: '发现孤立节点（未连接到工作流）',
          severity: 'warning',
          nodeId: node.id,
        })
      })
    }

    // 检查循环连接
    if (!validationRules.value.allowCyclicConnections) {
      const cycles = detectCycles(nodes, connections)
      cycles.forEach((cycle: string[]) => {
        results.warnings.push({
          type: 'logic',
          message: `检测到循环连接: ${cycle.join(' -> ')}`,
          severity: 'warning',
          nodeIds: cycle,
        })
      })
    }

    // 检查可达性
    validateReachability(nodes, connections, results)
  }

  // 检测循环
  function detectCycles(nodes: any[], connections: any[]): string[][] {
    const graph = new Map<string, string[]>()
    const cycles: string[][] = []

    // 构建邻接表
    nodes.forEach((node: any) => graph.set(node.id, []))
    connections.forEach((conn: any) => {
      if (graph.has(conn.fromNodeId)) {
        graph.get(conn.fromNodeId)!.push(conn.toNodeId)
      }
    })

    // DFS检测循环
    const visited = new Set<string>()
    const recursionStack = new Set<string>()

    function dfs(nodeId: string, path: string[]): void {
      if (recursionStack.has(nodeId)) {
        const cycleStart = path.indexOf(nodeId)
        cycles.push(path.slice(cycleStart))
        return
      }

      if (visited.has(nodeId)) return

      visited.add(nodeId)
      recursionStack.add(nodeId)
      path.push(nodeId)

      const neighbors = graph.get(nodeId) || []
      neighbors.forEach((neighbor: string) => dfs(neighbor, [...path]))

      recursionStack.delete(nodeId)
    }

    nodes.forEach((node: any) => {
      if (!visited.has(node.id)) {
        dfs(node.id, [])
      }
    })

    return cycles
  }

  // 可达性验证
  function validateReachability(nodes: any[], connections: any[], results: ValidationResults): void {
    const startNodes = nodes.filter((node: any) => node.type === 'start')
    const endNodes = nodes.filter((node: any) => node.type === 'end')

    if (startNodes.length === 0 || endNodes.length === 0) return

    // 构建邻接表
    const graph = new Map<string, string[]>()
    nodes.forEach((node: any) => graph.set(node.id, []))
    connections.forEach((conn: any) => {
      if (graph.has(conn.fromNodeId)) {
        graph.get(conn.fromNodeId)!.push(conn.toNodeId)
      }
    })

    // 检查从开始节点到结束节点的可达性
    startNodes.forEach((startNode: any) => {
      const reachable = getReachableNodes(startNode.id, graph)
      const canReachEnd = endNodes.some((endNode: any) => reachable.has(endNode.id))

      if (!canReachEnd) {
        results.warnings.push({
          type: 'logic',
          message: `开始节点 "${startNode.name}" 无法到达任何结束节点`,
          severity: 'warning',
          nodeId: startNode.id,
        })
      }
    })
  }

  // 获取可达节点
  function getReachableNodes(startNodeId: string, graph: Map<string, string[]>): Set<string> {
    const reachable = new Set<string>()
    const queue: string[] = [startNodeId]

    while (queue.length > 0) {
      const nodeId = queue.shift()!
      if (reachable.has(nodeId)) continue

      reachable.add(nodeId)
      const neighbors = graph.get(nodeId) || []
      neighbors.forEach((neighbor: string) => {
        if (!reachable.has(neighbor)) {
          queue.push(neighbor)
        }
      })
    }

    return reachable
  }

  // 性能验证
  function validatePerformance(nodes: any[], connections: any[], results: ValidationResults): void {
    // 检查节点密度
    const nodeCount = nodes.length
    const connectionCount = connections.length

    if (nodeCount > 0) {
      const density = connectionCount / (nodeCount * (nodeCount - 1))
      if (density > 0.5) {
        results.info.push({
          type: 'performance',
          message: `工作流连接密度较高 (${(density * 100).toFixed(1)}%)，可能影响性能`,
          severity: 'info',
        })
      }
    }

    // 检查节点分布
    if (nodes.length > 0) {
      const positions: Position[] = nodes.map((node: any) => ({ x: node.x, y: node.y }))
      const bounds = calculateBounds(positions)

      if (bounds.width > 10000 || bounds.height > 10000) {
        results.info.push({
          type: 'performance',
          message: '工作流画布范围较大，建议优化节点布局',
          severity: 'info',
        })
      }
    }
  }

  // 计算边界
  function calculateBounds(positions: Position[]): Bounds {
    if (positions.length === 0) return { width: 0, height: 0 }

    let minX = Infinity,
      maxX = -Infinity
    let minY = Infinity,
      maxY = -Infinity

    positions.forEach((pos: Position) => {
      minX = Math.min(minX, pos.x)
      maxX = Math.max(maxX, pos.x)
      minY = Math.min(minY, pos.y)
      maxY = Math.max(maxY, pos.y)
    })

    return {
      width: maxX - minX,
      height: maxY - minY,
    }
  }

  // 实时验证
  function enableRealTimeValidation(): void {
    watch(
      () => [workflowStore.nodes, workflowStore.connections],
      () => {
        validateWorkflow()
      },
      { deep: true }
    )
  }

  // 获取特定类型的问题
  function getErrorsByType(type: string): ValidationIssue[] {
    return validationResults.value.errors.filter((error: ValidationIssue) => error.type === type)
  }

  function getWarningsByType(type: string): ValidationIssue[] {
    return validationResults.value.warnings.filter((warning: ValidationIssue) => warning.type === type)
  }

  function getIssuesByNode(nodeId: string): ValidationIssue[] {
    const issues: ValidationIssue[] = []

    validationResults.value.errors.forEach((error: ValidationIssue) => {
      if (error.nodeId === nodeId || (error.nodeIds && error.nodeIds.includes(nodeId))) {
        issues.push({ ...error, severity: 'error' })
      }
    })

    validationResults.value.warnings.forEach((warning: ValidationIssue) => {
      if (warning.nodeId === nodeId || (warning.nodeIds && warning.nodeIds.includes(nodeId))) {
        issues.push({ ...warning, severity: 'warning' })
      }
    })

    return issues
  }

  function getIssuesByConnection(connectionId: string): ValidationIssue[] {
    const issues: ValidationIssue[] = []

    validationResults.value.errors.forEach((error: ValidationIssue) => {
      if (error.connectionId === connectionId) {
        issues.push({ ...error, severity: 'error' })
      }
    })

    validationResults.value.warnings.forEach((warning: ValidationIssue) => {
      if (warning.connectionId === connectionId) {
        issues.push({ ...warning, severity: 'warning' })
      }
    })

    return issues
  }

  // 清除验证结果
  function clearValidationResults(): void {
    validationResults.value = {
      isValid: true,
      errors: [],
      warnings: [],
      info: [],
    }
  }

  // 更新验证规则
  function updateValidationRules(rules: Partial<ValidationRules>): void {
    validationRules.value = { ...validationRules.value, ...rules }
  }

  return {
    // 状态
    validationResults: computed(() => validationResults.value),
    isValidating: computed(() => isValidating.value),
    lastValidationTime: computed(() => lastValidationTime.value),
    validationRules: computed(() => validationRules.value),

    // 计算属性
    hasErrors,
    hasWarnings,
    hasIssues,
    errorCount,
    warningCount,
    infoCount,
    validationSummary,

    // 方法
    validateWorkflow,
    enableRealTimeValidation,
    getErrorsByType,
    getWarningsByType,
    getIssuesByNode,
    getIssuesByConnection,
    clearValidationResults,
    updateValidationRules,
  }
}

// ========== 导出类型 ==========

export type {
  ValidationIssue,
  ValidationResults,
  ValidationRules,
  ValidationSummary,
  Bounds,
  Position,
}

