import { useUserStore, usePermissionStore } from '@/store'
import { getCurrentInstance } from 'vue'
import {
  getPermission,
  getPermissionByPage,
  hasPermission as checkPermissionV2,
  migratePermission,
  isValidPermissionFormat,
} from '@/utils/permission-config-v2'

/**
 * 标准化权限格式
 * 将权限统一为 'METHOD /path' 格式（大写方法名 + 空格 + 路径）
 * @param {string} permission - 原始权限字符串
 * @returns {string} 标准化后的权限字符串
 */
function normalizePermission(permission) {
  if (!permission || typeof permission !== 'string') {
    return permission
  }

  // 如果已经是标准格式（METHOD /path），直接返回
  if (/^[A-Z]+\s\//.test(permission)) {
    return permission
  }

  // 处理 'method/path' 格式（V1 API 返回格式）
  const methodPathMatch = permission.match(/^(get|post|put|delete|patch)(\/.*)/i)
  if (methodPathMatch) {
    const method = methodPathMatch[1].toUpperCase()
    const path = methodPathMatch[2]
    return `${method} ${path}`
  }

  // 处理其他可能的格式
  return permission
}

/**
 * 检查用户是否具有指定权限 (支持v2格式)
 * @param {string|Array} permission - 权限标识符或权限数组
 * @param {string} mode - 检查模式: 'any' (任一权限) 或 'all' (所有权限)
 * @returns {boolean} 是否具有权限
 */
function hasPermission(permission, mode = 'any') {
  const userStore = useUserStore()
  const userPermissionStore = usePermissionStore()

  const accessApis = userPermissionStore.apis

  console.log('=== 权限检查开始 ===')
  console.log('检查权限:', permission)
  console.log('检查模式:', mode)
  console.log('用户信息:', userStore.userInfo)
  console.log('是否超级管理员:', userStore.isSuperUser)
  console.log('用户权限列表:', accessApis)
  console.log('权限加载状态:', userPermissionStore.isLoadingApis)
  console.log('Token值:', userStore.token)
  console.log('Token类型:', typeof userStore.token)
  console.log('Token长度:', userStore.token ? userStore.token.length : 'null')

  // 首先检查是否有token
  if (!userStore.token) {
    console.log('无token，拒绝访问')
    return false
  }

  // 超级管理员拥有所有权限 - 这是最高优先级
  if (userStore.isSuperUser) {
    console.log('超级管理员，直接通过权限检查')
    return true
  }

  // 如果权限数据正在加载中，允许显示（避免闪烁）
  if (userPermissionStore.isLoadingApis) {
    console.log('权限数据加载中，允许显示')
    return true
  }

  // 如果权限数据为空且不在加载中，尝试重新加载权限
  if (!accessApis || accessApis.length === 0) {
    console.log('权限数据为空，尝试重新加载权限数据')

    // 检查是否正在登出，如果是则跳过权限重新加载
    if (userStore.isLoggingOut) {
      console.log('正在登出，跳过权限重新加载')
      return false
    }

    // 再次检查token是否存在（可能在检查过程中被清除）
    if (!userStore.token) {
      console.log('token已被清除，跳过权限重新加载')
      return false
    }

    // 检测到token存在，异步重新加载权限数据（只执行一次）
    if (!userPermissionStore._isReloading) {
      console.log('检测到token存在，异步重新加载权限数据')
      userPermissionStore._isReloading = true
      userPermissionStore
        .getAccessApis()
        .catch((error) => {
          console.error('重新加载权限数据失败:', error)
          // 如果是401错误且不在登出状态，可能需要重新登录
          if (error.response?.status === 401 && !userStore.isLoggingOut) {
            console.log('权限加载401错误，可能需要重新登录')
          }
        })
        .finally(() => {
          userPermissionStore._isReloading = false
        })
    }

    // 有token但权限数据为空，暂时允许访问，避免界面卡死
    console.log('有token但权限数据为空，暂时允许访问')
    return true
  }

  // 标准化用户权限列表
  const normalizedAccessApis = accessApis.map((api) => normalizePermission(api))
  console.log('标准化后的用户权限列表:', normalizedAccessApis)

  // 处理单个权限
  if (typeof permission === 'string') {
    const normalizedPermission = normalizePermission(permission)
    // 尝试迁移旧权限格式
    const migratedPermission = normalizePermission(migratePermission(permission))
    console.log('标准化后的权限:', normalizedPermission)
    console.log('迁移后的权限:', migratedPermission)

    const hasAccess =
      normalizedAccessApis.includes(normalizedPermission) ||
      normalizedAccessApis.includes(migratedPermission)
    console.log('单个权限检查结果:', hasAccess)
    return hasAccess
  }

  // 处理权限数组
  if (Array.isArray(permission)) {
    console.log('处理权限数组，模式:', mode)
    let hasAccess
    if (mode === 'all') {
      // 需要拥有所有权限
      hasAccess = permission.every((perm) => {
        const normalizedPerm = normalizePermission(perm)
        const migratedPerm = normalizePermission(migratePermission(perm))
        const result =
          normalizedAccessApis.includes(normalizedPerm) ||
          normalizedAccessApis.includes(migratedPerm)
        console.log(`权限 ${perm} 检查结果:`, result)
        return result
      })
      console.log('权限数组检查结果(all模式):', hasAccess)
    } else {
      // 只需要拥有任一权限
      hasAccess = permission.some((perm) => {
        const normalizedPerm = normalizePermission(perm)
        const migratedPerm = normalizePermission(migratePermission(perm))
        const result =
          normalizedAccessApis.includes(normalizedPerm) ||
          normalizedAccessApis.includes(migratedPerm)
        console.log(`权限 ${perm} 检查结果:`, result)
        return result
      })
      console.log('权限数组检查结果(any模式):', hasAccess)
    }
    return hasAccess
  }

  // 处理对象格式权限 { action: 'create', resource: 'api' }
  if (typeof permission === 'object' && permission !== null && !Array.isArray(permission)) {
    if (permission.resource && permission.action) {
      console.log('处理对象格式权限:', permission)
      // 使用 hasButtonPermission 处理对象格式
      const result = hasButtonPermission(permission.resource, permission.action)
      console.log('对象权限检查结果:', result)
      return result
    }
  }

  console.log('权限检查失败，未知权限格式')
  return false
}

/**
 * 检查按钮级权限 (支持v2格式)
 * @param {string} resource - 资源名称
 * @param {string} action - 操作类型 (create, read, update, delete)
 * @returns {boolean} 是否具有权限
 */
function hasButtonPermission(resource, action) {
  const userStore = useUserStore()
  const userPermissionStore = usePermissionStore()

  // 超级管理员拥有所有权限
  if (userStore.isSuperUser) {
    return true
  }

  // 如果权限数据正在加载中，允许显示（避免闪烁）
  if (userPermissionStore.isLoadingApis) {
    return true
  }

  // 优先使用v2权限配置
  const v2Permission = getPermission(resource, action)
  if (v2Permission) {
    return hasPermission(v2Permission)
  }

  // 回退到旧的权限检查逻辑
  const accessApis = userPermissionStore.apis

  // 检查精确匹配的权限
  const hasExactPermission = accessApis.some((api) => {
    return api.includes(resource) && api.includes(action)
  })

  if (hasExactPermission) {
    return true
  }

  // 检查通用权限模式
  const methodMap = {
    create: 'POST',
    read: 'GET',
    update: 'PUT',
    delete: 'DELETE',
  }

  const method = methodMap[action]
  if (method) {
    return accessApis.some((api) => {
      const [apiMethod, apiPath] = api.split(' ')
      return apiMethod === method && apiPath.includes(resource)
    })
  }

  return false
}

/**
 * 检查页面权限 (v2新增)
 * @param {string} pagePath - 页面路径
 * @param {string} action - 操作类型
 * @returns {boolean} 是否具有权限
 */
function hasPagePermission(pagePath, action) {
  const v2Permission = getPermissionByPage(pagePath, action)
  return v2Permission ? hasPermission(v2Permission) : false
}

/**
 * 检查角色权限
 * @param {string|Array} roles - 角色名称或角色数组
 * @param {string} mode - 检查模式: 'any' (任一角色) 或 'all' (所有角色)
 * @returns {boolean} 是否具有角色
 */
function hasRole(roles, mode = 'any') {
  const userStore = useUserStore()

  // 超级管理员拥有所有角色
  if (userStore.isSuperUser) {
    return true
  }

  const userRoles = userStore.userInfo?.roles || []
  const roleNames = userRoles.map((role) => role.name)

  // 处理单个角色
  if (typeof roles === 'string') {
    return roleNames.includes(roles)
  }

  // 处理角色数组
  if (Array.isArray(roles)) {
    if (mode === 'all') {
      return roles.every((role) => roleNames.includes(role))
    } else {
      return roles.some((role) => roleNames.includes(role))
    }
  }

  return false
}

// 基础操作列表 - 这些操作通常不需要严格的权限控制
const basicOperations = ['search', 'query', 'reset', 'clear', 'refresh', 'read']

// 检查是否为基础操作
const isBasicOperation = (action) => {
  if (!action) return false
  return basicOperations.includes(action.toLowerCase())
}

export default function setupPermissionDirective(app) {
  // 存储元素的原始状态
  const elementStates = new WeakMap()
  // 存储路由监听器
  const routeWatchers = new WeakMap()

  function saveElementState(el) {
    if (!elementStates.has(el)) {
      elementStates.set(el, {
        display: el.style.display,
        opacity: el.style.opacity,
        cursor: el.style.cursor,
        disabled: el.disabled,
        parentNode: el.parentNode,
        nextSibling: el.nextSibling,
      })
    }
  }

  function restoreElementState(el) {
    const state = elementStates.get(el)
    if (state) {
      el.style.display = state.display
      el.style.opacity = state.opacity
      el.style.cursor = state.cursor
      if (typeof el.disabled !== 'undefined') {
        el.disabled = state.disabled
      }
    }
  }

  function updateElVisible(el, binding) {
    const { value, modifiers, arg } = binding

    if (!value) {
      throw new Error(`权限指令需要值: 如 v-permission="'GET /api/v2/users'"`)
    }

    // 检查是否正在登出，如果是则跳过权限检查
    const userStore = useUserStore()
    if (userStore.isLoggingOut) {
      console.log('权限指令: 正在登出中，跳过updateElVisible权限检查')
      return
    }

    // 检查token是否存在，如果不存在则跳过权限检查
    if (!userStore.token) {
      console.log('权限指令: 无token，跳过updateElVisible权限检查')
      return
    }

    // 保存元素原始状态
    saveElementState(el)

    let hasAccess = false

    try {
      // 根据修饰符确定检查类型
      if (modifiers.role) {
        // 角色权限检查: v-permission.role="'admin'"
        hasAccess = hasRole(value, modifiers.all ? 'all' : 'any')
      } else if (modifiers.button) {
        // 按钮权限检查: v-permission.button="{ resource: 'users', action: 'create' }"
        if (typeof value === 'object' && value.resource && value.action) {
          hasAccess = hasButtonPermission(value.resource, value.action)
        } else {
          console.warn('按钮权限检查需要 { resource: string, action: string } 格式')
          hasAccess = false
        }
      } else if (modifiers.page) {
        // 页面权限检查: v-permission.page="{ path: '/system/user', action: 'read' }"
        if (typeof value === 'object' && value.path && value.action) {
          hasAccess = hasPagePermission(value.path, value.action)
        } else {
          console.warn('页面权限检查需要 { path: string, action: string } 格式')
          hasAccess = false
        }
      } else if (modifiers.v2) {
        // 强制使用v2权限检查: v-permission.v2="{ resource: 'users', action: 'read' }"
        if (typeof value === 'object' && value.resource && value.action) {
          const v2Permission = getPermission(value.resource, value.action)
          hasAccess = v2Permission
            ? hasPermission(v2Permission, modifiers.all ? 'all' : 'any')
            : false
        } else if (typeof value === 'string') {
          // 验证是否为v2格式
          if (isValidPermissionFormat(value)) {
            hasAccess = hasPermission(value, modifiers.all ? 'all' : 'any')
          } else {
            console.warn('v2权限格式无效:', value)
            hasAccess = false
          }
        }
      } else {
        // 默认API权限检查: v-permission="'GET /api/v2/users'"
        hasAccess = hasPermission(value, modifiers.all ? 'all' : 'any')
      }
    } catch (error) {
      console.error('权限检查出错:', error)
      hasAccess = false
    }

    // 检查是否为页面级权限控制（应用在页面根元素上）
    const isPageLevel =
      el.classList.contains('page-container') ||
      el.classList.contains('main-content') ||
      el.tagName === 'MAIN' ||
      el.id === 'app' ||
      el.parentElement?.tagName === 'BODY'

    // 添加详细的权限指令调试信息
    console.log('=== 权限指令DOM操作 ===', {
      element: el.tagName,
      elementText: el.textContent?.trim(),
      permission: value,
      hasAccess: hasAccess,
      modifiers: modifiers,
      isPageLevel: isPageLevel,
      elementInDOM: !!el.parentNode,
      elementDisplay: el.style.display,
      elementVisible: el.style.visibility,
    })

    // 根据权限结果显示/隐藏元素
    if (!hasAccess) {
      console.log('权限检查失败，隐藏元素:', el.textContent?.trim())
      // 根据修饰符决定隐藏方式
      if (modifiers.hide || isPageLevel) {
        // v-permission.hide 或页面级权限 - 隐藏但保留DOM结构
        el.style.display = 'none'
        el.setAttribute('data-permission-hidden', 'true')
      } else if (modifiers.disable) {
        // v-permission.disable - 禁用元素
        if (typeof el.disabled !== 'undefined') {
          el.disabled = true
        }
        el.style.opacity = '0.5'
        el.style.cursor = 'not-allowed'

        // 添加禁用类名
        el.classList.add('permission-disabled')
      } else if (modifiers.invisible) {
        // v-permission.invisible - 设置为不可见但保留空间
        el.style.visibility = 'hidden'
      } else {
        // 默认行为 - 从DOM中移除
        if (el.parentElement) {
          el.parentElement.removeChild(el)
          el.setAttribute('data-permission-removed', 'true')
        }
      }
    } else {
      console.log('权限检查成功，显示元素:', el.textContent?.trim())
      // 有权限时恢复元素状态
      if (modifiers.hide || isPageLevel) {
        el.style.display = ''
        el.removeAttribute('data-permission-hidden')
        console.log('恢复元素显示 (hide模式)')
      } else if (modifiers.disable) {
        if (typeof el.disabled !== 'undefined') {
          el.disabled = false
        }
        el.style.opacity = ''
        el.style.cursor = ''
        el.classList.remove('permission-disabled')
        console.log('恢复元素启用 (disable模式)')
      } else if (modifiers.invisible) {
        el.style.visibility = ''
        console.log('恢复元素可见 (invisible模式)')
      } else {
        // 如果元素被移除了，需要重新插入
        const state = elementStates.get(el)
        if (state && !el.parentNode && state.parentNode) {
          if (state.nextSibling) {
            state.parentNode.insertBefore(el, state.nextSibling)
          } else {
            state.parentNode.appendChild(el)
          }
          el.removeAttribute('data-permission-removed')
          console.log('重新插入被移除的元素')
        } else {
          console.log('元素已在DOM中，无需操作')
        }
      }
    }

    // 开发环境调试信息
    if (process.env.NODE_ENV === 'development') {
      console.debug('Permission Directive v2:', {
        element: el.tagName,
        elementId: el.id,
        elementClass: el.className,
        value,
        modifiers,
        hasAccess,
        isPageLevel,
        action: hasAccess ? 'show' : 'hide',
        currentRoute: window.location.pathname,
        elementInDOM: !!el.parentNode,
        elementDisplay: el.style.display,
        permissionHidden: el.getAttribute('data-permission-hidden'),
        permissionRemoved: el.getAttribute('data-permission-removed'),
      })
    }
  }

  const permissionDirective = {
    mounted(el, binding) {
      updateElVisible(el, binding)

      // 监听全局权限重新验证事件
      const handlePermissionRevalidate = async () => {
        console.log('权限指令: 收到权限重新验证事件', {
          element: el.tagName,
          permission: binding.value,
        })

        // 检查是否正在登出，如果是则跳过权限重新验证
        const userStore = useUserStore()
        if (userStore.isLoggingOut) {
          console.log('权限指令: 正在登出中，跳过权限重新验证')
          return
        }

        // 检查token是否存在，如果不存在则跳过权限重新验证
        if (!userStore.token) {
          console.log('权限指令: 无token，跳过权限重新验证')
          return
        }

        // 获取权限store实例
        const permissionStore = usePermissionStore()

        // 如果权限正在加载，等待加载完成
        if (permissionStore.isLoadingApis) {
          console.log('权限指令: 权限正在加载中，等待加载完成...')
          const maxWaitTime = 3000 // 最大等待3秒
          const startTime = Date.now()

          while (permissionStore.isLoadingApis && Date.now() - startTime < maxWaitTime) {
            await new Promise((resolve) => setTimeout(resolve, 100))
          }

          if (permissionStore.isLoadingApis) {
            console.warn('权限指令: 权限加载超时，继续执行权限检查')
          }
        }

        // 如果权限数据为空，尝试重新加载
        if (!permissionStore.apis || permissionStore.apis.length === 0) {
          console.log('权限指令: 权限数据为空，尝试重新加载...')
          try {
            await permissionStore.getAccessApis()
          } catch (error) {
            console.error('权限指令: 重新加载权限数据失败:', error)
          }
        }

        // 延迟执行权限检查，确保DOM和数据都已准备好
        setTimeout(() => {
          updateElVisible(el, binding)
        }, 50)
      }

      window.addEventListener('permission-revalidate', handlePermissionRevalidate)

      // 添加路由监听器，确保路由变化时重新检查权限
      let unwatch = null
      const instance = getCurrentInstance()
      if (instance && instance.proxy.$route) {
        unwatch = instance.proxy.$watch(
          () => instance.proxy.$route.path,
          () => {
            // 路由变化时重新检查权限
            setTimeout(() => {
              updateElVisible(el, binding)
            }, 0)
          },
          { immediate: false }
        )
      }

      // 存储监听器以便清理
      routeWatchers.set(el, {
        unwatch,
        eventListener: handlePermissionRevalidate,
      })
    },
    beforeUpdate(el, binding) {
      // 检查是否正在登出，如果是则跳过权限检查
      const userStore = useUserStore()
      if (userStore.isLoggingOut) {
        console.log('权限指令: 正在登出中，跳过beforeUpdate权限检查')
        return
      }

      // 检查token是否存在，如果不存在则跳过权限检查
      if (!userStore.token) {
        console.log('权限指令: 无token，跳过beforeUpdate权限检查')
        return
      }

      updateElVisible(el, binding)
    },
    unmounted(el) {
      // 清理路由监听器和事件监听器
      const watchers = routeWatchers.get(el)
      if (watchers) {
        if (typeof watchers === 'function') {
          // 兼容旧的单一unwatch函数
          watchers()
        } else if (watchers.unwatch) {
          // 新的对象格式
          watchers.unwatch()
        }

        if (watchers.eventListener) {
          window.removeEventListener('permission-revalidate', watchers.eventListener)
        }

        routeWatchers.delete(el)
      }
      // 清理元素状态
      elementStates.delete(el)
    },
  }

  app.directive('permission', permissionDirective)
}

// 导出权限检查函数供组合式API使用
export { hasPermission, hasButtonPermission, hasPagePermission, hasRole }
