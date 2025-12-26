/**
 * 权限实时更新组合式函数
 * 用于在Vue组件中监听和响应权限变更
 */

import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useEnhancedPermissionStore } from '@/store/modules/permission'
import { useUserStore } from '@/store/modules/user'

/**
 * 权限实时更新组合式函数
 */
export function usePermissionRealtime(options = {}) {
  const {
    autoRefresh = true, // 是否自动刷新
    refreshInterval = 30000, // 刷新间隔（毫秒）
    watchMenuChanges = true, // 是否监听菜单变更
    watchApiChanges = true, // 是否监听API权限变更
    onPermissionChanged = null, // 权限变更回调
  } = options

  // 状态
  const isRefreshing = ref(false)
  const lastRefreshTime = ref(null)
  const refreshCount = ref(0)
  const errorCount = ref(0)
  const lastError = ref(null)

  // Store实例
  const permissionStore = useEnhancedPermissionStore()
  const userStore = useUserStore()

  // 定时器
  let refreshTimer = null
  let eventListeners = []

  /**
   * 刷新权限数据
   */
  const refreshPermissions = async (source = 'manual') => {
    if (isRefreshing.value) {
      console.log('权限刷新正在进行中，跳过本次刷新')
      return
    }

    try {
      isRefreshing.value = true
      lastError.value = null

      console.log(`🔄 开始刷新权限数据 (来源: ${source})`)

      // 刷新权限Store数据
      await permissionStore.refreshPermissions({
        clearCache: true,
        notifyUI: true,
        source: source,
      })

      // 刷新用户信息（包含菜单数据）
      if (userStore.refreshUserInfo) {
        await userStore.refreshUserInfo()
      }

      // 更新状态
      lastRefreshTime.value = new Date().toISOString()
      refreshCount.value++

      // 触发回调
      if (onPermissionChanged) {
        await nextTick()
        onPermissionChanged({
          type: 'REFRESH_SUCCESS',
          source: source,
          timestamp: Date.now(),
        })
      }

      console.log('✅ 权限数据刷新成功')
    } catch (error) {
      console.error('❌ 权限数据刷新失败:', error)
      lastError.value = error
      errorCount.value++

      // 触发错误回调
      if (onPermissionChanged) {
        onPermissionChanged({
          type: 'REFRESH_ERROR',
          source: source,
          error: error,
          timestamp: Date.now(),
        })
      }

      throw error
    } finally {
      isRefreshing.value = false
    }
  }

  /**
   * 处理权限变更事件
   */
  const handlePermissionChange = async (event) => {
    console.log('🔔 收到权限变更事件:', event.type, event.detail)

    try {
      // 根据事件类型决定刷新策略
      const { type, source = 'event' } = event.detail || {}

      switch (type) {
        case 'ROLE_PERMISSION_CHANGED':
        case 'MENU_PERMISSION_CHANGED':
        case 'USER_ROLE_CHANGED':
          // 完整刷新
          await refreshPermissions(`${source}-${type}`)
          break

        case 'API_PERMISSION_CHANGED':
          // 只刷新API权限
          await permissionStore.getAccessApis(true)
          break

        case 'MANUAL_REFRESH':
          // 手动刷新
          await refreshPermissions('manual')
          break

        default:
          console.log('未知的权限变更类型:', type)
      }
    } catch (error) {
      console.error('❌ 处理权限变更事件失败:', error)
    }
  }

  /**
   * 处理菜单更新事件
   */
  const handleMenuUpdate = async (event) => {
    console.log('🍽️ 收到菜单更新事件:', event.detail)

    if (onPermissionChanged) {
      onPermissionChanged({
        type: 'MENU_UPDATED',
        data: event.detail,
        timestamp: Date.now(),
      })
    }
  }

  /**
   * 处理存储变更事件
   */
  const handleStorageChange = async (event) => {
    if (event.key === 'access_token') {
      console.log('🔑 检测到token变更')

      if (event.newValue && event.newValue !== event.oldValue) {
        // token更新，刷新权限
        setTimeout(() => refreshPermissions('token-change'), 1000)
      }
    }
  }

  /**
   * 启动自动刷新
   */
  const startAutoRefresh = () => {
    if (!autoRefresh || refreshTimer) {
      return
    }

    console.log(`🚀 启动权限自动刷新，间隔: ${refreshInterval}ms`)

    refreshTimer = setInterval(() => {
      refreshPermissions('auto')
    }, refreshInterval)
  }

  /**
   * 停止自动刷新
   */
  const stopAutoRefresh = () => {
    if (refreshTimer) {
      console.log('⏹️ 停止权限自动刷新')
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  /**
   * 添加事件监听器
   */
  const setupEventListeners = () => {
    // 权限变更事件
    const permissionChangeListener = (event) => handlePermissionChange(event)
    window.addEventListener('permission-updated', permissionChangeListener)
    eventListeners.push(['permission-updated', permissionChangeListener])

    // 权限数据更新事件
    const dataUpdateListener = (event) => handlePermissionChange(event)
    window.addEventListener('permission-data-updated', dataUpdateListener)
    eventListeners.push(['permission-data-updated', dataUpdateListener])

    // 菜单更新事件
    if (watchMenuChanges) {
      const menuUpdateListener = (event) => handleMenuUpdate(event)
      window.addEventListener('user-menus-updated', menuUpdateListener)
      eventListeners.push(['user-menus-updated', menuUpdateListener])
    }

    // 存储变更事件
    const storageChangeListener = (event) => handleStorageChange(event)
    window.addEventListener('storage', storageChangeListener)
    eventListeners.push(['storage', storageChangeListener])

    // 手动刷新事件
    const manualRefreshListener = (event) => handlePermissionChange(event)
    window.addEventListener('manual-permission-refresh', manualRefreshListener)
    eventListeners.push(['manual-permission-refresh', manualRefreshListener])

    console.log(`📡 已设置 ${eventListeners.length} 个权限事件监听器`)
  }

  /**
   * 移除事件监听器
   */
  const removeEventListeners = () => {
    eventListeners.forEach(([eventType, listener]) => {
      window.removeEventListener(eventType, listener)
    })
    eventListeners = []
    console.log('📡 已移除所有权限事件监听器')
  }

  /**
   * 强制刷新当前页面权限
   */
  const forceRefreshPage = async () => {
    try {
      console.log('🔄 强制刷新当前页面权限')

      // 清除所有缓存
      permissionStore.clearCache()

      // 刷新权限数据
      await refreshPermissions('force-page')

      // 等待一段时间确保数据更新
      await new Promise((resolve) => setTimeout(resolve, 500))

      // 刷新页面
      window.location.reload()
    } catch (error) {
      console.error('❌ 强制刷新页面权限失败:', error)
      throw error
    }
  }

  /**
   * 手动触发权限刷新
   */
  const manualRefresh = async () => {
    await refreshPermissions('manual')
  }

  /**
   * 获取权限状态
   */
  const getPermissionStatus = () => {
    return {
      isRefreshing: isRefreshing.value,
      lastRefreshTime: lastRefreshTime.value,
      refreshCount: refreshCount.value,
      errorCount: errorCount.value,
      lastError: lastError.value,
      hasAutoRefresh: !!refreshTimer,
      eventListenersCount: eventListeners.length,
    }
  }

  // 生命周期钩子
  onMounted(() => {
    console.log('🔧 权限实时更新组合式函数已挂载')

    // 设置事件监听器
    setupEventListeners()

    // 启动自动刷新
    if (autoRefresh) {
      startAutoRefresh()
    }

    // 初始化时刷新一次权限
    nextTick(() => {
      refreshPermissions('mount')
    })
  })

  onUnmounted(() => {
    console.log('🔧 权限实时更新组合式函数已卸载')

    // 停止自动刷新
    stopAutoRefresh()

    // 移除事件监听器
    removeEventListeners()
  })

  // 返回API
  return {
    // 状态
    isRefreshing,
    lastRefreshTime,
    refreshCount,
    errorCount,
    lastError,

    // 方法
    refreshPermissions,
    manualRefresh,
    forceRefreshPage,
    startAutoRefresh,
    stopAutoRefresh,
    getPermissionStatus,

    // 事件处理
    handlePermissionChange,
    handleMenuUpdate,
  }
}

/**
 * 权限变更监听器组合式函数
 * 用于监听特定的权限变更事件
 */
export function usePermissionChangeListener(callback, options = {}) {
  const { events = ['permission-updated', 'user-menus-updated'], immediate = false } = options

  const listeners = ref([])

  const setupListeners = () => {
    events.forEach((eventType) => {
      const listener = (event) => {
        callback(event, eventType)
      }

      window.addEventListener(eventType, listener)
      listeners.value.push([eventType, listener])
    })

    console.log(`📡 设置权限变更监听器，监听事件: ${events.join(', ')}`)
  }

  const removeListeners = () => {
    listeners.value.forEach(([eventType, listener]) => {
      window.removeEventListener(eventType, listener)
    })
    listeners.value = []
    console.log('📡 移除权限变更监听器')
  }

  onMounted(() => {
    setupListeners()

    if (immediate) {
      // 立即触发一次回调
      callback({ detail: { type: 'IMMEDIATE', timestamp: Date.now() } }, 'immediate')
    }
  })

  onUnmounted(() => {
    removeListeners()
  })

  return {
    setupListeners,
    removeListeners,
  }
}

/**
 * 权限缓存状态组合式函数
 */
export function usePermissionCacheStatus() {
  const cacheStatus = ref({
    isValid: false,
    lastUpdate: null,
    hitRate: 0,
  })

  const updateCacheStatus = () => {
    const permissionStore = useEnhancedPermissionStore()

    cacheStatus.value = {
      isValid: permissionStore.isCacheValid('menus') && permissionStore.isCacheValid('apis'),
      lastUpdate: new Date().toISOString(),
      hitRate: permissionStore.cacheHitRate,
    }
  }

  onMounted(() => {
    updateCacheStatus()

    // 定期更新缓存状态
    const timer = setInterval(updateCacheStatus, 5000)

    onUnmounted(() => {
      clearInterval(timer)
    })
  })

  return {
    cacheStatus,
    updateCacheStatus,
  }
}
