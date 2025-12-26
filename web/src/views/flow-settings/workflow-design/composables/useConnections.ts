/**
 * 连接管理组合函数
 * Connections management composable
 */

import { ref, computed, reactive, type Ref, type ComputedRef } from 'vue'
import {
  validateConnection,
  isDuplicateConnection,
  detectCycle,
} from '../utils/connectionValidator.js'
import { calculateDistance, getConnectionPointPosition } from '../utils/pathCalculator.js'
import { ACTION_TYPES, getActionDescription } from '../utils/historyManager.js'

// ========== 类型定义 ==========

/** 连接配置 */
interface UseConnectionsOptions {
  nodes: Ref<any[]>
  connections: Ref<any[]>
  onConnectionAdd?: (connection: any) => void
  onConnectionRemove?: (connectionId: string) => void
  onSaveHistory?: (description: string) => void
}

/** 连接起始数据 */
interface ConnectionStartData {
  node: any
  type: string
  x: number
  y: number
}

/** 临时连接状态 */
interface TempConnection {
  show: boolean
  fromNode: any | null
  fromType: string
  toX: number
  toY: number
}

/** 磁性吸附目标 */
interface MagneticTarget {
  show: boolean
  x: number
  y: number
  nodeId: string
  type: string
}

/** 连接映射 */
interface ConnectionMap {
  inputs: any[]
  outputs: any[]
}

// ========== Composable ==========

export function useConnections({
  nodes,
  connections,
  onConnectionAdd,
  onConnectionRemove,
  onSaveHistory,
}: UseConnectionsOptions) {
  // 连接状态
  const isConnecting: Ref<boolean> = ref(false)
  const connectionStart: Ref<ConnectionStartData | null> = ref(null)
  const tempConnection = reactive<TempConnection>({
    show: false,
    fromNode: null,
    fromType: '',
    toX: 0,
    toY: 0,
  })

  // 磁性吸附状态
  const magneticTarget = reactive<MagneticTarget>({
    show: false,
    x: 0,
    y: 0,
    nodeId: '',
    type: '',
  })

  // 高亮状态
  const highlightedConnections: Ref<string[]> = ref([])
  const selectedConnections: Ref<string[]> = ref([])

  // 计算属性
  const connectionMap: ComputedRef<Map<string, any>> = computed(() => {
    const map = new Map<string, any>()
    connections.value.forEach((conn: any) => {
      map.set(conn.id, conn)
    })
    return map
  })

  const nodeConnectionsMap: ComputedRef<Map<string, ConnectionMap>> = computed(() => {
    const map = new Map<string, ConnectionMap>()

    nodes.value.forEach((node: any) => {
      map.set(node.id, {
        inputs: [],
        outputs: [],
      })
    })

    connections.value.forEach((conn: any) => {
      const fromNodeConns = map.get(conn.fromNodeId)
      const toNodeConns = map.get(conn.toNodeId)

      if (fromNodeConns) {
        fromNodeConns.outputs.push(conn)
      }

      if (toNodeConns) {
        toNodeConns.inputs.push(conn)
      }
    })

    return map
  })

  /**
   * 开始连接
   * @param data - 连接起始数据
   */
  function startConnection(data: ConnectionStartData): void {
    isConnecting.value = true
    connectionStart.value = data

    tempConnection.show = true
    tempConnection.fromNode = data.node
    tempConnection.fromType = data.type
    tempConnection.toX = data.x
    tempConnection.toY = data.y
  }

  /**
   * 更新临时连接
   * @param x - X坐标
   * @param y - Y坐标
   */
  function updateConnection(x: number, y: number): void {
    if (!isConnecting.value) return

    tempConnection.toX = x
    tempConnection.toY = y

    // 检查磁性吸附
    checkMagneticSnap(x, y)
  }

  /**
   * 完成连接
   * @param targetNode - 目标节点
   * @param targetType - 目标类型
   */
  function completeConnection(targetNode: any, targetType: string): void {
    if (!isConnecting.value || !connectionStart.value) return

    const sourceNode = connectionStart.value.node
    const sourceType = connectionStart.value.type

    // 验证连接
    const validation = validateConnection(
      sourceNode,
      targetNode,
      sourceType,
      targetType,
      connections.value
    )

    if (!validation.valid) {
      console.warn('Invalid connection:', validation.message)
      cancelConnection()
      return
    }

    // 检查重复连接
    if (
      isDuplicateConnection(connections.value, sourceNode.id, targetNode.id, sourceType, targetType)
    ) {
      console.warn('Duplicate connection')
      cancelConnection()
      return
    }

    // 检查循环
    if (detectCycle(connections.value, sourceNode.id, targetNode.id)) {
      console.warn('Connection would create a cycle')
      cancelConnection()
      return
    }

    // 创建新连接
    const newConnection = {
      id: `conn_${Date.now()}`,
      fromNodeId: sourceNode.id,
      toNodeId: targetNode.id,
      fromType: sourceType,
      toType: targetType,
      style: {},
    }

    onConnectionAdd?.(newConnection)
    onSaveHistory?.(
      getActionDescription(ACTION_TYPES.ADD_CONNECTION, {
        fromNode: sourceNode.name,
        toNode: targetNode.name,
      })
    )

    resetConnectionState()
  }

  /**
   * 取消连接
   */
  function cancelConnection(): void {
    resetConnectionState()
  }

  /**
   * 重置连接状态
   */
  function resetConnectionState(): void {
    isConnecting.value = false
    connectionStart.value = null
    tempConnection.show = false
    tempConnection.fromNode = null
    tempConnection.fromType = ''
    tempConnection.toX = 0
    tempConnection.toY = 0
    magneticTarget.show = false
  }

  /**
   * 检查磁性吸附
   * @param x - X坐标
   * @param y - Y坐标
   */
  function checkMagneticSnap(x: number, y: number): void {
    const snapThreshold = 30

    let closestNode: any = null
    let closestDistance = Infinity
    let closestType = ''

    nodes.value.forEach((node: any) => {
      if (connectionStart.value && node.id === connectionStart.value.node.id) return

      const position = getConnectionPointPosition(node, 'input')
      const distance = calculateDistance(x, y, position.x, position.y)

      if (distance < snapThreshold && distance < closestDistance) {
        closestNode = node
        closestDistance = distance
        closestType = 'input'
      }
    })

    if (closestNode) {
      const position = getConnectionPointPosition(closestNode, closestType)
      magneticTarget.show = true
      magneticTarget.x = position.x
      magneticTarget.y = position.y
      magneticTarget.nodeId = closestNode.id
      magneticTarget.type = closestType
    } else {
      magneticTarget.show = false
    }
  }

  /**
   * 删除连接
   * @param connectionId - 连接ID
   */
  function removeConnection(connectionId: string): void {
    const connection = connectionMap.value.get(connectionId)
    if (!connection) return

    onConnectionRemove?.(connectionId)
    onSaveHistory?.(getActionDescription(ACTION_TYPES.DELETE_CONNECTION))
  }

  /**
   * 删除多个连接
   * @param connectionIds - 连接ID列表
   */
  function removeConnections(connectionIds: string[]): void {
    connectionIds.forEach((id) => {
      onConnectionRemove?.(id)
    })

    onSaveHistory?.(`删除 ${connectionIds.length} 个连接`)
  }

  /**
   * 高亮连接
   * @param connectionIds - 连接ID列表
   */
  function highlightConnections(connectionIds: string[]): void {
    highlightedConnections.value = connectionIds
  }

  /**
   * 清除高亮
   */
  function clearHighlight(): void {
    highlightedConnections.value = []
  }

  /**
   * 选择连接
   * @param connectionIds - 连接ID列表
   */
  function selectConnections(connectionIds: string[]): void {
    selectedConnections.value = connectionIds
  }

  /**
   * 清除选择
   */
  function clearSelection(): void {
    selectedConnections.value = []
  }

  /**
   * 获取节点的所有连接
   * @param nodeId - 节点ID
   * @returns 连接映射
   */
  function getNodeConnections(nodeId: string): ConnectionMap {
    return (
      nodeConnectionsMap.value.get(nodeId) || {
        inputs: [],
        outputs: [],
      }
    )
  }

  /**
   * 检查连接是否高亮
   * @param connectionId - 连接ID
   * @returns 是否高亮
   */
  function isConnectionHighlighted(connectionId: string): boolean {
    return highlightedConnections.value.includes(connectionId)
  }

  /**
   * 检查连接是否被选中
   * @param connectionId - 连接ID
   * @returns 是否被选中
   */
  function isConnectionSelected(connectionId: string): boolean {
    return selectedConnections.value.includes(connectionId)
  }

  /**
   * 高亮与节点相关的所有连接
   * @param nodeId - 节点ID
   */
  function highlightNodeConnections(nodeId: string): void {
    const nodeConns = getNodeConnections(nodeId)
    const connectionIds = [...nodeConns.inputs, ...nodeConns.outputs].map((conn: any) => conn.id)
    highlightConnections(connectionIds)
  }

  /**
   * 删除与节点相关的所有连接
   * @param nodeId - 节点ID
   */
  function removeNodeConnections(nodeId: string): void {
    const nodeConns = getNodeConnections(nodeId)
    const connectionIds = [...nodeConns.inputs, ...nodeConns.outputs].map((conn: any) => conn.id)
    removeConnections(connectionIds)
  }

  /**
   * 查找两个节点之间的连接
   * @param fromNodeId - 起始节点ID
   * @param toNodeId - 目标节点ID
   * @returns 连接列表
   */
  function findConnectionsBetweenNodes(fromNodeId: string, toNodeId: string): any[] {
    return connections.value.filter(
      (conn: any) =>
        (conn.fromNodeId === fromNodeId && conn.toNodeId === toNodeId) ||
        (conn.fromNodeId === toNodeId && conn.toNodeId === fromNodeId)
    )
  }

  /**
   * 获取连接路径
   * @param connection - 连接对象
   * @returns SVG 路径字符串
   */
  function getConnectionPath(connection: any): string {
    const fromNode = nodes.value.find((n: any) => n.id === connection.fromNodeId)
    const toNode = nodes.value.find((n: any) => n.id === connection.toNodeId)

    if (!fromNode || !toNode) return ''

    const fromPos = getConnectionPointPosition(fromNode, connection.fromType)
    const toPos = getConnectionPointPosition(toNode, connection.toType)

    // 简单的贝塞尔曲线
    const dx = toPos.x - fromPos.x
    const controlPoint1X = fromPos.x + dx * 0.5
    const controlPoint1Y = fromPos.y
    const controlPoint2X = toPos.x - dx * 0.5
    const controlPoint2Y = toPos.y

    return `M ${fromPos.x} ${fromPos.y} C ${controlPoint1X} ${controlPoint1Y}, ${controlPoint2X} ${controlPoint2Y}, ${toPos.x} ${toPos.y}`
  }

  /**
   * 验证所有连接
   * @returns 验证结果
   */
  function validateAllConnections(): { valid: boolean; errors: string[] } {
    const errors: string[] = []

    connections.value.forEach((conn: any) => {
      const fromNode = nodes.value.find((n: any) => n.id === conn.fromNodeId)
      const toNode = nodes.value.find((n: any) => n.id === conn.toNodeId)

      if (!fromNode || !toNode) {
        errors.push(`Connection ${conn.id} has invalid node references`)
        return
      }

      const validation = validateConnection(
        fromNode,
        toNode,
        conn.fromType,
        conn.toType,
        connections.value
      )

      if (!validation.valid) {
        errors.push(`Connection ${conn.id}: ${validation.message}`)
      }
    })

    return {
      valid: errors.length === 0,
      errors,
    }
  }

  return {
    // 状态
    isConnecting: computed(() => isConnecting.value),
    tempConnection: computed(() => tempConnection),
    magneticTarget: computed(() => magneticTarget),
    highlightedConnections: computed(() => highlightedConnections.value),
    selectedConnections: computed(() => selectedConnections.value),

    // 计算属性
    connectionMap,
    nodeConnectionsMap,

    // 方法
    startConnection,
    updateConnection,
    completeConnection,
    cancelConnection,
    removeConnection,
    removeConnections,
    highlightConnections,
    clearHighlight,
    selectConnections,
    clearSelection,
    getNodeConnections,
    isConnectionHighlighted,
    isConnectionSelected,
    highlightNodeConnections,
    removeNodeConnections,
    findConnectionsBetweenNodes,
    getConnectionPath,
    validateAllConnections,
  }
}

// ========== 导出类型 ==========

export type {
  UseConnectionsOptions,
  ConnectionStartData,
  TempConnection,
  MagneticTarget,
  ConnectionMap,
}

