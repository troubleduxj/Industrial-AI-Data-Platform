/**
 * 历史记录状态管理
 * History management store
 */

import { defineStore } from 'pinia'
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { createHistoryManager, ACTION_TYPES } from '../utils/historyManager.js'

// ========== 类型定义 ==========

/** 历史记录数据（临时类型，等 utils 迁移后会有完整定义） */
interface HistoryData {
  history: any[]
  currentIndex: number
  maxSize: number
  exportedAt: string
}

/** 历史记录管理器接口（临时） */
interface HistoryManager {
  canUndo(): boolean
  canRedo(): boolean
  getHistorySize(): number
  getCurrentAction(): any
  getHistoryInfo(): any
  getRecentActions(count: number): any[]
  saveState(state: any, actionDescription: string): void
  undo(): any | null
  redo(): any | null
  jumpTo(index: number): any | null
  clear(): void
  setMaxSize(size: number): void
  getHistoryAt(index: number): any
  getHistoryList(): any[]
  createCheckpoint(state: any, description: string): void
  restoreToCheckpoint(): any | null
  getActionStats(): any
  exportHistory(): any
  importHistory(history: any): void
  compress(keepCount: number): void
  getCurrentIndex(): number
}

// ========== Store 定义 ==========

export const useHistoryStore = defineStore('workflowHistory', () => {
  // 历史记录管理器
  const historyManager: HistoryManager = createHistoryManager(100) // 最多保存100条历史记录

  // 当前状态
  const currentIndex: Ref<number> = ref(-1)
  const maxHistorySize: Ref<number> = ref(100)

  // 计算属性
  const canUndo: ComputedRef<boolean> = computed(() => historyManager.canUndo())
  const canRedo: ComputedRef<boolean> = computed(() => historyManager.canRedo())
  const historySize: ComputedRef<number> = computed(() => historyManager.getHistorySize())
  const currentAction: ComputedRef<any> = computed(() => historyManager.getCurrentAction())

  // 获取历史记录信息
  const historyInfo: ComputedRef<any> = computed(() => {
    return historyManager.getHistoryInfo()
  })

  // 获取最近的操作列表
  const recentActions: ComputedRef<any[]> = computed(() => {
    return historyManager.getRecentActions(10)
  })

  // 保存状态到历史记录
  function saveState(state: any, actionDescription: string = ''): void {
    historyManager.saveState(state, actionDescription)
    currentIndex.value = historyManager.getCurrentIndex()
  }

  // 撤销操作
  function undo(): any | null {
    const previousState = historyManager.undo()
    if (previousState) {
      currentIndex.value = historyManager.getCurrentIndex()
      return previousState
    }
    return null
  }

  // 重做操作
  function redo(): any | null {
    const nextState = historyManager.redo()
    if (nextState) {
      currentIndex.value = historyManager.getCurrentIndex()
      return nextState
    }
    return null
  }

  // 跳转到指定历史记录
  function jumpToHistory(index: number): any | null {
    const state = historyManager.jumpTo(index)
    if (state) {
      currentIndex.value = index
      return state
    }
    return null
  }

  // 清空历史记录
  function clearHistory(): void {
    historyManager.clear()
    currentIndex.value = -1
  }

  // 设置最大历史记录数量
  function setMaxHistorySize(size: number): void {
    maxHistorySize.value = size
    historyManager.setMaxSize(size)
  }

  // 获取指定索引的历史记录
  function getHistoryAt(index: number): any {
    return historyManager.getHistoryAt(index)
  }

  // 获取历史记录列表（用于历史面板显示）
  function getHistoryList(): any[] {
    return historyManager.getHistoryList()
  }

  // 创建检查点（重要状态保存）
  function createCheckpoint(state: any, description: string = '检查点'): void {
    historyManager.createCheckpoint(state, description)
    currentIndex.value = historyManager.getCurrentIndex()
  }

  // 恢复到最近的检查点
  function restoreToCheckpoint(): any | null {
    const checkpointState = historyManager.restoreToCheckpoint()
    if (checkpointState) {
      currentIndex.value = historyManager.getCurrentIndex()
      return checkpointState
    }
    return null
  }

  // 获取操作统计信息
  function getActionStats(): any {
    return historyManager.getActionStats()
  }

  // 导出历史记录
  function exportHistory(): HistoryData {
    return {
      history: historyManager.exportHistory(),
      currentIndex: currentIndex.value,
      maxSize: maxHistorySize.value,
      exportedAt: new Date().toISOString(),
    }
  }

  // 导入历史记录
  function importHistory(historyData: Partial<HistoryData>): boolean {
    if (historyData.history) {
      historyManager.importHistory(historyData.history)
      currentIndex.value = historyData.currentIndex || -1
      maxHistorySize.value = historyData.maxSize || 100
      return true
    }
    return false
  }

  // 压缩历史记录（移除过旧的记录）
  function compressHistory(keepCount: number = 50): void {
    historyManager.compress(keepCount)
    currentIndex.value = historyManager.getCurrentIndex()
  }

  return {
    // 状态
    currentIndex: computed(() => currentIndex.value),
    maxHistorySize: computed(() => maxHistorySize.value),

    // 计算属性
    canUndo,
    canRedo,
    historySize,
    currentAction,
    historyInfo,
    recentActions,

    // 方法
    saveState,
    undo,
    redo,
    jumpToHistory,
    clearHistory,
    setMaxHistorySize,
    getHistoryAt,
    getHistoryList,
    createCheckpoint,
    restoreToCheckpoint,
    getActionStats,
    exportHistory,
    importHistory,
    compressHistory,
  }
})

// 操作类型常量
export { ACTION_TYPES } from '../utils/historyManager.js'

// ========== 导出类型 ==========

export type { HistoryData, HistoryManager }

