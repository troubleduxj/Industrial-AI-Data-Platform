<template>
  <NCard class="stat-card" :class="cardClass" v-bind="$attrs">
    <div class="stat-content">
      <!-- 图标区域 -->
      <div v-if="icon || $slots.icon" class="stat-icon" :class="iconClass">
        <slot name="icon">
          <TheIcon v-if="icon" :icon="icon" :size="iconSize" />
        </slot>
      </div>

      <!-- 内容区域 -->
      <div class="stat-info">
        <div class="stat-value" :class="valueClass">
          <slot name="value">{{ value }}</slot>
        </div>
        <div class="stat-label" :class="labelClass">
          <slot name="label">{{ label }}</slot>
        </div>
        <!-- 额外信息 -->
        <div v-if="$slots.extra" class="stat-extra">
          <slot name="extra"></slot>
        </div>
      </div>
    </div>
  </NCard>
</template>

<script setup>
import { NCard } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { computed } from 'vue'

/**
 * 统计卡片组件
 * 用于显示统计数据，支持图标、数值、标签等内容
 */
const props = defineProps({
  // 统计数值
  value: {
    type: [String, Number],
    default: '',
  },
  // 标签文本
  label: {
    type: String,
    default: '',
  },
  // 图标名称
  icon: {
    type: String,
    default: '',
  },
  // 图标大小
  iconSize: {
    type: Number,
    default: 24,
  },
  // 卡片类型
  type: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'primary', 'success', 'warning', 'error'].includes(value),
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
    default: true,
  },
})

// 卡片样式类
const cardClass = computed(() => {
  return {
    [`stat-card--${props.type}`]: props.type !== 'default',
    [`stat-card--${props.size}`]: props.size !== 'medium',
    'stat-card--hoverable': props.hoverable,
  }
})

// 图标样式类
const iconClass = computed(() => {
  return {
    [`stat-icon--${props.type}`]: props.type !== 'default',
  }
})

// 数值样式类
const valueClass = computed(() => {
  return {
    [`stat-value--${props.size}`]: props.size !== 'medium',
  }
})

// 标签样式类
const labelClass = computed(() => {
  return {
    [`stat-label--${props.size}`]: props.size !== 'medium',
  }
})
</script>

<style scoped>
.stat-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-card--hoverable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 图标样式 */
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.stat-icon--default {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon--success {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon--warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon--error {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  color: #d03050;
}

/* 信息区域 */
.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-value--small {
  font-size: 20px;
}

.stat-value--large {
  font-size: 28px;
}

.stat-label {
  font-size: 14px;
  color: #666;
  line-height: 1.2;
}

.stat-label--small {
  font-size: 12px;
}

.stat-label--large {
  font-size: 16px;
}

.stat-extra {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

/* 暗色主题适配 */
.dark .stat-value {
  color: #fff;
}

.dark .stat-label {
  color: #ccc;
}

.dark .stat-extra {
  color: #999;
}

/* 尺寸变体 */
.stat-card--small .stat-content {
  gap: 12px;
}

.stat-card--small .stat-icon {
  width: 40px;
  height: 40px;
}

.stat-card--large .stat-content {
  gap: 20px;
}

.stat-card--large .stat-icon {
  width: 56px;
  height: 56px;
}
</style>
