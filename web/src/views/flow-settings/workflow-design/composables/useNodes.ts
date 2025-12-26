/**
 * 节点管理组合函数
 * Nodes management composable
 */

import { ref, computed, reactive, watch, type Ref, type ComputedRef } from 'vue'
import { useNodeStore } from '../stores/nodeStore.js'
import { useWorkflowStore } from '../stores/workflowStore.js'
import { useSelectionStore } from '../stores/selectionStore.js'
import { useHistoryStore } from '../stores/historyStore.js'
import { createNode, NODE_TYPES, validateNodeData } from '../utils/nodeTypes.js'
import { snapToGrid } from '../utils/gridUtils.js'
import { ACTION_TYPES } from '../utils/historyManager.js'

// ========== 类型定义 ==========

interface Point { x: number; y: number }
interface Size { width: number; height: number }

interface CreatingState {
  active: boolean
  nodeType: string | null
  position: Point
  properties: Record<string, any>
}

interface EditingState {
  active: boolean
  nodeId: string | null
  field: string | null
  originalValue: any
}

interface DraggingState {
  active: boolean
  nodeIds: string[]
  startPositions: Map<string, Point>
  currentOffset: Point
  snapToGrid: boolean
}

interface ResizingState {
  active: boolean
  nodeId: string | null
  handle: string | null
  startSize: Size
  startPosition: Point
}

interface ClipboardState {
  nodes: any[]
  connections: any[]
  operation: 'copy' | 'cut' | null
}

interface SearchFilters {
  type: string[]
  status: string[]
  category: string[]
}

interface SearchState {
  query: string
  results: any[]
  filters: SearchFilters
}

interface NodeState {
  creating: CreatingState
  editing: EditingState
  dragging: DraggingState
  resizing: ResizingState
  clipboard: ClipboardState
  search: SearchState
}

// ========== Composable ==========

export function useNodes() {
  const nodeStore = useNodeStore()
  const workflowStore = useWorkflowStore()
  const selectionStore = useSelectionStore()
  const historyStore = useHistoryStore()

  const nodeState = reactive<NodeState>({
    creating: {
      active: false,
      nodeType: null,
      position: { x: 0, y: 0 },
      properties: {},
    },
    editing: {
      active: false,
      nodeId: null,
      field: null,
      originalValue: null,
    },
    dragging: {
      active: false,
      nodeIds: [],
      startPositions: new Map(),
      currentOffset: { x: 0, y: 0 },
      snapToGrid: true,
    },
    resizing: {
      active: false,
      nodeId: null,
      handle: null,
      startSize: { width: 0, height: 0 },
      startPosition: { x: 0, y: 0 },
    },
    clipboard: {
      nodes: [],
      connections: [],
      operation: null,
    },
    search: {
      query: '',
      results: [],
      filters: {
        type: [],
        status: [],
        category: [],
      },
    },
  })

  const nodes: ComputedRef<any[]> = computed(() => workflowStore.nodes)
  const selectedNodes: ComputedRef<string[]> = computed(() => selectionStore.selectedNodes)
  const selectedNodeObjects: ComputedRef<any[]> = computed(() =>
    selectedNodes.value.map((id: string) => workflowStore.getNodeById(id)).filter(Boolean)
  )

  const nodesByType: ComputedRef<any> = computed(() => nodeStore.nodesByType)
  const nodesByCategory: ComputedRef<any> = computed(() => nodeStore.nodesByCategory)
  const invalidNodes: ComputedRef<any[]> = computed(() => nodeStore.invalidNodes)
  const orphanNodes: ComputedRef<any[]> = computed(() => nodeStore.orphanNodes)

  const searchResults: ComputedRef<any[]> = computed(() => {
    if (!nodeState.search.query) return nodes.value

    const query = nodeState.search.query.toLowerCase()
    return nodes.value.filter((node: any) => {
      const matchesQuery =
        node.name?.toLowerCase().includes(query) ||
        node.type?.toLowerCase().includes(query) ||
        node.description?.toLowerCase().includes(query)

      const matchesTypeFilter =
        nodeState.search.filters.type.length === 0 ||
        nodeState.search.filters.type.includes(node.type)

      const matchesStatusFilter =
        nodeState.search.filters.status.length === 0 ||
        nodeState.search.filters.status.includes(node.status || 'idle')

      const matchesCategoryFilter =
        nodeState.search.filters.category.length === 0 ||
        nodeState.search.filters.category.includes(nodeStore.getNodeCategory(node.type))

      return matchesQuery && matchesTypeFilter && matchesStatusFilter && matchesCategoryFilter
    })
  })

  function startNodeCreation(nodeType: string, position: Point): void {
    nodeState.creating.active = true
    nodeState.creating.nodeType = nodeType
    nodeState.creating.position = position
    nodeState.creating.properties = {}
  }

  function createNodeAt(nodeType: string, position: Point, properties: Record<string, any> = {}): any {
    const node = createNode(nodeType, {
      id: nodeStore.generateNodeId(),
      x: position.x,
      y: position.y,
      ...properties,
    })

    const addedNode = workflowStore.addNode(nodeType, position, node)
    selectionStore.selectNodes([addedNode.id], 'replace')

    return addedNode
  }

  function createNodeFromTemplate(templateId: string, position: Point): any {
    return nodeStore.createNodeFromTemplate(templateId, position)
  }

  function cancelNodeCreation(): void {
    nodeState.creating.active = false
    nodeState.creating.nodeType = null
    nodeState.creating.position = { x: 0, y: 0 }
    nodeState.creating.properties = {}
  }

  function deleteNode(nodeId: string): boolean {
    return workflowStore.removeNode(nodeId)
  }

  function deleteNodes(nodeIds: string[]): number {
    let count = 0
    nodeIds.forEach((id) => {
      if (workflowStore.removeNode(id)) count++
    })
    return count
  }

  function duplicateNode(nodeId: string, offset: Point = { x: 20, y: 20 }): any | null {
    const node = workflowStore.getNodeById(nodeId)
    if (!node) return null

    return createNodeAt(node.type, {
      x: node.x + offset.x,
      y: node.y + offset.y,
    }, { ...node })
  }

  function copyNodes(nodeIds: string[]): void {
    nodeState.clipboard.nodes = nodeIds.map((id) => workflowStore.getNodeById(id)).filter(Boolean)
    nodeState.clipboard.operation = 'copy'
  }

  function cutNodes(nodeIds: string[]): void {
    nodeState.clipboard.nodes = nodeIds.map((id) => workflowStore.getNodeById(id)).filter(Boolean)
    nodeState.clipboard.operation = 'cut'
  }

  function pasteNodes(position: Point): any[] {
    const pastedNodes = nodeState.clipboard.nodes.map((node: any) =>
      createNodeAt(node.type, position, { ...node })
    )

    if (nodeState.clipboard.operation === 'cut') {
      nodeState.clipboard.nodes.forEach((node: any) => deleteNode(node.id))
    }

    nodeState.clipboard = { nodes: [], connections: [], operation: null }
    return pastedNodes
  }

  function searchNodes(query: string): void {
    nodeState.search.query = query
  }

  function setSearchFilters(filters: Partial<SearchFilters>): void {
    Object.assign(nodeState.search.filters, filters)
  }

  function clearSearchFilters(): void {
    nodeState.search.filters = { type: [], status: [], category: [] }
  }

  return {
    nodeState,
    nodes,
    selectedNodes,
    selectedNodeObjects,
    nodesByType,
    nodesByCategory,
    invalidNodes,
    orphanNodes,
    searchResults,
    startNodeCreation,
    createNodeAt,
    createNodeFromTemplate,
    cancelNodeCreation,
    deleteNode,
    deleteNodes,
    duplicateNode,
    copyNodes,
    cutNodes,
    pasteNodes,
    searchNodes,
    setSearchFilters,
    clearSearchFilters,
  }
}

export type { Point, Size, NodeState, CreatingState, EditingState, DraggingState, ResizingState, ClipboardState, SearchState }

