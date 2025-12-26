/**
 * 权限路由守卫
 * 实现基于权限的路由访问控制
 */

import { useUserStore } from '@/store/modules/user'
import { useEnhancedPermissionStore } from '@/store/modules/permission'
import { useAIModuleStore } from '@/store/modules/ai'
import { getToken, isNullOrWhitespace } from '@/utils'

/**
 * 白名单路由 - 不需要权限检查的路由
 */
const WHITE_LIST = ['/login', '/404', '/403', '/error-page', '/']

/**
 * 公开路由 - 登录后可以访问但不需要特定权限的路由
 */
const PUBLIC_ROUTES = [
  '/workbench',
  '/profile',
  '/test', // 测试路由也设为公开
]

/**
 * 检查路由是否在白名单中
 */
function isWhiteListRoute(path) {
  return WHITE_LIST.some((route) => {
    if (route === path) return true
    // 支持通配符匹配
    if (route.endsWith('*')) {
      return path.startsWith(route.slice(0, -1))
    }
    return false
  })
}

/**
 * 检查路由是否为公开路由
 */
function isPublicRoute(path) {
  return PUBLIC_ROUTES.some((route) => {
    if (route === path) return true
    // 支持子路由匹配
    return path.startsWith(route + '/')
  })
}

/**
 * 检查路由权限
 */
function checkRoutePermission(route, permissionStore, userStore) {
  // 超级用户拥有所有权限
  if (userStore.isSuperUser) {
    return true
  }

  // 检查路由元信息中的权限要求
  const routePermissions = route.meta?.permissions
  if (!routePermissions || routePermissions.length === 0) {
    return true // 没有权限要求的路由允许访问
  }

  // 使用权限Store检查权限
  return permissionStore.hasPermission(routePermissions, 'any')
}

/**
 * 检查AI模块权限
 */
function checkAIModuleAccess(route) {
  // 检查路由是否需要AI模块
  if (!route.meta?.requiresAIModule) {
    return true // 不需要AI模块的路由允许访问
  }

  // 获取AI模块Store
  const aiModuleStore = useAIModuleStore()

  // 检查AI模块是否启用
  return aiModuleStore.isEnabled
}

/**
 * 获取用户可访问的重定向路由
 */
function getAccessibleRedirectRoute(permissionStore, userStore) {
  // 超级用户默认跳转到工作台
  if (userStore.isSuperUser) {
    return '/workbench'
  }

  // 获取用户菜单，找到第一个可访问的路由
  const userMenus = permissionStore.userMenus
  if (userMenus && userMenus.length > 0) {
    for (const menu of userMenus) {
      if (menu.children && menu.children.length > 0) {
        const firstChild = menu.children[0]
        if (firstChild.path) {
          return firstChild.path.startsWith('/')
            ? firstChild.path
            : `/${menu.path}/${firstChild.path}`
        }
      } else if (menu.path && menu.component !== 'Layout') {
        return menu.path.startsWith('/') ? menu.path : `/${menu.path}`
      }
    }
  }

  // 如果没有找到可访问的菜单，跳转到工作台
  return '/workbench'
}

/**
 * 创建权限路由守卫
 */
export function createPermissionGuard(router) {
  router.beforeEach(async (to, from, next) => {
    const token = getToken()
    const userStore = useUserStore()
    const permissionStore = useEnhancedPermissionStore()

    console.log('=== 权限路由守卫 ===', {
      to: to.path,
      from: from.path,
      hasToken: !isNullOrWhitespace(token),
      isLoggingOut: userStore.isLoggingOut,
    })

    // 如果正在登出，允许访问白名单路由
    if (userStore.isLoggingOut) {
      if (isWhiteListRoute(to.path)) {
        next()
        return
      } else {
        next('/login')
        return
      }
    }

    // 没有token的情况
    if (isNullOrWhitespace(token)) {
      if (isWhiteListRoute(to.path)) {
        next()
        return
      }

      console.log('无token，重定向到登录页')
      next({
        path: '/login',
        query: { ...to.query, redirect: to.path },
      })
      return
    }

    // 有token但访问登录页，重定向到首页
    if (to.path === '/login') {
      const redirectPath = getAccessibleRedirectRoute(permissionStore, userStore)
      console.log('已登录用户访问登录页，重定向到:', redirectPath)
      next(redirectPath)
      return
    }

    // 白名单路由直接通过
    if (isWhiteListRoute(to.path)) {
      next()
      return
    }

    // 确保用户信息已加载
    if (!userStore.userId) {
      try {
        await userStore.getUserInfo()
        console.log('用户信息加载成功:', userStore.userId)
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 如果获取用户信息失败，清除token并重定向到登录页
        await userStore.logout()
        next('/login')
        return
      }
    }

    // 确保权限数据已加载
    if (!permissionStore.accessRoutes || permissionStore.accessRoutes.length === 0) {
      try {
        console.log('权限数据未加载，开始加载...')
        await Promise.all([permissionStore.getUserMenus(), permissionStore.getAccessApis()])
        console.log('权限数据加载成功')
      } catch (error) {
        console.error('获取权限数据失败:', error)
        // 权限数据获取失败，但不阻止访问公开路由
        if (isPublicRoute(to.path)) {
          next()
          return
        }
      }
    }

    // 公开路由检查
    if (isPublicRoute(to.path)) {
      next()
      return
    }

    // 检查路由权限
    const hasPermission = checkRoutePermission(to, permissionStore, userStore)

    console.log('路由权限检查结果:', {
      route: to.path,
      hasPermission,
      isSuperUser: userStore.isSuperUser,
      routePermissions: to.meta?.permissions,
    })

    if (!hasPermission) {
      console.log('权限不足，重定向到403页面')
      next('/403')
      return
    }

    // 检查AI模块权限
    const hasAIModuleAccess = checkAIModuleAccess(to)

    console.log('AI模块权限检查结果:', {
      route: to.path,
      requiresAIModule: to.meta?.requiresAIModule,
      hasAIModuleAccess,
    })

    if (!hasAIModuleAccess) {
      console.log('AI模块未启用，重定向到403页面')
      next('/403')
      return
    }

    // 所有检查通过，允许访问
    next()
  })
}

/**
 * 权限路由守卫配置
 */
export const PermissionGuardConfig = {
  // 白名单路由配置
  whiteList: WHITE_LIST,

  // 公开路由配置
  publicRoutes: PUBLIC_ROUTES,

  // 添加白名单路由
  addWhiteListRoute(route) {
    if (!WHITE_LIST.includes(route)) {
      WHITE_LIST.push(route)
    }
  },

  // 添加公开路由
  addPublicRoute(route) {
    if (!PUBLIC_ROUTES.includes(route)) {
      PUBLIC_ROUTES.push(route)
    }
  },

  // 移除白名单路由
  removeWhiteListRoute(route) {
    const index = WHITE_LIST.indexOf(route)
    if (index > -1) {
      WHITE_LIST.splice(index, 1)
    }
  },

  // 移除公开路由
  removePublicRoute(route) {
    const index = PUBLIC_ROUTES.indexOf(route)
    if (index > -1) {
      PUBLIC_ROUTES.splice(index, 1)
    }
  },
}

export default createPermissionGuard
