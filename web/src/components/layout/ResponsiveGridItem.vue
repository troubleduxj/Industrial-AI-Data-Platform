<template>
  <div class="responsive-grid-item" :class="itemClass" :style="itemStyle">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 响应式栅格项组件
 * 栅格容器的子项，支持跨列、跨行和响应式配置
 *
 * @component ResponsiveGridItem
 * @example
 * <ResponsiveGridItem :span="{ xs: 1, md: 2 }" :offset="{ md: 1 }">
 *   内容
 * </ResponsiveGridItem>
 */

const props = defineProps({
  // 跨列数 - 支持响应式断点
  span: {
    type: [Number, Object],
    default: 1,
  },

  // 跨行数
  rowSpan: {
    type: Number,
    default: 1,
  },

  // 列偏移 - 支持响应式断点
  offset: {
    type: [Number, Object],
    default: 0,
  },

  // 行偏移
  rowOffset: {
    type: Number,
    default: 0,
  },

  // 指定起始列位置
  colStart: {
    type: [Number, Object],
    default: null,
  },

  // 指定结束列位置
  colEnd: {
    type: [Number, Object],
    default: null,
  },

  // 指定起始行位置
  rowStart: {
    type: Number,
    default: null,
  },

  // 指定结束行位置
  rowEnd: {
    type: Number,
    default: null,
  },

  // 自对齐方式
  justifySelf: {
    type: String,
    default: 'stretch',
    validator: (value) => ['start', 'end', 'center', 'stretch'].includes(value),
  },

  // 垂直自对齐
  alignSelf: {
    type: String,
    default: 'stretch',
    validator: (value) => ['start', 'end', 'center', 'stretch'].includes(value),
  },

  // 排序
  order: {
    type: [Number, Object],
    default: 0,
  },
})

// 计算属性
const itemClass = computed(() => ({
  [`responsive-grid-item--justify-${props.justifySelf}`]: props.justifySelf !== 'stretch',
  [`responsive-grid-item--align-${props.alignSelf}`]: props.alignSelf !== 'stretch',
}))

const itemStyle = computed(() => {
  const styles = {}

  // 跨列设置
  if (typeof props.span === 'number') {
    if (props.span > 1) {
      styles.gridColumn = `span ${props.span}`
    }
  } else {
    // 响应式跨列
    styles['--span-xs'] = props.span.xs || 1
    styles['--span-sm'] = props.span.sm || props.span.xs || 1
    styles['--span-md'] = props.span.md || props.span.sm || 1
    styles['--span-lg'] = props.span.lg || props.span.md || 1
    styles['--span-xl'] = props.span.xl || props.span.lg || 1
    styles['--span-xxl'] = props.span.xxl || props.span.xl || 1
  }

  // 跨行设置
  if (props.rowSpan > 1) {
    styles.gridRow = `span ${props.rowSpan}`
  }

  // 列偏移设置
  if (typeof props.offset === 'number') {
    if (props.offset > 0) {
      styles.marginLeft = `calc(${props.offset} * (100% + var(--grid-gap, 16px)) / var(--grid-cols, 1))`
    }
  } else {
    // 响应式偏移
    styles['--offset-xs'] = props.offset.xs || 0
    styles['--offset-sm'] = props.offset.sm || props.offset.xs || 0
    styles['--offset-md'] = props.offset.md || props.offset.sm || 0
    styles['--offset-lg'] = props.offset.lg || props.offset.md || 0
    styles['--offset-xl'] = props.offset.xl || props.offset.lg || 0
    styles['--offset-xxl'] = props.offset.xxl || props.offset.xl || 0
  }

  // 行偏移设置
  if (props.rowOffset > 0) {
    styles.marginTop = `calc(${props.rowOffset} * var(--grid-row-gap, var(--grid-gap, 16px)))`
  }

  // 精确位置设置
  if (props.colStart !== null || props.colEnd !== null) {
    const start = props.colStart || 'auto'
    const end = props.colEnd || 'auto'
    styles.gridColumn = `${start} / ${end}`
  }

  if (props.rowStart !== null || props.rowEnd !== null) {
    const start = props.rowStart || 'auto'
    const end = props.rowEnd || 'auto'
    styles.gridRow = `${start} / ${end}`
  }

  // 排序设置
  if (typeof props.order === 'number') {
    if (props.order !== 0) {
      styles.order = props.order
    }
  } else {
    // 响应式排序
    styles['--order-xs'] = props.order.xs || 0
    styles['--order-sm'] = props.order.sm || props.order.xs || 0
    styles['--order-md'] = props.order.md || props.order.sm || 0
    styles['--order-lg'] = props.order.lg || props.order.md || 0
    styles['--order-xl'] = props.order.xl || props.order.lg || 0
    styles['--order-xxl'] = props.order.xxl || props.order.xl || 0
  }

  return styles
})
</script>

<style scoped>
.responsive-grid-item {
  min-width: 0; /* 防止内容溢出 */
}

/* 响应式跨列 */
.responsive-grid-item {
  grid-column: span var(--span-xs, 1);
}

@media (min-width: 576px) {
  .responsive-grid-item {
    grid-column: span var(--span-sm, var(--span-xs, 1));
  }
}

@media (min-width: 768px) {
  .responsive-grid-item {
    grid-column: span var(--span-md, var(--span-sm, var(--span-xs, 1)));
  }
}

@media (min-width: 992px) {
  .responsive-grid-item {
    grid-column: span var(--span-lg, var(--span-md, var(--span-sm, var(--span-xs, 1))));
  }
}

@media (min-width: 1200px) {
  .responsive-grid-item {
    grid-column: span
      var(--span-xl, var(--span-lg, var(--span-md, var(--span-sm, var(--span-xs, 1)))));
  }
}

@media (min-width: 1600px) {
  .responsive-grid-item {
    grid-column: span
      var(
        --span-xxl,
        var(--span-xl, var(--span-lg, var(--span-md, var(--span-sm, var(--span-xs, 1)))))
      );
  }
}

/* 响应式排序 */
.responsive-grid-item {
  order: var(--order-xs, 0);
}

@media (min-width: 576px) {
  .responsive-grid-item {
    order: var(--order-sm, var(--order-xs, 0));
  }
}

@media (min-width: 768px) {
  .responsive-grid-item {
    order: var(--order-md, var(--order-sm, var(--order-xs, 0)));
  }
}

@media (min-width: 992px) {
  .responsive-grid-item {
    order: var(--order-lg, var(--order-md, var(--order-sm, var(--order-xs, 0))));
  }
}

@media (min-width: 1200px) {
  .responsive-grid-item {
    order: var(--order-xl, var(--order-lg, var(--order-md, var(--order-sm, var(--order-xs, 0)))));
  }
}

@media (min-width: 1600px) {
  .responsive-grid-item {
    order: var(
      --order-xxl,
      var(--order-xl, var(--order-lg, var(--order-md, var(--order-sm, var(--order-xs, 0)))))
    );
  }
}

/* 自对齐方式 */
.responsive-grid-item--justify-start {
  justify-self: start;
}

.responsive-grid-item--justify-end {
  justify-self: end;
}

.responsive-grid-item--justify-center {
  justify-self: center;
}

.responsive-grid-item--align-start {
  align-self: start;
}

.responsive-grid-item--align-end {
  align-self: end;
}

.responsive-grid-item--align-center {
  align-self: center;
}
</style>
