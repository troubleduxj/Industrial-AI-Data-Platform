/**
 * 交互组件统一导出
 * 提供统一的交互状态和动画组件
 */

// 交互状态组件
export { default as LoadingState } from './LoadingState.vue'
export { default as TransitionWrapper } from './TransitionWrapper.vue'
export { default as FeedbackToast } from './FeedbackToast.vue'

// 异步导出 - 用于懒加载
export default {
  LoadingState: () => import('./LoadingState.vue'),
  TransitionWrapper: () => import('./TransitionWrapper.vue'),
  FeedbackToast: () => import('./FeedbackToast.vue')
}

// 组件类型定义（用于TypeScript支持）
export interface InteractionComponentsMap {
  LoadingState: typeof import('./LoadingState.vue').default
  TransitionWrapper: typeof import('./TransitionWrapper.vue').default
  FeedbackToast: typeof import('./FeedbackToast.vue').default
}

// 组件安装函数（用于全局注册）
export function installInteractionComponents(app) {
  const components = {
    LoadingState: () => import('./LoadingState.vue'),
    TransitionWrapper: () => import('./TransitionWrapper.vue'),
    FeedbackToast: () => import('./FeedbackToast.vue')
  }
  
  Object.entries(components).forEach(([name, component]) => {
    app.component(name, component)
  })
}

// 交互配置常量
export const INTERACTION_CONFIG = {
  // 默认动画持续时间
  durations: {
    fast: 150,
    normal: 300,
    slow: 500
  },
  
  // 缓动函数
  easings: {
    ease: 'ease',
    easeIn: 'ease-in',
    easeOut: 'ease-out',
    easeInOut: 'ease-in-out',
    linear: 'linear',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    elastic: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)'
  },
  
  // 加载状态配置
  loading: {
    defaultType: 'spinner',
    defaultSize: 'medium',
    defaultText: '加载中...'
  },
  
  // Toast配置
  toast: {
    defaultPosition: 'top-right',
    defaultDuration: 3000,
    maxCount: 5
  },
  
  // 过渡动画配置
  transitions: {
    default: 'fade',
    page: 'slide-left',
    modal: 'scale',
    dropdown: 'slide-down'
  }
}

// 交互工具函数
export const interactionUtils = {
  /**
   * 格式化持续时间
   * @param {number|string} duration - 持续时间
   * @returns {number} 毫秒数
   */
  formatDuration(duration) {
    if (typeof duration === 'string') {
      return INTERACTION_CONFIG.durations[duration] || 300
    }
    return duration
  },
  
  /**
   * 获取缓动函数
   * @param {string} easing - 缓动函数名称
   * @returns {string} CSS缓动函数
   */
  getEasing(easing) {
    return INTERACTION_CONFIG.easings[easing] || easing
  },
  
  /**
   * 创建延迟Promise
   * @param {number} ms - 延迟毫秒数
   * @returns {Promise} 延迟Promise
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  },
  
  /**
   * 防抖函数
   * @param {Function} func - 要防抖的函数
   * @param {number} wait - 等待时间
   * @returns {Function} 防抖后的函数
   */
  debounce(func, wait) {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  },
  
  /**
   * 节流函数
   * @param {Function} func - 要节流的函数
   * @param {number} limit - 限制时间
   * @returns {Function} 节流后的函数
   */
  throttle(func, limit) {
    let inThrottle
    return function executedFunction(...args) {
      if (!inThrottle) {
        func.apply(this, args)
        inThrottle = true
        setTimeout(() => inThrottle = false, limit)
      }
    }
  }
}