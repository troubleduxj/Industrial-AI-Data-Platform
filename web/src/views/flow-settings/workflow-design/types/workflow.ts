/**
 * 工作流类型定义
 * Workflow Type Definitions
 */

// 基础类型
export interface Position {
  x: number
  y: number
}

export interface Size {
  width: number
  height: number
}

export interface Bounds {
  x: number
  y: number
  width: number
  height: number
}

export interface Point {
  x: number
  y: number
}

// 节点类型
export type NodeType = 
  | 'start'
  | 'end'
  | 'process'
  | 'decision'
  | 'parallel'
  | 'delay'
  | 'http'
  | 'database'
  | 'email'
  | 'webhook'
  | 'script'
  | 'condition'
  | 'loop'
  | 'merge'
  | 'split'

// 节点状态
export type NodeStatus = 
  | 'idle'
  | 'running'
  | 'success'
  | 'error'
  | 'warning'
  | 'disabled'

// 连接点类型
export type ConnectorType = 'input' | 'output'

// 连接点定义
export interface NodeConnector {
  id: string
  type: ConnectorType
  label?: string
  position: Position
  maxConnections?: number
  allowedTypes?: NodeType[]
}

// 节点属性
export interface NodeProperties {
  [key: string]: any
  timeout?: number
  retries?: number
  condition?: string
  url?: string
  method?: string
  headers?: Record<string, string>
  body?: string
  query?: string
  email?: {
    to: string[]
    subject: string
    template: string
  }
  script?: {
    language: 'javascript' | 'python'
    code: string
  }
}

// 节点定义
export interface WorkflowNode {
  id: string
  type: NodeType
  name: string
  description?: string
  x: number
  y: number
  width?: number
  height?: number
  status: NodeStatus
  properties: NodeProperties
  connectors: {
    input: NodeConnector[]
    output: NodeConnector[]
  }
  metadata?: {
    createdAt: string
    updatedAt: string
    version: string
    tags?: string[]
  }
}

// 连接线定义
export interface WorkflowConnection {
  id: string
  fromNodeId: string
  fromConnectorId: string
  toNodeId: string
  toConnectorId: string
  label?: string
  condition?: string
  properties?: {
    [key: string]: any
  }
  path?: string
  metadata?: {
    createdAt: string
    updatedAt: string
  }
}

// 临时连接
export interface TempConnection {
  fromNodeId: string
  fromConnectorId: string
  fromPosition: Position
  currentPosition: Position
  toNodeId?: string
  toConnectorId?: string
}

// 磁性吸附目标
export interface MagneticTarget {
  nodeId: string
  connectorId: string
  position: Position
  distance: number
}

// 画布状态
export interface CanvasState {
  scale: number
  translateX: number
  translateY: number
  showGrid: boolean
  snapToGrid: boolean
  gridSize: number
  viewBox?: {
    x: number
    y: number
    width: number
    height: number
  }
}

// 选择状态
export interface SelectionState {
  selectedNodes: string[]
  selectedConnections: string[]
  highlightedNodes: string[]
  highlightedConnections: string[]
  selectionBox?: Bounds
}

// 编辑状态
export interface EditState {
  isEditing: boolean
  isDirty: boolean
  lastSaved: string | null
  lastModified: string | null
  autoSave: boolean
  readOnly: boolean
}

// 工作流信息
export interface WorkflowInfo {
  id: string
  name: string
  description: string
  version: string
  createdAt: string | null
  updatedAt: string | null
  author: string
  tags?: string[]
  category?: string
  isPublic?: boolean
}

// 工作流数据
export interface WorkflowData {
  nodes: WorkflowNode[]
  connections: WorkflowConnection[]
  info: WorkflowInfo
  canvasState: CanvasState
  metadata?: {
    exportedAt: string
    exportedBy: string
    version: string
  }
}

// 工作流统计
export interface WorkflowStats {
  totalNodes: number
  totalConnections: number
  nodeTypes: Record<NodeType, number>
  hasStartNode: boolean
  hasEndNode: boolean
  maxDepth: number
  avgConnectionsPerNode: number
}

// 验证结果
export interface ValidationResult {
  isValid: boolean
  errors: ValidationError[]
  warnings: ValidationWarning[]
}

export interface ValidationError {
  type: 'missing_start' | 'missing_end' | 'isolated_node' | 'circular_dependency' | 'invalid_connection' | 'duplicate_connection'
  message: string
  nodeId?: string
  connectionId?: string
  details?: any
}

export interface ValidationWarning {
  type: 'unreachable_node' | 'unused_output' | 'missing_condition' | 'performance'
  message: string
  nodeId?: string
  connectionId?: string
  suggestion?: string
}

// 历史记录
export interface HistoryState {
  nodes: WorkflowNode[]
  connections: WorkflowConnection[]
  selectedNodes: string[]
  selectedConnections: string[]
  canvasState: CanvasState
  timestamp: number
}

export interface HistoryEntry {
  state: HistoryState
  action: string
  timestamp: number
  id: string
}

// 操作类型
export enum ActionType {
  ADD_NODE = 'add_node',
  DELETE_NODE = 'delete_node',
  UPDATE_NODE = 'update_node',
  MOVE_NODE = 'move_node',
  ADD_CONNECTION = 'add_connection',
  DELETE_CONNECTION = 'delete_connection',
  UPDATE_CONNECTION = 'update_connection',
  BATCH_UPDATE = 'batch_update',
  CLEAR_CANVAS = 'clear_canvas',
  IMPORT_WORKFLOW = 'import_workflow',
  PASTE_NODES = 'paste_nodes'
}

// 拖拽状态
export interface DragState {
  isDragging: boolean
  draggedNodes: string[]
  startPosition: Position
  currentPosition: Position
  offset: Position
  previewPositions: Record<string, Position>
}

// 连接状态
export interface ConnectionState {
  isConnecting: boolean
  tempConnection: TempConnection | null
  magneticTarget: MagneticTarget | null
  highlightedConnectors: string[]
}

// 网格配置
export interface GridConfig {
  size: number
  snapThreshold: number
  showDots: boolean
  showLines: boolean
  majorLineInterval: number
}

// 对齐辅助线
export interface AlignmentGuide {
  type: 'horizontal' | 'vertical'
  position: number
  nodes: string[]
}

// 节点模板
export interface NodeTemplate {
  type: NodeType
  name: string
  description: string
  icon: string
  category: string
  defaultProperties: NodeProperties
  connectors: {
    input: Omit<NodeConnector, 'id' | 'position'>[]
    output: Omit<NodeConnector, 'id' | 'position'>[]
  }
  validation?: {
    required?: string[]
    rules?: ValidationRule[]
  }
}

export interface ValidationRule {
  field: string
  type: 'required' | 'pattern' | 'range' | 'custom'
  value?: any
  message: string
  validator?: (value: any, node: WorkflowNode) => boolean
}

// 事件类型
export interface NodeEvent {
  type: 'click' | 'dblclick' | 'contextmenu' | 'dragstart' | 'drag' | 'dragend'
  node: WorkflowNode
  position: Position
  originalEvent: Event
}

export interface ConnectionEvent {
  type: 'click' | 'dblclick' | 'contextmenu' | 'hover'
  connection: WorkflowConnection
  position: Position
  originalEvent: Event
}

export interface CanvasEvent {
  type: 'click' | 'dblclick' | 'contextmenu' | 'wheel' | 'dragstart' | 'drag' | 'dragend'
  position: Position
  canvasPosition: Position
  originalEvent: Event
}

// 工具栏配置
export interface ToolbarConfig {
  showZoom: boolean
  showGrid: boolean
  showMinimap: boolean
  showHistory: boolean
  showValidation: boolean
  customTools?: ToolbarItem[]
}

export interface ToolbarItem {
  id: string
  label: string
  icon: string
  action: () => void
  disabled?: boolean
  tooltip?: string
}

// 上下文菜单
export interface ContextMenuItem {
  id: string
  label: string
  icon?: string
  action: () => void
  disabled?: boolean
  divider?: boolean
  children?: ContextMenuItem[]
}

// 快捷键配置
export interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  action: () => void
  description: string
}

// 导出配置
export interface ExportConfig {
  format: 'json' | 'png' | 'svg' | 'pdf'
  includeMetadata: boolean
  compression?: boolean
  quality?: number
  scale?: number
}

// 导入配置
export interface ImportConfig {
  validateSchema: boolean
  mergeMode: 'replace' | 'merge' | 'append'
  preserveIds: boolean
  autoLayout: boolean
}

// 性能配置
export interface PerformanceConfig {
  maxNodes: number
  maxConnections: number
  renderThreshold: number
  updateThrottle: number
  enableVirtualization: boolean
}

// 主题配置
export interface ThemeConfig {
  name: string
  colors: {
    primary: string
    success: string
    warning: string
    error: string
    background: string
    surface: string
    text: string
    border: string
  }
  fonts: {
    family: string
    size: {
      small: string
      normal: string
      large: string
    }
  }
  spacing: {
    small: string
    normal: string
    large: string
  }
}

// 插件接口
export interface WorkflowPlugin {
  name: string
  version: string
  description: string
  install: (context: WorkflowContext) => void
  uninstall?: (context: WorkflowContext) => void
}

export interface WorkflowContext {
  store: any // WorkflowStore
  canvas: any // Canvas instance
  registerNodeType: (template: NodeTemplate) => void
  registerTool: (tool: ToolbarItem) => void
  registerShortcut: (shortcut: KeyboardShortcut) => void
}

// 类型守卫
export function isWorkflowNode(obj: any): obj is WorkflowNode {
  return obj && typeof obj.id === 'string' && typeof obj.type === 'string'
}

export function isWorkflowConnection(obj: any): obj is WorkflowConnection {
  return obj && typeof obj.id === 'string' && typeof obj.fromNodeId === 'string' && typeof obj.toNodeId === 'string'
}

export function isPosition(obj: any): obj is Position {
  return obj && typeof obj.x === 'number' && typeof obj.y === 'number'
}

// 工具函数类型
export type NodeFactory = (type: NodeType, options?: Partial<WorkflowNode>) => WorkflowNode
export type ConnectionFactory = (from: string, to: string, options?: Partial<WorkflowConnection>) => WorkflowConnection
export type PathCalculator = (from: Position, to: Position, options?: any) => string
export type ValidationFunction = (nodes: WorkflowNode[], connections: WorkflowConnection[]) => ValidationResult
export type LayoutFunction = (nodes: WorkflowNode[], connections: WorkflowConnection[]) => { nodes: WorkflowNode[], bounds: Bounds }

// 事件处理器类型
export type NodeEventHandler = (event: NodeEvent) => void
export type ConnectionEventHandler = (event: ConnectionEvent) => void
export type CanvasEventHandler = (event: CanvasEvent) => void

// 状态更新类型
export type StateUpdater<T> = (state: T) => T | void
export type AsyncStateUpdater<T> = (state: T) => Promise<T | void>

// 配置类型
export interface WorkflowConfig {
  canvas: {
    grid: GridConfig
    zoom: {
      min: number
      max: number
      step: number
    }
    selection: {
      multiSelect: boolean
      selectOnDrag: boolean
    }
  }
  nodes: {
    defaultSize: Size
    minSize: Size
    maxSize: Size
    snapToGrid: boolean
  }
  connections: {
    style: 'bezier' | 'straight' | 'orthogonal'
    showArrows: boolean
    allowSelfConnection: boolean
  }
  interaction: {
    dragThreshold: number
    doubleClickDelay: number
    magneticThreshold: number
  }
  performance: PerformanceConfig
  theme: ThemeConfig
  toolbar: ToolbarConfig
}

// 默认配置
export const DEFAULT_WORKFLOW_CONFIG: WorkflowConfig = {
  canvas: {
    grid: {
      size: 20,
      snapThreshold: 10,
      showDots: true,
      showLines: false,
      majorLineInterval: 5
    },
    zoom: {
      min: 0.1,
      max: 3,
      step: 0.1
    },
    selection: {
      multiSelect: true,
      selectOnDrag: true
    }
  },
  nodes: {
    defaultSize: { width: 120, height: 60 },
    minSize: { width: 80, height: 40 },
    maxSize: { width: 400, height: 300 },
    snapToGrid: true
  },
  connections: {
    style: 'bezier',
    showArrows: true,
    allowSelfConnection: false
  },
  interaction: {
    dragThreshold: 5,
    doubleClickDelay: 300,
    magneticThreshold: 20
  },
  performance: {
    maxNodes: 1000,
    maxConnections: 2000,
    renderThreshold: 100,
    updateThrottle: 16,
    enableVirtualization: true
  },
  theme: {
    name: 'default',
    colors: {
      primary: '#1890ff',
      success: '#52c41a',
      warning: '#faad14',
      error: '#ff4d4f',
      background: '#f5f5f5',
      surface: '#ffffff',
      text: '#262626',
      border: '#d9d9d9'
    },
    fonts: {
      family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      size: {
        small: '12px',
        normal: '14px',
        large: '16px'
      }
    },
    spacing: {
      small: '8px',
      normal: '16px',
      large: '24px'
    }
  },
  toolbar: {
    showZoom: true,
    showGrid: true,
    showMinimap: true,
    showHistory: true,
    showValidation: true
  }
}