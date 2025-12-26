/**
 * 路径计算工具函数
 * Path calculation utilities for connections
 */

// ========== 类型定义 ==========

/** 点坐标 */
interface Point {
  x: number
  y: number
}

/** 连接点类型 */
type ConnectionType = 'input' | 'output'

/** 节点（临时类型） */
interface WorkflowNode {
  x: number
  y: number
  [key: string]: any
}

/** 路径数据 */
interface PathData {
  start: Point
  end: Point
  controlPoints?: Point[]
}

/** 边界框 */
interface BoundingBox {
  minX: number
  minY: number
  maxX: number
  maxY: number
}

/** 路径选项 */
interface PathOptions {
  fromType?: ConnectionType
  toType?: ConnectionType
  controlOffset?: number
}

// ========== 路径计算函数 ==========

/**
 * 计算连接线的贝塞尔曲线路径
 * @param fromPoint - 起点坐标 {x, y}
 * @param toPoint - 终点坐标 {x, y}
 * @param fromType - 起点类型 'input' | 'output'
 * @param toType - 终点类型 'input' | 'output'
 * @returns SVG路径字符串
 */
export function calculateConnectionPath(
  fromPoint: Point,
  toPoint: Point,
  fromType: ConnectionType = 'output',
  toType: ConnectionType = 'input'
): string {
  const { x: fromX, y: fromY } = fromPoint
  const { x: toX, y: toY } = toPoint

  // 计算控制点偏移量
  const distance = Math.abs(toX - fromX)
  const controlOffset = Math.max(50, Math.min(200, distance * 0.5))

  // 根据连接点类型确定控制点方向
  const cp1X = fromX + (fromType === 'output' ? controlOffset : -controlOffset)
  const cp1Y = fromY
  const cp2X = toX + (toType === 'input' ? -controlOffset : controlOffset)
  const cp2Y = toY

  return `M ${fromX} ${fromY} C ${cp1X} ${cp1Y}, ${cp2X} ${cp2Y}, ${toX} ${toY}`
}

/**
 * 获取节点连接点的坐标
 * @param node - 节点对象
 * @param type - 连接点类型 'input' | 'output'
 * @returns 连接点坐标 {x, y}
 */
export function getConnectionPointPosition(node: WorkflowNode, type: ConnectionType): Point {
  const nodeWidth = 150
  const nodeHeight = 80
  const pointRadius = 6

  if (type === 'input') {
    return {
      x: node.x - pointRadius,
      y: node.y + nodeHeight / 2,
    }
  } else {
    return {
      x: node.x + nodeWidth + pointRadius,
      y: node.y + nodeHeight / 2,
    }
  }
}

/**
 * 计算临时连接线路径
 * @param fromNode - 起始节点
 * @param fromType - 起始连接点类型
 * @param toPosition - 目标位置 {x, y}
 * @returns SVG路径字符串
 */
export function calculateTempConnectionPath(
  fromNode: WorkflowNode,
  fromType: ConnectionType,
  toPosition: Point
): string {
  const fromPoint = getConnectionPointPosition(fromNode, fromType)
  return calculateConnectionPath(fromPoint, toPosition, fromType, 'input')
}

/**
 * 计算两点之间的距离
 * @param point1 - 点1坐标 {x, y}
 * @param point2 - 点2坐标 {x, y}
 * @returns 距离值
 */
export function calculateDistance(point1: Point, point2: Point): number {
  const dx = point2.x - point1.x
  const dy = point2.y - point1.y
  return Math.sqrt(dx * dx + dy * dy)
}

/**
 * 检查点是否在连接线附近
 * @param point - 检查的点坐标 {x, y}
 * @param pathString - SVG路径字符串
 * @param threshold - 距离阈值
 * @returns 是否在附近
 */
export function isPointNearPath(
  point: Point,
  pathString: string,
  threshold: number = 10
): boolean {
  // 简化实现：检查点是否在路径的起点和终点连线附近
  const pathData = parsePath(pathString)
  if (!pathData) return false

  const { start, end } = pathData
  const distance = distanceToLineSegment(point, start, end)
  return distance <= threshold
}

/**
 * 解析SVG路径字符串
 * @param pathString - SVG路径字符串
 * @returns 路径数据 {start, end, controlPoints}
 */
function parsePath(pathString: string): PathData | null {
  const match = pathString.match(/M\s*([\d.-]+)\s*([\d.-]+).*?([\d.-]+)\s*([\d.-]+)$/)
  if (!match) return null

  return {
    start: { x: parseFloat(match[1]), y: parseFloat(match[2]) },
    end: { x: parseFloat(match[3]), y: parseFloat(match[4]) },
  }
}

/**
 * 计算点到线段的距离
 * @param point - 点坐标 {x, y}
 * @param lineStart - 线段起点 {x, y}
 * @param lineEnd - 线段终点 {x, y}
 * @returns 距离值
 */
function distanceToLineSegment(point: Point, lineStart: Point, lineEnd: Point): number {
  const A = point.x - lineStart.x
  const B = point.y - lineStart.y
  const C = lineEnd.x - lineStart.x
  const D = lineEnd.y - lineStart.y

  const dot = A * C + B * D
  const lenSq = C * C + D * D

  if (lenSq === 0) {
    return Math.sqrt(A * A + B * B)
  }

  let param = dot / lenSq

  if (param < 0) {
    return Math.sqrt(A * A + B * B)
  } else if (param > 1) {
    const dx = point.x - lineEnd.x
    const dy = point.y - lineEnd.y
    return Math.sqrt(dx * dx + dy * dy)
  } else {
    const projX = lineStart.x + param * C
    const projY = lineStart.y + param * D
    const dx = point.x - projX
    const dy = point.y - projY
    return Math.sqrt(dx * dx + dy * dy)
  }
}

/**
 * 获取连接线的中点坐标
 * @param pathString - SVG路径字符串
 * @returns 中点坐标 {x, y}
 */
export function getPathMidpoint(pathString: string): Point | null {
  const pathData = parsePath(pathString)
  if (!pathData) return null

  const { start, end } = pathData
  return {
    x: (start.x + end.x) / 2,
    y: (start.y + end.y) / 2,
  }
}

/**
 * 计算连接线的边界框
 * @param pathString - SVG路径字符串
 * @returns 边界框 {minX, minY, maxX, maxY}
 */
export function getPathBounds(pathString: string): BoundingBox | null {
  const pathData = parsePath(pathString)
  if (!pathData) return null

  const { start, end } = pathData
  return {
    minX: Math.min(start.x, end.x),
    minY: Math.min(start.y, end.y),
    maxX: Math.max(start.x, end.x),
    maxY: Math.max(start.y, end.y),
  }
}

/**
 * 计算贝塞尔曲线路径（别名函数）
 * @param fromPoint - 起点坐标 {x, y}
 * @param toPoint - 终点坐标 {x, y}
 * @param options - 选项参数
 * @returns SVG路径字符串或路径数据对象
 */
export function calculateBezierPath(
  fromPoint: Point,
  toPoint: Point,
  options: PathOptions = {}
): any {
  return calculateConnectionPath(
    fromPoint,
    toPoint,
    options.fromType || 'output',
    options.toType || 'input'
  )
}

/**
 * 计算直线路径
 * @param fromPoint - 起点坐标 {x, y}
 * @param toPoint - 终点坐标 {x, y}
 * @returns 路径数据对象
 */
export function calculateStraightPath(fromPoint: Point, toPoint: Point): any {
  return {
    type: 'straight',
    pathData: `M ${fromPoint.x} ${fromPoint.y} L ${toPoint.x} ${toPoint.y}`,
    points: [fromPoint, toPoint],
  }
}

/**
 * 获取连接线的中点坐标（别名函数）
 * @param fromPoint - 起点坐标 {x, y}
 * @param toPoint - 终点坐标 {x, y}
 * @returns 中点坐标 {x, y}
 */
export function getConnectionMidpoint(fromPoint: Point, toPoint: Point): Point {
  return {
    x: (fromPoint.x + toPoint.x) / 2,
    y: (fromPoint.y + toPoint.y) / 2,
  }
}

/**
 * 计算两点之间的角度
 * @param fromPoint - 起点坐标
 * @param toPoint - 终点坐标
 * @returns 角度（弧度）
 */
export function calculateAngle(fromPoint: Point, toPoint: Point): number {
  return Math.atan2(toPoint.y - fromPoint.y, toPoint.x - fromPoint.x)
}

/**
 * 获取路径上的点（按比例）
 * @param fromPoint - 起点
 * @param toPoint - 终点
 * @param ratio - 比例 (0-1)
 * @returns 路径上的点
 */
export function getPointOnPath(fromPoint: Point, toPoint: Point, ratio: number): Point {
  const clampedRatio = Math.max(0, Math.min(1, ratio))
  return {
    x: fromPoint.x + (toPoint.x - fromPoint.x) * clampedRatio,
    y: fromPoint.y + (toPoint.y - fromPoint.y) * clampedRatio,
  }
}

/**
 * 检查两个边界框是否相交
 * @param box1 - 边界框1
 * @param box2 - 边界框2
 * @returns 是否相交
 */
export function boundsIntersect(box1: BoundingBox, box2: BoundingBox): boolean {
  return !(
    box1.maxX < box2.minX ||
    box1.minX > box2.maxX ||
    box1.maxY < box2.minY ||
    box1.minY > box2.maxY
  )
}

/**
 * 获取路径长度估算
 * @param fromPoint - 起点
 * @param toPoint - 终点
 * @returns 路径长度
 */
export function getPathLength(fromPoint: Point, toPoint: Point): number {
  return calculateDistance(fromPoint, toPoint)
}

// ========== pathCalculator 对象 ==========

/**
 * pathCalculator 对象，包含所有路径计算方法
 */
export const pathCalculator = {
  calculateConnectionPath,
  calculateBezierPath,
  calculateStraightPath,
  calculateTempConnectionPath,
  getConnectionPointPosition,
  getConnectionMidpoint,
  getPathMidpoint,
  getPathBounds,
  calculateDistance,
  calculateAngle,
  isPointNearPath,
  getPointOnPath,
  getPathLength,
  boundsIntersect,
}

// ========== 导出类型 ==========

export type {
  Point,
  ConnectionType,
  WorkflowNode,
  PathData,
  BoundingBox,
  PathOptions,
}

