<template>
  <div class="query-bar-item" flex items-center :style="{ width: width }">
    <label
      v-if="!isNullOrWhitespace(label)"
      class="query-bar-item__label"
      flex-shrink-0
      :style="{ width: labelWidth + 'px' }"
    >
      {{ label }}
    </label>
    <div class="query-bar-item__content" :style="{ width: contentWidth + 'px' }">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { isNullOrWhitespace } from '@/utils'

/**
 * 查询条件项组件
 * 用于统一查询表单中的标签和内容布局
 * 集成了UnoCSS样式和工具函数优化
 */
defineProps({
  // 标签文本
  label: {
    type: String,
    default: '',
  },
  // 标签宽度
  labelWidth: {
    type: Number,
    default: 80,
  },
  // 内容区域宽度
  contentWidth: {
    type: Number,
    default: 220,
  },
  // 组件宽度
  width: {
    type: String,
    default: 'auto',
  },
})
</script>

<style scoped>
.query-bar-item {
  gap: 8px;
}

.query-bar-item__label {
  font-size: 14px;
  color: #333;
  text-align: right;
}

.query-bar-item__content {
  flex: 1;
}

/* 暗色主题适配 */
.dark .query-bar-item__label {
  color: #ccc;
}
</style>
