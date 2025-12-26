/**
 * 统一错误处理中心
 * 提供集中化的错误处理、分类和用户提示
 */

import { useUserStore } from '@/store'
import { clearAuthStateEnhanced } from '@/utils/auth-enhanced'

// 错误分类
export const ERROR_CATEGORIES = {
  AUTHENTICATION: 'AUTHENTICATION',
  AUTHORIZATION: 'AUTHORIZATION',
  VALIDATION: 'VALIDATION',
  NETWORK: 'NETWORK',
  SERVER: 'SERVER',
  BUSINESS: 'BUSINESS',
  UNKNOWN: 'UNKNOWN',
}

// 错误严重程度
export const ERROR_SEVERITY = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL',
}

// 用户提示类型
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
}

/**
 * 错误处理中心类
 */
export class ErrorCenter {
  constructor() {
    this.errorHistory = []
    this.errorHandlers = new Map()
    this.globalErrorHandler = null
    this.maxHistorySize = 100

    // 注册默认错误处理器
    this.registerDefaultHandlers()
  }

  /**
   * 注册默认错误处理器
   */
  registerDefaultHandlers() {
    // 认证错误处理器
    this.registerHandler(ERROR_CATEGORIES.AUTHENTICATION, async (error) => {
      console.warn('[ErrorCenter] 认证错误:', error.message)

      try {
        const userStore = useUserStore()

        // 检查是否正在登出
        if (userStore.isLoggingOut) {
          return { handled: true, action: 'skip' }
        }

        // 检查错误详情，决定是否自动登出
        const shouldLogout = this.shouldAutoLogout(error)

        if (shouldLogout) {
          await userStore.logout()
          this.showNotification('登录已过期，请重新登录', NOTIFICATION_TYPES.WARNING)
          return { handled: true, action: 'logout' }
        } else {
          this.showNotification('认证失败，请检查权限', NOTIFICATION_TYPES.WARNING)
          return { handled: true, action: 'notify' }
        }
      } catch (logoutError) {
        console.error('[ErrorCenter] 自动登出失败:', logoutError)
        this.showNotification('系统错误，请刷新页面', NOTIFICATION_TYPES.ERROR)
        return { handled: false, error: logoutError }
      }
    })

    // 权限错误处理器
    this.registerHandler(ERROR_CATEGORIES.AUTHORIZATION, (error) => {
      console.warn('[ErrorCenter] 权限错误:', error.message)

      const message = this.getPermissionErrorMessage(error)
      this.showNotification(message, NOTIFICATION_TYPES.WARNING, {
        keepAliveOnHover: true,
        duration: 5000,
      })

      return { handled: true, action: 'notify' }
    })

    // 验证错误处理器
    this.registerHandler(ERROR_CATEGORIES.VALIDATION, (error) => {
      console.warn('[ErrorCenter] 验证错误:', error.message)

      // 处理字段验证错误
      if (error.details && error.details.validation_errors) {
        this.handleValidationErrors(error.details.validation_errors)
      } else {
        this.showNotification(error.message || '数据验证失败', NOTIFICATION_TYPES.WARNING)
      }

      return { handled: true, action: 'notify' }
    })

    // 网络错误处理器
    this.registerHandler(ERROR_CATEGORIES.NETWORK, (error) => {
      console.error('[ErrorCenter] 网络错误:', error.message)

      const message = this.getNetworkErrorMessage(error)
      this.showNotification(message, NOTIFICATION_TYPES.ERROR, {
        duration: 5000,
        keepAliveOnHover: true,
      })

      return { handled: true, action: 'notify' }
    })

    // 服务器错误处理器
    this.registerHandler(ERROR_CATEGORIES.SERVER, (error) => {
      console.error('[ErrorCenter] 服务器错误:', error.message)

      const message = this.getServerErrorMessage(error)
      this.showNotification(message, NOTIFICATION_TYPES.ERROR, {
        keepAliveOnHover: true,
      })

      return { handled: true, action: 'notify' }
    })

    // 业务错误处理器
    this.registerHandler(ERROR_CATEGORIES.BUSINESS, (error) => {
      console.warn('[ErrorCenter] 业务错误:', error.message)

      this.showNotification(error.message || '操作失败', NOTIFICATION_TYPES.WARNING, {
        keepAliveOnHover: true,
      })

      return { handled: true, action: 'notify' }
    })
  }

  /**
   * 注册错误处理器
   */
  registerHandler(category, handler) {
    this.errorHandlers.set(category, handler)
  }

  /**
   * 设置全局错误处理器
   */
  setGlobalHandler(handler) {
    this.globalErrorHandler = handler
  }

  /**
   * 处理错误
   */
  async handleError(error, context = {}) {
    try {
      // 标准化错误对象
      const normalizedError = this.normalizeError(error, context)

      // 记录错误历史
      this.recordError(normalizedError)

      // 获取错误分类
      const category = this.categorizeError(normalizedError)

      // 获取对应的处理器
      const handler = this.errorHandlers.get(category)

      if (handler) {
        const result = await handler(normalizedError)

        if (result.handled) {
          return result
        }
      }

      // 如果没有特定处理器或处理失败，使用全局处理器
      if (this.globalErrorHandler) {
        return await this.globalErrorHandler(normalizedError)
      }

      // 最后的兜底处理
      return this.handleUnknownError(normalizedError)
    } catch (handlerError) {
      console.error('[ErrorCenter] 错误处理器失败:', handlerError)

      // 兜底处理
      this.showNotification('系统错误，请联系管理员', NOTIFICATION_TYPES.ERROR)

      return {
        handled: false,
        error: handlerError,
        originalError: error,
      }
    }
  }

  /**
   * 标准化错误对象
   */
  normalizeError(error, context = {}) {
    // 如果已经是标准化的错误对象
    if (error && error.category && error.severity) {
      return error
    }

    const normalized = {
      id: this.generateErrorId(),
      timestamp: new Date().toISOString(),
      message: '',
      code: null,
      category: ERROR_CATEGORIES.UNKNOWN,
      severity: ERROR_SEVERITY.MEDIUM,
      details: null,
      context,
      originalError: error,
    }

    // 处理不同类型的错误
    if (error && error.response) {
      // HTTP响应错误
      const { status, data } = error.response
      normalized.code = data?.code || status
      normalized.message = data?.message || this.getDefaultHttpMessage(status)
      normalized.details = data?.details || data
      normalized.category = this.getHttpErrorCategory(status)
      normalized.severity = this.getHttpErrorSeverity(status)
    } else if (error && error.code && !error.response) {
      // 网络错误
      normalized.code = error.code
      normalized.message = error.message || '网络连接失败'
      normalized.category = ERROR_CATEGORIES.NETWORK
      normalized.severity = ERROR_SEVERITY.HIGH
    } else if (error instanceof Error) {
      // JavaScript错误
      normalized.message = error.message
      normalized.code = error.name
      normalized.category = ERROR_CATEGORIES.UNKNOWN
      normalized.severity = ERROR_SEVERITY.MEDIUM
    } else if (typeof error === 'string') {
      // 字符串错误
      normalized.message = error
      normalized.category = ERROR_CATEGORIES.UNKNOWN
      normalized.severity = ERROR_SEVERITY.LOW
    } else if (error && typeof error === 'object') {
      // 对象错误
      normalized.message = error.message || '未知错误'
      normalized.code = error.code
      normalized.details = error.details
      normalized.category = error.category || ERROR_CATEGORIES.UNKNOWN
      normalized.severity = error.severity || ERROR_SEVERITY.MEDIUM
    }

    return normalized
  }

  /**
   * 错误分类
   */
  categorizeError(error) {
    if (error.category && error.category !== ERROR_CATEGORIES.UNKNOWN) {
      return error.category
    }

    // 根据HTTP状态码分类
    if (error.code) {
      const code = parseInt(error.code)

      if (code === 401) {
        return ERROR_CATEGORIES.AUTHENTICATION
      } else if (code === 403) {
        return ERROR_CATEGORIES.AUTHORIZATION
      } else if (code === 422) {
        return ERROR_CATEGORIES.VALIDATION
      } else if (code >= 500) {
        return ERROR_CATEGORIES.SERVER
      } else if (code >= 400) {
        return ERROR_CATEGORIES.BUSINESS
      }
    }

    // 根据错误消息分类
    const message = (error.message || '').toLowerCase()

    if (message.includes('network') || message.includes('timeout') || message.includes('连接')) {
      return ERROR_CATEGORIES.NETWORK
    }

    if (message.includes('auth') || message.includes('login') || message.includes('token')) {
      return ERROR_CATEGORIES.AUTHENTICATION
    }

    if (
      message.includes('permission') ||
      message.includes('权限') ||
      message.includes('forbidden')
    ) {
      return ERROR_CATEGORIES.AUTHORIZATION
    }

    if (message.includes('validation') || message.includes('验证') || message.includes('invalid')) {
      return ERROR_CATEGORIES.VALIDATION
    }

    return ERROR_CATEGORIES.UNKNOWN
  }

  /**
   * 获取HTTP错误分类
   */
  getHttpErrorCategory(status) {
    switch (status) {
      case 401:
        return ERROR_CATEGORIES.AUTHENTICATION
      case 403:
        return ERROR_CATEGORIES.AUTHORIZATION
      case 422:
        return ERROR_CATEGORIES.VALIDATION
      case 500:
      case 502:
      case 503:
      case 504:
        return ERROR_CATEGORIES.SERVER
      default:
        return status >= 400 && status < 500 ? ERROR_CATEGORIES.BUSINESS : ERROR_CATEGORIES.UNKNOWN
    }
  }

  /**
   * 获取HTTP错误严重程度
   */
  getHttpErrorSeverity(status) {
    switch (status) {
      case 401:
      case 403:
        return ERROR_SEVERITY.HIGH
      case 500:
      case 502:
      case 503:
      case 504:
        return ERROR_SEVERITY.CRITICAL
      case 422:
        return ERROR_SEVERITY.MEDIUM
      default:
        return ERROR_SEVERITY.LOW
    }
  }

  /**
   * 获取默认HTTP错误消息
   */
  getDefaultHttpMessage(status) {
    switch (status) {
      case 400:
        return '请求参数错误'
      case 401:
        return '登录已过期，请重新登录'
      case 403:
        return '权限不足，无法执行此操作'
      case 404:
        return '请求的资源不存在'
      case 422:
        return '数据验证失败'
      case 500:
        return '服务器内部错误'
      case 502:
        return '网关错误'
      case 503:
        return '服务暂时不可用'
      case 504:
        return '请求超时'
      default:
        return `请求失败 (${status})`
    }
  }

  /**
   * 判断是否应该自动登出
   */
  shouldAutoLogout(error) {
    // 检查错误代码
    if (error.code === 401) {
      return true
    }

    // 检查错误消息
    const message = (error.message || '').toLowerCase()
    const logoutKeywords = [
      'token expired',
      'token invalid',
      'unauthorized',
      'please login',
      '令牌过期',
      '令牌无效',
      '请重新登录',
    ]

    return logoutKeywords.some((keyword) => message.includes(keyword))
  }

  /**
   * 获取权限错误消息
   */
  getPermissionErrorMessage(error) {
    const defaultMessage = '权限不足，无法执行此操作'

    if (error.details && error.details.required_permission) {
      return `需要权限：${error.details.required_permission}`
    }

    if (error.message && error.message.includes('权限')) {
      return error.message
    }

    return defaultMessage
  }

  /**
   * 获取网络错误消息
   */
  getNetworkErrorMessage(error) {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return '请求超时，请检查网络连接'
    }

    if (error.code === 'ERR_NETWORK') {
      return '网络连接失败，请检查网络设置'
    }

    return '网络错误，请稍后重试'
  }

  /**
   * 获取服务器错误消息
   */
  getServerErrorMessage(error) {
    const code = parseInt(error.code)

    switch (code) {
      case 500:
        return '服务器内部错误，请联系管理员'
      case 502:
        return '网关错误，服务暂时不可用'
      case 503:
        return '服务维护中，请稍后重试'
      case 504:
        return '服务器响应超时，请稍后重试'
      default:
        return error.message || '服务器错误，请稍后重试'
    }
  }

  /**
   * 处理验证错误
   */
  handleValidationErrors(validationErrors) {
    if (Array.isArray(validationErrors)) {
      validationErrors.forEach((error) => {
        this.showNotification(error.message || error, NOTIFICATION_TYPES.WARNING, {
          duration: 8000,
        })
      })
    } else if (typeof validationErrors === 'object') {
      Object.entries(validationErrors).forEach(([field, messages]) => {
        const fieldMessages = Array.isArray(messages) ? messages : [messages]
        fieldMessages.forEach((message) => {
          this.showNotification(`${field}: ${message}`, NOTIFICATION_TYPES.WARNING, {
            duration: 8000,
          })
        })
      })
    }
  }

  /**
   * 处理未知错误
   */
  handleUnknownError(error) {
    console.error('[ErrorCenter] 未知错误:', error)

    this.showNotification(error.message || '系统错误，请稍后重试', NOTIFICATION_TYPES.ERROR)

    return { handled: true, action: 'notify' }
  }

  /**
   * 显示通知
   */
  showNotification(message, type = NOTIFICATION_TYPES.ERROR, options = {}) {
    if (window.$message) {
      const messageOptions = {
        keepAliveOnHover: true,
        ...options,
      }

      switch (type) {
        case NOTIFICATION_TYPES.SUCCESS:
          window.$message.success(message, messageOptions)
          break
        case NOTIFICATION_TYPES.INFO:
          window.$message.info(message, messageOptions)
          break
        case NOTIFICATION_TYPES.WARNING:
          window.$message.warning(message, messageOptions)
          break
        case NOTIFICATION_TYPES.ERROR:
        default:
          window.$message.error(message, messageOptions)
          break
      }
    } else {
      console.error('[ErrorCenter] 无法显示通知:', message)
    }
  }

  /**
   * 记录错误历史
   */
  recordError(error) {
    this.errorHistory.unshift(error)

    // 限制历史记录大小
    if (this.errorHistory.length > this.maxHistorySize) {
      this.errorHistory = this.errorHistory.slice(0, this.maxHistorySize)
    }
  }

  /**
   * 生成错误ID
   */
  generateErrorId() {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 获取错误历史
   */
  getErrorHistory(limit = 10) {
    return this.errorHistory.slice(0, limit)
  }

  /**
   * 获取错误统计
   */
  getErrorStats() {
    const stats = {
      total: this.errorHistory.length,
      categories: {},
      severities: {},
      recent: this.errorHistory.slice(0, 5),
    }

    this.errorHistory.forEach((error) => {
      // 统计分类
      stats.categories[error.category] = (stats.categories[error.category] || 0) + 1

      // 统计严重程度
      stats.severities[error.severity] = (stats.severities[error.severity] || 0) + 1
    })

    return stats
  }

  /**
   * 清除错误历史
   */
  clearHistory() {
    this.errorHistory = []
  }
}

// 创建全局错误中心实例
export const errorCenter = new ErrorCenter()

// 便捷方法
export function handleError(error, context = {}) {
  return errorCenter.handleError(error, context)
}

export function registerErrorHandler(category, handler) {
  return errorCenter.registerHandler(category, handler)
}

export function getErrorStats() {
  return errorCenter.getErrorStats()
}

export function getErrorHistory(limit) {
  return errorCenter.getErrorHistory(limit)
}

// 在开发环境下暴露调试工具
if (import.meta.env.MODE === 'development') {
  window.errorCenter = errorCenter
  window.errorStats = getErrorStats
  window.errorHistory = getErrorHistory

  console.log('🔧 错误中心调试工具已挂载到window对象')
  console.log('可用命令：errorCenter, errorStats(), errorHistory()')
}
