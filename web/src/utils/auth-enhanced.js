/**
 * 增强版认证管理工具
 * 提供更强的token管理和调试能力
 *
 * @author DeviceMonitorV2 Team
 * @date 2025-01-11
 */

import { safeParseJWTPayload } from './jwt-decoder-fix'

const TOKEN_KEY = 'access_token'
const USER_INFO_KEY = 'userInfo'
const AUTH_DEBUG_KEY = 'auth_debug'

/**
 * 增强版token设置
 * @param {string} token - JWT token
 * @param {Object} userInfo - 用户信息对象
 * @returns {boolean} 是否设置成功
 */
export function setTokenEnhanced(token, userInfo = null) {
  try {
    // 验证token格式
    if (!token || typeof token !== 'string') {
      console.error('❌ Token格式无效', { token })
      return false
    }

    // 保存token
    localStorage.setItem(TOKEN_KEY, token)

    // 保存用户信息
    if (userInfo) {
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo))
    }

    // 保存调试信息
    const debugInfo = {
      setTime: new Date().toISOString(),
      tokenLength: token.length,
      tokenPrefix: token.substring(0, 20),
      userAgent: navigator.userAgent,
      url: window.location.href,
      userInfo: userInfo ? Object.keys(userInfo) : null,
    }
    localStorage.setItem(AUTH_DEBUG_KEY, JSON.stringify(debugInfo))

    console.log('✅ Token已保存（增强版）', debugInfo)

    // 验证保存是否成功
    const savedToken = localStorage.getItem(TOKEN_KEY)
    if (savedToken !== token) {
      console.error('❌ Token保存验证失败', { original: token.length, saved: savedToken?.length })
      return false
    }

    return true
  } catch (error) {
    console.error('❌ Token保存失败', error)
    return false
  }
}

/**
 * 增强版token获取
 * @returns {string|null} JWT token或null
 */
export function getTokenEnhanced() {
  try {
    const token = localStorage.getItem(TOKEN_KEY)
    const debugInfo = localStorage.getItem(AUTH_DEBUG_KEY)

    if (token) {
      console.log('✅ Token获取成功', {
        tokenLength: token.length,
        tokenPrefix: token.substring(0, 20),
        debugInfo: debugInfo ? JSON.parse(debugInfo) : null,
      })
      return token
    } else {
      console.warn('⚠️ 未找到Token', {
        localStorage: Object.keys(localStorage),
        debugInfo: debugInfo ? JSON.parse(debugInfo) : null,
      })
      return null
    }
  } catch (error) {
    console.error('❌ Token获取失败', error)
    return null
  }
}

/**
 * 认证状态诊断
 * @returns {Object} 诊断结果对象
 */
export function diagnoseAuthState() {
  const token = localStorage.getItem(TOKEN_KEY)
  const userInfo = localStorage.getItem(USER_INFO_KEY)
  const debugInfo = localStorage.getItem(AUTH_DEBUG_KEY)

  const diagnosis = {
    hasToken: !!token,
    hasUserInfo: !!userInfo,
    hasDebugInfo: !!debugInfo,
    tokenValid: false,
    tokenExpired: false,
    localStorage: Object.keys(localStorage),
    timestamp: new Date().toISOString(),
  }

  if (token) {
    try {
      const parts = token.split('.')
      if (parts.length === 3) {
        const payload = safeParseJWTPayload(token)
        diagnosis.tokenValid = true
        diagnosis.tokenExpired = payload.exp * 1000 < Date.now()
        diagnosis.tokenPayload = {
          username: payload.username,
          userId: payload.user_id,
          expiresAt: new Date(payload.exp * 1000).toISOString(),
          issuedAt: payload.iat ? new Date(payload.iat * 1000).toISOString() : null,
        }
      }
    } catch (e) {
      diagnosis.tokenParseError = e.message
    }
  }

  if (debugInfo) {
    try {
      diagnosis.debugInfo = JSON.parse(debugInfo)
    } catch (e) {
      diagnosis.debugParseError = e.message
    }
  }

  console.log('🔍 认证状态诊断', diagnosis)
  return diagnosis
}

/**
 * 清除认证状态
 * @returns {Object} 清除前的状态信息
 */
export function clearAuthStateEnhanced() {
  const beforeState = {
    hasToken: !!localStorage.getItem(TOKEN_KEY),
    hasUserInfo: !!localStorage.getItem(USER_INFO_KEY),
    hasDebugInfo: !!localStorage.getItem(AUTH_DEBUG_KEY),
    timestamp: new Date().toISOString(),
  }

  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_INFO_KEY)
  localStorage.removeItem(AUTH_DEBUG_KEY)

  console.log('🧹 认证状态已清除', { beforeState })
  return beforeState
}

/**
 * 检查token是否即将过期
 * @param {number} warningMinutes - 提前多少分钟警告，默认30分钟
 * @returns {Object} 检查结果
 */
export function checkTokenExpiration(warningMinutes = 30) {
  const token = localStorage.getItem(TOKEN_KEY)

  if (!token) {
    return { hasToken: false, expired: true, warning: false }
  }

  try {
    const parts = token.split('.')
    if (parts.length !== 3) {
      return { hasToken: true, expired: true, warning: false, error: 'Invalid token format' }
    }

    const payload = safeParseJWTPayload(token)
    const now = Date.now()
    const expTime = payload.exp * 1000
    const warningTime = expTime - warningMinutes * 60 * 1000

    return {
      hasToken: true,
      expired: now >= expTime,
      warning: now >= warningTime && now < expTime,
      expiresAt: new Date(expTime).toISOString(),
      minutesUntilExpiry: Math.floor((expTime - now) / (60 * 1000)),
    }
  } catch (error) {
    return { hasToken: true, expired: true, warning: false, error: error.message }
  }
}

/**
 * 自动刷新token（如果支持）
 * @returns {Promise<boolean>} 是否刷新成功
 */
export async function autoRefreshToken() {
  // 这里可以实现自动刷新逻辑
  // 目前返回false，表示不支持自动刷新
  console.log('ℹ️ 自动刷新token功能暂未实现')
  return false
}

/**
 * 获取用户信息
 * @returns {Object|null} 用户信息对象或null
 */
export function getUserInfoEnhanced() {
  try {
    const userInfo = localStorage.getItem(USER_INFO_KEY)
    return userInfo ? JSON.parse(userInfo) : null
  } catch (error) {
    console.error('❌ 获取用户信息失败', error)
    return null
  }
}

/**
 * 导出诊断报告
 * @returns {string} JSON格式的诊断报告
 */
export function exportDiagnosticReport() {
  const diagnosis = diagnoseAuthState()
  const expiration = checkTokenExpiration()

  const report = {
    ...diagnosis,
    expiration,
    browser: {
      userAgent: navigator.userAgent,
      language: navigator.language,
      cookieEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
    },
    page: {
      url: window.location.href,
      referrer: document.referrer,
      title: document.title,
    },
    reportTime: new Date().toISOString(),
  }

  console.log('📋 诊断报告已生成', report)
  return JSON.stringify(report, null, 2)
}

// 在开发环境下，将诊断函数挂载到window对象，方便调试
if (process.env.NODE_ENV === 'development') {
  window.authDiagnose = diagnoseAuthState
  window.authClear = clearAuthStateEnhanced
  window.authReport = exportDiagnosticReport
  window.authCheck = checkTokenExpiration

  console.log('🔧 开发模式：认证调试工具已挂载到window对象')
  console.log('可用命令：authDiagnose(), authClear(), authReport(), authCheck()')
}
