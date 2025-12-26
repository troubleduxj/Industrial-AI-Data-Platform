/**
 * 用户界面状态管理
 * 管理界面布局、主题、用户偏好设置和交互状态
 */
import { defineStore } from 'pinia'

export const useUIStateStore = defineStore('uiState', {
  state: () => ({
    // 布局设置
    layout: {
      sidebarCollapsed: false,
      sidebarWidth: 240,
      headerHeight: 60,
      footerHeight: 40,
      contentPadding: 16,
      showBreadcrumb: true,
      showTabs: true,
      tabsHeight: 40,
    },

    // 主题设置
    theme: {
      mode: 'light', // light, dark, auto
      primaryColor: '#1890ff',
      borderRadius: 6,
      fontSize: 14,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      customTheme: null,
    },

    // 页面状态
    pages: {
      // 当前页面信息
      current: {
        path: '',
        title: '',
        params: {},
        query: {},
        meta: {},
      },

      // 页面历史
      history: [],

      // 标签页
      tabs: [],

      // 面包屑
      breadcrumb: [],

      // 页面加载状态
      loading: false,

      // 页面错误状态
      error: null,
    },

    // 模态框和抽屉状态
    modals: {
      // 当前打开的模态框
      active: new Set(),

      // 模态框配置
      configs: new Map(),

      // 抽屉状态
      drawers: new Map(),

      // 全局遮罩
      globalMask: false,
    },

    // 表格状态
    tables: {
      // 表格配置
      configs: new Map(),

      // 列设置
      columns: new Map(),

      // 排序状态
      sorting: new Map(),

      // 过滤状态
      filters: new Map(),

      // 分页状态
      pagination: new Map(),

      // 选中行
      selections: new Map(),
    },

    // 表单状态
    forms: {
      // 表单数据
      data: new Map(),

      // 验证状态
      validation: new Map(),

      // 表单配置
      configs: new Map(),

      // 提交状态
      submitting: new Set(),

      // 脏数据标记
      dirty: new Set(),
    },

    // 通知和消息
    notifications: {
      // 消息列表
      messages: [],

      // 通知列表
      notifications: [],

      // 全局提示配置
      config: {
        duration: 3000,
        placement: 'topRight',
        maxCount: 5,
      },
    },

    // 用户偏好设置
    preferences: {
      // 语言设置
      language: 'zh-CN',

      // 时区设置
      timezone: 'Asia/Shanghai',

      // 日期格式
      dateFormat: 'YYYY-MM-DD',

      // 时间格式
      timeFormat: 'HH:mm:ss',

      // 数字格式
      numberFormat: {
        decimal: 2,
        separator: ',',
        currency: 'CNY',
      },

      // 表格偏好
      tablePreferences: {
        pageSize: 20,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: true,
      },

      // 图表偏好
      chartPreferences: {
        theme: 'default',
        animation: true,
        tooltip: true,
        legend: true,
      },
    },

    // 快捷键设置
    shortcuts: {
      enabled: true,
      bindings: new Map([
        ['ctrl+s', 'save'],
        ['ctrl+n', 'new'],
        ['ctrl+f', 'search'],
        ['esc', 'cancel'],
        ['f5', 'refresh'],
      ]),
    },

    // 响应式断点
    breakpoints: {
      current: 'lg',
      width: 1200,
      height: 800,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
    },

    // 性能监控
    performance: {
      renderTime: 0,
      loadTime: 0,
      memoryUsage: 0,
      fps: 60,
    },
  }),

  getters: {
    // 是否为暗色主题
    isDarkMode: (state) => {
      if (state.theme.mode === 'auto') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches
      }
      return state.theme.mode === 'dark'
    },

    // 当前主题配置
    currentTheme: (state) => {
      const isDark =
        state.theme.mode === 'dark' ||
        (state.theme.mode === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)

      return {
        ...state.theme,
        isDark,
        cssVars: {
          '--primary-color': state.theme.primaryColor,
          '--border-radius': `${state.theme.borderRadius}px`,
          '--font-size': `${state.theme.fontSize}px`,
          '--font-family': state.theme.fontFamily,
        },
      }
    },

    // 侧边栏实际宽度
    actualSidebarWidth: (state) => {
      return state.layout.sidebarCollapsed ? 64 : state.layout.sidebarWidth
    },

    // 内容区域样式
    contentAreaStyle: (state) => {
      const sidebarWidth = state.layout.sidebarCollapsed ? 64 : state.layout.sidebarWidth
      return {
        marginLeft: `${sidebarWidth}px`,
        paddingTop: `${state.layout.headerHeight}px`,
        paddingBottom: `${state.layout.footerHeight}px`,
        padding: `${state.layout.contentPadding}px`,
        minHeight: `calc(100vh - ${state.layout.headerHeight + state.layout.footerHeight}px)`,
      }
    },

    // 活跃的模态框数量
    activeModalsCount: (state) => {
      return state.modals.active.size
    },

    // 是否有模态框打开
    hasActiveModal: (state) => {
      return state.modals.active.size > 0
    },

    // 当前页面标签
    currentTab: (state) => {
      return state.pages.tabs.find((tab) => tab.path === state.pages.current.path)
    },

    // 格式化的面包屑
    formattedBreadcrumb: (state) => {
      return state.pages.breadcrumb.map((item) => ({
        ...item,
        clickable: !!item.path,
      }))
    },

    // 响应式类名
    responsiveClass: (state) => {
      const classes = [`breakpoint-${state.breakpoints.current}`]

      if (state.breakpoints.isMobile) classes.push('is-mobile')
      if (state.breakpoints.isTablet) classes.push('is-tablet')
      if (state.breakpoints.isDesktop) classes.push('is-desktop')

      return classes.join(' ')
    },
  },

  actions: {
    // ==================== 布局管理 ====================

    /**
     * 切换侧边栏折叠状态
     */
    toggleSidebar() {
      this.layout.sidebarCollapsed = !this.layout.sidebarCollapsed
      this.saveLayoutPreferences()
    },

    /**
     * 设置侧边栏状态
     */
    setSidebarCollapsed(collapsed) {
      this.layout.sidebarCollapsed = collapsed
      this.saveLayoutPreferences()
    },

    /**
     * 设置侧边栏宽度
     */
    setSidebarWidth(width) {
      this.layout.sidebarWidth = Math.max(200, Math.min(400, width))
      this.saveLayoutPreferences()
    },

    /**
     * 更新布局配置
     */
    updateLayout(config) {
      this.layout = { ...this.layout, ...config }
      this.saveLayoutPreferences()
    },

    // ==================== 主题管理 ====================

    /**
     * 设置主题模式
     */
    setThemeMode(mode) {
      this.theme.mode = mode
      this.applyTheme()
      this.saveThemePreferences()
    },

    /**
     * 设置主色调
     */
    setPrimaryColor(color) {
      this.theme.primaryColor = color
      this.applyTheme()
      this.saveThemePreferences()
    },

    /**
     * 更新主题配置
     */
    updateTheme(config) {
      this.theme = { ...this.theme, ...config }
      this.applyTheme()
      this.saveThemePreferences()
    },

    /**
     * 应用主题
     */
    applyTheme() {
      const theme = this.currentTheme
      const root = document.documentElement

      // 应用CSS变量
      Object.entries(theme.cssVars).forEach(([key, value]) => {
        root.style.setProperty(key, value)
      })

      // 设置主题类名
      root.className = root.className.replace(/theme-\w+/g, '')
      root.classList.add(`theme-${theme.isDark ? 'dark' : 'light'}`)
    },

    // ==================== 页面状态管理 ====================

    /**
     * 设置当前页面
     */
    setCurrentPage(pageInfo) {
      this.pages.current = { ...pageInfo }
      this.updatePageHistory(pageInfo)
      this.updateBreadcrumb(pageInfo)
    },

    /**
     * 更新页面历史
     */
    updatePageHistory(pageInfo) {
      const existingIndex = this.pages.history.findIndex((p) => p.path === pageInfo.path)

      if (existingIndex > -1) {
        this.pages.history.splice(existingIndex, 1)
      }

      this.pages.history.unshift(pageInfo)

      // 保持最多50条历史记录
      if (this.pages.history.length > 50) {
        this.pages.history = this.pages.history.slice(0, 50)
      }
    },

    /**
     * 更新面包屑
     */
    updateBreadcrumb(pageInfo) {
      // 根据路由meta信息生成面包屑
      const breadcrumb = []

      if (pageInfo.meta && pageInfo.meta.breadcrumb) {
        breadcrumb.push(...pageInfo.meta.breadcrumb)
      } else {
        // 默认根据路径生成
        const pathSegments = pageInfo.path.split('/').filter(Boolean)
        pathSegments.forEach((segment, index) => {
          breadcrumb.push({
            title: segment,
            path: '/' + pathSegments.slice(0, index + 1).join('/'),
          })
        })
      }

      this.pages.breadcrumb = breadcrumb
    },

    /**
     * 添加标签页
     */
    addTab(tab) {
      const existingIndex = this.pages.tabs.findIndex((t) => t.path === tab.path)

      if (existingIndex > -1) {
        this.pages.tabs[existingIndex] = { ...this.pages.tabs[existingIndex], ...tab }
      } else {
        this.pages.tabs.push({
          id: Date.now(),
          closable: true,
          ...tab,
        })
      }
    },

    /**
     * 关闭标签页
     */
    closeTab(path) {
      const index = this.pages.tabs.findIndex((t) => t.path === path)
      if (index > -1) {
        this.pages.tabs.splice(index, 1)
      }
    },

    /**
     * 关闭其他标签页
     */
    closeOtherTabs(path) {
      this.pages.tabs = this.pages.tabs.filter((t) => t.path === path || !t.closable)
    },

    /**
     * 关闭所有标签页
     */
    closeAllTabs() {
      this.pages.tabs = this.pages.tabs.filter((t) => !t.closable)
    },

    /**
     * 设置页面加载状态
     */
    setPageLoading(loading) {
      this.pages.loading = loading
    },

    /**
     * 设置页面错误
     */
    setPageError(error) {
      this.pages.error = error
    },

    // ==================== 模态框管理 ====================

    /**
     * 打开模态框
     */
    openModal(id, config = {}) {
      this.modals.active.add(id)
      this.modals.configs.set(id, config)

      if (config.mask !== false) {
        this.modals.globalMask = true
      }
    },

    /**
     * 关闭模态框
     */
    closeModal(id) {
      this.modals.active.delete(id)
      this.modals.configs.delete(id)

      if (this.modals.active.size === 0) {
        this.modals.globalMask = false
      }
    },

    /**
     * 关闭所有模态框
     */
    closeAllModals() {
      this.modals.active.clear()
      this.modals.configs.clear()
      this.modals.globalMask = false
    },

    /**
     * 打开抽屉
     */
    openDrawer(id, config = {}) {
      this.modals.drawers.set(id, { open: true, ...config })
    },

    /**
     * 关闭抽屉
     */
    closeDrawer(id) {
      const drawer = this.modals.drawers.get(id)
      if (drawer) {
        drawer.open = false
      }
    },

    // ==================== 表格状态管理 ====================

    /**
     * 设置表格配置
     */
    setTableConfig(tableId, config) {
      this.tables.configs.set(tableId, config)
    },

    /**
     * 设置表格列配置
     */
    setTableColumns(tableId, columns) {
      this.tables.columns.set(tableId, columns)
    },

    /**
     * 设置表格排序
     */
    setTableSorting(tableId, sorting) {
      this.tables.sorting.set(tableId, sorting)
    },

    /**
     * 设置表格过滤
     */
    setTableFilters(tableId, filters) {
      this.tables.filters.set(tableId, filters)
    },

    /**
     * 设置表格分页
     */
    setTablePagination(tableId, pagination) {
      this.tables.pagination.set(tableId, pagination)
    },

    /**
     * 设置表格选中行
     */
    setTableSelection(tableId, selection) {
      this.tables.selections.set(tableId, selection)
    },

    // ==================== 表单状态管理 ====================

    /**
     * 设置表单数据
     */
    setFormData(formId, data) {
      this.forms.data.set(formId, data)
      this.forms.dirty.add(formId)
    },

    /**
     * 设置表单验证状态
     */
    setFormValidation(formId, validation) {
      this.forms.validation.set(formId, validation)
    },

    /**
     * 设置表单配置
     */
    setFormConfig(formId, config) {
      this.forms.configs.set(formId, config)
    },

    /**
     * 设置表单提交状态
     */
    setFormSubmitting(formId, submitting) {
      if (submitting) {
        this.forms.submitting.add(formId)
      } else {
        this.forms.submitting.delete(formId)
      }
    },

    /**
     * 清除表单脏数据标记
     */
    clearFormDirty(formId) {
      this.forms.dirty.delete(formId)
    },

    /**
     * 重置表单状态
     */
    resetForm(formId) {
      this.forms.data.delete(formId)
      this.forms.validation.delete(formId)
      this.forms.submitting.delete(formId)
      this.forms.dirty.delete(formId)
    },

    // ==================== 通知管理 ====================

    /**
     * 添加消息
     */
    addMessage(message) {
      const msg = {
        id: Date.now() + Math.random(),
        timestamp: new Date(),
        ...message,
      }

      this.notifications.messages.unshift(msg)

      // 保持最多100条消息
      if (this.notifications.messages.length > 100) {
        this.notifications.messages = this.notifications.messages.slice(0, 100)
      }
    },

    /**
     * 添加通知
     */
    addNotification(notification) {
      const notif = {
        id: Date.now() + Math.random(),
        timestamp: new Date(),
        read: false,
        ...notification,
      }

      this.notifications.notifications.unshift(notif)

      // 保持最多50条通知
      if (this.notifications.notifications.length > 50) {
        this.notifications.notifications = this.notifications.notifications.slice(0, 50)
      }
    },

    /**
     * 标记通知为已读
     */
    markNotificationRead(id) {
      const notification = this.notifications.notifications.find((n) => n.id === id)
      if (notification) {
        notification.read = true
      }
    },

    /**
     * 标记所有通知为已读
     */
    markAllNotificationsRead() {
      this.notifications.notifications.forEach((n) => {
        n.read = true
      })
    },

    /**
     * 清除通知
     */
    clearNotification(id) {
      const index = this.notifications.notifications.findIndex((n) => n.id === id)
      if (index > -1) {
        this.notifications.notifications.splice(index, 1)
      }
    },

    // ==================== 偏好设置管理 ====================

    /**
     * 更新用户偏好
     */
    updatePreferences(preferences) {
      this.preferences = { ...this.preferences, ...preferences }
      this.saveUserPreferences()
    },

    /**
     * 设置语言
     */
    setLanguage(language) {
      this.preferences.language = language
      this.saveUserPreferences()
    },

    /**
     * 设置时区
     */
    setTimezone(timezone) {
      this.preferences.timezone = timezone
      this.saveUserPreferences()
    },

    // ==================== 响应式断点管理 ====================

    /**
     * 更新断点信息
     */
    updateBreakpoints(width, height) {
      this.breakpoints.width = width
      this.breakpoints.height = height

      // 确定当前断点
      if (width < 576) {
        this.breakpoints.current = 'xs'
        this.breakpoints.isMobile = true
        this.breakpoints.isTablet = false
        this.breakpoints.isDesktop = false
      } else if (width < 768) {
        this.breakpoints.current = 'sm'
        this.breakpoints.isMobile = true
        this.breakpoints.isTablet = false
        this.breakpoints.isDesktop = false
      } else if (width < 992) {
        this.breakpoints.current = 'md'
        this.breakpoints.isMobile = false
        this.breakpoints.isTablet = true
        this.breakpoints.isDesktop = false
      } else if (width < 1200) {
        this.breakpoints.current = 'lg'
        this.breakpoints.isMobile = false
        this.breakpoints.isTablet = false
        this.breakpoints.isDesktop = true
      } else {
        this.breakpoints.current = 'xl'
        this.breakpoints.isMobile = false
        this.breakpoints.isTablet = false
        this.breakpoints.isDesktop = true
      }
    },

    // ==================== 性能监控 ====================

    /**
     * 更新性能指标
     */
    updatePerformance(metrics) {
      this.performance = { ...this.performance, ...metrics }
    },

    // ==================== 数据持久化 ====================

    /**
     * 保存布局偏好
     */
    saveLayoutPreferences() {
      try {
        localStorage.setItem('ui-layout-preferences', JSON.stringify(this.layout))
      } catch (error) {
        console.warn('保存布局偏好失败:', error)
      }
    },

    /**
     * 保存主题偏好
     */
    saveThemePreferences() {
      try {
        localStorage.setItem('ui-theme-preferences', JSON.stringify(this.theme))
      } catch (error) {
        console.warn('保存主题偏好失败:', error)
      }
    },

    /**
     * 保存用户偏好
     */
    saveUserPreferences() {
      try {
        localStorage.setItem('ui-user-preferences', JSON.stringify(this.preferences))
      } catch (error) {
        console.warn('保存用户偏好失败:', error)
      }
    },

    /**
     * 加载偏好设置
     */
    loadPreferences() {
      try {
        // 加载布局偏好
        const layoutPrefs = localStorage.getItem('ui-layout-preferences')
        if (layoutPrefs) {
          this.layout = { ...this.layout, ...JSON.parse(layoutPrefs) }
        }

        // 加载主题偏好
        const themePrefs = localStorage.getItem('ui-theme-preferences')
        if (themePrefs) {
          this.theme = { ...this.theme, ...JSON.parse(themePrefs) }
        }

        // 加载用户偏好
        const userPrefs = localStorage.getItem('ui-user-preferences')
        if (userPrefs) {
          this.preferences = { ...this.preferences, ...JSON.parse(userPrefs) }
        }

        // 应用主题
        this.applyTheme()
      } catch (error) {
        console.warn('加载偏好设置失败:', error)
      }
    },

    /**
     * 重置所有偏好设置
     */
    resetPreferences() {
      try {
        localStorage.removeItem('ui-layout-preferences')
        localStorage.removeItem('ui-theme-preferences')
        localStorage.removeItem('ui-user-preferences')

        // 重置到默认值
        this.$reset()
        this.applyTheme()
      } catch (error) {
        console.warn('重置偏好设置失败:', error)
      }
    },
  },
})

export default useUIStateStore
