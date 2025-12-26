/**
 * 请求重试管理器
 * 处理网络请求的智能重试逻辑
 */

/**
 * 重试策略枚举
 */
export const RETRY_STRATEGIES = {
  EXPONENTIAL_BACKOFF: 'EXPONENTIAL_BACKOFF', // 指数退避
  LINEAR_BACKOFF: 'LINEAR_BACKOFF', // 线性退避
  FIXED_DELAY: 'FIXED_DELAY', // 固定延迟
  IMMEDIATE: 'IMMEDIATE', // 立即重试
}

/**
 * 重试条件枚举
 */
export const RETRY_CONDITIONS = {
  NETWORK_ERROR: 'NETWORK_ERROR', // 网络错误
  TIMEOUT_ERROR: 'TIMEOUT_ERROR', // 超时错误
  SERVER_ERROR: 'SERVER_ERROR', // 服务器错误（5xx）
  RATE_LIMIT: 'RATE_LIMIT', // 限流错误（429）
  CUSTOM: 'CUSTOM', // 自定义条件
}

/**
 * 请求重试管理器类
 */
export class RetryManager {
  constructor(options = {}) {
    // 默认配置
    this.config = {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 30000,
      strategy: RETRY_STRATEGIES.EXPONENTIAL_BACKOFF,
      conditions: [
        RETRY_CONDITIONS.NETWORK_ERROR,
        RETRY_CONDITIONS.TIMEOUT_ERROR,
        RETRY_CONDITIONS.SERVER_ERROR,
      ],
      retryCondition: null, // 自定义重试条件函数
      onRetry: null, // 重试回调函数
      ...options,
    }

    // 统计信息
    this.stats = {
      totalRequests: 0,
      retriedRequests: 0,
      successfulRetries: 0,
      failedRetries: 0,
      totalRetryAttempts: 0,
      averageRetryCount: 0,
    }

    // 活跃重试记录
    this.activeRetries = new Map()
  }

  /**
   * 执行带重试的请求
   */
  async executeWithRetry(requestFunction, config = {}) {
    const requestId = this.generateRequestId()
    const mergedConfig = { ...this.config, ...config }

    this.stats.totalRequests++

    let lastError = null
    let retryCount = 0

    // 记录重试开始
    this.activeRetries.set(requestId, {
      startTime: Date.now(),
      retryCount: 0,
      config: mergedConfig,
    })

    try {
      // 第一次尝试
      const result = await this.attemptRequest(requestFunction, requestId, retryCount)

      // 成功，清理记录
      this.activeRetries.delete(requestId)
      return result
    } catch (error) {
      lastError = error

      // 检查是否应该重试
      if (!this.shouldRetry(error, retryCount, mergedConfig)) {
        this.activeRetries.delete(requestId)
        throw error
      }

      this.stats.retriedRequests++
    }

    // 开始重试循环
    while (retryCount < mergedConfig.maxRetries) {
      retryCount++
      this.stats.totalRetryAttempts++

      // 更新活跃重试记录
      const retryRecord = this.activeRetries.get(requestId)
      if (retryRecord) {
        retryRecord.retryCount = retryCount
      }

      try {
        // 计算延迟时间
        const delay = this.calculateDelay(retryCount, mergedConfig)

        // 调用重试回调
        if (mergedConfig.onRetry) {
          await mergedConfig.onRetry(lastError, retryCount, delay)
        }

        console.log(
          `[RetryManager] 重试请求 ${requestId} (${retryCount}/${mergedConfig.maxRetries}), 延迟: ${delay}ms`
        )

        // 等待延迟
        await this.delay(delay)

        // 尝试请求
        const result = await this.attemptRequest(requestFunction, requestId, retryCount)

        // 重试成功
        this.stats.successfulRetries++
        this.updateAverageRetryCount()
        this.activeRetries.delete(requestId)

        console.log(`[RetryManager] 重试成功 ${requestId} (尝试次数: ${retryCount + 1})`)
        return result
      } catch (error) {
        lastError = error

        // 检查是否应该继续重试
        if (!this.shouldRetry(error, retryCount, mergedConfig)) {
          break
        }
      }
    }

    // 所有重试都失败了
    this.stats.failedRetries++
    this.updateAverageRetryCount()
    this.activeRetries.delete(requestId)

    console.error(`[RetryManager] 重试失败 ${requestId} (总尝试次数: ${retryCount + 1})`)

    // 抛出最后一个错误，并添加重试信息
    const enhancedError = this.enhanceError(lastError, retryCount + 1)
    throw enhancedError
  }

  /**
   * 尝试执行请求
   */
  async attemptRequest(requestFunction, requestId, retryCount) {
    const startTime = Date.now()

    try {
      const result = await requestFunction()
      const duration = Date.now() - startTime

      console.log(
        `[RetryManager] 请求成功 ${requestId} (尝试: ${retryCount + 1}, 耗时: ${duration}ms)`
      )
      return result
    } catch (error) {
      const duration = Date.now() - startTime

      console.warn(
        `[RetryManager] 请求失败 ${requestId} (尝试: ${retryCount + 1}, 耗时: ${duration}ms):`,
        error.message
      )
      throw error
    }
  }

  /**
   * 判断是否应该重试
   */
  shouldRetry(error, retryCount, config) {
    // 检查重试次数限制
    if (retryCount >= config.maxRetries) {
      return false
    }

    // 使用自定义重试条件
    if (config.retryCondition && typeof config.retryCondition === 'function') {
      return config.retryCondition(error, retryCount)
    }

    // 使用预定义的重试条件
    return this.checkRetryConditions(error, config.conditions)
  }

  /**
   * 检查重试条件
   */
  checkRetryConditions(error, conditions) {
    for (const condition of conditions) {
      if (this.matchesCondition(error, condition)) {
        return true
      }
    }
    return false
  }

  /**
   * 检查错误是否匹配特定条件
   */
  matchesCondition(error, condition) {
    switch (condition) {
      case RETRY_CONDITIONS.NETWORK_ERROR:
        return this.isNetworkError(error)

      case RETRY_CONDITIONS.TIMEOUT_ERROR:
        return this.isTimeoutError(error)

      case RETRY_CONDITIONS.SERVER_ERROR:
        return this.isServerError(error)

      case RETRY_CONDITIONS.RATE_LIMIT:
        return this.isRateLimitError(error)

      default:
        return false
    }
  }

  /**
   * 检查是否为网络错误
   */
  isNetworkError(error) {
    return (
      !error.response ||
      error.code === 'ERR_NETWORK' ||
      error.code === 'ECONNREFUSED' ||
      error.code === 'ENOTFOUND' ||
      error.message.includes('Network Error')
    )
  }

  /**
   * 检查是否为超时错误
   */
  isTimeoutError(error) {
    return (
      error.code === 'ECONNABORTED' ||
      error.message.includes('timeout') ||
      (error.response && error.response.status === 408)
    )
  }

  /**
   * 检查是否为服务器错误
   */
  isServerError(error) {
    return error.response && error.response.status >= 500 && error.response.status <= 599
  }

  /**
   * 检查是否为限流错误
   */
  isRateLimitError(error) {
    return error.response && error.response.status === 429
  }

  /**
   * 计算延迟时间
   */
  calculateDelay(retryCount, config) {
    let delay = 0

    switch (config.strategy) {
      case RETRY_STRATEGIES.EXPONENTIAL_BACKOFF:
        delay = config.baseDelay * Math.pow(2, retryCount - 1)
        break

      case RETRY_STRATEGIES.LINEAR_BACKOFF:
        delay = config.baseDelay * retryCount
        break

      case RETRY_STRATEGIES.FIXED_DELAY:
        delay = config.baseDelay
        break

      case RETRY_STRATEGIES.IMMEDIATE:
        delay = 0
        break

      default:
        delay = config.baseDelay
        break
    }

    // 添加随机抖动（避免惊群效应）
    const jitter = Math.random() * 0.1 * delay
    delay += jitter

    // 限制最大延迟
    return Math.min(delay, config.maxDelay)
  }

  /**
   * 延迟函数
   */
  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  /**
   * 增强错误对象
   */
  enhanceError(error, totalAttempts) {
    return {
      ...error,
      isRetryError: true,
      totalAttempts,
      retryExhausted: true,
      message: `${error.message} (重试 ${totalAttempts} 次后失败)`,
    }
  }

  /**
   * 生成请求ID
   */
  generateRequestId() {
    return `retry_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 更新平均重试次数
   */
  updateAverageRetryCount() {
    const totalRetries = this.stats.successfulRetries + this.stats.failedRetries
    if (totalRetries > 0) {
      this.stats.averageRetryCount = this.stats.totalRetryAttempts / totalRetries
    }
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return {
      ...this.stats,
      activeRetries: this.activeRetries.size,
      retryRate:
        this.stats.totalRequests > 0
          ? ((this.stats.retriedRequests / this.stats.totalRequests) * 100).toFixed(2) + '%'
          : '0%',
      successRate:
        this.stats.retriedRequests > 0
          ? ((this.stats.successfulRetries / this.stats.retriedRequests) * 100).toFixed(2) + '%'
          : '0%',
    }
  }

  /**
   * 获取活跃重试信息
   */
  getActiveRetries() {
    const active = []

    this.activeRetries.forEach((retry, requestId) => {
      active.push({
        requestId,
        duration: Date.now() - retry.startTime,
        retryCount: retry.retryCount,
        maxRetries: retry.config.maxRetries,
      })
    })

    return active
  }

  /**
   * 重置统计信息
   */
  resetStats() {
    this.stats = {
      totalRequests: 0,
      retriedRequests: 0,
      successfulRetries: 0,
      failedRetries: 0,
      totalRetryAttempts: 0,
      averageRetryCount: 0,
    }
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig) {
    this.config = {
      ...this.config,
      ...newConfig,
    }
  }

  /**
   * 取消所有活跃的重试
   */
  cancelAllRetries() {
    this.activeRetries.clear()
  }
}

/**
 * 创建重试装饰器
 */
export function withRetry(options = {}) {
  const retryManager = new RetryManager(options)

  return function (requestFunction) {
    return function (...args) {
      return retryManager.executeWithRetry(() => requestFunction.apply(this, args))
    }
  }
}

/**
 * 创建带重试的axios实例
 */
export function createRetryAxios(axiosInstance, retryOptions = {}) {
  const retryManager = new RetryManager(retryOptions)

  // 拦截请求，添加重试逻辑
  axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const config = error.config

      // 避免重复重试
      if (config.__isRetryRequest) {
        return Promise.reject(error)
      }

      // 标记为重试请求
      config.__isRetryRequest = true

      try {
        return await retryManager.executeWithRetry(() => axiosInstance.request(config))
      } catch (retryError) {
        return Promise.reject(retryError)
      }
    }
  )

  // 添加统计方法
  axiosInstance.getRetryStats = () => retryManager.getStats()
  axiosInstance.resetRetryStats = () => retryManager.resetStats()

  return axiosInstance
}

// 创建全局重试管理器实例
export const globalRetryManager = new RetryManager()

// 便捷方法
export function executeWithRetry(requestFunction, options = {}) {
  return globalRetryManager.executeWithRetry(requestFunction, options)
}

export function getRetryStats() {
  return globalRetryManager.getStats()
}

export function getActiveRetries() {
  return globalRetryManager.getActiveRetries()
}

// 在开发环境下暴露调试工具
if (import.meta.env.MODE === 'development') {
  window.retryManager = globalRetryManager
  window.retryStats = getRetryStats
  window.activeRetries = getActiveRetries

  console.log('🔧 重试管理器调试工具已挂载到window对象')
  console.log('可用命令：retryManager, retryStats(), activeRetries()')
}
