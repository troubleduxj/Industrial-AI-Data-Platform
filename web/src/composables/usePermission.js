/**
 * 权限管理Composable
 * 提供权限检查、权限数据管理等功能
 */

import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import {
  useEnhancedPermissionStore,
  PermissionType,
  PermissionMode,
} from '@/store/modules/permission/enhanced-permission-store'
import { useUserStore } from '@/store/modules/user'

/**
 * 权限管理Hook
 */
export function usePermission() {
  const permissionStore = useEnhancedPermissionStore()
  const userStore = useUserStore()

  // ===== 权限检查方法 =====

  /**
   * 检查是否有权限
   * @param {string|string[]} permissions - 权限标识
   * @param {string} mode - 检查模式
   * @returns {boolean}
   */
  const hasPermission = (permissions, mode = PermissionMode.ANY) => {
    return permissionStore.hasPermission(permissions, mode)
  }

  /**
   * 检查菜单权限
   * @param {string} permission - 菜单权限标识
   * @returns {boolean}
   */
  const hasMenuPermission = (permission) => {
    return permissionStore.hasMenuPermission(permission)
  }

  /**
   * 检查API权限
   * @param {string} apiPath - API路径
   * @param {string} method - HTTP方法
   * @returns {boolean}
   */
  const hasApiPermission = (apiPath, method = 'GET') => {
    return permissionStore.hasApiPermission(apiPath, method)
  }

  /**
   * 检查按钮权限
   * @param {string} permission - 按钮权限标识
   * @returns {boolean}
   */
  const hasButtonPermission = (permission) => {
    return permissionStore.hasButtonPermission(permission)
  }

  /**
   * 检查路由权限
   * @param {object} route - 路由对象
   * @returns {boolean}
   */
  const hasRoutePermission = (route) => {
    return permissionStore.hasRoutePermission(route)
  }

  // ===== 响应式权限状态 =====

  /**
   * 是否为超级用户
   */
  const isSuperUser = computed(() => userStore.isSuperUser)

  /**
   * 权限加载状态
   */
  const isLoadingPermissions = computed(() => permissionStore.isLoading)

  /**
   * 用户所有权限
   */
  const userPermissions = computed(() => permissionStore.allPermissions)

  /**
   * 用户菜单权限
   */
  const userMenuPermissions = computed(() => permissionStore.menuPermissions)

  /**
   * 用户API权限
   */
  const userApiPermissions = computed(() => permissionStore.accessApis)

  /**
   * 权限统计信息
   */
  const permissionStats = computed(() => permissionStore.getPermissionStats())

  // ===== 权限数据管理 =====

  /**
   * 刷新权限数据
   */
  const refreshPermissions = async () => {
    try {
      await permissionStore.refreshPermissions()
    } catch (error) {
      console.error('刷新权限数据失败:', error)
      throw error
    }
  }

  /**
   * 初始化权限数据
   */
  const initPermissions = async () => {
    try {
      console.log('初始化权限数据')

      // 并行获取权限数据
      await Promise.all([permissionStore.getUserMenus(), permissionStore.getAccessApis()])

      console.log('权限数据初始化完成')
    } catch (error) {
      console.error('初始化权限数据失败:', error)
      throw error
    }
  }

  // ===== 权限工具方法 =====

  /**
   * 创建权限检查器
   * @param {string|string[]} permissions - 权限标识
   * @param {string} mode - 检查模式
   * @returns {function}
   */
  const createPermissionChecker = (permissions, mode = PermissionMode.ANY) => {
    return () => hasPermission(permissions, mode)
  }

  /**
   * 创建响应式权限检查器
   * @param {string|string[]} permissions - 权限标识
   * @param {string} mode - 检查模式
   * @returns {ComputedRef<boolean>}
   */
  const createReactivePermissionChecker = (permissions, mode = PermissionMode.ANY) => {
    return computed(() => hasPermission(permissions, mode))
  }

  /**
   * 批量权限检查
   * @param {object} permissionMap - 权限映射对象
   * @returns {object}
   */
  const batchCheckPermissions = (permissionMap) => {
    const results = {}

    Object.keys(permissionMap).forEach((key) => {
      const permission = permissionMap[key]
      results[key] = hasPermission(permission)
    })

    return results
  }

  // ===== 权限监听 =====

  /**
   * 监听权限变化
   * @param {function} callback - 回调函数
   * @returns {function} - 取消监听函数
   */
  const watchPermissions = (callback) => {
    const stopWatcher = watch(
      () => permissionStore.allPermissions,
      (newPermissions, oldPermissions) => {
        callback(newPermissions, oldPermissions)
      },
      { deep: true }
    )

    return stopWatcher
  }

  // ===== 返回接口 =====

  return {
    // 权限检查方法
    hasPermission,
    hasMenuPermission,
    hasApiPermission,
    hasButtonPermission,
    hasRoutePermission,

    // 响应式状态
    isSuperUser,
    isLoadingPermissions,
    userPermissions,
    userMenuPermissions,
    userApiPermissions,
    permissionStats,

    // 权限数据管理
    refreshPermissions,
    initPermissions,

    // 权限工具方法
    createPermissionChecker,
    createReactivePermissionChecker,
    batchCheckPermissions,

    // 权限监听
    watchPermissions,

    // 常量
    PermissionType,
    PermissionMode,
  }
}

/**
 * 权限指令Hook
 * 用于创建v-permission指令
 */
export function usePermissionDirective() {
  const { hasPermission } = usePermission()

  /**
   * 权限指令实现
   */
  const permissionDirective = {
    mounted(el, binding) {
      const { value, modifiers } = binding

      if (!value) {
        console.warn('v-permission指令需要权限值')
        return
      }

      // 确定检查模式
      let mode = PermissionMode.ANY
      if (modifiers.all) {
        mode = PermissionMode.ALL
      } else if (modifiers.exact) {
        mode = PermissionMode.EXACT
      }

      // 检查权限
      const hasAuth = hasPermission(value, mode)

      if (!hasAuth) {
        // 根据修饰符决定处理方式
        if (modifiers.hide) {
          // 隐藏元素
          el.style.display = 'none'
        } else if (modifiers.disable) {
          // 禁用元素
          el.disabled = true
          el.style.opacity = '0.5'
          el.style.cursor = 'not-allowed'
        } else {
          // 默认移除元素
          el.parentNode?.removeChild(el)
        }
      }
    },

    updated(el, binding) {
      // 权限更新时重新检查
      this.mounted(el, binding)
    },
  }

  return {
    permissionDirective,
  }
}

/**
 * 权限按钮Hook
 * 用于创建权限控制的按钮组件
 */
export function usePermissionButton() {
  const { hasPermission, hasButtonPermission } = usePermission()

  /**
   * 创建权限按钮属性
   * @param {string|string[]} permissions - 权限标识
   * @param {object} options - 选项
   * @returns {object}
   */
  const createButtonProps = (permissions, options = {}) => {
    const {
      mode = PermissionMode.ANY,
      hideWhenNoPermission = false,
      disableWhenNoPermission = true,
      showTooltipWhenNoPermission = true,
    } = options

    const hasAuth = computed(() => {
      if (typeof permissions === 'string' && permissions.includes('button:')) {
        return hasButtonPermission(permissions)
      }
      return hasPermission(permissions, mode)
    })

    const buttonProps = computed(() => ({
      disabled: !hasAuth.value && disableWhenNoPermission,
      style: {
        display: !hasAuth.value && hideWhenNoPermission ? 'none' : undefined,
        opacity: !hasAuth.value && disableWhenNoPermission ? 0.5 : undefined,
        cursor: !hasAuth.value && disableWhenNoPermission ? 'not-allowed' : undefined,
      },
      title: !hasAuth.value && showTooltipWhenNoPermission ? '权限不足' : undefined,
    }))

    return {
      hasAuth,
      buttonProps,
    }
  }

  return {
    createButtonProps,
  }
}

export default usePermission
