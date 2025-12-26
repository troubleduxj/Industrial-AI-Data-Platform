/**
 * 工作流管理组合函数
 * Workflow management composable
 */

import { ref, computed, reactive, watch, nextTick, type Ref, type ComputedRef } from 'vue'
import { useWorkflowStore } from '../stores/workflowStore.js'
import { useNodeStore } from '../stores/nodeStore.js'
import { useConnectionStore } from '../stores/connectionStore.js'
import { useCanvasStore } from '../stores/canvasStore.js'
import { useHistoryStore } from '../stores/historyStore.js'
import { useSelectionStore } from '../stores/selectionStore.js'
import { validateWorkflow } from '../utils/validationUtils.js'
import { exportWorkflow, importWorkflow } from '../utils/exportUtils.js'
import { ACTION_TYPES } from '../utils/historyManager.js'

// ========== 类型定义 ==========

/** 执行状态 */
type ExecutionStatus = 'idle' | 'running' | 'paused' | 'completed' | 'error'

/** 权限类型 */
type PermissionType = 'view' | 'edit' | 'admin'

/** 工作流基本信息 */
interface WorkflowInfo {
  id: string | null
  name: string
  description: string
  version: string
  author: string
  tags: string[]
  category: string
  created: string | null
  modified: string | null
}

/** 执行状态 */
interface ExecutionState {
  status: ExecutionStatus
  progress: number
  currentNodeId: string | null
  startTime: string | null
  endTime: string | null
  duration: number
  logs: any[]
  errors: any[]
}

/** 验证状态 */
interface ValidationState {
  isValid: boolean
  errors: any[]
  warnings: any[]
  lastValidated: string | null
  autoValidate: boolean
}

/** 保存状态 */
interface SavingState {
  isDirty: boolean
  isAutoSaving: boolean
  lastSaved: string | null
  autoSaveInterval: number
  autoSaveEnabled: boolean
}

/** 导入导出选项 */
interface ImportExportOptions {
  includeMetadata: boolean
  includeHistory: boolean
  includeComments: boolean
  compress: boolean
}

/** 导入导出状态 */
interface ImportExportState {
  isImporting: boolean
  isExporting: boolean
  format: string
  options: ImportExportOptions
}

/** 协作状态 */
interface CollaborationState {
  isShared: boolean
  collaborators: any[]
  permissions: PermissionType
  conflicts: any[]
  lastSync: string | null
}

/** 性能状态 */
interface PerformanceState {
  nodeCount: number
  connectionCount: number
  renderTime: number
  memoryUsage: number
  fps: number
}

/** 工作流状态 */
interface WorkflowState {
  info: WorkflowInfo
  execution: ExecutionState
  validation: ValidationState
  saving: SavingState
  importExport: ImportExportState
  collaboration: CollaborationState
  performance: PerformanceState
}

/** 工作流统计 */
interface WorkflowStats {
  nodeCount: number
  connectionCount: number
  nodeTypes: string[]
  connectionTypes: string[]
  complexity: number
  depth: number
  width: number
}

/** 工作流创建选项 */
interface CreateWorkflowOptions {
  name?: string
  description?: string
  version?: string
  author?: string
  tags?: string[]
  category?: string
  nodes?: any[]
  connections?: any[]
  canvas?: {
    width: number
    height: number
    zoom: number
    offsetX: number
    offsetY: number
  }
}

// ========== Composable ==========

export function useWorkflow() {
  // 获取stores
  const workflowStore = useWorkflowStore()
  const nodeStore = useNodeStore()
  const connectionStore = useConnectionStore()
  const canvasStore = useCanvasStore()
  const historyStore = useHistoryStore()
  const selectionStore = useSelectionStore()

  // 工作流状态
  const workflowState = reactive<WorkflowState>({
    // 基本信息
    info: {
      id: null,
      name: '新建工作流',
      description: '',
      version: '1.0.0',
      author: '',
      tags: [],
      category: 'general',
      created: null,
      modified: null,
    },

    // 运行状态
    execution: {
      status: 'idle',
      progress: 0,
      currentNodeId: null,
      startTime: null,
      endTime: null,
      duration: 0,
      logs: [],
      errors: [],
    },

    // 验证状态
    validation: {
      isValid: true,
      errors: [],
      warnings: [],
      lastValidated: null,
      autoValidate: true,
    },

    // 保存状态
    saving: {
      isDirty: false,
      isAutoSaving: false,
      lastSaved: null,
      autoSaveInterval: 30000,
      autoSaveEnabled: true,
    },

    // 导入导出状态
    importExport: {
      isImporting: false,
      isExporting: false,
      format: 'json',
      options: {
        includeMetadata: true,
        includeHistory: false,
        includeComments: true,
        compress: false,
      },
    },

    // 协作状态
    collaboration: {
      isShared: false,
      collaborators: [],
      permissions: 'edit',
      conflicts: [],
      lastSync: null,
    },

    // 性能监控
    performance: {
      nodeCount: 0,
      connectionCount: 0,
      renderTime: 0,
      memoryUsage: 0,
      fps: 60,
    },
  })

  // 计算属性
  const workflow: ComputedRef<any> = computed(() => workflowStore.workflow)
  const nodes: ComputedRef<any[]> = computed(() => workflowStore.nodes)
  const connections: ComputedRef<any[]> = computed(() => workflowStore.connections)
  const isValid: ComputedRef<boolean> = computed(() => workflowState.validation.isValid)
  const isDirty: ComputedRef<boolean> = computed(() => workflowState.saving.isDirty)
  const isRunning: ComputedRef<boolean> = computed(() => workflowState.execution.status === 'running')
  const canExecute: ComputedRef<boolean> = computed(
    () => isValid.value && workflowState.execution.status === 'idle' && nodes.value.length > 0
  )

  const workflowStats: ComputedRef<WorkflowStats> = computed(() => ({
    nodeCount: nodes.value.length,
    connectionCount: connections.value.length,
    nodeTypes: [...new Set(nodes.value.map((node: any) => node.type))],
    connectionTypes: [...new Set(connections.value.map((conn: any) => conn.type))],
    complexity: calculateComplexity(),
    depth: calculateDepth(),
    width: calculateWidth(),
  }))

  // 工作流创建和初始化
  function createWorkflow(options: CreateWorkflowOptions = {}): any {
    const workflowData = {
      id: generateWorkflowId(),
      name: options.name || '新建工作流',
      description: options.description || '',
      version: options.version || '1.0.0',
      author: options.author || '',
      tags: options.tags || [],
      category: options.category || 'general',
      created: new Date().toISOString(),
      modified: new Date().toISOString(),
      nodes: options.nodes || [],
      connections: options.connections || [],
      canvas: options.canvas || {
        width: 5000,
        height: 3000,
        zoom: 1,
        offsetX: 0,
        offsetY: 0,
      },
    }

    workflowStore.initializeWorkflow(workflowData)

    workflowState.info = {
      id: workflowData.id,
      name: workflowData.name,
      description: workflowData.description,
      version: workflowData.version,
      author: workflowData.author,
      tags: workflowData.tags,
      category: workflowData.category,
      created: workflowData.created,
      modified: workflowData.modified,
    }

    resetExecutionState()
    resetValidationState()
    resetSavingState()

    canvasStore.setCanvasSize(workflowData.canvas.width, workflowData.canvas.height)
    canvasStore.setZoom(workflowData.canvas.zoom)
    canvasStore.setViewport({
      x: workflowData.canvas.offsetX,
      y: workflowData.canvas.offsetY,
    })

    historyStore.clearHistory()
    historyStore.saveToHistory(ACTION_TYPES.CREATE_WORKFLOW, {
      workflowId: workflowData.id,
      name: workflowData.name,
    })

    return workflowData
  }

  function loadWorkflow(workflowData: any): boolean {
    try {
      if (!validateWorkflowData(workflowData)) {
        throw new Error('无效的工作流数据')
      }

      workflowStore.loadWorkflow(workflowData)

      workflowState.info = {
        id: workflowData.id,
        name: workflowData.name,
        description: workflowData.description || '',
        version: workflowData.version || '1.0.0',
        author: workflowData.author || '',
        tags: workflowData.tags || [],
        category: workflowData.category || 'general',
        created: workflowData.created,
        modified: workflowData.modified,
      }

      resetExecutionState()
      resetValidationState()
      markAsSaved()

      return true
    } catch (error: any) {
      console.error('加载工作流失败:', error)
      return false
    }
  }

  function saveWorkflow(): any {
    const workflowData = {
      ...workflowState.info,
      modified: new Date().toISOString(),
      nodes: nodes.value,
      connections: connections.value,
      canvas: {
        width: canvasStore.canvasSize.width,
        height: canvasStore.canvasSize.height,
        zoom: canvasStore.transform.scale,
        offsetX: canvasStore.transform.translateX,
        offsetY: canvasStore.transform.translateY,
      },
    }

    markAsSaved()

    historyStore.saveToHistory(ACTION_TYPES.SAVE_WORKFLOW, {
      workflowId: workflowData.id,
      name: workflowData.name,
    })

    return workflowData
  }

  // 辅助函数
  function generateWorkflowId(): string {
    return `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  function validateWorkflowData(data: any): boolean {
    return !!(data && data.id && data.name && Array.isArray(data.nodes) && Array.isArray(data.connections))
  }

  function resetExecutionState(): void {
    workflowState.execution = {
      status: 'idle',
      progress: 0,
      currentNodeId: null,
      startTime: null,
      endTime: null,
      duration: 0,
      logs: [],
      errors: [],
    }
  }

  function resetValidationState(): void {
    workflowState.validation = {
      isValid: true,
      errors: [],
      warnings: [],
      lastValidated: null,
      autoValidate: true,
    }
  }

  function resetSavingState(): void {
    workflowState.saving = {
      isDirty: false,
      isAutoSaving: false,
      lastSaved: null,
      autoSaveInterval: 30000,
      autoSaveEnabled: true,
    }
  }

  function markAsDirty(): void {
    workflowState.saving.isDirty = true
  }

  function markAsSaved(): void {
    workflowState.saving.isDirty = false
    workflowState.saving.lastSaved = new Date().toISOString()
  }

  function calculateComplexity(): number {
    const nodeCount = nodes.value.length
    const connectionCount = connections.value.length
    return nodeCount > 0 ? connectionCount / nodeCount : 0
  }

  function calculateDepth(): number {
    // 简化实现
    return Math.max(...nodes.value.map((node: any) => node.y || 0))
  }

  function calculateWidth(): number {
    // 简化实现
    return Math.max(...nodes.value.map((node: any) => node.x || 0))
  }

  function executeWorkflow(): void {
    if (!canExecute.value) return

    workflowState.execution.status = 'running'
    workflowState.execution.startTime = new Date().toISOString()
    workflowState.execution.progress = 0

    // 实际执行逻辑需要根据具体需求实现
  }

  function pauseWorkflow(): void {
    if (workflowState.execution.status === 'running') {
      workflowState.execution.status = 'paused'
    }
  }

  function resumeWorkflow(): void {
    if (workflowState.execution.status === 'paused') {
      workflowState.execution.status = 'running'
    }
  }

  function stopWorkflow(): void {
    workflowState.execution.status = 'idle'
    workflowState.execution.endTime = new Date().toISOString()
  }

  return {
    // 状态
    workflowState,
    workflow,
    nodes,
    connections,
    isValid,
    isDirty,
    isRunning,
    canExecute,
    workflowStats,

    // 方法
    createWorkflow,
    loadWorkflow,
    saveWorkflow,
    executeWorkflow,
    pauseWorkflow,
    resumeWorkflow,
    stopWorkflow,
    markAsDirty,
    markAsSaved,
  }
}

// ========== 导出类型 ==========

export type {
  ExecutionStatus,
  PermissionType,
  WorkflowInfo,
  ExecutionState,
  ValidationState,
  SavingState,
  ImportExportOptions,
  ImportExportState,
  CollaborationState,
  PerformanceState,
  WorkflowState,
  WorkflowStats,
  CreateWorkflowOptions,
}

