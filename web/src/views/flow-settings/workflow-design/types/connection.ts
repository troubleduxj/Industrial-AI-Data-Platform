/**
 * 连接相关类型定义
 * Connection-related type definitions
 */

import type { NodePort } from './node'

// 连接基础类型
export interface BaseConnection {
  id: string
  sourceNodeId: string
  targetNodeId: string
  sourcePortId: string
  targetPortId: string
  type: ConnectionType
  status: ConnectionStatus
  config: ConnectionConfig
  metadata?: ConnectionMetadata
}

// 连接类型
export type ConnectionType = 
  | 'data'        // 数据连接
  | 'control'     // 控制连接
  | 'event'       // 事件连接
  | 'condition'   // 条件连接

// 连接状态
export type ConnectionStatus = 
  | 'idle'        // 空闲
  | 'active'      // 活跃
  | 'error'       // 错误
  | 'disabled'    // 禁用

// 连接配置
export interface ConnectionConfig {
  label?: string
  description?: string
  condition?: string
  transform?: string
  validation?: ConnectionValidation
  style?: ConnectionStyle
}

// 连接验证配置
export interface ConnectionValidation {
  required: boolean
  dataType?: string
  schema?: any // JSON Schema
  customValidator?: string
}

// 连接样式配置
export interface ConnectionStyle {
  strokeColor: string
  strokeWidth: number
  strokeDasharray?: string
  opacity: number
  animated: boolean
  markerEnd?: string
  markerStart?: string
}

// 连接元数据
export interface ConnectionMetadata {
  createdAt: string
  updatedAt: string
  version: string
  author?: string
  tags?: string[]
}

// 连接路径点
export interface ConnectionPoint {
  x: number
  y: number
  type: 'start' | 'end' | 'control' | 'waypoint'
}

// 连接路径
export interface ConnectionPath {
  points: ConnectionPoint[]
  pathData: string // SVG path data
  length: number
  bounds: {
    x: number
    y: number
    width: number
    height: number
  }
}

// 临时连接
export interface TempConnection {
  id: string
  sourceNodeId: string
  sourcePortId: string
  currentPosition: {
    x: number
    y: number
  }
  targetNodeId?: string
  targetPortId?: string
  valid: boolean
  style: ConnectionStyle
}

// 连接验证结果
export interface ConnectionValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  suggestions?: string[]
}

// 连接兼容性检查
export interface ConnectionCompatibility {
  compatible: boolean
  reason?: string
  sourcePort: NodePort
  targetPort: NodePort
  dataTypeMatch: boolean
  cardinalityMatch: boolean
}

// 连接创建选项
export interface ConnectionCreateOptions {
  sourceNodeId: string
  sourcePortId: string
  targetNodeId: string
  targetPortId: string
  type?: ConnectionType
  config?: Partial<ConnectionConfig>
  validate?: boolean
  autoRoute?: boolean
}

// 连接更新选项
export interface ConnectionUpdateOptions {
  config?: Partial<ConnectionConfig>
  style?: Partial<ConnectionStyle>
  validate?: boolean
  recalculatePath?: boolean
}

// 连接事件
export interface ConnectionEvent {
  type: 'create' | 'update' | 'delete' | 'select' | 'deselect' | 'hover' | 'unhover'
  connectionId: string
  data?: any
  timestamp: string
}

// 连接拖拽状态
export interface ConnectionDragState {
  dragging: boolean
  sourceNodeId?: string
  sourcePortId?: string
  currentPosition: {
    x: number
    y: number
  }
  targetNodeId?: string
  targetPortId?: string
  valid: boolean
}

// 连接选择状态
export interface ConnectionSelection {
  selected: boolean
  highlighted: boolean
  hovered: boolean
}

// 连接动画配置
export interface ConnectionAnimation {
  type: 'none' | 'flow' | 'pulse' | 'dash'
  speed: number
  direction: 'forward' | 'backward' | 'bidirectional'
  enabled: boolean
}

// 连接标签
export interface ConnectionLabel {
  text: string
  position: {
    x: number
    y: number
  }
  offset: {
    x: number
    y: number
  }
  style: {
    fontSize: number
    fontWeight: string
    color: string
    backgroundColor?: string
    padding: number
    borderRadius: number
  }
  visible: boolean
}

// 连接端点
export interface ConnectionEndpoint {
  nodeId: string
  portId: string
  position: {
    x: number
    y: number
  }
  direction: 'input' | 'output'
  connected: boolean
}

// 连接路由算法选项
export interface ConnectionRoutingOptions {
  algorithm: 'straight' | 'bezier' | 'orthogonal' | 'manhattan'
  avoidNodes: boolean
  avoidConnections: boolean
  cornerRadius: number
  padding: number
}

// 连接碰撞检测
export interface ConnectionCollision {
  detected: boolean
  point: {
    x: number
    y: number
  }
  distance: number
  connectionId?: string
  nodeId?: string
}

// 连接统计信息
export interface ConnectionStats {
  totalConnections: number
  connectionsByType: Record<ConnectionType, number>
  connectionsByStatus: Record<ConnectionStatus, number>
  averageLength: number
  maxLength: number
  minLength: number
}

// 连接导出数据
export interface ConnectionExportData {
  connections: BaseConnection[]
  metadata: {
    exportedAt: string
    version: string
    totalCount: number
  }
}

// 连接导入选项
export interface ConnectionImportOptions {
  validateConnections: boolean
  skipInvalidConnections: boolean
  mergeStrategy: 'replace' | 'merge' | 'append'
  preserveIds: boolean
}

// 连接搜索条件
export interface ConnectionSearchCriteria {
  sourceNodeId?: string
  targetNodeId?: string
  type?: ConnectionType
  status?: ConnectionStatus
  label?: string
  hasCondition?: boolean
}

// 连接过滤器
export interface ConnectionFilter {
  types: ConnectionType[]
  statuses: ConnectionStatus[]
  sourceNodes: string[]
  targetNodes: string[]
  dateRange?: {
    start: string
    end: string
  }
}

// 连接分组
export interface ConnectionGroup {
  id: string
  name: string
  description?: string
  connectionIds: string[]
  color: string
  visible: boolean
}

// 连接模板
export interface ConnectionTemplate {
  id: string
  name: string
  description: string
  type: ConnectionType
  defaultConfig: ConnectionConfig
  defaultStyle: ConnectionStyle
  sourcePortTypes: string[]
  targetPortTypes: string[]
}