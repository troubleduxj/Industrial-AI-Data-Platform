/**
 * 统一HTTP客户端
 * 整合增强版拦截器、错误处理、令牌刷新和重试机制
 */

import axios from 'axios'
import {
  enhancedRequestInterceptor,
  enhancedRequestErrorInterceptor,
  enhancedResponseInterceptor,
  enhancedResponseErrorInterceptor,
} from './enhanced-interceptors'
import { errorCenter } from './error-center'
import { tokenRefreshManager } from './token-refresh-manager'
import { RetryManager, RETRY_STRATEGIES, RETRY_CONDITIONS } from './retry-manager'

/**
 * HTTP客户端配置
 */
const CLIENT_CONFIG = {
  // 基础配置
  timeout: 60000,

  // 重试配置
  retry: {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    strategy: RETRY_STRATEGIES.EXPONENTIAL_BACKOFF,
    conditions: [
      RETRY_CONDITIONS.NETWORK_ERROR,
      RETRY_CONDITIONS.TIMEOUT_ERROR,
      RETRY_CONDITIONS.SERVER_ERROR,
    ],
  },

  // 令牌刷新配置
  tokenRefresh: {
    enabled: true,
    threshold: 5 * 60 * 1000, // 5分钟
  },

  // 错误处理配置
  errorHandling: {
    showNotifications: true,
    logErrors: true,
  },
}

/**
 * 统一HTTP客户端类
 */
export class UnifiedHttpClient {
  constructor(options = {}) {
    // 合并配置
    this.config = {
      ...CLIENT_CONFIG,
      ...options,
    }

    // 创建axios实例
    this.instance = axios.create({
      timeout: this.config.timeout,
      baseURL: this.config.baseURL,
    })

    // 创建重试管理器
    this.retryManager = new RetryManager(this.config.retry)

    // 设置拦截器
    this.setupInterceptors()

    // 统计信息
    this.stats = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      retriedRequests: 0,
      tokenRefreshes: 0,
    }
  }

  /**
   * 设置拦截器
   */
  setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(async (config) => {
      this.stats.totalRequests++

      try {
        // 应用增强版请求拦截器
        const enhancedConfig = enhancedRequestInterceptor(config)

        // 处理令牌刷新
        if (this.config.tokenRefresh.enabled && !this.isWhitelistedPath(config.url)) {
          const refreshedToken = await this.handleTokenRefresh(enhancedConfig)
          if (refreshedToken) {
            enhancedConfig.headers.Authorization = `Bearer ${refreshedToken}`
            enhancedConfig.headers.token = refreshedToken
          }
        }

        return enhancedConfig
      } catch (error) {
        return enhancedRequestErrorInterceptor(error)
      }
    }, enhancedRequestErrorInterceptor)

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response) => {
        this.stats.successfulRequests++
        return enhancedResponseInterceptor(response)
      },
      async (error) => {
        this.stats.failedRequests++

        try {
          // 处理令牌刷新相关的401错误
          if (this.isTokenRefreshError(error)) {
            const retryResult = await this.handleTokenRefreshRetry(error)
            if (retryResult) {
              return retryResult
            }
          }

          // 处理重试逻辑
          if (this.shouldRetryRequest(error)) {
            this.stats.retriedRequests++
            return await this.retryRequest(error)
          }

          // 应用增强版错误拦截器
          return await enhancedResponseErrorInterceptor(error)
        } catch (handlerError) {
          // 使用错误中心处理
          await errorCenter.handleError(handlerError, {
            originalError: error,
            requestConfig: error.config,
          })

          return Promise.reject(handlerError)
        }
      }
    )
  }

  /**
   * 处理令牌刷新
   */
  async handleTokenRefresh(config) {
    try {
      if (tokenRefreshManager.shouldRefreshToken()) {
        console.log('[UnifiedClient] 检测到令牌需要刷新')
        const refreshedToken = await tokenRefreshManager.getRefreshedToken()
        this.stats.tokenRefreshes++
        return refreshedToken
      }
      return null
    } catch (error) {
      console.error('[UnifiedClient] 令牌刷新失败:', error)
      return null
    }
  }

  /**
   * 检查是否为令牌刷新错误
   */
  isTokenRefreshError(error) {
    return (
      error.response &&
      error.response.status === 401 &&
      this.config.tokenRefresh.enabled &&
      !this.isWhitelistedPath(error.config?.url)
    )
  }

  /**
   * 处理令牌刷新重试
   */
  async handleTokenRefreshRetry(error) {
    try {
      console.log('[UnifiedClient] 尝试刷新令牌后重试请求')

      const refreshResult = await tokenRefreshManager.refreshToken()

      if (refreshResult.success) {
        // 更新请求头
        error.config.headers.Authorization = `Bearer ${refreshResult.token}`
        error.config.headers.token = refreshResult.token

        // 重试原请求
        return await this.instance.request(error.config)
      }

      return null
    } catch (refreshError) {
      console.error('[UnifiedClient] 令牌刷新重试失败:', refreshError)
      return null
    }
  }

  /**
   * 检查是否应该重试请求
   */
  shouldRetryRequest(error) {
    // 避免重复重试
    if (error.config?.__retryCount >= this.config.retry.maxRetries) {
      return false
    }

    return this.retryManager.checkRetryConditions(error, this.config.retry.conditions)
  }

  /**
   * 重试请求
   */
  async retryRequest(error) {
    const config = error.config
    config.__retryCount = (config.__retryCount || 0) + 1

    const delay = this.retryManager.calculateDelay(config.__retryCount, this.config.retry)

    console.log(
      `[UnifiedClient] 重试请求 (${config.__retryCount}/${this.config.retry.maxRetries}), 延迟: ${delay}ms`
    )

    // 等待延迟
    await new Promise((resolve) => setTimeout(resolve, delay))

    // 重试请求
    return this.instance.request(config)
  }

  /**
   * 检查是否为白名单路径
   */
  isWhitelistedPath(url) {
    if (!url) return false

    const whitelistPaths = [
      '/api/v2/auth/login',
      '/api/v2/auth/register',
      '/api/v2/auth/refresh',
      '/api/v2/health',
    ]

    return whitelistPaths.some((path) => url.includes(path))
  }

  /**
   * GET请求
   */
  async get(url, config = {}) {
    return this.instance.get(url, config)
  }

  /**
   * POST请求
   */
  async post(url, data = {}, config = {}) {
    return this.instance.post(url, data, config)
  }

  /**
   * PUT请求
   */
  async put(url, data = {}, config = {}) {
    return this.instance.put(url, data, config)
  }

  /**
   * DELETE请求
   */
  async delete(url, config = {}) {
    return this.instance.delete(url, config)
  }

  /**
   * PATCH请求
   */
  async patch(url, data = {}, config = {}) {
    return this.instance.patch(url, data, config)
  }

  /**
   * 上传文件
   */
  async upload(url, file, config = {}) {
    const formData = new FormData()
    formData.append('file', file)

    return this.instance.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config.headers,
      },
    })
  }

  /**
   * 下载文件
   */
  async download(url, config = {}) {
    return this.instance.get(url, {
      ...config,
      responseType: 'blob',
    })
  }

  /**
   * 批量请求
   */
  async batch(requests) {
    const promises = requests.map((request) => {
      const { method, url, data, config } = request

      switch (method.toLowerCase()) {
        case 'get':
          return this.get(url, config)
        case 'post':
          return this.post(url, data, config)
        case 'put':
          return this.put(url, data, config)
        case 'delete':
          return this.delete(url, config)
        case 'patch':
          return this.patch(url, data, config)
        default:
          throw new Error(`不支持的请求方法: ${method}`)
      }
    })

    return Promise.allSettled(promises)
  }

  /**
   * 取消请求
   */
  createCancelToken() {
    return axios.CancelToken.source()
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return {
      ...this.stats,
      retryStats: this.retryManager.getStats(),
      tokenRefreshStats: tokenRefreshManager.getStats(),
      errorStats: errorCenter.getErrorStats(),
      successRate:
        this.stats.totalRequests > 0
          ? ((this.stats.successfulRequests / this.stats.totalRequests) * 100).toFixed(2) + '%'
          : '0%',
    }
  }

  /**
   * 重置统计信息
   */
  resetStats() {
    this.stats = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      retriedRequests: 0,
      tokenRefreshes: 0,
    }

    this.retryManager.resetStats()
    tokenRefreshManager.resetStats()
    errorCenter.clearHistory()
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig) {
    this.config = {
      ...this.config,
      ...newConfig,
    }

    // 更新重试管理器配置
    if (newConfig.retry) {
      this.retryManager.updateConfig(newConfig.retry)
    }

    // 更新令牌刷新管理器配置
    if (newConfig.tokenRefresh) {
      tokenRefreshManager.updateConfig(newConfig.tokenRefresh)
    }
  }

  /**
   * 健康检查
   */
  async healthCheck() {
    try {
      const response = await this.get('/health', { timeout: 5000 })
      return {
        status: 'healthy',
        response: response.data,
        timestamp: new Date().toISOString(),
      }
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString(),
      }
    }
  }
}

/**
 * 创建HTTP客户端实例
 */
export function createHttpClient(options = {}) {
  return new UnifiedHttpClient(options)
}

/**
 * 创建默认的HTTP客户端
 */
export const httpClient = createHttpClient({
  baseURL:
    import.meta.env.VITE_USE_PROXY === 'true' ? '/api/v2' : `${import.meta.env.VITE_BASE_API}/v2`,
})

/**
 * 便捷的请求方法
 */
export const request = {
  get: (url, config) => httpClient.get(url, config),
  post: (url, data, config) => httpClient.post(url, data, config),
  put: (url, data, config) => httpClient.put(url, data, config),
  delete: (url, config) => httpClient.delete(url, config),
  patch: (url, data, config) => httpClient.patch(url, data, config),
  upload: (url, file, config) => httpClient.upload(url, file, config),
  download: (url, config) => httpClient.download(url, config),
  batch: (requests) => httpClient.batch(requests),
}

// 在开发环境下暴露调试工具
if (import.meta.env.MODE === 'development') {
  window.httpClient = httpClient
  window.httpStats = () => httpClient.getStats()
  window.httpHealth = () => httpClient.healthCheck()

  console.log('🔧 统一HTTP客户端调试工具已挂载到window对象')
  console.log('可用命令：httpClient, httpStats(), httpHealth()')
}

export default httpClient
