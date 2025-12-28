/**
 * 资产类别状态管理
 * 用于动态菜单生成和资产类别数据缓存
 */
import { defineStore } from 'pinia'
import { assetCategoryApi } from '@/api/v3/platform'

export const useAssetCategoryStore = defineStore('assetCategory', {
  state: () => ({
    // 资产类别列表
    categories: [],
    // 当前选中的类别
    currentCategory: null,
    // 加载状态
    loading: false,
    // 错误信息
    error: null,
    // 最后更新时间
    lastUpdated: null
  }),

  getters: {
    // 激活的类别
    activeCategories: (state) => {
      return state.categories.filter(c => c.is_active)
    },

    // 按行业分组
    categoriesByIndustry: (state) => {
      const groups = {}
      state.categories.forEach(category => {
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
    },

    // 类别选项（用于下拉选择）
    categoryOptions: (state) => {
      return state.categories
        .filter(c => c.is_active)
        .map(c => ({
          label: c.name,
          value: c.id,
          code: c.code,
          icon: c.icon,
          industry: c.industry
        }))
    },

    // 根据编码获取类别
    getCategoryByCode: (state) => (code) => {
      return state.categories.find(c => c.code === code)
    },

    // 根据ID获取类别
    getCategoryById: (state) => (id) => {
      return state.categories.find(c => c.id === id)
    },

    // 生成动态路由配置
    dynamicRoutes: (state) => {
      return state.categories
        .filter(c => c.is_active)
        .map(category => ({
          name: `Asset_${category.code}`,
          path: `/assets/${category.code}`,
          component: () => import('@/views/assets/AssetList.vue'),
          meta: {
            title: category.name,
            icon: category.icon || 'mdi:cube-outline',
            categoryId: category.id,
            categoryCode: category.code,
            industry: category.industry
          },
          children: [
            {
              name: `Asset_${category.code}_List`,
              path: '',
              component: () => import('@/views/assets/AssetList.vue'),
              meta: {
                title: `${category.name}列表`,
                categoryId: category.id,
                categoryCode: category.code
              }
            },
            {
              name: `Asset_${category.code}_Detail`,
              path: ':id',
              component: () => import('@/views/assets/AssetDetail.vue'),
              meta: {
                title: '资产详情',
                categoryId: category.id,
                categoryCode: category.code
              }
            },
            {
              name: `Asset_${category.code}_Monitor`,
              path: 'monitor',
              component: () => import('@/views/assets/AssetMonitor.vue'),
              meta: {
                title: `${category.name}监控`,
                categoryId: category.id,
                categoryCode: category.code
              }
            }
          ]
        }))
    },

    // 生成菜单配置
    menuConfig: (state) => {
      return state.categories
        .filter(c => c.is_active)
        .map(category => ({
          label: category.name,
          key: category.code,
          icon: category.icon,
          path: `/assets/${category.code}`,
          meta: {
            categoryId: category.id,
            categoryCode: category.code,
            industry: category.industry,
            assetCount: category.asset_count
          }
        }))
    }
  },

  actions: {
    // 加载资产类别列表
    async loadCategories(forceRefresh = false) {
      // 检查缓存（5分钟内不重复加载）
      const now = Date.now()
      if (!forceRefresh && this.lastUpdated && (now - this.lastUpdated) < 5 * 60 * 1000) {
        return this.categories
      }

      this.loading = true
      this.error = null

      try {
        const response = await assetCategoryApi.getList({ is_active: true })
        const data = response.data || response
        
        this.categories = Array.isArray(data) ? data : (data.items || data.categories || [])
        this.lastUpdated = now
        
        return this.categories
      } catch (err) {
        this.error = err.message || '加载资产类别失败'
        console.error('加载资产类别失败:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    // 设置当前类别
    setCurrentCategory(category) {
      this.currentCategory = category
    },

    // 根据编码设置当前类别
    async setCurrentCategoryByCode(code) {
      let category = this.getCategoryByCode(code)
      
      if (!category) {
        await this.loadCategories()
        category = this.getCategoryByCode(code)
      }

      this.currentCategory = category
      return category
    },

    // 刷新类别列表
    async refresh() {
      this.lastUpdated = null
      return await this.loadCategories(true)
    },

    // 清除缓存
    clearCache() {
      this.categories = []
      this.currentCategory = null
      this.lastUpdated = null
    },

    // 更新类别资产数量
    updateAssetCount(categoryId, count) {
      const category = this.categories.find(c => c.id === categoryId)
      if (category) {
        category.asset_count = count
      }
    }
  }
})

export default useAssetCategoryStore
