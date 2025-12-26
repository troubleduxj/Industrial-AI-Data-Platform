<template>
  <NCard class="base-card" :class="cardClass" v-bind="cardProps" @click="handleClick">
    <!-- 卡片头部 -->
    <template v-if="$slots.header || title" #header>
      <slot name="header">
        <div class="card-header">
          <div class="card-title">
            <TheIcon v-if="icon" :icon="icon" :size="iconSize" class="mr-8" />
            {{ title }}
          </div>
          <div v-if="$slots.extra" class="card-extra">
            <slot name="extra"></slot>
          </div>
        </div>
      </slot>
    </template>

    <!-- 卡片内容 -->
    <div class="card-content">
      <slot></slot>
    </div>

    <!-- 卡片底部 -->
    <template v-if="$slots.footer" #footer>
      <slot name="footer"></slot>
    </template>

    <!-- 操作区域 -->
    <template v-if="$slots.action" #action>
      <slot name="action"></slot>
    </template>
  </NCard>
</template>

<script setup>
import { NCard } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { computed } from 'vue'

/**
 * 基础卡片组件
 * 提供统一的卡片样式和交互行为
 */
const props = defineProps({
  // 卡片标题
  title: {
    type: String,
    default: '',
  },
  // 标题图标
  icon: {
    type: String,
    default: '',
  },
  // 图标大小
  iconSize: {
    type: Number,
    default: 16,
  },
  // 卡片类型
  type: {
    type: String,
    default: 'default',
    validator: (value) =>
      ['default', 'primary', 'success', 'warning', 'error', 'info'].includes(value),
  },
  // 卡片尺寸
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value),
  },
  // 是否可悬停
  hoverable: {
    type: Boolean,
    default: false,
  },
  // 是否可点击
  clickable: {
    type: Boolean,
    default: false,
  },
  // 是否显示边框
  bordered: {
    type: Boolean,
    default: true,
  },
  // 是否显示阴影
  shadow: {
    type: String,
    default: 'hover',
    validator: (value) => ['never', 'hover', 'always'].includes(value),
  },
  // 圆角大小
  rounded: {
    type: [String, Number],
    default: 8,
  },
  // 内边距
  padding: {
    type: String,
    default: 'default',
    validator: (value) => ['none', 'small', 'default', 'large'].includes(value),
  },
})

const emit = defineEmits(['click'])

// 卡片样式类
const cardClass = computed(() => {
  return {
    [`base-card--${props.type}`]: props.type !== 'default',
    [`base-card--${props.size}`]: props.size !== 'medium',
    [`base-card--shadow-${props.shadow}`]: props.shadow !== 'hover',
    [`base-card--padding-${props.padding}`]: props.padding !== 'default',
    'base-card--hoverable': props.hoverable,
    'base-card--clickable': props.clickable,
  }
})

// 传递给 NCard 的属性
const cardProps = computed(() => {
  return {
    hoverable: props.hoverable,
    bordered: props.bordered,
    size: props.size,
  }
})

/**
 * 处理卡片点击事件
 */
function handleClick(event) {
  if (props.clickable) {
    emit('click', event)
  }
}
</script>

<style scoped>
.base-card {
  transition: all 0.3s ease;
}

/* 卡片类型样式 */
.base-card--primary {
  border-color: #18a058;
}

.base-card--success {
  border-color: #18a058;
}

.base-card--warning {
  border-color: #f0a020;
}

.base-card--error {
  border-color: #d03050;
}

.base-card--info {
  border-color: #2080f0;
}

/* 悬停效果 */
.base-card--hoverable:hover {
  transform: translateY(-2px);
}

.base-card--clickable {
  cursor: pointer;
}

.base-card--clickable:hover {
  transform: translateY(-1px);
}

/* 阴影样式 */
.base-card--shadow-never {
  box-shadow: none !important;
}

.base-card--shadow-always {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.base-card--shadow-always:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

/* 内边距样式 */
.base-card--padding-none :deep(.n-card__content) {
  padding: 0;
}

.base-card--padding-small :deep(.n-card__content) {
  padding: 12px;
}

.base-card--padding-large :deep(.n-card__content) {
  padding: 24px;
}

/* 尺寸样式 */
.base-card--small {
  font-size: 12px;
}

.base-card--large {
  font-size: 16px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #333;
}

.card-extra {
  flex-shrink: 0;
}

/* 卡片内容 */
.card-content {
  width: 100%;
}

/* 暗色主题适配 */
.dark .card-title {
  color: #fff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .base-card--large {
    font-size: 14px;
  }

  .base-card--padding-large :deep(.n-card__content) {
    padding: 16px;
  }
}
</style>
