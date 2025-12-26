<template>
  <div class="responsive-grid" :class="gridClass" :style="gridStyle">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 响应式栅格容器组件
 * 提供灵活的栅格布局系统，支持响应式断点
 *
 * @component ResponsiveGrid
 * @example
 * <ResponsiveGrid :cols="{ xs: 1, sm: 2, md: 3, lg: 4 }" :gap="16">
 *   <ResponsiveGridItem>内容1</ResponsiveGridItem>
 *   <ResponsiveGridItem>内容2</ResponsiveGridItem>
 * </ResponsiveGrid>
 */

const props = defineProps({
  // 列数配置 - 支持响应式断点
  cols: {
    type: [Number, Object],
    default: () => ({
      xs: 1, // <576px
      sm: 2, // ≥576px
      md: 3, // ≥768px
      lg: 4, // ≥992px
      xl: 6, // ≥1200px
      xxl: 8, // ≥1600px
    }),
  },

  // 间距配置
  gap: {
    type: [Number, String, Object],
    default: 16,
  },

  // 行间距（如果与列间距不同）
  rowGap: {
    type: [Number, String],
    default: null,
  },

  // 列间距（如果与行间距不同）
  columnGap: {
    type: [Number, String],
    default: null,
  },

  // 对齐方式
  justify: {
    type: String,
    default: 'start',
    validator: (value) =>
      [
        'start',
        'end',
        'center',
        'stretch',
        'space-around',
        'space-between',
        'space-evenly',
      ].includes(value),
  },

  // 垂直对齐
  align: {
    type: String,
    default: 'stretch',
    validator: (value) => ['start', 'end', 'center', 'stretch'].includes(value),
  },

  // 是否自动填充
  autoFit: {
    type: Boolean,
    default: false,
  },

  // 最小列宽（autoFit模式下）
  minColWidth: {
    type: [Number, String],
    default: '200px',
  },

  // 最大列宽（autoFit模式下）
  maxColWidth: {
    type: [Number, String],
    default: '1fr',
  },

  // 是否密集布局
  dense: {
    type: Boolean,
    default: false,
  },
})

// 计算属性
const gridClass = computed(() => ({
  'responsive-grid--auto-fit': props.autoFit,
  'responsive-grid--dense': props.dense,
  [`responsive-grid--justify-${props.justify}`]: props.justify !== 'start',
  [`responsive-grid--align-${props.align}`]: props.align !== 'stretch',
}))

const gridStyle = computed(() => {
  const styles = {}

  if (props.autoFit) {
    // 自动填充模式
    styles.gridTemplateColumns = `repeat(auto-fit, minmax(${formatSize(
      props.minColWidth
    )}, ${formatSize(props.maxColWidth)}))`
  } else {
    // 响应式列数模式
    if (typeof props.cols === 'number') {
      styles.gridTemplateColumns = `repeat(${props.cols}, 1fr)`
    } else {
      // 通过CSS变量实现响应式
      styles['--grid-cols-xs'] = props.cols.xs || 1
      styles['--grid-cols-sm'] = props.cols.sm || props.cols.xs || 2
      styles['--grid-cols-md'] = props.cols.md || props.cols.sm || 3
      styles['--grid-cols-lg'] = props.cols.lg || props.cols.md || 4
      styles['--grid-cols-xl'] = props.cols.xl || props.cols.lg || 6
      styles['--grid-cols-xxl'] = props.cols.xxl || props.cols.xl || 8
    }
  }

  // 间距设置
  if (typeof props.gap === 'object') {
    styles['--gap-xs'] = formatSize(props.gap.xs || 8)
    styles['--gap-sm'] = formatSize(props.gap.sm || 12)
    styles['--gap-md'] = formatSize(props.gap.md || 16)
    styles['--gap-lg'] = formatSize(props.gap.lg || 20)
    styles['--gap-xl'] = formatSize(props.gap.xl || 24)
    styles['--gap-xxl'] = formatSize(props.gap.xxl || 32)
  } else {
    styles.gap = formatSize(props.gap)
  }

  // 单独设置行列间距
  if (props.rowGap !== null) {
    styles.rowGap = formatSize(props.rowGap)
  }

  if (props.columnGap !== null) {
    styles.columnGap = formatSize(props.columnGap)
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
.responsive-grid {
  display: grid;
  width: 100%;
}

/* 默认响应式列数 */
.responsive-grid:not(.responsive-grid--auto-fit) {
  grid-template-columns: repeat(var(--grid-cols-xs, 1), 1fr);
}

/* 响应式断点 */
@media (min-width: 576px) {
  .responsive-grid:not(.responsive-grid--auto-fit) {
    grid-template-columns: repeat(var(--grid-cols-sm, 2), 1fr);
  }
}

@media (min-width: 768px) {
  .responsive-grid:not(.responsive-grid--auto-fit) {
    grid-template-columns: repeat(var(--grid-cols-md, 3), 1fr);
  }
}

@media (min-width: 992px) {
  .responsive-grid:not(.responsive-grid--auto-fit) {
    grid-template-columns: repeat(var(--grid-cols-lg, 4), 1fr);
  }
}

@media (min-width: 1200px) {
  .responsive-grid:not(.responsive-grid--auto-fit) {
    grid-template-columns: repeat(var(--grid-cols-xl, 6), 1fr);
  }
}

@media (min-width: 1600px) {
  .responsive-grid:not(.responsive-grid--auto-fit) {
    grid-template-columns: repeat(var(--grid-cols-xxl, 8), 1fr);
  }
}

/* 响应式间距 */
.responsive-grid {
  gap: var(--gap-xs, 8px);
}

@media (min-width: 576px) {
  .responsive-grid {
    gap: var(--gap-sm, 12px);
  }
}

@media (min-width: 768px) {
  .responsive-grid {
    gap: var(--gap-md, 16px);
  }
}

@media (min-width: 992px) {
  .responsive-grid {
    gap: var(--gap-lg, 20px);
  }
}

@media (min-width: 1200px) {
  .responsive-grid {
    gap: var(--gap-xl, 24px);
  }
}

@media (min-width: 1600px) {
  .responsive-grid {
    gap: var(--gap-xxl, 32px);
  }
}

/* 对齐方式 */
.responsive-grid--justify-end {
  justify-content: end;
}

.responsive-grid--justify-center {
  justify-content: center;
}

.responsive-grid--justify-stretch {
  justify-content: stretch;
}

.responsive-grid--justify-space-around {
  justify-content: space-around;
}

.responsive-grid--justify-space-between {
  justify-content: space-between;
}

.responsive-grid--justify-space-evenly {
  justify-content: space-evenly;
}

.responsive-grid--align-start {
  align-content: start;
}

.responsive-grid--align-end {
  align-content: end;
}

.responsive-grid--align-center {
  align-content: center;
}

/* 密集布局 */
.responsive-grid--dense {
  grid-auto-flow: row dense;
}

/* 自动填充模式 */
.responsive-grid--auto-fit {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}
</style>
