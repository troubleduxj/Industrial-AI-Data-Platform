/**
 * 坐标转换工具函数
 * Coordinate transformation utilities
 */

// ========== 类型定义 ==========

/** 点坐标 */
interface Point {
  x: number
  y: number
}

/** 矩形 */
interface Rectangle {
  x: number
  y: number
  width: number
  height: number
}

/** 圆形 */
interface Circle {
  x: number
  y: number
  radius: number
}

/** 画布变换信息 */
interface CanvasTransform {
  scale?: number
  offsetX?: number
  offsetY?: number
}

// ========== 坐标转换函数 ==========

/**
 * 屏幕坐标转换为画布坐标
 * @param screenPoint - 屏幕坐标点 {x, y}
 * @param canvasTransform - 画布变换信息 {scale, offsetX, offsetY}
 * @returns 画布坐标点 {x, y}
 */
export function screenToCanvas(screenPoint: Point, canvasTransform: CanvasTransform): Point {
  const { x, y } = screenPoint
  const { scale = 1, offsetX = 0, offsetY = 0 } = canvasTransform

  return {
    x: (x - offsetX) / scale,
    y: (y - offsetY) / scale,
  }
}

/**
 * 画布坐标转换为屏幕坐标
 * @param canvasPoint - 画布坐标点 {x, y}
 * @param canvasTransform - 画布变换信息 {scale, offsetX, offsetY}
 * @returns 屏幕坐标点 {x, y}
 */
export function canvasToScreen(canvasPoint: Point, canvasTransform: CanvasTransform): Point {
  const { x, y } = canvasPoint
  const { scale = 1, offsetX = 0, offsetY = 0 } = canvasTransform

  return {
    x: x * scale + offsetX,
    y: y * scale + offsetY,
  }
}

/**
 * 获取元素相对于画布的坐标
 * @param event - 鼠标事件
 * @param canvasElement - 画布元素
 * @param canvasTransform - 画布变换信息
 * @returns 画布坐标点 {x, y}
 */
export function getCanvasCoordinates(
  event: MouseEvent,
  canvasElement: HTMLElement,
  canvasTransform: CanvasTransform
): Point {
  const rect = canvasElement.getBoundingClientRect()
  const screenPoint: Point = {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
  }

  return screenToCanvas(screenPoint, canvasTransform)
}

/**
 * 获取鼠标相对于元素的坐标
 * @param event - 鼠标事件
 * @param element - 目标元素
 * @returns 相对坐标点 {x, y}
 */
export function getRelativeCoordinates(event: MouseEvent, element: HTMLElement): Point {
  const rect = element.getBoundingClientRect()
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
  }
}

// ========== 几何计算函数 ==========

/**
 * 计算两点之间的距离
 * @param point1 - 第一个点 {x, y}
 * @param point2 - 第二个点 {x, y}
 * @returns 距离
 */
export function calculateDistance(point1: Point, point2: Point): number {
  const dx = point2.x - point1.x
  const dy = point2.y - point1.y
  return Math.sqrt(dx * dx + dy * dy)
}

/**
 * 计算两点之间的角度（弧度）
 * @param point1 - 起始点 {x, y}
 * @param point2 - 结束点 {x, y}
 * @returns 角度（弧度）
 */
export function calculateAngle(point1: Point, point2: Point): number {
  const dx = point2.x - point1.x
  const dy = point2.y - point1.y
  return Math.atan2(dy, dx)
}

/**
 * 计算两点之间的角度（度数）
 * @param point1 - 起始点 {x, y}
 * @param point2 - 结束点 {x, y}
 * @returns 角度（度数）
 */
export function calculateAngleDegrees(point1: Point, point2: Point): number {
  const radians = calculateAngle(point1, point2)
  return radians * (180 / Math.PI)
}

/**
 * 计算点到线段的最短距离
 * @param point - 点 {x, y}
 * @param lineStart - 线段起点 {x, y}
 * @param lineEnd - 线段终点 {x, y}
 * @returns 最短距离
 */
export function pointToLineDistance(point: Point, lineStart: Point, lineEnd: Point): number {
  const A = point.x - lineStart.x
  const B = point.y - lineStart.y
  const C = lineEnd.x - lineStart.x
  const D = lineEnd.y - lineStart.y

  const dot = A * C + B * D
  const lenSq = C * C + D * D

  if (lenSq === 0) {
    // 线段退化为点
    return calculateDistance(point, lineStart)
  }

  let param = dot / lenSq

  let xx: number, yy: number

  if (param < 0) {
    xx = lineStart.x
    yy = lineStart.y
  } else if (param > 1) {
    xx = lineEnd.x
    yy = lineEnd.y
  } else {
    xx = lineStart.x + param * C
    yy = lineStart.y + param * D
  }

  const dx = point.x - xx
  const dy = point.y - yy
  return Math.sqrt(dx * dx + dy * dy)
}

// ========== 碰撞检测函数 ==========

/**
 * 检查点是否在矩形内
 * @param point - 点 {x, y}
 * @param rect - 矩形 {x, y, width, height}
 * @returns 是否在矩形内
 */
export function isPointInRect(point: Point, rect: Rectangle): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  )
}

/**
 * 检查点是否在圆形内
 * @param point - 点 {x, y}
 * @param circle - 圆形 {x, y, radius}
 * @returns 是否在圆形内
 */
export function isPointInCircle(point: Point, circle: Circle): boolean {
  const distance = calculateDistance(point, { x: circle.x, y: circle.y })
  return distance <= circle.radius
}

/**
 * 检查两个矩形是否相交
 * @param rect1 - 第一个矩形 {x, y, width, height}
 * @param rect2 - 第二个矩形 {x, y, width, height}
 * @returns 是否相交
 */
export function rectsIntersect(rect1: Rectangle, rect2: Rectangle): boolean {
  return !(
    rect1.x + rect1.width < rect2.x ||
    rect2.x + rect2.width < rect1.x ||
    rect1.y + rect1.height < rect2.y ||
    rect2.y + rect2.height < rect1.y
  )
}

// ========== 矩形相关函数 ==========

/**
 * 计算矩形的中心点
 * @param rect - 矩形 {x, y, width, height}
 * @returns 中心点 {x, y}
 */
export function getRectCenter(rect: Rectangle): Point {
  return {
    x: rect.x + rect.width / 2,
    y: rect.y + rect.height / 2,
  }
}

/**
 * 计算矩形的边界框
 * @param points - 点数组 [{x, y}, ...]
 * @returns 边界框 {x, y, width, height}
 */
export function getBoundingRect(points: Point[]): Rectangle {
  if (!points || points.length === 0) {
    return { x: 0, y: 0, width: 0, height: 0 }
  }

  let minX = points[0].x
  let minY = points[0].y
  let maxX = points[0].x
  let maxY = points[0].y

  for (let i = 1; i < points.length; i++) {
    const point = points[i]
    minX = Math.min(minX, point.x)
    minY = Math.min(minY, point.y)
    maxX = Math.max(maxX, point.x)
    maxY = Math.max(maxY, point.y)
  }

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
  }
}

// ========== 点变换函数 ==========

/**
 * 将点绕另一个点旋转指定角度
 * @param point - 要旋转的点 {x, y}
 * @param center - 旋转中心 {x, y}
 * @param angle - 旋转角度（弧度）
 * @returns 旋转后的点 {x, y}
 */
export function rotatePoint(point: Point, center: Point, angle: number): Point {
  const cos = Math.cos(angle)
  const sin = Math.sin(angle)

  const dx = point.x - center.x
  const dy = point.y - center.y

  return {
    x: center.x + dx * cos - dy * sin,
    y: center.y + dx * sin + dy * cos,
  }
}

/**
 * 缩放点坐标
 * @param point - 点 {x, y}
 * @param center - 缩放中心 {x, y}
 * @param scale - 缩放比例
 * @returns 缩放后的点 {x, y}
 */
export function scalePoint(point: Point, center: Point, scale: number): Point {
  return {
    x: center.x + (point.x - center.x) * scale,
    y: center.y + (point.y - center.y) * scale,
  }
}

/**
 * 平移点坐标
 * @param point - 点 {x, y}
 * @param offset - 偏移量 {x, y}
 * @returns 平移后的点 {x, y}
 */
export function translatePoint(point: Point, offset: Point): Point {
  return {
    x: point.x + offset.x,
    y: point.y + offset.y,
  }
}

/**
 * 限制点在指定矩形范围内
 * @param point - 点 {x, y}
 * @param bounds - 边界矩形 {x, y, width, height}
 * @returns 限制后的点 {x, y}
 */
export function clampPointToRect(point: Point, bounds: Rectangle): Point {
  return {
    x: Math.max(bounds.x, Math.min(bounds.x + bounds.width, point.x)),
    y: Math.max(bounds.y, Math.min(bounds.y + bounds.height, point.y)),
  }
}

// ========== 贝塞尔曲线函数 ==========

/**
 * 计算贝塞尔曲线上的点
 * @param t - 参数 (0-1)
 * @param points - 控制点数组 [{x, y}, ...]
 * @returns 曲线上的点 {x, y}
 */
export function getBezierPoint(t: number, points: Point[]): Point {
  const n = points.length - 1
  let x = 0
  let y = 0

  for (let i = 0; i <= n; i++) {
    const coefficient = binomialCoefficient(n, i) * Math.pow(1 - t, n - i) * Math.pow(t, i)
    x += coefficient * points[i].x
    y += coefficient * points[i].y
  }

  return { x, y }
}

/**
 * 计算二项式系数
 * @param n - n
 * @param k - k
 * @returns 二项式系数
 */
function binomialCoefficient(n: number, k: number): number {
  if (k === 0 || k === n) return 1
  if (k === 1 || k === n - 1) return n

  let result = 1
  for (let i = 0; i < k; i++) {
    result = (result * (n - i)) / (i + 1)
  }
  return result
}

/**
 * 计算三次贝塞尔曲线的控制点
 * @param start - 起点 {x, y}
 * @param end - 终点 {x, y}
 * @param curvature - 曲率 (0-1)
 * @returns 控制点数组 [{x, y}, {x, y}, {x, y}, {x, y}]
 */
export function getCubicBezierControlPoints(
  start: Point,
  end: Point,
  curvature: number = 0.5
): Point[] {
  const dx = end.x - start.x
  const dy = end.y - start.y
  const distance = Math.sqrt(dx * dx + dy * dy)

  const controlDistance = distance * curvature

  return [
    start,
    {
      x: start.x + controlDistance,
      y: start.y,
    },
    {
      x: end.x - controlDistance,
      y: end.y,
    },
    end,
  ]
}

/**
 * 计算点到贝塞尔曲线的最短距离
 * @param point - 点 {x, y}
 * @param controlPoints - 贝塞尔曲线控制点
 * @param precision - 精度（采样点数量）
 * @returns 最短距离
 */
export function pointToBezierDistance(
  point: Point,
  controlPoints: Point[],
  precision: number = 100
): number {
  let minDistance = Infinity

  for (let i = 0; i <= precision; i++) {
    const t = i / precision
    const curvePoint = getBezierPoint(t, controlPoints)
    const distance = calculateDistance(point, curvePoint)
    minDistance = Math.min(minDistance, distance)
  }

  return minDistance
}

// ========== 实用工具函数 ==========

/**
 * 格式化坐标为整数
 * @param point - 点 {x, y}
 * @returns 格式化后的点 {x, y}
 */
export function formatCoordinates(point: Point): Point {
  return {
    x: Math.round(point.x),
    y: Math.round(point.y),
  }
}

/**
 * 检查坐标是否有效
 * @param point - 点 {x, y}
 * @returns 是否有效
 */
export function isValidCoordinate(point: any): point is Point {
  return (
    point &&
    typeof point.x === 'number' &&
    typeof point.y === 'number' &&
    !isNaN(point.x) &&
    !isNaN(point.y) &&
    isFinite(point.x) &&
    isFinite(point.y)
  )
}

/**
 * 创建坐标点
 * @param x - x坐标
 * @param y - y坐标
 * @returns 坐标点 {x, y}
 */
export function createPoint(x: number = 0, y: number = 0): Point {
  return { x, y }
}

/**
 * 复制坐标点
 * @param point - 原始点 {x, y}
 * @returns 复制的点 {x, y}
 */
export function clonePoint(point: Point): Point {
  return { x: point.x, y: point.y }
}

/**
 * 比较两个坐标点是否相等
 * @param point1 - 第一个点 {x, y}
 * @param point2 - 第二个点 {x, y}
 * @param tolerance - 容差
 * @returns 是否相等
 */
export function pointsEqual(point1: Point, point2: Point, tolerance: number = 0): boolean {
  return Math.abs(point1.x - point2.x) <= tolerance && Math.abs(point1.y - point2.y) <= tolerance
}

/**
 * 计算多个点的重心
 * @param points - 点数组 [{x, y}, ...]
 * @returns 重心 {x, y}
 */
export function getCentroid(points: Point[]): Point {
  if (!points || points.length === 0) {
    return { x: 0, y: 0 }
  }

  let totalX = 0
  let totalY = 0

  for (const point of points) {
    totalX += point.x
    totalY += point.y
  }

  return {
    x: totalX / points.length,
    y: totalY / points.length,
  }
}

// ========== 坐标转换工具类 ==========

/**
 * 坐标转换工具类
 */
export class CoordinateTransformer {
  private scale: number
  private offsetX: number
  private offsetY: number

  constructor(canvasTransform: CanvasTransform = {}) {
    this.scale = canvasTransform.scale || 1
    this.offsetX = canvasTransform.offsetX || 0
    this.offsetY = canvasTransform.offsetY || 0
  }

  /**
   * 更新变换参数
   * @param transform - 变换参数
   */
  updateTransform(transform: CanvasTransform): void {
    this.scale = transform.scale !== undefined ? transform.scale : this.scale
    this.offsetX = transform.offsetX !== undefined ? transform.offsetX : this.offsetX
    this.offsetY = transform.offsetY !== undefined ? transform.offsetY : this.offsetY
  }

  /**
   * 屏幕坐标转画布坐标
   * @param screenPoint - 屏幕坐标
   * @returns 画布坐标
   */
  screenToCanvas(screenPoint: Point): Point {
    return screenToCanvas(screenPoint, {
      scale: this.scale,
      offsetX: this.offsetX,
      offsetY: this.offsetY,
    })
  }

  /**
   * 画布坐标转屏幕坐标
   * @param canvasPoint - 画布坐标
   * @returns 屏幕坐标
   */
  canvasToScreen(canvasPoint: Point): Point {
    return canvasToScreen(canvasPoint, {
      scale: this.scale,
      offsetX: this.offsetX,
      offsetY: this.offsetY,
    })
  }

  /**
   * 获取当前变换信息
   * @returns 变换信息
   */
  getTransform(): CanvasTransform {
    return {
      scale: this.scale,
      offsetX: this.offsetX,
      offsetY: this.offsetY,
    }
  }

  /**
   * 重置变换
   */
  reset(): void {
    this.scale = 1
    this.offsetX = 0
    this.offsetY = 0
  }

  /**
   * 设置缩放比例
   * @param scale - 缩放比例
   */
  setScale(scale: number): void {
    this.scale = scale
  }

  /**
   * 设置偏移量
   * @param offsetX - X轴偏移
   * @param offsetY - Y轴偏移
   */
  setOffset(offsetX: number, offsetY: number): void {
    this.offsetX = offsetX
    this.offsetY = offsetY
  }

  /**
   * 获取缩放比例
   * @returns 缩放比例
   */
  getScale(): number {
    return this.scale
  }

  /**
   * 获取偏移量
   * @returns 偏移量 {offsetX, offsetY}
   */
  getOffset(): { offsetX: number; offsetY: number } {
    return {
      offsetX: this.offsetX,
      offsetY: this.offsetY,
    }
  }
}

// ========== 导出类型 ==========

export type { Point, Rectangle, Circle, CanvasTransform }

