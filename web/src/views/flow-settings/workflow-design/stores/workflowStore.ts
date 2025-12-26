/**
 * 工作流状态管理
 * Workflow state management store
 */

import { defineStore } from 'pinia'
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { createHistoryManager, ACTION_TYPES, createStateSnapshot } from '../utils/historyManager.js'
import { validateWorkflow } from '../utils/connectionValidator.js'
import { createNode, NODE_TYPES } from '../utils/nodeTypes.js'

// ========== 类型定义 ==========

/** 工作流信息 */
interface WorkflowInfo {
  id: string
  name: string
  description: string
  version: string
  createdAt: string | null
  updatedAt: string | null
  author: string
}

/** 画布状态 */
interface CanvasState {
  scale: number
  translateX: number
  translateY: number
  showGrid: boolean
  snapToGrid: boolean
  gridSize: number
}

/** 编辑状态 */
interface EditState {
  isEditing: boolean
  isDirty: boolean
  lastSaved: string | null
  lastModified?: string
  autoSave: boolean
}

/** 位置信息 */
interface Position {
  x: number
  y: number
}

/** 节点数据（临时类型） */
interface WorkflowNode {
  id: string
  type: string
  name: string
  x: number
  y: number
  [key: string]: any
}

/** 连接数据（临时类型） */
interface Connection {
  id: string
  fromNodeId: string
  toNodeId: string
  fromPort?: string
  toPort?: string
  [key: string]: any
}

/** 工作流统计 */
interface WorkflowStats {
  totalNodes: number
  totalConnections: number
  nodeTypes: Record<string, number>
  hasStartNode: boolean
  hasEndNode: boolean
}

/** 工作流验证结果（临时类型） */
interface WorkflowValidation {
  isValid: boolean
  errors: string[]
  warnings?: string[]
}

/** 历史管理器（临时类型） */
interface HistoryManager {
  canUndo(): boolean
  canRedo(): boolean
  saveState(state: any, description: string): void
  undo(): any | null
  redo(): any | null
  getHistoryInfo(): any
}

/** 状态快照 */
interface StateSnapshot {
  nodes: WorkflowNode[]
  connections: Connection[]
  selectedNodes?: string[]
  selectedConnections?: string[]
  canvasState?: CanvasState
}

/** 工作流导出数据 */
interface WorkflowExportData {
  nodes: WorkflowNode[]
  connections: Connection[]
  info: WorkflowInfo
  canvasState: CanvasState
  exportedAt: string
}

/** 工作流加载数据 */
interface WorkflowLoadData {
  nodes?: WorkflowNode[]
  connections?: Connection[]
  info?: Partial<WorkflowInfo>
  canvasState?: Partial<CanvasState>
}

/** 节点更新数据 */
interface NodeUpdate {
  id: string
  [key: string]: any
}

// ========== Store 定义 ==========

export const useWorkflowStore = defineStore('workflow', () => {
  // 基础数据
  const nodes: Ref<WorkflowNode[]> = ref([])
  const connections: Ref<Connection[]> = ref([])
  const workflowInfo: Ref<WorkflowInfo> = ref({
    id: '',
    name: '未命名工作流',
    description: '',
    version: '1.0.0',
    createdAt: null,
    updatedAt: null,
    author: '',
  })

  // 选择状态
  const selectedNodes: Ref<string[]> = ref([])
  const selectedConnections: Ref<string[]> = ref([])
  const highlightedNodes: Ref<string[]> = ref([])
  const highlightedConnections: Ref<string[]> = ref([])

  // 画布状态
  const canvasState: Ref<CanvasState> = ref({
    scale: 1,
    translateX: 0,
    translateY: 0,
    showGrid: true,
    snapToGrid: true,
    gridSize: 20,
  })

  // 编辑状态
  const editState: Ref<EditState> = ref({
    isEditing: false,
    isDirty: false,
    lastSaved: null,
    autoSave: true,
  })

  // 历史记录管理
  const historyManager: HistoryManager = createHistoryManager(50)

  // ID计数器
  const nodeIdCounter: Ref<number> = ref(1)
  const connectionIdCounter: Ref<number> = ref(1)

  // 计算属性
  const nodeMap: ComputedRef<Map<string, WorkflowNode>> = computed(() => {
    const map = new Map<string, WorkflowNode>()
    nodes.value.forEach((node) => {
      map.set(node.id, node)
    })
    return map
  })

  const connectionMap: ComputedRef<Map<string, Connection>> = computed(() => {
    const map = new Map<string, Connection>()
    connections.value.forEach((conn) => {
      map.set(conn.id, conn)
    })
    return map
  })

  const workflowStats: ComputedRef<WorkflowStats> = computed(() => {
    const nodeTypes: Record<string, number> = {}
    nodes.value.forEach((node) => {
      nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1
    })

    return {
      totalNodes: nodes.value.length,
      totalConnections: connections.value.length,
      nodeTypes,
      hasStartNode: nodes.value.some((node) => node.type === 'start'),
      hasEndNode: nodes.value.some((node) => node.type === 'end'),
    }
  })

  const workflowValidation: ComputedRef<WorkflowValidation> = computed(() => {
    return validateWorkflow(nodes.value, connections.value)
  })

  const canUndo: ComputedRef<boolean> = computed(() => historyManager.canUndo())
  const canRedo: ComputedRef<boolean> = computed(() => historyManager.canRedo())

  // 节点操作
  function addNode(nodeType: string, position: Position = { x: 100, y: 100 }, properties: Record<string, any> = {}): WorkflowNode {
    const node = createNode(nodeType, {
      id: `node_${nodeIdCounter.value++}`,
      x: position.x,
      y: position.y,
      ...properties,
    })

    nodes.value.push(node)
    saveToHistory(ACTION_TYPES.ADD_NODE, { nodeType, nodeName: node.name })
    markDirty()

    return node
  }

  function removeNode(nodeId: string): boolean {
    const nodeIndex = nodes.value.findIndex((node) => node.id === nodeId)
    if (nodeIndex === -1) return false

    const node = nodes.value[nodeIndex]

    // 删除相关连接
    const relatedConnections = connections.value.filter(
      (conn) => conn.fromNodeId === nodeId || conn.toNodeId === nodeId
    )

    relatedConnections.forEach((conn) => {
      removeConnection(conn.id, false) // 不保存历史记录
    })

    // 删除节点
    nodes.value.splice(nodeIndex, 1)

    // 清除选择状态
    const selectedIndex = selectedNodes.value.indexOf(nodeId)
    if (selectedIndex > -1) {
      selectedNodes.value.splice(selectedIndex, 1)
    }

    saveToHistory(ACTION_TYPES.DELETE_NODE, { nodeName: node.name })
    markDirty()

    return true
  }

  function updateNode(nodeId: string, updates: Partial<WorkflowNode>): boolean {
    const node = nodeMap.value.get(nodeId)
    if (!node) return false

    const nodeIndex = nodes.value.findIndex((n) => n.id === nodeId)
    nodes.value[nodeIndex] = { ...node, ...updates }

    saveToHistory(ACTION_TYPES.UPDATE_NODE, { nodeName: node.name })
    markDirty()

    return true
  }

  function moveNode(nodeId: string, position: Position): boolean {
    return updateNode(nodeId, position)
  }

  function moveNodes(nodeUpdates: NodeUpdate[]): void {
    nodeUpdates.forEach((update) => {
      const nodeIndex = nodes.value.findIndex((n) => n.id === update.id)
      if (nodeIndex > -1) {
        nodes.value[nodeIndex] = { ...nodes.value[nodeIndex], ...update }
      }
    })

    const count = nodeUpdates.length
    saveToHistory(ACTION_TYPES.BATCH_UPDATE, { count })
    markDirty()
  }

  function duplicateNode(nodeId: string, offset: Position = { x: 50, y: 50 }): WorkflowNode | null {
    const originalNode = nodeMap.value.get(nodeId)
    if (!originalNode) return null

    const newNode: WorkflowNode = {
      ...originalNode,
      id: `node_${nodeIdCounter.value++}`,
      name: `${originalNode.name} (副本)`,
      x: originalNode.x + offset.x,
      y: originalNode.y + offset.y,
    }

    nodes.value.push(newNode)
    saveToHistory(ACTION_TYPES.ADD_NODE, { nodeType: newNode.type, nodeName: newNode.name })
    markDirty()

    return newNode
  }

  // 连接操作
  function addConnection(connectionData: Partial<Connection>): Connection {
    const connection: Connection = {
      id: `conn_${connectionIdCounter.value++}`,
      fromNodeId: '',
      toNodeId: '',
      ...connectionData,
    }

    connections.value.push(connection)
    saveToHistory(ACTION_TYPES.ADD_CONNECTION)
    markDirty()

    return connection
  }

  function removeConnection(connectionId: string, saveHistory: boolean = true): boolean {
    const connectionIndex = connections.value.findIndex((conn) => conn.id === connectionId)
    if (connectionIndex === -1) return false

    connections.value.splice(connectionIndex, 1)

    // 清除选择状态
    const selectedIndex = selectedConnections.value.indexOf(connectionId)
    if (selectedIndex > -1) {
      selectedConnections.value.splice(selectedIndex, 1)
    }

    if (saveHistory) {
      saveToHistory(ACTION_TYPES.DELETE_CONNECTION)
      markDirty()
    }

    return true
  }

  // 选择操作
  function selectNode(nodeId: string, multiple: boolean = false): void {
    if (multiple) {
      const index = selectedNodes.value.indexOf(nodeId)
      if (index > -1) {
        selectedNodes.value.splice(index, 1)
      } else {
        selectedNodes.value.push(nodeId)
      }
    } else {
      selectedNodes.value = [nodeId]
    }
  }

  function selectNodes(nodeIds: string[]): void {
    selectedNodes.value = [...nodeIds]
  }

  function clearNodeSelection(): void {
    selectedNodes.value = []
  }

  function selectConnection(connectionId: string, multiple: boolean = false): void {
    if (multiple) {
      const index = selectedConnections.value.indexOf(connectionId)
      if (index > -1) {
        selectedConnections.value.splice(index, 1)
      } else {
        selectedConnections.value.push(connectionId)
      }
    } else {
      selectedConnections.value = [connectionId]
    }
  }

  function clearConnectionSelection(): void {
    selectedConnections.value = []
  }

  function clearAllSelection(): void {
    clearNodeSelection()
    clearConnectionSelection()
  }

  function selectAll(): void {
    selectedNodes.value = nodes.value.map((node) => node.id)
    selectedConnections.value = connections.value.map((conn) => conn.id)
  }

  // 高亮操作
  function highlightNodes(nodeIds: string[]): void {
    highlightedNodes.value = [...nodeIds]
  }

  function highlightConnections(connectionIds: string[]): void {
    highlightedConnections.value = [...connectionIds]
  }

  function clearHighlight(): void {
    highlightedNodes.value = []
    highlightedConnections.value = []
  }

  // 画布操作
  function updateCanvasState(updates: Partial<CanvasState>): void {
    canvasState.value = { ...canvasState.value, ...updates }
  }

  function resetCanvasView(): void {
    canvasState.value.scale = 1
    canvasState.value.translateX = 0
    canvasState.value.translateY = 0
  }

  // 历史记录操作
  function saveToHistory(actionType: string | typeof ACTION_TYPES[keyof typeof ACTION_TYPES], data: Record<string, any> = {}): void {
    const state = createStateSnapshot(nodes.value, connections.value, {
      selectedNodes: selectedNodes.value,
      selectedConnections: selectedConnections.value,
      canvasState: canvasState.value,
    })

    const actionDescription =
      typeof actionType === 'string' ? actionType : getActionDescription(actionType, data)

    historyManager.saveState(state, actionDescription)
  }

  function undo(): boolean {
    const previousState = historyManager.undo()
    if (previousState) {
      restoreState(previousState)
      return true
    }
    return false
  }

  function redo(): boolean {
    const nextState = historyManager.redo()
    if (nextState) {
      restoreState(nextState)
      return true
    }
    return false
  }

  function restoreState(state: StateSnapshot): void {
    nodes.value = state.nodes || []
    connections.value = state.connections || []
    selectedNodes.value = state.selectedNodes || []
    selectedConnections.value = state.selectedConnections || []

    if (state.canvasState) {
      canvasState.value = { ...canvasState.value, ...state.canvasState }
    }

    markDirty()
  }

  function getHistoryInfo(): any {
    return historyManager.getHistoryInfo()
  }

  // 工作流操作
  function clearWorkflow(): void {
    nodes.value = []
    connections.value = []
    clearAllSelection()
    clearHighlight()
    resetCanvasView()

    saveToHistory(ACTION_TYPES.CLEAR_CANVAS)
    markDirty()
  }

  function loadWorkflow(workflowData: WorkflowLoadData): void {
    const {
      nodes: newNodes,
      connections: newConnections,
      info,
      canvasState: newCanvasState,
    } = workflowData

    nodes.value = newNodes || []
    connections.value = newConnections || []

    if (info) {
      workflowInfo.value = { ...workflowInfo.value, ...info }
    }

    if (newCanvasState) {
      canvasState.value = { ...canvasState.value, ...newCanvasState }
    }

    // 更新ID计数器
    updateIdCounters()

    clearAllSelection()
    clearHighlight()

    saveToHistory(ACTION_TYPES.IMPORT_WORKFLOW)
    markClean()
  }

  function exportWorkflow(): WorkflowExportData {
    return {
      nodes: nodes.value,
      connections: connections.value,
      info: workflowInfo.value,
      canvasState: canvasState.value,
      exportedAt: new Date().toISOString(),
    }
  }

  function updateWorkflowInfo(updates: Partial<WorkflowInfo>): void {
    workflowInfo.value = { ...workflowInfo.value, ...updates, updatedAt: new Date().toISOString() }
    markDirty()
  }

  // 辅助函数
  function updateIdCounters(): void {
    let maxNodeId = 0
    let maxConnectionId = 0

    nodes.value.forEach((node) => {
      const match = node.id.match(/node_(\d+)/)
      if (match) {
        maxNodeId = Math.max(maxNodeId, parseInt(match[1]))
      }
    })

    connections.value.forEach((conn) => {
      const match = conn.id.match(/conn_(\d+)/)
      if (match) {
        maxConnectionId = Math.max(maxConnectionId, parseInt(match[1]))
      }
    })

    nodeIdCounter.value = maxNodeId + 1
    connectionIdCounter.value = maxConnectionId + 1
  }

  function markDirty(): void {
    editState.value.isDirty = true
    editState.value.lastModified = new Date().toISOString()
  }

  function markClean(): void {
    editState.value.isDirty = false
    editState.value.lastSaved = new Date().toISOString()
  }

  // 别名方法，保持兼容性
  function markAsSaved(): void {
    markClean()
  }

  // 加载工作流数据（别名）
  function loadWorkflowData(data: WorkflowLoadData): void {
    loadWorkflow(data)
  }

  function getNodeById(nodeId: string): WorkflowNode | undefined {
    return nodeMap.value.get(nodeId)
  }

  function getConnectionById(connectionId: string): Connection | undefined {
    return connectionMap.value.get(connectionId)
  }

  function getSelectedNodesData(): WorkflowNode[] {
    return selectedNodes.value.map((id) => nodeMap.value.get(id)).filter(Boolean) as WorkflowNode[]
  }

  function getSelectedConnectionsData(): Connection[] {
    return selectedConnections.value.map((id) => connectionMap.value.get(id)).filter(Boolean) as Connection[]
  }

  function getActionDescription(actionType: string, data: Record<string, any>): string {
    // 辅助函数：生成操作描述
    const descriptions: Record<string, (data: Record<string, any>) => string> = {
      [ACTION_TYPES.ADD_NODE]: (d) => `添加节点: ${d.nodeName || d.nodeType}`,
      [ACTION_TYPES.DELETE_NODE]: (d) => `删除节点: ${d.nodeName}`,
      [ACTION_TYPES.UPDATE_NODE]: (d) => `更新节点: ${d.nodeName}`,
      [ACTION_TYPES.BATCH_UPDATE]: (d) => `批量更新: ${d.count} 个节点`,
      [ACTION_TYPES.ADD_CONNECTION]: () => '添加连接',
      [ACTION_TYPES.DELETE_CONNECTION]: () => '删除连接',
      [ACTION_TYPES.CLEAR_CANVAS]: () => '清空画布',
      [ACTION_TYPES.IMPORT_WORKFLOW]: () => '导入工作流',
    }

    const generator = descriptions[actionType]
    return generator ? generator(data) : actionType
  }

  // 初始化
  function initialize(): void {
    // 保存初始状态
    saveToHistory('初始化工作流')
    markClean()
  }

  return {
    // 状态
    nodes: computed(() => nodes.value),
    connections: computed(() => connections.value),
    workflowInfo: computed(() => workflowInfo.value),
    selectedNodes: computed(() => selectedNodes.value),
    selectedConnections: computed(() => selectedConnections.value),
    highlightedNodes: computed(() => highlightedNodes.value),
    highlightedConnections: computed(() => highlightedConnections.value),
    canvasState: computed(() => canvasState.value),
    editState: computed(() => editState.value),

    // 计算属性
    nodeMap,
    connectionMap,
    workflowStats,
    workflowValidation,
    canUndo,
    canRedo,
    isDirty: computed(() => editState.value.isDirty),
    canPaste: computed(() => false), // TODO: 实现剪贴板功能

    // 方法
    addNode,
    removeNode,
    updateNode,
    moveNode,
    moveNodes,
    duplicateNode,
    addConnection,
    removeConnection,
    selectNode,
    selectNodes,
    clearNodeSelection,
    selectConnection,
    clearConnectionSelection,
    clearAllSelection,
    selectAll,
    highlightNodes,
    highlightConnections,
    clearHighlight,
    updateCanvasState,
    resetCanvasView,
    saveToHistory,
    undo,
    redo,
    getHistoryInfo,
    clearWorkflow,
    loadWorkflow,
    exportWorkflow,
    updateWorkflowInfo,
    getNodeById,
    getConnectionById,
    getSelectedNodesData,
    getSelectedConnectionsData,
    markClean,
    markAsSaved,
    loadWorkflowData,
    initialize,
  }
})

// ========== 导出类型 ==========

export type {
  WorkflowInfo,
  CanvasState,
  EditState,
  Position,
  WorkflowNode,
  Connection,
  WorkflowStats,
  WorkflowValidation,
  StateSnapshot,
  WorkflowExportData,
  WorkflowLoadData,
  NodeUpdate,
}

