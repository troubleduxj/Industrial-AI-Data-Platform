/**
 * DOM操作安全工具函数
 * 用于防止Vue组件中常见的DOM操作错误，特别是parentNode相关错误
 */

import { nextTick } from 'vue'

/**
 * 安全的DOM元素检查
 * @param {Element|null} element - 要检查的DOM元素
 * @returns {boolean} 元素是否有效且已挂载
 */
export function isElementSafe(element) {
  return (
    element &&
    element.nodeType === Node.ELEMENT_NODE &&
    element.parentNode &&
    document.contains(element)
  )
}

/**
 * 安全的parentNode访问
 * @param {Element|null} element - 要访问parentNode的元素
 * @returns {Element|null} 安全的parentNode或null
 */
export function safeParentNode(element) {
  try {
    if (!element || !element.parentNode) {
      return null
    }
    return element.parentNode
  } catch (error) {
    console.warn('访问parentNode失败:', error)
    return null
  }
}

/**
 * 安全的DOM操作执行器
 * @param {Function} operation - 要执行的DOM操作函数
 * @param {Object} options - 配置选项
 * @param {boolean} options.useNextTick - 是否使用nextTick
 * @param {string} options.errorMessage - 自定义错误消息
 * @returns {Promise<any>} 操作结果
 */
export async function safeDOMOperation(operation, options = {}) {
  const { useNextTick = true, errorMessage = 'DOM操作失败' } = options

  try {
    if (useNextTick) {
      await nextTick()
    }

    return await operation()
  } catch (error) {
    console.error(`${errorMessage}:`, error)
    return null
  }
}

/**
 * 安全的元素查询
 * @param {string} selector - CSS选择器
 * @param {Element} container - 容器元素，默认为document
 * @returns {Element|null} 查询到的元素或null
 */
export function safeQuerySelector(selector, container = document) {
  try {
    if (!container || !selector) {
      return null
    }
    return container.querySelector(selector)
  } catch (error) {
    console.warn('元素查询失败:', error)
    return null
  }
}

/**
 * 安全的元素列表查询
 * @param {string} selector - CSS选择器
 * @param {Element} container - 容器元素，默认为document
 * @returns {NodeList|Array} 查询到的元素列表
 */
export function safeQuerySelectorAll(selector, container = document) {
  try {
    if (!container || !selector) {
      return []
    }
    return Array.from(container.querySelectorAll(selector))
  } catch (error) {
    console.warn('元素列表查询失败:', error)
    return []
  }
}

/**
 * 安全的事件监听器添加
 * @param {Element} element - 目标元素
 * @param {string} event - 事件名称
 * @param {Function} handler - 事件处理函数
 * @param {Object} options - 事件选项
 * @returns {Function|null} 移除监听器的函数
 */
export function safeAddEventListener(element, event, handler, options = {}) {
  try {
    if (!isElementSafe(element) || !event || typeof handler !== 'function') {
      return null
    }

    element.addEventListener(event, handler, options)

    // 返回移除监听器的函数
    return () => {
      try {
        if (isElementSafe(element)) {
          element.removeEventListener(event, handler, options)
        }
      } catch (error) {
        console.warn('移除事件监听器失败:', error)
      }
    }
  } catch (error) {
    console.error('添加事件监听器失败:', error)
    return null
  }
}

/**
 * 安全的样式设置
 * @param {Element} element - 目标元素
 * @param {Object} styles - 样式对象
 */
export function safeSetStyles(element, styles) {
  try {
    if (!isElementSafe(element) || !styles || typeof styles !== 'object') {
      return
    }

    Object.entries(styles).forEach(([property, value]) => {
      try {
        element.style[property] = value
      } catch (error) {
        console.warn(`设置样式 ${property} 失败:`, error)
      }
    })
  } catch (error) {
    console.error('设置样式失败:', error)
  }
}

/**
 * 安全的类名操作
 * @param {Element} element - 目标元素
 * @param {string} className - 类名
 * @param {string} action - 操作类型：'add', 'remove', 'toggle', 'contains'
 * @returns {boolean|void} 对于contains操作返回boolean，其他返回void
 */
export function safeClassOperation(element, className, action) {
  try {
    if (!isElementSafe(element) || !className || !action) {
      return action === 'contains' ? false : undefined
    }

    switch (action) {
      case 'add':
        element.classList.add(className)
        break
      case 'remove':
        element.classList.remove(className)
        break
      case 'toggle':
        element.classList.toggle(className)
        break
      case 'contains':
        return element.classList.contains(className)
      default:
        console.warn('未知的类名操作:', action)
    }
  } catch (error) {
    console.error('类名操作失败:', error)
    return action === 'contains' ? false : undefined
  }
}

/**
 * 安全的滚动操作
 * @param {Element} element - 目标元素
 * @param {Object} options - 滚动选项
 */
export function safeScrollTo(element, options = {}) {
  try {
    if (!element) {
      element = document.documentElement || document.body
    }

    if (!isElementSafe(element)) {
      return
    }

    const defaultOptions = {
      top: 0,
      left: 0,
      behavior: 'smooth',
    }

    element.scrollTo({ ...defaultOptions, ...options })
  } catch (error) {
    console.error('滚动操作失败:', error)
  }
}

/**
 * Vue组件安全挂载检查
 * @param {Object} componentInstance - Vue组件实例
 * @returns {boolean} 组件是否安全挂载
 */
export function isComponentSafeMounted(componentInstance) {
  try {
    return componentInstance && componentInstance.$el && isElementSafe(componentInstance.$el)
  } catch (error) {
    console.warn('组件挂载状态检查失败:', error)
    return false
  }
}

/**
 * 创建安全的DOM操作上下文
 * @param {Object} options - 配置选项
 * @returns {Object} DOM操作上下文对象
 */
export function createSafeDOMContext(options = {}) {
  const { errorHandler = console.error } = options

  return {
    isElementSafe,
    safeParentNode,
    safeDOMOperation,
    safeQuerySelector,
    safeQuerySelectorAll,
    safeAddEventListener,
    safeSetStyles,
    safeClassOperation,
    safeScrollTo,
    isComponentSafeMounted,

    // 包装函数，自动处理错误
    wrap: (operation) => {
      return async (...args) => {
        try {
          return await operation(...args)
        } catch (error) {
          errorHandler('DOM操作错误:', error)
          return null
        }
      }
    },
  }
}

// 默认导出安全DOM操作上下文
export default createSafeDOMContext()
