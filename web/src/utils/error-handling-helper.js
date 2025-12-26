/**
 * 错误处理助手
 * 用于避免重复的错误消息显示
 */

/**
 * 检查错误是否已经被HTTP拦截器处理过
 * @param {*} error - 错误对象
 * @returns {boolean} - 是否已被处理
 */
export function isErrorHandledByInterceptor(error) {
  // 检查错误是否有 ErrorHandler 处理过的标记
  return error && typeof error === 'object' && error.success === false
}

/**
 * 安全的错误消息显示
 * 只有在错误未被拦截器处理时才显示消息
 * @param {*} error - 错误对象
 * @param {string} fallbackMessage - 备用错误消息
 * @param {Object} options - 消息选项
 */
export function showErrorIfNotHandled(error, fallbackMessage = '操作失败', options = {}) {
  if (!isErrorHandledByInterceptor(error)) {
    const message = error?.message || error?.response?.data?.detail || fallbackMessage

    if (window.$message) {
      window.$message.error(message, options)
    } else {
      console.error('[ErrorHelper] 无法显示错误消息:', message)
    }
  }
}

/**
 * 包装API调用，避免重复错误处理
 * @param {Function} apiCall - API调用函数
 * @param {string} fallbackMessage - 备用错误消息
 * @param {Object} options - 选项
 * @returns {Promise} - API调用结果
 */
export async function safeApiCall(apiCall, fallbackMessage = '操作失败', options = {}) {
  try {
    return await apiCall()
  } catch (error) {
    if (!options.silent) {
      showErrorIfNotHandled(error, fallbackMessage, options.messageOptions)
    }
    throw error
  }
}

/**
 * 创建一个安全的错误处理器
 * @param {string} defaultMessage - 默认错误消息
 * @param {Object} options - 选项
 * @returns {Function} - 错误处理函数
 */
export function createSafeErrorHandler(defaultMessage = '操作失败', options = {}) {
  return (error) => {
    console.error(options.logPrefix || '[Error]', error)
    showErrorIfNotHandled(error, defaultMessage, options.messageOptions)
  }
}

/**
 * 装饰器：为函数添加安全的错误处理
 * @param {Function} fn - 要装饰的函数
 * @param {string} errorMessage - 错误消息
 * @param {Object} options - 选项
 * @returns {Function} - 装饰后的函数
 */
export function withSafeErrorHandling(fn, errorMessage = '操作失败', options = {}) {
  return async (...args) => {
    try {
      return await fn(...args)
    } catch (error) {
      if (!options.silent) {
        showErrorIfNotHandled(error, errorMessage, options.messageOptions)
      }
      if (options.rethrow !== false) {
        throw error
      }
    }
  }
}

export default {
  isErrorHandledByInterceptor,
  showErrorIfNotHandled,
  safeApiCall,
  createSafeErrorHandler,
  withSafeErrorHandling,
}
