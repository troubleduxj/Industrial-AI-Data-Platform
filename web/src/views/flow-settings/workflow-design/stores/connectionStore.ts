/**
 * 连接状态管理
 * Connection state management store
 */

import { defineStore } from 'pinia'
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { useWorkflowStore } from './workflowStore.js'
import { useHistoryStore } from './historyStore.js'
import { ACTION_TYPES } from '../utils/historyManager.js'
import { validateConnection, getConnectionRules } from '../utils/validationUtils.js'
import { calculateBezierPath, calculateStraightPath } from '../utils/pathCalculator.js'

// ========== 类型定义 ==========

/** 连接模式 */
type ConnectionMode = 'bezier' | 'straight' | 'orthogonal'

/** 动画类型 */
type AnimationType = 'flow' | 'pulse' | 'dash'

/** 连接模板 */
interface ConnectionTemplate {
  id: string
  name: string
  type?: string
  style?: ConnectionStyle
  createdAt?: number
  updatedAt?: number
}

/** 连接类型 */
interface ConnectionType {
  id: string
  name: string
  color: string
}

/** 连接样式 */
interface ConnectionStyle {
  stroke?: string
  strokeWidth?: number
  strokeDasharray?: string
  fill?: string
  [key: string]: any
}

/** 连接起点/终点 */
interface ConnectionPoint {
  nodeId: string
  port: string
  timestamp?: number
}

/** 位置信息 */
interface Position {
  x: number
  y: number
}

/** 端口位置 */
interface PortPosition {
  x?: number
  y?: number
}

/** 临时连接 */
interface TempConnection {
  id: string
  fromNodeId: string
  fromPort: string
  toNodeId: string | null
  toPort: string | null
  type: string
  style: ConnectionStyle
  endPosition?: Position
}

/** 连接数据（完整） */
interface Connection {
  id: string
  fromNodeId: string
  fromPort: string
  toNodeId: string
  toPort: string
  type?: string
  style?: ConnectionStyle
  [key: string]: any
}

/** 节点数据（临时） */
interface WorkflowNode {
  id: string
  x: number
  y: number
  width?: number
  height?: number
  ports?: Record<string, PortPosition>
  [key: string]: any
}

/** 连接验证结果 */
interface ConnectionValidation {
  isValid: boolean
  errors: string[]
  warnings?: string[]
}

/** 验证错误 */
interface ValidationError {
  type: string
  message: string
  timestamp: number
  connectionId?: string
}

/** 流动动画 */
interface FlowAnimation {
  type: string
  duration: number
  startTime: number
}

/** 连接路径 */
interface ConnectionPath {
  type: ConnectionMode
  points?: Position[]
  pathData: string
}

/** 连接规则 */
interface ConnectionRule {
  fromPort: string
  toNodeType: string
  toPort: string
}

/** 偏移量 */
interface Offset {
  x: number
  y: number
}

// ========== Store 定义 ==========

export const useConnectionStore = defineStore('workflowConnection', () => {
  // 连接相关状态
  const connectionTemplates: Ref<Map<string, ConnectionTemplate>> = ref(new Map())
  const connectionTypes: Ref<ConnectionType[]> = ref([])
  const connectionStyles: Ref<Map<string, ConnectionStyle>> = ref(new Map())
  const connectionIdCounter: Ref<number> = ref(1)

  // 连接操作状态
  const activeConnection: Ref<Connection | null> = ref(null)
  const tempConnection: Ref<TempConnection | null> = ref(null)
  const hoveredConnection: Ref<Connection | null> = ref(null)
  const editingConnection: Ref<Connection | null> = ref(null)

  // 连接创建状态
  const isConnecting: Ref<boolean> = ref(false)
  const connectionStart: Ref<ConnectionPoint | null> = ref(null)
  const connectionEnd: Ref<ConnectionPoint | null> = ref(null)
  const connectionMode: Ref<ConnectionMode> = ref('bezier')

  // 连接验证状态
  const connectionValidation: Ref<Map<string, ConnectionValidation>> = ref(new Map())
  const validationErrors: Ref<ValidationError[]> = ref([])

  // 连接动画状态
  const animatedConnections: Ref<Set<string>> = ref(new Set())
  const flowAnimations: Ref<Map<string, FlowAnimation>> = ref(new Map())

  // 获取其他store
  const workflowStore = useWorkflowStore()
  const historyStore = useHistoryStore()

  // 计算属性
  const connectionCount: ComputedRef<number> = computed(() => workflowStore.connections.length)

  const connectionsByType: ComputedRef<Map<string, Connection[]>> = computed(() => {
    const result = new Map<string, Connection[]>()
    workflowStore.connections.forEach((conn: Connection) => {
      const type = conn.type || 'default'
      if (!result.has(type)) {
        result.set(type, [])
      }
      result.get(type)!.push(conn)
    })
    return result
  })

  const invalidConnections: ComputedRef<Connection[]> = computed(() => {
    return workflowStore.connections.filter((conn: Connection) => {
      const validation = connectionValidation.value.get(conn.id)
      return validation && !validation.isValid
    })
  })

  const orphanConnections: ComputedRef<Connection[]> = computed(() => {
    return workflowStore.connections.filter((conn: Connection) => {
      const fromNode = workflowStore.getNodeById(conn.fromNodeId)
      const toNode = workflowStore.getNodeById(conn.toNodeId)
      return !fromNode || !toNode
    })
  })

  const connectionPaths: ComputedRef<Map<string, ConnectionPath>> = computed(() => {
    const paths = new Map<string, ConnectionPath>()
    workflowStore.connections.forEach((conn: Connection) => {
      const path = calculateConnectionPath(conn)
      if (path) {
        paths.set(conn.id, path)
      }
    })
    return paths
  })

  // 连接创建和管理
  function startConnection(fromNodeId: string, fromPort: string): void {
    if (isConnecting.value) {
      cancelConnection()
    }

    isConnecting.value = true
    connectionStart.value = {
      nodeId: fromNodeId,
      port: fromPort,
      timestamp: Date.now(),
    }

    // 创建临时连接
    tempConnection.value = {
      id: 'temp',
      fromNodeId,
      fromPort,
      toNodeId: null,
      toPort: null,
      type: 'temp',
      style: {
        stroke: '#3b82f6',
        strokeWidth: 2,
        strokeDasharray: '5,5',
      },
    }
  }

  function updateTempConnection(position: Position): void {
    if (!tempConnection.value) return

    tempConnection.value.endPosition = position
  }

  function completeConnection(toNodeId: string, toPort: string): Connection | null {
    if (!isConnecting.value || !connectionStart.value) {
      return null
    }

    const connectionData: Partial<Connection> = {
      fromNodeId: connectionStart.value.nodeId,
      fromPort: connectionStart.value.port,
      toNodeId,
      toPort,
      type: 'default',
    }

    // 验证连接
    const validation = validateConnection(
      connectionData,
      workflowStore.nodes,
      workflowStore.connections
    )

    if (!validation.isValid) {
      // 显示验证错误
      validationErrors.value.push({
        type: 'connection_validation',
        message: validation.errors.join(', '),
        timestamp: Date.now(),
      })
      cancelConnection()
      return null
    }

    // 创建连接
    const connection = workflowStore.addConnection(connectionData)

    // 保存验证结果
    connectionValidation.value.set(connection.id, validation)

    cancelConnection()
    return connection
  }

  function cancelConnection(): void {
    isConnecting.value = false
    connectionStart.value = null
    connectionEnd.value = null
    tempConnection.value = null
  }

  function duplicateConnection(connectionId: string, offset: Offset = { x: 50, y: 50 }): Connection | null {
    const originalConnection = workflowStore.connections.find((c: Connection) => c.id === connectionId)
    if (!originalConnection) return null

    // 查找目标节点的副本
    const fromNode = workflowStore.getNodeById(originalConnection.fromNodeId)
    const toNode = workflowStore.getNodeById(originalConnection.toNodeId)

    if (!fromNode || !toNode) return null

    // 这里需要根据实际需求实现连接复制逻辑
    // 通常连接复制会在节点复制时一起处理
    return null
  }

  function reconnectConnection(
    connectionId: string,
    newFromNodeId?: string,
    newFromPort?: string,
    newToNodeId?: string,
    newToPort?: string
  ): boolean {
    const connection = workflowStore.connections.find((c: Connection) => c.id === connectionId)
    if (!connection) return false

    const oldData = { ...connection }

    // 更新连接数据
    if (newFromNodeId !== undefined) connection.fromNodeId = newFromNodeId
    if (newFromPort !== undefined) connection.fromPort = newFromPort
    if (newToNodeId !== undefined) connection.toNodeId = newToNodeId
    if (newToPort !== undefined) connection.toPort = newToPort

    // 验证新连接
    const validation = validateConnection(
      connection,
      workflowStore.nodes,
      workflowStore.connections.filter((c: Connection) => c.id !== connectionId)
    )

    if (!validation.isValid) {
      // 恢复原数据
      Object.assign(connection, oldData)
      return false
    }

    // 保存验证结果
    connectionValidation.value.set(connectionId, validation)

    historyStore.saveToHistory(ACTION_TYPES.UPDATE_CONNECTION, {
      connectionId,
    })

    return true
  }

  // 连接验证
  function validateConnectionById(connectionId: string): ConnectionValidation | null {
    const connection = workflowStore.connections.find((c: Connection) => c.id === connectionId)
    if (!connection) return null

    const validation = validateConnection(
      connection,
      workflowStore.nodes,
      workflowStore.connections.filter((c: Connection) => c.id !== connectionId)
    )

    connectionValidation.value.set(connectionId, validation)

    if (!validation.isValid) {
      const existingError = validationErrors.value.find((err) => err.connectionId === connectionId)
      if (!existingError) {
        validationErrors.value.push({
          connectionId,
          type: 'connection_validation',
          message: validation.errors.join(', '),
          timestamp: Date.now(),
        })
      }
    } else {
      // 移除验证错误
      const errorIndex = validationErrors.value.findIndex(
        (err) => err.connectionId === connectionId
      )
      if (errorIndex > -1) {
        validationErrors.value.splice(errorIndex, 1)
      }
    }

    return validation
  }

  function validateAllConnections(): Map<string, ConnectionValidation> {
    const results = new Map<string, ConnectionValidation>()
    workflowStore.connections.forEach((conn: Connection) => {
      const validation = validateConnectionById(conn.id)
      if (validation) {
        results.set(conn.id, validation)
      }
    })
    return results
  }

  // 连接路径计算
  function calculateConnectionPath(connection: Connection): ConnectionPath | null {
    const fromNode = workflowStore.getNodeById(connection.fromNodeId)
    const toNode = workflowStore.getNodeById(connection.toNodeId)

    if (!fromNode || !toNode) return null

    // 计算连接点位置
    const fromPoint = getConnectionPoint(fromNode, connection.fromPort, 'output')
    const toPoint = getConnectionPoint(toNode, connection.toPort, 'input')

    if (!fromPoint || !toPoint) return null

    // 根据连接模式计算路径
    switch (connectionMode.value) {
      case 'straight':
        return calculateStraightPath(fromPoint, toPoint)
      case 'orthogonal':
        return calculateOrthogonalPath(fromPoint, toPoint)
      case 'bezier':
      default:
        return calculateBezierPath(fromPoint, toPoint)
    }
  }

  function getConnectionPoint(node: WorkflowNode, portName: string, portType: 'input' | 'output'): Position | null {
    const nodeWidth = node.width || 200
    const nodeHeight = node.height || 100

    // 默认连接点位置
    const defaultPoints: Record<'input' | 'output', Position> = {
      input: {
        x: node.x,
        y: node.y + nodeHeight / 2,
      },
      output: {
        x: node.x + nodeWidth,
        y: node.y + nodeHeight / 2,
      },
    }

    // 如果节点有自定义端口配置，使用自定义位置
    if (node.ports && node.ports[portName]) {
      const port = node.ports[portName]
      return {
        x: node.x + (port.x || 0),
        y: node.y + (port.y || 0),
      }
    }

    return defaultPoints[portType] || defaultPoints.output
  }

  function calculateOrthogonalPath(fromPoint: Position, toPoint: Position): ConnectionPath {
    const midX = (fromPoint.x + toPoint.x) / 2

    return {
      type: 'orthogonal',
      points: [fromPoint, { x: midX, y: fromPoint.y }, { x: midX, y: toPoint.y }, toPoint],
      pathData: `M ${fromPoint.x} ${fromPoint.y} L ${midX} ${fromPoint.y} L ${midX} ${toPoint.y} L ${toPoint.x} ${toPoint.y}`,
    }
  }

  // 连接样式管理
  function setConnectionStyle(connectionId: string, style: ConnectionStyle): void {
    connectionStyles.value.set(connectionId, style)
    const connection = workflowStore.connections.find((c: Connection) => c.id === connectionId)
    if (connection) {
      connection.style = { ...connection.style, ...style }
    }
  }

  function getConnectionStyle(connectionId: string): ConnectionStyle {
    return connectionStyles.value.get(connectionId) || {}
  }

  function applyConnectionTheme(themeName: string): void {
    const themeStyles: Record<string, ConnectionStyle> = {
      default: {
        stroke: '#6b7280',
        strokeWidth: 2,
        fill: 'none',
      },
      success: {
        stroke: '#10b981',
        strokeWidth: 2,
        fill: 'none',
      },
      error: {
        stroke: '#ef4444',
        strokeWidth: 2,
        fill: 'none',
      },
      warning: {
        stroke: '#f59e0b',
        strokeWidth: 2,
        fill: 'none',
      },
    }

    const style = themeStyles[themeName] || themeStyles.default

    workflowStore.connections.forEach((conn: Connection) => {
      setConnectionStyle(conn.id, style)
    })
  }

  // 连接动画
  function startConnectionAnimation(connectionId: string, animationType: AnimationType = 'flow'): void {
    animatedConnections.value.add(connectionId)

    if (animationType === 'flow') {
      const animation: FlowAnimation = {
        type: 'flow',
        duration: 2000,
        startTime: Date.now(),
      }
      flowAnimations.value.set(connectionId, animation)
    }
  }

  function stopConnectionAnimation(connectionId: string): void {
    animatedConnections.value.delete(connectionId)
    flowAnimations.value.delete(connectionId)
  }

  function stopAllAnimations(): void {
    animatedConnections.value.clear()
    flowAnimations.value.clear()
  }

  // 连接模板管理
  function addConnectionTemplate(template: ConnectionTemplate): void {
    if (!template.id || !template.name) {
      throw new Error('连接模板必须包含id和name字段')
    }

    connectionTemplates.value.set(template.id, {
      ...template,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    })
  }

  function removeConnectionTemplate(templateId: string): boolean {
    return connectionTemplates.value.delete(templateId)
  }

  function updateConnectionTemplate(templateId: string, updates: Partial<ConnectionTemplate>): boolean {
    const template = connectionTemplates.value.get(templateId)
    if (template) {
      connectionTemplates.value.set(templateId, {
        ...template,
        ...updates,
        updatedAt: Date.now(),
      })
      return true
    }
    return false
  }

  // 连接查找和过滤
  function findConnectionsByNode(nodeId: string): Connection[] {
    return workflowStore.connections.filter(
      (conn: Connection) => conn.fromNodeId === nodeId || conn.toNodeId === nodeId
    )
  }

  function findConnectionsByPort(nodeId: string, portName: string): Connection[] {
    return workflowStore.connections.filter(
      (conn: Connection) =>
        (conn.fromNodeId === nodeId && conn.fromPort === portName) ||
        (conn.toNodeId === nodeId && conn.toPort === portName)
    )
  }

  function findConnectionPath(fromNodeId: string, toNodeId: string): string[] | null {
    const visited = new Set<string>()
    const path: string[] = []

    function dfs(currentNodeId: string, targetNodeId: string): boolean {
      if (currentNodeId === targetNodeId) {
        return true
      }

      if (visited.has(currentNodeId)) {
        return false
      }

      visited.add(currentNodeId)
      path.push(currentNodeId)

      const outgoingConnections = workflowStore.connections.filter(
        (conn: Connection) => conn.fromNodeId === currentNodeId
      )

      for (const conn of outgoingConnections) {
        if (dfs(conn.toNodeId, targetNodeId)) {
          return true
        }
      }

      path.pop()
      return false
    }

    return dfs(fromNodeId, toNodeId) ? path : null
  }

  // 工具函数
  function generateConnectionId(): string {
    return `conn_${connectionIdCounter.value++}`
  }

  function getConnectionRulesForNode(nodeType: string): ConnectionRule[] {
    return getConnectionRules()[nodeType] || []
  }

  function isConnectionAllowed(fromNodeType: string, fromPort: string, toNodeType: string, toPort: string): boolean {
    const rules = getConnectionRulesForNode(fromNodeType)
    return rules.some(
      (rule) =>
        rule.fromPort === fromPort && rule.toNodeType === toNodeType && rule.toPort === toPort
    )
  }

  // 初始化
  function initializeConnectionStore(): void {
    // 初始化连接类型
    connectionTypes.value = [
      { id: 'default', name: '默认', color: '#6b7280' },
      { id: 'success', name: '成功', color: '#10b981' },
      { id: 'error', name: '错误', color: '#ef4444' },
      { id: 'warning', name: '警告', color: '#f59e0b' },
      { id: 'data', name: '数据', color: '#3b82f6' },
      { id: 'control', name: '控制', color: '#8b5cf6' },
    ]
  }

  // 清理函数
  function clearConnectionStore(): void {
    connectionTemplates.value.clear()
    connectionStyles.value.clear()
    connectionValidation.value.clear()
    validationErrors.value = []
    activeConnection.value = null
    tempConnection.value = null
    hoveredConnection.value = null
    editingConnection.value = null
    cancelConnection()
    stopAllAnimations()
  }

  return {
    // 状态
    connectionTemplates,
    connectionTypes,
    connectionStyles,
    connectionIdCounter,
    activeConnection,
    tempConnection,
    hoveredConnection,
    editingConnection,
    isConnecting,
    connectionStart,
    connectionEnd,
    connectionMode,
    connectionValidation,
    validationErrors,
    animatedConnections,
    flowAnimations,

    // 计算属性
    connectionCount,
    connectionsByType,
    invalidConnections,
    orphanConnections,
    connectionPaths,

    // 方法
    startConnection,
    updateTempConnection,
    completeConnection,
    cancelConnection,
    duplicateConnection,
    reconnectConnection,
    validateConnectionById,
    validateAllConnections,
    calculateConnectionPath,
    getConnectionPoint,
    setConnectionStyle,
    getConnectionStyle,
    applyConnectionTheme,
    startConnectionAnimation,
    stopConnectionAnimation,
    stopAllAnimations,
    addConnectionTemplate,
    removeConnectionTemplate,
    updateConnectionTemplate,
    findConnectionsByNode,
    findConnectionsByPort,
    findConnectionPath,
    generateConnectionId,
    getConnectionRulesForNode,
    isConnectionAllowed,
    initializeConnectionStore,
    clearConnectionStore,
  }
})

// ========== 导出类型 ==========

export type {
  ConnectionMode,
  AnimationType,
  ConnectionTemplate,
  ConnectionType,
  ConnectionStyle,
  ConnectionPoint,
  Position,
  TempConnection,
  Connection,
  WorkflowNode,
  ConnectionValidation,
  ValidationError,
  FlowAnimation,
  ConnectionPath,
  ConnectionRule,
  Offset,
}

