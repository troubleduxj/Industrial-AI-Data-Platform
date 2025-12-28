/**
 * 资产类别动态路由生成器
 * 基于资产类别配置自动生成路由
 */
import { useAssetCategoryStore } from '@/store/modules/assetCategory'

// 资产管理布局组件
const AssetLayout = () => import('@/views/assets/AssetLayout.vue')

// 资产相关页面组件
const AssetList = () => import('@/views/assets/AssetList.vue')
const AssetDetail = () => import('@/views/assets/AssetDetail.vue')
const AssetMonitor = () => import('@/views/assets/AssetMonitor.vue')
const AssetCreate = () => import('@/views/assets/AssetCreate.vue')
const AssetEdit = () => import('@/views/assets/AssetEdit.vue')

/**
 * 生成资产类别路由
 * @param {Object} category - 资产类别对象
 * @returns {Object} 路由配置
 */
export function generateCategoryRoute(category) {
  return {
    name: `Asset_${category.code}`,
    path: `/assets/${category.code}`,
    component: AssetLayout,
    redirect: `/assets/${category.code}/list`,
    meta: {
      title: category.name,
      icon: category.icon || 'mdi:cube-outline',
      categoryId: category.id,
      categoryCode: category.code,
      industry: category.industry,
      order: category.sort_order || 0
    },
    children: [
      {
        name: `Asset_${category.code}_List`,
        path: 'list',
        component: AssetList,
        meta: {
          title: `${category.name}列表`,
          icon: 'mdi:format-list-bulleted',
          categoryId: category.id,
          categoryCode: category.code,
          keepAlive: true
        }
      },
      {
        name: `Asset_${category.code}_Monitor`,
        path: 'monitor',
        component: AssetMonitor,
        meta: {
          title: `${category.name}监控`,
          icon: 'mdi:monitor-dashboard',
          categoryId: category.id,
          categoryCode: category.code
        }
      },
      {
        name: `Asset_${category.code}_Create`,
        path: 'create',
        component: AssetCreate,
        meta: {
          title: `新建${category.name}`,
          icon: 'mdi:plus',
          categoryId: category.id,
          categoryCode: category.code,
          isHidden: true
        }
      },
      {
        name: `Asset_${category.code}_Detail`,
        path: ':id',
        component: AssetDetail,
        meta: {
          title: '资产详情',
          icon: 'mdi:information-outline',
          categoryId: category.id,
          categoryCode: category.code,
          isHidden: true
        }
      },
      {
        name: `Asset_${category.code}_Edit`,
        path: ':id/edit',
        component: AssetEdit,
        meta: {
          title: '编辑资产',
          icon: 'mdi:pencil',
          categoryId: category.id,
          categoryCode: category.code,
          isHidden: true
        }
      }
    ]
  }
}

/**
 * 生成所有资产类别路由
 * @returns {Promise<Array>} 路由配置数组
 */
export async function generateAssetRoutes() {
  const assetCategoryStore = useAssetCategoryStore()
  
  // 确保类别数据已加载
  if (assetCategoryStore.categories.length === 0) {
    await assetCategoryStore.loadCategories()
  }

  // 生成路由
  const routes = assetCategoryStore.activeCategories.map(category => 
    generateCategoryRoute(category)
  )

  return routes
}

/**
 * 动态添加资产路由到路由器
 * @param {Object} router - Vue Router实例
 */
export async function addAssetRoutesToRouter(router) {
  try {
    const routes = await generateAssetRoutes()
    
    routes.forEach(route => {
      // 检查路由是否已存在
      if (!router.hasRoute(route.name)) {
        router.addRoute(route)
        console.log(`添加资产路由: ${route.name}`)
      }
    })

    return routes
  } catch (error) {
    console.error('添加资产路由失败:', error)
    throw error
  }
}

/**
 * 移除资产路由
 * @param {Object} router - Vue Router实例
 */
export function removeAssetRoutes(router) {
  const assetCategoryStore = useAssetCategoryStore()
  
  assetCategoryStore.categories.forEach(category => {
    const routeName = `Asset_${category.code}`
    if (router.hasRoute(routeName)) {
      router.removeRoute(routeName)
      console.log(`移除资产路由: ${routeName}`)
    }
  })
}

/**
 * 刷新资产路由
 * @param {Object} router - Vue Router实例
 */
export async function refreshAssetRoutes(router) {
  // 先移除现有路由
  removeAssetRoutes(router)
  
  // 刷新类别数据
  const assetCategoryStore = useAssetCategoryStore()
  await assetCategoryStore.refresh()
  
  // 重新添加路由
  return await addAssetRoutesToRouter(router)
}

/**
 * 生成资产菜单配置
 * @returns {Array} 菜单配置数组
 */
export function generateAssetMenus() {
  const assetCategoryStore = useAssetCategoryStore()
  
  return assetCategoryStore.activeCategories.map(category => ({
    name: `Asset_${category.code}`,
    path: `/assets/${category.code}`,
    meta: {
      title: category.name,
      icon: category.icon || 'mdi:cube-outline',
      order: category.sort_order || 0
    },
    children: [
      {
        name: `Asset_${category.code}_List`,
        path: `/assets/${category.code}/list`,
        meta: {
          title: `${category.name}列表`,
          icon: 'mdi:format-list-bulleted'
        }
      },
      {
        name: `Asset_${category.code}_Monitor`,
        path: `/assets/${category.code}/monitor`,
        meta: {
          title: `${category.name}监控`,
          icon: 'mdi:monitor-dashboard'
        }
      }
    ]
  }))
}

export default {
  generateCategoryRoute,
  generateAssetRoutes,
  addAssetRoutesToRouter,
  removeAssetRoutes,
  refreshAssetRoutes,
  generateAssetMenus
}
