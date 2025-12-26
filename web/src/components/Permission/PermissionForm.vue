<template>
  <n-form v-if="hasAuth" v-bind="formProps" ref="formRef" :model="model" :rules="rules">
    <slot />
  </n-form>
  <div v-else-if="showFallback" class="permission-form-fallback">
    <slot name="fallback">
      <n-alert
        type="warning"
        :title="noPermissionTitle"
        :description="noPermissionText"
        show-icon
      />
    </slot>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { NForm, NAlert } from 'naive-ui'
import { useEnhancedPermissionStore } from '@/store/modules/permission'

/**
 * 权限表单组件
 * 根据权限控制表单的显示和提交
 */

const props = defineProps({
  // 权限相关
  permission: {
    type: [String, Array],
    required: true,
  },
  permissionMode: {
    type: String,
    default: 'any',
    validator: (value) => ['all', 'any', 'exact'].includes(value),
  },

  // 表单相关
  model: {
    type: Object,
    required: true,
  },
  rules: {
    type: Object,
    default: () => ({}),
  },

  // 显示控制
  showFallback: {
    type: Boolean,
    default: true,
  },
  noPermissionTitle: {
    type: String,
    default: '权限不足',
  },
  noPermissionText: {
    type: String,
    default: '您没有权限访问此表单',
  },

  // 表单属性
  labelPlacement: {
    type: String,
    default: 'top',
  },
  labelWidth: {
    type: [String, Number],
    default: 'auto',
  },
  size: {
    type: String,
    default: 'medium',
  },
  showFeedback: {
    type: Boolean,
    default: true,
  },
  showLabel: {
    type: Boolean,
    default: true,
  },
  showRequireMark: {
    type: Boolean,
    default: undefined,
  },
  requireMarkPlacement: {
    type: String,
    default: 'right',
  },
  inline: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

// 直接使用Store，避免Composable循环导入
const permissionStore = useEnhancedPermissionStore()

// 定义权限模式
const PermissionMode = {
  ALL: 'all',
  ANY: 'any',
  EXACT: 'exact',
}

// 表单引用
const formRef = ref(null)

// 权限检查
const hasAuth = computed(() => {
  return permissionStore.hasPermission(props.permission, props.permissionMode)
})

// 表单属性
const formProps = computed(() => ({
  labelPlacement: props.labelPlacement,
  labelWidth: props.labelWidth,
  size: props.size,
  showFeedback: props.showFeedback,
  showLabel: props.showLabel,
  showRequireMark: props.showRequireMark,
  requireMarkPlacement: props.requireMarkPlacement,
  inline: props.inline,
  disabled: props.disabled || !hasAuth.value,
}))

// 暴露表单方法
defineExpose({
  validate: () => formRef.value?.validate(),
  restoreValidation: () => formRef.value?.restoreValidation(),
  getValidationStatus: () => formRef.value?.getValidationStatus(),
})
</script>

<style scoped>
.permission-form-fallback {
  padding: 20px;
}
</style>
