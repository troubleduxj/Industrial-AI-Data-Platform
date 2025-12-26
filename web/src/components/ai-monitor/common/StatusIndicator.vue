<template>
  <div class="status-indicator">
    <!-- 基础状态指示器 -->
    <div v-if="type === 'basic'" class="basic-indicator">
      <div class="status-dot" :class="statusClass"></div>
      <span class="status-text">{{ statusText }}</span>
    </div>

    <!-- 标签式状态指示器 -->
    <n-tag v-else-if="type === 'tag'" :type="tagType" :size="size">
      <template v-if="showIcon" #icon>
        <n-icon><component :is="statusIcon" /></n-icon>
      </template>
      {{ statusText }}
    </n-tag>

    <!-- 进度式状态指示器 -->
    <div v-else-if="type === 'progress'" class="progress-indicator">
      <div class="progress-header">
        <span class="progress-label">{{ statusText }}</span>
        <span class="progress-value">{{ progressValue }}%</span>
      </div>
      <n-progress
        :percentage="progressValue"
        :status="progressStatus"
        :show-indicator="false"
        :height="progressHeight"
      />
    </div>

    <!-- 详细状态指示器 -->
    <div v-else-if="type === 'detailed'" class="detailed-indicator">
      <div class="status-header">
        <div class="status-main">
          <n-icon :size="iconSize" :color="statusColor">
            <component :is="statusIcon" />
          </n-icon>
          <div class="status-info">
            <div class="status-title">{{ statusText }}</div>
            <div v-if="subtitle" class="status-subtitle">{{ subtitle }}</div>
          </div>
        </div>
        <div v-if="showTime" class="status-time">
          {{ formatTime(timestamp) }}
        </div>
      </div>

      <!-- 额外信息 -->
      <div v-if="details && details.length > 0" class="status-details">
        <div v-for="(detail, index) in details" :key="index" class="detail-item">
          <span class="detail-label">{{ detail.label }}:</span>
          <span class="detail-value">{{ detail.value }}</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div v-if="actions && actions.length > 0" class="status-actions">
        <n-space size="small">
          <n-button
            v-for="action in actions"
            :key="action.key"
            :type="action.type || 'default'"
            :size="action.size || 'small'"
            @click="$emit('action', action.key)"
          >
            <template v-if="action.icon" #icon>
              <n-icon><component :is="action.icon" /></n-icon>
            </template>
            {{ action.label }}
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 卡片式状态指示器 -->
    <n-card v-else-if="type === 'card'" size="small" class="card-indicator">
      <div class="card-content">
        <div class="card-icon">
          <n-icon :size="24" :color="statusColor">
            <component :is="statusIcon" />
          </n-icon>
        </div>
        <div class="card-info">
          <div class="card-title">{{ statusText }}</div>
          <div v-if="value" class="card-value">{{ value }}</div>
          <div v-if="description" class="card-description">{{ description }}</div>
        </div>
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  CheckmarkCircleOutline,
  AlertCircleOutline,
  CloseCircleOutline,
  TimeOutline,
  PlayOutline,
  PauseOutline,
  StopOutline,
  RefreshOutline,
  WarningOutline,
  InformationCircleOutline,
} from '@vicons/ionicons5'
import { format } from 'date-fns'

// Props
const props = defineProps({
  // 状态值
  status: {
    type: String,
    required: true,
    validator: (value) =>
      [
        'success',
        'error',
        'warning',
        'info',
        'loading',
        'running',
        'stopped',
        'paused',
        'pending',
        'unknown',
      ].includes(value),
  },
  // 显示类型
  type: {
    type: String,
    default: 'basic',
    validator: (value) => ['basic', 'tag', 'progress', 'detailed', 'card'].includes(value),
  },
  // 自定义状态文本
  text: {
    type: String,
    default: '',
  },
  // 副标题
  subtitle: {
    type: String,
    default: '',
  },
  // 描述
  description: {
    type: String,
    default: '',
  },
  // 数值
  value: {
    type: [String, Number],
    default: '',
  },
  // 进度值 (0-100)
  progress: {
    type: Number,
    default: 0,
  },
  // 进度条高度
  progressHeight: {
    type: Number,
    default: 6,
  },
  // 时间戳
  timestamp: {
    type: [String, Number, Date],
    default: null,
  },
  // 是否显示时间
  showTime: {
    type: Boolean,
    default: false,
  },
  // 是否显示图标
  showIcon: {
    type: Boolean,
    default: true,
  },
  // 图标大小
  iconSize: {
    type: Number,
    default: 18,
  },
  // 组件大小
  size: {
    type: String,
    default: 'medium',
  },
  // 详细信息
  details: {
    type: Array,
    default: () => [],
  },
  // 操作按钮
  actions: {
    type: Array,
    default: () => [],
  },
})

// Emits
const emit = defineEmits(['action'])

// 状态配置映射
const statusConfig = {
  success: {
    text: '正常',
    color: '#52c41a',
    icon: CheckmarkCircleOutline,
    tagType: 'success',
    class: 'success',
  },
  error: {
    text: '错误',
    color: '#ff4d4f',
    icon: CloseCircleOutline,
    tagType: 'error',
    class: 'error',
  },
  warning: {
    text: '警告',
    color: '#faad14',
    icon: WarningOutline,
    tagType: 'warning',
    class: 'warning',
  },
  info: {
    text: '信息',
    color: '#1890ff',
    icon: InformationCircleOutline,
    tagType: 'info',
    class: 'info',
  },
  loading: {
    text: '加载中',
    color: '#1890ff',
    icon: RefreshOutline,
    tagType: 'info',
    class: 'loading',
  },
  running: {
    text: '运行中',
    color: '#52c41a',
    icon: PlayOutline,
    tagType: 'success',
    class: 'running',
  },
  stopped: {
    text: '已停止',
    color: '#d9d9d9',
    icon: StopOutline,
    tagType: 'default',
    class: 'stopped',
  },
  paused: {
    text: '已暂停',
    color: '#faad14',
    icon: PauseOutline,
    tagType: 'warning',
    class: 'paused',
  },
  pending: {
    text: '等待中',
    color: '#722ed1',
    icon: TimeOutline,
    tagType: 'default',
    class: 'pending',
  },
  unknown: {
    text: '未知',
    color: '#d9d9d9',
    icon: AlertCircleOutline,
    tagType: 'default',
    class: 'unknown',
  },
}

// 计算属性
const currentConfig = computed(() => {
  return statusConfig[props.status] || statusConfig.unknown
})

const statusText = computed(() => {
  return props.text || currentConfig.value.text
})

const statusColor = computed(() => {
  return currentConfig.value.color
})

const statusIcon = computed(() => {
  return currentConfig.value.icon
})

const statusClass = computed(() => {
  return currentConfig.value.class
})

const tagType = computed(() => {
  return currentConfig.value.tagType
})

const progressValue = computed(() => {
  return Math.max(0, Math.min(100, props.progress))
})

const progressStatus = computed(() => {
  if (props.status === 'error') return 'error'
  if (props.status === 'warning') return 'warning'
  if (props.status === 'success') return 'success'
  return 'default'
})

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''

  try {
    const date = new Date(timestamp)
    return format(date, 'yyyy-MM-dd HH:mm:ss')
  } catch (error) {
    return ''
  }
}
</script>

<style scoped>
.status-indicator {
  display: inline-block;
}

/* 基础指示器 */
.basic-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.success {
  background-color: #52c41a;
}

.status-dot.error {
  background-color: #ff4d4f;
}

.status-dot.warning {
  background-color: #faad14;
}

.status-dot.info {
  background-color: #1890ff;
}

.status-dot.loading {
  background-color: #1890ff;
  animation: pulse 1.5s ease-in-out infinite;
}

.status-dot.running {
  background-color: #52c41a;
  animation: pulse 2s ease-in-out infinite;
}

.status-dot.stopped {
  background-color: #d9d9d9;
}

.status-dot.paused {
  background-color: #faad14;
}

.status-dot.pending {
  background-color: #722ed1;
}

.status-dot.unknown {
  background-color: #d9d9d9;
}

.status-text {
  font-size: 14px;
  color: #333;
}

/* 进度指示器 */
.progress-indicator {
  width: 100%;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 14px;
  color: #333;
}

.progress-value {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

/* 详细指示器 */
.detailed-indicator {
  width: 100%;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.status-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-info {
  flex: 1;
}

.status-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.status-subtitle {
  font-size: 12px;
  color: #666;
}

.status-time {
  font-size: 12px;
  color: #999;
}

.status-details {
  margin-bottom: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 14px;
}

.detail-label {
  color: #666;
}

.detail-value {
  color: #333;
  font-weight: 500;
}

.status-actions {
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

/* 卡片指示器 */
.card-indicator {
  width: 100%;
}

.card-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-icon {
  flex-shrink: 0;
}

.card-info {
  flex: 1;
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.card-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.card-description {
  font-size: 12px;
  color: #666;
}

/* 动画 */
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .status-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .detail-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
}
</style>
