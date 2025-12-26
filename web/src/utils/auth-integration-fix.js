/**
 * 认证集成修复工具
 * 在应用启动时自动检查和修复认证状态
 */

import { emergencyAuthFix, forceLogin, checkLoginRequired } from './auth-emergency-fix'

/**
 * 在应用启动时调用的认证修复函数
 */
export async function initAuthFix() {
  console.log('🔄 初始化认证修复...')

  try {
    // 如果明显需要登录，直接跳转
    if (checkLoginRequired()) {
      console.log('⚠️ 检测到需要登录，跳转到登录页面')
      forceLogin()
      return { success: false, action: 'REDIRECTED_TO_LOGIN' }
    }

    // 尝试修复认证状态
    const result = await emergencyAuthFix()

    if (result.success) {
      console.log('✅ 认证状态修复成功')
      return result
    } else {
      console.log('❌ 认证状态修复失败:', result.message)

      if (result.action === 'LOGIN_REQUIRED') {
        console.log('🔄 需要重新登录，跳转到登录页面')
        forceLogin()
        return { success: false, action: 'REDIRECTED_TO_LOGIN' }
      }

      return result
    }
  } catch (error) {
    console.error('❌ 认证修复过程中出错:', error)
    return {
      success: false,
      message: '认证修复失败',
      error: error.message,
    }
  }
}

/**
 * 在路由守卫中使用的认证检查
 */
export async function routeAuthCheck(to, from, next) {
  console.log(`🔍 路由认证检查: ${to.path}`)

  // 如果是登录页面，直接通过
  if (to.path === '/login') {
    next()
    return
  }

  // 检查是否需要登录
  if (checkLoginRequired()) {
    console.log('⚠️ 路由检查：需要登录')
    next('/login')
    return
  }

  try {
    // 尝试修复认证状态
    const result = await emergencyAuthFix()

    if (result.success) {
      console.log('✅ 路由认证检查通过')
      next()
    } else {
      console.log('❌ 路由认证检查失败，跳转到登录页面')
      next('/login')
    }
  } catch (error) {
    console.error('❌ 路由认证检查出错:', error)
    next('/login')
  }
}

/**
 * 在API请求拦截器中使用的认证修复
 */
export async function apiAuthFix(error) {
  console.log('🔍 API认证修复检查')

  // 如果是401错误，尝试修复认证状态
  if (error.response?.status === 401) {
    console.log('⚠️ 检测到401错误，尝试修复认证状态')

    try {
      const result = await emergencyAuthFix()

      if (result.success) {
        console.log('✅ 认证状态修复成功，可以重试请求')
        return { canRetry: true }
      } else {
        console.log('❌ 认证状态修复失败，需要重新登录')
        forceLogin()
        return { canRetry: false, action: 'REDIRECTED_TO_LOGIN' }
      }
    } catch (fixError) {
      console.error('❌ API认证修复出错:', fixError)
      forceLogin()
      return { canRetry: false, action: 'REDIRECTED_TO_LOGIN' }
    }
  }

  return { canRetry: false }
}

/**
 * 权限检查增强版
 */
export async function enhancedPermissionCheck(requiredPermission) {
  console.log(`🔍 增强权限检查: ${requiredPermission}`)

  try {
    // 先尝试修复认证状态
    const authResult = await emergencyAuthFix()

    if (!authResult.success) {
      console.log('❌ 认证状态修复失败，权限检查失败')
      return { hasPermission: false, reason: 'AUTH_FAILED' }
    }

    // 检查权限
    const { usePermissionStore } = await import('@/store')
    const permissionStore = usePermissionStore()

    if (!permissionStore.apis || permissionStore.apis.length === 0) {
      console.log('⚠️ 权限列表为空')
      return { hasPermission: false, reason: 'NO_PERMISSIONS' }
    }

    const hasPermission = permissionStore.apis.some(
      (api) =>
        api.path === requiredPermission ||
        api.name === requiredPermission ||
        api.code === requiredPermission
    )

    console.log(`权限检查结果: ${hasPermission ? '通过' : '拒绝'}`)
    return {
      hasPermission,
      reason: hasPermission ? 'GRANTED' : 'DENIED',
      totalPermissions: permissionStore.apis.length,
    }
  } catch (error) {
    console.error('❌ 增强权限检查出错:', error)
    return { hasPermission: false, reason: 'CHECK_ERROR', error: error.message }
  }
}

/**
 * 监听认证状态变化
 */
export function setupAuthWatcher() {
  console.log('🔄 设置认证状态监听器')

  // 监听localStorage变化
  window.addEventListener('storage', (event) => {
    if (event.key === 'access_token') {
      console.log('🔔 检测到token变化')

      if (!event.newValue) {
        console.log('⚠️ Token被删除，可能需要重新登录')
        // 可以在这里触发重新登录逻辑
      } else {
        console.log('✅ Token已更新')
        // 可以在这里触发状态刷新
      }
    }
  })

  // 监听页面可见性变化
  document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'visible') {
      console.log('🔍 页面重新可见，检查认证状态')

      if (checkLoginRequired()) {
        console.log('⚠️ 检测到需要重新登录')
        forceLogin()
      }
    }
  })
}

/**
 * 获取认证修复建议
 */
export function getAuthFixSuggestions() {
  const token = localStorage.getItem('access_token')
  const userInfo = localStorage.getItem('userInfo')
  const permissions = localStorage.getItem('permissions')

  const suggestions = []

  if (!token) {
    suggestions.push({
      type: 'error',
      message: '缺少访问令牌',
      action: '请重新登录',
      priority: 'high',
    })
  } else if (!checkTokenValid(token)) {
    suggestions.push({
      type: 'error',
      message: '访问令牌已过期或无效',
      action: '请重新登录',
      priority: 'high',
    })
  }

  if (!userInfo) {
    suggestions.push({
      type: 'warning',
      message: '用户信息缺失',
      action: '尝试刷新页面或重新登录',
      priority: 'medium',
    })
  }

  if (!permissions) {
    suggestions.push({
      type: 'warning',
      message: '权限信息缺失',
      action: '尝试刷新页面或重新登录',
      priority: 'medium',
    })
  }

  if (suggestions.length === 0) {
    suggestions.push({
      type: 'success',
      message: '认证状态正常',
      action: '无需操作',
      priority: 'low',
    })
  }

  return suggestions
}

function checkTokenValid(token) {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return false

    const payload = JSON.parse(atob(parts[1]))
    const exp = payload.exp * 1000
    const now = Date.now()

    return exp > now
  } catch (error) {
    return false
  }
}
