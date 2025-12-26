/**
 * 网格工具函数
 * Grid utilities for snapping and alignment
 */

// ========== 类型定义 ==========

/** 点坐标 */
interface Point {
  x: number
  y: number
}

/** 视图框 */
interface ViewBox {
  x: number
  y: number
  width: number
  height: number
}

/** 网格线 */
interface GridLine {
  x1: number
  y1: number
  x2: number
  y2: number
}

/** 网格线集合 */
interface GridLines {
  verticalLines: GridLine[]
  horizontalLines: GridLine[]
}

/** 网格位置 */
interface GridPosition {
  gridX: number
  gridY: number
}

/** 对齐信息 */
interface AlignmentInfo {
  alignedX: boolean
  alignedY: boolean
}

/** 对齐辅助线 */
interface AlignmentGuide {
  type: 'horizontal' | 'vertical'
  x?: number
  y?: number
  x1?: number
  y1?: number
  x2?: number
  y2?: number
}

/** 节点（临时类型） */
interface WorkflowNode {
  id: string
  x: number
  y: number
  [key: string]: any
}

/** 网格配置 */
interface GridConfiguration {
  SIZE: number
  SNAP_THRESHOLD: number
  SHOW_GRID: boolean
  SNAP_ENABLED: boolean
}

// ========== 网格配置 ==========

/**
 * 网格配置常量
 */
export const GRID_CONFIG: GridConfiguration = {
  SIZE: 20, // 网格大小
  SNAP_THRESHOLD: 10, // 磁性吸附阈值
  SHOW_GRID: true, // 是否显示网格
  SNAP_ENABLED: true, // 是否启用磁性吸附
}

// ========== 网格对齐函数 ==========

/**
 * 将坐标对齐到网格
 * @param value - 坐标值
 * @param gridSize - 网格大小
 * @returns 对齐后的坐标值
 */
export function snapToGrid(value: number, gridSize: number = GRID_CONFIG.SIZE): number {
  return Math.round(value / gridSize) * gridSize
}

/**
 * 将点坐标对齐到网格
 * @param point - 点坐标 {x, y}
 * @param gridSize - 网格大小
 * @returns 对齐后的点坐标 {x, y}
 */
export function snapPointToGrid(point: Point, gridSize: number = GRID_CONFIG.SIZE): Point {
  return {
    x: snapToGrid(point.x, gridSize),
    y: snapToGrid(point.y, gridSize),
  }
}

// ========== 磁性吸附函数 ==========

/**
 * 检查是否应该进行磁性吸附
 * @param currentValue - 当前值
 * @param targetValue - 目标值
 * @param threshold - 吸附阈值
 * @returns 是否应该吸附
 */
export function shouldSnap(
  currentValue: number,
  targetValue: number,
  threshold: number = GRID_CONFIG.SNAP_THRESHOLD
): boolean {
  return Math.abs(currentValue - targetValue) < threshold
}

/**
 * 带磁性吸附的坐标对齐
 * @param value - 坐标值
 * @param gridSize - 网格大小
 * @param threshold - 吸附阈值
 * @returns 处理后的坐标值
 */
export function snapWithMagnetism(
  value: number,
  gridSize: number = GRID_CONFIG.SIZE,
  threshold: number = GRID_CONFIG.SNAP_THRESHOLD
): number {
  const snappedValue = snapToGrid(value, gridSize)

  if (shouldSnap(value, snappedValue, threshold)) {
    return snappedValue
  }

  return value
}

/**
 * 带磁性吸附的点坐标对齐
 * @param point - 点坐标 {x, y}
 * @param gridSize - 网格大小
 * @param threshold - 吸附阈值
 * @returns 处理后的点坐标 {x, y}
 */
export function snapPointWithMagnetism(
  point: Point,
  gridSize: number = GRID_CONFIG.SIZE,
  threshold: number = GRID_CONFIG.SNAP_THRESHOLD
): Point {
  return {
    x: snapWithMagnetism(point.x, gridSize, threshold),
    y: snapWithMagnetism(point.y, gridSize, threshold),
  }
}

// ========== 网格线生成函数 ==========

/**
 * 获取网格线坐标
 * @param viewBox - 视图框 {x, y, width, height}
 * @param gridSize - 网格大小
 * @returns 网格线坐标 {verticalLines, horizontalLines}
 */
export function getGridLines(viewBox: ViewBox, gridSize: number = GRID_CONFIG.SIZE): GridLines {
  const { x, y, width, height } = viewBox

  const verticalLines: GridLine[] = []
  const horizontalLines: GridLine[] = []

  // 计算起始位置
  const startX = Math.floor(x / gridSize) * gridSize
  const startY = Math.floor(y / gridSize) * gridSize

  // 生成垂直线
  for (let i = startX; i <= x + width; i += gridSize) {
    verticalLines.push({
      x1: i,
      y1: y,
      x2: i,
      y2: y + height,
    })
  }

  // 生成水平线
  for (let i = startY; i <= y + height; i += gridSize) {
    horizontalLines.push({
      x1: x,
      y1: i,
      x2: x + width,
      y2: i,
    })
  }

  return { verticalLines, horizontalLines }
}

// ========== 节点网格位置函数 ==========

/**
 * 计算节点在网格中的位置
 * @param node - 节点对象
 * @param gridSize - 网格大小
 * @returns 网格位置 {gridX, gridY}
 */
export function getNodeGridPosition(
  node: WorkflowNode,
  gridSize: number = GRID_CONFIG.SIZE
): GridPosition {
  return {
    gridX: Math.floor(node.x / gridSize),
    gridY: Math.floor(node.y / gridSize),
  }
}

/**
 * 检查两个节点是否在同一网格行或列
 * @param node1 - 节点1
 * @param node2 - 节点2
 * @param gridSize - 网格大小
 * @returns 对齐信息 {alignedX, alignedY}
 */
export function checkNodeAlignment(
  node1: WorkflowNode,
  node2: WorkflowNode,
  gridSize: number = GRID_CONFIG.SIZE
): AlignmentInfo {
  const pos1 = getNodeGridPosition(node1, gridSize)
  const pos2 = getNodeGridPosition(node2, gridSize)

  return {
    alignedX: pos1.gridX === pos2.gridX,
    alignedY: pos1.gridY === pos2.gridY,
  }
}

// ========== 对齐辅助线函数 ==========

/**
 * 获取对齐辅助线
 * @param draggedNode - 被拖拽的节点
 * @param otherNodes - 其他节点列表
 * @param threshold - 对齐阈值
 * @returns 辅助线列表
 */
export function getAlignmentGuides(
  draggedNode: WorkflowNode,
  otherNodes: WorkflowNode[],
  threshold: number = 5
): AlignmentGuide[] {
  const guides: AlignmentGuide[] = []

  otherNodes.forEach((node) => {
    if (node.id === draggedNode.id) return

    // 检查水平对齐
    if (Math.abs(node.y - draggedNode.y) < threshold) {
      guides.push({
        type: 'horizontal',
        y: node.y,
        x1: Math.min(node.x, draggedNode.x) - 50,
        x2: Math.max(node.x + 150, draggedNode.x + 150) + 50,
      })
    }

    // 检查垂直对齐
    if (Math.abs(node.x - draggedNode.x) < threshold) {
      guides.push({
        type: 'vertical',
        x: node.x,
        y1: Math.min(node.y, draggedNode.y) - 50,
        y2: Math.max(node.y + 80, draggedNode.y + 80) + 50,
      })
    }

    // 检查中心对齐
    const nodeCenterX = node.x + 75
    const draggedCenterX = draggedNode.x + 75
    if (Math.abs(nodeCenterX - draggedCenterX) < threshold) {
      guides.push({
        type: 'vertical',
        x: nodeCenterX,
        y1: Math.min(node.y, draggedNode.y) - 50,
        y2: Math.max(node.y + 80, draggedNode.y + 80) + 50,
      })
    }

    const nodeCenterY = node.y + 40
    const draggedCenterY = draggedNode.y + 40
    if (Math.abs(nodeCenterY - draggedCenterY) < threshold) {
      guides.push({
        type: 'horizontal',
        y: nodeCenterY,
        x1: Math.min(node.x, draggedNode.x) - 50,
        x2: Math.max(node.x + 150, draggedNode.x + 150) + 50,
      })
    }
  })

  return guides
}

/**
 * 应用对齐吸附
 * @param position - 当前位置 {x, y}
 * @param otherNodes - 其他节点列表
 * @param threshold - 对齐阈值
 * @returns 调整后的位置 {x, y}
 */
export function applyAlignmentSnap(
  position: Point,
  otherNodes: WorkflowNode[],
  threshold: number = 5
): Point {
  let { x, y } = position

  otherNodes.forEach((node) => {
    // 水平对齐吸附
    if (Math.abs(node.y - y) < threshold) {
      y = node.y
    }

    // 垂直对齐吸附
    if (Math.abs(node.x - x) < threshold) {
      x = node.x
    }

    // 中心对齐吸附
    const nodeCenterX = node.x + 75
    const positionCenterX = x + 75
    if (Math.abs(nodeCenterX - positionCenterX) < threshold) {
      x = node.x
    }

    const nodeCenterY = node.y + 40
    const positionCenterY = y + 40
    if (Math.abs(nodeCenterY - positionCenterY) < threshold) {
      y = node.y
    }
  })

  return { x, y }
}

// ========== 辅助函数 ==========

/**
 * 检查是否启用网格吸附
 * @returns 是否启用
 */
export function isGridSnapEnabled(): boolean {
  return GRID_CONFIG.SNAP_ENABLED
}

/**
 * 检查是否显示网格
 * @returns 是否显示
 */
export function isGridVisible(): boolean {
  return GRID_CONFIG.SHOW_GRID
}

/**
 * 获取网格大小
 * @returns 网格大小
 */
export function getGridSize(): number {
  return GRID_CONFIG.SIZE
}

/**
 * 设置网格配置
 * @param config - 部分配置
 */
export function setGridConfig(config: Partial<GridConfiguration>): void {
  Object.assign(GRID_CONFIG, config)
}

/**
 * 重置网格配置到默认值
 */
export function resetGridConfig(): void {
  GRID_CONFIG.SIZE = 20
  GRID_CONFIG.SNAP_THRESHOLD = 10
  GRID_CONFIG.SHOW_GRID = true
  GRID_CONFIG.SNAP_ENABLED = true
}

// ========== 导出类型 ==========

export type {
  Point,
  ViewBox,
  GridLine,
  GridLines,
  GridPosition,
  AlignmentInfo,
  AlignmentGuide,
  WorkflowNode,
  GridConfiguration,
}

