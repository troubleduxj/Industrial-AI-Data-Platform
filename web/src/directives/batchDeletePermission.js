/**
 * 批量删除权限指令
 *
 * 提供Vue指令形式的权限控制，包括：
 * - v-batch-delete-permission 指令
 * - 元素显示/隐藏控制
 * - 权限状态绑定
 *
 * 需求映射：
 * - 需求6.1: 前端权限控制
 * - 需求6.5: 权限一致性
 */

import { useUserStore } from '@/store/modules/user'
import { BatchDeletePermissionUtils } from '@/composables/useBatchDeletePermission'

/**
 * 批量删除权限指令
 *
 * 用法：
 * v-batch-delete-permission="'api'"
 * v-batch-delete-permission="{ resource: 'api', conditions: ['exclude_system_items'] }"
 * v-batch-delete-permission:hide="'dict_type'"
 * v-batch-delete-permission:disable="'system_param'"
 */
const batchDeletePermission = {
  /**
   * 指令挂载时
   */
  async mounted(el, binding) {
    await updateElementPermission(el, binding)
  },

  /**
   * 指令更新时
   */
  async updated(el, binding) {
    await updateElementPermission(el, binding)
  },
}

/**
 * 更新元素权限状态
 */
async function updateElementPermission(el, binding) {
  try {
    const userStore = useUserStore()

    // 解析指令参数
    const config = parseDirectiveConfig(binding.value)
    const modifier = Object.keys(binding.modifiers)[0] || 'hide'

    // 超级管理员直接通过
    if (userStore.userInfo?.is_superuser) {
      applyPermissionResult(el, true, modifier)
      return
    }

    // 检查权限
    const hasPermission = await BatchDeletePermissionUtils.hasPermission(
      config.resource,
      config.conditions
    )

    // 应用权限结果
    applyPermissionResult(el, hasPermission, modifier)

    // 添加权限状态属性
    el.setAttribute('data-batch-delete-permission', hasPermission ? 'allowed' : 'denied')
    el.setAttribute('data-resource-type', config.resource)
  } catch (error) {
    console.error('批量删除权限指令执行失败:', error)
    // 权限检查失败时，默认拒绝访问
    applyPermissionResult(el, false, 'hide')
  }
}

/**
 * 解析指令配置
 */
function parseDirectiveConfig(value) {
  if (typeof value === 'string') {
    return {
      resource: value,
      conditions: [],
    }
  }

  if (typeof value === 'object' && value !== null) {
    return {
      resource: value.resource || '',
      conditions: value.conditions || [],
    }
  }

  throw new Error('批量删除权限指令参数格式错误')
}

/**
 * 应用权限结果到元素
 */
function applyPermissionResult(el, hasPermission, modifier) {
  switch (modifier) {
    case 'hide':
      // 隐藏/显示元素
      if (hasPermission) {
        el.style.display = ''
        el.removeAttribute('hidden')
      } else {
        el.style.display = 'none'
        el.setAttribute('hidden', 'true')
      }
      break

    case 'disable':
      // 禁用/启用元素
      if (hasPermission) {
        el.removeAttribute('disabled')
        el.classList.remove('permission-disabled')
      } else {
        el.setAttribute('disabled', 'true')
        el.classList.add('permission-disabled')
      }
      break

    case 'class':
      // 添加/移除CSS类
      if (hasPermission) {
        el.classList.add('permission-allowed')
        el.classList.remove('permission-denied')
      } else {
        el.classList.add('permission-denied')
        el.classList.remove('permission-allowed')
      }
      break

    case 'tooltip':
      // 设置提示信息
      const tooltip = hasPermission ? '可以执行批量删除操作' : '权限不足，无法执行批量删除操作'
      el.setAttribute('title', tooltip)
      el.setAttribute('data-tooltip', tooltip)
      break

    default:
      // 默认行为：隐藏元素
      if (hasPermission) {
        el.style.display = ''
        el.removeAttribute('hidden')
      } else {
        el.style.display = 'none'
        el.setAttribute('hidden', 'true')
      }
  }
}

/**
 * 权限检查指令（简化版）
 *
 * 用法：
 * v-permission-check="'api:batch_delete'"
 */
const permissionCheck = {
  async mounted(el, binding) {
    const permission = binding.value
    if (!permission) return

    try {
      const userStore = useUserStore()

      // 超级管理员直接通过
      if (userStore.userInfo?.is_superuser) {
        return
      }

      // 解析权限字符串
      const [resource, action] = permission.split(':')
      if (action !== 'batch_delete') {
        console.warn('权限检查指令只支持批量删除权限')
        return
      }

      // 检查权限
      const hasPermission = await BatchDeletePermissionUtils.hasPermission(resource)

      if (!hasPermission) {
        el.style.display = 'none'
        el.setAttribute('hidden', 'true')
      }
    } catch (error) {
      console.error('权限检查指令执行失败:', error)
      el.style.display = 'none'
      el.setAttribute('hidden', 'true')
    }
  },
}

/**
 * 批量删除按钮权限指令
 *
 * 专门用于批量删除按钮的权限控制
 *
 * 用法：
 * v-batch-delete-button="'api'"
 */
const batchDeleteButton = {
  async mounted(el, binding) {
    const resourceType = binding.value
    if (!resourceType) return

    try {
      const userStore = useUserStore()

      // 超级管理员直接通过
      if (userStore.userInfo?.is_superuser) {
        enhanceButton(el, true, resourceType)
        return
      }

      // 检查权限
      const hasPermission = await BatchDeletePermissionUtils.hasPermission(resourceType)

      // 增强按钮
      enhanceButton(el, hasPermission, resourceType)
    } catch (error) {
      console.error('批量删除按钮权限指令执行失败:', error)
      enhanceButton(el, false, resourceType)
    }
  },
}

/**
 * 增强批量删除按钮
 */
function enhanceButton(el, hasPermission, resourceType) {
  // 设置按钮状态
  if (hasPermission) {
    el.removeAttribute('disabled')
    el.classList.remove('permission-disabled')
    el.classList.add('permission-enabled')
  } else {
    el.setAttribute('disabled', 'true')
    el.classList.add('permission-disabled')
    el.classList.remove('permission-enabled')
  }

  // 设置提示信息
  const tooltip = hasPermission
    ? `可以批量删除${resourceType}`
    : `权限不足，无法批量删除${resourceType}`
  el.setAttribute('title', tooltip)

  // 添加权限属性
  el.setAttribute('data-batch-delete-permission', hasPermission ? 'allowed' : 'denied')
  el.setAttribute('data-resource-type', resourceType)

  // 添加点击事件监听（如果没有权限则阻止）
  if (!hasPermission) {
    el.addEventListener(
      'click',
      (event) => {
        event.preventDefault()
        event.stopPropagation()

        // 显示权限不足提示
        console.warn(`权限不足，无法批量删除${resourceType}`)

        // 可以在这里触发权限不足的提示消息
        if (window.$message) {
          window.$message.warning(`权限不足，无法批量删除${resourceType}`)
        }
      },
      true
    )
  }
}

/**
 * 权限相关的CSS样式
 */
const permissionStyles = `
  .permission-disabled {
    opacity: 0.5;
    cursor: not-allowed !important;
    pointer-events: none;
  }
  
  .permission-denied {
    opacity: 0.6;
    filter: grayscale(50%);
  }
  
  .permission-allowed {
    opacity: 1;
    filter: none;
  }
  
  .permission-enabled {
    cursor: pointer;
  }
  
  [data-batch-delete-permission="denied"] {
    position: relative;
  }
  
  [data-batch-delete-permission="denied"]::after {
    content: "🔒";
    position: absolute;
    top: -5px;
    right: -5px;
    font-size: 12px;
    opacity: 0.7;
  }
`

/**
 * 注入权限样式
 */
function injectPermissionStyles() {
  if (typeof document !== 'undefined') {
    const styleId = 'batch-delete-permission-styles'

    if (!document.getElementById(styleId)) {
      const style = document.createElement('style')
      style.id = styleId
      style.textContent = permissionStyles
      document.head.appendChild(style)
    }
  }
}

/**
 * 安装权限指令
 */
export function installBatchDeletePermissionDirectives(app) {
  // 注入样式
  injectPermissionStyles()

  // 注册指令
  app.directive('batch-delete-permission', batchDeletePermission)
  app.directive('permission-check', permissionCheck)
  app.directive('batch-delete-button', batchDeleteButton)
}

/**
 * 导出指令对象
 */
export { batchDeletePermission, permissionCheck, batchDeleteButton }

/**
 * 默认导出
 */
export default {
  install: installBatchDeletePermissionDirectives,
}
