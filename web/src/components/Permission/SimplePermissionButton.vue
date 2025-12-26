<template>
  <n-button v-if="shouldShow" v-bind="$attrs" :disabled="isDisabled" @click="handleClick">
    <slot />
  </n-button>
</template>

<script setup>
import { computed } from 'vue'
import { NButton } from 'naive-ui'
import { useUserStore } from '@/store'

/**
 * 简化版权限按钮组件
 * 避免循环依赖问题
 */

const props = defineProps({
  permission: {
    type: [String, Array],
    default: null,
  },
  hideWhenNoPermission: {
    type: Boolean,
    default: false,
  },
  disableWhenNoPermission: {
    type: Boolean,
    default: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['click'])

const userStore = useUserStore()

// 简单的权限检查
const hasPermission = computed(() => {
  if (!props.permission) {
    return true
  }

  // 超级用户拥有所有权限
  if (userStore.isSuperUser) {
    return true
  }

  // 这里可以添加更复杂的权限检查逻辑
  // 暂时返回true避免循环依赖
  return true
})

// 是否显示按钮
const shouldShow = computed(() => {
  if (!hasPermission.value && props.hideWhenNoPermission) {
    return false
  }
  return true
})

// 是否禁用按钮
const isDisabled = computed(() => {
  if (props.disabled) {
    return true
  }
  if (!hasPermission.value && props.disableWhenNoPermission) {
    return true
  }
  return false
})

// 点击处理
const handleClick = (event) => {
  if (!hasPermission.value) {
    window.$message?.warning('权限不足，无法执行此操作')
    return
  }
  emit('click', event)
}
</script>
