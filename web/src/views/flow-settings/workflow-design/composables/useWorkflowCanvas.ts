/**
 * 工作流画布管理组合式函数
 * 提供画布的缩放、平移、选择等核心功能
 */

import { ref, computed, reactive, nextTick, type Ref, type ComputedRef } from 'vue'
import { useWorkflowStore } from '../stores/workflowStore'

// ========== 类型定义 ==========

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

/** 画布变换 */
interface Transform {
  x: number
  y: number
  scale: number
}

/** 画布尺寸 */
interface CanvasSize {
  width: number
  height: number
}

/** 网格设置 */
interface GridSettings {
  enabled: boolean
  size: number
  color: string
  strokeWidth: number
}

/** 对齐设置 */
interface SnapSettings {
  enabled: boolean
  threshold: number
}

/** 选择状态 */
interface SelectionState {
  enabled: boolean
  startX: number
  startY: number
  endX: number
  endY: number
}

/** 拖拽状态 */
interface DraggingState {
  active: boolean
  startX: number
  startY: number
  lastX: number
  lastY: number
}

/** 鼠标状态 */
interface MouseState {
  x: number
  y: number
  worldX: number
  worldY: number
}

/** 画布模式 */
type CanvasMode = 'select' | 'pan' | 'connect'

/** 画布状态 */
interface CanvasState {
  transform: Transform
  size: CanvasSize
  viewport: CanvasSize
  grid: GridSettings
  snap: SnapSettings
  selection: SelectionState
  dragging: DraggingState
  mode: CanvasMode
  mouse: MouseState
}

// ========== Composable ==========

export function useWorkflowCanvas() {
  const workflowStore = useWorkflowStore()

  // 画布状态
  const canvasState = reactive<CanvasState>({
    // 视口变换
    transform: {
      x: 0,
      y: 0,
      scale: 1,
    },

    // 画布尺寸
    size: {
      width: 5000,
      height: 5000,
    },

    // 视口尺寸
    viewport: {
      width: 0,
      height: 0,
    },

    // 网格设置
    grid: {
      enabled: true,
      size: 20,
      color: '#e8e8e8',
      strokeWidth: 1,
    },

    // 对齐设置
    snap: {
      enabled: true,
      threshold: 10,
    },

    // 选择状态
    selection: {
      enabled: false,
      startX: 0,
      startY: 0,
      endX: 0,
      endY: 0,
    },

    // 拖拽状态
    dragging: {
      active: false,
      startX: 0,
      startY: 0,
      lastX: 0,
      lastY: 0,
    },

    // 交互模式
    mode: 'select',

    // 鼠标状态
    mouse: {
      x: 0,
      y: 0,
      worldX: 0,
      worldY: 0,
    },
  })

  // 缩放限制
  const ZOOM_MIN = 0.1
  const ZOOM_MAX = 3
  const ZOOM_STEP = 0.1

  // 计算属性
  const transformStyle: ComputedRef<Record<string, string>> = computed(() => {
    return {
      transform: `translate(${canvasState.transform.x}px, ${canvasState.transform.y}px) scale(${canvasState.transform.scale})`,
      transformOrigin: '0 0',
    }
  })

  const selectionRect: ComputedRef<Rectangle | null> = computed(() => {
    if (!canvasState.selection.enabled) return null

    const x = Math.min(canvasState.selection.startX, canvasState.selection.endX)
    const y = Math.min(canvasState.selection.startY, canvasState.selection.endY)
    const width = Math.abs(canvasState.selection.endX - canvasState.selection.startX)
    const height = Math.abs(canvasState.selection.endY - canvasState.selection.startY)

    return { x, y, width, height }
  })

  const visibleBounds: ComputedRef<Rectangle> = computed(() => {
    const scale = canvasState.transform.scale
    const x = -canvasState.transform.x / scale
    const y = -canvasState.transform.y / scale
    const width = canvasState.viewport.width / scale
    const height = canvasState.viewport.height / scale

    return { x, y, width, height }
  })

  // 坐标转换
  function screenToWorld(screenX: number, screenY: number): Point {
    const scale = canvasState.transform.scale
    const worldX = (screenX - canvasState.transform.x) / scale
    const worldY = (screenY - canvasState.transform.y) / scale
    return { x: worldX, y: worldY }
  }

  function worldToScreen(worldX: number, worldY: number): Point {
    const scale = canvasState.transform.scale
    const screenX = worldX * scale + canvasState.transform.x
    const screenY = worldY * scale + canvasState.transform.y
    return { x: screenX, y: screenY }
  }

  // 缩放控制
  function zoomIn(centerX?: number | null, centerY?: number | null): void {
    zoom(canvasState.transform.scale + ZOOM_STEP, centerX, centerY)
  }

  function zoomOut(centerX?: number | null, centerY?: number | null): void {
    zoom(canvasState.transform.scale - ZOOM_STEP, centerX, centerY)
  }

  function zoom(newScale: number, centerX?: number | null, centerY?: number | null): void {
    const clampedScale = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, newScale))

    if (centerX !== null && centerX !== undefined && centerY !== null && centerY !== undefined) {
      // 以指定点为中心缩放
      const worldPoint = screenToWorld(centerX, centerY)

      canvasState.transform.scale = clampedScale

      const newScreenPoint = worldToScreen(worldPoint.x, worldPoint.y)
      canvasState.transform.x += centerX - newScreenPoint.x
      canvasState.transform.y += centerY - newScreenPoint.y
    } else {
      // 以画布中心缩放
      const centerX = canvasState.viewport.width / 2
      const centerY = canvasState.viewport.height / 2
      zoom(clampedScale, centerX, centerY)
    }
  }

  function zoomToFit(): void {
    const nodes = workflowStore.nodes
    if (nodes.length === 0) {
      resetView()
      return
    }

    // 计算所有节点的边界
    let minX = Infinity,
      minY = Infinity
    let maxX = -Infinity,
      maxY = -Infinity

    nodes.forEach((node: any) => {
      const x = node.position.x
      const y = node.position.y
      const width = node.width || 200
      const height = node.height || 100

      minX = Math.min(minX, x)
      minY = Math.min(minY, y)
      maxX = Math.max(maxX, x + width)
      maxY = Math.max(maxY, y + height)
    })

    // 添加边距
    const padding = 50
    minX -= padding
    minY -= padding
    maxX += padding
    maxY += padding

    const contentWidth = maxX - minX
    const contentHeight = maxY - minY

    // 计算合适的缩放比例
    const scaleX = canvasState.viewport.width / contentWidth
    const scaleY = canvasState.viewport.height / contentHeight
    const scale = Math.min(scaleX, scaleY, ZOOM_MAX)

    // 计算居中位置
    const centerX = (minX + maxX) / 2
    const centerY = (minY + maxY) / 2

    canvasState.transform.scale = scale
    canvasState.transform.x = canvasState.viewport.width / 2 - centerX * scale
    canvasState.transform.y = canvasState.viewport.height / 2 - centerY * scale
  }

  function resetView(): void {
    canvasState.transform.x = 0
    canvasState.transform.y = 0
    canvasState.transform.scale = 1
  }

  // 平移控制
  function pan(deltaX: number, deltaY: number): void {
    canvasState.transform.x += deltaX
    canvasState.transform.y += deltaY
  }

  function panTo(worldX: number, worldY: number): void {
    const centerX = canvasState.viewport.width / 2
    const centerY = canvasState.viewport.height / 2

    canvasState.transform.x = centerX - worldX * canvasState.transform.scale
    canvasState.transform.y = centerY - worldY * canvasState.transform.scale
  }

  // 网格对齐
  function snapToGrid(x: number, y: number): Point {
    if (!canvasState.snap.enabled) return { x, y }

    const gridSize = canvasState.grid.size
    const snappedX = Math.round(x / gridSize) * gridSize
    const snappedY = Math.round(y / gridSize) * gridSize

    return { x: snappedX, y: snappedY }
  }

  function snapToNodes(x: number, y: number, excludeNodeId?: string | null): Point {
    if (!canvasState.snap.enabled) return { x, y }

    const threshold = canvasState.snap.threshold
    let snappedX = x
    let snappedY = y

    workflowStore.nodes.forEach((node: any) => {
      if (node.id === excludeNodeId) return

      const nodeX = node.position.x
      const nodeY = node.position.y
      const nodeWidth = node.width || 200
      const nodeHeight = node.height || 100

      // 水平对齐
      if (Math.abs(x - nodeX) < threshold) {
        snappedX = nodeX
      } else if (Math.abs(x - (nodeX + nodeWidth)) < threshold) {
        snappedX = nodeX + nodeWidth
      } else if (Math.abs(x - (nodeX + nodeWidth / 2)) < threshold) {
        snappedX = nodeX + nodeWidth / 2
      }

      // 垂直对齐
      if (Math.abs(y - nodeY) < threshold) {
        snappedY = nodeY
      } else if (Math.abs(y - (nodeY + nodeHeight)) < threshold) {
        snappedY = nodeY + nodeHeight
      } else if (Math.abs(y - (nodeY + nodeHeight / 2)) < threshold) {
        snappedY = nodeY + nodeHeight / 2
      }
    })

    return { x: snappedX, y: snappedY }
  }

  // 选择控制
  function startSelection(screenX: number, screenY: number): void {
    const worldPos = screenToWorld(screenX, screenY)
    canvasState.selection.enabled = true
    canvasState.selection.startX = worldPos.x
    canvasState.selection.startY = worldPos.y
    canvasState.selection.endX = worldPos.x
    canvasState.selection.endY = worldPos.y
  }

  function updateSelection(screenX: number, screenY: number): void {
    if (!canvasState.selection.enabled) return

    const worldPos = screenToWorld(screenX, screenY)
    canvasState.selection.endX = worldPos.x
    canvasState.selection.endY = worldPos.y
  }

  function endSelection(): void {
    if (!canvasState.selection.enabled) return

    const rect = selectionRect.value
    if (rect && (rect.width > 5 || rect.height > 5)) {
      // 选择矩形内的节点
      const selectedNodes = workflowStore.nodes.filter((node: any) => {
        const nodeX = node.position.x
        const nodeY = node.position.y
        const nodeWidth = node.width || 200
        const nodeHeight = node.height || 100

        return (
          nodeX < rect.x + rect.width &&
          nodeX + nodeWidth > rect.x &&
          nodeY < rect.y + rect.height &&
          nodeY + nodeHeight > rect.y
        )
      })

      workflowStore.setSelectedNodes(selectedNodes.map((node: any) => node.id))
    }

    canvasState.selection.enabled = false
  }

  // 拖拽控制
  function startDrag(screenX: number, screenY: number): void {
    canvasState.dragging.active = true
    canvasState.dragging.startX = screenX
    canvasState.dragging.startY = screenY
    canvasState.dragging.lastX = screenX
    canvasState.dragging.lastY = screenY
  }

  function updateDrag(screenX: number, screenY: number): void {
    if (!canvasState.dragging.active) return

    const deltaX = screenX - canvasState.dragging.lastX
    const deltaY = screenY - canvasState.dragging.lastY

    if (canvasState.mode === 'pan') {
      pan(deltaX, deltaY)
    }

    canvasState.dragging.lastX = screenX
    canvasState.dragging.lastY = screenY
  }

  function endDrag(): void {
    canvasState.dragging.active = false
  }

  // 鼠标位置更新
  function updateMousePosition(screenX: number, screenY: number): void {
    canvasState.mouse.x = screenX
    canvasState.mouse.y = screenY

    const worldPos = screenToWorld(screenX, screenY)
    canvasState.mouse.worldX = worldPos.x
    canvasState.mouse.worldY = worldPos.y
  }

  // 模式切换
  function setMode(mode: CanvasMode): void {
    canvasState.mode = mode
  }

  // 网格设置
  function toggleGrid(): void {
    canvasState.grid.enabled = !canvasState.grid.enabled
  }

  function setGridSize(size: number): void {
    canvasState.grid.size = size
  }

  // 对齐设置
  function toggleSnap(): void {
    canvasState.snap.enabled = !canvasState.snap.enabled
  }

  function setSnapThreshold(threshold: number): void {
    canvasState.snap.threshold = threshold
  }

  // 视口尺寸更新
  function updateViewportSize(width: number, height: number): void {
    canvasState.viewport.width = width
    canvasState.viewport.height = height
  }

  // 获取画布边界
  function getCanvasBounds(): Rectangle {
    return {
      x: 0,
      y: 0,
      width: canvasState.size.width,
      height: canvasState.size.height,
    }
  }

  // 检查点是否在画布内
  function isPointInCanvas(worldX: number, worldY: number): boolean {
    return (
      worldX >= 0 &&
      worldX <= canvasState.size.width &&
      worldY >= 0 &&
      worldY <= canvasState.size.height
    )
  }

  // 自动布局
  function autoLayout(): void {
    const nodes = workflowStore.nodes
    if (nodes.length === 0) return

    // 简单的层次布局算法
    const layers: any[][] = []
    const visited = new Set<string>()
    const nodeMap = new Map<string, any>(nodes.map((node: any) => [node.id, node]))

    // 找到起始节点（没有输入连接的节点）
    const startNodes = nodes.filter((node: any) => {
      return !workflowStore.connections.some((conn: any) => conn.targetNodeId === node.id)
    })

    if (startNodes.length === 0) {
      // 如果没有明确的起始节点，选择第一个节点
      startNodes.push(nodes[0])
    }

    // 广度优先遍历构建层次
    let currentLayer = [...startNodes]
    while (currentLayer.length > 0) {
      layers.push([...currentLayer])
      currentLayer.forEach((node: any) => visited.add(node.id))

      const nextLayer: any[] = []
      currentLayer.forEach((node: any) => {
        workflowStore.connections
          .filter((conn: any) => conn.sourceNodeId === node.id)
          .forEach((conn: any) => {
            const targetNode = nodeMap.get(conn.targetNodeId)
            if (targetNode && !visited.has(targetNode.id) && !nextLayer.includes(targetNode)) {
              nextLayer.push(targetNode)
            }
          })
      })

      currentLayer = nextLayer
    }

    // 添加未访问的节点到最后一层
    const unvisited = nodes.filter((node: any) => !visited.has(node.id))
    if (unvisited.length > 0) {
      layers.push(unvisited)
    }

    // 计算布局
    const layerSpacing = 300
    const nodeSpacing = 150
    const startX = 100
    const startY = 100

    layers.forEach((layer: any[], layerIndex: number) => {
      const layerY = startY + layerIndex * layerSpacing
      const totalWidth = (layer.length - 1) * nodeSpacing
      const startLayerX = startX - totalWidth / 2

      layer.forEach((node: any, nodeIndex: number) => {
        const x = startLayerX + nodeIndex * nodeSpacing
        const y = layerY

        workflowStore.updateNodePosition(node.id, { x, y })
      })
    })

    // 自动适应视图
    nextTick(() => {
      zoomToFit()
    })
  }

  return {
    // 状态
    canvasState,
    transformStyle,
    selectionRect,
    visibleBounds,

    // 坐标转换
    screenToWorld,
    worldToScreen,

    // 缩放控制
    zoomIn,
    zoomOut,
    zoom,
    zoomToFit,
    resetView,

    // 平移控制
    pan,
    panTo,

    // 对齐功能
    snapToGrid,
    snapToNodes,

    // 选择控制
    startSelection,
    updateSelection,
    endSelection,

    // 拖拽控制
    startDrag,
    updateDrag,
    endDrag,

    // 鼠标位置
    updateMousePosition,

    // 模式切换
    setMode,

    // 网格设置
    toggleGrid,
    setGridSize,

    // 对齐设置
    toggleSnap,
    setSnapThreshold,

    // 视口管理
    updateViewportSize,
    getCanvasBounds,
    isPointInCanvas,

    // 布局
    autoLayout,
  }
}

// ========== 导出类型 ==========

export type {
  Point,
  Rectangle,
  Transform,
  CanvasSize,
  GridSettings,
  SnapSettings,
  SelectionState,
  DraggingState,
  MouseState,
  CanvasMode,
  CanvasState,
}

