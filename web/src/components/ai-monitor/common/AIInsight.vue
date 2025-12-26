<template>
  <div class="ai-insight">
    <!-- 简单洞察 -->
    <n-alert
      v-if="type === 'simple'"
      :type="alertType"
      :show-icon="showIcon"
      :closable="closable"
      @close="$emit('close')"
    >
      <template v-if="customIcon" #icon>
        <n-icon><component :is="customIcon" /></n-icon>
      </template>
      <template v-if="title" #header>
        <strong>{{ title }}</strong>
      </template>
      {{ content }}
    </n-alert>

    <!-- 卡片洞察 -->
    <n-card v-else-if="type === 'card'" class="insight-card" :size="cardSize">
      <template #header>
        <div class="insight-header">
          <div class="header-left">
            <n-icon v-if="showIcon" :size="20" :color="iconColor">
              <component :is="insightIcon" />
            </n-icon>
            <span class="insight-title">{{ title || 'AI洞察' }}</span>
          </div>
          <div class="header-right">
            <n-tag v-if="priority" :type="priorityType" size="small">
              {{ priorityText }}
            </n-tag>
            <n-button v-if="closable" text size="small" @click="$emit('close')">
              <template #icon>
                <n-icon><CloseOutline /></n-icon>
              </template>
            </n-button>
          </div>
        </div>
      </template>

      <div class="insight-content">
        <div class="insight-text">{{ content }}</div>

        <!-- 详细信息 -->
        <div v-if="details && details.length > 0" class="insight-details">
          <n-collapse>
            <n-collapse-item title="详细分析" name="details">
              <div v-for="(detail, index) in details" :key="index" class="detail-item">
                <div class="detail-label">{{ detail.label }}</div>
                <div class="detail-value">{{ detail.value }}</div>
              </div>
            </n-collapse-item>
          </n-collapse>
        </div>

        <!-- 建议操作 -->
        <div v-if="suggestions && suggestions.length > 0" class="insight-suggestions">
          <div class="suggestions-title">建议操作：</div>
          <n-space vertical size="small">
            <div v-for="(suggestion, index) in suggestions" :key="index" class="suggestion-item">
              <n-icon size="14" color="#52c41a">
                <CheckmarkOutline />
              </n-icon>
              <span>{{ suggestion }}</span>
            </div>
          </n-space>
        </div>

        <!-- 操作按钮 -->
        <div v-if="actions && actions.length > 0" class="insight-actions">
          <n-space>
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

      <template v-if="showFooter" #footer>
        <div class="insight-footer">
          <div class="insight-meta">
            <span class="insight-time">{{ formatTime(timestamp) }}</span>
            <span v-if="confidence" class="insight-confidence">
              置信度: {{ (confidence * 100).toFixed(1) }}%
            </span>
          </div>
          <div v-if="source" class="insight-source">来源: {{ source }}</div>
        </div>
      </template>
    </n-card>

    <!-- 列表洞察 -->
    <div v-else-if="type === 'list'" class="insight-list">
      <div v-if="title" class="list-header">
        <n-icon v-if="showIcon" :size="18" :color="iconColor">
          <component :is="insightIcon" />
        </n-icon>
        <span class="list-title">{{ title }}</span>
      </div>

      <div class="list-content">
        <div v-for="(item, index) in listItems" :key="index" class="list-item">
          <div class="item-indicator">
            <n-icon :size="12" :color="getItemColor(item.type)">
              <component :is="getItemIcon(item.type)" />
            </n-icon>
          </div>
          <div class="item-content">
            <div class="item-text">{{ item.content }}</div>
            <div v-if="item.time || item.confidence" class="item-meta">
              <span v-if="item.time" class="item-time">{{ formatTime(item.time) }}</span>
              <span v-if="item.confidence" class="item-confidence">
                置信度: {{ (item.confidence * 100).toFixed(1) }}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 时间线洞察 -->
    <div v-else-if="type === 'timeline'" class="insight-timeline">
      <n-timeline>
        <n-timeline-item
          v-for="(item, index) in timelineItems"
          :key="index"
          :type="getTimelineType(item.type)"
          :title="item.title"
          :content="item.content"
          :time="formatTime(item.time)"
        >
          <template #icon>
            <n-icon><component :is="getItemIcon(item.type)" /></n-icon>
          </template>
        </n-timeline-item>
      </n-timeline>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  BulbOutline,
  WarningOutline,
  InformationCircleOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  CheckmarkOutline,
  CloseOutline,
  TrendingUpOutline,
  AlertTriangleOutline,
} from '@vicons/ionicons5'
import { format } from 'date-fns'

// Props
const props = defineProps({
  // 洞察类型
  type: {
    type: String,
    default: 'simple',
    validator: (value) => ['simple', 'card', 'list', 'timeline'].includes(value),
  },
  // 洞察级别
  level: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'info', 'warning', 'error'].includes(value),
  },
  // 优先级
  priority: {
    type: String,
    default: '',
    validator: (value) => ['', 'low', 'medium', 'high', 'critical'].includes(value),
  },
  // 标题
  title: {
    type: String,
    default: '',
  },
  // 内容
  content: {
    type: String,
    required: true,
  },
  // 详细信息
  details: {
    type: Array,
    default: () => [],
  },
  // 建议
  suggestions: {
    type: Array,
    default: () => [],
  },
  // 操作按钮
  actions: {
    type: Array,
    default: () => [],
  },
  // 列表项目
  listItems: {
    type: Array,
    default: () => [],
  },
  // 时间线项目
  timelineItems: {
    type: Array,
    default: () => [],
  },
  // 时间戳
  timestamp: {
    type: [String, Number, Date],
    default: () => new Date(),
  },
  // 置信度 (0-1)
  confidence: {
    type: Number,
    default: null,
  },
  // 来源
  source: {
    type: String,
    default: '',
  },
  // 是否显示图标
  showIcon: {
    type: Boolean,
    default: true,
  },
  // 是否可关闭
  closable: {
    type: Boolean,
    default: false,
  },
  // 是否显示底部
  showFooter: {
    type: Boolean,
    default: true,
  },
  // 卡片大小
  cardSize: {
    type: String,
    default: 'medium',
  },
})

// Emits
const emit = defineEmits(['close', 'action'])

// 级别配置
const levelConfig = {
  success: {
    alertType: 'success',
    icon: CheckmarkCircleOutline,
    color: '#52c41a',
  },
  info: {
    alertType: 'info',
    icon: InformationCircleOutline,
    color: '#1890ff',
  },
  warning: {
    alertType: 'warning',
    icon: WarningOutline,
    color: '#faad14',
  },
  error: {
    alertType: 'error',
    icon: CloseCircleOutline,
    color: '#ff4d4f',
  },
}

// 优先级配置
const priorityConfig = {
  low: { type: 'default', text: '低' },
  medium: { type: 'info', text: '中' },
  high: { type: 'warning', text: '高' },
  critical: { type: 'error', text: '紧急' },
}

// 计算属性
const alertType = computed(() => {
  return levelConfig[props.level]?.alertType || 'info'
})

const insightIcon = computed(() => {
  return levelConfig[props.level]?.icon || BulbOutline
})

const iconColor = computed(() => {
  return levelConfig[props.level]?.color || '#1890ff'
})

const customIcon = computed(() => {
  return props.showIcon ? insightIcon.value : null
})

const priorityType = computed(() => {
  return priorityConfig[props.priority]?.type || 'default'
})

const priorityText = computed(() => {
  return priorityConfig[props.priority]?.text || props.priority
})

// 获取项目颜色
const getItemColor = (type) => {
  const colors = {
    success: '#52c41a',
    info: '#1890ff',
    warning: '#faad14',
    error: '#ff4d4f',
    trend: '#722ed1',
  }
  return colors[type] || '#1890ff'
}

// 获取项目图标
const getItemIcon = (type) => {
  const icons = {
    success: CheckmarkCircleOutline,
    info: InformationCircleOutline,
    warning: WarningOutline,
    error: CloseCircleOutline,
    trend: TrendingUpOutline,
  }
  return icons[type] || InformationCircleOutline
}

// 获取时间线类型
const getTimelineType = (type) => {
  const types = {
    success: 'success',
    info: 'info',
    warning: 'warning',
    error: 'error',
  }
  return types[type] || 'info'
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''

  try {
    const date = new Date(timestamp)
    return format(date, 'MM-dd HH:mm')
  } catch (error) {
    return ''
  }
}
</script>

<style scoped>
.ai-insight {
  width: 100%;
}

/* 卡片洞察 */
.insight-card {
  border-left: 4px solid v-bind(iconColor);
}

.insight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.insight-title {
  font-weight: 500;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.insight-content {
  line-height: 1.6;
}

.insight-text {
  margin-bottom: 16px;
  color: #333;
}

.insight-details {
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  color: #666;
  font-size: 14px;
}

.detail-value {
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

.insight-suggestions {
  margin-bottom: 16px;
  padding: 12px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
}

.suggestions-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #333;
}

.insight-actions {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.insight-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
}

.insight-meta {
  display: flex;
  gap: 12px;
}

/* 列表洞察 */
.insight-list {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  overflow: hidden;
}

.list-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.list-title {
  font-weight: 500;
  color: #333;
}

.list-content {
  padding: 8px 0;
}

.list-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 16px;
  border-bottom: 1px solid #f9f9f9;
}

.list-item:last-child {
  border-bottom: none;
}

.item-indicator {
  margin-top: 2px;
}

.item-content {
  flex: 1;
}

.item-text {
  color: #333;
  line-height: 1.5;
  margin-bottom: 4px;
}

.item-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
}

/* 时间线洞察 */
.insight-timeline {
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

/* 响应式 */
@media (max-width: 768px) {
  .insight-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
  }

  .insight-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .detail-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
}
</style>
