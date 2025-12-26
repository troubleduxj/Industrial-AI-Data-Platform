<!--
权限按钮组件 v2
根据用户权限自动显示/隐藏或禁用按钮
支持API v2权限格式和多权限检查
-->
<template>
  <n-button
    v-if="shouldShow"
    :disabled="shouldDisable"
    :type="type"
    :size="size"
    :loading="loading"
    :ghost="ghost"
    :dashed="dashed"
    :round="round"
    :circle="circle"
    :quaternary="quaternary"
    :secondary="secondary"
    :tertiary="tertiary"
    :strong="strong"
    :focusable="focusable"
    :keyboard="keyboard"
    :tag="tag"
    :color="color"
    :text-color="textColor"
    :icon-placement="iconPlacement"
    @click="handleClick"
  >
    <template v-if="$slots.icon" #icon>
      <slot name="icon" />
    </template>
    <slot />
  </n-button>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import { NButton } from 'naive-ui'
import { usePermission } from '@/composables/usePermission'
import {
  getPermission,
  getPermissionByPage,
  hasPermission as checkPermission,
} from '@/utils/permission-config-v2'

const props = defineProps({
  // v2权限相关属性
  permission: {
    type: [String, Array],
    default: null,
  },
  resource: {
    type: String,
    default: null,
  },
  action: {
    type: String,
    default: null,
  },
  pagePath: {
    type: String,
    default: null,
  },
  roles: {
    type: [String, Array],
    default: null,
  },
  permissionMode: {
    type: String,
    default: 'any', // 'any' | 'all'
    validator: (value) => ['any', 'all'].includes(value),
  },

  // 显示模式配置
  hideWhenNoPermission: {
    type: Boolean,
    default: true,
  },
  disableWhenNoPermission: {
    type: Boolean,
    default: false,
  },
  showTooltipWhenDisabled: {
    type: Boolean,
    default: true,
  },
  noPermissionTooltip: {
    type: String,
    default: '您没有权限执行此操作',
  },

  // 多权限检查配置
  multiplePermissions: {
    type: Array,
    default: () => [],
  },
  requireAllPermissions: {
    type: Boolean,
    default: false,
  },

  // 权限状态变化回调
  onPermissionChange: {
    type: Function,
    default: null,
  },

  // NButton 原生属性
  type: {
    type: String,
    default: 'default',
  },
  size: {
    type: String,
    default: 'medium',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  ghost: {
    type: Boolean,
    default: false,
  },
  dashed: {
    type: Boolean,
    default: false,
  },
  round: {
    type: Boolean,
    default: false,
  },
  circle: {
    type: Boolean,
    default: false,
  },
  quaternary: {
    type: Boolean,
    default: false,
  },
  secondary: {
    type: Boolean,
    default: false,
  },
  tertiary: {
    type: Boolean,
    default: false,
  },
  strong: {
    type: Boolean,
    default: false,
  },
  focusable: {
    type: Boolean,
    default: true,
  },
  keyboard: {
    type: Boolean,
    default: true,
  },
  tag: {
    type: String,
    default: 'button',
  },
  color: String,
  textColor: String,
  iconPlacement: {
    type: String,
    default: 'left',
  },
})

const emit = defineEmits(['click', 'permission-change'])

const { hasPermission, hasButtonPermission, hasRole } = usePermission()

// 权限状态追踪
const previousPermissionState = ref(null)

// v2权限检查逻辑
const getV2Permission = () => {
  // 优先级1: 直接传入的权限标识
  if (props.permission) {
    return props.permission
  }

  // 优先级2: 通过resource和action获取v2权限
  if (props.resource && props.action) {
    return getPermission(props.resource, props.action)
  }

  // 优先级3: 通过页面路径和action获取权限
  if (props.pagePath && props.action) {
    return getPermissionByPage(props.pagePath, props.action)
  }

  return null
}

// 权限检查
const hasAccess = computed(() => {
  try {
    // 多权限检查
    if (props.multiplePermissions.length > 0) {
      const permissionResults = props.multiplePermissions.map((perm) => {
        if (typeof perm === 'string') {
          return hasPermission(perm, 'any')
        } else if (typeof perm === 'object') {
          if (perm.resource && perm.action) {
            const v2Permission = getPermission(perm.resource, perm.action)
            return v2Permission ? hasPermission(v2Permission, 'any') : false
          } else if (perm.permission) {
            return hasPermission(perm.permission, 'any')
          }
        }
        return false
      })

      return props.requireAllPermissions
        ? permissionResults.every((result) => result)
        : permissionResults.some((result) => result)
    }

    // v2权限检查
    const v2Permission = getV2Permission()
    if (v2Permission) {
      if (Array.isArray(v2Permission)) {
        return checkPermission(hasPermission, v2Permission, props.permissionMode)
      } else {
        return hasPermission(v2Permission, props.permissionMode)
      }
    }

    // 角色权限检查
    if (props.roles) {
      return hasRole(props.roles, props.permissionMode)
    }

    // 没有设置权限要求，默认显示
    return true
  } catch (error) {
    console.error('权限检查出错:', error)
    return false
  }
})

// 是否显示按钮
const shouldShow = computed(() => {
  if (!hasAccess.value && props.hideWhenNoPermission) {
    return false
  }
  return true
})

// 是否禁用按钮
const shouldDisable = computed(() => {
  if (props.disabled) {
    return true
  }

  if (!hasAccess.value && props.disableWhenNoPermission) {
    return true
  }

  return false
})

// 监听权限状态变化
watch(
  hasAccess,
  (newValue, oldValue) => {
    if (oldValue !== null && newValue !== oldValue) {
      // 触发权限变化事件
      emit('permission-change', {
        hasPermission: newValue,
        previousState: oldValue,
        timestamp: Date.now(),
      })

      // 调用权限变化回调
      if (props.onPermissionChange) {
        props.onPermissionChange({
          hasPermission: newValue,
          previousState: oldValue,
          permission: getV2Permission(),
          resource: props.resource,
          action: props.action,
        })
      }
    }
    previousPermissionState.value = newValue
  },
  { immediate: true }
)

const handleClick = (event) => {
  if (!hasAccess.value) {
    console.warn('用户无权限执行此操作:', {
      permission: getV2Permission(),
      resource: props.resource,
      action: props.action,
      roles: props.roles,
    })
    return
  }

  emit('click', event)
}

// 调试信息 (开发环境)
if (process.env.NODE_ENV === 'development') {
  watch(
    () => [props.resource, props.action, props.permission, props.pagePath],
    () => {
      const v2Permission = getV2Permission()
      console.debug('PermissionButton v2 Debug:', {
        resource: props.resource,
        action: props.action,
        permission: props.permission,
        pagePath: props.pagePath,
        resolvedPermission: v2Permission,
        hasAccess: hasAccess.value,
        shouldShow: shouldShow.value,
        shouldDisable: shouldDisable.value,
      })
    },
    { immediate: true }
  )
}
</script>

<style scoped>
/* 权限相关样式 */
.permission-button-disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.permission-button-hidden {
  display: none;
}

/* 权限提示样式 */
.permission-tooltip {
  max-width: 200px;
}
</style>
