/**
 * 认证状态诊断工具
 * 用于快速诊断和修复认证问题
 * 更新时间: 2025-01-11
 */

/**
 * 执行完整的认证诊断
 * @returns {Object} 诊断结果
 */
export function runAuthDiagnosis() {
  const diagnosis = {
    timestamp: new Date().toISOString(),
    issues: [],
    recommendations: [],
    tokenStatus: null,
    storageStatus: null,
    userStatus: null,
  }

  console.log('🔍 开始认证状态诊断...')

  // 1. 检查token存储
  const localToken = localStorage.getItem('access_token')
  const sessionToken = sessionStorage.getItem('access_token')

  diagnosis.storageStatus = {
    localStorage: {
      hasToken: !!localToken,
      tokenLength: localToken ? localToken.length : 0,
      tokenPrefix: localToken ? localToken.substring(0, 20) : null,
    },
    sessionStorage: {
      hasToken: !!sessionToken,
      tokenLength: sessionToken ? sessionToken.length : 0,
      tokenPrefix: sessionToken ? sessionToken.substring(0, 20) : null,
    },
  }

  // 2. 检查token有效性
  const activeToken = localToken || sessionToken
  if (activeToken) {
    try {
      const tokenParts = activeToken.split('.')
      if (tokenParts.length === 3) {
        const payload = JSON.parse(atob(tokenParts[1]))
        const currentTime = Math.floor(Date.now() / 1000)
        const isExpired = payload.exp && payload.exp < currentTime

        diagnosis.tokenStatus = {
          format: 'valid',
          payload: {
            username: payload.username,
            exp: payload.exp,
            iat: payload.iat,
            expireDate: new Date(payload.exp * 1000).toISOString(),
          },
          isExpired,
          timeUntilExpiry: payload.exp ? payload.exp - currentTime : null,
        }

        if (isExpired) {
          diagnosis.issues.push('Token已过期')
          diagnosis.recommendations.push('需要重新登录获取新token')
        }
      } else {
        diagnosis.tokenStatus = { format: 'invalid', reason: 'JWT格式错误' }
        diagnosis.issues.push('Token格式无效')
        diagnosis.recommendations.push('清除无效token并重新登录')
      }
    } catch (error) {
      diagnosis.tokenStatus = { format: 'invalid', error: error.message }
      diagnosis.issues.push('Token解析失败')
      diagnosis.recommendations.push('清除损坏的token并重新登录')
    }
  } else {
    diagnosis.issues.push('未找到token')
    diagnosis.recommendations.push('需要登录获取token')
  }

  // 3. 检查用户信息
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    try {
      const parsedUserInfo = JSON.parse(userInfo)
      diagnosis.userStatus = {
        exists: true,
        data: parsedUserInfo,
      }
    } catch (error) {
      diagnosis.userStatus = {
        exists: false,
        error: 'JSON解析失败',
      }
      diagnosis.issues.push('用户信息损坏')
      diagnosis.recommendations.push('清除损坏的用户信息')
    }
  } else {
    diagnosis.userStatus = { exists: false }
    diagnosis.issues.push('未找到用户信息')
  }

  // 4. 检查调试信息
  const debugInfo = localStorage.getItem('auth_debug')
  if (debugInfo) {
    try {
      diagnosis.debugInfo = JSON.parse(debugInfo)
    } catch (error) {
      diagnosis.issues.push('调试信息损坏')
    }
  }

  console.log('📊 诊断结果:', diagnosis)
  return diagnosis
}

/**
 * 自动修复认证问题
 * @returns {Object} 修复结果
 */
export function autoFixAuth() {
  const diagnosis = runAuthDiagnosis()
  const fixResult = {
    timestamp: new Date().toISOString(),
    actions: [],
    success: false,
  }

  console.log('🔧 开始自动修复认证问题...')

  // 清除无效或过期的token
  if (
    diagnosis.issues.includes('Token已过期') ||
    diagnosis.issues.includes('Token格式无效') ||
    diagnosis.issues.includes('Token解析失败')
  ) {
    localStorage.removeItem('access_token')
    sessionStorage.removeItem('access_token')
    fixResult.actions.push('清除无效token')
    console.log('✅ 已清除无效token')
  }

  // 清除损坏的用户信息
  if (diagnosis.issues.includes('用户信息损坏')) {
    localStorage.removeItem('userInfo')
    fixResult.actions.push('清除损坏的用户信息')
    console.log('✅ 已清除损坏的用户信息')
  }

  // 清除损坏的调试信息
  if (diagnosis.issues.includes('调试信息损坏')) {
    localStorage.removeItem('auth_debug')
    fixResult.actions.push('清除损坏的调试信息')
    console.log('✅ 已清除损坏的调试信息')
  }

  if (fixResult.actions.length > 0) {
    fixResult.success = true
    console.log('✅ 自动修复完成，建议刷新页面并重新登录')
  } else {
    console.log('ℹ️ 未发现可自动修复的问题')
  }

  return fixResult
}

/**
 * 强制清除所有认证数据
 */
export function clearAllAuthData() {
  const keys = ['access_token', 'userInfo', 'auth_debug', 'refresh_token']

  keys.forEach((key) => {
    localStorage.removeItem(key)
    sessionStorage.removeItem(key)
  })

  console.log('🧹 已清除所有认证数据')
  return true
}

/**
 * 检查认证状态
 */
export function checkAuthStatus() {
  console.log('🔍 检查认证状态...')

  const token = localStorage.getItem('access_token')
  const userInfo = localStorage.getItem('userInfo')
  const permissions = localStorage.getItem('permissions')

  const result = {
    timestamp: new Date().toISOString(),
    token: {
      exists: !!token,
      value: token ? `${token.substring(0, 20)}...` : null,
      length: token ? token.length : 0,
      isJWT: token ? token.split('.').length === 3 : false,
    },
    userInfo: {
      exists: !!userInfo,
      parsed: null,
    },
    permissions: {
      exists: !!permissions,
      parsed: null,
    },
    headers: {},
    issues: [],
  }

  // 解析用户信息
  if (userInfo) {
    try {
      result.userInfo.parsed = JSON.parse(userInfo)
    } catch (error) {
      result.issues.push('用户信息JSON格式错误')
    }
  }

  // 解析权限信息
  if (permissions) {
    try {
      result.permissions.parsed = JSON.parse(permissions)
    } catch (error) {
      result.issues.push('权限信息JSON格式错误')
    }
  }

  // 检查JWT token
  if (token && result.token.isJWT) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Math.floor(Date.now() / 1000)

      result.token.payload = payload
      result.token.expired = payload.exp < currentTime
      result.token.expiresAt = new Date(payload.exp * 1000).toISOString()

      if (result.token.expired) {
        result.issues.push('访问令牌已过期')
      }
    } catch (error) {
      result.issues.push('JWT token解析失败')
    }
  }

  // 检查请求头
  if (token) {
    result.headers.Authorization = `Bearer ${token.substring(0, 20)}...`
  } else {
    result.issues.push('缺少访问令牌')
  }

  return result
}

/**
 * 测试API认证
 */
export async function testApiAuth() {
  console.log('🧪 测试API认证...')

  const authStatus = checkAuthStatus()

  if (authStatus.issues.length > 0) {
    console.warn('⚠️ 认证状态有问题:', authStatus.issues)
    return {
      success: false,
      issues: authStatus.issues,
      authStatus,
    }
  }

  // 测试简单的API调用
  try {
    const response = await fetch('/api/v2/auth/me', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    return {
      success: response.ok,
      status: response.status,
      statusText: response.statusText,
      data,
      authStatus,
    }
  } catch (error) {
    return {
      success: false,
      error: error.message,
      authStatus,
    }
  }
}

/**
 * 修复认证问题
 */
export async function fixAuthIssues() {
  console.log('🔧 尝试修复认证问题...')

  const authStatus = checkAuthStatus()
  const fixes = []

  // 如果token过期，尝试刷新
  if (authStatus.token.expired) {
    fixes.push('Token已过期，需要重新登录')

    // 清除过期的认证信息
    localStorage.removeItem('access_token')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('permissions')

    fixes.push('已清除过期的认证信息')
  }

  // 如果缺少token，提示登录
  if (!authStatus.token.exists) {
    fixes.push('缺少访问令牌，请重新登录')
  }

  // 如果token格式错误
  if (authStatus.token.exists && !authStatus.token.isJWT) {
    fixes.push('Token格式错误，请重新登录')
    localStorage.removeItem('access_token')
  }

  return {
    fixes,
    needsLogin: fixes.some((fix) => fix.includes('登录')),
    authStatus,
  }
}

/**
 * 生成认证诊断报告
 */
export async function generateAuthReport() {
  console.log('📋 生成认证诊断报告...')

  const authStatus = checkAuthStatus()
  const apiTest = await testApiAuth()
  const fixes = await fixAuthIssues()

  const report = {
    timestamp: new Date().toISOString(),
    title: '认证状态诊断报告',
    summary: {
      hasToken: authStatus.token.exists,
      tokenValid: authStatus.token.exists && !authStatus.token.expired,
      apiWorking: apiTest.success,
      needsLogin: fixes.needsLogin,
    },
    details: {
      authStatus,
      apiTest,
      fixes,
    },
    recommendations: [],
  }

  // 生成建议
  if (fixes.needsLogin) {
    report.recommendations.push('🔑 请重新登录系统')
    report.recommendations.push('📍 导航到登录页面: /login')
  } else if (!apiTest.success) {
    report.recommendations.push('🔧 检查后端服务是否正常运行')
    report.recommendations.push('🌐 检查网络连接')
    report.recommendations.push('⚙️ 检查API端点配置')
  } else {
    report.recommendations.push('✅ 认证状态正常')
  }

  console.log('📊 认证诊断报告:', report.summary)

  return report
}

/**
 * 快速认证修复
 */
export async function quickAuthFix() {
  console.log('⚡ 快速认证修复...')

  const report = await generateAuthReport()

  if (report.summary.needsLogin) {
    console.log('🔑 需要重新登录')

    // 尝试跳转到登录页面
    if (typeof window !== 'undefined' && window.location) {
      const currentPath = window.location.pathname
      if (currentPath !== '/login') {
        console.log('📍 跳转到登录页面...')
        window.location.href = '/login'
        return { redirected: true, report }
      }
    }
  }

  return { redirected: false, report }
}

/**
 * 在开发环境下挂载到window对象
 */
if (process.env.NODE_ENV === 'development') {
  window.runAuthDiagnosis = runAuthDiagnosis
  window.autoFixAuth = autoFixAuth
  window.clearAllAuthData = clearAllAuthData
  window.checkAuthStatus = checkAuthStatus
  window.testApiAuth = testApiAuth
  window.fixAuthIssues = fixAuthIssues
  window.generateAuthReport = generateAuthReport
  window.quickAuthFix = quickAuthFix
  console.log('🛠️ 认证诊断工具已挂载到window对象')
  console.log('可用命令: runAuthDiagnosis(), autoFixAuth(), clearAllAuthData()')
}

export default {
  runAuthDiagnosis,
  autoFixAuth,
  clearAllAuthData,
  checkAuthStatus,
  testApiAuth,
  fixAuthIssues,
  generateAuthReport,
  quickAuthFix,
}
