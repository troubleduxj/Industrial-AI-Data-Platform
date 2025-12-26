import { useUserStore } from '@/store'

export const ERROR_TYPES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  PERMISSION_ERROR: 'PERMISSION_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  BUSINESS_ERROR: 'BUSINESS_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
}

export class ErrorHandler {
  static handle(error, options = {}) {
    try {
      const normalizedError = this.normalizeError(error)
      this.logError(normalizedError)

      switch (normalizedError.type) {
        case ERROR_TYPES.AUTHENTICATION_ERROR:
          return this.handleAuthError(normalizedError, options)
        case ERROR_TYPES.PERMISSION_ERROR:
          return this.handlePermissionError(normalizedError, options)
        case ERROR_TYPES.VALIDATION_ERROR:
          return this.handleValidationError(normalizedError, options)
        case ERROR_TYPES.NETWORK_ERROR:
          return this.handleNetworkError(normalizedError, options)
        case ERROR_TYPES.SERVER_ERROR:
          return this.handleServerError(normalizedError, options)
        case ERROR_TYPES.BUSINESS_ERROR:
          return this.handleBusinessError(normalizedError, options)
        default:
          return this.handleGenericError(normalizedError, options)
      }
    } catch (handlerError) {
      console.error('[ErrorHandler] 错误处理器自身发生错误:', handlerError)
      return this.createErrorResponse('HANDLER_ERROR', '系统错误，请联系管理员', handlerError)
    }
  }

  static normalizeError(error) {
    if (error && error.type && ERROR_TYPES[error.type]) {
      return error
    }

    if (error && error.response) {
      const { status, data } = error.response
      return {
        code: data?.code || status,
        message: data?.message || this.getDefaultMessage(status),
        type: this.getErrorType(status, data),
        details: data?.details,
        validationErrors: data?.details?.validation_errors,
        requestId: error.config?.headers?.['X-Request-ID'],
        originalError: error,
      }
    }

    if (error && error.code && !error.response) {
      return {
        code: error.code,
        message: error.message || '网络连接失败',
        type: ERROR_TYPES.NETWORK_ERROR,
        originalError: error,
      }
    }

    if (error && error.code && error.message && error.type) {
      return error
    }

    if (error instanceof Error) {
      return {
        code: 'UNKNOWN_ERROR',
        message: error.message,
        type: ERROR_TYPES.UNKNOWN_ERROR,
        originalError: error,
      }
    }

    if (typeof error === 'string') {
      return {
        code: 'UNKNOWN_ERROR',
        message: error,
        type: ERROR_TYPES.UNKNOWN_ERROR,
        originalError: error,
      }
    }

    return {
      code: 'UNKNOWN_ERROR',
      message: '未知错误',
      type: ERROR_TYPES.UNKNOWN_ERROR,
      originalError: error,
    }
  }

  static getErrorType(status, data) {
    if (data?.details?.error_code) {
      switch (data.details.error_code) {
        case 'AUTHENTICATION_ERROR':
          return ERROR_TYPES.AUTHENTICATION_ERROR
        case 'PERMISSION_DENIED':
          return ERROR_TYPES.PERMISSION_ERROR
        case 'VALIDATION_ERROR':
          return ERROR_TYPES.VALIDATION_ERROR
        default:
          return ERROR_TYPES.BUSINESS_ERROR
      }
    }

    switch (status) {
      case 401:
        return ERROR_TYPES.AUTHENTICATION_ERROR
      case 403:
        return ERROR_TYPES.PERMISSION_ERROR
      case 422:
        return ERROR_TYPES.VALIDATION_ERROR
      case 500:
      case 502:
      case 503:
      case 504:
        return ERROR_TYPES.SERVER_ERROR
      default:
        return status >= 400 && status < 500
          ? ERROR_TYPES.BUSINESS_ERROR
          : ERROR_TYPES.UNKNOWN_ERROR
    }
  }

  static getDefaultMessage(status) {
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

  static async handleAuthError(error, options = {}) {
    try {
      const userStore = useUserStore()

      // 检查是否正在登出，如果是则跳过处理
      if (userStore.isLoggingOut) {
        console.log('[ErrorHandler] 正在登出，跳过认证错误处理')
        return this.createErrorResponse(error.code, error.message, error, { skipped: true })
      }

      // 检查是否应该自动登出
      // 只有在以下情况下才自动登出：
      // 1. 明确的token过期或无效错误
      // 2. 登录接口返回的401错误
      // 3. 用户信息获取接口返回的401错误
      const shouldAutoLogout = this.shouldAutoLogout(error, options)

      if (shouldAutoLogout) {
        await userStore.logout()

        if (!options.silent) {
          console.warn('[ErrorHandler] 认证失败，用户已自动登出')
        }

        return this.createErrorResponse(error.code, error.message, error, { autoLogout: true })
      } else {
        // 不自动登出，但需要判断是否显示错误信息
        // 如果是退出登录相关的请求，不显示错误消息
        const url = error.originalError?.config?.url || error.config?.url || ''
        const isLogoutRelated = url.includes('/auth/logout') || url.includes('/auth/user/apis')

        if (!options.silent && !isLogoutRelated) {
          this.showErrorMessage(error.message || '权限不足或操作未授权', {
            type: 'warning',
            keepAliveOnHover: true,
          })
        }

        return this.createErrorResponse(error.code, error.message, error, { autoLogout: false })
      }
    } catch (logoutError) {
      console.error('[ErrorHandler] 自动登出失败:', logoutError)

      if (!options.silent) {
        this.showErrorMessage(error.message)
      }

      return this.createErrorResponse(error.code, error.message, error, { logoutFailed: true })
    }
  }

  /**
   * 判断是否应该自动登出
   * @param {Object} error - 错误对象
   * @param {Object} options - 选项
   * @returns {boolean} 是否应该自动登出
   */
  static shouldAutoLogout(error, options = {}) {
    // 检查是否正在登出，如果是则不再自动登出
    try {
      const userStore = useUserStore()
      if (userStore.isLoggingOut) {
        console.log('[ErrorHandler] 正在登出，跳过自动登出检查')
        return false
      }
    } catch (e) {
      // 如果获取userStore失败，继续执行其他检查
      console.warn('[ErrorHandler] 无法获取userStore状态:', e)
    }

    // 如果明确指定不自动登出
    if (options.noAutoLogout === true) {
      return false
    }

    // 如果明确指定自动登出
    if (options.forceAutoLogout === true) {
      return true
    }

    // 检查请求URL，某些关键接口的401错误应该自动登出
    const url = error.config?.url || error.url || ''
    const criticalEndpoints = [
      '/api/v2/auth/login',
      '/api/v2/auth/logout',
      '/api/v2/auth/refresh',
      '/api/v2/users/me',
      '/api/v2/users/profile',
    ]

    if (criticalEndpoints.some((endpoint) => url.includes(endpoint))) {
      return true
    }

    // 检查错误消息，包含特定关键词的应该自动登出
    const message = (error.message || '').toLowerCase()
    const autoLogoutKeywords = [
      'token expired',
      'token invalid',
      'unauthorized access',
      'authentication failed',
      'please login again',
      '令牌已过期',
      '令牌无效',
      '请重新登录',
    ]

    if (autoLogoutKeywords.some((keyword) => message.includes(keyword))) {
      return true
    }

    // 默认情况下，对于普通的401错误，不自动登出
    // 这样可以避免因为权限不足而误触发登出
    return false
  }

  static handlePermissionError(error, options = {}) {
    if (!options.silent) {
      this.showErrorMessage(error.message, {
        type: 'warning',
        keepAliveOnHover: true,
      })
    }

    return this.createErrorResponse(error.code, error.message, error)
  }

  static handleValidationError(error, options = {}) {
    if (!options.silent) {
      this.showErrorMessage(error.message, { type: 'warning' })

      if (error.validationErrors && typeof error.validationErrors === 'object') {
        this.showValidationErrors(error.validationErrors)
      }
    }

    return this.createErrorResponse(error.code, error.message, error, {
      validationErrors: error.validationErrors,
    })
  }

  static handleNetworkError(error, options = {}) {
    if (!options.silent) {
      this.showErrorMessage(error.message, {
        type: 'error',
        duration: 5000,
      })
    }

    return this.createErrorResponse(error.code, error.message, error)
  }

  static handleServerError(error, options = {}) {
    if (!options.silent) {
      this.showErrorMessage(error.message, {
        type: 'error',
        keepAliveOnHover: true,
      })
    }

    return this.createErrorResponse(error.code, error.message, error)
  }

  static handleBusinessError(error, options = {}) {
    if (!options.silent) {
      this.showErrorMessage(error.message, {
        type: 'warning',
        keepAliveOnHover: true,
      })
    }

    return this.createErrorResponse(error.code, error.message, error)
  }

  static handleGenericError(error, options = {}) {
    if (!options.silent) {
      this.showErrorMessage(error.message || '系统错误，请稍后重试')
    }

    return this.createErrorResponse(
      error.code || 'UNKNOWN_ERROR',
      error.message || '未知错误',
      error
    )
  }

  static showValidationErrors(validationErrors) {
    Object.entries(validationErrors).forEach(([field, messages]) => {
      const fieldMessages = Array.isArray(messages) ? messages : [messages]
      fieldMessages.forEach((msg) => {
        this.showErrorMessage(`${field}: ${msg}`, {
          type: 'warning',
          duration: 8000,
          keepAliveOnHover: true,
        })
      })
    })
  }

  static showErrorMessage(message, options = {}) {
    if (window.$message) {
      const messageOptions = {
        keepAliveOnHover: true,
        ...options,
      }

      switch (options.type) {
        case 'warning':
          window.$message.warning(message, messageOptions)
          break
        case 'error':
        default:
          window.$message.error(message, messageOptions)
          break
      }
    } else {
      console.error('[ErrorHandler] 无法显示错误消息:', message)
    }
  }

  static createErrorResponse(code, message, originalError, metadata = {}) {
    return {
      success: false,
      code,
      message,
      error: originalError,
      timestamp: new Date().toISOString(),
      ...metadata,
    }
  }

  static logError(error) {
    const logData = {
      type: error.type,
      code: error.code,
      message: error.message,
      requestId: error.requestId,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    }

    if (import.meta.env.MODE === 'development') {
      console.group(`[ErrorHandler] ${error.type}`)
      console.error('错误详情:', logData)
      if (error.details) {
        console.error('错误详细信息:', error.details)
      }
      if (error.originalError) {
        console.error('原始错误:', error.originalError)
      }
      console.groupEnd()
    } else {
      console.error('[ErrorHandler]', {
        type: error.type,
        code: error.code,
        message: error.message,
        requestId: error.requestId,
      })
    }
  }
}

export function withErrorHandler(options = {}) {
  return function (target, propertyKey, descriptor) {
    const originalMethod = descriptor.value

    descriptor.value = async function (...args) {
      try {
        return await originalMethod.apply(this, args)
      } catch (error) {
        return ErrorHandler.handle(error, options)
      }
    }

    return descriptor
  }
}

export function createSafeApiCall(apiCall, options = {}) {
  return async function (...args) {
    try {
      return await apiCall(...args)
    } catch (error) {
      const handledError = ErrorHandler.handle(error, options)

      if (options.rethrow !== false) {
        throw handledError
      }

      return handledError
    }
  }
}

export default ErrorHandler
