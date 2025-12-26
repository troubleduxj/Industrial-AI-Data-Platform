/**
 * 认证紧急修复脚本
 * 用于快速诊断和修复认证问题
 */

/**
 * 检查token有效性
 */
function checkTokenValidity() {
  const token = localStorage.getItem('access_token')

  if (!token) {
    return { valid: false, reason: '缺少访问令牌' }
  }

  try {
    const parts = token.split('.')
    if (parts.length !== 3) {
      return { valid: false, reason: 'Token格式无效' }
    }

    const payload = JSON.parse(atob(parts[1]))
    const currentTime = Math.floor(Date.now() / 1000)

    if (payload.exp < currentTime) {
      return {
        valid: false,
        reason: 'Token已过期',
        expiredAt: new Date(payload.exp * 1000).toISOString(),
        currentTime: new Date().toISOString(),
      }
    }

    return {
      valid: true,
      payload,
      expiresAt: new Date(payload.exp * 1000).toISOString(),
    }
  } catch (error) {
    return { valid: false, reason: 'Token解析失败', error: error.message }
  }
}

/**
 * 清除认证信息
 */
function clearAuthData() {
  console.log('🧹 清除认证信息...')

  const keysToRemove = [
    'access_token',
    'userInfo',
    'permissions',
    'refresh_token',
    'user_permissions',
    'user_roles',
  ]

  keysToRemove.forEach((key) => {
    if (localStorage.getItem(key)) {
      localStorage.removeItem(key)
      console.log(`✅ 已清除: ${key}`)
    }
  })

  // 清除sessionStorage中的认证信息
  keysToRemove.forEach((key) => {
    if (sessionStorage.getItem(key)) {
      sessionStorage.removeItem(key)
      console.log(`✅ 已清除sessionStorage: ${key}`)
    }
  })
}

/**
 * 重定向到登录页面
 */
function redirectToLogin() {
  console.log('🔄 重定向到登录页面...')

  const currentPath = window.location.pathname
  const loginPath = '/login'

  if (currentPath !== loginPath) {
    // 保存当前路径，登录后可以返回
    sessionStorage.setItem('redirect_after_login', currentPath)
    window.location.href = loginPath
    return true
  }

  return false
}

/**
 * 测试API连接
 */
async function testApiConnection() {
  console.log('🧪 测试API连接...')

  try {
    // 测试不需要认证的端点
    const healthResponse = await fetch('/api/v2/health', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    console.log('Health API状态:', healthResponse.status)

    // 测试需要认证的端点
    const token = localStorage.getItem('access_token')
    if (token) {
      const authResponse = await fetch('/api/v2/auth/me', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      console.log('Auth API状态:', authResponse.status)

      if (authResponse.ok) {
        const userData = await authResponse.json()
        console.log('✅ 认证API测试成功:', userData)
        return { success: true, userData }
      } else {
        const errorData = await authResponse.json()
        console.log('❌ 认证API测试失败:', errorData)
        return { success: false, status: authResponse.status, error: errorData }
      }
    }

    return { success: false, reason: '没有token进行认证测试' }
  } catch (error) {
    console.error('❌ API连接测试失败:', error)
    return { success: false, error: error.message }
  }
}

/**
 * 紧急认证修复
 */
export async function emergencyAuthFix() {
  console.log('🚨 开始紧急认证修复...')
  console.log('=====================================')

  // 1. 检查token有效性
  console.log('📋 步骤1: 检查Token有效性...')
  const tokenCheck = checkTokenValidity()
  console.log('Token检查结果:', tokenCheck)

  // 2. 测试API连接
  console.log('🌐 步骤2: 测试API连接...')
  const apiTest = await testApiConnection()
  console.log('API测试结果:', apiTest)

  // 3. 决定修复策略
  console.log('🔧 步骤3: 执行修复...')

  if (!tokenCheck.valid) {
    console.log('❌ Token无效，清除认证信息并重定向到登录页面')
    clearAuthData()

    setTimeout(() => {
      redirectToLogin()
    }, 1000)

    return {
      action: 'redirect_to_login',
      reason: tokenCheck.reason,
      tokenCheck,
      apiTest,
    }
  }

  if (!apiTest.success) {
    if (apiTest.status === 401) {
      console.log('❌ API返回401，Token可能在服务端无效，清除认证信息')
      clearAuthData()

      setTimeout(() => {
        redirectToLogin()
      }, 1000)

      return {
        action: 'redirect_to_login',
        reason: 'API认证失败',
        tokenCheck,
        apiTest,
      }
    } else {
      console.log('⚠️ API连接有问题，但不是认证问题')
      return {
        action: 'api_connection_issue',
        reason: 'API连接问题',
        tokenCheck,
        apiTest,
      }
    }
  }

  console.log('✅ 认证状态正常')
  return {
    action: 'no_action_needed',
    reason: '认证状态正常',
    tokenCheck,
    apiTest,
  }
}

/**
 * 快速登录检查
 */
export function quickLoginCheck() {
  const tokenCheck = checkTokenValidity()

  if (!tokenCheck.valid) {
    console.log('🔑 需要重新登录:', tokenCheck.reason)

    // 显示用户友好的提示
    if (window.$message) {
      window.$message.warning('登录已过期，请重新登录', { duration: 3000 })
    }

    // 延迟跳转，让用户看到提示
    setTimeout(() => {
      clearAuthData()
      redirectToLogin()
    }, 2000)

    return false
  }

  return true
}

// 在开发环境下挂载到window对象
if (typeof window !== 'undefined') {
  window.emergencyAuthFix = emergencyAuthFix
  window.quickLoginCheck = quickLoginCheck
  window.checkTokenValidity = checkTokenValidity
  window.clearAuthData = clearAuthData
  window.testApiConnection = testApiConnection
}

// 自动运行检查
if (typeof window !== 'undefined') {
  console.log('🔧 认证紧急修复工具已加载！')
  console.log('💡 使用方法:')
  console.log('  - 紧急修复: await emergencyAuthFix()')
  console.log('  - 快速检查: quickLoginCheck()')
  console.log('  - 检查Token: checkTokenValidity()')
  console.log('  - 测试API: await testApiConnection()')
}

export default {
  emergencyAuthFix,
  quickLoginCheck,
  checkTokenValidity,
  clearAuthData,
  testApiConnection,
}
