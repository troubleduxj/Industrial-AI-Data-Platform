<template>
  <n-card :title="title" :class="cardClass" hoverable @click="handleClick">
    <template #header-extra>
      <n-icon :size="20" :color="iconColor">
        <component :is="iconComponent" />
      </n-icon>
    </template>

    <div class="task-status-content">
      <div class="status-value">
        {{ formatValue(value) }}
      </div>

      <div class="status-info">
        <div class="status-label">{{ label }}</div>

        <div v-if="trend !== null" class="status-trend">
          <n-icon :size="14" :color="trendColor">
            <ArrowUpOutline v-if="trend > 0" />
            <ArrowDownOutline v-if="trend < 0" />
            <RemoveOutline v-if="trend === 0" />
          </n-icon>
          <span :style="{ color: trendColor }">{{ formatTrend(trend) }}</span>
        </div>
      </div>

      <div v-if="description" class="status-description">
        {{ description }}
      </div>

      <!-- 进度条 -->
      <div v-if="showProgress" class="status-progress">
        <n-progress
          type="line"
          :percentage="progressPercentage"
          :color="progressColor"
          :height="6"
          :show-indicator="false"
        />
      </div>

      <!-- 状态标签 -->
      <div v-if="tags && tags.length > 0" class="status-tags">
        <n-tag v-for="tag in tags" :key="tag.label" :type="tag.type || 'default'" size="small">
          {{ tag.label }}
        </n-tag>
      </div>
    </div>
  </n-card>
</template>

<script setup>
import { computed } from 'vue'
import { NCard, NIcon, NProgress, NTag } from 'naive-ui'
import {
  CheckmarkCircleOutline,
  CloseCircleOutline,
  TimeOutline,
  PlayCircleOutline,
  PauseCircleOutline,
  WarningOutline,
  ArrowUpOutline,
  ArrowDownOutline,
  RemoveOutline,
  StatsChartOutline,
} from '@vicons/ionicons5'

/**
 * 任务状态卡片组件
 * 用于显示各种任务状态信息
 */
const props = defineProps({
  // 卡片标题
  title: {
    type: String,
    required: true,
  },
  // 状态值
  value: {
    type: [Number, String],
    required: true,
  },
  // 状态标签
  label: {
    type: String,
    default: '',
  },
  // 状态类型
  type: {
    type: String,
    default: 'default',
    validator: (value) =>
      ['default', 'success', 'warning', 'error', 'info', 'running', 'stopped'].includes(value),
  },
  // 趋势值（正数上升，负数下降，0持平）
  trend: {
    type: Number,
    default: null,
  },
  // 描述信息
  description: {
    type: String,
    default: '',
  },
  // 是否显示进度条
  showProgress: {
    type: Boolean,
    default: false,
  },
  // 进度百分比
  progressPercentage: {
    type: Number,
    default: 0,
  },
  // 状态标签
  tags: {
    type: Array,
    default: () => [],
  },
  // 是否可点击
  clickable: {
    type: Boolean,
    default: false,
  },
  // 数值格式化类型
  valueType: {
    type: String,
    default: 'number',
    validator: (value) => ['number', 'percentage', 'duration', 'bytes'].includes(value),
  },
})

const emit = defineEmits(['click'])

// 卡片样式类
const cardClass = computed(() => {
  const classes = ['task-status-card', `task-status-${props.type}`]
  if (props.clickable) {
    classes.push('clickable')
  }
  return classes.join(' ')
})

// 图标组件
const iconComponent = computed(() => {
  const iconMap = {
    success: CheckmarkCircleOutline,
    error: CloseCircleOutline,
    warning: WarningOutline,
    running: PlayCircleOutline,
    stopped: PauseCircleOutline,
    info: StatsChartOutline,
    default: TimeOutline,
  }
  return iconMap[props.type] || iconMap.default
})

// 图标颜色
const iconColor = computed(() => {
  const colorMap = {
    success: '#52c41a',
    error: '#ff4d4f',
    warning: '#faad14',
    running: '#1890ff',
    stopped: '#8c8c8c',
    info: '#722ed1',
    default: '#8c8c8c',
  }
  return colorMap[props.type] || colorMap.default
})

// 趋势颜色
const trendColor = computed(() => {
  if (props.trend === null) return '#8c8c8c'
  if (props.trend > 0) return '#52c41a'
  if (props.trend < 0) return '#ff4d4f'
  return '#8c8c8c'
})

// 进度条颜色
const progressColor = computed(() => {
  const colorMap = {
    success: '#52c41a',
    error: '#ff4d4f',
    warning: '#faad14',
    running: '#1890ff',
    stopped: '#8c8c8c',
    info: '#722ed1',
    default: '#1890ff',
  }
  return colorMap[props.type] || colorMap.default
})

// 格式化数值
const formatValue = (value) => {
  if (value === null || value === undefined) return '-'

  switch (props.valueType) {
    case 'percentage':
      return `${Number(value).toFixed(1)}%`
    case 'duration':
      return formatDuration(value)
    case 'bytes':
      return formatBytes(value)
    case 'number':
    default:
      if (typeof value === 'number') {
        return value.toLocaleString()
      }
      return value
  }
}

// 格式化趋势
const formatTrend = (trend) => {
  if (trend === null || trend === undefined) return ''
  const abs = Math.abs(trend)
  if (props.valueType === 'percentage') {
    return `${abs.toFixed(1)}%`
  }
  return abs.toLocaleString()
}

// 格式化时长
const formatDuration = (seconds) => {
  if (seconds < 60) {
    return `${seconds}s`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
  }
}

// 格式化字节
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

// 点击处理
const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style scoped>
.task-status-card {
  transition: all 0.3s ease;
  border-radius: 8px;
}

.task-status-card.clickable {
  cursor: pointer;
}

.task-status-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.task-status-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-value {
  font-size: 28px;
  font-weight: 600;
  line-height: 1;
  color: #262626;
}

.status-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-label {
  font-size: 14px;
  color: #8c8c8c;
}

.status-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-description {
  font-size: 12px;
  color: #595959;
  line-height: 1.4;
}

.status-progress {
  margin-top: 4px;
}

.status-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

/* 状态类型样式 */
.task-status-success {
  border-left: 4px solid #52c41a;
}

.task-status-error {
  border-left: 4px solid #ff4d4f;
}

.task-status-warning {
  border-left: 4px solid #faad14;
}

.task-status-running {
  border-left: 4px solid #1890ff;
}

.task-status-stopped {
  border-left: 4px solid #8c8c8c;
}

.task-status-info {
  border-left: 4px solid #722ed1;
}

.task-status-default {
  border-left: 4px solid #d9d9d9;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .status-value {
    font-size: 24px;
  }

  .status-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
