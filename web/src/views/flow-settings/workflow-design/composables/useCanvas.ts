/**
 * 画布管理组合函数
 * Canvas management composable
 */

import { ref, computed, reactive, watch, nextTick, type Ref, type ComputedRef } from 'vue'
import { useCanvasStore } from '../stores/canvasStore.js'
import { useWorkflowStore } from '../stores/workflowStore.js'
import { useSelectionStore } from '../stores/selectionStore.js'
import { screenToCanvas, canvasToScreen, calculateDistance } from '../utils/coordinateUtils.js'
import { snapToGrid, getGridSize } from '../utils/gridUtils.js'

// ========== 类型定义 ==========

/** 交互模式 */
type InteractionMode = 'select' | 'pan' | 'connect' | 'draw'

/** 工具类型 */
type Tool = 'pointer' | 'hand' | 'connection'

/** 元素类型 */
type ElementType = 'node' | 'connection'

/** 坐标点 */
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

/** 视口状态 */
interface ViewportState {
  width: number
  height: number
  centerX: number
  centerY: number
}

/** 交互状态 */
interface InteractionState {
  mode: InteractionMode
  tool: Tool
  isActive: boolean
}

/** 拖拽状态 */
interface DraggingState {
  active: boolean
  startX: number
  startY: number
  currentX: number
  currentY: number
  deltaX: number
  deltaY: number
}

/** 选择状态 */
interface SelectionState {
  active: boolean
  startX: number
  startY: number
  endX: number
  endY: number
  rect: Rectangle | null
}

/** 缩放状态 */
interface ZoomState {
  min: number
  max: number
  step: number
  sensitivity: number
}

/** 网格状态 */
interface GridState {
  enabled: boolean
  size: number
  snap: boolean
  visible: boolean
}

/** 性能状态 */
interface PerformanceState {
  fps: number
  lastFrameTime: number
  frameCount: number
}

/** 画布状态 */
interface CanvasState {
  viewport: ViewportState
  interaction: InteractionState
  dragging: DraggingState
  selection: SelectionState
  zoom: ZoomState
  grid: GridState
  performance: PerformanceState
}

/** 元素结果 */
interface ElementResult {
  type: ElementType
  element: any
}

// ========== Composable ==========

export function useCanvas(canvasRef: Ref<HTMLElement | null>) {
  // 获取stores
  const canvasStore = useCanvasStore()
  const workflowStore = useWorkflowStore()
  const selectionStore = useSelectionStore()

  // 画布状态
  const canvasState = reactive<CanvasState>({
    // 视口状态
    viewport: {
      width: 0,
      height: 0,
      centerX: 0,
      centerY: 0,
    },

    // 交互状态
    interaction: {
      mode: 'select',
      tool: 'pointer',
      isActive: false,
    },

    // 拖拽状态
    dragging: {
      active: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0,
      deltaX: 0,
      deltaY: 0,
    },

    // 选择状态
    selection: {
      active: false,
      startX: 0,
      startY: 0,
      endX: 0,
      endY: 0,
      rect: null,
    },

    // 缩放状态
    zoom: {
      min: 0.1,
      max: 5,
      step: 0.1,
      sensitivity: 0.001,
    },

    // 网格状态
    grid: {
      enabled: true,
      size: 20,
      snap: true,
      visible: true,
    },

    // 性能状态
    performance: {
      fps: 60,
      lastFrameTime: 0,
      frameCount: 0,
    },
  })

  // 计算属性
  const transform: ComputedRef<any> = computed(() => canvasStore.transform)
  const canvasSize: ComputedRef<any> = computed(() => canvasStore.canvasSize)
  const viewportBounds: ComputedRef<any> = computed(() => canvasStore.viewportBounds)
  const isGridVisible: ComputedRef<boolean> = computed(
    () => canvasState.grid.visible && transform.value.scale > 0.5
  )

  const selectionRect: ComputedRef<Rectangle | null> = computed(() => {
    if (!canvasState.selection.active) return null

    const startX = Math.min(canvasState.selection.startX, canvasState.selection.endX)
    const startY = Math.min(canvasState.selection.startY, canvasState.selection.endY)
    const endX = Math.max(canvasState.selection.startX, canvasState.selection.endX)
    const endY = Math.max(canvasState.selection.startY, canvasState.selection.endY)

    return {
      x: startX,
      y: startY,
      width: endX - startX,
      height: endY - startY,
    }
  })

  const visibleNodes: ComputedRef<any[]> = computed(() => {
    const bounds = viewportBounds.value
    return workflowStore.nodes.filter((node: any) => {
      const nodeRight = node.x + (node.width || 200)
      const nodeBottom = node.y + (node.height || 100)

      return !(
        node.x > bounds.right ||
        nodeRight < bounds.left ||
        node.y > bounds.bottom ||
        nodeBottom < bounds.top
      )
    })
  })

  const visibleConnections: ComputedRef<any[]> = computed(() => {
    const bounds = viewportBounds.value
    return workflowStore.connections.filter((conn: any) => {
      const fromNode = workflowStore.getNodeById(conn.fromNodeId)
      const toNode = workflowStore.getNodeById(conn.toNodeId)

      if (!fromNode || !toNode) return false

      const minX = Math.min(fromNode.x, toNode.x)
      const maxX = Math.max(fromNode.x + (fromNode.width || 200), toNode.x + (toNode.width || 200))
      const minY = Math.min(fromNode.y, toNode.y)
      const maxY = Math.max(
        fromNode.y + (fromNode.height || 100),
        toNode.y + (toNode.height || 100)
      )

      return !(
        minX > bounds.right ||
        maxX < bounds.left ||
        minY > bounds.bottom ||
        maxY < bounds.top
      )
    })
  })

  // 坐标转换
  function screenToCanvasCoords(screenX: number, screenY: number): Point {
    return screenToCanvas({ x: screenX, y: screenY }, transform.value, canvasState.viewport)
  }

  function canvasToScreenCoords(canvasX: number, canvasY: number): Point {
    return canvasToScreen({ x: canvasX, y: canvasY }, transform.value, canvasState.viewport)
  }

  // 视口操作
  function updateViewport(): void {
    if (!canvasRef.value) return

    const rect = canvasRef.value.getBoundingClientRect()
    canvasState.viewport.width = rect.width
    canvasState.viewport.height = rect.height
    canvasState.viewport.centerX = rect.width / 2
    canvasState.viewport.centerY = rect.height / 2

    canvasStore.updateViewport({
      width: rect.width,
      height: rect.height,
    })
  }

  function centerView(): void {
    const nodes = workflowStore.nodes
    if (nodes.length === 0) {
      canvasStore.resetTransform()
      return
    }

    const bounds = calculateNodesBounds(nodes)
    const centerX = bounds.x + bounds.width / 2
    const centerY = bounds.y + bounds.height / 2

    canvasStore.setTransform({
      translateX: canvasState.viewport.centerX - centerX * transform.value.scale,
      translateY: canvasState.viewport.centerY - centerY * transform.value.scale,
    })
  }

  function fitToView(padding: number = 50): void {
    const nodes = workflowStore.nodes
    if (nodes.length === 0) {
      canvasStore.resetTransform()
      return
    }

    const bounds = calculateNodesBounds(nodes)
    const viewportWidth = canvasState.viewport.width - padding * 2
    const viewportHeight = canvasState.viewport.height - padding * 2

    const scaleX = viewportWidth / bounds.width
    const scaleY = viewportHeight / bounds.height
    const scale = Math.min(scaleX, scaleY, canvasState.zoom.max)

    const centerX = bounds.x + bounds.width / 2
    const centerY = bounds.y + bounds.height / 2

    canvasStore.setTransform({
      scale: Math.max(scale, canvasState.zoom.min),
      translateX: canvasState.viewport.centerX - centerX * scale,
      translateY: canvasState.viewport.centerY - centerY * scale,
    })
  }

  function resetView(): void {
    canvasStore.resetTransform()
  }

  // 缩放操作
  function zoomIn(factor: number = 1.2): void {
    const newScale = Math.min(transform.value.scale * factor, canvasState.zoom.max)
    zoomToPoint(canvasState.viewport.centerX, canvasState.viewport.centerY, newScale)
  }

  function zoomOut(factor: number = 0.8): void {
    const newScale = Math.max(transform.value.scale * factor, canvasState.zoom.min)
    zoomToPoint(canvasState.viewport.centerX, canvasState.viewport.centerY, newScale)
  }

  function zoomToPoint(screenX: number, screenY: number, newScale: number): void {
    const canvasPoint = screenToCanvasCoords(screenX, screenY)

    canvasStore.setTransform({
      scale: newScale,
      translateX: screenX - canvasPoint.x * newScale,
      translateY: screenY - canvasPoint.y * newScale,
    })
  }

  function handleWheel(event: WheelEvent): void {
    event.preventDefault()

    if (!canvasRef.value) return
    const rect = canvasRef.value.getBoundingClientRect()
    const screenX = event.clientX - rect.left
    const screenY = event.clientY - rect.top

    const delta = -event.deltaY * canvasState.zoom.sensitivity
    const newScale = Math.max(
      canvasState.zoom.min,
      Math.min(canvasState.zoom.max, transform.value.scale * (1 + delta))
    )

    zoomToPoint(screenX, screenY, newScale)
  }

  // 平移操作
  function pan(deltaX: number, deltaY: number): void {
    canvasStore.setTransform({
      translateX: transform.value.translateX + deltaX,
      translateY: transform.value.translateY + deltaY,
    })
  }

  function startPan(screenX: number, screenY: number): void {
    canvasState.dragging.active = true
    canvasState.dragging.startX = screenX
    canvasState.dragging.startY = screenY
    canvasState.dragging.currentX = screenX
    canvasState.dragging.currentY = screenY
    canvasState.interaction.mode = 'pan'
  }

  function updatePan(screenX: number, screenY: number): void {
    if (!canvasState.dragging.active) return

    const deltaX = screenX - canvasState.dragging.currentX
    const deltaY = screenY - canvasState.dragging.currentY

    pan(deltaX, deltaY)

    canvasState.dragging.currentX = screenX
    canvasState.dragging.currentY = screenY
    canvasState.dragging.deltaX = deltaX
    canvasState.dragging.deltaY = deltaY
  }

  function endPan(): void {
    canvasState.dragging.active = false
    canvasState.interaction.mode = 'select'
  }

  // 选择操作
  function startSelection(screenX: number, screenY: number): void {
    const canvasPoint = screenToCanvasCoords(screenX, screenY)

    canvasState.selection.active = true
    canvasState.selection.startX = canvasPoint.x
    canvasState.selection.startY = canvasPoint.y
    canvasState.selection.endX = canvasPoint.x
    canvasState.selection.endY = canvasPoint.y
  }

  function updateSelection(screenX: number, screenY: number): void {
    if (!canvasState.selection.active) return

    const canvasPoint = screenToCanvasCoords(screenX, screenY)
    canvasState.selection.endX = canvasPoint.x
    canvasState.selection.endY = canvasPoint.y
  }

  function endSelection(): void {
    if (!canvasState.selection.active) return

    const rect = selectionRect.value
    if (rect && (rect.width > 5 || rect.height > 5)) {
      const selectedNodeIds = workflowStore.nodes
        .filter((node: any) => {
          const nodeRight = node.x + (node.width || 200)
          const nodeBottom = node.y + (node.height || 100)

          return (
            node.x < rect.x + rect.width &&
            nodeRight > rect.x &&
            node.y < rect.y + rect.height &&
            nodeBottom > rect.y
          )
        })
        .map((node: any) => node.id)

      selectionStore.selectNodes(selectedNodeIds, 'replace')
    }

    canvasState.selection.active = false
  }

  function cancelSelection(): void {
    canvasState.selection.active = false
  }

  // 网格操作
  function toggleGrid(): void {
    canvasState.grid.visible = !canvasState.grid.visible
    canvasStore.updateGridSettings({ visible: canvasState.grid.visible })
  }

  function toggleGridSnap(): void {
    canvasState.grid.snap = !canvasState.grid.snap
    canvasStore.updateGridSettings({ snap: canvasState.grid.snap })
  }

  function setGridSize(size: number): void {
    canvasState.grid.size = size
    canvasStore.updateGridSettings({ size })
  }

  function snapPointToGrid(point: Point): Point {
    if (!canvasState.grid.snap) return point
    return snapToGrid(point, canvasState.grid.size)
  }

  // 工具函数
  function calculateNodesBounds(nodes: any[]): Rectangle {
    if (nodes.length === 0) {
      return { x: 0, y: 0, width: 0, height: 0 }
    }

    let minX = Infinity,
      minY = Infinity
    let maxX = -Infinity,
      maxY = -Infinity

    nodes.forEach((node: any) => {
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

  function getElementAtPoint(canvasX: number, canvasY: number): ElementResult | null {
    // 检查节点
    for (const node of workflowStore.nodes) {
      const nodeWidth = node.width || 200
      const nodeHeight = node.height || 100

      if (
        canvasX >= node.x &&
        canvasX <= node.x + nodeWidth &&
        canvasY >= node.y &&
        canvasY <= node.y + nodeHeight
      ) {
        return { type: 'node', element: node }
      }
    }

    // 检查连接
    for (const connection of workflowStore.connections) {
      const fromNode = workflowStore.getNodeById(connection.fromNodeId)
      const toNode = workflowStore.getNodeById(connection.toNodeId)

      if (fromNode && toNode) {
        const fromPoint: Point = {
          x: fromNode.x + (fromNode.width || 200),
          y: fromNode.y + (fromNode.height || 100) / 2,
        }
        const toPoint: Point = {
          x: toNode.x,
          y: toNode.y + (toNode.height || 100) / 2,
        }

        const distance = distanceToLine(
          canvasX,
          canvasY,
          fromPoint.x,
          fromPoint.y,
          toPoint.x,
          toPoint.y
        )
        if (distance < 10) {
          return { type: 'connection', element: connection }
        }
      }
    }

    return null
  }

  function distanceToLine(
    px: number,
    py: number,
    x1: number,
    y1: number,
    x2: number,
    y2: number
  ): number {
    const A = px - x1
    const B = py - y1
    const C = x2 - x1
    const D = y2 - y1

    const dot = A * C + B * D
    const lenSq = C * C + D * D

    if (lenSq === 0) return Math.sqrt(A * A + B * B)

    let param = dot / lenSq
    let xx: number, yy: number

    if (param < 0) {
      xx = x1
      yy = y1
    } else if (param > 1) {
      xx = x2
      yy = y2
    } else {
      xx = x1 + param * C
      yy = y1 + param * D
    }

    const dx = px - xx
    const dy = py - yy
    return Math.sqrt(dx * dx + dy * dy)
  }

  // 性能监控
  function updatePerformance(): void {
    const now = performance.now()
    const deltaTime = now - canvasState.performance.lastFrameTime

    if (deltaTime > 0) {
      canvasState.performance.fps = Math.round(1000 / deltaTime)
    }

    canvasState.performance.lastFrameTime = now
    canvasState.performance.frameCount++
  }

  // 事件处理
  function handleMouseDown(event: MouseEvent): void {
    if (!canvasRef.value) return
    const rect = canvasRef.value.getBoundingClientRect()
    const screenX = event.clientX - rect.left
    const screenY = event.clientY - rect.top

    if (event.button === 1 || (event.button === 0 && event.ctrlKey)) {
      startPan(screenX, screenY)
    } else if (event.button === 0) {
      const canvasPoint = screenToCanvasCoords(screenX, screenY)
      const element = getElementAtPoint(canvasPoint.x, canvasPoint.y)

      if (!element) {
        startSelection(screenX, screenY)
      }
    }
  }

  function handleMouseMove(event: MouseEvent): void {
    if (!canvasRef.value) return
    const rect = canvasRef.value.getBoundingClientRect()
    const screenX = event.clientX - rect.left
    const screenY = event.clientY - rect.top

    if (canvasState.dragging.active && canvasState.interaction.mode === 'pan') {
      updatePan(screenX, screenY)
    } else if (canvasState.selection.active) {
      updateSelection(screenX, screenY)
    }

    updatePerformance()
  }

  function handleMouseUp(event: MouseEvent): void {
    if (canvasState.dragging.active && canvasState.interaction.mode === 'pan') {
      endPan()
    } else if (canvasState.selection.active) {
      endSelection()
    }
  }

  // 键盘事件
  function handleKeyDown(event: KeyboardEvent): void {
    switch (event.key) {
      case ' ':
        if (!canvasState.dragging.active) {
          canvasState.interaction.tool = 'hand'
        }
        break
      case 'Escape':
        cancelSelection()
        break
      case '0':
        if (event.ctrlKey) {
          event.preventDefault()
          fitToView()
        }
        break
      case '=':
      case '+':
        if (event.ctrlKey) {
          event.preventDefault()
          zoomIn()
        }
        break
      case '-':
        if (event.ctrlKey) {
          event.preventDefault()
          zoomOut()
        }
        break
    }
  }

  function handleKeyUp(event: KeyboardEvent): void {
    switch (event.key) {
      case ' ':
        canvasState.interaction.tool = 'pointer'
        break
    }
  }

  // 初始化和清理
  function initializeCanvas(): void {
    nextTick(() => {
      updateViewport()
    })

    window.addEventListener('resize', updateViewport)
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('keyup', handleKeyUp)
  }

  function destroyCanvas(): void {
    window.removeEventListener('resize', updateViewport)
    document.removeEventListener('keydown', handleKeyDown)
    document.removeEventListener('keyup', handleKeyUp)
  }

  return {
    // 状态
    canvasState,
    transform,
    canvasSize,
    viewportBounds,
    isGridVisible,
    selectionRect,
    visibleNodes,
    visibleConnections,

    // 坐标转换
    screenToCanvasCoords,
    canvasToScreenCoords,

    // 视口操作
    updateViewport,
    centerView,
    fitToView,
    resetView,

    // 缩放操作
    zoomIn,
    zoomOut,
    zoomToPoint,
    handleWheel,

    // 平移操作
    pan,
    startPan,
    updatePan,
    endPan,

    // 选择操作
    startSelection,
    updateSelection,
    endSelection,
    cancelSelection,

    // 网格操作
    toggleGrid,
    toggleGridSnap,
    setGridSize,
    snapPointToGrid,

    // 工具函数
    calculateNodesBounds,
    getElementAtPoint,
    updatePerformance,

    // 事件处理
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleKeyDown,
    handleKeyUp,

    // 生命周期
    initializeCanvas,
    destroyCanvas,
  }
}

// ========== 导出类型 ==========

export type {
  InteractionMode,
  Tool,
  ElementType,
  Point,
  Rectangle,
  ViewportState,
  InteractionState,
  DraggingState,
  SelectionState,
  ZoomState,
  GridState,
  PerformanceState,
  CanvasState,
  ElementResult,
}

