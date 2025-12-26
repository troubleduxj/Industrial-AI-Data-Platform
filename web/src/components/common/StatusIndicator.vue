<template>
  <div class="status-indicator" :class="indicatorClass">
    <div class="status-dot" :class="dotClass"></div>
    <span class="status-text">{{ statusText }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
  type: {
    type: String,
    default: 'repair', // 'repair' | 'fault' | 'priority' | 'device' | 'custom'
  },
  size: {
    type: String,
    default: 'small', // 'small' | 'medium' | 'large'
  },
  customConfig: {
    type: Object,
    default: () => ({}),
  },
})

// 状态配置映射
const statusConfig = {
  repair: {
    pending: { text: '待处理', color: 'warning', bgColor: '#fff7e6', textColor: '#fa8c16' },
    in_progress: { text: '进行中', color: 'info', bgColor: '#e6f7ff', textColor: '#1890ff' },
    completed: { text: '已完成', color: 'success', bgColor: '#f6ffed', textColor: '#52c41a' },
    cancelled: { text: '已取消', color: 'error', bgColor: '#fff2f0', textColor: '#ff4d4f' },
  },
  fault: {
    true: { text: '故障', color: 'error', bgColor: '#fff2f0', textColor: '#ff4d4f' },
    false: { text: '正常', color: 'success', bgColor: '#f6ffed', textColor: '#52c41a' },
  },
  priority: {
    low: { text: '低', color: 'default', bgColor: '#fafafa', textColor: '#8c8c8c' },
    medium: { text: '中', color: 'info', bgColor: '#e6f7ff', textColor: '#1890ff' },
    high: { text: '高', color: 'warning', bgColor: '#fff7e6', textColor: '#fa8c16' },
    urgent: { text: '紧急', color: 'error', bgColor: '#fff2f0', textColor: '#ff4d4f' },
  },
  device: {
    online: { text: '在线', color: 'success', bgColor: '#f6ffed', textColor: '#52c41a' },
    offline: { text: '离线', color: 'warning', bgColor: '#fff7e6', textColor: '#fa8c16' },
    maintenance: { text: '维护中', color: 'info', bgColor: '#e6f7ff', textColor: '#1890ff' },
    fault: { text: '故障', color: 'error', bgColor: '#fff2f0', textColor: '#ff4d4f' },
  },
  custom: props.customConfig,
}

// 计算状态配置
const config = computed(() => {
  const typeConfig = statusConfig[props.type] || statusConfig.repair
  return (
    typeConfig[props.status] ||
    typeConfig.pending || {
      text: '未知',
      color: 'default',
      bgColor: '#fafafa',
      textColor: '#8c8c8c',
    }
  )
})

// 状态文本
const statusText = computed(() => config.value.text)

// 指示器样式类
const indicatorClass = computed(() => [
  `status-indicator--${props.size}`,
  `status-indicator--${config.value.color}`,
])

// 点样式类
const dotClass = computed(() => [`status-dot--${config.value.color}`])
</script>

<style scoped>
.status-indicator {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.status-indicator--small {
  padding: 1px 6px;
  font-size: 11px;
}

.status-indicator--medium {
  padding: 3px 10px;
  font-size: 13px;
}

.status-indicator--large {
  padding: 4px 12px;
  font-size: 14px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 4px;
  flex-shrink: 0;
}

.status-text {
  line-height: 1;
}

/* 颜色主题 */
.status-indicator--success {
  background: #f6ffed;
  color: #52c41a;
}

.status-dot--success {
  background: #52c41a;
}

.status-indicator--warning {
  background: #fff7e6;
  color: #fa8c16;
}

.status-dot--warning {
  background: #fa8c16;
}

.status-indicator--error {
  background: #fff2f0;
  color: #ff4d4f;
}

.status-dot--error {
  background: #ff4d4f;
}

.status-indicator--info {
  background: #e6f7ff;
  color: #1890ff;
}

.status-dot--info {
  background: #1890ff;
}

.status-indicator--default {
  background: #fafafa;
  color: #8c8c8c;
}

.status-dot--default {
  background: #8c8c8c;
}

/* 暗色主题适配 */
.dark .status-indicator--success {
  background: rgba(82, 196, 26, 0.1);
  color: #73d13d;
}

.dark .status-indicator--warning {
  background: rgba(250, 140, 22, 0.1);
  color: #ffc53d;
}

.dark .status-indicator--error {
  background: rgba(255, 77, 79, 0.1);
  color: #ff7875;
}

.dark .status-indicator--info {
  background: rgba(24, 144, 255, 0.1);
  color: #69c0ff;
}

.dark .status-indicator--default {
  background: rgba(140, 140, 140, 0.1);
  color: #bfbfbf;
}
</style>
