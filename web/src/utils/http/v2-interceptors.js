/**
 * API v2版本的HTTP拦截器
 * 支持标准化响应格式和增强的错误处理
 */
import { getToken } from '@/utils'
import { getTokenEnhanced } from '@/utils/auth-enhanced'
import { resolveResError } from './helpers'
import { useUserStore } from '@/store'
import ErrorHandler from '@/utils/error-handler'
import { safeParseJWTPayload, checkTokenExpiration } from '@/utils/jwt-decoder-fix'
import axios from 'axios'
import { mockRequestInterceptor } from '@/utils/mock-interceptor'

// Mock请求拦截器仍然保留，但adapter已移除
// 这样Mock只在请求拦截器中标记请求，不干扰实际的网络请求

export function reqResolveV2(config) {
  try {
    // Mock拦截器 - 在其他处理之前检查
    config = mockRequestInterceptor(config)
    
    // 处理不需要token的请求
    if (config.noNeedToken) {
      return config
    }

    // 检查是否正在登出，如果是则拒绝权限相关的API请求
    const userStore = useUserStore()
    if (userStore.isLoggingOut && config.url && config.url.includes('/auth/user/apis')) {
      console.log('[API v2 Interceptor] 正在登出中，拒绝权限API请求:', config.url)
      return Promise.reject(new Error('正在登出中，取消权限API请求'))
    }

    // 使用增强版token获取，提供更好的调试信息
    const token = getTokenEnhanced()

    // 如果增强版获取失败，尝试使用原版本作为备用
    const fallbackToken = token || getToken()
    const finalToken = fallbackToken

    console.log(
      `[API v2 Interceptor] 获取到的token: ${
        finalToken ? finalToken.substring(0, 20) + '...' : 'null'
      }`
    )
    console.log(`[API v2 Interceptor] 请求URL: ${config.url}`)
    console.log(`[API v2 Interceptor] 请求方法: ${config.method}`)

    // 验证token是否有效（简单检查）
    if (finalToken) {
      try {
        // 检查token格式（JWT应该有3个部分，用.分隔）
        const tokenParts = finalToken.split('.')
        if (tokenParts.length !== 3) {
          console.error(`[API v2 Interceptor] Token格式无效，部分数量: ${tokenParts.length}`)
          throw new Error('Invalid token format')
        }

        // 使用安全的JWT解码方法，避免'Invalid crypto padding'错误
        const payload = safeParseJWTPayload(finalToken)
        const expirationCheck = checkTokenExpiration(finalToken)

        if (expirationCheck.expired) {
          console.error(`[API v2 Interceptor] Token已过期，过期时间: ${expirationCheck.expiresAt}`)
          throw new Error('Token expired')
        }

        console.log(
          `[API v2 Interceptor] Token验证通过，用户: ${payload.username}, 过期时间: ${expirationCheck.expiresAt}`
        )
      } catch (tokenError) {
        console.error(`[API v2 Interceptor] Token验证失败:`, tokenError)
        // Token验证失败时，不在拦截器中自动重定向
        // 让请求继续进行，由各个页面自己处理401错误
        console.warn(`[API v2 Interceptor] 检测到可能的token问题，但继续发送请求让后端验证`)
        // 对于token验证错误，继续发送请求让后端处理
      }

      // 确保headers对象存在
      if (!config.headers) {
        config.headers = {}
      }

      // 设置认证头 - 同时设置Authorization和token头以确保兼容性
      config.headers.Authorization = `Bearer ${finalToken}`
      config.headers.token = finalToken // 后端期望的token头
      console.log(
        `[API v2 Interceptor] 已设置Authorization头: Bearer ${finalToken.substring(0, 20)}...`
      )
      console.log(`[API v2 Interceptor] 已设置token头: ${finalToken.substring(0, 20)}...`)
      console.log(`[API v2 Interceptor] 完整请求头:`, JSON.stringify(config.headers, null, 2))
    } else {
      console.warn(`[API v2 Interceptor] 警告：没有获取到token，请求可能会失败`)
      console.warn(`[API v2 Interceptor] localStorage内容:`, localStorage.getItem('access_token'))
    }

    // URL路径自动修正逻辑（增强版）
    if (config.url) {
      const originalUrl = config.url
      config.url = normalizeApiUrl(config.url)

      // 记录URL修正日志
      if (originalUrl !== config.url) {
        console.log(`[API v2] URL路径已修正: ${originalUrl} -> ${config.url}`)
      }
    }

    // 确保API版本头的正确设置
    if (config.url && config.url.includes('/api/v2/')) {
      config.headers['API-Version'] = 'v2'
      config.headers['Content-Type'] = config.headers['Content-Type'] || 'application/json'
    }

    // 添加请求ID用于追踪
    config.headers['X-Request-ID'] = generateRequestId()

    // 添加时间戳用于性能监控
    config.metadata = {
      startTime: Date.now(),
      requestId: config.headers['X-Request-ID'],
    }

    // 记录请求日志
    logRequest(config)

    return config
  } catch (error) {
    console.error('[API v2] 请求拦截器处理失败:', error)
    // 即使处理失败，也要返回原始配置以避免请求完全失败
    return config
  }
}

/**
 * 标准化API URL
 * @param {string} url - 原始URL
 * @returns {string} 标准化后的URL
 */
function normalizeApiUrl(url) {
  if (!url || typeof url !== 'string') {
    return url
  }

  // 如果是完整的HTTP URL，不进行处理
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }

  let normalizedUrl = url.trim()

  // 移除重复的API路径前缀（更全面的处理）
  const duplicatePatterns = [
    { pattern: /^\/api\/v1\/api\/v2\//, replacement: '/api/v2/' },
    { pattern: /^\/api\/v2\/api\/v1\//, replacement: '/api/v2/' },
    { pattern: /^\/api\/v2\/api\/v2\//, replacement: '/api/v2/' },
    { pattern: /^\/api\/v1\/api\/v1\//, replacement: '/api/v1/' },
  ]

  duplicatePatterns.forEach(({ pattern, replacement }) => {
    normalizedUrl = normalizedUrl.replace(pattern, replacement)
  })

  // 自动转换v1路径到v2
  if (normalizedUrl.startsWith('/api/v1/')) {
    normalizedUrl = normalizedUrl.replace(/^\/api\/v1\//, '/api/v2/')
  }

  // 不需要自动添加/api/v2前缀，因为requestV2的baseURL已经是/api/v2
  // 只需要确保路径格式正确即可

  // 移除多余的斜杠
  normalizedUrl = normalizedUrl.replace(/\/+/g, '/')

  // 注意：不要移除API路径末尾的斜杠，因为某些API端点需要斜杠
  // 例如：/users/ 和 /users 可能是不同的端点

  return normalizedUrl
}

/**
 * 生成请求ID
 * @returns {string} 请求ID
 */
function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 记录请求日志
 * @param {Object} config - 请求配置
 */
function logRequest(config) {
  if (import.meta.env.MODE === 'development') {
    console.log(`[API v2 Request] ${config.method?.toUpperCase()} ${config.url}`, {
      requestId: config.metadata?.requestId,
      headers: config.headers,
      params: config.params,
      data: config.data,
    })
  }
}

export function reqRejectV2(error) {
  return Promise.reject(error)
}

export function resResolveV2(response) {
  try {
    const { data, status, statusText, config } = response

    // 记录响应时间
    const responseTime = config.metadata ? Date.now() - config.metadata.startTime : 0

    // 记录成功响应日志
    logResponse(response, responseTime)

    // v2版本使用success字段判断成功/失败
    if (data?.success === false) {
      const code = data?.code ?? status
      const message = data?.message || resolveResError(code, statusText)

      // 记录业务错误日志
      logBusinessError(response, { code, message })

      // 显示错误消息
      window.$message?.error(message, { keepAliveOnHover: true })

      // 返回标准化的错误信息
      return Promise.reject({
        code,
        message,
        error: data,
        details: data?.details, // v2版本的详细错误信息
        requestId: config.headers?.['X-Request-ID'],
        responseTime,
      })
    }

    // 成功响应，返回标准化格式
    const result = {
      ...data,
      // 为了兼容性，同时提供v1格式的字段
      code: data.code,
      msg: data.message,
      data: data.data,
      // 添加元数据
      _metadata: {
        requestId: config.headers?.['X-Request-ID'],
        responseTime,
        timestamp: new Date().toISOString(),
      },
    }

    return Promise.resolve(result)
  } catch (error) {
    console.error('[API v2] 响应拦截器处理失败:', error)
    // 返回原始响应数据
    return Promise.resolve(response.data)
  }
}

export async function resRejectV2(error) {
  try {
    // 计算响应时间
    const responseTime = error.config?.metadata ? Date.now() - error.config.metadata.startTime : 0
    const requestId = error.config?.headers?.['X-Request-ID']

    // 增强错误对象，添加元数据
    const enhancedError = {
      ...error,
      responseTime,
      requestId,
      config: error.config,
    }

    // 使用统一的ErrorHandler处理错误
    const handledError = await ErrorHandler.handle(enhancedError, {
      silent: false, // 允许显示错误消息
    })

    // 记录HTTP错误日志（保留原有的详细日志记录）
    logHttpError(error, responseTime)

    return Promise.reject(handledError)
  } catch (handlerError) {
    console.error('[API v2] 错误处理器失败:', handlerError)

    // 最后的兜底处理
    const fallbackMessage = '系统错误，请联系管理员'
    window.$message?.error(fallbackMessage)

    return Promise.reject({
      code: 'HANDLER_ERROR',
      message: fallbackMessage,
      error: handlerError,
      originalError: error,
    })
  }
}

/**
 * 记录响应日志
 * @param {Object} response - 响应对象
 * @param {number} responseTime - 响应时间
 */
function logResponse(response, responseTime) {
  if (import.meta.env.MODE === 'development') {
    const { config, status, data } = response
    console.log(`[API v2 Response] ${config.method?.toUpperCase()} ${config.url} - ${status}`, {
      requestId: config.headers?.['X-Request-ID'],
      responseTime: `${responseTime}ms`,
      dataSize: JSON.stringify(data).length,
      success: data?.success,
    })
  }
}

/**
 * 记录业务错误日志
 * @param {Object} response - 响应对象
 * @param {Object} errorInfo - 错误信息
 */
function logBusinessError(response, errorInfo) {
  const { config, data } = response
  console.warn(`[API v2 Business Error] ${config.method?.toUpperCase()} ${config.url}`, {
    requestId: config.headers?.['X-Request-ID'],
    code: errorInfo.code,
    message: errorInfo.message,
    details: data?.details,
  })
}

/**
 * 记录网络错误日志
 * @param {Object} error - 错误对象
 * @param {Object} errorInfo - 错误信息
 */
function logNetworkError(error, errorInfo) {
  console.error(`[API v2 Network Error]`, {
    requestId: errorInfo.requestId,
    code: errorInfo.code,
    message: errorInfo.message,
    responseTime: `${errorInfo.responseTime}ms`,
    url: error.config?.url,
    method: error.config?.method,
  })
}

/**
 * 记录HTTP错误日志
 * @param {Object} error - 错误对象
 * @param {number} responseTime - 响应时间
 */
function logHttpError(error, responseTime) {
  const { config, response } = error
  const status = response?.status || 'Network Error'
  const statusText = response?.statusText || 'Connection Failed'

  console.error(`[API v2 HTTP Error] ${config?.method?.toUpperCase()} ${config?.url} - ${status}`, {
    requestId: config?.headers?.['X-Request-ID'],
    status: status,
    statusText: statusText,
    responseTime: `${responseTime}ms`,
    data: response?.data,
    errorType: response ? 'HTTP_ERROR' : 'NETWORK_ERROR',
  })
}

// 创建v2版本的axios实例
export function createAxiosV2(options = {}) {
  const defaultOptions = {
    timeout: 60000,
    // 完全禁用Mock适配器，使用axios默认行为
    // adapter配置被移除，让axios使用内置的xhr/http adapter
  }

  const service = axios.create({
    ...defaultOptions,
    ...options,
  })

  service.interceptors.request.use(reqResolveV2, reqRejectV2)
  service.interceptors.response.use(resResolveV2, resRejectV2)

  return service
}

// 创建v2版本的请求实例
// 注意：Vite环境变量可能是字符串或布尔值，需要容错处理
const useProxy = import.meta.env.VITE_USE_PROXY === 'true' || import.meta.env.VITE_USE_PROXY === true
const baseURL = useProxy ? '/api/v2' : `${import.meta.env.VITE_BASE_API || '/api'}/v2`

console.log('[HTTP Config] 代理配置:', {
  VITE_USE_PROXY: import.meta.env.VITE_USE_PROXY,
  useProxy: useProxy,
  baseURL: baseURL,
  VITE_BASE_API: import.meta.env.VITE_BASE_API
})

export const requestV2 = createAxiosV2({
  baseURL: baseURL
})
