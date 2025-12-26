/**
 * 紧急认证修复工具
 * 解决用户认证状态丢失和权限检查失败问题
 */

import { useUserStore, usePermissionStore } from '@/store'
import { getToken, removeToken, setToken } from '@/utils/auth/token'
import { authApi } from '@/api/system-v2'

/**
 * 紧急认证状态检查和修复
 */
export async function emergencyAuthFix() {
  console.log('🚨 开始紧急认证修复...')

  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  // 1. 检查token
  const token = getToken()
  if (!token) {
    console.log('❌ 没有token，需要重新登录')
    return handleNoToken()
  }

  // 2. 验证token有效性
  const tokenValid = await validateToken(token)
  if (!tokenValid) {
    console.log('❌ Token无效，需要重新登录')
    return handleInvalidToken()
  }

  // 3. 检查用户信息
  if (!userStore.userId) {
    console.log('⚠️ 用户信息缺失，尝试获取...')
    const userInfoResult = await loadUserInfo(userStore)
    if (!userInfoResult.success) {
      return userInfoResult
    }
  }

  // 4. 检查权限信息
  if (!permissionStore.apis || permissionStore.apis.length === 0) {
    console.log('⚠️ 权限信息缺失，尝试获取...')
    const permissionResult = await loadPermissions(permissionStore)
    if (!permissionResult.success) {
      return permissionResult
    }
  }

  // 5. 修复权限加载状态
  if (permissionStore.isLoadingApis) {
    console.log('🔧 修复权限加载状态...')
    permissionStore.isLoadingApis = false
  }

  console.log('✅ 紧急认证修复完成')
  return {
    success: true,
    message: '认证状态已修复',
    user: userStore.userInfo,
    permissions: permissionStore.apis.length,
  }
}

/**
 * 验证token有效性
 */
async function validateToken(token) {
  try {
    // 检查token格式
    const parts = token.split('.')
    if (parts.length !== 3) {
      return false
    }

    // 检查token是否过期
    const payload = JSON.parse(atob(parts[1]))
    const exp = payload.exp * 1000
    const now = Date.now()

    if (exp <= now) {
      console.log('Token已过期')
      return false
    }

    console.log(`Token有效，${Math.floor((exp - now) / 1000 / 60)} 分钟后过期`)
    return true
  } catch (error) {
    console.error('Token验证失败:', error)
    return false
  }
}

/**
 * 加载用户信息
 */
async function loadUserInfo(userStore) {
  try {
    await userStore.getUserInfo()
    console.log('✅ 用户信息加载成功')
    return { success: true }
  } catch (error) {
    console.error('❌ 用户信息加载失败:', error)
    if (error.response?.status === 401) {
      return handleUnauthorized()
    }
    return {
      success: false,
      message: '用户信息加载失败',
      error: error.message,
    }
  }
}

/**
 * 加载权限信息
 */
async function loadPermissions(permissionStore) {
  // 检查是否正在登出，如果是则跳过权限加载
  const userStore = useUserStore()
  if (userStore.isLoggingOut) {
    console.log('正在登出，跳过权限加载')
    return { success: false, reason: 'LOGGING_OUT' }
  }

  try {
    await permissionStore.getAccessApis()
    console.log(`✅ 权限信息加载成功: ${permissionStore.apis.length} 个权限`)
    return { success: true }
  } catch (error) {
    console.error('❌ 权限信息加载失败:', error)
    if (error.response?.status === 401) {
      return handleUnauthorized()
    }
    return {
      success: false,
      message: '权限信息加载失败',
      error: error.message,
    }
  }
}

/**
 * 处理没有token的情况
 */
function handleNoToken() {
  console.log('🔄 清理认证状态，准备重新登录')
  clearAuthState()
  return {
    success: false,
    message: '用户未登录，请重新登录',
    action: 'LOGIN_REQUIRED',
  }
}

/**
 * 处理token无效的情况
 */
function handleInvalidToken() {
  console.log('🔄 清理无效token，准备重新登录')
  clearAuthState()
  return {
    success: false,
    message: 'Token无效，请重新登录',
    action: 'LOGIN_REQUIRED',
  }
}

/**
 * 处理未授权的情况
 */
function handleUnauthorized() {
  const userStore = useUserStore()

  // 如果正在登出，不需要额外处理
  if (userStore.isLoggingOut) {
    console.log('正在登出过程中，跳过未授权处理')
    return {
      success: false,
      reason: 'LOGGING_OUT',
    }
  }

  console.log('🔄 认证失败，清理状态')
  clearAuthState()
  return {
    success: false,
    message: '认证失败，请重新登录',
    action: 'LOGIN_REQUIRED',
  }
}

/**
 * 清理认证状态
 */
function clearAuthState() {
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  // 清除token
  removeToken()

  // 清除localStorage中的其他认证信息
  localStorage.removeItem('userInfo')
  localStorage.removeItem('permissions')

  // 重置store状态
  userStore.$reset()
  permissionStore.resetPermission()
}

/**
 * 强制跳转到登录页面
 */
export function forceLogin() {
  console.log('🔄 强制跳转到登录页面')
  clearAuthState()

  // 保存当前页面路径，登录后可以返回
  const currentPath = window.location.pathname + window.location.search
  if (currentPath !== '/login') {
    localStorage.setItem('redirect_after_login', currentPath)
  }

  // 跳转到登录页面
  window.location.href = '/login'
}

/**
 * 检查是否需要登录
 */
export function checkLoginRequired() {
  const token = getToken()
  if (!token) {
    console.log('⚠️ 检测到用户未登录')
    return true
  }

  // 检查token是否过期
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000
    const now = Date.now()

    if (exp <= now) {
      console.log('⚠️ 检测到token已过期')
      return true
    }
  } catch (error) {
    console.log('⚠️ 检测到token格式错误')
    return true
  }

  return false
}

/**
 * 自动修复认证状态（在页面加载时调用）
 */
export async function autoFixAuth() {
  console.log('🔄 自动修复认证状态...')

  // 如果需要登录，直接跳转
  if (checkLoginRequired()) {
    console.log('🔄 需要登录，跳转到登录页面')
    forceLogin()
    return { success: false, action: 'REDIRECTED_TO_LOGIN' }
  }

  // 尝试修复认证状态
  const result = await emergencyAuthFix()

  if (!result.success && result.action === 'LOGIN_REQUIRED') {
    console.log('🔄 修复失败，跳转到登录页面')
    forceLogin()
    return { success: false, action: 'REDIRECTED_TO_LOGIN' }
  }

  return result
}

/**
 * 获取认证状态摘要
 */
export function getAuthSummary() {
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()
  const token = getToken()

  return {
    hasToken: !!token,
    tokenValid: token ? validateTokenSync(token) : false,
    hasUserInfo: !!userStore.userId,
    hasPermissions: permissionStore.apis && permissionStore.apis.length > 0,
    isLoadingPermissions: permissionStore.isLoadingApis,
    username: userStore.name,
    permissionCount: permissionStore.apis ? permissionStore.apis.length : 0,
    isSuperUser: userStore.isSuperUser,
  }
}

/**
 * 同步验证token（不抛出异常）
 */
function validateTokenSync(token) {
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
