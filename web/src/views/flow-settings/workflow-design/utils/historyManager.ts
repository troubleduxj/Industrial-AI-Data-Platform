/**
 * 历史记录管理工具函数
 * History management utilities for undo/redo functionality
 */

// ========== 类型定义 ==========

/** 历史记录项 */
interface HistoryItem<T = any> {
  state: T
  action: string
  timestamp: number
}

/** 历史信息 */
interface HistoryInfo {
  total: number
  currentIndex: number
  canUndo: boolean
  canRedo: boolean
  currentAction: string
}

/** 历史记录列表项 */
interface HistoryListItem {
  index: number
  action: string
  timestamp: number
  isCurrent: boolean
}

/** 状态快照 */
interface StateSnapshot {
  nodes: any[]
  connections: any[]
  timestamp: number
  [key: string]: any
}

/** 操作数据 */
interface ActionData {
  nodeType?: string
  nodeName?: string
  count?: number
  [key: string]: any
}

// ========== 历史记录管理器类 ==========

/**
 * 历史记录管理器类
 */
export class HistoryManager<T = any> {
  private history: HistoryItem<T>[]
  private currentIndex: number
  private maxHistorySize: number

  constructor(maxHistorySize: number = 50) {
    this.history = []
    this.currentIndex = -1
    this.maxHistorySize = maxHistorySize
  }

  /**
   * 保存当前状态到历史记录
   * @param state - 当前状态
   * @param action - 操作描述
   */
  saveState(state: T, action: string = ''): void {
    // 深拷贝状态以避免引用问题
    const stateCopy = this.deepClone(state)

    // 如果当前不在历史记录的末尾，删除后面的记录
    if (this.currentIndex < this.history.length - 1) {
      this.history = this.history.slice(0, this.currentIndex + 1)
    }

    // 添加新状态
    this.history.push({
      state: stateCopy,
      action,
      timestamp: Date.now(),
    })

    // 限制历史记录大小
    if (this.history.length > this.maxHistorySize) {
      this.history.shift()
    } else {
      this.currentIndex++
    }
  }

  /**
   * 撤销操作
   * @returns 上一个状态
   */
  undo(): T | null {
    if (this.canUndo()) {
      this.currentIndex--
      return this.deepClone(this.history[this.currentIndex].state)
    }
    return null
  }

  /**
   * 重做操作
   * @returns 下一个状态
   */
  redo(): T | null {
    if (this.canRedo()) {
      this.currentIndex++
      return this.deepClone(this.history[this.currentIndex].state)
    }
    return null
  }

  /**
   * 检查是否可以撤销
   * @returns boolean
   */
  canUndo(): boolean {
    return this.currentIndex > 0
  }

  /**
   * 检查是否可以重做
   * @returns boolean
   */
  canRedo(): boolean {
    return this.currentIndex < this.history.length - 1
  }

  /**
   * 获取当前状态
   * @returns 当前状态或null
   */
  getCurrentState(): T | null {
    if (this.currentIndex >= 0 && this.currentIndex < this.history.length) {
      return this.deepClone(this.history[this.currentIndex].state)
    }
    return null
  }

  /**
   * 获取历史记录信息
   * @returns 历史信息
   */
  getHistoryInfo(): HistoryInfo {
    return {
      total: this.history.length,
      currentIndex: this.currentIndex,
      canUndo: this.canUndo(),
      canRedo: this.canRedo(),
      currentAction: this.currentIndex >= 0 ? this.history[this.currentIndex].action : '',
    }
  }

  /**
   * 获取历史记录列表
   * @returns 历史记录列表
   */
  getHistoryList(): HistoryListItem[] {
    return this.history.map((item, index) => ({
      index,
      action: item.action,
      timestamp: item.timestamp,
      isCurrent: index === this.currentIndex,
    }))
  }

  /**
   * 跳转到指定历史记录
   * @param index - 历史记录索引
   * @returns 指定状态或null
   */
  jumpToState(index: number): T | null {
    if (index >= 0 && index < this.history.length) {
      this.currentIndex = index
      return this.deepClone(this.history[index].state)
    }
    return null
  }

  /**
   * 获取历史记录大小
   * @returns 历史记录数量
   */
  getHistorySize(): number {
    return this.history.length
  }

  /**
   * 获取当前索引
   * @returns 当前索引
   */
  getCurrentIndex(): number {
    return this.currentIndex
  }

  /**
   * 获取当前操作
   * @returns 当前操作描述
   */
  getCurrentAction(): string {
    if (this.currentIndex >= 0 && this.currentIndex < this.history.length) {
      return this.history[this.currentIndex].action
    }
    return ''
  }

  /**
   * 获取最近的操作列表
   * @param count - 数量
   * @returns 最近的操作列表
   */
  getRecentActions(count: number): HistoryListItem[] {
    const startIndex = Math.max(0, this.history.length - count)
    return this.history.slice(startIndex).map((item, index) => ({
      index: startIndex + index,
      action: item.action,
      timestamp: item.timestamp,
      isCurrent: startIndex + index === this.currentIndex,
    }))
  }

  /**
   * 跳转到指定索引
   * @param index - 索引
   * @returns 状态或null
   */
  jumpTo(index: number): T | null {
    return this.jumpToState(index)
  }

  /**
   * 设置最大历史记录大小
   * @param size - 大小
   */
  setMaxSize(size: number): void {
    this.maxHistorySize = size
    while (this.history.length > this.maxHistorySize) {
      this.history.shift()
      this.currentIndex--
    }
  }

  /**
   * 获取指定索引的历史记录
   * @param index - 索引
   * @returns 历史记录或null
   */
  getHistoryAt(index: number): HistoryItem<T> | null {
    if (index >= 0 && index < this.history.length) {
      return { ...this.history[index] }
    }
    return null
  }

  /**
   * 创建检查点（重要状态保存）
   * @param state - 状态
   * @param description - 描述
   */
  createCheckpoint(state: T, description: string = '检查点'): void {
    this.saveState(state, `[检查点] ${description}`)
  }

  /**
   * 恢复到最近的检查点
   * @returns 检查点状态或null
   */
  restoreToCheckpoint(): T | null {
    // 从当前位置向前查找最近的检查点
    for (let i = this.currentIndex - 1; i >= 0; i--) {
      if (this.history[i].action.startsWith('[检查点]')) {
        this.currentIndex = i
        return this.deepClone(this.history[i].state)
      }
    }
    return null
  }

  /**
   * 获取操作统计信息
   * @returns 统计信息
   */
  getActionStats(): Record<string, number> {
    const stats: Record<string, number> = {}
    this.history.forEach(item => {
      const action = item.action.replace(/\[检查点\]\s*/, '').split(':')[0]
      stats[action] = (stats[action] || 0) + 1
    })
    return stats
  }

  /**
   * 导出历史记录
   * @returns 历史记录数组
   */
  exportHistory(): HistoryItem<T>[] {
    return this.history.map(item => ({ ...item }))
  }

  /**
   * 导入历史记录
   * @param history - 历史记录数组
   */
  importHistory(history: HistoryItem<T>[]): void {
    this.history = history.map(item => ({ ...item }))
    this.currentIndex = this.history.length - 1
  }

  /**
   * 压缩历史记录（移除过旧的记录）
   * @param keepCount - 保留数量
   */
  compress(keepCount: number): void {
    if (this.history.length > keepCount) {
      const removeCount = this.history.length - keepCount
      this.history = this.history.slice(removeCount)
      this.currentIndex = Math.max(-1, this.currentIndex - removeCount)
    }
  }

  /**
   * 清空历史记录
   */
  clear(): void {
    this.history = []
    this.currentIndex = -1
  }

  /**
   * 深拷贝对象
   * @param obj - 要拷贝的对象
   * @returns 拷贝后的对象
   */
  private deepClone<U>(obj: U): U {
    if (obj === null || typeof obj !== 'object') {
      return obj
    }

    if (obj instanceof Date) {
      return new Date(obj.getTime()) as any
    }

    if (obj instanceof Array) {
      return obj.map((item) => this.deepClone(item)) as any
    }

    if (typeof obj === 'object') {
      const cloned: any = {}
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          cloned[key] = this.deepClone(obj[key])
        }
      }
      return cloned
    }

    return obj
  }
}

// ========== 工厂函数 ==========

/**
 * 创建历史记录管理器实例
 * @param maxHistorySize - 最大历史记录数量
 * @returns HistoryManager实例
 */
export function createHistoryManager<T = any>(maxHistorySize: number = 50): HistoryManager<T> {
  return new HistoryManager<T>(maxHistorySize)
}

// ========== 状态快照工具 ==========

/**
 * 比较两个状态是否相同
 * @param state1 - 状态1
 * @param state2 - 状态2
 * @returns boolean
 */
export function compareStates(state1: any, state2: any): boolean {
  return JSON.stringify(state1) === JSON.stringify(state2)
}

/**
 * 创建状态快照
 * @param nodes - 节点列表
 * @param connections - 连接列表
 * @param additionalData - 额外数据
 * @returns 状态快照
 */
export function createStateSnapshot(
  nodes: any[],
  connections: any[],
  additionalData: Record<string, any> = {}
): StateSnapshot {
  return {
    nodes: nodes.map((node) => ({ ...node })),
    connections: connections.map((conn) => ({ ...conn })),
    timestamp: Date.now(),
    ...additionalData,
  }
}

/**
 * 应用状态快照
 * @param snapshot - 状态快照
 * @returns 状态对象
 */
export function applyStateSnapshot(snapshot: StateSnapshot): StateSnapshot {
  return {
    nodes: snapshot.nodes.map((node) => ({ ...node })),
    connections: snapshot.connections.map((conn) => ({ ...conn })),
    ...snapshot,
  }
}

// ========== 操作类型常量 ==========

/**
 * 操作类型常量
 */
export const ACTION_TYPES = {
  ADD_NODE: 'add_node',
  DELETE_NODE: 'delete_node',
  MOVE_NODE: 'move_node',
  UPDATE_NODE: 'update_node',
  UPDATE_CONNECTION: 'update_connection',
  ADD_CONNECTION: 'add_connection',
  DELETE_CONNECTION: 'delete_connection',
  PASTE_NODES: 'paste_nodes',
  DUPLICATE_NODES: 'duplicate_nodes',
  GROUP_NODES: 'group_nodes',
  UNGROUP_NODES: 'ungroup_nodes',
  CLEAR_CANVAS: 'clear_canvas',
  IMPORT_WORKFLOW: 'import_workflow',
  BATCH_UPDATE: 'batch_update',
} as const

export type ActionType = typeof ACTION_TYPES[keyof typeof ACTION_TYPES]

// ========== 工具函数 ==========

/**
 * 获取操作描述
 * @param actionType - 操作类型
 * @param data - 操作数据
 * @returns 操作描述
 */
export function getActionDescription(actionType: string, data: ActionData = {}): string {
  const descriptions: Record<string, string | ((data: ActionData) => string)> = {
    [ACTION_TYPES.ADD_NODE]: (d) => `添加节点: ${d.nodeType || '未知类型'}`,
    [ACTION_TYPES.DELETE_NODE]: (d) => `删除节点: ${d.nodeName || '未知节点'}`,
    [ACTION_TYPES.MOVE_NODE]: (d) => `移动节点: ${d.nodeName || '未知节点'}`,
    [ACTION_TYPES.UPDATE_NODE]: (d) => `更新节点: ${d.nodeName || '未知节点'}`,
    [ACTION_TYPES.UPDATE_CONNECTION]: '更新连接',
    [ACTION_TYPES.ADD_CONNECTION]: '添加连接',
    [ACTION_TYPES.DELETE_CONNECTION]: '删除连接',
    [ACTION_TYPES.PASTE_NODES]: (d) => `粘贴节点: ${d.count || 0}个`,
    [ACTION_TYPES.DUPLICATE_NODES]: (d) => `复制节点: ${d.count || 0}个`,
    [ACTION_TYPES.GROUP_NODES]: (d) => `组合节点: ${d.count || 0}个`,
    [ACTION_TYPES.UNGROUP_NODES]: '取消组合',
    [ACTION_TYPES.CLEAR_CANVAS]: '清空画布',
    [ACTION_TYPES.IMPORT_WORKFLOW]: '导入工作流',
    [ACTION_TYPES.BATCH_UPDATE]: '批量更新',
  }

  const desc = descriptions[actionType]
  if (typeof desc === 'function') {
    return desc(data)
  }
  return desc || '未知操作'
}

// ========== 历史记录工具对象 ==========

/**
 * 历史记录工具函数
 */
export const historyUtils = {
  /**
   * 节流保存状态
   * @param saveFunction - 保存函数
   * @param delay - 延迟时间
   * @returns 节流函数
   */
  throttleSave<F extends (...args: any[]) => any>(saveFunction: F, delay: number = 300): F {
    let timeoutId: NodeJS.Timeout | null = null
    let lastSaveTime = 0

    return function (this: any, ...args: Parameters<F>): void {
      const now = Date.now()

      if (now - lastSaveTime >= delay) {
        saveFunction.apply(this, args)
        lastSaveTime = now
      } else {
        if (timeoutId) clearTimeout(timeoutId)
        timeoutId = setTimeout(() => {
          saveFunction.apply(this, args)
          lastSaveTime = Date.now()
        }, delay - (now - lastSaveTime))
      }
    } as F
  },

  /**
   * 防抖保存状态
   * @param saveFunction - 保存函数
   * @param delay - 延迟时间
   * @returns 防抖函数
   */
  debounceSave<F extends (...args: any[]) => any>(saveFunction: F, delay: number = 500): F {
    let timeoutId: NodeJS.Timeout | null = null

    return function (this: any, ...args: Parameters<F>): void {
      if (timeoutId) clearTimeout(timeoutId)
      timeoutId = setTimeout(() => {
        saveFunction.apply(this, args)
      }, delay)
    } as F
  },
}

// ========== 导出类型 ==========

export type {
  HistoryItem,
  HistoryInfo,
  HistoryListItem,
  StateSnapshot,
  ActionData,
}

