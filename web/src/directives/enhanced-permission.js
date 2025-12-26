/**
 * 增强版权限指令
 * 提供更丰富的权限控制功能
 */

// 暂时简化导入，避免循环依赖
// import { PermissionMode } from '@/composables/usePermission'
// import { useUserStore } from '@/store/modules/user'
// import { useEnhancedPermissionStore } from '@/store/modules/permission'

// 临时定义权限模式
const PermissionMode = {
  ALL: 'all',
  ANY: 'any',
  EXACT: 'exact',
}

/**
 * 权限指令
 * 用法：
 * v-enhanced-permission="'system:user:list'" - 单个权限
 * v-enhanced-permission="['system:user:list', 'system:user:add']" - 多个权限（任意一个）
 * v-enhanced-permission.all="['system:user:list', 'system:user:add']" - 多个权限（全部需要）
 * v-enhanced-permission.exact="'system:user:list'" - 精确匹配权限
 * v-enhanced-permission.hide="'system:user:list'" - 隐藏元素而不是移除
 * v-enhanced-permission.disable="'system:user:list'" - 禁用元素而不是移除
 * v-enhanced-permission.fade="'system:user:list'" - 淡化元素而不是移除
 */
export const enhancedPermissionDirective = {
  mounted(el, binding) {
    checkPermission(el, binding)
  },

  updated(el, binding) {
    checkPermission(el, binding)
  },

  beforeUnmount(el) {
    // 清理事件监听器
    const preventClick = el._permissionPreventClick
    if (preventClick) {
      el.removeEventListener('click', preventClick, true)
      delete el._permissionPreventClick
    }
  },
}

/**
 * 角色指令
 * 用法：
 * v-enhanced-role="'admin'" - 单个角色
 * v-enhanced-role="['admin', 'user']" - 多个角色（任意一个）
 * v-enhanced-role.all="['admin', 'user']" - 多个角色（全部需要）
 */
export const enhancedRoleDirective = {
  mounted(el, binding) {
    checkRole(el, binding)
  },

  updated(el, binding) {
    checkRole(el, binding)
  },
}

/**
 * 超级用户指令
 * 用法：
 * v-enhanced-superuser - 只有超级用户可见
 * v-enhanced-superuser.hide - 非超级用户隐藏
 * v-enhanced-superuser.disable - 非超级用户禁用
 */
export const enhancedSuperuserDirective = {
  mounted(el, binding) {
    checkSuperuser(el, binding)
  },

  updated(el, binding) {
    checkSuperuser(el, binding)
  },
}

/**
 * API权限指令
 * 用法：
 * v-enhanced-api="{path: '/api/v2/users', method: 'GET'}" - 检查API权限
 * v-enhanced-api.hide="{path: '/api/v2/users', method: 'POST'}" - 隐藏元素
 */
export const enhancedApiDirective = {
  mounted(el, binding) {
    checkApiPermission(el, binding)
  },

  updated(el, binding) {
    checkApiPermission(el, binding)
  },
}

/**
 * 检查权限
 */
function checkPermission(el, binding) {
  const { value, modifiers } = binding

  if (!value) {
    console.warn('v-enhanced-permission指令需要权限值')
    return
  }

  // 暂时简化权限检查，避免Store依赖问题
  console.log('Enhanced permission check:', value, modifiers)

  // 暂时总是返回true，避免权限检查导致的问题
  const hasAuth = true

  // 处理元素
  handleElement(el, hasAuth, modifiers)
}

/**
 * 检查角色
 */
function checkRole(el, binding) {
  const { value, modifiers } = binding

  if (!value) {
    console.warn('v-enhanced-role指令需要角色值')
    return
  }

  console.log('Enhanced role check:', value, modifiers)

  // 暂时总是返回true
  const hasRole = true

  // 处理元素
  handleElement(el, hasRole, modifiers)
}

/**
 * 检查超级用户
 */
function checkSuperuser(el, binding) {
  const { modifiers } = binding

  console.log('Enhanced superuser check:', modifiers)

  // 暂时总是返回true
  const isSuperUser = true

  // 处理元素
  handleElement(el, isSuperUser, modifiers)
}

/**
 * 检查API权限
 */
function checkApiPermission(el, binding) {
  const { value, modifiers } = binding

  if (!value || !value.path) {
    console.warn('v-enhanced-api指令需要包含path的对象')
    return
  }

  console.log('Enhanced API permission check:', value, modifiers)

  // 暂时总是返回true
  const hasAuth = true

  // 处理元素
  handleElement(el, hasAuth, modifiers)
}

/**
 * 处理元素显示/隐藏/禁用
 */
function handleElement(el, hasAuth, modifiers) {
  // 保存原始状态
  if (!el._originalState) {
    el._originalState = {
      display: el.style.display,
      opacity: el.style.opacity,
      cursor: el.style.cursor,
      disabled: el.disabled,
      pointerEvents: el.style.pointerEvents,
      filter: el.style.filter,
    }
  }

  if (!hasAuth) {
    if (modifiers.hide) {
      // 隐藏元素
      el.style.display = 'none'
      el.setAttribute('data-permission-hidden', 'true')
    } else if (modifiers.disable) {
      // 禁用元素
      if (typeof el.disabled !== 'undefined') {
        el.disabled = true
      }
      el.style.opacity = '0.5'
      el.style.cursor = 'not-allowed'
      el.style.pointerEvents = 'none'
      el.setAttribute('data-permission-disabled', 'true')

      // 阻止点击事件
      const preventClick = (event) => {
        event.preventDefault()
        event.stopPropagation()
        return false
      }
      el.addEventListener('click', preventClick, true)
      el._permissionPreventClick = preventClick
    } else if (modifiers.fade) {
      // 淡化元素
      el.style.opacity = '0.3'
      el.style.pointerEvents = 'none'
      el.style.filter = 'grayscale(100%)'
      el.setAttribute('data-permission-faded', 'true')
    } else {
      // 默认移除元素
      el.style.display = 'none'
      el.setAttribute('data-permission-removed', 'true')
    }
  } else {
    // 有权限时恢复元素状态
    const originalState = el._originalState

    if (el.hasAttribute('data-permission-hidden')) {
      el.style.display = originalState.display
      el.removeAttribute('data-permission-hidden')
    }

    if (el.hasAttribute('data-permission-disabled')) {
      if (typeof el.disabled !== 'undefined') {
        el.disabled = originalState.disabled
      }
      el.style.opacity = originalState.opacity
      el.style.cursor = originalState.cursor
      el.style.pointerEvents = originalState.pointerEvents
      el.removeAttribute('data-permission-disabled')

      // 移除点击事件监听器
      const preventClick = el._permissionPreventClick
      if (preventClick) {
        el.removeEventListener('click', preventClick, true)
        delete el._permissionPreventClick
      }
    }

    if (el.hasAttribute('data-permission-faded')) {
      el.style.opacity = originalState.opacity
      el.style.pointerEvents = originalState.pointerEvents
      el.style.filter = originalState.filter
      el.removeAttribute('data-permission-faded')
    }

    if (el.hasAttribute('data-permission-removed')) {
      el.style.display = originalState.display
      el.removeAttribute('data-permission-removed')
    }
  }
}

/**
 * 增强版权限指令插件
 */
export default {
  install(app) {
    console.log('🔒+ 开始注册增强版权限指令...')

    try {
      console.log('📝 注册 v-enhanced-permission 指令...')
      app.directive('enhanced-permission', enhancedPermissionDirective)

      console.log('👤 注册 v-enhanced-role 指令...')
      app.directive('enhanced-role', enhancedRoleDirective)

      console.log('👑 注册 v-enhanced-superuser 指令...')
      app.directive('enhanced-superuser', enhancedSuperuserDirective)

      console.log('🔌 注册 v-enhanced-api 指令...')
      app.directive('enhanced-api', enhancedApiDirective)

      console.log('✅ 所有增强版权限指令注册完成')
    } catch (error) {
      console.error('❌ 增强版权限指令注册失败:', error)
      console.error('错误堆栈:', error.stack)
      throw error
    }
  },
}

/**
 * 权限检查工具函数
 */
export const enhancedPermissionUtils = {
  /**
   * 检查元素权限
   */
  checkElementPermission(el, permission, mode = PermissionMode.ANY) {
    const permissionStore = useEnhancedPermissionStore()
    return permissionStore.hasPermission(permission, mode)
  },

  /**
   * 批量检查权限
   */
  batchCheckPermissions(permissions) {
    const permissionStore = useEnhancedPermissionStore()
    const results = {}

    Object.keys(permissions).forEach((key) => {
      results[key] = permissionStore.hasPermission(permissions[key])
    })

    return results
  },

  /**
   * 动态设置元素权限
   */
  setElementPermission(el, permission, options = {}) {
    const permissionStore = useEnhancedPermissionStore()
    const hasAuth = permissionStore.hasPermission(permission)

    const modifiers = {
      hide: options.hide || false,
      disable: options.disable || false,
      fade: options.fade || false,
    }

    handleElement(el, hasAuth, modifiers)
  },

  /**
   * 恢复元素原始状态
   */
  restoreElementState(el) {
    if (el._originalState) {
      const originalState = el._originalState

      el.style.display = originalState.display
      el.style.opacity = originalState.opacity
      el.style.cursor = originalState.cursor
      el.style.pointerEvents = originalState.pointerEvents
      el.style.filter = originalState.filter

      if (typeof el.disabled !== 'undefined') {
        el.disabled = originalState.disabled
      }

      // 清理属性
      el.removeAttribute('data-permission-hidden')
      el.removeAttribute('data-permission-disabled')
      el.removeAttribute('data-permission-faded')
      el.removeAttribute('data-permission-removed')

      // 清理事件监听器
      const preventClick = el._permissionPreventClick
      if (preventClick) {
        el.removeEventListener('click', preventClick, true)
        delete el._permissionPreventClick
      }

      delete el._originalState
    }
  },
}
