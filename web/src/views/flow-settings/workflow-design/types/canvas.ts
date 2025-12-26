/**
 * 画布相关类型定义
 * Canvas-related type definitions
 */

// 画布基础配置
export interface CanvasConfig {
  width: number
  height: number
  zoom: number
  minZoom: number
  maxZoom: number
  zoomStep: number
  offset: {
    x: number
    y: number
  }
  grid: GridConfig
  snap: SnapConfig
  selection: SelectionConfig
  viewport: ViewportConfig
}

// 网格配置
export interface GridConfig {
  enabled: boolean
  size: number
  color: string
  opacity: number
  type: 'dots' | 'lines' | 'cross'
  subdivisions: number
  subdivisionColor: string
  subdivisionOpacity: number
}

// 吸附配置
export interface SnapConfig {
  enabled: boolean
  toGrid: boolean
  toNodes: boolean
  toConnections: boolean
  threshold: number
  showGuides: boolean
  guideColor: string
}

// 选择配置
export interface SelectionConfig {
  enabled: boolean
  multiSelect: boolean
  selectOnDrag: boolean
  showBounds: boolean
  boundsColor: string
  boundsWidth: number
}

// 视口配置
export interface ViewportConfig {
  autoFit: boolean
  padding: number
  centerOnLoad: boolean
  smoothZoom: boolean
  zoomDuration: number
}

// 画布状态
export interface CanvasState {
  mode: CanvasMode
  tool: CanvasTool
  dragging: boolean
  panning: boolean
  selecting: boolean
  connecting: boolean
  resizing: boolean
  readonly: boolean
  loading: boolean
}

// 画布模式
export type CanvasMode = 
  | 'normal'      // 正常模式
  | 'readonly'    // 只读模式
  | 'presentation'// 演示模式
  | 'debug'       // 调试模式

// 画布工具
export type CanvasTool = 
  | 'select'      // 选择工具
  | 'pan'         // 平移工具
  | 'connect'     // 连接工具
  | 'zoom'        // 缩放工具
  | 'measure'     // 测量工具

// 画布坐标
export interface CanvasCoordinate {
  x: number
  y: number
}

// 画布区域
export interface CanvasRect {
  x: number
  y: number
  width: number
  height: number
}

// 画布边界
export interface CanvasBounds {
  left: number
  top: number
  right: number
  bottom: number
  width: number
  height: number
}

// 画布变换
export interface CanvasTransform {
  scale: number
  translateX: number
  translateY: number
  rotation: number
}

// 画布视口
export interface CanvasViewport {
  x: number
  y: number
  width: number
  height: number
  zoom: number
  bounds: CanvasBounds
}

// 画布事件
export interface CanvasEvent {
  type: CanvasEventType
  position: CanvasCoordinate
  worldPosition: CanvasCoordinate
  button?: number
  buttons?: number
  ctrlKey: boolean
  shiftKey: boolean
  altKey: boolean
  metaKey: boolean
  delta?: number
  target?: any
  timestamp: number
}

// 画布事件类型
export type CanvasEventType = 
  | 'click'
  | 'dblclick'
  | 'mousedown'
  | 'mouseup'
  | 'mousemove'
  | 'mouseenter'
  | 'mouseleave'
  | 'wheel'
  | 'keydown'
  | 'keyup'
  | 'contextmenu'
  | 'dragstart'
  | 'drag'
  | 'dragend'
  | 'drop'
  | 'resize'

// 画布拖拽状态
export interface CanvasDragState {
  dragging: boolean
  startPosition: CanvasCoordinate
  currentPosition: CanvasCoordinate
  deltaPosition: CanvasCoordinate
  target?: any
  data?: any
}

// 画布选择状态
export interface CanvasSelectionState {
  selecting: boolean
  startPosition: CanvasCoordinate
  currentPosition: CanvasCoordinate
  selectionRect: CanvasRect
  selectedItems: string[]
}

// 画布缩放状态
export interface CanvasZoomState {
  zooming: boolean
  startZoom: number
  currentZoom: number
  center: CanvasCoordinate
  animated: boolean
}

// 画布平移状态
export interface CanvasPanState {
  panning: boolean
  startOffset: CanvasCoordinate
  currentOffset: CanvasCoordinate
  velocity: CanvasCoordinate
  inertia: boolean
}

// 画布历史记录
export interface CanvasHistoryEntry {
  id: string
  timestamp: string
  action: string
  data: any
  canvasState: Partial<CanvasConfig>
}

// 画布性能指标
export interface CanvasPerformance {
  fps: number
  frameTime: number
  renderTime: number
  updateTime: number
  nodeCount: number
  connectionCount: number
  visibleNodes: number
  visibleConnections: number
}

// 画布渲染选项
export interface CanvasRenderOptions {
  antialias: boolean
  pixelRatio: number
  backgroundColor: string
  showFPS: boolean
  showGrid: boolean
  showRulers: boolean
  showMinimap: boolean
  culling: boolean
  levelOfDetail: boolean
}

// 画布导出选项
export interface CanvasExportOptions {
  format: 'png' | 'jpg' | 'svg' | 'pdf'
  quality: number
  scale: number
  background: boolean
  backgroundColor: string
  bounds?: CanvasRect
  includeHidden: boolean
}

// 画布导入选项
export interface CanvasImportOptions {
  preservePosition: boolean
  preserveZoom: boolean
  centerContent: boolean
  validateData: boolean
  mergeStrategy: 'replace' | 'merge' | 'append'
}

// 画布快照
export interface CanvasSnapshot {
  id: string
  name: string
  description?: string
  timestamp: string
  config: CanvasConfig
  state: CanvasState
  viewport: CanvasViewport
  thumbnail?: string
}

// 画布主题
export interface CanvasTheme {
  name: string
  colors: {
    background: string
    grid: string
    selection: string
    highlight: string
    text: string
    border: string
  }
  fonts: {
    family: string
    size: number
    weight: string
  }
  spacing: {
    grid: number
    padding: number
    margin: number
  }
}

// 画布布局算法
export interface CanvasLayoutAlgorithm {
  name: string
  type: 'hierarchical' | 'force' | 'circular' | 'grid' | 'tree'
  options: Record<string, any>
  animate: boolean
  duration: number
}

// 画布搜索结果
export interface CanvasSearchResult {
  type: 'node' | 'connection' | 'group'
  id: string
  name: string
  position: CanvasCoordinate
  bounds: CanvasRect
  score: number
}

// 画布统计信息
export interface CanvasStats {
  totalNodes: number
  totalConnections: number
  selectedNodes: number
  selectedConnections: number
  visibleNodes: number
  visibleConnections: number
  canvasSize: {
    width: number
    height: number
  }
  contentBounds: CanvasRect
  zoomLevel: number
}

// 画布操作历史
export interface CanvasOperation {
  id: string
  type: 'create' | 'update' | 'delete' | 'move' | 'resize' | 'connect'
  target: string
  data: any
  timestamp: string
  undoable: boolean
}

// 画布快捷键
export interface CanvasShortcut {
  key: string
  modifiers: string[]
  action: string
  description: string
  enabled: boolean
}

// 画布工具栏配置
export interface CanvasToolbarConfig {
  visible: boolean
  position: 'top' | 'bottom' | 'left' | 'right' | 'floating'
  tools: string[]
  customTools: any[]
  compact: boolean
}

// 画布右键菜单
export interface CanvasContextMenu {
  items: CanvasContextMenuItem[]
  position: CanvasCoordinate
  target?: any
  visible: boolean
}

// 画布右键菜单项
export interface CanvasContextMenuItem {
  id: string
  label: string
  icon?: string
  shortcut?: string
  action: string
  enabled: boolean
  visible: boolean
  separator?: boolean
  submenu?: CanvasContextMenuItem[]
}