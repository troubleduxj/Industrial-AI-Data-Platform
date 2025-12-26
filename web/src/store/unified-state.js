/**
 * 统一状态管理入口
 * 整合所有状态管理模块，提供统一的接口和初始化方法
 */
import { useUIStateStore } from './modules/ui-state'
import { useAppStore } from './modules/app'
import { useUserStore } from './modules/user'
import { usePermissionStore } from './modules/permission'
import { useTagsStore } from './modules/tags'
import { useChatWidgetStore } from './modules/chatWidget'

/**
 * 统一状态管理类
 * 提供所有store的统一访问接口
 */
export class UnifiedStateManager {
  constructor() {
    this.stores = null
    this.initialized = false
    this.initPromise = null
  }

  /**
   * 初始化stores（延迟初始化，确保Pinia已准备好）
   */
  _initializeStores() {
    if (this.stores) {
      return this.stores
    }

    this.stores = {
      // 界面状态
      ui: useUIStateStore(),

      // 系统状态
      app: useAppStore(),
      user: useUserStore(),
      permission: usePermissionStore(),
      tags: useTagsStore(),
      chatWidget: useChatWidgetStore(),
    }

    return this.stores
  }

  /**
   * 获取指定store
   */
  getStore(name) {
    const stores = this._initializeStores()
    return stores[name]
  }

  /**
   * 获取所有store
   */
  getAllStores() {
    return this._initializeStores()
  }

  /**
   * 初始化所有状态管理
   */
  async initialize() {
    if (this.initialized) {
      return this.initPromise
    }

    if (this.initPromise) {
      return this.initPromise
    }

    this.initPromise = this._doInitialize()
    return this.initPromise
  }

  /**
   * 执行初始化
   */
  async _doInitialize() {
    try {
      console.log('开始初始化统一状态管理...')

      // 确保stores已初始化
      this._initializeStores()

      // 1. 初始化UI状态（优先级最高，影响界面渲染）
      await this._initializeUIState()

      // 2. 初始化用户和权限状态
      await this._initializeUserState()

      // 3. 初始化应用状态
      await this._initializeAppState()

      // 4. 初始化业务状态
      await this._initializeBusinessState()

      // 5. 设置状态同步
      this._setupStateSynchronization()

      // 6. 设置错误处理
      this._setupErrorHandling()

      this.initialized = true
      console.log('统一状态管理初始化完成')
    } catch (error) {
      console.error('统一状态管理初始化失败:', error)
      throw error
    }
  }

  /**
   * 初始化UI状态
   */
  async _initializeUIState() {
    const stores = this._initializeStores()
    const uiStore = stores.ui

    // 加载用户偏好设置
    uiStore.loadPreferences()

    // 监听窗口大小变化
    const updateBreakpoints = () => {
      uiStore.updateBreakpoints(window.innerWidth, window.innerHeight)
    }

    window.addEventListener('resize', updateBreakpoints)
    updateBreakpoints()

    // 监听主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleThemeChange = (e) => {
      if (uiStore.theme.mode === 'auto') {
        uiStore.applyTheme()
      }
    }

    mediaQuery.addEventListener('change', handleThemeChange)

    console.log('UI状态初始化完成')
  }

  /**
   * 初始化用户状态
   */
  async _initializeUserState() {
    const stores = this._initializeStores()
    const userStore = stores.user
    const permissionStore = stores.permission

    try {
      // 检查用户登录状态
      if (userStore.token) {
        await userStore.getUserInfo()
        await permissionStore.generateRoutes(userStore.roles)
      }
    } catch (error) {
      console.warn('用户状态初始化失败:', error)
      // 清除无效的登录状态
      userStore.logout()
    }

    console.log('用户状态初始化完成')
  }

  /**
   * 初始化应用状态
   */
  async _initializeAppState() {
    const stores = this._initializeStores()
    const appStore = stores.app
    const tagsStore = stores.tags

    // 恢复应用状态
    // 这里可以添加应用级别的初始化逻辑

    console.log('应用状态初始化完成')
  }

  /**
   * 初始化业务状态
   */
  async _initializeBusinessState() {
    // 业务状态初始化逻辑
    // 这里可以添加其他业务模块的初始化逻辑

    console.log('业务状态初始化完成')
  }

  /**
   * 设置状态同步
   */
  _setupStateSynchronization() {
    // 状态同步逻辑
    // 这里可以添加其他模块间的状态同步逻辑

    console.log('状态同步设置完成')
  }

  /**
   * 设置错误处理
   */
  _setupErrorHandling() {
    const stores = this._initializeStores()
    const { ui } = stores

    // 全局错误处理
    window.addEventListener('error', (event) => {
      console.error('全局错误:', event.error)

      ui.addNotification({
        type: 'error',
        title: '系统错误',
        content: event.error?.message || '发生未知错误',
        duration: 5000,
      })
    })

    // Promise错误处理
    window.addEventListener('unhandledrejection', (event) => {
      console.error('未处理的Promise错误:', event.reason)

      ui.addNotification({
        type: 'error',
        title: '异步操作错误',
        content: event.reason?.message || '异步操作失败',
        duration: 5000,
      })
    })

    console.log('错误处理设置完成')
  }

  /**
   * 重置所有状态
   */
  async resetAllStates() {
    try {
      const stores = this._initializeStores()

      // 重置各个store
      Object.values(stores).forEach((store) => {
        if (typeof store.$reset === 'function') {
          store.$reset()
        }
      })

      // 清除本地存储
      stores.ui.resetPreferences()

      this.initialized = false
      this.initPromise = null

      console.log('所有状态已重置')
    } catch (error) {
      console.error('重置状态失败:', error)
      throw error
    }
  }

  /**
   * 获取状态快照
   */
  getStateSnapshot() {
    const stores = this._initializeStores()
    const snapshot = {}

    Object.entries(stores).forEach(([name, store]) => {
      snapshot[name] = {
        ...store.$state,
      }
    })

    return snapshot
  }

  /**
   * 导出状态数据
   */
  exportState() {
    const snapshot = this.getStateSnapshot()

    // 移除敏感信息
    if (snapshot.user) {
      delete snapshot.user.token
      delete snapshot.user.refreshToken
    }

    return {
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      data: snapshot,
    }
  }

  /**
   * 导入状态数据
   */
  async importState(stateData) {
    try {
      if (!stateData || !stateData.data) {
        throw new Error('无效的状态数据')
      }

      // 重置当前状态
      await this.resetAllStates()

      // 导入状态数据
      const stores = this._initializeStores()
      Object.entries(stateData.data).forEach(([name, state]) => {
        const store = stores[name]
        if (store && state) {
          // 安全地合并状态
          Object.assign(store.$state, state)
        }
      })

      // 重新初始化
      await this.initialize()

      console.log('状态数据导入完成')
    } catch (error) {
      console.error('导入状态数据失败:', error)
      throw error
    }
  }
}

// 全局状态管理实例（延迟创建）
let unifiedStateManagerInstance = null

/**
 * 获取统一状态管理实例
 * 延迟创建，确保Pinia已经初始化
 */
export const getUnifiedStateManager = () => {
  if (!unifiedStateManagerInstance) {
    unifiedStateManagerInstance = new UnifiedStateManager()
  }
  return unifiedStateManagerInstance
}

// 便捷的store访问函数
export const useStores = () => getUnifiedStateManager().getAllStores()
export const useStore = (name) => getUnifiedStateManager().getStore(name)

// 兼容性导出
export const unifiedStateManager = getUnifiedStateManager()

// 导出各个store的使用函数
export {
  useUIStateStore,
  useAppStore,
  useUserStore,
  usePermissionStore,
  useTagsStore,
  useChatWidgetStore,
}

// 默认导出
export default getUnifiedStateManager
