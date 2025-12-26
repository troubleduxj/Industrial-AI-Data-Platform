/**
 * 增强版HTTP拦截器
 * 实现任务16：前端HTTP拦截器和错误处理
 *
 * 功能特性：
 * 1. 自动添加认证头
 * 2. 统一错误处理和用户提示
 * 3. 令牌自动刷新
 * 4. 网络错误和权限错误区分处理
 * 5. 请求重试机制
 * 6. 性能监控和日志记录
 */

import axios from 'axios'
import {
  getTokenEnhanced,
  setTokenEnhanced,
  checkTokenExpiration,
  clearAuthStateEnhanced,
} from '@/utils/auth-enhanced'
import { useUserStore } from '@/store'
import { resolveResError } from './helpers'

// 请求配置常量
const REQUEST_CONFIG = {
  TIMEOUT: 60000,
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
  TOKEN_REFRESH_THRESHOLD: 5 * 60 * 1000, // 5分钟
}

// 错误类型枚举
export const ERROR_TYPES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  PERMISSION_ERROR: 'PERMISSION_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  BUSINESS_ERROR: 'BUSINESS_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
}

// 白名单路径（不需要认证的接口）
const WHITELIST_PATHS = [
  '/api/v2/auth/login',
  '/api/v2/auth/register',
  '/api/v2/auth/forgot-password',
  '/api/v2/auth/reset-password',
  '/api/v2/health',
  '/api/v2/docs',
]

// 重试配置
const RETRY_CONFIG = {
  retryCondition: (error) => {
    // 网络错误或5xx服务器错误时重试
    return !error.response || (error.response.status >= 500 && error.response.status <= 599)
  },
  retryDelay: (retryCount) => {
    return Math.min(REQUEST_CONFIG.RETRY_DELAY * Math.pow(2, retryCount), 10000)
  },
}

// 请求性能监控
class RequestMonitor {
  constructor() {
    this.requests = new Map()
    this.stats = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      slowRequests: 0, // 超过3秒的请求
    }
  }

  startRequest(requestId, config) {
    this.requests.set(requestId, {
      startTime: Date.now(),
      url: config.url,
      method: config.method,
    })
    this.stats.totalRequests++
  }

  endRequest(requestId, success = true, responseTime = 0) {
    const request = this.requests.get(requestId)
    if (request) {
      this.requests.delete(requestId)

      if (success) {
        this.stats.successfulRequests++
      } else {
        this.stats.failedRequests++
      }

      // 更新平均响应时间
      const totalTime =
        this.stats.averageResponseTime * (this.stats.totalRequests - 1) + responseTime
      this.stats.averageResponseTime = totalTime / this.stats.totalRequests

      // 记录慢请求
      if (responseTime > 3000) {
        this.stats.slowRequests++
        console.warn(
          `[HTTP Monitor] 慢请求检测: ${request.method} ${request.url} - ${responseTime}ms`
        )
      }
    }
  }

  getStats() {
    return {
      ...this.stats,
      successRate:
        this.stats.totalRequests > 0
          ? ((this.stats.successfulRequests / this.stats.totalRequests) * 100).toFixed(2) + '%'
          : '0%',
      activeRequests: this.requests.size,
    }
  }

  reset() {
    this.requests.clear()
    this.stats = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      slowRequests: 0,
    }
  }
}

// 全局请求监控实例
const requestMonitor = new RequestMonitor()

// 令牌刷新管理器
class TokenRefreshManager {
  constructor() {
    this.isRefreshing = false
    this.failedQueue = []
  }

  async refreshToken() {
    if (this.isRefreshing) {
      return new Promise((resolve, reject) => {
        this.failedQueue.push({ resolve, reject })
      })
    }

    this.isRefreshing = true

    try {
      // 这里应该调用刷新令牌的API
      // 目前返回false表示不支持自动刷新
      const refreshed = await this.callRefreshAPI()

      if (refreshed) {
        this.processQueue(null, refreshed.token)
        return refreshed.token
      } else {
        this.processQueue(new Error('Token refresh failed'), null)
        return null
      }
    } catch (error) {
      this.processQueue(error, null)
      throw error
    } finally {
      this.isRefreshing = false
    }
  }

  async callRefreshAPI() {
    // TODO: 实现实际的令牌刷新API调用
    // 目前返回null表示不支持
    return null
  }

  processQueue(error, token = null) {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error)
      } else {
        resolve(token)
      }
    })

    this.failedQueue = []
  }
}

// 全局令牌刷新管理器
const tokenRefreshManager = new TokenRefreshManager()

/**
 * 增强版请求拦截器
 */
export function enhancedRequestInterceptor(config) {
  try {
    // 生成请求ID
    const requestId = generateRequestId()
    config.metadata = {
      requestId,
      startTime: Date.now(),
    }

    // 开始监控请求
    requestMonitor.startRequest(requestId, config)

    // 检查是否在白名单中
    if (isWhitelistedPath(config.url)) {
      console.log(`[HTTP] 白名单请求: ${config.method?.toUpperCase()} ${config.url}`)
      return config
    }

    // 处理认证
    const authResult = handleAuthentication(config)
    if (!authResult.success) {
      throw new Error(authResult.message)
    }

    // 设置通用请求头
    setCommonHeaders(config)

    // 处理请求参数
    processRequestParams(config)

    // 记录请求日志
    logRequest(config)

    return config
  } catch (error) {
    console.error('[HTTP] 请求拦截器错误:', error)
    requestMonitor.endRequest(config.metadata?.requestId, false)
    return Promise.reject(error)
  }
}

/**
 * 增强版请求错误拦截器
 */
export function enhancedRequestErrorInterceptor(error) {
  console.error('[HTTP] 请求发送失败:', error)
  return Promise.reject(error)
}

/**
 * 增强版响应拦截器
 */
export function enhancedResponseInterceptor(response) {
  try {
    const { config, data, status } = response
    const responseTime = Date.now() - config.metadata.startTime

    // 结束请求监控
    requestMonitor.endRequest(config.metadata.requestId, true, responseTime)

    // 记录响应日志
    logResponse(response, responseTime)

    // 处理业务错误
    if (data && typeof data === 'object') {
      // 检查不同的错误标识
      const hasError =
        data.success === false ||
        data.code !== 200 ||
        data.error ||
        (data.status && data.status !== 'success')

      if (hasError) {
        const error = createBusinessError(data, response)
        return Promise.reject(error)
      }
    }

    // 标准化响应数据
    return normalizeResponse(response)
  } catch (error) {
    console.error('[HTTP] 响应拦截器错误:', error)
    return Promise.reject(error)
  }
}

/**
 * 增强版响应错误拦截器
 */
export async function enhancedResponseErrorInterceptor(error) {
  try {
    const { config, response } = error
    const responseTime = config?.metadata ? Date.now() - config.metadata.startTime : 0

    // 结束请求监控
    if (config?.metadata?.requestId) {
      requestMonitor.endRequest(config.metadata.requestId, false, responseTime)
    }

    // 记录错误日志
    logError(error, responseTime)

    // 处理不同类型的错误
    const errorType = determineErrorType(error)
    const normalizedError = normalizeError(error, errorType)

    // 特殊错误处理
    switch (errorType) {
      case ERROR_TYPES.AUTHENTICATION_ERROR:
        return await handleAuthenticationError(normalizedError, config)

      case ERROR_TYPES.PERMISSION_ERROR:
        return handlePermissionError(normalizedError)

      case ERROR_TYPES.NETWORK_ERROR:
        return await handleNetworkError(normalizedError, config)

      case ERROR_TYPES.TIMEOUT_ERROR:
        return await handleTimeoutError(normalizedError, config)

      case ERROR_TYPES.SERVER_ERROR:
        return await handleServerError(normalizedError, config)

      default:
        return handleGenericError(normalizedError)
    }
  } catch (handlerError) {
    console.error('[HTTP] 错误处理器失败:', handlerError)
    return Promise.reject(createFallbackError(error, handlerError))
  }
}

/**
 * 处理认证
 */
function handleAuthentication(config) {
  try {
    const token = getTokenEnhanced()

    if (!token) {
      return { success: false, message: '未找到认证令牌' }
    }

    // 检查令牌是否即将过期
    const expirationCheck = checkTokenExpiration(5) // 5分钟内过期
    if (expirationCheck.expired) {
      return { success: false, message: '认证令牌已过期' }
    }

    if (expirationCheck.warning) {
      console.warn(`[HTTP] 令牌即将过期，剩余时间: ${expirationCheck.minutesUntilExpiry}分钟`)
      // 这里可以触发令牌刷新逻辑
    }

    // 设置认证头
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
    config.headers.token = token // 兼容后端的token头

    return { success: true }
  } catch (error) {
    console.error('[HTTP] 认证处理失败:', error)
    return { success: false, message: '认证处理失败' }
  }
}

/**
 * 设置通用请求头
 */
function setCommonHeaders(config) {
  config.headers = config.headers || {}

  // 设置内容类型
  if (!config.headers['Content-Type']) {
    config.headers['Content-Type'] = 'application/json'
  }

  // 设置API版本
  if (config.url && config.url.includes('/api/v2/')) {
    config.headers['API-Version'] = 'v2'
  }

  // 设置请求ID
  config.headers['X-Request-ID'] = config.metadata.requestId

  // 设置时间戳
  config.headers['X-Request-Time'] = new Date().toISOString()

  // 设置用户代理信息
  config.headers['X-User-Agent'] = navigator.userAgent

  // 设置页面信息
  config.headers['X-Page-URL'] = window.location.href
}

/**
 * 处理请求参数
 */
function processRequestParams(config) {
  // 处理GET请求参数
  if (config.method === 'get' && config.params) {
    // 移除空值参数
    Object.keys(config.params).forEach((key) => {
      if (
        config.params[key] === null ||
        config.params[key] === undefined ||
        config.params[key] === ''
      ) {
        delete config.params[key]
      }
    })
  }

  // 处理POST/PUT请求数据
  if (['post', 'put', 'patch'].includes(config.method) && config.data) {
    // 确保数据是JSON格式
    if (typeof config.data === 'object' && !(config.data instanceof FormData)) {
      config.data = JSON.stringify(config.data)
    }
  }
}

/**
 * 检查是否为白名单路径
 */
function isWhitelistedPath(url) {
  if (!url) return false
  return WHITELIST_PATHS.some((path) => url.includes(path))
}

/**
 * 生成请求ID
 */
function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 确定错误类型
 */
function determineErrorType(error) {
  if (!error.response) {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return ERROR_TYPES.TIMEOUT_ERROR
    }
    return ERROR_TYPES.NETWORK_ERROR
  }

  const { status, data } = error.response

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
      if (status >= 400 && status < 500) {
        return ERROR_TYPES.BUSINESS_ERROR
      }
      return ERROR_TYPES.UNKNOWN_ERROR
  }
}

/**
 * 标准化错误对象
 */
function normalizeError(error, errorType) {
  const { config, response } = error
  const responseTime = config?.metadata ? Date.now() - config.metadata.startTime : 0

  return {
    type: errorType,
    code: response?.data?.code || response?.status || error.code || 'UNKNOWN',
    message: response?.data?.message || error.message || '未知错误',
    details: response?.data?.details || null,
    status: response?.status || null,
    url: config?.url || null,
    method: config?.method || null,
    requestId: config?.metadata?.requestId || null,
    responseTime,
    timestamp: new Date().toISOString(),
    originalError: error,
  }
}

/**
 * 处理认证错误
 */
async function handleAuthenticationError(error, config) {
  console.warn('[HTTP] 认证错误:', error.message)

  try {
    // 尝试刷新令牌
    const newToken = await tokenRefreshManager.refreshToken()

    if (newToken) {
      // 令牌刷新成功，重试原请求
      console.log('[HTTP] 令牌刷新成功，重试请求')
      config.headers.Authorization = `Bearer ${newToken}`
      config.headers.token = newToken
      return axios.request(config)
    }
  } catch (refreshError) {
    console.error('[HTTP] 令牌刷新失败:', refreshError)
  }

  // 令牌刷新失败，执行登出
  try {
    const userStore = useUserStore()
    if (!userStore.isLoggingOut) {
      console.log('[HTTP] 执行自动登出')
      await userStore.logout()

      // 显示友好的错误提示
      showErrorMessage('登录已过期，请重新登录', { type: 'warning' })
    }
  } catch (logoutError) {
    console.error('[HTTP] 自动登出失败:', logoutError)
  }

  return Promise.reject(error)
}

/**
 * 处理权限错误
 */
function handlePermissionError(error) {
  console.warn('[HTTP] 权限错误:', error.message)

  showErrorMessage(error.message || '权限不足，无法执行此操作', {
    type: 'warning',
    keepAliveOnHover: true,
  })

  return Promise.reject(error)
}

/**
 * 处理网络错误
 */
async function handleNetworkError(error, config) {
  console.error('[HTTP] 网络错误:', error.message)

  // 检查是否需要重试
  if (shouldRetry(config)) {
    return await retryRequest(config, error)
  }

  showErrorMessage('网络连接失败，请检查网络设置', {
    type: 'error',
    duration: 5000,
  })

  return Promise.reject(error)
}

/**
 * 处理超时错误
 */
async function handleTimeoutError(error, config) {
  console.error('[HTTP] 请求超时:', error.message)

  // 检查是否需要重试
  if (shouldRetry(config)) {
    return await retryRequest(config, error)
  }

  showErrorMessage('请求超时，请稍后重试', {
    type: 'warning',
    duration: 3000,
  })

  return Promise.reject(error)
}

/**
 * 处理服务器错误
 */
async function handleServerError(error, config) {
  console.error('[HTTP] 服务器错误:', error.message)

  // 检查是否需要重试
  if (shouldRetry(config)) {
    return await retryRequest(config, error)
  }

  showErrorMessage(error.message || '服务器错误，请稍后重试', {
    type: 'error',
    keepAliveOnHover: true,
  })

  return Promise.reject(error)
}

/**
 * 处理通用错误
 */
function handleGenericError(error) {
  console.error('[HTTP] 通用错误:', error.message)

  showErrorMessage(error.message || '请求失败，请稍后重试')

  return Promise.reject(error)
}

/**
 * 检查是否应该重试
 */
function shouldRetry(config) {
  const retryCount = config.__retryCount || 0
  return retryCount < REQUEST_CONFIG.MAX_RETRIES && RETRY_CONFIG.retryCondition({ response: null })
}

/**
 * 重试请求
 */
async function retryRequest(config, originalError) {
  config.__retryCount = (config.__retryCount || 0) + 1

  const delay = RETRY_CONFIG.retryDelay(config.__retryCount - 1)

  console.log(
    `[HTTP] 重试请求 (${config.__retryCount}/${REQUEST_CONFIG.MAX_RETRIES}), 延迟: ${delay}ms`
  )

  await new Promise((resolve) => setTimeout(resolve, delay))

  try {
    return await axios.request(config)
  } catch (retryError) {
    if (config.__retryCount >= REQUEST_CONFIG.MAX_RETRIES) {
      console.error('[HTTP] 重试次数已达上限')
      return Promise.reject(originalError)
    }
    return retryRequest(config, originalError)
  }
}

/**
 * 创建业务错误
 */
function createBusinessError(data, response) {
  return {
    type: ERROR_TYPES.BUSINESS_ERROR,
    code: data.code || response.status,
    message: data.message || data.msg || '业务处理失败',
    details: data.details || data.data,
    response,
    isBusinessError: true,
  }
}

/**
 * 标准化响应数据
 */
function normalizeResponse(response) {
  const { data, config } = response
  const responseTime = Date.now() - config.metadata.startTime

  // 添加元数据
  if (data && typeof data === 'object') {
    data._metadata = {
      requestId: config.metadata.requestId,
      responseTime,
      timestamp: new Date().toISOString(),
    }
  }

  return data
}

/**
 * 创建兜底错误
 */
function createFallbackError(originalError, handlerError) {
  return {
    type: ERROR_TYPES.UNKNOWN_ERROR,
    code: 'HANDLER_ERROR',
    message: '错误处理器失败',
    originalError,
    handlerError,
    timestamp: new Date().toISOString(),
  }
}

/**
 * 显示错误消息
 */
function showErrorMessage(message, options = {}) {
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
    console.error('[HTTP] 无法显示错误消息:', message)
  }
}

/**
 * 记录请求日志
 */
function logRequest(config) {
  if (import.meta.env.MODE === 'development') {
    console.log(`[HTTP Request] ${config.method?.toUpperCase()} ${config.url}`, {
      requestId: config.metadata.requestId,
      headers: config.headers,
      params: config.params,
      data: config.data,
    })
  }
}

/**
 * 记录响应日志
 */
function logResponse(response, responseTime) {
  if (import.meta.env.MODE === 'development') {
    const { config, status, data } = response
    console.log(`[HTTP Response] ${config.method?.toUpperCase()} ${config.url} - ${status}`, {
      requestId: config.metadata.requestId,
      responseTime: `${responseTime}ms`,
      dataSize: JSON.stringify(data).length,
    })
  }
}

/**
 * 记录错误日志
 */
function logError(error, responseTime) {
  const { config, response } = error
  const status = response?.status || 'Network Error'

  console.error(`[HTTP Error] ${config?.method?.toUpperCase()} ${config?.url} - ${status}`, {
    requestId: config?.metadata?.requestId,
    responseTime: `${responseTime}ms`,
    message: error.message,
    data: response?.data,
  })
}

/**
 * 获取请求监控统计
 */
export function getRequestStats() {
  return requestMonitor.getStats()
}

/**
 * 重置请求监控统计
 */
export function resetRequestStats() {
  requestMonitor.reset()
}

/**
 * 创建增强版axios实例
 */
export function createEnhancedAxios(options = {}) {
  const defaultOptions = {
    timeout: REQUEST_CONFIG.TIMEOUT,
  }

  const service = axios.create({
    ...defaultOptions,
    ...options,
  })

  // 注册拦截器
  service.interceptors.request.use(enhancedRequestInterceptor, enhancedRequestErrorInterceptor)

  service.interceptors.response.use(enhancedResponseInterceptor, enhancedResponseErrorInterceptor)

  return service
}

// 导出增强版请求实例
export const enhancedRequest = createEnhancedAxios({
  baseURL:
    import.meta.env.VITE_USE_PROXY === 'true' ? '/api/v2' : `${import.meta.env.VITE_BASE_API}/v2`,
})

// 在开发环境下暴露调试工具
if (import.meta.env.MODE === 'development') {
  window.httpStats = getRequestStats
  window.httpReset = resetRequestStats
  window.httpMonitor = requestMonitor

  console.log('🔧 HTTP调试工具已挂载到window对象')
  console.log('可用命令：httpStats(), httpReset(), httpMonitor')
}
