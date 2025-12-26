<template>
  <router-link v-if="showLink && hasAuth" v-bind="linkProps" :to="to" @click="handleClick">
    <slot />
  </router-link>
  <span
    v-else-if="showLink && !hasAuth"
    :class="disabledClass"
    :title="noPermissionText"
    @click="handleDisabledClick"
  >
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { useEnhancedPermissionStore } from '@/store/modules/permission'

// 直接定义权限模式，避免循环导入
const PermissionMode = {
  ALL: 'all',
  ANY: 'any',
  EXACT: 'exact',
}

/**
 * 权限链接组件
 * 根据路由权限控制链接的显示和可用性
 */

const props = defineProps({
  // 路由相关
  to: {
    type: [String, Object],
    required: true,
  },

  // 权限相关
  permission: {
    type: [String, Array],
    default: null,
  },
  permissionMode: {
    type: String,
    default: 'any',
    validator: (value) => ['all', 'any', 'exact'].includes(value),
  },

  // 显示控制
  hideWhenNoPermission: {
    type: Boolean,
    default: false,
  },
  disableWhenNoPermission: {
    type: Boolean,
    default: true,
  },

  // 样式相关
  activeClass: {
    type: String,
    default: 'router-link-active',
  },
  exactActiveClass: {
    type: String,
    default: 'router-link-exact-active',
  },
  disabledClass: {
    type: String,
    default: 'permission-link-disabled',
  },

  // 权限不足时的提示
  noPermissionText: {
    type: String,
    default: '权限不足，无法访问此页面',
  },
})

const emit = defineEmits(['click', 'disabled-click'])

// 直接使用Store，避免Composable循环导入
const permissionStore = useEnhancedPermissionStore()

// 权限检查
const hasAuth = computed(() => {
  // 如果指定了权限，检查权限
  if (props.permission) {
    return permissionStore.hasPermission(props.permission, props.permissionMode)
  }

  // 否则检查路由权限（简化实现，暂时返回true）
  // const targetPath = typeof props.to === 'string' ? props.to : props.to.path
  // return hasPathPermission(targetPath)
  return true
})

// 链接显示控制
const showLink = computed(() => {
  if (!hasAuth.value && props.hideWhenNoPermission) {
    return false
  }
  return true
})

// 链接属性
const linkProps = computed(() => ({
  activeClass: props.activeClass,
  exactActiveClass: props.exactActiveClass,
}))

// 点击处理
const handleClick = (event) => {
  if (!hasAuth.value && props.disableWhenNoPermission) {
    event.preventDefault()
    handleDisabledClick(event)
    return
  }

  emit('click', event)
}

// 禁用状态点击处理
const handleDisabledClick = (event) => {
  event.preventDefault()
  window.$message?.warning(props.noPermissionText)
  emit('disabled-click', event)
}
</script>

<style scoped>
.permission-link-disabled {
  color: #ccc;
  cursor: not-allowed;
  text-decoration: none;
  pointer-events: none;
}

.permission-link-disabled:hover {
  color: #ccc;
  text-decoration: none;
}
</style>
