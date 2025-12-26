/**
 * 维修记录字典数据 API
 * 提供维修记录相关的字典数据获取接口
 */

import { systemV2Api } from './system-v2'

// 字典类型代码常量
export const REPAIR_DICT_TYPES = {
  DEVICE_CATEGORY: 'repair_device_category',  // 设备类别
  DEVICE_BRAND: 'device_brand',               // 设备品牌
  FAULT_REASON: 'repair_fault_reason',        // 故障原因
  DAMAGE_CATEGORY: 'repair_damage_category',  // 损坏类别
}

// 缓存字典数据
const dictCache = new Map()
const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

/**
 * 获取字典数据（带缓存）
 * @param {string} typeCode 字典类型代码
 * @param {boolean} forceRefresh 是否强制刷新
 * @returns {Promise<Array>} 字典数据列表
 */
async function getDictData(typeCode, forceRefresh = false) {
  const cacheKey = typeCode
  const cached = dictCache.get(cacheKey)
  
  // 检查缓存是否有效
  if (!forceRefresh && cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data
  }
  
  try {
    const response = await systemV2Api.getDictDataByType(typeCode)
    
    if (response && response.success && response.data) {
      const data = Array.isArray(response.data) ? response.data : (response.data.items || [])
      
      // 转换为选项格式
      const options = data
        .filter(item => item.is_enabled !== false)
        .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
        .map(item => ({
          label: item.data_label,
          value: item.data_value,
          description: item.description,
          sortOrder: item.sort_order,
        }))
      
      // 更新缓存
      dictCache.set(cacheKey, {
        data: options,
        timestamp: Date.now(),
      })
      
      return options
    }
    
    return []
  } catch (error) {
    console.error(`获取字典数据失败 [${typeCode}]:`, error)
    
    // 如果有缓存，返回过期的缓存数据
    if (cached) {
      console.warn(`使用过期缓存数据 [${typeCode}]`)
      return cached.data
    }
    
    return []
  }
}

/**
 * 维修记录字典API
 */
export const repairDictApi = {
  /**
   * 获取设备类别选项
   * @param {boolean} forceRefresh 是否强制刷新
   * @returns {Promise<Array>} 设备类别选项列表
   */
  getDeviceCategories: (forceRefresh = false) => 
    getDictData(REPAIR_DICT_TYPES.DEVICE_CATEGORY, forceRefresh),
  
  /**
   * 获取设备品牌选项
   * @param {boolean} forceRefresh 是否强制刷新
   * @returns {Promise<Array>} 设备品牌选项列表
   */
  getDeviceBrands: (forceRefresh = false) => 
    getDictData(REPAIR_DICT_TYPES.DEVICE_BRAND, forceRefresh),
  
  /**
   * 获取故障原因选项
   * @param {boolean} forceRefresh 是否强制刷新
   * @returns {Promise<Array>} 故障原因选项列表
   */
  getFaultReasons: (forceRefresh = false) => 
    getDictData(REPAIR_DICT_TYPES.FAULT_REASON, forceRefresh),
  
  /**
   * 获取损坏类别选项
   * @param {boolean} forceRefresh 是否强制刷新
   * @returns {Promise<Array>} 损坏类别选项列表
   */
  getDamageCategories: (forceRefresh = false) => 
    getDictData(REPAIR_DICT_TYPES.DAMAGE_CATEGORY, forceRefresh),
  
  /**
   * 批量获取所有维修记录相关字典数据
   * @param {boolean} forceRefresh 是否强制刷新
   * @returns {Promise<Object>} 所有字典数据
   */
  getAllDictData: async (forceRefresh = false) => {
    const [categories, brands, faultReasons, damageCategories] = await Promise.all([
      getDictData(REPAIR_DICT_TYPES.DEVICE_CATEGORY, forceRefresh),
      getDictData(REPAIR_DICT_TYPES.DEVICE_BRAND, forceRefresh),
      getDictData(REPAIR_DICT_TYPES.FAULT_REASON, forceRefresh),
      getDictData(REPAIR_DICT_TYPES.DAMAGE_CATEGORY, forceRefresh),
    ])
    
    return {
      categories,
      brands,
      faultReasons,
      damageCategories,
    }
  },
  
  /**
   * 清除字典缓存
   * @param {string} typeCode 字典类型代码，不传则清除所有
   */
  clearCache: (typeCode = null) => {
    if (typeCode) {
      dictCache.delete(typeCode)
    } else {
      dictCache.clear()
    }
  },
  
  /**
   * 获取带"全部"选项的字典数据
   * @param {string} typeCode 字典类型代码
   * @param {string} allLabel "全部"选项的标签
   * @returns {Promise<Array>} 带"全部"选项的字典数据
   */
  getOptionsWithAll: async (typeCode, allLabel = '全部') => {
    const options = await getDictData(typeCode)
    return [{ label: allLabel, value: '' }, ...options]
  },
}

// 默认导出
export default repairDictApi
