/**
 * 统一的API错误处理工具
 * 用于处理401认证错误和其他常见API错误
 */

import { useUserStore } from '@/store/modules/user'
import { usePermissionStore } from '@/store/modules/permission'
import { removeToken } from '@/utils/auth/token'

/**
 * 检查是否为认证错误
 * @param {*} error - 错误对象
 * @returns {boolean} 是否为认证错误
 */
export function isAuthError(error) {
  return (
    error?.response?.status === 401 ||
    error?.status === 401 ||
    error?.code === 401 ||
    error?.message?.includes('401') ||
    error?.message?.includes('Unauthorized') ||
    error?.message?.includes('缺少访问令牌')
  )
}

/**
 * 检查是否为token过期错误
 * @param {*} error - 错误对象
 * @returns {boolean} 是否为token过期错误
 */
export function isTokenExpiredError(error) {
  const message = error?.message || error?.response?.data?.message || ''
  return (
    message.includes('Token expired') ||
    message.includes('令牌已过期') ||
    message.includes('token已过期') ||
    message.includes('登录已过期')
  )
}

/**
 * 清除认证状态
 */
export function clearAuthState() {
  console.log('🔄 清除认证状态')

  // 清除token
  removeToken()

  // 清除localStorage中的认证信息
  localStorage.removeItem('userInfo')
  localStorage.removeItem('permissions')
  localStorage.removeItem('access_token')

  // 重置store状态
  try {
    const userStore = useUserStore()
    const permissionStore = usePermissionStore()
    userStore.$reset()
    permissionStore.resetPermission()
  } catch (error) {
    console.warn('重置store状态失败:', error)
  }
}

/**
 * 重定向到登录页
 */
export function redirectToLogin() {
  const currentPath = window.location.pathname
  if (!currentPath.includes('/login')) {
    console.log('🔄 重定向到登录页')
    // 保存当前路径，登录后可以返回
    sessionStorage.setItem('redirectPath', currentPath)
    window.location.href = '/login'
  }
}

/**
 * 处理认证错误
 * @param {*} error - 错误对象
 * @param {Object} options - 选项
 * @returns {Promise} 处理结果
 */
export async function handleAuthError(error, options = {}) {
  const { showMessage = true, autoRedirect = true } = options

  console.error('🚫 认证错误:', error)

  // 检查是否正在登出
  try {
    const userStore = useUserStore()
    if (userStore.isLoggingOut) {
      console.log('🔄 正在登出，跳过错误消息显示')
      return Promise.reject({
        type: 'AUTH_ERROR',
        message: '认证失败',
        originalError: error,
      })
    }
  } catch (e) {
    console.warn('获取用户状态失败:', e)
  }

  // 显示错误消息
  if (showMessage && window.$message) {
    if (isTokenExpiredError(error)) {
      window.$message.warning('登录已过期，请重新登录')
    } else {
      window.$message.error('认证失败，请重新登录')
    }
  }

  // 清除认证状态
  clearAuthState()

  // 自动重定向到登录页
  if (autoRedirect) {
    setTimeout(() => {
      redirectToLogin()
    }, 1000) // 延迟1秒，让用户看到错误消息
  }

  return Promise.reject({
    type: 'AUTH_ERROR',
    message: '认证失败',
    originalError: error,
  })
}

/**
 * 带重试的API调用
 * @param {Function} apiCall - API调用函数
 * @param {Object} options - 选项
 * @returns {Promise} API调用结果
 */
export async function apiCallWithRetry(apiCall, options = {}) {
  const { maxRetries = 1, retryDelay = 1000, showError = true } = options

  let lastError = null

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall()
    } catch (error) {
      lastError = error

      // 如果是认证错误
      if (isAuthError(error)) {
        console.log(`🔄 检测到401错误，尝试次数: ${attempt + 1}/${maxRetries + 1}`)

        // 检查是否正在登出
        try {
          const userStore = useUserStore()
          if (userStore.isLoggingOut) {
            console.log('🔄 正在登出，跳过API重试和错误处理')
            throw error
          }
        } catch (e) {
          // 如果获取store失败，继续正常流程
        }

        // 如果还有重试次数
        if (attempt < maxRetries) {
          console.log(`⏳ ${retryDelay}ms后重试...`)
          await new Promise((resolve) => setTimeout(resolve, retryDelay))
          continue
        } else {
          // 重试次数用完，处理认证错误
          return handleAuthError(error, { showMessage: showError })
        }
      } else {
        // 非认证错误，直接抛出
        if (showError && window.$message) {
          const message = error?.message || error?.response?.data?.message || '操作失败'
          window.$message.error(message)
        }
        throw error
      }
    }
  }

  // 如果到这里，说明重试次数用完了
  throw lastError
}

/**
 * 创建带错误处理的API调用函数
 * @param {Function} apiCall - 原始API调用函数
 * @param {Object} options - 选项
 * @returns {Function} 包装后的API调用函数
 */
export function createSafeApiCall(apiCall, options = {}) {
  return async (...args) => {
    return apiCallWithRetry(() => apiCall(...args), options)
  }
}

/**
 * 统一的数据获取函数
 * @param {Function} apiCall - API调用函数
 * @param {Object} options - 选项
 * @returns {Promise} 数据获取结果
 */
export async function safeDataFetch(apiCall, options = {}) {
  const { defaultData = [], showError = true, maxRetries = 1, onError = null } = options

  try {
    const result = await apiCallWithRetry(apiCall, {
      maxRetries,
      showError: false, // 我们自己处理错误显示
    })
    return result
  } catch (error) {
    console.error('数据获取失败:', error)

    // 检查是否正在登出
    let isLoggingOut = false
    try {
      const userStore = useUserStore()
      isLoggingOut = userStore.isLoggingOut
    } catch (e) {
      // 如果获取store失败，继续正常流程
    }

    // 如果不是认证错误且不在登出过程中，显示错误消息
    if (!isAuthError(error) && !isLoggingOut && showError && window.$message) {
      const message = error?.message || error?.response?.data?.message || '数据获取失败'
      window.$message.error(message)
    }

    // 调用自定义错误处理函数
    if (onError && typeof onError === 'function') {
      onError(error)
    }

    // 返回默认数据
    return { data: defaultData, total: 0 }
  }
}

export default {
  isAuthError,
  isTokenExpiredError,
  clearAuthState,
  redirectToLogin,
  handleAuthError,
  apiCallWithRetry,
  createSafeApiCall,
  safeDataFetch,
}
