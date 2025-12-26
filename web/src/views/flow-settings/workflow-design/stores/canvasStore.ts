/**
 * 画布状态管理
 * Canvas state management store
 */

import { defineStore } from 'pinia'
import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ========== 类型定义 ==========

/** 画布变换状态 */
interface Transform {
  scale: number
  translateX: number
  translateY: number
  rotation: number
}

/** 画布尺寸 */
interface CanvasSize {
  width: number
  height: number
}

/** 视口信息 */
interface Viewport {
  width: number
  height: number
  offsetX: number
  offsetY: number
}

/** 网格设置 */
interface GridSettings {
  enabled: boolean
  size: number
  color: string
  opacity: number
  majorLines: boolean
  majorLineInterval: number
  majorLineColor: string
  majorLineOpacity: number
}

/** 对齐设置 */
interface SnapSettings {
  enabled: boolean
  toGrid: boolean
  toNodes: boolean
  toConnections: boolean
  threshold: number
  gridSize: number
}

/** 缩放设置 */
interface ZoomSettings {
  min: number
  max: number
  step: number
  wheelSensitivity: number
  touchSensitivity: number
}

/** 平移设置 */
interface PanSettings {
  enabled: boolean
  button: number
  keyModifier: string | null
  inertia: boolean
  friction: number
}

/** 画布模式 */
type CanvasMode = 'select' | 'pan' | 'zoom' | 'connect' | 'draw'

/** 鼠标状态 */
interface MouseState {
  x: number
  y: number
  canvasX: number
  canvasY: number
  isDragging: boolean
  dragStartX: number
  dragStartY: number
}

/** 小地图位置 */
type MinimapPosition = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'

/** 小地图设置 */
interface MinimapSettings {
  enabled: boolean
  position: MinimapPosition
  size: { width: number; height: number }
  scale: number
  opacity: number
}

/** 背景图案类型 */
type BackgroundPattern = 'dots' | 'lines' | 'grid' | null

/** 画布背景 */
interface BackgroundSettings {
  color: string
  pattern: BackgroundPattern
  image: string | null
}

/** 性能设置 */
interface PerformanceSettings {
  enableVirtualization: boolean
  renderThreshold: number
  updateThreshold: number
  enableLOD: boolean
  lodThreshold: number
}

/** 画布边界 */
interface CanvasBounds {
  left: number
  top: number
  right: number
  bottom: number
  width: number
  height: number
}

/** 可见区域 */
interface VisibleArea {
  x: number
  y: number
  width: number
  height: number
}

/** 坐标点 */
interface Point {
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

/** 画布状态导出 */
interface CanvasState {
  transform: Transform
  canvasSize: CanvasSize
  viewport: Viewport
  grid: GridSettings
  snap: SnapSettings
  zoom: ZoomSettings
  pan: PanSettings
  minimap: MinimapSettings
  background: BackgroundSettings
  performance: PerformanceSettings
  mode: CanvasMode
}

// ========== Store 定义 ==========

export const useCanvasStore = defineStore('workflowCanvas', () => {
  // 画布变换状态
  const transform: Ref<Transform> = ref({
    scale: 1,
    translateX: 0,
    translateY: 0,
    rotation: 0,
  })
  
  // 画布尺寸
  const canvasSize: Ref<CanvasSize> = ref({
    width: 0,
    height: 0,
  })
  
  // 视口信息
  const viewport: Ref<Viewport> = ref({
    width: 0,
    height: 0,
    offsetX: 0,
    offsetY: 0,
  })
  
  // 网格设置
  const grid: Ref<GridSettings> = ref({
    enabled: true,
    size: 20,
    color: '#e0e0e0',
    opacity: 0.5,
    majorLines: true,
    majorLineInterval: 5,
    majorLineColor: '#d0d0d0',
    majorLineOpacity: 0.8,
  })
  
  // 对齐设置
  const snap: Ref<SnapSettings> = ref({
    enabled: true,
    toGrid: true,
    toNodes: true,
    toConnections: false,
    threshold: 10,
    gridSize: 20,
  })
  
  // 缩放设置
  const zoom: Ref<ZoomSettings> = ref({
    min: 0.1,
    max: 5,
    step: 0.1,
    wheelSensitivity: 0.001,
    touchSensitivity: 0.005,
  })
  
  // 平移设置
  const pan: Ref<PanSettings> = ref({
    enabled: true,
    button: 1, // 中键
    keyModifier: null, // 'ctrl', 'shift', 'alt'
    inertia: true,
    friction: 0.9,
  })
  
  // 画布模式
  const mode: Ref<CanvasMode> = ref('select')
  
  // 鼠标状态
  const mouse: Ref<MouseState> = ref({
    x: 0,
    y: 0,
    canvasX: 0,
    canvasY: 0,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
  })
  
  // 小地图设置
  const minimap: Ref<MinimapSettings> = ref({
    enabled: true,
    position: 'bottom-right',
    size: { width: 200, height: 150 },
    scale: 0.1,
    opacity: 0.8,
  })
  
  // 画布背景
  const background: Ref<BackgroundSettings> = ref({
    color: '#fafafa',
    pattern: null,
    image: null,
  })
  
  // 性能设置
  const performance: Ref<PerformanceSettings> = ref({
    enableVirtualization: true,
    renderThreshold: 100,
    updateThreshold: 16, // 60fps
    enableLOD: true, // Level of Detail
    lodThreshold: 0.5,
  })
  
  // 计算属性
  const transformMatrix: ComputedRef<string> = computed(() => {
    const { scale, translateX, translateY, rotation } = transform.value
    return `translate(${translateX}px, ${translateY}px) scale(${scale}) rotate(${rotation}deg)`
  })
  
  const transformCSS: ComputedRef<{ transform: string; transformOrigin: string }> = computed(() => {
    return {
      transform: transformMatrix.value,
      transformOrigin: 'center',
    }
  })
  
  const canvasBounds: ComputedRef<CanvasBounds> = computed(() => {
    const { scale, translateX, translateY } = transform.value
    const { width, height } = viewport.value
    
    return {
      left: -translateX / scale,
      top: -translateY / scale,
      right: (-translateX + width) / scale,
      bottom: (-translateY + height) / scale,
      width: width / scale,
      height: height / scale,
    }
  })
  
  const visibleArea: ComputedRef<VisibleArea> = computed(() => {
    const bounds = canvasBounds.value
    return {
      x: bounds.left,
      y: bounds.top,
      width: bounds.width,
      height: bounds.height,
    }
  })
  
  const isZoomedIn: ComputedRef<boolean> = computed(() => transform.value.scale > 1)
  const isZoomedOut: ComputedRef<boolean> = computed(() => transform.value.scale < 1)
  const canZoomIn: ComputedRef<boolean> = computed(() => transform.value.scale < zoom.value.max)
  const canZoomOut: ComputedRef<boolean> = computed(() => transform.value.scale > zoom.value.min)
  
  // 坐标转换
  function screenToCanvas(screenX: number, screenY: number): Point {
    const { scale, translateX, translateY } = transform.value
    return {
      x: (screenX - translateX) / scale,
      y: (screenY - translateY) / scale,
    }
  }
  
  function canvasToScreen(canvasX: number, canvasY: number): Point {
    const { scale, translateX, translateY } = transform.value
    return {
      x: canvasX * scale + translateX,
      y: canvasY * scale + translateY,
    }
  }
  
  // 缩放操作
  function zoomIn(factor: number = zoom.value.step): void {
    const newScale = Math.min(transform.value.scale + factor, zoom.value.max)
    setZoom(newScale)
  }
  
  function zoomOut(factor: number = zoom.value.step): void {
    const newScale = Math.max(transform.value.scale - factor, zoom.value.min)
    setZoom(newScale)
  }
  
  function setZoom(scale: number, centerX: number = viewport.value.width / 2, centerY: number = viewport.value.height / 2): void {
    const oldScale = transform.value.scale
    const newScale = Math.max(zoom.value.min, Math.min(zoom.value.max, scale))
    
    if (newScale !== oldScale) {
      const scaleFactor = newScale / oldScale
      const { translateX, translateY } = transform.value
      
      // 以指定点为中心缩放
      const newTranslateX = centerX - (centerX - translateX) * scaleFactor
      const newTranslateY = centerY - (centerY - translateY) * scaleFactor
      
      transform.value = {
        ...transform.value,
        scale: newScale,
        translateX: newTranslateX,
        translateY: newTranslateY,
      }
    }
  }
  
  function zoomToFit(padding: number = 50): void {
    // 这里需要根据实际的节点位置计算
    // 暂时使用默认实现
    const scale = Math.min(
      (viewport.value.width - padding * 2) / canvasSize.value.width,
      (viewport.value.height - padding * 2) / canvasSize.value.height
    )
    
    const centerX = viewport.value.width / 2
    const centerY = viewport.value.height / 2
    
    transform.value = {
      ...transform.value,
      scale: Math.max(zoom.value.min, Math.min(zoom.value.max, scale)),
      translateX: centerX - (canvasSize.value.width * scale) / 2,
      translateY: centerY - (canvasSize.value.height * scale) / 2,
    }
  }
  
  function zoomToSelection(bounds: Bounds | null, padding: number = 50): void {
    if (!bounds) return
    
    const scaleX = (viewport.value.width - padding * 2) / bounds.width
    const scaleY = (viewport.value.height - padding * 2) / bounds.height
    const scale = Math.min(scaleX, scaleY)
    
    const centerX = viewport.value.width / 2
    const centerY = viewport.value.height / 2
    
    transform.value = {
      ...transform.value,
      scale: Math.max(zoom.value.min, Math.min(zoom.value.max, scale)),
      translateX: centerX - (bounds.x + bounds.width / 2) * scale,
      translateY: centerY - (bounds.y + bounds.height / 2) * scale,
    }
  }
  
  function resetZoom(): void {
    transform.value.scale = 1
  }
  
  // 平移操作
  function panCanvas(deltaX: number, deltaY: number): void {
    transform.value.translateX += deltaX
    transform.value.translateY += deltaY
  }
  
  function panTo(x: number, y: number): void {
    transform.value.translateX = x
    transform.value.translateY = y
  }
  
  function centerView(): void {
    transform.value.translateX = viewport.value.width / 2
    transform.value.translateY = viewport.value.height / 2
  }
  
  function resetPan(): void {
    transform.value.translateX = 0
    transform.value.translateY = 0
  }
  
  // 对齐功能
  function snapToGrid(x: number, y: number): Point {
    if (!snap.value.enabled || !snap.value.toGrid) {
      return { x, y }
    }
    
    const gridSize = snap.value.gridSize
    return {
      x: Math.round(x / gridSize) * gridSize,
      y: Math.round(y / gridSize) * gridSize,
    }
  }
  
  function snapToPoint(x: number, y: number, points: Point[], threshold: number = snap.value.threshold): Point {
    if (!snap.value.enabled) {
      return { x, y }
    }
    
    let snappedX = x
    let snappedY = y
    let minDistanceX = threshold
    let minDistanceY = threshold
    
    points.forEach(point => {
      const distanceX = Math.abs(x - point.x)
      const distanceY = Math.abs(y - point.y)
      
      if (distanceX < minDistanceX) {
        snappedX = point.x
        minDistanceX = distanceX
      }
      
      if (distanceY < minDistanceY) {
        snappedY = point.y
        minDistanceY = distanceY
      }
    })
    
    return { x: snappedX, y: snappedY }
  }
  
  // 鼠标位置更新
  function updateMousePosition(screenX: number, screenY: number): void {
    mouse.value.x = screenX
    mouse.value.y = screenY
    
    const canvasPos = screenToCanvas(screenX, screenY)
    mouse.value.canvasX = canvasPos.x
    mouse.value.canvasY = canvasPos.y
  }
  
  // 拖拽状态
  function startDrag(x: number, y: number): void {
    mouse.value.isDragging = true
    mouse.value.dragStartX = x
    mouse.value.dragStartY = y
  }
  
  function endDrag(): void {
    mouse.value.isDragging = false
  }
  
  // 画布设置
  function updateCanvasSize(width: number, height: number): void {
    canvasSize.value.width = width
    canvasSize.value.height = height
  }
  
  function updateViewport(width: number, height: number, offsetX: number = 0, offsetY: number = 0): void {
    viewport.value = { width, height, offsetX, offsetY }
  }
  
  function setMode(newMode: CanvasMode): void {
    mode.value = newMode
  }
  
  function toggleGrid(): void {
    grid.value.enabled = !grid.value.enabled
  }
  
  function toggleSnap(): void {
    snap.value.enabled = !snap.value.enabled
  }
  
  function toggleMinimap(): void {
    minimap.value.enabled = !minimap.value.enabled
  }
  
  // 网格设置
  function updateGridSettings(settings: Partial<GridSettings>): void {
    grid.value = { ...grid.value, ...settings }
  }
  
  function updateSnapSettings(settings: Partial<SnapSettings>): void {
    snap.value = { ...snap.value, ...settings }
  }
  
  function updateZoomSettings(settings: Partial<ZoomSettings>): void {
    zoom.value = { ...zoom.value, ...settings }
  }
  
  function updatePanSettings(settings: Partial<PanSettings>): void {
    pan.value = { ...pan.value, ...settings }
  }
  
  function updateMinimapSettings(settings: Partial<MinimapSettings>): void {
    minimap.value = { ...minimap.value, ...settings }
  }
  
  function updateBackgroundSettings(settings: Partial<BackgroundSettings>): void {
    background.value = { ...background.value, ...settings }
  }
  
  function updatePerformanceSettings(settings: Partial<PerformanceSettings>): void {
    performance.value = { ...performance.value, ...settings }
  }
  
  // 重置画布
  function resetCanvas(): void {
    transform.value = {
      scale: 1,
      translateX: 0,
      translateY: 0,
      rotation: 0,
    }
    
    mouse.value = {
      x: 0,
      y: 0,
      canvasX: 0,
      canvasY: 0,
      isDragging: false,
      dragStartX: 0,
      dragStartY: 0,
    }
    
    mode.value = 'select'
  }
  
  // 导出画布状态
  function exportCanvasState(): CanvasState {
    return {
      transform: transform.value,
      canvasSize: canvasSize.value,
      viewport: viewport.value,
      grid: grid.value,
      snap: snap.value,
      zoom: zoom.value,
      pan: pan.value,
      minimap: minimap.value,
      background: background.value,
      performance: performance.value,
      mode: mode.value,
    }
  }
  
  // 导入画布状态
  function importCanvasState(state: Partial<CanvasState>): void {
    if (state.transform) transform.value = { ...transform.value, ...state.transform }
    if (state.canvasSize) canvasSize.value = { ...canvasSize.value, ...state.canvasSize }
    if (state.viewport) viewport.value = { ...viewport.value, ...state.viewport }
    if (state.grid) grid.value = { ...grid.value, ...state.grid }
    if (state.snap) snap.value = { ...snap.value, ...state.snap }
    if (state.zoom) zoom.value = { ...zoom.value, ...state.zoom }
    if (state.pan) pan.value = { ...pan.value, ...state.pan }
    if (state.minimap) minimap.value = { ...minimap.value, ...state.minimap }
    if (state.background) background.value = { ...background.value, ...state.background }
    if (state.performance) performance.value = { ...performance.value, ...state.performance }
    if (state.mode) mode.value = state.mode
  }
  
  return {
    // 状态
    transform: computed(() => transform.value),
    canvasSize: computed(() => canvasSize.value),
    viewport: computed(() => viewport.value),
    grid: computed(() => grid.value),
    snap: computed(() => snap.value),
    zoom: computed(() => zoom.value),
    pan: computed(() => pan.value),
    mode: computed(() => mode.value),
    mouse: computed(() => mouse.value),
    minimap: computed(() => minimap.value),
    background: computed(() => background.value),
    performance: computed(() => performance.value),
    
    // 计算属性
    transformMatrix,
    transformCSS,
    canvasBounds,
    visibleArea,
    isZoomedIn,
    isZoomedOut,
    canZoomIn,
    canZoomOut,
    
    // 方法
    screenToCanvas,
    canvasToScreen,
    zoomIn,
    zoomOut,
    setZoom,
    zoomToFit,
    zoomToSelection,
    resetZoom,
    panCanvas,
    panTo,
    centerView,
    resetPan,
    snapToGrid,
    snapToPoint,
    updateMousePosition,
    startDrag,
    endDrag,
    updateCanvasSize,
    updateViewport,
    setMode,
    toggleGrid,
    toggleSnap,
    toggleMinimap,
    updateGridSettings,
    updateSnapSettings,
    updateZoomSettings,
    updatePanSettings,
    updateMinimapSettings,
    updateBackgroundSettings,
    updatePerformanceSettings,
    resetCanvas,
    exportCanvasState,
    importCanvasState,
  }
})

// ========== 导出类型 ==========

export type {
  Transform,
  CanvasSize,
  Viewport,
  GridSettings,
  SnapSettings,
  ZoomSettings,
  PanSettings,
  CanvasMode,
  MouseState,
  MinimapPosition,
  MinimapSettings,
  BackgroundPattern,
  BackgroundSettings,
  PerformanceSettings,
  CanvasBounds,
  VisibleArea,
  Point,
  Bounds,
  CanvasState,
}

