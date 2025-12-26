/**
 * 维修记录表单缓存管理
 * 实现智能表单缓存，支持多记录编辑状态保持
 */
import { ref, reactive, watch, nextTick, readonly, type Ref, type WatchStopHandle } from 'vue'
import type { RepairRecordData } from './useDataExport'

// ==================== 类型定义 ====================

/** 记录ID类型 */
type RecordId = string | number

/** 缓存键类型 */
type CacheKey = string

/** 缓存数据 */
interface CacheData {
  recordId: RecordId
  formData: Partial<RepairRecordData>
  timestamp: number
  lastModified: number
}

/** 缓存统计信息 */
export interface CacheStats {
  totalCount: number
  cacheKeys: CacheKey[]
  cacheInfo: CacheInfo[]
}

/** 缓存详细信息 */
interface CacheInfo {
  key: CacheKey
  recordId: RecordId
  age: number
  lastModified: number
  hasChanges: boolean
}

/** 切换选项 */
interface SwitchOptions {
  autoSave?: boolean
  mergeWithOriginal?: boolean
  resetIfNoCache?: boolean
}

/** 切换结果 */
export interface SwitchResult {
  hasCache: boolean
  recordId: RecordId
  formData: Partial<RepairRecordData>
  hasRealChanges: boolean
  timestamp: number
  lastModified: number | null
}

/** 表单管理器返回值 */
export interface FormManager {
  // 核心方法
  switchToRecord: (recordId: RecordId, originalData?: Partial<RepairRecordData> | null, options?: SwitchOptions) => Promise<SwitchResult>
  saveCurrentForm: () => void
  resetToCache: () => void
  clearCurrentCache: () => void

  // 自动保存
  startAutoSave: (interval?: number) => void
  stopAutoSave: () => void

  // 状态检查
  hasUnsavedChanges: () => boolean
  isLoading: () => boolean
  getCurrentRecordId: () => RecordId | null
  hasCacheData: (recordId?: RecordId) => boolean
  getCacheStats: () => CacheStats
}

/** 监听选项 */
interface WatchOptions {
  debounce?: number
  deep?: boolean
}

/** 全局缓存统计 */
export interface GlobalCacheStats {
  totalCaches: number
  currentRecord: RecordId | null
  cacheEnabled: boolean
  cacheKeys: CacheKey[]
}

// ==================== 全局状态 ====================

// 全局缓存存储（会话级别，页面刷新后清除）
const formCacheStore = reactive(new Map<CacheKey, CacheData>())
const currentRecordId: Ref<RecordId | null> = ref(null)
const cacheEnabled: Ref<boolean> = ref(true)

/**
 * 获取默认表单数据结构
 * @returns 默认表单数据
 */
const getDefaultFormData = (): Partial<RepairRecordData> => ({
  // 基础信息
  repair_date: undefined,
  category: '',
  device_number: '',
  device_name: '',
  brand: '',
  model: '',
  pin_type: '',
  repair_completion_date: undefined,

  // 公司信息
  company: '',
  department: '',
  workshop: '',
  construction_unit: '',
  applicant: '',
  phone: '',

  // 故障信息
  is_fault: true,
  fault_reason: '',
  damage_category: '',
  fault_content: '',
  fault_location: '',

  // 维修信息
  repair_content: '',
  parts_name: '',
  repairer: '',
  remarks: '',
})

// ==================== Composable ====================

export function useFormCache() {
  /**
   * 获取缓存键
   * @param recordId - 记录ID，'new' 表示新建
   * @returns 缓存键
   */
  const getCacheKey = (recordId: RecordId): CacheKey => {
    return recordId ? `repair_record_${recordId}` : 'repair_record_new'
  }

  /**
   * 保存表单数据到缓存
   * @param recordId - 记录ID
   * @param formData - 表单数据
   */
  const saveToCache = (recordId: RecordId, formData: Partial<RepairRecordData>): void => {
    if (!cacheEnabled.value) return

    const cacheKey = getCacheKey(recordId)
    const cacheData: CacheData = {
      recordId,
      formData: { ...formData },
      timestamp: Date.now(),
      lastModified: Date.now(),
    }

    formCacheStore.set(cacheKey, cacheData)

    console.log(`[FormCache] 保存缓存: ${cacheKey}`, {
      recordId,
      dataKeys: Object.keys(formData),
      timestamp: new Date(cacheData.timestamp).toLocaleTimeString(),
    })
  }

  /**
   * 从缓存加载表单数据
   * @param recordId - 记录ID
   * @returns 缓存的表单数据或null
   */
  const loadFromCache = (recordId: RecordId): Partial<RepairRecordData> | null => {
    if (!cacheEnabled.value) return null

    const cacheKey = getCacheKey(recordId)
    const cacheData = formCacheStore.get(cacheKey)

    if (cacheData) {
      console.log(`[FormCache] 加载缓存: ${cacheKey}`, {
        recordId: cacheData.recordId,
        age: `${Math.round((Date.now() - cacheData.timestamp) / 1000)}秒前`,
        lastModified: new Date(cacheData.lastModified).toLocaleTimeString(),
      })

      return { ...cacheData.formData }
    }

    console.log(`[FormCache] 缓存未找到: ${cacheKey}`)
    return null
  }

  /**
   * 检查缓存是否存在
   * @param recordId - 记录ID
   * @returns 是否存在缓存
   */
  const hasCacheData = (recordId: RecordId): boolean => {
    const cacheKey = getCacheKey(recordId)
    return formCacheStore.has(cacheKey)
  }

  /**
   * 删除指定记录的缓存
   * @param recordId - 记录ID
   */
  const removeFromCache = (recordId: RecordId): void => {
    const cacheKey = getCacheKey(recordId)
    const removed = formCacheStore.delete(cacheKey)

    if (removed) {
      console.log(`[FormCache] 删除缓存: ${cacheKey}`)
    }
  }

  /**
   * 清空所有缓存
   */
  const clearAllCache = (): void => {
    const count = formCacheStore.size
    formCacheStore.clear()
    console.log(`[FormCache] 清空所有缓存，共删除 ${count} 项`)
  }

  /**
   * 获取缓存统计信息
   * @returns 缓存统计
   */
  const getCacheStats = (): CacheStats => {
    const stats: CacheStats = {
      totalCount: formCacheStore.size,
      cacheKeys: Array.from(formCacheStore.keys()),
      cacheInfo: [],
    }

    formCacheStore.forEach((data, key) => {
      stats.cacheInfo.push({
        key,
        recordId: data.recordId,
        age: Date.now() - data.timestamp,
        lastModified: data.lastModified,
        hasChanges: data.lastModified > data.timestamp,
      })
    })

    return stats
  }

  /**
   * 智能表单数据管理器
   * @param formData - 响应式表单数据对象
   * @returns 表单管理器
   */
  const createFormManager = (formData: Partial<RepairRecordData>): FormManager => {
    let isLoading = false
    let autoSaveTimer: ReturnType<typeof setInterval> | null = null

    /**
     * 切换到指定记录
     * @param recordId - 记录ID
     * @param originalData - 原始数据（从API获取）
     * @param options - 选项
     * @returns 切换结果信息
     */
    const switchToRecord = async (
      recordId: RecordId,
      originalData: Partial<RepairRecordData> | null = null,
      options: SwitchOptions = {}
    ): Promise<SwitchResult> => {
      const { autoSave = true, mergeWithOriginal = true, resetIfNoCache = true } = options

      // 如果当前有记录在编辑，先保存当前表单状态
      if (currentRecordId.value && currentRecordId.value !== recordId && autoSave) {
        saveToCache(currentRecordId.value, formData)
      }

      isLoading = true
      currentRecordId.value = recordId

      try {
        // 尝试从缓存加载
        const cachedData = loadFromCache(recordId)
        let hasRealChanges = false

        if (cachedData) {
          // 检查缓存数据是否与原始数据不同（即真正被编辑过）
          if (originalData) {
            // 比较缓存数据和原始数据，看是否有实际修改
            hasRealChanges = Object.keys(cachedData).some((key) => {
              const cachedValue = cachedData[key as keyof RepairRecordData]
              const originalValue = originalData[key as keyof RepairRecordData]

              // 处理空值比较
              const normalizedCached =
                cachedValue === null || cachedValue === undefined ? '' : String(cachedValue)
              const normalizedOriginal =
                originalValue === null || originalValue === undefined ? '' : String(originalValue)

              return normalizedCached !== normalizedOriginal
            })
          } else {
            // 新建记录，检查是否有非空字段
            hasRealChanges = Object.values(cachedData).some((value) => {
              return value !== null && value !== undefined && value !== ''
            })
          }

          // 如果有缓存数据，使用缓存
          console.log(`[FormManager] 使用缓存数据切换到记录: ${recordId}`, { hasRealChanges })
          Object.assign(formData, cachedData)
        } else if (originalData && mergeWithOriginal) {
          // 如果没有缓存但有原始数据，使用原始数据
          console.log(`[FormManager] 使用原始数据切换到记录: ${recordId}`)
          Object.assign(formData, originalData)

          // 立即保存到缓存作为基准
          if (autoSave) {
            saveToCache(recordId, originalData)
          }
        } else if (resetIfNoCache) {
          // 如果没有缓存也没有原始数据，重置为默认值
          console.log(`[FormManager] 重置表单数据切换到记录: ${recordId}`)
          Object.assign(formData, getDefaultFormData())
        }

        // 等待DOM更新
        await nextTick()

        console.log(`[FormManager] 成功切换到记录: ${recordId}`, {
          hasCache: !!cachedData,
          hasRealChanges,
          hasOriginal: !!originalData,
          currentData: { ...formData },
        })

        // 返回切换结果信息
        const cacheData = formCacheStore.get(getCacheKey(recordId))
        return {
          hasCache: !!cachedData && hasRealChanges, // 只有真正有变化时才标记为有缓存
          recordId,
          formData: { ...formData },
          hasRealChanges,
          timestamp: cacheData ? cacheData.timestamp : Date.now(),
          lastModified: cacheData ? cacheData.lastModified : null,
        }
      } catch (error) {
        console.error(`[FormManager] 切换记录失败: ${recordId}`, error)
        throw error
      } finally {
        isLoading = false
      }
    }

    /**
     * 启动自动保存
     * @param interval - 自动保存间隔（毫秒）
     */
    const startAutoSave = (interval: number = 2000): void => {
      if (autoSaveTimer) {
        clearInterval(autoSaveTimer)
      }

      autoSaveTimer = setInterval(() => {
        if (currentRecordId.value && !isLoading) {
          saveToCache(currentRecordId.value, formData)
        }
      }, interval)

      console.log(`[FormManager] 启动自动保存，间隔: ${interval}ms`)
    }

    /**
     * 停止自动保存
     */
    const stopAutoSave = (): void => {
      if (autoSaveTimer) {
        clearInterval(autoSaveTimer)
        autoSaveTimer = null
        console.log('[FormManager] 停止自动保存')
      }
    }

    /**
     * 手动保存当前表单
     */
    const saveCurrentForm = (): void => {
      if (currentRecordId.value) {
        saveToCache(currentRecordId.value, formData)
      }
    }

    /**
     * 重置当前表单到缓存状态
     */
    const resetToCache = (): void => {
      if (currentRecordId.value) {
        const cachedData = loadFromCache(currentRecordId.value)
        if (cachedData) {
          Object.assign(formData, cachedData)
          console.log(`[FormManager] 重置表单到缓存状态: ${currentRecordId.value}`)
        }
      }
    }

    /**
     * 检查当前表单是否有未保存的更改
     * @returns 是否有未保存的更改
     */
    const hasUnsavedChanges = (): boolean => {
      if (!currentRecordId.value) return false

      const cachedData = loadFromCache(currentRecordId.value)
      if (!cachedData) return true

      // 简单的深度比较
      return JSON.stringify(formData) !== JSON.stringify(cachedData)
    }

    /**
     * 清理当前记录的缓存
     */
    const clearCurrentCache = (): void => {
      if (currentRecordId.value) {
        removeFromCache(currentRecordId.value)
      }
    }

    return {
      // 核心方法
      switchToRecord,
      saveCurrentForm,
      resetToCache,
      clearCurrentCache,

      // 自动保存
      startAutoSave,
      stopAutoSave,

      // 状态检查
      hasUnsavedChanges,
      isLoading: () => isLoading,
      getCurrentRecordId: () => currentRecordId.value,

      // 缓存管理
      hasCacheData: (recordId?: RecordId) => hasCacheData(recordId || currentRecordId.value || ''),
      getCacheStats,
    }
  }

  /**
   * 监听表单数据变化并自动保存
   * @param formData - 响应式表单数据
   * @param options - 选项
   * @returns 停止监听函数
   */
  const watchFormChanges = (
    formData: Partial<RepairRecordData>,
    options: WatchOptions = {}
  ): WatchStopHandle => {
    const { debounce = 1000, deep = true } = options

    let saveTimer: ReturnType<typeof setTimeout> | null = null

    const stopWatcher = watch(
      () => formData,
      () => {
        if (currentRecordId.value && cacheEnabled.value) {
          // 防抖保存
          if (saveTimer) {
            clearTimeout(saveTimer)
          }

          saveTimer = setTimeout(() => {
            if (currentRecordId.value) {
              saveToCache(currentRecordId.value, formData)
            }
          }, debounce)
        }
      },
      { deep }
    )

    return stopWatcher
  }

  return {
    // 基础缓存操作
    saveToCache,
    loadFromCache,
    removeFromCache,
    clearAllCache,
    hasCacheData,
    getCacheStats,

    // 表单管理器
    createFormManager,
    watchFormChanges,

    // 全局状态
    currentRecordId: readonly(currentRecordId),
    cacheEnabled: readonly(cacheEnabled),

    // 工具方法
    getDefaultFormData,

    // 缓存控制
    enableCache: () => {
      cacheEnabled.value = true
    },
    disableCache: () => {
      cacheEnabled.value = false
    },
  }
}

// ==================== 全局导出 ====================

/**
 * 导出缓存统计信息（用于调试）
 * @returns 全局缓存统计
 */
export const getGlobalCacheStats = (): GlobalCacheStats => {
  return {
    totalCaches: formCacheStore.size,
    currentRecord: currentRecordId.value,
    cacheEnabled: cacheEnabled.value,
    cacheKeys: Array.from(formCacheStore.keys()),
  }
}

// 开发环境下暴露到全局（用于调试）
if (import.meta.env.DEV) {
  ;(window as any).__repairFormCache = {
    store: formCacheStore,
    currentRecordId,
    getStats: getGlobalCacheStats,
    clearAll: () => formCacheStore.clear(),
  }
}

