/**
 * 认证状态修复工具
 * 解决用户登录状态丢失和权限加载问题
 */

import { useUserStore, usePermissionStore } from '@/store'
import { getToken, removeToken } from '@/utils/auth/token'

/**
 * 检查并修复认证状态
 */
export async function checkAndFixAuthState() {
  console.log('🔍 开始检查认证状态...')

  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  // 检查是否正在登出，如果是则跳过认证状态检查
  if (userStore.isLoggingOut) {
    console.log('正在登出，跳过认证状态检查')
    return { success: false, reason: 'LOGGING_OUT' }
  }

  // 检查token是否存在
  const token = getToken()
  if (!token) {
    console.log('❌ Token不存在，用户未登录')
    return { success: false, reason: 'NO_TOKEN' }
  }

  // 检查token是否过期
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000
    const now = Date.now()

    if (exp <= now) {
      console.log('❌ Token已过期')
      removeToken()
      userStore.$reset()
      permissionStore.resetPermission()
      return { success: false, reason: 'TOKEN_EXPIRED' }
    }

    console.log(`✅ Token有效，${Math.floor((exp - now) / 1000 / 60)} 分钟后过期`)
  } catch (error) {
    console.log('❌ Token格式错误')
    removeToken()
    userStore.$reset()
    permissionStore.resetPermission()
    return { success: false, reason: 'INVALID_TOKEN' }
  }

  // 检查用户信息是否存在
  if (!userStore.userId) {
    console.log('⚠️ 用户信息缺失，尝试重新获取...')
    try {
      await userStore.getUserInfo()
      console.log('✅ 用户信息获取成功')
    } catch (error) {
      console.log('❌ 用户信息获取失败:', error)
      return { success: false, reason: 'USER_INFO_FAILED' }
    }
  }

  // 检查权限是否存在
  if (!permissionStore.apis || permissionStore.apis.length === 0) {
    console.log('⚠️ 权限信息缺失，尝试重新获取...')
    try {
      await permissionStore.getAccessApis()
      console.log(`✅ 权限信息获取成功: ${permissionStore.apis.length} 个权限`)
    } catch (error) {
      console.log('❌ 权限信息获取失败:', error)
      return { success: false, reason: 'PERMISSION_FAILED' }
    }
  }

  console.log('✅ 认证状态检查完成，一切正常')
  return {
    success: true,
    user: userStore.userInfo,
    permissions: permissionStore.apis.length,
  }
}

/**
 * 强制重新登录
 */
export function forceRelogin() {
  console.log('🔄 强制重新登录...')

  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  // 清除所有认证信息
  removeToken()
  localStorage.removeItem('userInfo')
  localStorage.removeItem('permissions')

  // 重置store状态
  userStore.$reset()
  permissionStore.resetPermission()

  // 跳转到登录页面
  window.location.href = '/login'
}

/**
 * 修复权限加载状态
 */
export function fixPermissionLoadingState() {
  const permissionStore = usePermissionStore()

  // 如果权限正在加载但实际上没有在加载，重置状态
  if (
    permissionStore.isLoadingApis &&
    (!permissionStore.apis || permissionStore.apis.length === 0)
  ) {
    console.log('🔧 修复权限加载状态...')
    permissionStore.isLoadingApis = false
  }
}

/**
 * 自动修复认证状态（在应用启动时调用）
 */
export async function autoFixAuthState() {
  try {
    const result = await checkAndFixAuthState()

    if (!result.success) {
      switch (result.reason) {
        case 'NO_TOKEN':
        case 'TOKEN_EXPIRED':
        case 'INVALID_TOKEN':
          console.log('🔄 认证信息无效，需要重新登录')
          // 不自动跳转，让用户手动登录
          break
        case 'USER_INFO_FAILED':
        case 'PERMISSION_FAILED':
          console.log('⚠️ 认证信息获取失败，可能需要重新登录')
          break
      }
    }

    // 修复权限加载状态
    fixPermissionLoadingState()

    return result
  } catch (error) {
    console.error('❌ 认证状态自动修复失败:', error)
    return { success: false, reason: 'AUTO_FIX_FAILED', error }
  }
}

/**
 * 监听认证状态变化
 */
export function watchAuthState() {
  // 监听token变化
  const originalSetItem = localStorage.setItem
  localStorage.setItem = function (key, value) {
    if (key === 'access_token') {
      console.log('🔔 Token发生变化')

      // 检查是否正在登出，如果是则跳过权限重新验证
      try {
        const userStore = useUserStore()
        if (userStore.isLoggingOut) {
          console.log('🚪 用户正在登出，跳过权限重新验证事件触发')
          originalSetItem.apply(this, arguments)
          return
        }
      } catch (error) {
        console.warn('检查登出状态失败:', error)
        // 如果无法获取用户状态，为了安全起见，也跳过权限重新验证
        console.log('🚪 无法获取用户状态，跳过权限重新验证事件触发')
        originalSetItem.apply(this, arguments)
        return
      }

      // 额外延迟检查，确保登出状态已经设置
      setTimeout(() => {
        try {
          const userStore = useUserStore()
          if (userStore.isLoggingOut) {
            console.log('🚪 延迟检查：用户正在登出，跳过权限重新验证事件触发')
            return
          }
          // 触发权限重新验证事件
          window.dispatchEvent(new CustomEvent('permission-revalidate'))
        } catch (error) {
          console.warn('延迟检查登出状态失败:', error)
        }
      }, 100)
    }
    originalSetItem.apply(this, arguments)
  }

  // 监听token删除
  const originalRemoveItem = localStorage.removeItem
  localStorage.removeItem = function (key) {
    if (key === 'access_token') {
      console.log('🔔 Token被删除')

      // 检查是否正在登出，如果是则跳过权限重新验证
      try {
        const userStore = useUserStore()
        if (userStore.isLoggingOut) {
          console.log('🚪 用户正在登出，跳过权限重新验证事件触发')
          originalRemoveItem.apply(this, arguments)
          return
        }
      } catch (error) {
        console.warn('检查登出状态失败:', error)
        // 如果无法获取用户状态，为了安全起见，也跳过权限重新验证
        console.log('🚪 无法获取用户状态，跳过权限重新验证事件触发')
        originalRemoveItem.apply(this, arguments)
        return
      }

      // 额外延迟检查，确保登出状态已经设置
      setTimeout(() => {
        try {
          const userStore = useUserStore()
          if (userStore.isLoggingOut) {
            console.log('🚪 延迟检查：用户正在登出，跳过权限重新验证事件触发')
            return
          }
          // 触发权限重新验证事件
          window.dispatchEvent(new CustomEvent('permission-revalidate'))
        } catch (error) {
          console.warn('延迟检查登出状态失败:', error)
        }
      }, 100)
    }
    originalRemoveItem.apply(this, arguments)
  }
}

/**
 * 获取认证状态摘要
 */
export function getAuthStateSummary() {
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()
  const token = getToken()

  return {
    hasToken: !!token,
    hasUserInfo: !!userStore.userId,
    hasPermissions: permissionStore.apis && permissionStore.apis.length > 0,
    isLoadingPermissions: permissionStore.isLoadingApis,
    username: userStore.name,
    permissionCount: permissionStore.apis ? permissionStore.apis.length : 0,
    isSuperUser: userStore.isSuperUser,
  }
}
