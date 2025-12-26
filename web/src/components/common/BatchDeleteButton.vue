<!--
批量删除按钮组件
显示选中数量和删除按钮，支持权限控制和禁用状态显示
-->
<template>
  <n-button
    v-if="shouldShow"
    :type="type"
    :size="size"
    :disabled="shouldDisable"
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
    :icon-placement="iconPlacement"
    @click="handleClick"
  >
    <template v-if="showIcon" #icon>
      <slot name="icon">
        <n-icon :component="TrashOutline" />
      </slot>
    </template>

    <span v-if="showText">
      {{ buttonText }}
    </span>
  </n-button>
</template>

<script setup>
import { computed, watch } from 'vue'
import { NButton, NIcon } from 'naive-ui'
import { TrashOutline } from '@vicons/ionicons5'
import { usePermission } from '@/composables/usePermission'

const props = defineProps({
  // 选中项目相关
  selectedItems: {
    type: Array,
    default: () => [],
  },
  selectedCount: {
    type: Number,
    default: 0,
  },
  resourceName: {
    type: String,
    default: '项目',
  },

  // 权限控制
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
    default: 'batch_delete',
  },

  // 排除条件
  excludeCondition: {
    type: Function,
    default: null,
  },

  // 显示控制
  hideWhenNoPermission: {
    type: Boolean,
    default: true,
  },
  hideWhenNoSelection: {
    type: Boolean,
    default: true,
  },
  showIcon: {
    type: Boolean,
    default: true,
  },
  showText: {
    type: Boolean,
    default: true,
  },
  showCount: {
    type: Boolean,
    default: true,
  },

  // 按钮样式
  type: {
    type: String,
    default: 'error',
  },
  size: {
    type: String,
    default: 'medium',
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
  iconPlacement: {
    type: String,
    default: 'left',
  },

  // 状态控制
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },

  // 限制条件
  maxBatchSize: {
    type: Number,
    default: 100,
  },

  // 自定义文本
  customText: {
    type: String,
    default: null,
  },

  // 验证函数
  validateSelection: {
    type: Function,
    default: null,
  },
})

const emit = defineEmits(['click', 'batch-delete', 'permission-change', 'validation-error'])

const { hasPermission } = usePermission()

// 计算有效选中数量（排除不能删除的项目）
const validSelectedCount = computed(() => {
  if (!props.excludeCondition) {
    return props.selectedCount
  }

  return props.selectedItems.filter((item) => !props.excludeCondition(item)).length
})

// 计算无效选中数量
const invalidSelectedCount = computed(() => {
  return props.selectedCount - validSelectedCount.value
})

// 权限检查
const hasAccess = computed(() => {
  try {
    // 如果指定了权限，检查权限
    if (props.permission) {
      if (Array.isArray(props.permission)) {
        return props.permission.some((perm) => hasPermission(perm))
      }
      return hasPermission(props.permission)
    }

    // 如果指定了资源和操作，构建权限标识符
    if (props.resource && props.action) {
      const permissionKey = `${props.resource}:${props.action}`
      return hasPermission(permissionKey)
    }

    // 没有权限要求，默认允许
    return true
  } catch (error) {
    console.error('权限检查出错:', error)
    return false
  }
})

// 选择验证
const selectionValidation = computed(() => {
  const result = {
    valid: true,
    message: '',
    canProceed: false,
  }

  // 检查是否有选中项目
  if (props.selectedCount === 0) {
    result.valid = false
    result.message = `请选择要删除的${props.resourceName}`
    return result
  }

  // 检查是否超过最大批量删除数量
  if (props.selectedCount > props.maxBatchSize) {
    result.valid = false
    result.message = `一次最多只能删除 ${props.maxBatchSize} 个${props.resourceName}`
    return result
  }

  // 检查是否有有效的选中项目
  if (validSelectedCount.value === 0) {
    result.valid = false
    result.message = `选中的${props.resourceName}都无法删除`
    return result
  }

  // 自定义验证
  if (props.validateSelection) {
    const customValidation = props.validateSelection(props.selectedItems)
    if (!customValidation.valid) {
      result.valid = false
      result.message = customValidation.message || '选择验证失败'
      return result
    }
  }

  result.canProceed = true
  return result
})

// 是否显示按钮
const shouldShow = computed(() => {
  // 权限检查
  if (!hasAccess.value && props.hideWhenNoPermission) {
    return false
  }

  // 选择检查
  if (props.selectedCount === 0 && props.hideWhenNoSelection) {
    return false
  }

  return true
})

// 是否禁用按钮
const shouldDisable = computed(() => {
  // 手动禁用
  if (props.disabled || props.loading) {
    return true
  }

  // 权限不足
  if (!hasAccess.value) {
    return true
  }

  // 选择验证失败
  if (!selectionValidation.value.canProceed) {
    return true
  }

  return false
})

// 按钮文本
const buttonText = computed(() => {
  if (props.customText) {
    return props.customText
  }

  let text = `批量删除`

  if (props.showCount && props.selectedCount > 0) {
    if (invalidSelectedCount.value > 0) {
      text += ` (${validSelectedCount.value}/${props.selectedCount})`
    } else {
      text += ` (${props.selectedCount})`
    }
  }

  return text
})

// 处理点击事件
const handleClick = (event) => {
  // 权限检查
  if (!hasAccess.value) {
    console.warn('用户无权限执行批量删除操作:', {
      permission: props.permission,
      resource: props.resource,
      action: props.action,
    })
    return
  }

  // 选择验证
  if (!selectionValidation.value.canProceed) {
    emit('validation-error', {
      message: selectionValidation.value.message,
      selectedCount: props.selectedCount,
      validCount: validSelectedCount.value,
      invalidCount: invalidSelectedCount.value,
    })
    return
  }

  // 触发事件
  emit('click', event)
  emit('batch-delete', {
    selectedItems: props.selectedItems,
    selectedCount: props.selectedCount,
    validCount: validSelectedCount.value,
    invalidCount: invalidSelectedCount.value,
  })
}

// 监听权限状态变化
watch(
  hasAccess,
  (newValue, oldValue) => {
    if (oldValue !== null && newValue !== oldValue) {
      emit('permission-change', {
        hasPermission: newValue,
        previousState: oldValue,
        permission: props.permission,
        resource: props.resource,
        action: props.action,
        timestamp: Date.now(),
      })
    }
  },
  { immediate: true }
)

// 监听选择验证状态变化
watch(
  selectionValidation,
  (newValue, oldValue) => {
    if (oldValue && newValue.valid !== oldValue.valid) {
      if (!newValue.valid && newValue.message) {
        emit('validation-error', {
          message: newValue.message,
          selectedCount: props.selectedCount,
          validCount: validSelectedCount.value,
          invalidCount: invalidSelectedCount.value,
        })
      }
    }
  },
  { deep: true }
)

// 暴露组件方法和状态
defineExpose({
  hasAccess,
  shouldShow,
  shouldDisable,
  validSelectedCount,
  invalidSelectedCount,
  selectionValidation,
  buttonText,
})
</script>

<style scoped>
/* 批量删除按钮样式 */
.batch-delete-button {
  position: relative;
}

/* 权限不足时的样式 */
.batch-delete-button--no-permission {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 选择无效时的样式 */
.batch-delete-button--invalid-selection {
  opacity: 0.7;
}

/* 加载状态样式 */
.batch-delete-button--loading {
  pointer-events: none;
}
</style>
