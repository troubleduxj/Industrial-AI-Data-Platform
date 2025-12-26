/**
 * 设备字段 Store
 * 管理设备类型的字段配置缓存
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { deviceFieldApi } from '@/api/device-field'
import type { DeviceField } from '@/api/device-field'
import { dataModelApi } from '@/api/v2/data-model'

/**
 * 设备字段 Store
 */
export const useDeviceFieldStore = defineStore('deviceField', () => {
  // ==================== State ====================

  /**
   * 字段配置缓存
   * key: 设备类型代码
   * value: 监测字段配置列表
   */
  const monitoringFieldsCache = ref<Map<string, DeviceField[]>>(new Map())

  /**
   * 缓存时间戳
   * key: 设备类型代码
   * value: 缓存时间戳
   */
  const cacheTimestamp = ref<Map<string, number>>(new Map())

  /**
   * 缓存有效期（毫秒）
   * 默认：会话期间有效（不设置过期时间）
   * 如果需要设置过期时间，可以设置为具体的毫秒数，如：3600000 (1小时)
   */
  const cacheTTL = ref<number>(Infinity)

  /**
   * 加载状态
   * key: 设备类型代码
   * value: 是否正在加载
   */
  const loadingState = ref<Map<string, boolean>>(new Map())

  // ==================== Getters ====================

  /**
   * 检查缓存是否有效
   * @param deviceTypeCode 设备类型代码
   * @returns 是否有效
   */
  function isCacheValid(deviceTypeCode: string): boolean {
    const timestamp = cacheTimestamp.value.get(deviceTypeCode)
    if (!timestamp) {
      return false
    }

    // 如果 cacheTTL 是 Infinity，则缓存永久有效
    if (cacheTTL.value === Infinity) {
      return true
    }

    // 检查是否过期
    const now = Date.now()
    return now - timestamp < cacheTTL.value
  }

  /**
   * 获取缓存的字段配置
   * @param deviceTypeCode 设备类型代码
   * @returns 字段配置列表或 null
   */
  function getCachedFields(deviceTypeCode: string): DeviceField[] | null {
    if (isCacheValid(deviceTypeCode)) {
      return monitoringFieldsCache.value.get(deviceTypeCode) || null
    }
    return null
  }

  /**
   * 检查是否正在加载
   * @param deviceTypeCode 设备类型代码
   * @returns 是否正在加载
   */
  function isLoading(deviceTypeCode: string): boolean {
    return loadingState.value.get(deviceTypeCode) || false
  }

  // ==================== Actions ====================

  /**
   * 获取监测字段配置（带缓存）
   * @param deviceTypeCode 设备类型代码
   * @param forceRefresh 是否强制刷新缓存
   * @returns 字段配置列表
   */
  async function getMonitoringFields(
    deviceTypeCode: string,
    forceRefresh = false
  ): Promise<DeviceField[]> {
    // 检查缓存
    if (!forceRefresh) {
      const cached = getCachedFields(deviceTypeCode)
      if (cached) {
        console.log(`[DeviceFieldStore] 使用缓存的字段配置: ${deviceTypeCode}`)
        return cached
      }
    }

    // 检查是否正在加载
    if (isLoading(deviceTypeCode)) {
      console.log(`[DeviceFieldStore] 正在加载字段配置，等待完成: ${deviceTypeCode}`)
      // 等待加载完成
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!isLoading(deviceTypeCode)) {
            clearInterval(checkInterval)
            const cached = getCachedFields(deviceTypeCode)
            resolve(cached || [])
          }
        }, 100)
      })
    }

    // 从 API 获取
    try {
      loadingState.value.set(deviceTypeCode, true)
      console.log(`[DeviceFieldStore] 从 API 获取字段配置: ${deviceTypeCode}`)

      // 使用 dataModelApi 获取所有字段配置，支持分组和排序
      // 替换原来的 deviceFieldApi.getMonitoringKeys，因为后者可能只返回部分字段且不支持新属性
      const response = await dataModelApi.getFields({ 
        device_type_code: deviceTypeCode,
        is_active: true,
        page_size: 1000 // 获取所有字段
      })
      
      let fields: DeviceField[] = []
      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : (response.data.items || response.data || [])
        // 按 sort_order 排序
        items.sort((a: any, b: any) => (a.sort_order || 0) - (b.sort_order || 0))
        fields = items as DeviceField[]
      }

      // 存入缓存
      setCache(deviceTypeCode, fields)

      console.log(
        `[DeviceFieldStore] 字段配置已缓存: ${deviceTypeCode}, 共 ${fields.length} 个字段`
      )

      return fields
    } catch (error) {
      console.error(`[DeviceFieldStore] 获取字段配置失败: ${deviceTypeCode}`, error)
      throw error
    } finally {
      loadingState.value.set(deviceTypeCode, false)
    }
  }

  /**
   * 批量获取监测字段配置
   * @param deviceTypeCodes 设备类型代码列表
   * @returns 字段配置 Map
   */
  async function batchGetMonitoringFields(
    deviceTypeCodes: string[]
  ): Promise<Map<string, DeviceField[]>> {
    const result = new Map<string, DeviceField[]>()

    // 并行获取所有字段配置
    await Promise.all(
      deviceTypeCodes.map(async (deviceTypeCode) => {
        try {
          const fields = await getMonitoringFields(deviceTypeCode)
          result.set(deviceTypeCode, fields)
        } catch (error) {
          console.error(`[DeviceFieldStore] 批量获取字段配置失败: ${deviceTypeCode}`, error)
          result.set(deviceTypeCode, [])
        }
      })
    )

    return result
  }

  /**
   * 设置缓存
   * @param deviceTypeCode 设备类型代码
   * @param fields 字段配置列表
   */
  function setCache(deviceTypeCode: string, fields: DeviceField[]): void {
    monitoringFieldsCache.value.set(deviceTypeCode, fields)
    cacheTimestamp.value.set(deviceTypeCode, Date.now())
  }

  /**
   * 清除指定设备类型的缓存
   * @param deviceTypeCode 设备类型代码
   */
  function clearCache(deviceTypeCode?: string): void {
    if (deviceTypeCode) {
      monitoringFieldsCache.value.delete(deviceTypeCode)
      cacheTimestamp.value.delete(deviceTypeCode)
      loadingState.value.delete(deviceTypeCode)
      console.log(`[DeviceFieldStore] 已清除缓存: ${deviceTypeCode}`)
    } else {
      monitoringFieldsCache.value.clear()
      cacheTimestamp.value.clear()
      loadingState.value.clear()
      console.log('[DeviceFieldStore] 已清除所有缓存')
    }
  }

  /**
   * 清除过期的缓存
   */
  function clearExpiredCache(): void {
    const now = Date.now()
    const expiredKeys: string[] = []

    cacheTimestamp.value.forEach((timestamp, key) => {
      if (cacheTTL.value !== Infinity && now - timestamp >= cacheTTL.value) {
        expiredKeys.push(key)
      }
    })

    expiredKeys.forEach((key) => {
      monitoringFieldsCache.value.delete(key)
      cacheTimestamp.value.delete(key)
      loadingState.value.delete(key)
    })

    if (expiredKeys.length > 0) {
      console.log(`[DeviceFieldStore] 已清除 ${expiredKeys.length} 个过期缓存`)
    }
  }

  /**
   * 设置缓存有效期
   * @param ttl 有效期（毫秒），Infinity 表示永久有效
   */
  function setCacheTTL(ttl: number): void {
    cacheTTL.value = ttl
    console.log(`[DeviceFieldStore] 缓存有效期已设置为: ${ttl}ms`)
  }

  /**
   * 获取缓存统计信息
   * @returns 缓存统计信息
   */
  function getCacheStats() {
    return {
      totalCached: monitoringFieldsCache.value.size,
      cachedTypes: Array.from(monitoringFieldsCache.value.keys()),
      cacheTTL: cacheTTL.value,
      loadingCount: Array.from(loadingState.value.values()).filter((v) => v).length
    }
  }

  // ==================== Return ====================

  return {
    // State
    monitoringFieldsCache,
    cacheTimestamp,
    cacheTTL,
    loadingState,

    // Getters
    isCacheValid,
    getCachedFields,
    isLoading,
    getCacheStats,

    // Actions
    getMonitoringFields,
    batchGetMonitoringFields,
    setCache,
    clearCache,
    clearExpiredCache,
    setCacheTTL
  }
})

export default useDeviceFieldStore
