/**
 * 通用组件类型定义
 * 提供TypeScript类型支持
 */

// 视图切换选项类型
export interface ViewToggleOption {
  value: string
  label: string
  icon: string
}

// 加载状态包装器属性类型
export interface LoadingEmptyWrapperProps {
  loading?: boolean
  empty?: boolean
  loadingSize?: 'small' | 'medium' | 'large'
  loadingText?: string
  emptyDescription?: string
  iconClass?: string
  showNetworkReload?: boolean
  overlayClass?: string
  minHeight?: string | number
}

// 水平滚动组件属性类型
export interface ScrollXProps {
  showArrows?: boolean
  showIndicator?: boolean
  scrollStep?: number
  arrowSize?: number
  showLeftArrow?: boolean
  showRightArrow?: boolean
  scrollDuration?: number
  smoothScroll?: boolean
}

// 权限按钮属性类型
export interface PermissionButtonProps {
  permission?: string | string[]
  resource?: string
  action?: string
  roles?: string | string[]
  permissionMode?: 'any' | 'all'
  hideWhenNoPermission?: boolean
  disableWhenNoPermission?: boolean
  type?: string
  size?: string
  loading?: boolean
  disabled?: boolean
  ghost?: boolean
  dashed?: boolean
  round?: boolean
  circle?: boolean
}

// 视图切换组件属性类型
export interface ViewToggleProps {
  modelValue: string
  options: ViewToggleOption[]
  size?: 'tiny' | 'small' | 'medium' | 'large'
  showLabel?: boolean
  iconSize?: number
  disabled?: boolean
  align?: 'left' | 'center' | 'right'
  compact?: boolean
}

// 滚动事件类型
export interface ScrollEvent {
  translateX: number
  canScrollLeft: boolean
  canScrollRight: boolean
}

// 组件事件类型
export interface CommonComponentEvents {
  // LoadingEmptyWrapper 事件
  'loading-empty-wrapper': {
    reload: () => void
    retry: () => void
  }
  
  // ScrollX 事件
  'scroll-x': {
    scroll: (event: ScrollEvent) => void
    'scroll-start': (direction: 'left' | 'right') => void
    'scroll-end': () => void
  }
  
  // ViewToggle 事件
  'view-toggle': {
    'update:modelValue': (value: string) => void
    change: (value: string) => void
  }
  
  // PermissionButton 事件
  'permission-button': {
    click: (event: MouseEvent) => void
  }
}

// 组件实例类型
export interface ScrollXInstance {
  scrollTo: (targetX: number, smooth?: boolean) => void
  scrollLeft: () => void
  scrollRight: () => void
  scrollToElement: (element: HTMLElement, offset?: number) => void
  checkOverflow: () => void
  reset: () => void
}

// 页面类型枚举
export type PageType = 
  | 'device-monitor'
  | 'device-management'
  | 'statistics'
  | 'file-management'
  | 'calendar'
  | 'map'
  | 'default'

// 组件尺寸类型
export type ComponentSize = 'tiny' | 'small' | 'medium' | 'large'

// 组件状态类型
export type ComponentStatus = 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'

// 对齐方式类型
export type AlignType = 'left' | 'center' | 'right'

// 权限模式类型
export type PermissionMode = 'any' | 'all'