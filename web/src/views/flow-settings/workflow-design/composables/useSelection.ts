/**
 * 选择管理组合函数
 * Selection management composable
 */

import { ref, computed, reactive, watch, type Ref, type ComputedRef } from 'vue'
import { useSelectionStore } from '../stores/selectionStore.js'
import { useWorkflowStore } from '../stores/workflowStore.js'
import { useCanvasStore } from '../stores/canvasStore.js'
import { useHistoryStore } from '../stores/historyStore.js'
import { ACTION_TYPES } from '../utils/historyManager.js'

// ========== 类型定义 ==========

/** 选择模式 */
type SelectionMode = 'replace' | 'add' | 'remove' | 'toggle'

/** 选择方向 */
type SelectionDirection = 'both' | 'outgoing' | 'incoming'

/** 选择操作类型 */
type SelectionOperationType = 'copy' | 'cut' | 'delete' | 'group' | 'align' | null

/** 点坐标 */
interface Point {
  x: number
  y: number
}

/** 矩形区域 */
interface Rectangle {
  x: number
  y: number
  width: number
  height: number
}

/** 选择边界 */
interface SelectionBounds extends Rectangle {
  centerX: number
  centerY: number
}

/** 选择框状态 */
interface SelectionBoxState {
  active: boolean
  startPoint: Point
  endPoint: Point
  rect: Rectangle
  visible: boolean
}

/** 多选状态 */
interface MultiSelectState {
  enabled: boolean
  anchor: string | null
  range: string[]
}

/** 选择历史项 */
interface SelectionHistoryItem {
  nodes: string[]
  connections: string[]
  timestamp: number
}

/** 选择历史 */
interface SelectionHistory {
  previous: SelectionHistoryItem[]
  current: SelectionHistoryItem
  maxHistory: number
}

/** 选择过滤器 */
interface SelectionFilter {
  nodeTypes: string[]
  connectionTypes: string[]
  status: string[]
  categories: string[]
}

/** 选择操作 */
interface SelectionOperation {
  type: SelectionOperationType
  pending: boolean
  data: any
}

/** 选择状态 */
interface SelectionState {
  mode: SelectionMode
  selectionBox: SelectionBoxState
  multiSelect: MultiSelectState
  history: SelectionHistory
  filter: SelectionFilter
  operation: SelectionOperation
}

// ========== Composable ==========

export function useSelection() {
  // 获取stores
  const selectionStore = useSelectionStore()
  const workflowStore = useWorkflowStore()
  const canvasStore = useCanvasStore()
  const historyStore = useHistoryStore()

  // 选择状态
  const selectionState = reactive<SelectionState>({
    // 选择模式
    mode: 'replace',

    // 选择框状态
    selectionBox: {
      active: false,
      startPoint: { x: 0, y: 0 },
      endPoint: { x: 0, y: 0 },
      rect: { x: 0, y: 0, width: 0, height: 0 },
      visible: false,
    },

    // 多选状态
    multiSelect: {
      enabled: false,
      anchor: null,
      range: [],
    },

    // 选择历史
    history: {
      previous: [],
      current: { nodes: [], connections: [], timestamp: 0 },
      maxHistory: 10,
    },

    // 选择过滤
    filter: {
      nodeTypes: [],
      connectionTypes: [],
      status: [],
      categories: [],
    },

    // 选择操作
    operation: {
      type: null,
      pending: false,
      data: null,
    },
  })

  // 计算属性
  const selectedNodes: ComputedRef<string[]> = computed(() => selectionStore.selectedNodes)
  const selectedConnections: ComputedRef<string[]> = computed(() => selectionStore.selectedConnections)
  const hasSelection: ComputedRef<boolean> = computed(
    () => selectedNodes.value.length > 0 || selectedConnections.value.length > 0
  )
  const selectionCount: ComputedRef<number> = computed(
    () => selectedNodes.value.length + selectedConnections.value.length
  )

  const selectedNodeObjects: ComputedRef<any[]> = computed(() => {
    return selectedNodes.value.map((id: string) => workflowStore.getNodeById(id)).filter(Boolean)
  })

  const selectedConnectionObjects: ComputedRef<any[]> = computed(() => {
    return selectedConnections.value
      .map((id: string) => workflowStore.getConnectionById(id))
      .filter(Boolean)
  })

  const selectionBounds: ComputedRef<SelectionBounds | null> = computed(() => {
    if (selectedNodeObjects.value.length === 0) return null

    let minX = Infinity,
      minY = Infinity
    let maxX = -Infinity,
      maxY = -Infinity

    selectedNodeObjects.value.forEach((node: any) => {
      const nodeWidth = node.width || 200
      const nodeHeight = node.height || 100

      minX = Math.min(minX, node.x)
      minY = Math.min(minY, node.y)
      maxX = Math.max(maxX, node.x + nodeWidth)
      maxY = Math.max(maxY, node.y + nodeHeight)
    })

    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY,
      centerX: (minX + maxX) / 2,
      centerY: (minY + maxY) / 2,
    }
  })

  const canSelectAll: ComputedRef<boolean> = computed(() => {
    const totalItems = workflowStore.nodes.length + workflowStore.connections.length
    return totalItems > selectionCount.value
  })

  const canInvertSelection: ComputedRef<boolean> = computed(() => {
    return workflowStore.nodes.length > 0 || workflowStore.connections.length > 0
  })

  // 基础选择操作
  function selectNode(nodeId: string, mode: SelectionMode = 'replace'): boolean {
    return selectNodes([nodeId], mode)
  }

  function selectNodes(nodeIds: string[], mode: SelectionMode = 'replace'): boolean {
    const validNodeIds = nodeIds.filter((id: string) => workflowStore.getNodeById(id))

    if (validNodeIds.length === 0) return false

    // 保存选择历史
    saveSelectionHistory()

    const success = selectionStore.selectNodes(validNodeIds, mode)

    if (success) {
      // 触发选择变化事件
      emitSelectionChange('nodes', validNodeIds, mode)
    }

    return success
  }

  function selectConnection(connectionId: string, mode: SelectionMode = 'replace'): boolean {
    return selectConnections([connectionId], mode)
  }

  function selectConnections(connectionIds: string[], mode: SelectionMode = 'replace'): boolean {
    const validConnectionIds = connectionIds.filter((id: string) => workflowStore.getConnectionById(id))

    if (validConnectionIds.length === 0) return false

    // 保存选择历史
    saveSelectionHistory()

    const success = selectionStore.selectConnections(validConnectionIds, mode)

    if (success) {
      // 触发选择变化事件
      emitSelectionChange('connections', validConnectionIds, mode)
    }

    return success
  }

  function selectAll(): boolean {
    const allNodeIds = workflowStore.nodes.map((node: any) => node.id)
    const allConnectionIds = workflowStore.connections.map((conn: any) => conn.id)

    // 保存选择历史
    saveSelectionHistory()

    const success = selectionStore.selectAll()

    if (success) {
      emitSelectionChange('all', [...allNodeIds, ...allConnectionIds], 'replace')
    }

    return success
  }

  function clearSelection(): boolean {
    if (!hasSelection.value) return false

    // 保存选择历史
    saveSelectionHistory()

    const success = selectionStore.clearSelection()

    if (success) {
      emitSelectionChange('clear', [], 'replace')
    }

    return success
  }

  function invertSelection(): boolean {
    const allNodeIds = workflowStore.nodes.map((node: any) => node.id)
    const allConnectionIds = workflowStore.connections.map((conn: any) => conn.id)

    const unselectedNodeIds = allNodeIds.filter((id: string) => !selectedNodes.value.includes(id))
    const unselectedConnectionIds = allConnectionIds.filter(
      (id: string) => !selectedConnections.value.includes(id)
    )

    // 保存选择历史
    saveSelectionHistory()

    const success =
      selectionStore.selectNodes(unselectedNodeIds, 'replace') &&
      selectionStore.selectConnections(unselectedConnectionIds, 'add')

    if (success) {
      emitSelectionChange('invert', [...unselectedNodeIds, ...unselectedConnectionIds], 'replace')
    }

    return success
  }

  // 高级选择操作
  function selectByType(type: string, mode: SelectionMode = 'replace'): boolean {
    let targetIds: string[] = []

    if (type.startsWith('node:')) {
      const nodeType = type.substring(5)
      targetIds = workflowStore.nodes
        .filter((node: any) => node.type === nodeType)
        .map((node: any) => node.id)
      return selectNodes(targetIds, mode)
    } else if (type.startsWith('connection:')) {
      const connectionType = type.substring(11)
      targetIds = workflowStore.connections
        .filter((conn: any) => conn.type === connectionType)
        .map((conn: any) => conn.id)
      return selectConnections(targetIds, mode)
    }

    return false
  }

  function selectByStatus(status: string, mode: SelectionMode = 'replace'): boolean {
    const nodeIds = workflowStore.nodes
      .filter((node: any) => node.status === status)
      .map((node: any) => node.id)

    return selectNodes(nodeIds, mode)
  }

  function selectByCategory(category: string, mode: SelectionMode = 'replace'): boolean {
    const nodeIds = workflowStore.nodes
      .filter((node: any) => node.category === category)
      .map((node: any) => node.id)

    return selectNodes(nodeIds, mode)
  }

  function selectInRect(rect: Rectangle, mode: SelectionMode = 'replace'): boolean {
    const nodesInRect = workflowStore.nodes.filter((node: any) => {
      const nodeRight = node.x + (node.width || 200)
      const nodeBottom = node.y + (node.height || 100)

      return !(
        node.x > rect.x + rect.width ||
        nodeRight < rect.x ||
        node.y > rect.y + rect.height ||
        nodeBottom < rect.y
      )
    })

    const nodeIds = nodesInRect.map((node: any) => node.id)
    return selectNodes(nodeIds, mode)
  }

  function selectConnected(
    nodeId: string,
    direction: SelectionDirection = 'both',
    mode: SelectionMode = 'add'
  ): boolean {
    const connectedNodeIds = new Set<string>()
    const connectionIds = new Set<string>()

    workflowStore.connections.forEach((conn: any) => {
      if (direction === 'both' || direction === 'outgoing') {
        if (conn.sourceNodeId === nodeId) {
          connectedNodeIds.add(conn.targetNodeId)
          connectionIds.add(conn.id)
        }
      }

      if (direction === 'both' || direction === 'incoming') {
        if (conn.targetNodeId === nodeId) {
          connectedNodeIds.add(conn.sourceNodeId)
          connectionIds.add(conn.id)
        }
      }
    })

    const success1 = selectNodes(Array.from(connectedNodeIds), mode)
    const success2 = selectConnections(Array.from(connectionIds), 'add')

    return success1 || success2
  }

  function selectPath(startNodeId: string, endNodeId: string, mode: SelectionMode = 'replace'): boolean {
    // 实现路径选择逻辑（简化版）
    const pathNodeIds = findPath(startNodeId, endNodeId)
    const pathConnectionIds = findPathConnections(pathNodeIds)

    const success1 = selectNodes(pathNodeIds, mode)
    const success2 = selectConnections(pathConnectionIds, 'add')

    return success1 || success2
  }

  // 选择框操作
  function startSelectionBox(startPoint: Point): void {
    selectionState.selectionBox.active = true
    selectionState.selectionBox.startPoint = startPoint
    selectionState.selectionBox.endPoint = startPoint
    selectionState.selectionBox.visible = true

    updateSelectionBoxRect()
  }

  function updateSelectionBox(endPoint: Point): void {
    if (!selectionState.selectionBox.active) return

    selectionState.selectionBox.endPoint = endPoint
    updateSelectionBoxRect()

    // 预览选择
    const rect = selectionState.selectionBox.rect
    const nodesInRect = workflowStore.nodes.filter((node: any) => {
      const nodeRight = node.x + (node.width || 200)
      const nodeBottom = node.y + (node.height || 100)

      return !(
        node.x > rect.x + rect.width ||
        nodeRight < rect.x ||
        node.y > rect.y + rect.height ||
        nodeBottom < rect.y
      )
    })

    // 显示预览选择
    selectionStore.previewSelection(nodesInRect.map((node: any) => node.id))
  }

  function endSelectionBox(mode: SelectionMode = 'replace'): boolean {
    if (!selectionState.selectionBox.active) return false

    const rect = selectionState.selectionBox.rect
    const success = selectInRect(rect, mode)

    // 清理选择框状态
    selectionState.selectionBox.active = false
    selectionState.selectionBox.visible = false
    selectionStore.clearPreviewSelection()

    return success
  }

  function cancelSelectionBox(): void {
    if (!selectionState.selectionBox.active) return

    selectionState.selectionBox.active = false
    selectionState.selectionBox.visible = false
    selectionStore.clearPreviewSelection()
  }

  // 多选操作
  function enableMultiSelect(anchor: string | null = null): void {
    selectionState.multiSelect.enabled = true
    selectionState.multiSelect.anchor = anchor
  }

  function disableMultiSelect(): void {
    selectionState.multiSelect.enabled = false
    selectionState.multiSelect.anchor = null
    selectionState.multiSelect.range = []
  }

  function selectRange(startId: string, endId: string, type: 'node' | 'connection' = 'node'): boolean {
    if (!selectionState.multiSelect.enabled) return false

    let items: any[] = []
    if (type === 'node') {
      items = workflowStore.nodes
    } else if (type === 'connection') {
      items = workflowStore.connections
    }

    const startIndex = items.findIndex((item: any) => item.id === startId)
    const endIndex = items.findIndex((item: any) => item.id === endId)

    if (startIndex === -1 || endIndex === -1) return false

    const minIndex = Math.min(startIndex, endIndex)
    const maxIndex = Math.max(startIndex, endIndex)

    const rangeIds = items.slice(minIndex, maxIndex + 1).map((item: any) => item.id)

    if (type === 'node') {
      return selectNodes(rangeIds, 'add')
    } else {
      return selectConnections(rangeIds, 'add')
    }
  }

  // 选择历史
  function saveSelectionHistory(): void {
    const currentSelection: SelectionHistoryItem = {
      nodes: [...selectedNodes.value],
      connections: [...selectedConnections.value],
      timestamp: Date.now(),
    }

    selectionState.history.previous.push(selectionState.history.current)
    selectionState.history.current = currentSelection

    // 限制历史记录数量
    if (selectionState.history.previous.length > selectionState.history.maxHistory) {
      selectionState.history.previous.shift()
    }
  }

  function restorePreviousSelection(): boolean {
    if (selectionState.history.previous.length === 0) return false

    const previousSelection = selectionState.history.previous.pop()!

    // 不保存当前选择到历史（避免循环）
    const success1 = selectionStore.selectNodes(previousSelection.nodes, 'replace')
    const success2 = selectionStore.selectConnections(previousSelection.connections, 'replace')

    if (success1 || success2) {
      selectionState.history.current = previousSelection
      emitSelectionChange(
        'restore',
        [...previousSelection.nodes, ...previousSelection.connections],
        'replace'
      )
    }

    return success1 || success2
  }

  function clearSelectionHistory(): void {
    selectionState.history.previous = []
    selectionState.history.current = { nodes: [], connections: [], timestamp: 0 }
  }

  // 选择过滤
  function setSelectionFilter(filterType: keyof SelectionFilter, values: string[]): void {
    selectionState.filter[filterType] = values
    applySelectionFilter()
  }

  function clearSelectionFilter(): void {
    selectionState.filter.nodeTypes = []
    selectionState.filter.connectionTypes = []
    selectionState.filter.status = []
    selectionState.filter.categories = []
  }

  function applySelectionFilter(): void {
    const { nodeTypes, connectionTypes, status, categories } = selectionState.filter

    // 过滤节点
    if (nodeTypes.length > 0 || status.length > 0 || categories.length > 0) {
      const filteredNodeIds = selectedNodes.value.filter((nodeId: string) => {
        const node = workflowStore.getNodeById(nodeId)
        if (!node) return false

        const matchesType = nodeTypes.length === 0 || nodeTypes.includes(node.type)
        const matchesStatus = status.length === 0 || status.includes(node.status || 'idle')
        const matchesCategory = categories.length === 0 || categories.includes(node.category)

        return matchesType && matchesStatus && matchesCategory
      })

      selectionStore.selectNodes(filteredNodeIds, 'replace')
    }

    // 过滤连接
    if (connectionTypes.length > 0) {
      const filteredConnectionIds = selectedConnections.value.filter((connId: string) => {
        const connection = workflowStore.getConnectionById(connId)
        if (!connection) return false

        return connectionTypes.includes(connection.type)
      })

      selectionStore.selectConnections(filteredConnectionIds, 'replace')
    }
  }

  // 工具函数
  function updateSelectionBoxRect(): void {
    const start = selectionState.selectionBox.startPoint
    const end = selectionState.selectionBox.endPoint

    selectionState.selectionBox.rect = {
      x: Math.min(start.x, end.x),
      y: Math.min(start.y, end.y),
      width: Math.abs(end.x - start.x),
      height: Math.abs(end.y - start.y),
    }
  }

  function findPath(startNodeId: string, endNodeId: string): string[] {
    // 简化的路径查找实现
    // 实际应用中可能需要更复杂的图算法
    return [startNodeId, endNodeId]
  }

  function findPathConnections(nodeIds: string[]): string[] {
    const connectionIds: string[] = []

    for (let i = 0; i < nodeIds.length - 1; i++) {
      const sourceId = nodeIds[i]
      const targetId = nodeIds[i + 1]

      const connection = workflowStore.connections.find(
        (conn: any) => conn.sourceNodeId === sourceId && conn.targetNodeId === targetId
      )

      if (connection) {
        connectionIds.push(connection.id)
      }
    }

    return connectionIds
  }

  function emitSelectionChange(type: string, items: string[], mode: SelectionMode): void {
    // 触发选择变化事件
    // 可以在这里添加事件发射逻辑
  }

  // 键盘快捷键支持
  function handleKeyboardShortcut(event: KeyboardEvent): void {
    if (event.ctrlKey || event.metaKey) {
      switch (event.key) {
        case 'a':
          event.preventDefault()
          selectAll()
          break
        case 'd':
          event.preventDefault()
          clearSelection()
          break
        case 'i':
          event.preventDefault()
          invertSelection()
          break
        case 'z':
          if (event.shiftKey) {
            event.preventDefault()
            // 重做选择（如果有历史管理）
          } else {
            event.preventDefault()
            restorePreviousSelection()
          }
          break
      }
    }

    if (event.key === 'Escape') {
      clearSelection()
    }
  }

  return {
    // 状态
    selectionState,
    selectedNodes,
    selectedConnections,
    selectedNodeObjects,
    selectedConnectionObjects,
    hasSelection,
    selectionCount,
    selectionBounds,
    canSelectAll,
    canInvertSelection,

    // 基础选择操作
    selectNode,
    selectNodes,
    selectConnection,
    selectConnections,
    selectAll,
    clearSelection,
    invertSelection,

    // 高级选择操作
    selectByType,
    selectByStatus,
    selectByCategory,
    selectInRect,
    selectConnected,
    selectPath,

    // 选择框操作
    startSelectionBox,
    updateSelectionBox,
    endSelectionBox,
    cancelSelectionBox,

    // 多选操作
    enableMultiSelect,
    disableMultiSelect,
    selectRange,

    // 选择历史
    saveSelectionHistory,
    restorePreviousSelection,
    clearSelectionHistory,

    // 选择过滤
    setSelectionFilter,
    clearSelectionFilter,
    applySelectionFilter,

    // 键盘快捷键
    handleKeyboardShortcut,
  }
}

// ========== 导出类型 ==========

export type {
  SelectionMode,
  SelectionDirection,
  SelectionOperationType,
  Point,
  Rectangle,
  SelectionBounds,
  SelectionBoxState,
  MultiSelectState,
  SelectionHistoryItem,
  SelectionHistory,
  SelectionFilter,
  SelectionOperation,
  SelectionState,
}

