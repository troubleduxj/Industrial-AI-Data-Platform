/**
 * 令牌刷新管理器
 * 处理JWT令牌的自动刷新和队列管理
 */

import { getTokenEnhanced, setTokenEnhanced, checkTokenExpiration } from '@/utils/auth-enhanced'
import { useUserStore } from '@/store'

/**
 * 令牌刷新管理器类
 */
export class TokenRefreshManager {
  constructor() {
    // 刷新状态
    this.isRefreshing = false
    this.refreshPromise = null

    // 等待队列
    this.pendingRequests = []

    // 配置
    this.config = {
      refreshEndpoint: '/api/v2/auth/refresh',
      maxRetries: 3,
      retryDelay: 1000,
      refreshThreshold: 5 * 60 * 1000, // 5分钟
    }

    // 统计信息
    this.stats = {
      totalRefreshAttempts: 0,
      successfulRefreshes: 0,
      failedRefreshes: 0,
      lastRefreshTime: null,
      lastRefreshDuration: 0,
    }

    // 启动定期检查
    this.startPeriodicCheck()
  }

  /**
   * 检查令牌是否需要刷新
   */
  shouldRefreshToken() {
    const expirationCheck = checkTokenExpiration()

    if (!expirationCheck.hasToken) {
      return false
    }

    if (expirationCheck.expired) {
      return true
    }

    // 检查是否在刷新阈值内
    const minutesUntilExpiry = expirationCheck.minutesUntilExpiry || 0
    const thresholdMinutes = this.config.refreshThreshold / (60 * 1000)

    return minutesUntilExpiry <= thresholdMinutes
  }

  /**
   * 刷新令牌
   */
  async refreshToken() {
    // 如果已经在刷新中，返回现有的Promise
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise
    }

    // 开始刷新流程
    this.isRefreshing = true
    this.refreshPromise = this.performRefresh()

    try {
      const result = await this.refreshPromise
      return result
    } finally {
      this.isRefreshing = false
      this.refreshPromise = null
    }
  }

  /**
   * 执行实际的刷新操作
   */
  async performRefresh() {
    const startTime = Date.now()
    this.stats.totalRefreshAttempts++

    try {
      console.log('[TokenRefresh] 开始刷新令牌...')

      // 获取当前令牌
      const currentToken = getTokenEnhanced()
      if (!currentToken) {
        throw new Error('没有可用的令牌进行刷新')
      }

      // 调用刷新API
      const newTokenData = await this.callRefreshAPI(currentToken)

      if (!newTokenData || !newTokenData.access_token) {
        throw new Error('刷新API返回无效数据')
      }

      // 保存新令牌
      const saveSuccess = setTokenEnhanced(newTokenData.access_token, newTokenData.user_info)
      if (!saveSuccess) {
        throw new Error('新令牌保存失败')
      }

      // 更新统计信息
      this.stats.successfulRefreshes++
      this.stats.lastRefreshTime = new Date().toISOString()
      this.stats.lastRefreshDuration = Date.now() - startTime

      console.log('[TokenRefresh] 令牌刷新成功', {
        duration: this.stats.lastRefreshDuration,
        newTokenLength: newTokenData.access_token.length,
      })

      // 处理等待队列
      this.processQueue(null, newTokenData.access_token)

      return {
        success: true,
        token: newTokenData.access_token,
        userInfo: newTokenData.user_info,
      }
    } catch (error) {
      console.error('[TokenRefresh] 令牌刷新失败:', error)

      // 更新统计信息
      this.stats.failedRefreshes++
      this.stats.lastRefreshDuration = Date.now() - startTime

      // 处理等待队列
      this.processQueue(error, null)

      return {
        success: false,
        error: error.message,
      }
    }
  }

  /**
   * 调用刷新API
   */
  async callRefreshAPI(currentToken) {
    const { default: axios } = await import('axios')

    try {
      const response = await axios.post(
        this.config.refreshEndpoint,
        {
          refresh_token: currentToken, // 使用当前令牌作为刷新令牌
        },
        {
          headers: {
            Authorization: `Bearer ${currentToken}`,
            'Content-Type': 'application/json',
          },
          timeout: 10000, // 10秒超时
        }
      )

      if (response.data && response.data.success) {
        return response.data.data
      } else {
        throw new Error(response.data?.message || '刷新API返回失败状态')
      }
    } catch (error) {
      if (error.response) {
        const { status, data } = error.response

        // 如果是401错误，说明刷新令牌也过期了
        if (status === 401) {
          throw new Error('刷新令牌已过期，需要重新登录')
        }

        throw new Error(data?.message || `刷新API请求失败 (${status})`)
      } else {
        throw new Error(`刷新API网络错误: ${error.message}`)
      }
    }
  }

  /**
   * 添加请求到等待队列
   */
  addToQueue(resolve, reject) {
    this.pendingRequests.push({ resolve, reject })
  }

  /**
   * 处理等待队列
   */
  processQueue(error, token = null) {
    this.pendingRequests.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error)
      } else {
        resolve(token)
      }
    })

    this.pendingRequests = []
  }

  /**
   * 获取新令牌（用于请求拦截器）
   */
  async getRefreshedToken() {
    // 如果正在刷新，加入等待队列
    if (this.isRefreshing) {
      return new Promise((resolve, reject) => {
        this.addToQueue(resolve, reject)
      })
    }

    // 检查是否需要刷新
    if (!this.shouldRefreshToken()) {
      return getTokenEnhanced()
    }

    // 执行刷新
    const result = await this.refreshToken()

    if (result.success) {
      return result.token
    } else {
      throw new Error(result.error)
    }
  }

  /**
   * 启动定期检查
   */
  startPeriodicCheck() {
    // 每分钟检查一次令牌状态
    setInterval(() => {
      this.checkTokenStatus()
    }, 60000)
  }

  /**
   * 检查令牌状态
   */
  async checkTokenStatus() {
    try {
      const expirationCheck = checkTokenExpiration()

      if (!expirationCheck.hasToken) {
        return
      }

      // 如果令牌即将过期且没有在刷新中，主动刷新
      if (this.shouldRefreshToken() && !this.isRefreshing) {
        console.log('[TokenRefresh] 检测到令牌即将过期，主动刷新')
        await this.refreshToken()
      }
    } catch (error) {
      console.error('[TokenRefresh] 定期检查失败:', error)
    }
  }

  /**
   * 手动触发刷新
   */
  async forceRefresh() {
    console.log('[TokenRefresh] 手动触发令牌刷新')
    return await this.refreshToken()
  }

  /**
   * 停止刷新流程
   */
  stopRefresh() {
    this.isRefreshing = false
    this.refreshPromise = null

    // 清空等待队列
    this.processQueue(new Error('刷新流程已停止'), null)
  }

  /**
   * 获取统计信息
   */
  getStats() {
    const expirationCheck = checkTokenExpiration()

    return {
      ...this.stats,
      isRefreshing: this.isRefreshing,
      pendingRequests: this.pendingRequests.length,
      tokenStatus: {
        hasToken: expirationCheck.hasToken,
        expired: expirationCheck.expired,
        warning: expirationCheck.warning,
        minutesUntilExpiry: expirationCheck.minutesUntilExpiry,
        expiresAt: expirationCheck.expiresAt,
      },
      successRate:
        this.stats.totalRefreshAttempts > 0
          ? ((this.stats.successfulRefreshes / this.stats.totalRefreshAttempts) * 100).toFixed(2) +
            '%'
          : '0%',
    }
  }

  /**
   * 重置统计信息
   */
  resetStats() {
    this.stats = {
      totalRefreshAttempts: 0,
      successfulRefreshes: 0,
      failedRefreshes: 0,
      lastRefreshTime: null,
      lastRefreshDuration: 0,
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
   * 检查刷新功能是否可用
   */
  isRefreshAvailable() {
    try {
      const userStore = useUserStore()

      // 检查用户是否已登录
      if (!userStore.isLoggedIn) {
        return false
      }

      // 检查是否有有效令牌
      const expirationCheck = checkTokenExpiration()
      if (!expirationCheck.hasToken) {
        return false
      }

      // 检查是否支持刷新API
      // 这里可以添加更多的检查逻辑

      return true
    } catch (error) {
      console.error('[TokenRefresh] 检查刷新可用性失败:', error)
      return false
    }
  }
}

// 创建全局令牌刷新管理器实例
export const tokenRefreshManager = new TokenRefreshManager()

// 便捷方法
export function refreshToken() {
  return tokenRefreshManager.refreshToken()
}

export function getRefreshedToken() {
  return tokenRefreshManager.getRefreshedToken()
}

export function getRefreshStats() {
  return tokenRefreshManager.getStats()
}

export function forceRefreshToken() {
  return tokenRefreshManager.forceRefresh()
}

// 在开发环境下暴露调试工具
if (import.meta.env.MODE === 'development') {
  window.tokenRefresh = tokenRefreshManager
  window.refreshStats = getRefreshStats
  window.forceRefresh = forceRefreshToken

  console.log('🔧 令牌刷新调试工具已挂载到window对象')
  console.log('可用命令：tokenRefresh, refreshStats(), forceRefresh()')
}
