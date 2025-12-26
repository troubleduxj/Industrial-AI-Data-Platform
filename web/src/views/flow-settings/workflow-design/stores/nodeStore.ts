/**
 * 节点状态管理
 * Node state management store
 */

import { defineStore } from 'pinia'
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { createNode, NODE_TYPES, validateNodeData } from '../utils/nodeTypes.js'
import { useWorkflowStore } from './workflowStore.js'
import { useHistoryStore } from './historyStore.js'
import { ACTION_TYPES } from '../utils/historyManager.js'

// ========== 类型定义 ==========

/** 节点模板 */
interface NodeTemplate {
  id: string
  type: string
  name: string
  defaultProperties?: Record<string, any>
  createdAt?: number
  updatedAt?: number
  description?: string
  icon?: string
}

/** 节点分类 */
interface NodeCategory {
  id: string
  name: string
  icon: string
}

/** 节点库项 */
interface NodeLibraryItem {
  type: string
  category: string
  name: string
  description: string
  icon: string
  defaultProperties: Record<string, any>
}

/** 节点样式 */
interface NodeStyle {
  backgroundColor?: string
  borderColor?: string
  textColor?: string
  [key: string]: any
}

/** 节点主题 */
interface NodeTheme {
  name: string
  displayName: string
  nodeStyles: {
    [nodeType: string]: NodeStyle
    default: NodeStyle
  }
}

/** 节点验证结果 */
interface NodeValidation {
  isValid: boolean
  errors: string[]
  warnings?: string[]
}

/** 验证错误 */
interface ValidationError {
  nodeId: string
  type: string
  message: string
  timestamp: number
}

/** 节点数据（临时类型，等 utils 迁移后会有完整定义） */
interface WorkflowNode {
  id: string
  type: string
  name: string
  x: number
  y: number
  width?: number
  height?: number
  style?: NodeStyle
  parentId?: string
  children?: string[]
  collapsed?: boolean
  [key: string]: any
}

/** 连接数据（临时类型） */
interface Connection {
  id: string
  fromNodeId: string
  toNodeId: string
  [key: string]: any
}

/** 位置信息 */
interface Position {
  x: number
  y: number
}

/** 区域边界 */
interface Bounds {
  x: number
  y: number
  width: number
  height: number
}

// ========== Store 定义 ==========

export const useNodeStore = defineStore('workflowNode', () => {
  // 节点相关状态
  const nodeTemplates: Ref<Map<string, NodeTemplate>> = ref(new Map())
  const nodeCategories: Ref<NodeCategory[]> = ref([])
  const nodeLibrary: Ref<NodeLibraryItem[]> = ref([])
  const nodeClipboard: Ref<WorkflowNode[]> = ref([])
  const nodeIdCounter: Ref<number> = ref(1)

  // 节点操作状态
  const draggedNode: Ref<WorkflowNode | null> = ref(null)
  const hoveredNode: Ref<WorkflowNode | null> = ref(null)
  const editingNode: Ref<WorkflowNode | null> = ref(null)
  const resizingNode: Ref<WorkflowNode | null> = ref(null)

  // 节点样式状态
  const nodeStyles: Ref<Map<string, NodeStyle>> = ref(new Map())
  const nodeThemes: Ref<NodeTheme[]> = ref([])
  const currentTheme: Ref<string> = ref('default')

  // 节点验证状态
  const nodeValidation: Ref<Map<string, NodeValidation>> = ref(new Map())
  const validationErrors: Ref<ValidationError[]> = ref([])

  // 获取其他store
  const workflowStore = useWorkflowStore()
  const historyStore = useHistoryStore()

  // 计算属性
  const nodeCount: ComputedRef<number> = computed(() => workflowStore.nodes.length)
  
  const nodesByType: ComputedRef<Map<string, WorkflowNode[]>> = computed(() => {
    const result = new Map<string, WorkflowNode[]>()
    workflowStore.nodes.forEach((node: WorkflowNode) => {
      const type = node.type
      if (!result.has(type)) {
        result.set(type, [])
      }
      result.get(type)!.push(node)
    })
    return result
  })

  const nodesByCategory: ComputedRef<Map<string, WorkflowNode[]>> = computed(() => {
    const result = new Map<string, WorkflowNode[]>()
    workflowStore.nodes.forEach((node: WorkflowNode) => {
      const category = getNodeCategory(node.type)
      if (!result.has(category)) {
        result.set(category, [])
      }
      result.get(category)!.push(node)
    })
    return result
  })

  const invalidNodes: ComputedRef<WorkflowNode[]> = computed(() => {
    return workflowStore.nodes.filter((node: WorkflowNode) => {
      const validation = nodeValidation.value.get(node.id)
      return validation && !validation.isValid
    })
  })

  const orphanNodes: ComputedRef<WorkflowNode[]> = computed(() => {
    return workflowStore.nodes.filter((node: WorkflowNode) => {
      const hasIncoming = workflowStore.connections.some((conn: Connection) => conn.toNodeId === node.id)
      const hasOutgoing = workflowStore.connections.some((conn: Connection) => conn.fromNodeId === node.id)
      return !hasIncoming && !hasOutgoing && node.type !== NODE_TYPES.START
    })
  })

  // 节点创建和管理
  function createNodeFromTemplate(
    templateId: string,
    position: Position,
    properties: Record<string, any> = {}
  ): WorkflowNode {
    const template = nodeTemplates.value.get(templateId)
    if (!template) {
      throw new Error(`节点模板不存在: ${templateId}`)
    }

    const nodeData = {
      id: generateNodeId(),
      type: template.type,
      name: template.name,
      x: position.x,
      y: position.y,
      ...template.defaultProperties,
      ...properties,
    }

    const node = createNode(template.type, nodeData)
    return workflowStore.addNode(node.type, { x: node.x, y: node.y }, node)
  }

  function duplicateNodes(nodeIds: string[], offset: Position = { x: 50, y: 50 }): WorkflowNode[] {
    const duplicatedNodes: WorkflowNode[] = []
    const nodeMap = new Map<string, string>()

    // 复制节点
    nodeIds.forEach((nodeId) => {
      const originalNode = workflowStore.getNodeById(nodeId)
      if (originalNode) {
        const newNode: WorkflowNode = {
          ...originalNode,
          id: generateNodeId(),
          name: `${originalNode.name} (副本)`,
          x: originalNode.x + offset.x,
          y: originalNode.y + offset.y,
        }

        nodeMap.set(originalNode.id, newNode.id)
        duplicatedNodes.push(newNode)
        workflowStore.nodes.push(newNode)
      }
    })

    // 复制相关连接
    const connectionsToAdd: Connection[] = []
    workflowStore.connections.forEach((conn: Connection) => {
      if (nodeMap.has(conn.fromNodeId) && nodeMap.has(conn.toNodeId)) {
        connectionsToAdd.push({
          ...conn,
          id: `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          fromNodeId: nodeMap.get(conn.fromNodeId)!,
          toNodeId: nodeMap.get(conn.toNodeId)!,
        })
      }
    })

    connectionsToAdd.forEach((conn) => {
      workflowStore.connections.push(conn)
    })

    historyStore.saveToHistory(ACTION_TYPES.DUPLICATE_NODES, {
      count: duplicatedNodes.length,
    })

    return duplicatedNodes
  }

  function groupNodes(nodeIds: string[], groupName: string = '节点组'): WorkflowNode | null {
    const nodes = nodeIds.map((id) => workflowStore.getNodeById(id)).filter(Boolean) as WorkflowNode[]
    if (nodes.length < 2) return null

    // 计算组的边界
    const bounds = calculateNodesBounds(nodes)

    // 创建组节点
    const groupNode: WorkflowNode = {
      id: generateNodeId(),
      type: NODE_TYPES.GROUP,
      name: groupName,
      x: bounds.x - 20,
      y: bounds.y - 40,
      width: bounds.width + 40,
      height: bounds.height + 60,
      children: nodeIds,
      collapsed: false,
    }

    workflowStore.nodes.push(groupNode)

    // 更新子节点的父节点引用
    nodeIds.forEach((nodeId) => {
      const node = workflowStore.getNodeById(nodeId)
      if (node) {
        node.parentId = groupNode.id
      }
    })

    historyStore.saveToHistory(ACTION_TYPES.GROUP_NODES, {
      groupName,
      nodeCount: nodeIds.length,
    })

    return groupNode
  }

  function ungroupNodes(groupNodeId: string): boolean {
    const groupNode = workflowStore.getNodeById(groupNodeId)
    if (!groupNode || groupNode.type !== NODE_TYPES.GROUP) return false

    // 移除子节点的父节点引用
    if (groupNode.children) {
      groupNode.children.forEach((nodeId: string) => {
        const node = workflowStore.getNodeById(nodeId)
        if (node) {
          delete node.parentId
        }
      })
    }

    // 删除组节点
    workflowStore.removeNode(groupNodeId)

    historyStore.saveToHistory(ACTION_TYPES.UNGROUP_NODES, {
      nodeCount: groupNode.children?.length || 0,
    })

    return true
  }

  // 节点验证
  function validateNode(nodeId: string): NodeValidation | null {
    const node = workflowStore.getNodeById(nodeId)
    if (!node) return null

    const validation = validateNodeData(node)
    nodeValidation.value.set(nodeId, validation)

    if (!validation.isValid) {
      const existingError = validationErrors.value.find((err) => err.nodeId === nodeId)
      if (!existingError) {
        validationErrors.value.push({
          nodeId,
          type: 'node_validation',
          message: validation.errors.join(', '),
          timestamp: Date.now(),
        })
      }
    } else {
      // 移除验证错误
      const errorIndex = validationErrors.value.findIndex((err) => err.nodeId === nodeId)
      if (errorIndex > -1) {
        validationErrors.value.splice(errorIndex, 1)
      }
    }

    return validation
  }

  function validateAllNodes(): Map<string, NodeValidation> {
    const results = new Map<string, NodeValidation>()
    workflowStore.nodes.forEach((node: WorkflowNode) => {
      const validation = validateNode(node.id)
      if (validation) {
        results.set(node.id, validation)
      }
    })
    return results
  }

  // 节点样式管理
  function setNodeStyle(nodeId: string, style: NodeStyle): void {
    nodeStyles.value.set(nodeId, style)
    const node = workflowStore.getNodeById(nodeId)
    if (node) {
      node.style = { ...node.style, ...style }
    }
  }

  function getNodeStyle(nodeId: string): NodeStyle {
    return nodeStyles.value.get(nodeId) || {}
  }

  function applyThemeToNode(nodeId: string, themeName: string): void {
    const theme = nodeThemes.value.find((t) => t.name === themeName)
    if (theme && theme.nodeStyles) {
      const node = workflowStore.getNodeById(nodeId)
      if (node) {
        const typeStyle = theme.nodeStyles[node.type] || theme.nodeStyles.default
        if (typeStyle) {
          setNodeStyle(nodeId, typeStyle)
        }
      }
    }
  }

  // 节点模板管理
  function addNodeTemplate(template: NodeTemplate): void {
    if (!template.id || !template.type || !template.name) {
      throw new Error('节点模板必须包含id、type和name字段')
    }

    nodeTemplates.value.set(template.id, {
      ...template,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    })
  }

  function removeNodeTemplate(templateId: string): boolean {
    return nodeTemplates.value.delete(templateId)
  }

  function updateNodeTemplate(templateId: string, updates: Partial<NodeTemplate>): boolean {
    const template = nodeTemplates.value.get(templateId)
    if (template) {
      nodeTemplates.value.set(templateId, {
        ...template,
        ...updates,
        updatedAt: Date.now(),
      })
      return true
    }
    return false
  }

  // 节点剪贴板操作
  function copyNodes(nodeIds: string[]): void {
    const nodes = nodeIds.map((id) => workflowStore.getNodeById(id)).filter(Boolean) as WorkflowNode[]
    nodeClipboard.value = nodes.map((node) => ({ ...node }))
  }

  function cutNodes(nodeIds: string[]): void {
    copyNodes(nodeIds)
    nodeIds.forEach((nodeId) => workflowStore.removeNode(nodeId))
  }

  function pasteNodes(position: Position = { x: 100, y: 100 }): WorkflowNode[] {
    if (nodeClipboard.value.length === 0) return []

    const pastedNodes: WorkflowNode[] = []
    const nodeMap = new Map<string, string>()

    // 计算偏移量
    const firstNode = nodeClipboard.value[0]
    const offset: Position = {
      x: position.x - firstNode.x,
      y: position.y - firstNode.y,
    }

    // 粘贴节点
    nodeClipboard.value.forEach((node) => {
      const newNode: WorkflowNode = {
        ...node,
        id: generateNodeId(),
        x: node.x + offset.x,
        y: node.y + offset.y,
      }

      nodeMap.set(node.id, newNode.id)
      pastedNodes.push(newNode)
      workflowStore.nodes.push(newNode)
    })

    return pastedNodes
  }

  // 工具函数
  function generateNodeId(): string {
    return `node_${nodeIdCounter.value++}`
  }

  function getNodeCategory(nodeType: string): string {
    const categoryMap: Record<string, string> = {
      [NODE_TYPES.START]: '控制',
      [NODE_TYPES.END]: '控制',
      [NODE_TYPES.CONDITION]: '控制',
      [NODE_TYPES.LOOP]: '控制',
      [NODE_TYPES.API]: '数据',
      [NODE_TYPES.DATABASE]: '数据',
      [NODE_TYPES.TRANSFORM]: '处理',
      [NODE_TYPES.SCRIPT]: '处理',
      [NODE_TYPES.EMAIL]: '通知',
      [NODE_TYPES.SMS]: '通知',
      [NODE_TYPES.WEBHOOK]: '集成',
      [NODE_TYPES.TIMER]: '触发器',
    }
    return categoryMap[nodeType] || '其他'
  }

  function calculateNodesBounds(nodes: WorkflowNode[]): Bounds {
    if (nodes.length === 0) return { x: 0, y: 0, width: 0, height: 0 }

    let minX = Infinity
    let minY = Infinity
    let maxX = -Infinity
    let maxY = -Infinity

    nodes.forEach((node) => {
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
    }
  }

  // 初始化
  function initializeNodeStore(): void {
    // 初始化节点分类
    nodeCategories.value = [
      { id: 'control', name: '控制', icon: 'control' },
      { id: 'data', name: '数据', icon: 'data' },
      { id: 'process', name: '处理', icon: 'process' },
      { id: 'notification', name: '通知', icon: 'notification' },
      { id: 'integration', name: '集成', icon: 'integration' },
      { id: 'trigger', name: '触发器', icon: 'trigger' },
      { id: 'other', name: '其他', icon: 'other' },
    ]

    // 初始化节点库
    nodeLibrary.value = Object.values(NODE_TYPES).map((type) => ({
      type,
      category: getNodeCategory(type),
      name: type,
      description: `${type}节点`,
      icon: type.toLowerCase(),
      defaultProperties: {},
    }))

    // 初始化默认主题
    nodeThemes.value = [
      {
        name: 'default',
        displayName: '默认主题',
        nodeStyles: {
          default: {
            backgroundColor: '#ffffff',
            borderColor: '#d1d5db',
            textColor: '#374151',
          },
        },
      },
    ]
  }

  // 清理函数
  function clearNodeStore(): void {
    nodeTemplates.value.clear()
    nodeClipboard.value = []
    nodeStyles.value.clear()
    nodeValidation.value.clear()
    validationErrors.value = []
    draggedNode.value = null
    hoveredNode.value = null
    editingNode.value = null
    resizingNode.value = null
  }

  return {
    // 状态
    nodeTemplates,
    nodeCategories,
    nodeLibrary,
    nodeClipboard,
    nodeIdCounter,
    draggedNode,
    hoveredNode,
    editingNode,
    resizingNode,
    nodeStyles,
    nodeThemes,
    currentTheme,
    nodeValidation,
    validationErrors,

    // 计算属性
    nodeCount,
    nodesByType,
    nodesByCategory,
    invalidNodes,
    orphanNodes,

    // 方法
    createNodeFromTemplate,
    duplicateNodes,
    groupNodes,
    ungroupNodes,
    validateNode,
    validateAllNodes,
    setNodeStyle,
    getNodeStyle,
    applyThemeToNode,
    addNodeTemplate,
    removeNodeTemplate,
    updateNodeTemplate,
    copyNodes,
    cutNodes,
    pasteNodes,
    generateNodeId,
    getNodeCategory,
    calculateNodesBounds,
    initializeNodeStore,
    clearNodeStore,
  }
})

// ========== 导出类型 ==========

export type {
  NodeTemplate,
  NodeCategory,
  NodeLibraryItem,
  NodeStyle,
  NodeTheme,
  NodeValidation,
  ValidationError,
  WorkflowNode,
  Connection,
  Position,
  Bounds,
}

