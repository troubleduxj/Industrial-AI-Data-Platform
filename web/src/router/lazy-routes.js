/**
 * 懒加载路由配置
 * 实现路由和组件的懒加载，提高应用启动性能
 */

import { defineAsyncComponent } from 'vue'
import LoadingComponent from '@/components/common/LoadingComponent.vue'
import ErrorComponent from '@/components/common/ErrorComponent.vue'

/**
 * 创建懒加载组件
 * @param {Function} loader - 组件加载函数
 * @param {Object} options - 配置选项
 * @returns {Object} 异步组件
 */
export function createLazyComponent(loader, options = {}) {
  const defaultOptions = {
    // 加载组件时显示的组件
    loadingComponent: LoadingComponent,
    // 加载失败时显示的组件
    errorComponent: ErrorComponent,
    // 展示加载组件前的延迟时间，默认200ms
    delay: 200,
    // 如果提供了超时时间且组件加载超时，则显示错误组件，默认3秒
    timeout: 3000,
    // 是否在服务端渲染时挂起
    suspensible: false,
    // 错误重试次数
    retryTimes: 3,
    // 重试间隔
    retryDelay: 1000,
  }

  const finalOptions = { ...defaultOptions, ...options }

  // 包装loader以支持重试机制
  const wrappedLoader = async () => {
    let lastError = null

    for (let i = 0; i < finalOptions.retryTimes; i++) {
      try {
        const component = await loader()

        // 预加载相关资源
        if (component.default && typeof component.default.preload === 'function') {
          component.default.preload()
        }

        return component
      } catch (error) {
        lastError = error
        console.warn(`组件加载失败，第${i + 1}次重试:`, error)

        if (i < finalOptions.retryTimes - 1) {
          await new Promise((resolve) => setTimeout(resolve, finalOptions.retryDelay))
        }
      }
    }

    throw lastError
  }

  return defineAsyncComponent({
    loader: wrappedLoader,
    loadingComponent: finalOptions.loadingComponent,
    errorComponent: finalOptions.errorComponent,
    delay: finalOptions.delay,
    timeout: finalOptions.timeout,
    suspensible: finalOptions.suspensible,
    onError: (error, retry, fail, attempts) => {
      console.error(`异步组件加载失败 (尝试 ${attempts} 次):`, error)

      // 如果是网络错误，可以重试
      if (error.message.includes('Loading chunk') || error.message.includes('Loading CSS chunk')) {
        if (attempts < finalOptions.retryTimes) {
          console.log('检测到资源加载失败，正在重试...')
          setTimeout(retry, finalOptions.retryDelay)
        } else {
          fail()
        }
      } else {
        fail()
      }
    },
  })
}

/**
 * 创建路由懒加载函数
 * @param {string} path - 组件路径
 * @param {Object} options - 配置选项
 * @returns {Function} 路由组件加载函数
 */
export function createRouteComponent(path, options = {}) {
  return () =>
    createLazyComponent(() => {
      // 清理路径，移除空段和多余的斜杠
      const cleanPath = path
        .split('/')
        .filter((segment) => segment.trim() !== '')
        .join('/')

      if (!cleanPath) {
        throw new Error(`Invalid route path: ${path}`)
      }

      return import(/* webpackChunkName: "[request]" */ `../views/${cleanPath}.vue`)
    }, options)
}

/**
 * 批量创建路由组件
 * @param {Object} routes - 路由配置对象
 * @returns {Object} 懒加载路由组件对象
 */
export function createRouteComponents(routes) {
  const components = {}

  Object.entries(routes).forEach(([key, path]) => {
    components[key] = createRouteComponent(path)
  })

  return components
}

/**
 * 预加载路由组件
 * @param {Array} routePaths - 路由路径数组
 */
export async function preloadRouteComponents(routePaths) {
  const preloadPromises = routePaths.map(async (path) => {
    try {
      // 清理路径，移除空段和多余的斜杠
      const cleanPath = path
        .split('/')
        .filter((segment) => segment.trim() !== '')
        .join('/')

      if (!cleanPath) {
        console.warn(`预加载跳过空路径: ${path}`)
        return
      }

      await import(/* webpackChunkName: "preload-[request]" */ `../views/${cleanPath}.vue`)
      console.log(`预加载组件成功: ${cleanPath}`)
    } catch (error) {
      console.warn(`预加载组件失败: ${path}`, error)
    }
  })

  await Promise.allSettled(preloadPromises)
}

/**
 * 智能预加载策略
 * 根据用户权限和访问历史预加载可能访问的路由
 */
export class SmartPreloader {
  constructor() {
    this.preloadedRoutes = new Set()
    this.accessHistory = this.loadAccessHistory()
    this.preloadQueue = []
    this.isPreloading = false
  }

  /**
   * 加载访问历史
   */
  loadAccessHistory() {
    try {
      const history = localStorage.getItem('route_access_history')
      return history ? JSON.parse(history) : {}
    } catch {
      return {}
    }
  }

  /**
   * 保存访问历史
   */
  saveAccessHistory() {
    try {
      localStorage.setItem('route_access_history', JSON.stringify(this.accessHistory))
    } catch (error) {
      console.warn('保存访问历史失败:', error)
    }
  }

  /**
   * 记录路由访问
   * @param {string} routePath - 路由路径
   */
  recordAccess(routePath) {
    const now = Date.now()
    if (!this.accessHistory[routePath]) {
      this.accessHistory[routePath] = { count: 0, lastAccess: now }
    }

    this.accessHistory[routePath].count++
    this.accessHistory[routePath].lastAccess = now

    this.saveAccessHistory()
  }

  /**
   * 获取预加载优先级
   * @param {string} routePath - 路由路径
   * @returns {number} 优先级分数
   */
  getPreloadPriority(routePath) {
    const history = this.accessHistory[routePath]
    if (!history) return 0

    const { count, lastAccess } = history
    const daysSinceLastAccess = (Date.now() - lastAccess) / (1000 * 60 * 60 * 24)

    // 访问频率权重 + 时间衰减
    return count * Math.exp(-daysSinceLastAccess / 7)
  }

  /**
   * 添加到预加载队列
   * @param {string} routePath - 路由路径
   * @param {number} priority - 优先级
   */
  addToPreloadQueue(routePath, priority = 0) {
    if (this.preloadedRoutes.has(routePath)) {
      return
    }

    const calculatedPriority = priority || this.getPreloadPriority(routePath)

    this.preloadQueue.push({ routePath, priority: calculatedPriority })
    this.preloadQueue.sort((a, b) => b.priority - a.priority)

    this.processPreloadQueue()
  }

  /**
   * 处理预加载队列
   */
  async processPreloadQueue() {
    if (this.isPreloading || this.preloadQueue.length === 0) {
      return
    }

    this.isPreloading = true

    // 在空闲时间进行预加载
    const processNext = async () => {
      if (this.preloadQueue.length === 0) {
        this.isPreloading = false
        return
      }

      const { routePath } = this.preloadQueue.shift()

      // 清理路径，移除空段和多余的斜杠
      const cleanPath = routePath
        .split('/')
        .filter((segment) => segment.trim() !== '')
        .join('/')

      if (!cleanPath) {
        console.warn(`智能预加载跳过空路径: ${routePath}`)
        return
      }

      try {
        await import(/* webpackChunkName: "smart-preload-[request]" */ `../views/${cleanPath}.vue`)
        this.preloadedRoutes.add(routePath)
        console.log(`智能预加载成功: ${cleanPath}`)
      } catch (error) {
        console.warn(`智能预加载失败: ${routePath} -> ${cleanPath}`, error)
      }

      // 使用requestIdleCallback在浏览器空闲时继续处理
      if (window.requestIdleCallback) {
        window.requestIdleCallback(processNext, { timeout: 1000 })
      } else {
        setTimeout(processNext, 100)
      }
    }

    if (window.requestIdleCallback) {
      window.requestIdleCallback(processNext, { timeout: 1000 })
    } else {
      setTimeout(processNext, 100)
    }
  }

  /**
   * 根据用户权限预加载路由
   * @param {Array} userRoutes - 用户可访问的路由
   */
  preloadByPermissions(userRoutes) {
    userRoutes.forEach((route) => {
      if (route.component && typeof route.component === 'string') {
        this.addToPreloadQueue(route.component, 1)
      }

      if (route.children) {
        this.preloadByPermissions(route.children)
      }
    })
  }

  /**
   * 预加载相关路由
   * @param {string} currentRoute - 当前路由
   */
  preloadRelatedRoutes(currentRoute) {
    // 根据路由关系预加载相关路由
    const relatedRoutes = this.getRelatedRoutes(currentRoute)

    relatedRoutes.forEach((route) => {
      this.addToPreloadQueue(route, 0.5)
    })
  }

  /**
   * 获取相关路由
   * @param {string} currentRoute - 当前路由
   * @returns {Array} 相关路由数组
   */
  getRelatedRoutes(currentRoute) {
    const related = []

    // 定义有效的路由组件路径（避免预加载不存在的父级路由）
    const validRoutes = new Set([
      'device/baseinfo',
      'device/type',
      'process/process-card',
      'device-maintenance/repair-records',
      'system/user',
      'system/role',
      'system/permission',
      'system/menu',
      'system/dept',
      'system/api',
      'system/dict',
      'system/param',
      'dashboard/index',
      'statistics/overview',
    ])

    // 基于路由层级关系（仅预加载存在的组件）
    const pathSegments = currentRoute.split('/')
    if (pathSegments.length > 1) {
      // 父级路由
      const parentPath = pathSegments.slice(0, -1).join('/')
      if (parentPath && validRoutes.has(parentPath)) {
        related.push(parentPath)
      }
    }

    // 基于业务逻辑的关联路由
    const routeRelations = {
      'device/baseinfo': ['device/type', 'process/process-card'],
      'device/type': ['device/baseinfo'],
      'process/process-card': ['device/baseinfo'],
      'system/user': ['system/role', 'system/permission'],
      'dashboard/index': ['statistics/overview', 'device/baseinfo'],
    }

    if (routeRelations[currentRoute]) {
      // 只添加有效的路由
      const validRelatedRoutes = routeRelations[currentRoute].filter((route) =>
        validRoutes.has(route)
      )
      related.push(...validRelatedRoutes)
    }

    return related
  }
}

// 全局智能预加载器实例
export const smartPreloader = new SmartPreloader()

/**
 * 路由组件缓存管理
 */
export class RouteComponentCache {
  constructor() {
    this.cache = new Map()
    this.maxCacheSize = 20
    this.accessOrder = []
  }

  /**
   * 获取缓存的组件
   * @param {string} key - 缓存键
   * @returns {Object|null} 缓存的组件
   */
  get(key) {
    if (this.cache.has(key)) {
      // 更新访问顺序
      this.updateAccessOrder(key)
      return this.cache.get(key)
    }
    return null
  }

  /**
   * 设置缓存
   * @param {string} key - 缓存键
   * @param {Object} component - 组件
   */
  set(key, component) {
    // 如果缓存已满，删除最少使用的项
    if (this.cache.size >= this.maxCacheSize && !this.cache.has(key)) {
      const lruKey = this.accessOrder.shift()
      this.cache.delete(lruKey)
    }

    this.cache.set(key, component)
    this.updateAccessOrder(key)
  }

  /**
   * 更新访问顺序
   * @param {string} key - 缓存键
   */
  updateAccessOrder(key) {
    const index = this.accessOrder.indexOf(key)
    if (index > -1) {
      this.accessOrder.splice(index, 1)
    }
    this.accessOrder.push(key)
  }

  /**
   * 清除缓存
   * @param {string} key - 缓存键，如果不提供则清除所有
   */
  clear(key) {
    if (key) {
      this.cache.delete(key)
      const index = this.accessOrder.indexOf(key)
      if (index > -1) {
        this.accessOrder.splice(index, 1)
      }
    } else {
      this.cache.clear()
      this.accessOrder = []
    }
  }

  /**
   * 获取缓存统计信息
   */
  getStats() {
    return {
      size: this.cache.size,
      maxSize: this.maxCacheSize,
      keys: Array.from(this.cache.keys()),
      accessOrder: [...this.accessOrder],
    }
  }
}

// 全局路由组件缓存实例
export const routeComponentCache = new RouteComponentCache()

/**
 * 优化的路由组件创建函数
 * 集成缓存和智能预加载
 */
export function createOptimizedRouteComponent(path, options = {}) {
  return () => {
    // 检查缓存
    const cached = routeComponentCache.get(path)
    if (cached) {
      return cached
    }

    // 创建懒加载组件
    const component = createLazyComponent(async () => {
      // 清理路径，移除空段和多余的斜杠
      const cleanPath = path
        .split('/')
        .filter((segment) => segment.trim() !== '')
        .join('/')

      if (!cleanPath) {
        throw new Error(`Invalid route path: ${path}`)
      }

      const module = await import(/* webpackChunkName: "[request]" */ `../views/${cleanPath}.vue`)

      // 缓存组件
      routeComponentCache.set(path, module)

      // 记录访问
      smartPreloader.recordAccess(path)

      // 预加载相关路由
      smartPreloader.preloadRelatedRoutes(path)

      return module
    }, options)

    return component
  }
}

export default {
  createLazyComponent,
  createRouteComponent,
  createRouteComponents,
  preloadRouteComponents,
  createOptimizedRouteComponent,
  smartPreloader,
  routeComponentCache,
}
