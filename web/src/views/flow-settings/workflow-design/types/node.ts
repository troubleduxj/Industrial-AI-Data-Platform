/**
 * 节点相关类型定义
 * Node-related type definitions
 */

// 节点基础类型
export interface BaseNode {
  id: string
  type: string
  name: string
  description?: string
  position: {
    x: number
    y: number
  }
  size: {
    width: number
    height: number
  }
  status: NodeStatus
  config: Record<string, any>
  metadata?: NodeMetadata
}

// 节点状态
export type NodeStatus = 
  | 'idle'        // 空闲
  | 'running'     // 运行中
  | 'success'     // 成功
  | 'error'       // 错误
  | 'warning'     // 警告
  | 'disabled'    // 禁用

// 节点元数据
export interface NodeMetadata {
  createdAt: string
  updatedAt: string
  version: string
  author?: string
  tags?: string[]
  category?: string
}

// 节点类型定义
export type NodeType = 
  | 'start'       // 开始节点
  | 'end'         // 结束节点
  | 'process'     // 处理节点
  | 'decision'    // 决策节点
  | 'condition'   // 条件节点
  | 'loop'        // 循环节点
  | 'api'         // API节点
  | 'database'    // 数据库节点
  | 'timer'       // 定时器节点
  | 'email'       // 邮件节点
  | 'file'        // 文件节点
  | 'action'      // 动作节点

// 特定节点类型接口
export interface StartNode extends BaseNode {
  type: 'start'
  config: {
    triggerType: 'manual' | 'schedule' | 'event'
    schedule?: {
      cron: string
      timezone: string
    }
    event?: {
      source: string
      condition: string
    }
  }
}

export interface EndNode extends BaseNode {
  type: 'end'
  config: {
    returnType: 'success' | 'error' | 'custom'
    returnValue?: any
    message?: string
  }
}

export interface ProcessNode extends BaseNode {
  type: 'process'
  config: {
    script: string
    language: 'javascript' | 'python' | 'shell'
    timeout: number
    retryCount: number
    environment?: Record<string, string>
  }
}

export interface DecisionNode extends BaseNode {
  type: 'decision'
  config: {
    conditions: Array<{
      id: string
      expression: string
      label: string
      outputPort: string
    }>
    defaultOutput?: string
  }
}

export interface ConditionNode extends BaseNode {
  type: 'condition'
  config: {
    expression: string
    trueOutput: string
    falseOutput: string
    variables?: Record<string, any>
  }
}

export interface LoopNode extends BaseNode {
  type: 'loop'
  config: {
    loopType: 'for' | 'while' | 'forEach'
    condition: string
    maxIterations: number
    breakCondition?: string
    variables?: Record<string, any>
  }
}

export interface ApiNode extends BaseNode {
  type: 'api'
  config: {
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
    url: string
    headers?: Record<string, string>
    body?: any
    timeout: number
    retryCount: number
    authentication?: {
      type: 'none' | 'basic' | 'bearer' | 'apiKey'
      credentials?: Record<string, string>
    }
  }
}

export interface DatabaseNode extends BaseNode {
  type: 'database'
  config: {
    operation: 'select' | 'insert' | 'update' | 'delete'
    connection: {
      type: 'mysql' | 'postgresql' | 'mongodb' | 'redis'
      host: string
      port: number
      database: string
      username: string
      password: string
    }
    query: string
    parameters?: Record<string, any>
  }
}

export interface TimerNode extends BaseNode {
  type: 'timer'
  config: {
    delay: number
    unit: 'seconds' | 'minutes' | 'hours' | 'days'
    repeat: boolean
    repeatCount?: number
    repeatInterval?: number
  }
}

export interface EmailNode extends BaseNode {
  type: 'email'
  config: {
    smtp: {
      host: string
      port: number
      secure: boolean
      username: string
      password: string
    }
    from: string
    to: string | string[]
    cc?: string | string[]
    bcc?: string | string[]
    subject: string
    body: string
    bodyType: 'text' | 'html'
    attachments?: Array<{
      filename: string
      path: string
      contentType?: string
    }>
  }
}

export interface FileNode extends BaseNode {
  type: 'file'
  config: {
    operation: 'read' | 'write' | 'copy' | 'move' | 'delete'
    path: string
    encoding?: string
    content?: string
    destination?: string
    createDirectories?: boolean
  }
}

export interface ActionNode extends BaseNode {
  type: 'action'
  config: {
    actionType: string
    parameters: Record<string, any>
    async: boolean
    timeout: number
  }
}

// 节点联合类型
export type WorkflowNode = 
  | StartNode
  | EndNode
  | ProcessNode
  | DecisionNode
  | ConditionNode
  | LoopNode
  | ApiNode
  | DatabaseNode
  | TimerNode
  | EmailNode
  | FileNode
  | ActionNode

// 节点输入输出端口
export interface NodePort {
  id: string
  name: string
  type: 'input' | 'output'
  dataType: string
  required: boolean
  multiple: boolean
  position: {
    x: number
    y: number
  }
}

// 节点验证结果
export interface NodeValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

// 节点执行结果
export interface NodeExecutionResult {
  success: boolean
  data?: any
  error?: string
  duration: number
  timestamp: string
}

// 节点配置模板
export interface NodeTemplate {
  type: NodeType
  name: string
  description: string
  icon: string
  category: string
  defaultConfig: Record<string, any>
  configSchema: any // JSON Schema
  inputPorts: Omit<NodePort, 'id' | 'position'>[]
  outputPorts: Omit<NodePort, 'id' | 'position'>[]
}

// 节点操作事件
export interface NodeEvent {
  type: 'create' | 'update' | 'delete' | 'move' | 'select' | 'deselect'
  nodeId: string
  data?: any
  timestamp: string
}

// 节点拖拽数据
export interface NodeDragData {
  nodeType: NodeType
  template: NodeTemplate
  offset: {
    x: number
    y: number
  }
}

// 节点选择状态
export interface NodeSelection {
  selected: boolean
  highlighted: boolean
  focused: boolean
}

// 节点样式配置
export interface NodeStyle {
  backgroundColor: string
  borderColor: string
  borderWidth: number
  borderRadius: number
  textColor: string
  fontSize: number
  fontWeight: string
  opacity: number
  shadow: boolean
}

// 节点动画配置
export interface NodeAnimation {
  type: 'none' | 'pulse' | 'glow' | 'shake' | 'bounce'
  duration: number
  iterations: number | 'infinite'
  easing: string
}