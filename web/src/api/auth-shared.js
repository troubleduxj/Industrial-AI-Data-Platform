/**
 * 认证管理 API - Shared 层适配器
 * 使用 shared API 层，保持与现有 API 接口兼容
 */

import sharedApi from './shared'

// ========== 认证 API ==========

export const authApi = {
  // 用户登录
  login: async (credentials) => {
    const result = await sharedApi.auth.login(credentials)

    // 登录成功后保存 token
    if (result.data.access_token) {
      localStorage.setItem('token', result.data.access_token)

      if (result.data.refresh_token) {
        localStorage.setItem('refreshToken', result.data.refresh_token)
      }

      // 保存用户信息
      if (result.data.user) {
        localStorage.setItem('userInfo', JSON.stringify(result.data.user))
      }

      // 保存权限信息
      if (result.data.permissions) {
        localStorage.setItem('permissions', JSON.stringify(result.data.permissions))
      }

      // 保存菜单信息
      if (result.data.menus) {
        localStorage.setItem('menus', JSON.stringify(result.data.menus))
      }
    }

    return { data: result.data }
  },

  // 用户登出
  logout: async () => {
    try {
      const result = await sharedApi.auth.logout()
      return { data: result.data }
    } finally {
      // 无论请求是否成功，都清除本地存储
      clearAuthData()
    }
  },

  // 刷新 Token
  refreshToken: async (refreshToken) => {
    const token = refreshToken || localStorage.getItem('refreshToken')

    if (!token) {
      throw new Error('No refresh token available')
    }

    const result = await sharedApi.auth.refreshToken(token)

    // 更新 token
    if (result.data.access_token) {
      localStorage.setItem('token', result.data.access_token)
    }

    if (result.data.refresh_token) {
      localStorage.setItem('refreshToken', result.data.refresh_token)
    }

    return { data: result.data }
  },

  // 获取当前用户信息
  getCurrentUser: async () => {
    const result = await sharedApi.auth.getCurrentUser()

    // 更新本地存储的用户信息
    if (result.data) {
      localStorage.setItem('userInfo', JSON.stringify(result.data))
    }

    return { data: result.data }
  },

  // 修改密码
  changePassword: async (oldPassword, newPassword) => {
    const result = await sharedApi.auth.changePassword(oldPassword, newPassword)
    return { data: result.data }
  },

  // 获取用户权限列表
  getPermissions: async () => {
    const result = await sharedApi.auth.getPermissions()

    // 更新本地存储的权限信息
    if (result.data) {
      localStorage.setItem('permissions', JSON.stringify(result.data))
    }

    return { data: result.data }
  },

  // 检查是否已登录
  isAuthenticated: () => {
    return !!localStorage.getItem('token')
  },

  // 获取本地存储的用户信息
  getLocalUser: () => {
    const userInfo = localStorage.getItem('userInfo')
    return userInfo ? JSON.parse(userInfo) : null
  },

  // 获取本地存储的权限列表
  getLocalPermissions: () => {
    const permissions = localStorage.getItem('permissions')
    return permissions ? JSON.parse(permissions) : []
  },

  // 获取本地存储的菜单列表
  getLocalMenus: () => {
    const menus = localStorage.getItem('menus')
    return menus ? JSON.parse(menus) : []
  },
}

// ========== 工具函数 ==========

/**
 * 清除认证数据
 */
export function clearAuthData() {
  localStorage.removeItem('token')
  localStorage.removeItem('refreshToken')
  localStorage.removeItem('userInfo')
  localStorage.removeItem('permissions')
  localStorage.removeItem('menus')
}

/**
 * 检查权限
 */
export function hasPermission(permission) {
  const permissions = authApi.getLocalPermissions()
  return permissions.includes(permission)
}

/**
 * 检查是否有任一权限
 */
export function hasAnyPermission(permissionList) {
  const permissions = authApi.getLocalPermissions()
  return permissionList.some((p) => permissions.includes(p))
}

/**
 * 检查是否拥有所有权限
 */
export function hasAllPermissions(permissionList) {
  const permissions = authApi.getLocalPermissions()
  return permissionList.every((p) => permissions.includes(p))
}

/**
 * 检查是否为超级管理员
 */
export function isSuperAdmin() {
  const user = authApi.getLocalUser()
  return user?.isSuperuser === true || user?.is_superuser === true
}

/**
 * 获取 Token（用于 HTTP 请求）
 */
export function getToken() {
  return localStorage.getItem('token') || ''
}

/**
 * 设置 Token
 */
export function setToken(token) {
  if (token) {
    localStorage.setItem('token', token)
  } else {
    localStorage.removeItem('token')
  }
}

/**
 * Token 是否即将过期（提前 5 分钟）
 */
export function isTokenExpiringSoon() {
  const token = getToken()
  if (!token) return true

  try {
    // 简单的 JWT 解析
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000 // 转换为毫秒
    const now = Date.now()
    const fiveMinutes = 5 * 60 * 1000

    return exp - now < fiveMinutes
  } catch (error) {
    console.error('Token 解析失败:', error)
    return true
  }
}

/**
 * 自动刷新 Token
 */
export async function autoRefreshToken() {
  if (!authApi.isAuthenticated()) {
    return false
  }

  if (isTokenExpiringSoon()) {
    try {
      await authApi.refreshToken()
      return true
    } catch (error) {
      console.error('Token 刷新失败:', error)
      clearAuthData()
      return false
    }
  }

  return true
}

// ========== 默认导出（兼容现有代码） ==========

export default {
  ...authApi,
  clearAuthData,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  isSuperAdmin,
  getToken,
  setToken,
  isTokenExpiringSoon,
  autoRefreshToken,
}

/**
 * 使用说明：
 *
 * 登录示例：
 * import { authApi } from '@/api/auth-shared';
 * const result = await authApi.login({
 *   username: 'admin',
 *   password: '123456',
 *   remember: true,
 * });
 *
 * 登出示例：
 * await authApi.logout();
 *
 * 检查权限：
 * import { hasPermission, isSuperAdmin } from '@/api/auth-shared';
 * if (hasPermission('device:create')) {
 *   // 有权限
 * }
 * if (isSuperAdmin()) {
 *   // 是超级管理员
 * }
 *
 * 自动刷新 Token：
 * import { autoRefreshToken } from '@/api/auth-shared';
 * setInterval(autoRefreshToken, 60000); // 每分钟检查一次
 *
 * 或直接使用 shared：
 * import sharedApi from '@/api/shared';
 * await sharedApi.auth.login({ username, password });
 */
