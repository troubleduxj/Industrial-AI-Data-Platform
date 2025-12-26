<template>
  <div class="view-toggle" :class="toggleClass">
    <div class="view-toggle-group">
      <NTooltip
        v-for="option in options"
        :key="option.value"
        :disabled="showLabel || disabled"
        placement="bottom"
        trigger="hover"
      >
        <template #trigger>
          <NButton
            :type="modelValue === option.value ? 'primary' : 'default'"
            :size="size"
            :disabled="disabled"
            class="view-toggle-button"
            @click="handleToggle(option.value)"
          >
            <TheIcon
              v-if="option.icon"
              :icon="option.icon"
              :size="iconSize"
              :class="showLabel ? 'mr-1' : ''"
            />
            <span v-if="showLabel">{{ option.label }}</span>
          </NButton>
        </template>
        <span>{{ option.label }}</span>
      </NTooltip>
    </div>
  </div>
</template>

<script setup>
import { NButton, NTooltip } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { computed } from 'vue'

/**
 * 视图切换组件
 * 提供统一的视图模式切换功能
 */
const props = defineProps({
  // 当前选中的视图模式
  modelValue: {
    type: String,
    required: true,
  },
  // 视图选项配置
  options: {
    type: Array,
    required: true,
    validator: (value) => {
      return value.every((option) => option.value && option.label && option.icon)
    },
  },
  // 组件尺寸
  size: {
    type: String,
    default: 'small',
    validator: (value) => ['tiny', 'small', 'medium', 'large'].includes(value),
  },
  // 是否显示标签文字
  showLabel: {
    type: Boolean,
    default: true,
  },
  // 图标尺寸
  iconSize: {
    type: Number,
    default: 16,
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false,
  },
  // 对齐方式
  align: {
    type: String,
    default: 'right',
    validator: (value) => ['left', 'center', 'right'].includes(value),
  },
  // 是否紧凑模式（仅显示图标）
  compact: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

// 组件样式类
const toggleClass = computed(() => {
  return {
    [`view-toggle--${props.align}`]: props.align !== 'right',
    'view-toggle--compact': props.compact,
    'view-toggle--disabled': props.disabled,
  }
})

// 是否显示标签（受紧凑模式影响）
const showLabel = computed(() => {
  return props.showLabel && !props.compact
})

/**
 * 处理视图切换
 * @param {string} value - 新的视图模式值
 */
function handleToggle(value) {
  if (props.disabled || value === props.modelValue) {
    return
  }

  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style scoped>
.view-toggle {
  display: flex;
  align-items: center;
}

.view-toggle--left {
  justify-content: flex-start;
}

.view-toggle--center {
  justify-content: center;
}

.view-toggle--right {
  justify-content: flex-end;
}

.view-toggle--disabled {
  opacity: 0.6;
  pointer-events: none;
}

/* 按钮组容器 */
.view-toggle-group {
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border-color, #e0e0e6);
  background: var(--bg-color, #fff);
  transition: all 0.3s ease;
}

.view-toggle-group:hover {
  border-color: var(--primary-color, #18a058);
}

/* 按钮样式 */
.view-toggle-button {
  border-radius: 0 !important;
  border: none !important;
  margin: 0 !important;
  position: relative;
  transition: all 0.2s ease;
}

.view-toggle-button:not(:last-child)::after {
  content: '';
  position: absolute;
  right: 0;
  top: 20%;
  bottom: 20%;
  width: 1px;
  background: var(--border-color, #e0e0e6);
  transition: opacity 0.2s ease;
}

.view-toggle-button:hover::after,
.view-toggle-button:focus::after {
  opacity: 0;
}

/* 第一个和最后一个按钮的圆角 */
.view-toggle-button:first-child {
  border-top-left-radius: 6px !important;
  border-bottom-left-radius: 6px !important;
}

.view-toggle-button:last-child {
  border-top-right-radius: 6px !important;
  border-bottom-right-radius: 6px !important;
}

/* 紧凑模式样式 */
.view-toggle--compact .view-toggle-button {
  min-width: 32px;
  padding: 0 8px;
}

/* 暗色主题适配 */
.dark .view-toggle-group {
  --border-color: #48484e;
  --bg-color: #2d2d30;
}

.dark .view-toggle-button:not(:last-child)::after {
  background: #48484e;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .view-toggle-group {
    border-radius: 4px;
  }

  .view-toggle-button:first-child {
    border-top-left-radius: 4px !important;
    border-bottom-left-radius: 4px !important;
  }

  .view-toggle-button:last-child {
    border-top-right-radius: 4px !important;
    border-bottom-right-radius: 4px !important;
  }

  /* 移动端自动启用紧凑模式 */
  .view-toggle:not(.view-toggle--compact) .view-toggle-button {
    min-width: 28px;
    padding: 0 6px;
  }
}

/* 动画效果 */
@keyframes toggleActive {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(0.95);
  }
  100% {
    transform: scale(1);
  }
}

.view-toggle-button:active {
  animation: toggleActive 0.15s ease;
}
</style>
