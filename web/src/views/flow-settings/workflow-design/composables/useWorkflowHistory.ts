/**
 * 工作流历史记录管理
 * Workflow history management composable
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { useHistoryStore } from '../stores/historyStore.js'
import { useWorkflowStore } from '../stores/workflowStore.js'
import { createStateSnapshot } from '../utils/historyManager.js'

// ========== 类型定义 ==========

/** 工作流状态快照 */
interface WorkflowStateSnapshot {
  nodes: any[]
  connections: any[]
  selectedNodes?: string[]
  selectedConnections?: string[]
  canvasState?: any
  workflowInfo?: any
  [key: string]: any
}

/** 历史记录项 */
interface HistoryItem {
  description: string
  timestamp: string
  tags?: string[]
}

/** 历史记录差异 */
interface HistoryDiff {
  nodes: {
    added: any[]
    removed: any[]
    modified: any[]
  }
  connections: {
    added: any[]
    removed: any[]
    modified: any[]
  }
}

/** 分支数据 */
interface BranchData {
  name: string
  description: string
  createdAt: string
  state: WorkflowStateSnapshot
}

/** 内存使用统计 */
interface MemoryUsageStats {
  bytes: number
  kb: number
  mb: number
}

/** 历史记录性能统计 */
interface HistoryPerformanceStats {
  totalSize: number
  maxSize: number
  memoryUsage: MemoryUsageStats
  autoSaveEnabled: boolean
  autoSaveInterval: number
}

// ========== Composable ==========

export function useWorkflowHistory() {
  const historyStore = useHistoryStore()
  const workflowStore = useWorkflowStore()

  // 本地状态
  const autoSaveEnabled: Ref<boolean> = ref(true)
  const autoSaveInterval: Ref<number> = ref(30000) // 30秒
  const maxUndoSteps: Ref<number> = ref(50)

  let autoSaveTimer: ReturnType<typeof setInterval> | null = null

  // 计算属性
  const canUndo: ComputedRef<boolean> = computed(() => historyStore.canUndo)
  const canRedo: ComputedRef<boolean> = computed(() => historyStore.canRedo)
  const historySize: ComputedRef<number> = computed(() => historyStore.historySize)
  const currentAction: ComputedRef<any> = computed(() => historyStore.currentAction)
  const historyInfo: ComputedRef<any> = computed(() => historyStore.historyInfo)
  const recentActions: ComputedRef<any[]> = computed(() => historyStore.recentActions)

  // 保存当前状态到历史记录
  function saveCurrentState(description: string = ''): void {
    const state = createCurrentStateSnapshot()
    historyStore.saveState(state, description)

    // 重置自动保存计时器
    if (autoSaveEnabled.value) {
      resetAutoSaveTimer()
    }
  }

  // 创建当前状态快照
  function createCurrentStateSnapshot(): WorkflowStateSnapshot {
    return createStateSnapshot(workflowStore.nodes, workflowStore.connections, {
      selectedNodes: workflowStore.selectedNodes,
      selectedConnections: workflowStore.selectedConnections,
      canvasState: workflowStore.canvasState,
      workflowInfo: workflowStore.workflowInfo,
    })
  }

  // 撤销操作
  function undo(): boolean {
    const previousState = historyStore.undo()
    if (previousState) {
      restoreWorkflowState(previousState)
      return true
    }
    return false
  }

  // 重做操作
  function redo(): boolean {
    const nextState = historyStore.redo()
    if (nextState) {
      restoreWorkflowState(nextState)
      return true
    }
    return false
  }

  // 恢复工作流状态
  function restoreWorkflowState(state: WorkflowStateSnapshot): void {
    if (!state) return

    // 恢复节点和连接
    if (state.nodes) {
      workflowStore.nodes.splice(0, workflowStore.nodes.length, ...state.nodes)
    }

    if (state.connections) {
      workflowStore.connections.splice(0, workflowStore.connections.length, ...state.connections)
    }

    // 恢复选择状态
    if (state.selectedNodes) {
      workflowStore.selectedNodes.splice(
        0,
        workflowStore.selectedNodes.length,
        ...state.selectedNodes
      )
    }

    if (state.selectedConnections) {
      workflowStore.selectedConnections.splice(
        0,
        workflowStore.selectedConnections.length,
        ...state.selectedConnections
      )
    }

    // 恢复画布状态
    if (state.canvasState) {
      workflowStore.updateCanvasState(state.canvasState)
    }

    // 恢复工作流信息
    if (state.workflowInfo) {
      workflowStore.updateWorkflowInfo(state.workflowInfo)
    }
  }

  // 跳转到指定历史记录
  function jumpToHistory(index: number): boolean {
    const state = historyStore.jumpToHistory(index)
    if (state) {
      restoreWorkflowState(state)
      return true
    }
    return false
  }

  // 创建检查点
  function createCheckpoint(description: string = '检查点'): void {
    const state = createCurrentStateSnapshot()
    historyStore.createCheckpoint(state, description)
  }

  // 恢复到最近检查点
  function restoreToCheckpoint(): boolean {
    const checkpointState = historyStore.restoreToCheckpoint()
    if (checkpointState) {
      restoreWorkflowState(checkpointState)
      return true
    }
    return false
  }

  // 清空历史记录
  function clearHistory(): void {
    historyStore.clearHistory()
  }

  // 获取历史记录列表
  function getHistoryList(): HistoryItem[] {
    return historyStore.getHistoryList()
  }

  // 获取指定索引的历史记录
  function getHistoryAt(index: number): any {
    return historyStore.getHistoryAt(index)
  }

  // 获取操作统计
  function getActionStats(): any {
    return historyStore.getActionStats()
  }

  // 自动保存功能
  function enableAutoSave(interval: number = autoSaveInterval.value): void {
    autoSaveEnabled.value = true
    autoSaveInterval.value = interval
    startAutoSaveTimer()
  }

  function disableAutoSave(): void {
    autoSaveEnabled.value = false
    stopAutoSaveTimer()
  }

  function startAutoSaveTimer(): void {
    stopAutoSaveTimer()
    autoSaveTimer = setInterval(() => {
      if (workflowStore.editState.isDirty) {
        saveCurrentState('自动保存')
      }
    }, autoSaveInterval.value)
  }

  function stopAutoSaveTimer(): void {
    if (autoSaveTimer) {
      clearInterval(autoSaveTimer)
      autoSaveTimer = null
    }
  }

  function resetAutoSaveTimer(): void {
    if (autoSaveEnabled.value) {
      startAutoSaveTimer()
    }
  }

  // 批量操作历史记录
  function startBatchOperation(description: string = '批量操作'): void {
    // 保存批量操作开始前的状态
    saveCurrentState(`${description} - 开始`)
  }

  function endBatchOperation(description: string = '批量操作'): void {
    // 保存批量操作结束后的状态
    saveCurrentState(`${description} - 完成`)
  }

  // 历史记录压缩
  function compressHistory(keepCount: number = 20): void {
    historyStore.compressHistory(keepCount)
  }

  // 导出历史记录
  function exportHistory(): any {
    return historyStore.exportHistory()
  }

  // 导入历史记录
  function importHistory(historyData: any): void {
    return historyStore.importHistory(historyData)
  }

  // 设置最大历史记录数
  function setMaxHistorySize(size: number): void {
    maxUndoSteps.value = size
    historyStore.setMaxHistorySize(size)
  }

  // 历史记录搜索
  function searchHistory(query: string): HistoryItem[] {
    const historyList = getHistoryList()
    return historyList.filter(
      (item: HistoryItem) =>
        item.description.toLowerCase().includes(query.toLowerCase()) ||
        item.timestamp.includes(query)
    )
  }

  // 获取历史记录差异
  function getHistoryDiff(fromIndex: number, toIndex: number): HistoryDiff | null {
    const fromState = getHistoryAt(fromIndex)
    const toState = getHistoryAt(toIndex)

    if (!fromState || !toState) return null

    return {
      nodes: {
        added: toState.nodes.filter((node: any) => !fromState.nodes.find((n: any) => n.id === node.id)),
        removed: fromState.nodes.filter((node: any) => !toState.nodes.find((n: any) => n.id === node.id)),
        modified: toState.nodes.filter((node: any) => {
          const fromNode = fromState.nodes.find((n: any) => n.id === node.id)
          return fromNode && JSON.stringify(fromNode) !== JSON.stringify(node)
        }),
      },
      connections: {
        added: toState.connections.filter(
          (conn: any) => !fromState.connections.find((c: any) => c.id === conn.id)
        ),
        removed: fromState.connections.filter(
          (conn: any) => !toState.connections.find((c: any) => c.id === conn.id)
        ),
        modified: toState.connections.filter((conn: any) => {
          const fromConn = fromState.connections.find((c: any) => c.id === conn.id)
          return fromConn && JSON.stringify(fromConn) !== JSON.stringify(conn)
        }),
      },
    }
  }

  // 历史记录分支管理
  function createBranch(name: string, description: string = ''): BranchData {
    const currentState = createCurrentStateSnapshot()
    const branchData: BranchData = {
      name,
      description,
      createdAt: new Date().toISOString(),
      state: currentState,
    }

    // 这里可以扩展为更复杂的分支管理
    saveCurrentState(`创建分支: ${name}`)
    return branchData
  }

  // 历史记录标签
  function addHistoryTag(index: number, tag: string): void {
    const historyItem = getHistoryAt(index)
    if (historyItem) {
      historyItem.tags = historyItem.tags || []
      if (!historyItem.tags.includes(tag)) {
        historyItem.tags.push(tag)
      }
    }
  }

  function removeHistoryTag(index: number, tag: string): void {
    const historyItem = getHistoryAt(index)
    if (historyItem && historyItem.tags) {
      const tagIndex = historyItem.tags.indexOf(tag)
      if (tagIndex > -1) {
        historyItem.tags.splice(tagIndex, 1)
      }
    }
  }

  function getHistoryByTag(tag: string): HistoryItem[] {
    const historyList = getHistoryList()
    return historyList.filter((item: any) => item.tags && item.tags.includes(tag))
  }

  // 历史记录性能监控
  function getHistoryPerformanceStats(): HistoryPerformanceStats {
    return {
      totalSize: historySize.value,
      maxSize: maxUndoSteps.value,
      memoryUsage: estimateMemoryUsage(),
      autoSaveEnabled: autoSaveEnabled.value,
      autoSaveInterval: autoSaveInterval.value,
    }
  }

  function estimateMemoryUsage(): MemoryUsageStats {
    const historyList = getHistoryList()
    let totalSize = 0

    historyList.forEach((item: any) => {
      totalSize += JSON.stringify(item).length
    })

    return {
      bytes: totalSize,
      kb: Math.round(totalSize / 1024),
      mb: Math.round(totalSize / (1024 * 1024)),
    }
  }

  // 初始化
  function initialize(): void {
    // 保存初始状态
    saveCurrentState('初始化工作流')

    // 启动自动保存
    if (autoSaveEnabled.value) {
      enableAutoSave()
    }
  }

  // 清理
  function cleanup(): void {
    stopAutoSaveTimer()
  }

  return {
    // 状态
    autoSaveEnabled: computed(() => autoSaveEnabled.value),
    autoSaveInterval: computed(() => autoSaveInterval.value),
    maxUndoSteps: computed(() => maxUndoSteps.value),

    // 计算属性
    canUndo,
    canRedo,
    historySize,
    currentAction,
    historyInfo,
    recentActions,

    // 基础操作
    saveCurrentState,
    undo,
    redo,
    jumpToHistory,
    createCheckpoint,
    restoreToCheckpoint,
    clearHistory,

    // 历史记录查询
    getHistoryList,
    getHistoryAt,
    getActionStats,
    searchHistory,
    getHistoryDiff,

    // 自动保存
    enableAutoSave,
    disableAutoSave,

    // 批量操作
    startBatchOperation,
    endBatchOperation,

    // 高级功能
    compressHistory,
    exportHistory,
    importHistory,
    setMaxHistorySize,
    createBranch,

    // 标签管理
    addHistoryTag,
    removeHistoryTag,
    getHistoryByTag,

    // 性能监控
    getHistoryPerformanceStats,

    // 生命周期
    initialize,
    cleanup,
  }
}

// ========== 导出类型 ==========

export type {
  WorkflowStateSnapshot,
  HistoryItem,
  HistoryDiff,
  BranchData,
  MemoryUsageStats,
  HistoryPerformanceStats,
}

