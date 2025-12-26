/**
 * 统一状态管理组合式函数
 * 提供在Vue组件中使用统一状态管理的便捷方法
 */
import { computed, watch, onMounted, onUnmounted } from 'vue'
import {
  unifiedStateManager,
  useStores,
  useStore,
  useUnifiedCollectorStore,
  useCollectorConfigStore,
  useCollectorMonitorStore,
  useUIStateStore,
} from '@/store/unified-state'

/**
 * 使用统一状态管理
 * @returns {Object} 统一状态管理相关方法和状态
 */
export function useUnifiedState() {
  const stores = useStores()

  return {
    // 状态管理器实例
    stateManager: unifiedStateManager,

    // 所有store
    stores,

    // 便捷访问方法
    getStore: useStore,

    // 初始化状态
    async initialize() {
      return await unifiedStateManager.initialize()
    },

    // 重置状态
    async reset() {
      return await unifiedStateManager.resetAllStates()
    },

    // 获取状态快照
    getSnapshot() {
      return unifiedStateManager.getStateSnapshot()
    },

    // 导出状态
    exportState() {
      return unifiedStateManager.exportState()
    },

    // 导入状态
    async importState(data) {
      return await unifiedStateManager.importState(data)
    },
  }
}

/**
 * 使用采集器状态
 * @returns {Object} 采集器相关状态和方法
 */
export function useCollectorState() {
  const collectorStore = useUnifiedCollectorStore()
  const configStore = useCollectorConfigStore()
  const monitorStore = useCollectorMonitorStore()

  return {
    // 采集器store
    collector: collectorStore,
    config: configStore,
    monitor: monitorStore,

    // 采集器列表
    collectors: computed(() => collectorStore.collectors),

    // 当前采集器
    currentCollector: computed(() => collectorStore.currentCollector),

    // 加载状态
    loading: computed(() => collectorStore.loading),

    // 统计信息
    statistics: computed(() => collectorStore.statistics),

    // 实时监控数据
    realtimeData: computed(() => monitorStore.realtimeData),

    // 告警信息
    alerts: computed(() => monitorStore.alerts),

    // 系统健康状态
    systemHealth: computed(() => monitorStore.systemHealthStatus),

    // 方法
    async fetchCollectors(params) {
      return await collectorStore.fetchCollectors(params)
    },

    async createCollector(data) {
      return await collectorStore.createCollector(data)
    },

    async updateCollector(id, data) {
      return await collectorStore.updateCollector(id, data)
    },

    async deleteCollector(id) {
      return await collectorStore.deleteCollector(id)
    },

    async startCollector(id) {
      return await collectorStore.startCollector(id)
    },

    async stopCollector(id) {
      return await collectorStore.stopCollector(id)
    },

    async restartCollector(id) {
      return await collectorStore.restartCollector(id)
    },
  }
}

/**
 * 使用UI状态
 * @returns {Object} UI相关状态和方法
 */
export function useUIState() {
  const uiStore = useUIStateStore()

  return {
    // UI store
    ui: uiStore,

    // 布局状态
    layout: computed(() => uiStore.layout),
    sidebarCollapsed: computed(() => uiStore.layout.sidebarCollapsed),

    // 主题状态
    theme: computed(() => uiStore.currentTheme),
    isDarkMode: computed(() => uiStore.isDarkMode),

    // 响应式状态
    breakpoints: computed(() => uiStore.breakpoints),
    isMobile: computed(() => uiStore.breakpoints.isMobile),
    isTablet: computed(() => uiStore.breakpoints.isTablet),
    isDesktop: computed(() => uiStore.breakpoints.isDesktop),

    // 页面状态
    currentPage: computed(() => uiStore.pages.current),
    tabs: computed(() => uiStore.pages.tabs),
    breadcrumb: computed(() => uiStore.formattedBreadcrumb),

    // 模态框状态
    activeModals: computed(() => uiStore.activeModalsCount),
    hasModal: computed(() => uiStore.hasActiveModal),

    // 通知状态
    notifications: computed(() => uiStore.notifications.notifications),
    unreadCount: computed(() => uiStore.notifications.notifications.filter((n) => !n.read).length),

    // 方法
    toggleSidebar() {
      uiStore.toggleSidebar()
    },

    setSidebarCollapsed(collapsed) {
      uiStore.setSidebarCollapsed(collapsed)
    },

    setThemeMode(mode) {
      uiStore.setThemeMode(mode)
    },

    setPrimaryColor(color) {
      uiStore.setPrimaryColor(color)
    },

    openModal(id, config) {
      uiStore.openModal(id, config)
    },

    closeModal(id) {
      uiStore.closeModal(id)
    },

    addNotification(notification) {
      uiStore.addNotification(notification)
    },

    markNotificationRead(id) {
      uiStore.markNotificationRead(id)
    },

    setCurrentPage(pageInfo) {
      uiStore.setCurrentPage(pageInfo)
    },

    addTab(tab) {
      uiStore.addTab(tab)
    },

    closeTab(path) {
      uiStore.closeTab(path)
    },
  }
}

/**
 * 使用状态同步
 * 在组件中设置状态同步和监听
 * @param {Object} options 配置选项
 */
export function useStateSync(options = {}) {
  const {
    watchCollectorStatus = false,
    watchUIChanges = false,
    watchMonitorData = false,
    onCollectorChange = null,
    onUIChange = null,
    onMonitorChange = null,
  } = options

  const stores = useStores()
  const watchers = []

  onMounted(() => {
    // 监听采集器状态变化
    if (watchCollectorStatus && onCollectorChange) {
      const stopWatcher = watch(
        () => stores.collector.currentCollector,
        (newCollector, oldCollector) => {
          onCollectorChange(newCollector, oldCollector)
        },
        { deep: true }
      )
      watchers.push(stopWatcher)
    }

    // 监听UI状态变化
    if (watchUIChanges && onUIChange) {
      const stopWatcher = watch(
        () => stores.ui.theme,
        (newTheme, oldTheme) => {
          onUIChange(newTheme, oldTheme)
        },
        { deep: true }
      )
      watchers.push(stopWatcher)
    }

    // 监听监控数据变化
    if (watchMonitorData && onMonitorChange) {
      const stopWatcher = watch(
        () => stores.collectorMonitor.realtimeData,
        (newData, oldData) => {
          onMonitorChange(newData, oldData)
        },
        { deep: true }
      )
      watchers.push(stopWatcher)
    }
  })

  onUnmounted(() => {
    // 清理监听器
    watchers.forEach((stop) => stop())
    watchers.length = 0
  })

  return {
    stores,

    // 手动触发同步
    syncStates() {
      // 这里可以添加手动同步逻辑
      console.log('手动同步状态')
    },
  }
}

/**
 * 使用状态持久化
 * 管理状态的本地存储
 */
export function useStatePersistence() {
  const stateManager = unifiedStateManager

  return {
    // 保存状态到本地存储
    async saveToLocal(key = 'app-state') {
      try {
        const stateData = stateManager.exportState()
        localStorage.setItem(key, JSON.stringify(stateData))
        return true
      } catch (error) {
        console.error('保存状态失败:', error)
        return false
      }
    },

    // 从本地存储加载状态
    async loadFromLocal(key = 'app-state') {
      try {
        const data = localStorage.getItem(key)
        if (data) {
          const stateData = JSON.parse(data)
          await stateManager.importState(stateData)
          return true
        }
        return false
      } catch (error) {
        console.error('加载状态失败:', error)
        return false
      }
    },

    // 清除本地存储的状态
    clearLocal(key = 'app-state') {
      try {
        localStorage.removeItem(key)
        return true
      } catch (error) {
        console.error('清除状态失败:', error)
        return false
      }
    },

    // 导出状态到文件
    exportToFile(filename = 'app-state.json') {
      try {
        const stateData = stateManager.exportState()
        const blob = new Blob([JSON.stringify(stateData, null, 2)], {
          type: 'application/json',
        })

        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        return true
      } catch (error) {
        console.error('导出状态失败:', error)
        return false
      }
    },

    // 从文件导入状态
    async importFromFile(file) {
      try {
        const text = await file.text()
        const stateData = JSON.parse(text)
        await stateManager.importState(stateData)
        return true
      } catch (error) {
        console.error('导入状态失败:', error)
        return false
      }
    },
  }
}

/**
 * 使用状态调试
 * 提供状态调试和开发工具
 */
export function useStateDebug() {
  const stateManager = unifiedStateManager

  return {
    // 打印当前状态
    logCurrentState() {
      console.log('当前状态快照:', stateManager.getStateSnapshot())
    },

    // 监控状态变化
    startStateMonitoring() {
      const stores = stateManager.getAllStores()

      Object.entries(stores).forEach(([name, store]) => {
        store.$subscribe((mutation, state) => {
          console.log(`[${name}] 状态变化:`, {
            type: mutation.type,
            storeId: mutation.storeId,
            payload: mutation.payload,
            events: mutation.events,
          })
        })
      })
    },

    // 性能分析
    analyzePerformance() {
      const stores = stateManager.getAllStores()
      const analysis = {}

      Object.entries(stores).forEach(([name, store]) => {
        const stateSize = JSON.stringify(store.$state).length
        analysis[name] = {
          stateSize,
          stateSizeKB: (stateSize / 1024).toFixed(2),
        }
      })

      console.table(analysis)
      return analysis
    },

    // 重置特定store
    resetStore(storeName) {
      const store = stateManager.getStore(storeName)
      if (store && typeof store.$reset === 'function') {
        store.$reset()
        console.log(`${storeName} store已重置`)
      } else {
        console.warn(`无法重置 ${storeName} store`)
      }
    },
  }
}

export default {
  useUnifiedState,
  useCollectorState,
  useUIState,
  useStateSync,
  useStatePersistence,
  useStateDebug,
}
