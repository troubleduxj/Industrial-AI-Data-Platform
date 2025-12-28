/**
 * 资产类别组合式函数
 * 提供资产类别的获取、缓存和菜单生成功能
 */
import { ref, computed, watch } from 'vue'
import { assetCategoryApi, dynamicMenuApi } from '@/api/v3/platform'

// 资产类别缓存
let categoriesCache = null
let cacheTimestamp = 0
const CACHE_TTL = 5 * 60 * 1000 // 5分钟缓存

/**
 * 资产类别组合式函数
 */
export function useAssetCategories() {
  const categories = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentCategory = ref(null)

  // 按行业分组的类别
  const categoriesByIndustry = computed(() => {
    const groups = {}
    
    categories.value.forEach(category => {
      const industry = category.industry || '通用'
      if (!groups[industry]) {
        groups[industry] = {
          name: industry,
          categories: []
        }
      }
      groups[industry].categories.push(category)
    })

    return Object.values(groups)
  })

  // 激活的类别
  const activeCategories = computed(() => {
    return categories.value.filter(c => c.is_active)
  })

  // 类别选项（用于下拉选择）
  const categoryOptions = computed(() => {
    return activeCategories.value.map(c => ({
      label: c.name,
      value: c.id,
      code: c.code,
      icon: c.icon,
      industry: c.industry
    }))
  })

  // 加载资产类别列表
  async function loadCategories(forceRefresh = false) {
    // 检查缓存
    const now = Date.now()
    if (!forceRefresh && categoriesCache && (now - cacheTimestamp) < CACHE_TTL) {
      categories.value = categoriesCache
      return
    }

    loading.value = true
    error.value = null

    try {
      const response = await assetCategoryApi.getList({ is_active: true })
      const data = response.data || response
      
      categories.value = Array.isArray(data) ? data : (data.items || data.categories || [])
      
      // 更新缓存
      categoriesCache = categories.value
      cacheTimestamp = now
    } catch (err) {
      error.value = err.message || '加载资产类别失败'
      console.error('加载资产类别失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 根据ID获取类别
  async function getCategoryById(id) {
    // 先从缓存查找
    const cached = categories.value.find(c => c.id === id)
    if (cached) {
      currentCategory.value = cached
      return cached
    }

    try {
      const response = await assetCategoryApi.getById(id)
      currentCategory.value = response.data || response
      return currentCategory.value
    } catch (err) {
      console.error('获取资产类别失败:', err)
      throw err
    }
  }

  // 根据编码获取类别
  async function getCategoryByCode(code) {
    // 先从缓存查找
    const cached = categories.value.find(c => c.code === code)
    if (cached) {
      currentCategory.value = cached
      return cached
    }

    try {
      const response = await assetCategoryApi.getByCode(code)
      currentCategory.value = response.data || response
      return currentCategory.value
    } catch (err) {
      console.error('获取资产类别失败:', err)
      throw err
    }
  }

  // 生成动态菜单配置
  function generateMenuConfig(options = {}) {
    const {
      basePath = '/assets',
      parentName = 'AssetManagement',
      iconMap = {}
    } = options

    return activeCategories.value.map(category => ({
      name: `Asset_${category.code}`,
      path: `${basePath}/${category.code}`,
      meta: {
        title: category.name,
        icon: iconMap[category.code] || category.icon || 'mdi:cube-outline',
        order: category.sort_order || 0,
        categoryId: category.id,
        categoryCode: category.code,
        industry: category.industry
      },
      children: [
        {
          name: `Asset_${category.code}_List`,
          path: 'list',
          meta: {
            title: `${category.name}列表`,
            icon: 'mdi:format-list-bulleted'
          }
        },
        {
          name: `Asset_${category.code}_Monitor`,
          path: 'monitor',
          meta: {
            title: `${category.name}监控`,
            icon: 'mdi:monitor-dashboard'
          }
        }
      ]
    }))
  }

  // 生成导航菜单选项
  function generateNavMenuOptions(options = {}) {
    const {
      basePath = '/assets',
      showCount = true,
      groupByIndustry = false
    } = options

    if (groupByIndustry) {
      return categoriesByIndustry.value.map(group => ({
        label: group.name,
        key: `industry_${group.name}`,
        type: 'group',
        children: group.categories.map(category => createMenuOption(category, basePath, showCount))
      }))
    }

    return activeCategories.value.map(category => 
      createMenuOption(category, basePath, showCount)
    )
  }

  // 创建菜单选项
  function createMenuOption(category, basePath, showCount) {
    return {
      label: showCount && category.asset_count 
        ? `${category.name} (${category.asset_count})`
        : category.name,
      key: category.code,
      path: `${basePath}/${category.code}`,
      icon: category.icon,
      meta: {
        categoryId: category.id,
        categoryCode: category.code,
        industry: category.industry,
        assetCount: category.asset_count
      }
    }
  }

  // 生成面包屑配置
  function generateBreadcrumb(categoryCode, assetName = null) {
    const category = categories.value.find(c => c.code === categoryCode)
    
    const breadcrumbs = [
      { title: '资产管理', path: '/assets' }
    ]

    if (category) {
      breadcrumbs.push({
        title: category.name,
        path: `/assets/${category.code}`
      })
    }

    if (assetName) {
      breadcrumbs.push({
        title: assetName,
        path: null
      })
    }

    return breadcrumbs
  }

  // 清除缓存
  function clearCache() {
    categoriesCache = null
    cacheTimestamp = 0
  }

  // 刷新类别列表
  async function refresh() {
    clearCache()
    await loadCategories(true)
  }

  return {
    // 状态
    categories,
    loading,
    error,
    currentCategory,
    // 计算属性
    categoriesByIndustry,
    activeCategories,
    categoryOptions,
    // 方法
    loadCategories,
    getCategoryById,
    getCategoryByCode,
    generateMenuConfig,
    generateNavMenuOptions,
    generateBreadcrumb,
    clearCache,
    refresh
  }
}

export default useAssetCategories
