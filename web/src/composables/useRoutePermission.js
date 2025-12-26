/**
 * 路由权限管理Composable
 * 提供路由权限检查、动态路由管理等功能
 */

import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useEnhancedPermissionStore } from '@/store/modules/permission'
import { useUserStore } from '@/store/modules/user'
import { dynamicRouteManager } from '@/router/dynamic-routes'

/**
 * 路由权限管理Hook
 */
export function useRoutePermission() {
  const router = useRouter()
  const route = useRoute()
  const permissionStore = useEnhancedPermissionStore()
  const userStore = useUserStore()

  // ===== 响应式状态 =====

  const isRouteLoading = ref(false)
  const routeError = ref(null)

  // ===== 计算属性 =====

  /**
   * 当前路由是否有权限访问
   */
  const hasCurrentRoutePermission = computed(() => {
    return hasRoutePermission(route)
  })

  /**
   * 当前用户可访问的路由列表
   */
  const accessibleRoutes = computed(() => {
    return router.getRoutes().filter((route) => {
      return hasRoutePermission(route)
    })
  })

  /**
   * 路由统计信息
   */
  const routeStats = computed(() => {
    return dynamicRouteManager.getRouteStats()
  })

  /**
   * 是否为超级用户
   */
  const isSuperUser = computed(() => userStore.isSuperUser)

  // ===== 路由权限检查方法 =====

  /**
   * 检查路由权限
   * @param {object} routeInfo - 路由信息
   * @returns {boolean}
   */
  const hasRoutePermission = (routeInfo) => {
    // 超级用户拥有所有权限
    if (userStore.isSuperUser) {
      return true
    }

    // 检查路由元信息中的权限要求
    const routePermissions = routeInfo.meta?.permissions
    if (!routePermissions || routePermissions.length === 0) {
      return true // 没有权限要求的路由允许访问
    }

    // 使用权限Store检查权限
    return permissionStore.hasPermission(routePermissions, 'any')
  }

  /**
   * 检查路由路径权限
   * @param {string} path - 路由路径
   * @returns {boolean}
   */
  const hasPathPermission = (path) => {
    const targetRoute = router.getRoutes().find((route) => route.path === path)
    if (!targetRoute) {
      return false
    }
    return hasRoutePermission(targetRoute)
  }

  /**
   * 批量检查路由权限
   * @param {string[]} paths - 路由路径数组
   * @returns {object}
   */
  const batchCheckRoutePermissions = (paths) => {
    const results = {}
    paths.forEach((path) => {
      results[path] = hasPathPermission(path)
    })
    return results
  }

  // ===== 动态路由管理方法 =====

  /**
   * 刷新动态路由
   */
  const refreshRoutes = async () => {
    try {
      isRouteLoading.value = true
      routeError.value = null

      await dynamicRouteManager.refreshDynamicRoutes()

      console.log('路由刷新成功')
    } catch (error) {
      console.error('路由刷新失败:', error)
      routeError.value = error
      throw error
    } finally {
      isRouteLoading.value = false
    }
  }

  /**
   * 重置动态路由
   */
  const resetRoutes = () => {
    try {
      dynamicRouteManager.resetDynamicRoutes()
      console.log('路由重置成功')
    } catch (error) {
      console.error('路由重置失败:', error)
      routeError.value = error
      throw error
    }
  }

  /**
   * 初始化动态路由
   */
  const initializeRoutes = async () => {
    try {
      isRouteLoading.value = true
      routeError.value = null

      await dynamicRouteManager.initialize()

      console.log('路由初始化成功')
    } catch (error) {
      console.error('路由初始化失败:', error)
      routeError.value = error
      throw error
    } finally {
      isRouteLoading.value = false
    }
  }

  // ===== 路由导航方法 =====

  /**
   * 安全导航到指定路由
   * @param {string|object} to - 目标路由
   * @returns {Promise}
   */
  const safeNavigateTo = async (to) => {
    try {
      const targetPath = typeof to === 'string' ? to : to.path

      // 检查目标路由权限
      if (!hasPathPermission(targetPath)) {
        console.warn('没有权限访问目标路由:', targetPath)
        throw new Error(`没有权限访问路由: ${targetPath}`)
      }

      // 执行导航
      await router.push(to)
    } catch (error) {
      console.error('路由导航失败:', error)

      // 如果是权限错误，跳转到403页面
      if (error.message.includes('没有权限')) {
        await router.push('/403')
      } else {
        throw error
      }
    }
  }

  /**
   * 获取用户首页路由
   */
  const getHomeRoute = () => {
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
            const fullPath = firstChild.path.startsWith('/')
              ? firstChild.path
              : `/${menu.path}/${firstChild.path}`

            if (hasPathPermission(fullPath)) {
              return fullPath
            }
          }
        } else if (menu.path && menu.component !== 'Layout') {
          const fullPath = menu.path.startsWith('/') ? menu.path : `/${menu.path}`
          if (hasPathPermission(fullPath)) {
            return fullPath
          }
        }
      }
    }

    // 如果没有找到可访问的菜单，跳转到工作台
    return '/workbench'
  }

  /**
   * 导航到首页
   */
  const navigateToHome = async () => {
    const homeRoute = getHomeRoute()
    await safeNavigateTo(homeRoute)
  }

  // ===== 路由监听 =====

  /**
   * 监听路由变化
   * @param {function} callback - 回调函数
   * @returns {function} - 取消监听函数
   */
  const watchRouteChange = (callback) => {
    return watch(
      () => route.path,
      (newPath, oldPath) => {
        callback(newPath, oldPath, route)
      },
      { immediate: true }
    )
  }

  /**
   * 监听权限变化并刷新路由
   */
  const watchPermissionChange = () => {
    return watch(
      () => permissionStore.allPermissions,
      async (newPermissions, oldPermissions) => {
        if (newPermissions.length !== oldPermissions?.length) {
          console.log('权限发生变化，刷新路由')
          try {
            await refreshRoutes()
          } catch (error) {
            console.error('权限变化后路由刷新失败:', error)
          }
        }
      },
      { deep: true }
    )
  }

  // ===== 路由更新回调 =====

  const routeUpdateCallbacks = ref([])

  /**
   * 添加路由更新回调
   */
  const onRouteUpdate = (callback) => {
    routeUpdateCallbacks.value.push(callback)
    dynamicRouteManager.onRouteUpdate(callback)
  }

  /**
   * 移除路由更新回调
   */
  const offRouteUpdate = (callback) => {
    const index = routeUpdateCallbacks.value.indexOf(callback)
    if (index > -1) {
      routeUpdateCallbacks.value.splice(index, 1)
    }
    dynamicRouteManager.offRouteUpdate(callback)
  }

  // ===== 生命周期 =====

  onMounted(() => {
    // 启动权限变化监听
    watchPermissionChange()
  })

  onUnmounted(() => {
    // 清理路由更新回调
    routeUpdateCallbacks.value.forEach((callback) => {
      dynamicRouteManager.offRouteUpdate(callback)
    })
    routeUpdateCallbacks.value = []
  })

  // ===== 返回接口 =====

  return {
    // 响应式状态
    isRouteLoading,
    routeError,

    // 计算属性
    hasCurrentRoutePermission,
    accessibleRoutes,
    routeStats,
    isSuperUser,

    // 权限检查方法
    hasRoutePermission,
    hasPathPermission,
    batchCheckRoutePermissions,

    // 动态路由管理
    refreshRoutes,
    resetRoutes,
    initializeRoutes,

    // 路由导航
    safeNavigateTo,
    getHomeRoute,
    navigateToHome,

    // 路由监听
    watchRouteChange,
    onRouteUpdate,
    offRouteUpdate,
  }
}

/**
 * 路由权限指令Hook
 */
export function useRoutePermissionDirective() {
  const { hasPathPermission } = useRoutePermission()

  /**
   * 路由权限指令实现
   */
  const routePermissionDirective = {
    mounted(el, binding) {
      const { value, modifiers } = binding

      if (!value) {
        console.warn('v-route-permission指令需要路由路径')
        return
      }

      const hasAuth = hasPathPermission(value)

      if (!hasAuth) {
        if (modifiers.hide) {
          el.style.display = 'none'
        } else if (modifiers.disable) {
          el.disabled = true
          el.style.opacity = '0.5'
          el.style.cursor = 'not-allowed'
        } else {
          el.parentNode?.removeChild(el)
        }
      }
    },

    updated(el, binding) {
      this.mounted(el, binding)
    },
  }

  return {
    routePermissionDirective,
  }
}

export default useRoutePermission
