// Layout组件导出文件
import type { Component } from 'vue'
import MainLayout from './MainLayout.vue'
import SidebarLayout from './SidebarLayout.vue'
import LeftToolbar from './LeftToolbar.vue'
import WorkflowHeader from './WorkflowHeader.vue'
import RightSidebar from './RightSidebar.vue'

// 导出所有布局组件
export { MainLayout, SidebarLayout, LeftToolbar, WorkflowHeader, RightSidebar }

// 默认导出主布局
export default MainLayout

// ==================== 类型定义 ====================

/** 布局配置属性 */
interface LayoutProps {
  showHeader?: boolean
  showFooter?: boolean
  showLeftSidebar?: boolean
  showRightSidebar?: boolean
  showMiniMap?: boolean
  defaultLeftSidebarWidth?: number
  defaultRightSidebarWidth?: number
  minSidebarWidth?: number
  maxSidebarWidth?: number
}

/** 侧边栏配置属性 */
interface SidebarProps {
  showHeader?: boolean
  showActions?: boolean
  collapsible?: boolean
  closable?: boolean
  resizable?: boolean
  searchable?: boolean
  width?: number
  minWidth?: number
  maxWidth?: number
}

/** 布局配置项 */
interface LayoutConfig {
  name: string
  component: Component
  props: LayoutProps | SidebarProps
}

/** 主题颜色配置 */
interface ThemeColors {
  background: string
  surface: string
  text: string
  textSecondary: string
  border: string
  primary: string
  hover: string
  active: string
}

/** 主题配置 */
interface ThemeConfig {
  name: string
  label: string
  colors: ThemeColors
}

/** 布局模式配置 */
interface LayoutMode {
  name: string
  label: string
  description: string
}

/** 侧边栏位置配置 */
interface SidebarPosition {
  name: string
  label: string
  icon: string
}

/** 布局状态 */
export interface LayoutState {
  theme: string
  mode: string
  showHeader: boolean
  showFooter: boolean
  showLeftSidebar: boolean
  showRightSidebar: boolean
  showMiniMap: boolean
  leftSidebarWidth: number
  rightSidebarWidth: number
  leftSidebarCollapsed: boolean
  rightSidebarCollapsed: boolean
  activeLeftTab: string
  activeRightTab: string
}

/** 断点类型 */
type Breakpoint = 'mobile' | 'tablet' | 'desktop' | 'large'

// ==================== 配置常量 ====================

/** 布局配置 */
export const LAYOUT_CONFIGS: Record<string, LayoutConfig> = {
  // 主布局配置
  main: {
    name: 'MainLayout',
    component: MainLayout,
    props: {
      showHeader: true,
      showFooter: true,
      showLeftSidebar: true,
      showRightSidebar: true,
      showMiniMap: true,
      defaultLeftSidebarWidth: 280,
      defaultRightSidebarWidth: 320,
      minSidebarWidth: 200,
      maxSidebarWidth: 500,
    },
  },

  // 侧边栏配置
  sidebar: {
    name: 'SidebarLayout',
    component: SidebarLayout,
    props: {
      showHeader: true,
      showActions: true,
      collapsible: true,
      closable: false,
      resizable: true,
      searchable: false,
      width: 280,
      minWidth: 200,
      maxWidth: 500,
    },
  },
}

/** 布局主题 */
export const LAYOUT_THEMES: Record<string, ThemeConfig> = {
  light: {
    name: 'light',
    label: '浅色主题',
    colors: {
      background: '#f5f5f5',
      surface: '#ffffff',
      text: '#333333',
      textSecondary: '#666666',
      border: '#e0e0e0',
      primary: '#1976d2',
      hover: '#f5f5f5',
      active: '#e3f2fd',
    },
  },

  dark: {
    name: 'dark',
    label: '深色主题',
    colors: {
      background: '#1e1e1e',
      surface: '#252526',
      text: '#ffffff',
      textSecondary: '#cccccc',
      border: '#404040',
      primary: '#4fc3f7',
      hover: '#2a2d2e',
      active: '#094771',
    },
  },
}

/** 布局模式 */
export const LAYOUT_MODES: Record<string, LayoutMode> = {
  normal: {
    name: 'normal',
    label: '普通模式',
    description: '标准的工作流设计界面',
  },

  compact: {
    name: 'compact',
    label: '紧凑模式',
    description: '更紧凑的界面布局，适合小屏幕',
  },

  fullscreen: {
    name: 'fullscreen',
    label: '全屏模式',
    description: '全屏显示，隐藏头部和底部',
  },
}

/** 侧边栏位置 */
export const SIDEBAR_POSITIONS: Record<string, SidebarPosition> = {
  left: {
    name: 'left',
    label: '左侧',
    icon: 'sidebar-left',
  },

  right: {
    name: 'right',
    label: '右侧',
    icon: 'sidebar-right',
  },
}

// ==================== 工具函数 ====================

/** 布局工具函数 */
export const layoutUtils = {
  /**
   * 获取布局配置
   * @param layoutName - 布局名称
   * @returns 布局配置
   */
  getLayoutConfig(layoutName: string): LayoutConfig {
    return LAYOUT_CONFIGS[layoutName] || LAYOUT_CONFIGS.main
  },

  /**
   * 获取主题配置
   * @param themeName - 主题名称
   * @returns 主题配置
   */
  getThemeConfig(themeName: string): ThemeConfig {
    return LAYOUT_THEMES[themeName] || LAYOUT_THEMES.light
  },

  /**
   * 获取布局模式配置
   * @param modeName - 模式名称
   * @returns 模式配置
   */
  getModeConfig(modeName: string): LayoutMode {
    return LAYOUT_MODES[modeName] || LAYOUT_MODES.normal
  },

  /**
   * 应用主题到CSS变量
   * @param themeName - 主题名称
   * @param element - 目标元素
   */
  applyTheme(themeName: string, element: HTMLElement = document.documentElement): void {
    const theme = this.getThemeConfig(themeName)
    if (theme && theme.colors) {
      Object.entries(theme.colors).forEach(([key, value]) => {
        element.style.setProperty(`--${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`, value)
      })
    }
  },

  /**
   * 计算侧边栏宽度
   * @param currentWidth - 当前宽度
   * @param delta - 变化量
   * @param minWidth - 最小宽度
   * @param maxWidth - 最大宽度
   * @returns 新宽度
   */
  calculateSidebarWidth(
    currentWidth: number,
    delta: number,
    minWidth: number = 200,
    maxWidth: number = 500
  ): number {
    const newWidth = currentWidth + delta
    return Math.max(minWidth, Math.min(maxWidth, newWidth))
  },

  /**
   * 获取响应式断点
   * @param width - 屏幕宽度
   * @returns 断点名称
   */
  getBreakpoint(width: number): Breakpoint {
    if (width < 768) return 'mobile'
    if (width < 1024) return 'tablet'
    if (width < 1440) return 'desktop'
    return 'large'
  },

  /**
   * 检查是否为移动设备
   * @returns 是否为移动设备
   */
  isMobile(): boolean {
    return window.innerWidth < 768
  },

  /**
   * 保存布局状态到本地存储
   * @param key - 存储键
   * @param state - 布局状态
   */
  saveLayoutState(key: string, state: Partial<LayoutState>): void {
    try {
      localStorage.setItem(`workflow-layout-${key}`, JSON.stringify(state))
    } catch (error) {
      console.warn('Failed to save layout state:', error)
    }
  },

  /**
   * 从本地存储加载布局状态
   * @param key - 存储键
   * @param defaultState - 默认状态
   * @returns 布局状态
   */
  loadLayoutState<T extends Record<string, any>>(key: string, defaultState: T = {} as T): T {
    try {
      const saved = localStorage.getItem(`workflow-layout-${key}`)
      return saved ? { ...defaultState, ...JSON.parse(saved) } : defaultState
    } catch (error) {
      console.warn('Failed to load layout state:', error)
      return defaultState
    }
  },

  /**
   * 清除布局状态
   * @param key - 存储键
   */
  clearLayoutState(key: string): void {
    try {
      localStorage.removeItem(`workflow-layout-${key}`)
    } catch (error) {
      console.warn('Failed to clear layout state:', error)
    }
  },
}

// ==================== 事件常量 ====================

/** 布局事件常量 */
export const LAYOUT_EVENTS = {
  // 主布局事件
  SAVE: 'save',
  RUN: 'run',
  STOP: 'stop',
  EXPORT: 'export',
  IMPORT: 'import',
  UNDO: 'undo',
  REDO: 'redo',
  ZOOM_IN: 'zoom-in',
  ZOOM_OUT: 'zoom-out',
  ZOOM_FIT: 'zoom-fit',
  ZOOM_RESET: 'zoom-reset',
  NODE_DRAG_START: 'node-drag-start',
  PROPERTY_CHANGE: 'property-change',
  VIEWPORT_CHANGE: 'viewport-change',

  // 侧边栏事件
  SIDEBAR_TOGGLE: 'sidebar-toggle',
  SIDEBAR_CLOSE: 'sidebar-close',
  SIDEBAR_RESIZE: 'sidebar-resize',
  TAB_CHANGE: 'tab-change',
  SEARCH: 'search',

  // 布局事件
  LAYOUT_CHANGE: 'layout-change',
  THEME_CHANGE: 'theme-change',
  MODE_CHANGE: 'mode-change',
} as const

/** 布局事件类型 */
export type LayoutEventType = (typeof LAYOUT_EVENTS)[keyof typeof LAYOUT_EVENTS]

// ==================== 默认状态 ====================

/** 默认布局状态 */
export const DEFAULT_LAYOUT_STATE: LayoutState = {
  theme: 'light',
  mode: 'normal',
  showHeader: true,
  showFooter: true,
  showLeftSidebar: true,
  showRightSidebar: true,
  showMiniMap: true,
  leftSidebarWidth: 280,
  rightSidebarWidth: 320,
  leftSidebarCollapsed: false,
  rightSidebarCollapsed: false,
  activeLeftTab: '',
  activeRightTab: '',
}

