/**
 * 维修记录字典选项 Composable
 * 提供维修记录表单中使用的字典数据选项
 */

import { ref, onMounted } from 'vue'
import { repairDictApi, REPAIR_DICT_TYPES } from '@/api/repair-dict'

/**
 * 使用维修记录字典选项
 * @param {Object} options 配置选项
 * @param {boolean} options.autoLoad 是否自动加载，默认true
 * @param {boolean} options.withAllOption 是否包含"全部"选项，默认false
 * @returns {Object} 字典选项和加载方法
 */
export function useRepairDictOptions(options = {}) {
  const { autoLoad = true, withAllOption = false } = options
  
  // 选项数据
  const categoryOptions = ref([])
  const brandOptions = ref([])
  const faultReasonOptions = ref([])
  const damageCategoryOptions = ref([])
  
  // 加载状态
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref(null)
  
  // 默认选项（当字典数据加载失败时使用）
  const defaultOptions = {
    categories: [
      { label: '二氧化碳保护焊机', value: '二氧化碳保护焊机' },
      { label: '氩弧焊机', value: '氩弧焊机' },
      { label: '电焊机', value: '电焊机' },
      { label: '等离子切割机', value: '等离子切割机' },
    ],
    brands: [
      { label: '松下', value: '松下' },
      { label: '林肯', value: '林肯' },
      { label: '米勒', value: '米勒' },
      { label: '奥太', value: '奥太' },
      { label: '瑞凌', value: '瑞凌' },
    ],
    faultReasons: [
      { label: '操作不当', value: '操作不当' },
      { label: '老化磨损', value: '老化磨损' },
      { label: '环境因素', value: '环境因素' },
      { label: '设备缺陷', value: '设备缺陷' },
      { label: '维护不当', value: '维护不当' },
    ],
    damageCategories: [
      { label: '正常损坏', value: '正常损坏' },
      { label: '非正常损坏', value: '非正常损坏' },
      { label: '人为损坏', value: '人为损坏' },
    ],
  }
  
  /**
   * 添加"全部"选项
   */
  const addAllOption = (options, label = '全部') => {
    return [{ label, value: '' }, ...options]
  }
  
  /**
   * 加载所有字典数据
   */
  const loadAllOptions = async (forceRefresh = false) => {
    if (loading.value) return
    
    loading.value = true
    error.value = null
    
    try {
      const dictData = await repairDictApi.getAllDictData(forceRefresh)
      
      // 设置选项数据
      categoryOptions.value = withAllOption 
        ? addAllOption(dictData.categories.length > 0 ? dictData.categories : defaultOptions.categories, '全部类别')
        : (dictData.categories.length > 0 ? dictData.categories : defaultOptions.categories)
      
      brandOptions.value = withAllOption
        ? addAllOption(dictData.brands.length > 0 ? dictData.brands : defaultOptions.brands, '全部品牌')
        : (dictData.brands.length > 0 ? dictData.brands : defaultOptions.brands)
      
      faultReasonOptions.value = withAllOption
        ? addAllOption(dictData.faultReasons.length > 0 ? dictData.faultReasons : defaultOptions.faultReasons, '全部原因')
        : (dictData.faultReasons.length > 0 ? dictData.faultReasons : defaultOptions.faultReasons)
      
      damageCategoryOptions.value = withAllOption
        ? addAllOption(dictData.damageCategories.length > 0 ? dictData.damageCategories : defaultOptions.damageCategories, '全部类别')
        : (dictData.damageCategories.length > 0 ? dictData.damageCategories : defaultOptions.damageCategories)
      
      loaded.value = true
      
      console.log('[useRepairDictOptions] 字典数据加载完成:', {
        categories: categoryOptions.value.length,
        brands: brandOptions.value.length,
        faultReasons: faultReasonOptions.value.length,
        damageCategories: damageCategoryOptions.value.length,
      })
      
    } catch (err) {
      console.error('[useRepairDictOptions] 加载字典数据失败:', err)
      error.value = err
      
      // 使用默认选项
      categoryOptions.value = withAllOption 
        ? addAllOption(defaultOptions.categories, '全部类别')
        : defaultOptions.categories
      brandOptions.value = withAllOption
        ? addAllOption(defaultOptions.brands, '全部品牌')
        : defaultOptions.brands
      faultReasonOptions.value = withAllOption
        ? addAllOption(defaultOptions.faultReasons, '全部原因')
        : defaultOptions.faultReasons
      damageCategoryOptions.value = withAllOption
        ? addAllOption(defaultOptions.damageCategories, '全部类别')
        : defaultOptions.damageCategories
      
      loaded.value = true
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 刷新字典数据
   */
  const refresh = () => loadAllOptions(true)
  
  /**
   * 清除缓存并重新加载
   */
  const clearCacheAndReload = async () => {
    repairDictApi.clearCache()
    await loadAllOptions(true)
  }
  
  // 自动加载
  if (autoLoad) {
    onMounted(() => {
      loadAllOptions()
    })
  }
  
  return {
    // 选项数据
    categoryOptions,
    brandOptions,
    faultReasonOptions,
    damageCategoryOptions,
    
    // 状态
    loading,
    loaded,
    error,
    
    // 方法
    loadAllOptions,
    refresh,
    clearCacheAndReload,
    
    // 常量
    REPAIR_DICT_TYPES,
  }
}

export default useRepairDictOptions
