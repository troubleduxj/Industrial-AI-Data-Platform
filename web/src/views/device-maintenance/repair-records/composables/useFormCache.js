/**
 * 维修记录表单缓存管理
 * 实现智能表单缓存，支持多记录编辑状态保持
 */
import { ref, reactive, watch, nextTick } from 'vue'

// 全局缓存存储（会话级别，页面刷新后清除）
const formCacheStore = reactive(new Map())
const currentRecordId = ref(null)
const cacheEnabled = ref(true)

// 默认表单数据结构
const getDefaultFormData = () => ({
  // 基础信息
  repair_date: null,
  category: '',
  device_number: '',
  device_name: '',
  brand: '',
  model: '',
  pin_type: '',
  repair_completion_date: null,

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
  repair_completion_date: null,
  remarks: '',
})

export function useFormCache() {
  /**
   * 获取缓存键
   * @param {string|number} recordId - 记录ID，'new' 表示新建
   * @returns {string}
   */
  const getCacheKey = (recordId) => {
    return recordId ? `repair_record_${recordId}` : 'repair_record_new'
  }

  /**
   * 保存表单数据到缓存
   * @param {string|number} recordId - 记录ID
   * @param {Object} formData - 表单数据
   */
  const saveToCache = (recordId, formData) => {
    if (!cacheEnabled.value) return

    const cacheKey = getCacheKey(recordId)
    const cacheData = {
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
   * @param {string|number} recordId - 记录ID
   * @returns {Object|null}
   */
  const loadFromCache = (recordId) => {
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
   * @param {string|number} recordId - 记录ID
   * @returns {boolean}
   */
  const hasCacheData = (recordId) => {
    const cacheKey = getCacheKey(recordId)
    return formCacheStore.has(cacheKey)
  }

  /**
   * 删除指定记录的缓存
   * @param {string|number} recordId - 记录ID
   */
  const removeFromCache = (recordId) => {
    const cacheKey = getCacheKey(recordId)
    const removed = formCacheStore.delete(cacheKey)

    if (removed) {
      console.log(`[FormCache] 删除缓存: ${cacheKey}`)
    }
  }

  /**
   * 清空所有缓存
   */
  const clearAllCache = () => {
    const count = formCacheStore.size
    formCacheStore.clear()
    console.log(`[FormCache] 清空所有缓存，共删除 ${count} 项`)
  }

  /**
   * 获取缓存统计信息
   * @returns {Object}
   */
  const getCacheStats = () => {
    const stats = {
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
   * @param {Object} formData - 响应式表单数据对象
   * @returns {Object}
   */
  const createFormManager = (formData) => {
    let isLoading = false
    let autoSaveTimer = null

    /**
     * 切换到指定记录
     * @param {string|number} recordId - 记录ID
     * @param {Object} originalData - 原始数据（从API获取）
     * @param {Object} options - 选项
     * @returns {Object} 切换结果信息
     */
    const switchToRecord = async (recordId, originalData = null, options = {}) => {
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
              const cachedValue = cachedData[key]
              const originalValue = originalData[key]

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
        return {
          hasCache: !!cachedData && hasRealChanges, // 只有真正有变化时才标记为有缓存
          recordId,
          formData: { ...formData },
          hasRealChanges,
          timestamp: cachedData ? cachedData.timestamp : Date.now(),
          lastModified: cachedData ? cachedData.lastModified : null,
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
     * @param {number} interval - 自动保存间隔（毫秒）
     */
    const startAutoSave = (interval = 2000) => {
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
    const stopAutoSave = () => {
      if (autoSaveTimer) {
        clearInterval(autoSaveTimer)
        autoSaveTimer = null
        console.log('[FormManager] 停止自动保存')
      }
    }

    /**
     * 手动保存当前表单
     */
    const saveCurrentForm = () => {
      if (currentRecordId.value) {
        saveToCache(currentRecordId.value, formData)
      }
    }

    /**
     * 重置当前表单到缓存状态
     */
    const resetToCache = () => {
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
     * @returns {boolean}
     */
    const hasUnsavedChanges = () => {
      if (!currentRecordId.value) return false

      const cachedData = loadFromCache(currentRecordId.value)
      if (!cachedData) return true

      // 简单的深度比较
      return JSON.stringify(formData) !== JSON.stringify(cachedData)
    }

    /**
     * 清理当前记录的缓存
     */
    const clearCurrentCache = () => {
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
      hasCacheData: (recordId) => hasCacheData(recordId || currentRecordId.value),
      getCacheStats,
    }
  }

  /**
   * 监听表单数据变化并自动保存
   * @param {Object} formData - 响应式表单数据
   * @param {Object} options - 选项
   */
  const watchFormChanges = (formData, options = {}) => {
    const { debounce = 1000, deep = true } = options

    let saveTimer = null

    const stopWatcher = watch(
      formData,
      () => {
        if (currentRecordId.value && cacheEnabled.value) {
          // 防抖保存
          if (saveTimer) {
            clearTimeout(saveTimer)
          }

          saveTimer = setTimeout(() => {
            saveToCache(currentRecordId.value, formData)
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

// 导出缓存统计信息（用于调试）
export const getGlobalCacheStats = () => {
  return {
    totalCaches: formCacheStore.size,
    currentRecord: currentRecordId.value,
    cacheEnabled: cacheEnabled.value,
    cacheKeys: Array.from(formCacheStore.keys()),
  }
}

// 开发环境下暴露到全局（用于调试）
if (import.meta.env.DEV) {
  window.__repairFormCache = {
    store: formCacheStore,
    currentRecordId,
    getStats: getGlobalCacheStats,
    clearAll: () => formCacheStore.clear(),
  }
}
