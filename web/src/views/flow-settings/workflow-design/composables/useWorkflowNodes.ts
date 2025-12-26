/**
 * 工作流节点管理组合式函数
 * 提供节点的创建、编辑、删除、复制等功能
 */

import { ref, computed, reactive, nextTick, type ComputedRef } from 'vue'
import { useWorkflowStore } from '../stores/workflowStore'

// ========== 类型定义 ==========

interface Point { x: number; y: number }
interface Size { width: number; height: number }

interface DraggingState {
  active: boolean
  nodeId: string | null
  startPosition: Point
  offset: Point
  multiSelect: boolean
}

interface ResizingState {
  active: boolean
  nodeId: string | null
  handle: string | null
  startSize: Size
  startPosition: Point
  startMouse: Point
}

interface EditingState {
  active: boolean
  nodeId: string | null
  field: string | null
}

interface ConnectingState {
  active: boolean
  sourceNodeId: string | null
  sourcePoint: any | null
  targetNodeId: string | null
  targetPoint: any | null
}

interface HoveringState {
  nodeId: string | null
  connectionPoint: any | null
}

interface ClipboardState {
  nodes: any[]
  connections: any[]
}

interface NodeState {
  dragging: DraggingState
  resizing: ResizingState
  editing: EditingState
  connecting: ConnectingState
  hovering: HoveringState
  clipboard: ClipboardState
}

interface NodeConfig {
  width: number
  height: number
  minWidth: number
  minHeight: number
  maxWidth: number
  maxHeight: number
}

// ========== Composable ==========

export function useWorkflowNodes() {
  const workflowStore = useWorkflowStore()

  const nodeState = reactive<NodeState>({
    dragging: {
      active: false,
      nodeId: null,
      startPosition: { x: 0, y: 0 },
      offset: { x: 0, y: 0 },
      multiSelect: false,
    },
    resizing: {
      active: false,
      nodeId: null,
      handle: null,
      startSize: { width: 0, height: 0 },
      startPosition: { x: 0, y: 0 },
      startMouse: { x: 0, y: 0 },
    },
    editing: {
      active: false,
      nodeId: null,
      field: null,
    },
    connecting: {
      active: false,
      sourceNodeId: null,
      sourcePoint: null,
      targetNodeId: null,
      targetPoint: null,
    },
    hovering: {
      nodeId: null,
      connectionPoint: null,
    },
    clipboard: {
      nodes: [],
      connections: [],
    },
  })

  const defaultNodeConfig: NodeConfig = {
    width: 200,
    height: 100,
    minWidth: 120,
    minHeight: 60,
    maxWidth: 400,
    maxHeight: 300,
  }

  const selectedNodes: ComputedRef<any[]> = computed(() =>
    workflowStore.nodes.filter((node: any) => workflowStore.selectedNodeIds.includes(node.id))
  )

  const draggingNodes: ComputedRef<any[]> = computed(() => {
    if (!nodeState.dragging.active) return []

    if (nodeState.dragging.multiSelect) {
      return selectedNodes.value
    } else {
      const node = workflowStore.getNodeById(nodeState.dragging.nodeId)
      return node ? [node] : []
    }
  })

  function createNode(type: string, position: Point, config: any = {}): any | null {
    const nodeId = `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    const newNode = {
      id: nodeId,
      type,
      position: { ...position },
      width: config.width || defaultNodeConfig.width,
      height: config.height || defaultNodeConfig.height,
      data: {
        label: config.label || type,
        ...config.data,
      },
      style: {
        ...config.style,
      },
      connectionPoints: [],
      validation: {
        isValid: true,
        errors: [],
      },
      metadata: {
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        version: 1,
      },
    }

    workflowStore.addNode(newNode)
    return newNode
  }

  function duplicateNode(nodeId: string, offset: Point = { x: 20, y: 20 }): any | null {
    const originalNode = workflowStore.getNodeById(nodeId)
    if (!originalNode) return null

    const newPosition: Point = {
      x: originalNode.position.x + offset.x,
      y: originalNode.position.y + offset.y,
    }

    return createNode(originalNode.type, newPosition, {
      width: originalNode.width,
      height: originalNode.height,
      data: { ...originalNode.data },
      style: { ...originalNode.style },
    })
  }

  function duplicateNodes(nodeIds: string[], offset: Point = { x: 20, y: 20 }): any[] {
    return nodeIds.map((id) => duplicateNode(id, offset)).filter(Boolean)
  }

  function deleteNode(nodeId: string): boolean {
    return workflowStore.removeNode(nodeId)
  }

  function deleteNodes(nodeIds: string[]): number {
    let deletedCount = 0
    nodeIds.forEach((id) => {
      if (workflowStore.removeNode(id)) {
        deletedCount++
      }
    })
    return deletedCount
  }

  function updateNodePosition(nodeId: string, position: Point): boolean {
    return workflowStore.updateNodePosition(nodeId, position)
  }

  function updateNodeSize(nodeId: string, size: Size): boolean {
    const node = workflowStore.getNodeById(nodeId)
    if (!node) return false

    node.width = Math.max(defaultNodeConfig.minWidth, Math.min(defaultNodeConfig.maxWidth, size.width))
    node.height = Math.max(defaultNodeConfig.minHeight, Math.min(defaultNodeConfig.maxHeight, size.height))

    return true
  }

  function startDragging(nodeId: string, startPosition: Point, multiSelect: boolean = false): void {
    nodeState.dragging = {
      active: true,
      nodeId,
      startPosition,
      offset: { x: 0, y: 0 },
      multiSelect,
    }
  }

  function updateDragging(currentPosition: Point): void {
    if (!nodeState.dragging.active) return

    nodeState.dragging.offset = {
      x: currentPosition.x - nodeState.dragging.startPosition.x,
      y: currentPosition.y - nodeState.dragging.startPosition.y,
    }
  }

  function endDragging(): void {
    nodeState.dragging = {
      active: false,
      nodeId: null,
      startPosition: { x: 0, y: 0 },
      offset: { x: 0, y: 0 },
      multiSelect: false,
    }
  }

  function startResizing(nodeId: string, handle: string, startMouse: Point): void {
    const node = workflowStore.getNodeById(nodeId)
    if (!node) return

    nodeState.resizing = {
      active: true,
      nodeId,
      handle,
      startSize: { width: node.width, height: node.height },
      startPosition: { ...node.position },
      startMouse,
    }
  }

  function updateResizing(currentMouse: Point): void {
    if (!nodeState.resizing.active || !nodeState.resizing.nodeId) return

    const deltaX = currentMouse.x - nodeState.resizing.startMouse.x
    const deltaY = currentMouse.y - nodeState.resizing.startMouse.y

    let newWidth = nodeState.resizing.startSize.width
    let newHeight = nodeState.resizing.startSize.height

    if (nodeState.resizing.handle?.includes('e')) newWidth += deltaX
    if (nodeState.resizing.handle?.includes('w')) newWidth -= deltaX
    if (nodeState.resizing.handle?.includes('s')) newHeight += deltaY
    if (nodeState.resizing.handle?.includes('n')) newHeight -= deltaY

    updateNodeSize(nodeState.resizing.nodeId, { width: newWidth, height: newHeight })
  }

  function endResizing(): void {
    nodeState.resizing = {
      active: false,
      nodeId: null,
      handle: null,
      startSize: { width: 0, height: 0 },
      startPosition: { x: 0, y: 0 },
      startMouse: { x: 0, y: 0 },
    }
  }

  return {
    nodeState,
    defaultNodeConfig,
    selectedNodes,
    draggingNodes,
    createNode,
    duplicateNode,
    duplicateNodes,
    deleteNode,
    deleteNodes,
    updateNodePosition,
    updateNodeSize,
    startDragging,
    updateDragging,
    endDragging,
    startResizing,
    updateResizing,
    endResizing,
  }
}

export type { Point, Size, NodeState, NodeConfig }

