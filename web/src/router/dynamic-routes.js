/**
 * 动态路由管理器
 * 负责根据用户权限动态生成和管理路由
 */

import { useUserStore } from '@/store/modules/user'
import { useEnhancedPermissionStore } from '@/store/modules/permission'
import { basicRoutes, asyncRoutes, vueModules, NOT_FOUND_ROUTE, EMPTY_ROUTE } from './routes'

/**
 * 动态路由管理器类
 */
class DynamicRouteManager {
  constructor() {
    this.isInitialized = false
    this.loadedRoutes = new Set()
    this.routeUpdateCallbacks = []
    this.router = null
  }

  /**
   * 设置路由器实例
   */
  setRouter(router) {
    this.router = router
  }

  /**
   * 初始化动态路由系统
   */
  async initialize() {
    if (this.isInitialized) {
      console.log('动态路由系统已初始化')
      return
    }

    console.log('初始化动态路由系统...')

    try {
      await this.loadDynamicRoutes()
      this.isInitialized = true
      console.log('动态路由系统初始化完成')
    } catch (error) {
      console.error('动态路由系统初始化失败:', error)
      throw error
    }
  }

  /**
   * 加载动态路由
   */
  async loadDynamicRoutes() {
    const userStore = useUserStore()
    const permissionStore = useEnhancedPermissionStore()

    // 检查是否正在登出
    if (userStore.isLoggingOut) {
      console.log('正在登出，跳过动态路由加载')
      return
    }

    // 检查token
    if (!userStore.token) {
      console.log('无token，跳过动态路由加载')
      this.addEmptyRoute()
      return
    }

    console.log('开始加载动态路由...')

    try {
      // 确保用户信息已加载
      if (!userStore.userId) {
        await userStore.getUserInfo()
      }

      // 生成基于权限的路由
      const accessRoutes = await permissionStore.generateRoutes()
      console.log('生成的权限路由数量:', accessRoutes.length)

      // 获取API权限
      await permissionStore.getAccessApis()

      // 添加权限路由到路由器
      this.addAccessRoutes(accessRoutes)

      // 添加静态异步路由
      this.addAsyncRoutes()

      // 添加404路由
      this.addNotFoundRoute()

      // 移除空路由
      this.removeEmptyRoute()

      // 触发路由更新回调
      this.triggerRouteUpdateCallbacks()

      console.log('动态路由加载完成')
    } catch (error) {
      console.error('加载动态路由失败:', error)
      throw error
    }
  }

  /**
   * 添加权限路由
   */
  addAccessRoutes(routes) {
    console.log('📋 开始添加权限路由，共', routes.length, '个')
    routes.forEach((route, index) => {
      try {
        console.log(`📋 [${index + 1}/${routes.length}] 处理路由:`, route.name, route.path)
        this.validateAndFixRoute(route)

        if (!this.router.hasRoute(route.name)) {
          this.router.addRoute(route)
          this.loadedRoutes.add(route.name)
          console.log('✅ 添加权限路由:', route.name, route.path)
        } else {
          console.log('⚠️ 路由已存在，跳过:', route.name, route.path)
        }
      } catch (error) {
        console.error(`❌ 添加权限路由失败 ${route.name}:`, error)
      }
    })
    console.log('📋 权限路由添加完成')
  }

  /**
   * 添加静态异步路由
   */
  addAsyncRoutes() {
    asyncRoutes.forEach((route) => {
      try {
        this.validateAndFixRoute(route)

        if (!this.router.hasRoute(route.name)) {
          this.router.addRoute(route)
          this.loadedRoutes.add(route.name)
          console.log('添加异步路由:', route.name, route.path)
        }
      } catch (error) {
        console.error(`添加异步路由失败 ${route.name}:`, error)
      }
    })
  }

  /**
   * 验证和修复路由配置
   */
  validateAndFixRoute(route) {
    // 验证父路由路径格式
    if (route.path && !route.path.startsWith('/')) {
      console.warn(`父路由路径应以'/'开头: "${route.path}" -> "/${route.path}"`)
      route.path = `/${route.path}`
    }

    // 验证子路由路径格式
    if (route.children && route.children.length > 0) {
      route.children.forEach((child) => {
        if (child.path && child.path.startsWith('/') && child.path !== '/') {
          console.warn(`子路由路径应为相对路径: "${child.path}" -> "${child.path.substring(1)}"`)
          child.path = child.path.substring(1)
        }
      })
    }

    // 确保路由有名称
    if (!route.name) {
      console.warn('路由缺少名称:', route.path)
      route.name = route.path.replace(/\//g, '_').replace(/^_/, '') || 'UnnamedRoute'
    }
  }

  /**
   * 添加404路由
   */
  addNotFoundRoute() {
    if (!this.router.hasRoute(NOT_FOUND_ROUTE.name)) {
      this.router.addRoute(NOT_FOUND_ROUTE)
      console.log('添加404路由')
    }
  }

  /**
   * 添加空路由
   */
  addEmptyRoute() {
    if (!this.router.hasRoute(EMPTY_ROUTE.name)) {
      this.router.addRoute(EMPTY_ROUTE)
      console.log('添加空路由')
    }
  }

  /**
   * 移除空路由
   */
  removeEmptyRoute() {
    if (this.router.hasRoute(EMPTY_ROUTE.name)) {
      this.router.removeRoute(EMPTY_ROUTE.name)
      console.log('移除空路由')
    }
  }

  /**
   * 重置动态路由
   */
  resetDynamicRoutes() {
    console.log('重置动态路由...')

    // 获取基础路由名称
    const basicRouteNames = this.getRouteNames(basicRoutes)

    // 移除所有动态添加的路由
    this.router.getRoutes().forEach((route) => {
      if (route.name && !basicRouteNames.includes(route.name)) {
        this.router.removeRoute(route.name)
        console.log('移除动态路由:', route.name)
      }
    })

    // 清空已加载路由记录
    this.loadedRoutes.clear()
    this.isInitialized = false

    console.log('动态路由重置完成')
  }

  /**
   * 刷新动态路由
   */
  async refreshDynamicRoutes() {
    console.log('刷新动态路由...')

    try {
      // 重置路由
      this.resetDynamicRoutes()

      // 重新加载路由
      await this.loadDynamicRoutes()

      console.log('动态路由刷新完成')
    } catch (error) {
      console.error('刷新动态路由失败:', error)
      throw error
    }
  }

  /**
   * 获取路由名称列表
   */
  getRouteNames(routes) {
    const names = []

    const extractNames = (routeList) => {
      routeList.forEach((route) => {
        if (route.name) {
          names.push(route.name)
        }
        if (route.children && route.children.length > 0) {
          extractNames(route.children)
        }
      })
    }

    extractNames(routes)
    return names
  }

  /**
   * 检查路由是否已加载
   */
  isRouteLoaded(routeName) {
    return this.loadedRoutes.has(routeName)
  }

  /**
   * 获取所有已加载的路由
   */
  getLoadedRoutes() {
    return Array.from(this.loadedRoutes)
  }

  /**
   * 添加路由更新回调
   */
  onRouteUpdate(callback) {
    if (typeof callback === 'function') {
      this.routeUpdateCallbacks.push(callback)
    }
  }

  /**
   * 移除路由更新回调
   */
  offRouteUpdate(callback) {
    const index = this.routeUpdateCallbacks.indexOf(callback)
    if (index > -1) {
      this.routeUpdateCallbacks.splice(index, 1)
    }
  }

  /**
   * 触发路由更新回调
   */
  triggerRouteUpdateCallbacks() {
    this.routeUpdateCallbacks.forEach((callback) => {
      try {
        callback(this.getLoadedRoutes())
      } catch (error) {
        console.error('路由更新回调执行失败:', error)
      }
    })
  }

  /**
   * 获取当前路由统计信息
   */
  getRouteStats() {
    const allRoutes = this.router.getRoutes()
    const basicRouteNames = this.getRouteNames(basicRoutes)

    return {
      total: allRoutes.length,
      basic: basicRouteNames.length,
      dynamic: this.loadedRoutes.size,
      isInitialized: this.isInitialized,
      loadedRoutes: this.getLoadedRoutes(),
    }
  }
}

// 创建单例实例
export const dynamicRouteManager = new DynamicRouteManager()

/**
 * 初始化动态路由系统
 */
export async function initializeDynamicRoutes() {
  return await dynamicRouteManager.initialize()
}

/**
 * 重置动态路由
 */
export function resetDynamicRoutes() {
  return dynamicRouteManager.resetDynamicRoutes()
}

/**
 * 刷新动态路由
 */
export async function refreshDynamicRoutes() {
  return await dynamicRouteManager.refreshDynamicRoutes()
}

/**
 * 获取路由统计信息
 */
export function getRouteStats() {
  return dynamicRouteManager.getRouteStats()
}

export default dynamicRouteManager
