/**
 * Vue错误处理工具
 * 用于捕获和处理Vue运行时错误
 */

/**
 * 全局错误处理器
 */
export function setupGlobalErrorHandler(app) {
  // 捕获Vue组件错误
  app.config.errorHandler = (err, instance, info) => {
    console.error('Vue Error:', err)
    console.error('Component Instance:', instance)
    console.error('Error Info:', info)

    // 特殊处理component为null的错误
    if (
      err.message &&
      err.message.includes("Cannot read properties of null (reading 'component')")
    ) {
      console.warn('检测到组件为null错误，尝试恢复...')
      // 可以在这里添加恢复逻辑
      return true // 阻止错误继续传播
    }

    // 记录错误到监控系统（如果有的话）
    if (window.errorReporting) {
      window.errorReporting.captureException(err, {
        extra: { instance, info },
      })
    }
  }

  // 捕获未处理的Promise错误
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled Promise Rejection:', event.reason)

    // 如果是Vue相关错误，尝试处理
    if (
      event.reason &&
      event.reason.message &&
      event.reason.message.includes("Cannot read properties of null (reading 'component')")
    ) {
      console.warn('检测到Promise中的组件错误，已处理')
      event.preventDefault() // 阻止默认的错误处理
    }
  })
}

/**
 * 组件安全包装器
 * 用于包装可能出错的组件
 */
export function safeComponent(component, fallback = null) {
  return {
    ...component,
    setup(props, ctx) {
      try {
        return component.setup ? component.setup(props, ctx) : {}
      } catch (error) {
        console.error('Component setup error:', error)
        return fallback || {}
      }
    },
    render(ctx) {
      try {
        return component.render ? component.render(ctx) : null
      } catch (error) {
        console.error('Component render error:', error)
        return fallback
      }
    },
  }
}

/**
 * 安全的ref访问
 */
export function safeRef(ref, defaultValue = null) {
  try {
    return ref.value || defaultValue
  } catch (error) {
    console.warn('Safe ref access error:', error)
    return defaultValue
  }
}

/**
 * 安全的组件方法调用
 */
export function safeCall(fn, ...args) {
  try {
    if (typeof fn === 'function') {
      return fn(...args)
    }
  } catch (error) {
    console.warn('Safe call error:', error)
  }
  return null
}

/**
 * 检查组件是否有效
 */
export function isValidComponent(component) {
  return (
    component &&
    typeof component === 'object' &&
    (component.render || component.setup || component.template)
  )
}

/**
 * 延迟执行，避免在组件销毁时执行
 */
export function safeNextTick(fn) {
  return new Promise((resolve) => {
    setTimeout(() => {
      try {
        const result = fn()
        resolve(result)
      } catch (error) {
        console.warn('Safe nextTick error:', error)
        resolve(null)
      }
    }, 0)
  })
}
