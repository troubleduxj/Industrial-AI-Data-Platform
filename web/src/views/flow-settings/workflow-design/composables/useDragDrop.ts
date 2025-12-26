/**
 * 拖拽操作组合函数
 * Drag and drop operations composable
 */

import { ref, reactive, computed, nextTick, type Ref, type ComputedRef } from 'vue'
import { useNodeStore } from '../stores/nodeStore.js'
import { useConnectionStore } from '../stores/connectionStore.js'
import { useWorkflowStore } from '../stores/workflowStore.js'
import { useSelectionStore } from '../stores/selectionStore.js'
import { useCanvasStore } from '../stores/canvasStore.js'
import { snapToGrid } from '../utils/gridUtils.js'
import { screenToCanvas, canvasToScreen } from '../utils/coordinateUtils.js'

// ========== 类型定义 ==========

interface Point { x: number; y: number }
interface Rectangle { x: number; y: number; width: number; height: number }

type DragType = 'node' | 'connection' | 'selection' | 'canvas' | 'library-item' | null
type SelectionMode = 'replace' | 'add' | 'remove'

interface NodeDragState {
  active: boolean
  nodeIds: string[]
  startPositions: Map<string, Point>
  ghostNodes: any[]
  snapToGrid: boolean
  constrainToCanvas: boolean
}

interface ConnectionDragState {
  active: boolean
  sourceNodeId: string | null
  sourcePortId: string | null
  targetNodeId: string | null
  targetPortId: string | null
  tempConnection: any | null
  validTargets: any[]
  showPreview: boolean
}

interface SelectionDragState {
  active: boolean
  startPoint: Point
  currentRect: Rectangle
  mode: SelectionMode
}

interface CanvasDragState {
  active: boolean
  startViewport: Point
  momentum: Point
  inertia: boolean
}

interface LibraryItemDragState {
  active: boolean
  itemType: string | null
  itemData: any | null
  preview: any | null
  canDrop: boolean
  dropZone: any | null
}

interface DragState {
  isDragging: boolean
  dragType: DragType
  startPosition: Point
  currentPosition: Point
  offset: Point
  node: NodeDragState
  connection: ConnectionDragState
  selection: SelectionDragState
  canvas: CanvasDragState
  libraryItem: LibraryItemDragState
}

// ========== Composable ==========

export function useDragDrop() {
  const nodeStore = useNodeStore()
  const connectionStore = useConnectionStore()
  const workflowStore = useWorkflowStore()
  const selectionStore = useSelectionStore()
  const canvasStore = useCanvasStore()

  const dragState = reactive<DragState>({
    isDragging: false,
    dragType: null,
    startPosition: { x: 0, y: 0 },
    currentPosition: { x: 0, y: 0 },
    offset: { x: 0, y: 0 },

    node: {
      active: false,
      nodeIds: [],
      startPositions: new Map(),
      ghostNodes: [],
      snapToGrid: true,
      constrainToCanvas: true,
    },

    connection: {
      active: false,
      sourceNodeId: null,
      sourcePortId: null,
      targetNodeId: null,
      targetPortId: null,
      tempConnection: null,
      validTargets: [],
      showPreview: true,
    },

    selection: {
      active: false,
      startPoint: { x: 0, y: 0 },
      currentRect: { x: 0, y: 0, width: 0, height: 0 },
      mode: 'replace',
    },

    canvas: {
      active: false,
      startViewport: { x: 0, y: 0 },
      momentum: { x: 0, y: 0 },
      inertia: false,
    },

    libraryItem: {
      active: false,
      itemType: null,
      itemData: null,
      preview: null,
      canDrop: false,
      dropZone: null,
    },
  })

  const isDragging: ComputedRef<boolean> = computed(() => dragState.isDragging)
  const dragType: ComputedRef<DragType> = computed(() => dragState.dragType)
  const canDrop: ComputedRef<boolean> = computed(() => {
    switch (dragState.dragType) {
      case 'library-item':
        return dragState.libraryItem.canDrop
      case 'connection':
        return !!(dragState.connection.targetNodeId && dragState.connection.targetPortId)
      default:
        return true
    }
  })

  function startDrag(type: DragType, event: MouseEvent, data: any = {}): void {
    dragState.isDragging = true
    dragState.dragType = type
    dragState.startPosition = getEventPosition(event)
    dragState.currentPosition = { ...dragState.startPosition }
    dragState.offset = { x: 0, y: 0 }

    switch (type) {
      case 'node':
        startNodeDrag(event, data)
        break
      case 'connection':
        startConnectionDrag(event, data)
        break
      case 'selection':
        startSelectionDrag(event, data)
        break
      case 'canvas':
        startCanvasDrag(event, data)
        break
      case 'library-item':
        startLibraryItemDrag(event, data)
        break
    }

    document.addEventListener('mousemove', handleDragMove)
    document.addEventListener('mouseup', handleDragEnd)
    document.addEventListener('keydown', handleDragKeyDown)

    event.preventDefault()
    event.stopPropagation()
  }

  function updateDrag(event: MouseEvent): void {
    if (!dragState.isDragging) return

    const currentPos = getEventPosition(event)
    dragState.currentPosition = currentPos
    dragState.offset = {
      x: currentPos.x - dragState.startPosition.x,
      y: currentPos.y - dragState.startPosition.y,
    }

    switch (dragState.dragType) {
      case 'node':
        updateNodeDrag(event)
        break
      case 'connection':
        updateConnectionDrag(event)
        break
      case 'selection':
        updateSelectionDrag(event)
        break
      case 'canvas':
        updateCanvasDrag(event)
        break
      case 'library-item':
        updateLibraryItemDrag(event)
        break
    }
  }

  function endDrag(event?: MouseEvent): void {
    if (!dragState.isDragging) return

    switch (dragState.dragType) {
      case 'node':
        endNodeDrag(event)
        break
      case 'connection':
        endConnectionDrag(event)
        break
      case 'selection':
        endSelectionDrag(event)
        break
      case 'canvas':
        endCanvasDrag(event)
        break
      case 'library-item':
        endLibraryItemDrag(event)
        break
    }

    resetDragState()
    removeEventListeners()
  }

  function cancelDrag(): void {
    resetDragState()
    removeEventListeners()
  }

  // 节点拖拽
  function startNodeDrag(event: MouseEvent, data: any): void {
    dragState.node.active = true
    dragState.node.nodeIds = data.nodeIds || []
    dragState.node.startPositions = new Map()

    dragState.node.nodeIds.forEach((nodeId: string) => {
      const node = workflowStore.getNodeById(nodeId)
      if (node) {
        dragState.node.startPositions.set(nodeId, { x: node.position.x, y: node.position.y })
      }
    })
  }

  function updateNodeDrag(event: MouseEvent): void {
    const { offset } = dragState
    dragState.node.nodeIds.forEach((nodeId: string) => {
      const startPos = dragState.node.startPositions.get(nodeId)
      if (startPos) {
        let newPos = { x: startPos.x + offset.x, y: startPos.y + offset.y }

        if (dragState.node.snapToGrid) {
          newPos = snapToGrid(newPos, 20)
        }

        workflowStore.updateNodePosition(nodeId, newPos)
      }
    })
  }

  function endNodeDrag(event?: MouseEvent): void {
    dragState.node = {
      active: false,
      nodeIds: [],
      startPositions: new Map(),
      ghostNodes: [],
      snapToGrid: true,
      constrainToCanvas: true,
    }
  }

  // 连接拖拽
  function startConnectionDrag(event: MouseEvent, data: any): void {
    dragState.connection.active = true
    dragState.connection.sourceNodeId = data.sourceNodeId || null
    dragState.connection.sourcePortId = data.sourcePortId || null
  }

  function updateConnectionDrag(event: MouseEvent): void {
    // 更新临时连接预览
    dragState.connection.tempConnection = {
      from: dragState.startPosition,
      to: dragState.currentPosition,
    }
  }

  function endConnectionDrag(event?: MouseEvent): void {
    if (dragState.connection.targetNodeId && dragState.connection.targetPortId) {
      workflowStore.addConnection({
        sourceNodeId: dragState.connection.sourceNodeId,
        sourcePortId: dragState.connection.sourcePortId,
        targetNodeId: dragState.connection.targetNodeId,
        targetPortId: dragState.connection.targetPortId,
      })
    }

    dragState.connection = {
      active: false,
      sourceNodeId: null,
      sourcePortId: null,
      targetNodeId: null,
      targetPortId: null,
      tempConnection: null,
      validTargets: [],
      showPreview: true,
    }
  }

  // 选择框拖拽
  function startSelectionDrag(event: MouseEvent, data: any): void {
    dragState.selection.active = true
    dragState.selection.startPoint = { ...dragState.startPosition }
    dragState.selection.mode = data.mode || 'replace'
  }

  function updateSelectionDrag(event: MouseEvent): void {
    const startX = Math.min(dragState.selection.startPoint.x, dragState.currentPosition.x)
    const startY = Math.min(dragState.selection.startPoint.y, dragState.currentPosition.y)
    const width = Math.abs(dragState.currentPosition.x - dragState.selection.startPoint.x)
    const height = Math.abs(dragState.currentPosition.y - dragState.selection.startPoint.y)

    dragState.selection.currentRect = { x: startX, y: startY, width, height }
  }

  function endSelectionDrag(event?: MouseEvent): void {
    const rect = dragState.selection.currentRect
    const selectedNodeIds = workflowStore.nodes
      .filter((node: any) => {
        return (
          node.position.x >= rect.x &&
          node.position.x + node.width <= rect.x + rect.width &&
          node.position.y >= rect.y &&
          node.position.y + node.height <= rect.y + rect.height
        )
      })
      .map((node: any) => node.id)

    selectionStore.selectNodes(selectedNodeIds, dragState.selection.mode)

    dragState.selection = {
      active: false,
      startPoint: { x: 0, y: 0 },
      currentRect: { x: 0, y: 0, width: 0, height: 0 },
      mode: 'replace',
    }
  }

  // 画布拖拽（平移）
  function startCanvasDrag(event: MouseEvent, data: any): void {
    dragState.canvas.active = true
    dragState.canvas.startViewport = {
      x: canvasStore.transform.translateX,
      y: canvasStore.transform.translateY,
    }
  }

  function updateCanvasDrag(event: MouseEvent): void {
    const newTranslate = {
      x: dragState.canvas.startViewport.x + dragState.offset.x,
      y: dragState.canvas.startViewport.y + dragState.offset.y,
    }

    canvasStore.setTransform({
      translateX: newTranslate.x,
      translateY: newTranslate.y,
    })
  }

  function endCanvasDrag(event?: MouseEvent): void {
    dragState.canvas = {
      active: false,
      startViewport: { x: 0, y: 0 },
      momentum: { x: 0, y: 0 },
      inertia: false,
    }
  }

  // 库项目拖拽
  function startLibraryItemDrag(event: MouseEvent, data: any): void {
    dragState.libraryItem.active = true
    dragState.libraryItem.itemType = data.itemType || null
    dragState.libraryItem.itemData = data.itemData || null
  }

  function updateLibraryItemDrag(event: MouseEvent): void {
    dragState.libraryItem.canDrop = true
  }

  function endLibraryItemDrag(event?: MouseEvent): void {
    if (dragState.libraryItem.canDrop && dragState.libraryItem.itemType) {
      const canvasPos = screenToCanvas(
        dragState.currentPosition,
        canvasStore.transform,
        canvasStore.viewport
      )

      workflowStore.addNode(dragState.libraryItem.itemType, canvasPos, dragState.libraryItem.itemData)
    }

    dragState.libraryItem = {
      active: false,
      itemType: null,
      itemData: null,
      preview: null,
      canDrop: false,
      dropZone: null,
    }
  }

  // 辅助函数
  function getEventPosition(event: MouseEvent): Point {
    return { x: event.clientX, y: event.clientY }
  }

  function resetDragState(): void {
    dragState.isDragging = false
    dragState.dragType = null
    dragState.startPosition = { x: 0, y: 0 }
    dragState.currentPosition = { x: 0, y: 0 }
    dragState.offset = { x: 0, y: 0 }
  }

  function removeEventListeners(): void {
    document.removeEventListener('mousemove', handleDragMove)
    document.removeEventListener('mouseup', handleDragEnd)
    document.removeEventListener('keydown', handleDragKeyDown)
  }

  function handleDragMove(event: MouseEvent): void {
    updateDrag(event)
  }

  function handleDragEnd(event: MouseEvent): void {
    endDrag(event)
  }

  function handleDragKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      cancelDrag()
    }
  }

  return {
    dragState,
    isDragging,
    dragType,
    canDrop,
    startDrag,
    updateDrag,
    endDrag,
    cancelDrag,
    startNodeDrag,
    updateNodeDrag,
    endNodeDrag,
    startConnectionDrag,
    updateConnectionDrag,
    endConnectionDrag,
    startSelectionDrag,
    updateSelectionDrag,
    endSelectionDrag,
    startCanvasDrag,
    updateCanvasDrag,
    endCanvasDrag,
    startLibraryItemDrag,
    updateLibraryItemDrag,
    endLibraryItemDrag,
  }
}

// ========== 导出类型 ==========

export type {
  Point,
  Rectangle,
  DragType,
  SelectionMode,
  NodeDragState,
  ConnectionDragState,
  SelectionDragState,
  CanvasDragState,
  LibraryItemDragState,
  DragState,
}

