<template>
  <div class="responsive-container" :class="containerClass" :style="containerStyle">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 响应式容器组件
 * 提供响应式的容器宽度和内边距管理
 *
 * @component ResponsiveContainer
 * @example
 * <ResponsiveContainer size="lg" :fluid="false">
 *   <div>内容</div>
 * </ResponsiveContainer>
 */

const props = defineProps({
  // 容器尺寸
  size: {
    type: String,
    default: 'xl',
    validator: (value) => ['sm', 'md', 'lg', 'xl', 'xxl', 'fluid'].includes(value),
  },

  // 是否流式布局（100%宽度）
  fluid: {
    type: Boolean,
    default: false,
  },

  // 内边距配置
  padding: {
    type: [Number, String, Object],
    default: () => ({
      xs: 16,
      sm: 20,
      md: 24,
      lg: 32,
      xl: 40,
      xxl: 48,
    }),
  },

  // 是否居中
  centered: {
    type: Boolean,
    default: true,
  },

  // 自定义最大宽度
  maxWidth: {
    type: [Number, String],
    default: null,
  },

  // 自定义最小宽度
  minWidth: {
    type: [Number, String],
    default: null,
  },
})

// 容器尺寸映射
const containerSizes = {
  sm: '576px',
  md: '768px',
  lg: '992px',
  xl: '1200px',
  xxl: '1600px',
  fluid: '100%',
}

// 计算属性
const containerClass = computed(() => ({
  [`responsive-container--${props.size}`]: !props.fluid,
  'responsive-container--fluid': props.fluid,
  'responsive-container--centered': props.centered,
}))

const containerStyle = computed(() => {
  const styles = {}

  // 设置最大宽度
  if (props.maxWidth) {
    styles.maxWidth = formatSize(props.maxWidth)
  } else if (!props.fluid) {
    styles.maxWidth = containerSizes[props.size] || containerSizes.xl
  }

  // 设置最小宽度
  if (props.minWidth) {
    styles.minWidth = formatSize(props.minWidth)
  }

  // 设置内边距
  if (typeof props.padding === 'object') {
    styles['--padding-xs'] = formatSize(props.padding.xs || 16)
    styles['--padding-sm'] = formatSize(props.padding.sm || 20)
    styles['--padding-md'] = formatSize(props.padding.md || 24)
    styles['--padding-lg'] = formatSize(props.padding.lg || 32)
    styles['--padding-xl'] = formatSize(props.padding.xl || 40)
    styles['--padding-xxl'] = formatSize(props.padding.xxl || 48)
  } else {
    styles.padding = formatSize(props.padding)
  }

  return styles
})

// 工具函数
function formatSize(size) {
  if (typeof size === 'number') {
    return `${size}px`
  }
  return size
}
</script>

<style scoped>
.responsive-container {
  width: 100%;
  box-sizing: border-box;
}

/* 居中对齐 */
.responsive-container--centered {
  margin-left: auto;
  margin-right: auto;
}

/* 流式布局 */
.responsive-container--fluid {
  max-width: none;
}

/* 响应式内边距 */
.responsive-container {
  padding-left: var(--padding-xs, 16px);
  padding-right: var(--padding-xs, 16px);
}

@media (min-width: 576px) {
  .responsive-container {
    padding-left: var(--padding-sm, 20px);
    padding-right: var(--padding-sm, 20px);
  }
}

@media (min-width: 768px) {
  .responsive-container {
    padding-left: var(--padding-md, 24px);
    padding-right: var(--padding-md, 24px);
  }
}

@media (min-width: 992px) {
  .responsive-container {
    padding-left: var(--padding-lg, 32px);
    padding-right: var(--padding-lg, 32px);
  }
}

@media (min-width: 1200px) {
  .responsive-container {
    padding-left: var(--padding-xl, 40px);
    padding-right: var(--padding-xl, 40px);
  }
}

@media (min-width: 1600px) {
  .responsive-container {
    padding-left: var(--padding-xxl, 48px);
    padding-right: var(--padding-xxl, 48px);
  }
}

/* 容器尺寸断点 */
.responsive-container--sm {
  max-width: 576px;
}

.responsive-container--md {
  max-width: 768px;
}

.responsive-container--lg {
  max-width: 992px;
}

.responsive-container--xl {
  max-width: 1200px;
}

.responsive-container--xxl {
  max-width: 1600px;
}

/* 平滑过渡 */
.responsive-container {
  transition: padding 0.3s ease, max-width 0.3s ease;
}
</style>
