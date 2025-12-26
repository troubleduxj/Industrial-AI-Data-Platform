/**
 * 权限实时更新插件
 * 全局安装权限实时更新功能
 */

import { nextTick } from 'vue'

// 权限实时更新管理器
class PermissionRealtimeManager {
  constructor() {
    this.isInstalled = false
    this.app = null
    this.interceptors = []
    this.eventListeners = []
    this.config = {
      autoRefresh: true,
      refreshInterval: 30000,
      enableApiInterception: true,
      enableStorageWatch: true,
      debugMode: false,
    }
  }

  /**
   * 安装插件
   */
  install(app, options = {}) {
    if (this.isInstalled) {
      console.warn('权限实时更新插件已安装')
      return
    }

    this.app = app
    this.config = { ...this.config, ...options }
    this.isInstalled = true

    console.log('🔧 安装权限实时更新插件', this.config)

    // 设置全局属性
    this.setupGlobalProperties()

    // 设置API拦截器
    if (this.config.enableApiInterception) {
      this.setupApiInterceptors()
    }

    // 设置存储监听
    if (this.config.enableStorageWatch) {
      this.setupStorageWatcher()
    }

    // 设置全局事件监听
    this.setupGlobalEventListeners()

    console.log('✅ 权限实时更新插件安装完成')
  }

  /**
   * 设置全局属性
   */
  setupGlobalProperties() {
    const globalProperties = this.app.config.globalProperties

    // 权限刷新方法
    globalProperties.$refreshPermissions = async (source = 'global') => {
      return await this.refreshPermissions(source)
    }

    // 清除权限缓存方法
    globalProperties.$clearPermissionCache = () => {
      return this.clearPermissionCache()
    }

    // 强制刷新页面权限
    globalProperties.$forceRefreshPagePermissions = async () => {
      return await this.forceRefreshPagePermissions()
    }

    // 获取权限状态
    globalProperties.$getPermissionStatus = () => {
      return this.getPermissionStatus()
    }

    console.log('✅ 全局权限方法已注册')
  }

  /**
   * 设置API拦截器
   */
  setupApiInterceptors() {
    // 拦截fetch请求
    const originalFetch = window.fetch

    window.fetch = async (...args) => {
      const response = await originalFetch.apply(window, args)

      // 检查权限相关API
      this.checkPermissionApiResponse(args[0], response)

      return response
    }

    this.interceptors.push({
      type: 'fetch',
      original: originalFetch,
    })

    console.log('✅ API拦截器已设置')
  }

  /**
   * 检查权限相关API响应
   */
  async checkPermissionApiResponse(url, response) {
    try {
      if (typeof url !== 'string' || !response.ok) {
        return
      }

      // 权限相关API模式
      const permissionApiPatterns = [
        '/api/v2/roles',
        '/api/v2/users',
        '/api/v2/menus',
        '/api/v2/permissions',
        '/api/v2/auth/user',
      ]

      const isPermissionApi = permissionApiPatterns.some((pattern) => url.includes(pattern))

      if (isPermissionApi) {
        if (this.config.debugMode) {
          console.log(`🔔 检测到权限API调用: ${url}`)
        }

        // 延迟触发权限刷新，避免频繁刷新
        setTimeout(() => {
          this.triggerPermissionRefresh('api-change', { url })
        }, 1000)
      }
    } catch (error) {
      console.error('❌ 检查权限API响应失败:', error)
    }
  }

  /**
   * 设置存储监听
   */
  setupStorageWatcher() {
    const storageListener = (event) => {
      if (event.key === 'access_token' || event.key === 'user_info') {
        if (this.config.debugMode) {
          console.log(`🔔 检测到存储变化: ${event.key}`)
        }

        this.triggerPermissionRefresh('storage-change', {
          key: event.key,
          oldValue: event.oldValue,
          newValue: event.newValue,
        })
      }
    }

    window.addEventListener('storage', storageListener)
    this.eventListeners.push(['storage', storageListener])

    console.log('✅ 存储监听器已设置')
  }

  /**
   * 设置全局事件监听
   */
  setupGlobalEventListeners() {
    // 监听页面可见性变化
    const visibilityChangeListener = () => {
      if (document.visibilityState === 'visible') {
        // 页面变为可见时，检查权限是否需要刷新
        setTimeout(() => {
          this.checkAndRefreshPermissions('visibility-change')
        }, 1000)
      }
    }

    document.addEventListener('visibilitychange', visibilityChangeListener)
    this.eventListeners.push(['visibilitychange', visibilityChangeListener])

    // 监听焦点事件
    const focusListener = () => {
      this.checkAndRefreshPermissions('focus')
    }

    window.addEventListener('focus', focusListener)
    this.eventListeners.push(['focus', focusListener])

    console.log('✅ 全局事件监听器已设置')
  }

  /**
   * 触发权限刷新
   */
  async triggerPermissionRefresh(source, data = {}) {
    try {
      // 发送自定义事件
      window.dispatchEvent(
        new CustomEvent('permission-refresh-triggered', {
          detail: {
            source: source,
            data: data,
            timestamp: Date.now(),
          },
        })
      )

      // 执行权限刷新
      await this.refreshPermissions(source)
    } catch (error) {
      console.error('❌ 触发权限刷新失败:', error)
    }
  }

  /**
   * 刷新权限
   */
  async refreshPermissions(source = 'unknown') {
    try {
      if (this.config.debugMode) {
        console.log(`🔄 刷新权限数据 (来源: ${source})`)
      }

      // 获取权限Store
      const permissionStore = await this.getPermissionStore()
      if (!permissionStore) {
        throw new Error('无法获取权限Store')
      }

      // 刷新权限数据
      await permissionStore.refreshPermissions({
        clearCache: true,
        notifyUI: true,
        source: source,
      })

      // 发送权限更新完成事件
      window.dispatchEvent(
        new CustomEvent('permission-refresh-completed', {
          detail: {
            source: source,
            timestamp: Date.now(),
          },
        })
      )

      if (this.config.debugMode) {
        console.log('✅ 权限数据刷新完成')
      }
    } catch (error) {
      console.error('❌ 刷新权限数据失败:', error)

      // 发送权限更新失败事件
      window.dispatchEvent(
        new CustomEvent('permission-refresh-failed', {
          detail: {
            source: source,
            error: error.message,
            timestamp: Date.now(),
          },
        })
      )

      throw error
    }
  }

  /**
   * 检查并刷新权限
   */
  async checkAndRefreshPermissions(source) {
    try {
      const permissionStore = await this.getPermissionStore()
      if (!permissionStore) {
        return
      }

      // 检查缓存是否过期
      const isMenuCacheValid = permissionStore.isCacheValid('menus')
      const isApiCacheValid = permissionStore.isCacheValid('apis')

      if (!isMenuCacheValid || !isApiCacheValid) {
        if (this.config.debugMode) {
          console.log(`🔄 检测到权限缓存过期，触发刷新 (来源: ${source})`)
        }
        await this.refreshPermissions(source)
      }
    } catch (error) {
      console.error('❌ 检查权限状态失败:', error)
    }
  }

  /**
   * 清除权限缓存
   */
  clearPermissionCache() {
    try {
      // 发送清除缓存事件
      window.dispatchEvent(
        new CustomEvent('permission-cache-clear', {
          detail: {
            timestamp: Date.now(),
          },
        })
      )

      console.log('✅ 权限缓存清除事件已发送')
    } catch (error) {
      console.error('❌ 清除权限缓存失败:', error)
    }
  }

  /**
   * 强制刷新页面权限
   */
  async forceRefreshPagePermissions() {
    try {
      console.log('🔄 强制刷新页面权限')

      // 清除缓存
      this.clearPermissionCache()

      // 刷新权限
      await this.refreshPermissions('force-page')

      // 等待数据更新
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // 刷新页面
      window.location.reload()
    } catch (error) {
      console.error('❌ 强制刷新页面权限失败:', error)
      throw error
    }
  }

  /**
   * 获取权限Store
   */
  async getPermissionStore() {
    try {
      // 方法1: 通过Pinia获取
      if (this.app && this.app.config.globalProperties.$pinia) {
        const pinia = this.app.config.globalProperties.$pinia
        if (pinia._s && pinia._s.has('enhancedPermission')) {
          return pinia._s.get('enhancedPermission')
        }
      }

      // 方法2: 通过全局变量获取
      if (window.__VUE_APP__ && window.__VUE_APP__.config.globalProperties.$pinia) {
        const pinia = window.__VUE_APP__.config.globalProperties.$pinia
        if (pinia._s && pinia._s.has('enhancedPermission')) {
          return pinia._s.get('enhancedPermission')
        }
      }

      // 方法3: 动态导入
      const { useEnhancedPermissionStore } = await import('@/store/modules/permission')
      return useEnhancedPermissionStore()
    } catch (error) {
      console.error('❌ 获取权限Store失败:', error)
      return null
    }
  }

  /**
   * 获取权限状态
   */
  getPermissionStatus() {
    return {
      isInstalled: this.isInstalled,
      config: this.config,
      interceptorsCount: this.interceptors.length,
      eventListenersCount: this.eventListeners.length,
      lastCheckTime: new Date().toISOString(),
    }
  }

  /**
   * 卸载插件
   */
  uninstall() {
    if (!this.isInstalled) {
      return
    }

    console.log('🔧 卸载权限实时更新插件')

    // 恢复原始API
    this.interceptors.forEach((interceptor) => {
      if (interceptor.type === 'fetch') {
        window.fetch = interceptor.original
      }
    })

    // 移除事件监听器
    this.eventListeners.forEach(([eventType, listener]) => {
      if (eventType === 'visibilitychange') {
        document.removeEventListener(eventType, listener)
      } else {
        window.removeEventListener(eventType, listener)
      }
    })

    // 重置状态
    this.isInstalled = false
    this.app = null
    this.interceptors = []
    this.eventListeners = []

    console.log('✅ 权限实时更新插件已卸载')
  }
}

// 创建插件实例
const permissionRealtimeManager = new PermissionRealtimeManager()

// 导出插件
export default {
  install(app, options = {}) {
    permissionRealtimeManager.install(app, options)
  },

  // 导出管理器实例供外部使用
  manager: permissionRealtimeManager,
}

// 导出管理器类
export { PermissionRealtimeManager }

// 全局可用
if (typeof window !== 'undefined') {
  window.PermissionRealtimeManager = permissionRealtimeManager
}
