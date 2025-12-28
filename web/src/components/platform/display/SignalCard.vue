<template>
  <n-card
    class="signal-card"
    :class="cardClass"
    size="small"
    hoverable
    @click="$emit('click')"
  >
    <template #header>
      <div class="signal-header">
        <span class="signal-name">{{ signal.name }}</span>
        <n-tag v-if="status" :type="status.type" size="small">
          {{ status.text }}
        </n-tag>
      </div>
    </template>

    <div class="signal-content">
      <!-- 数值显示 -->
      <div class="signal-value">
        <span class="value">{{ formattedValue }}</span>
        <span v-if="signal.unit" class="unit">{{ signal.unit }}</span>
      </div>

      <!-- 趋势图标 -->
      <div v-if="showTrend && trend" class="signal-trend">
        <n-icon :component="trendIcon" :color="trendColor" :size="20" />
      </div>
    </div>

    <!-- 进度条 -->
    <n-progress
      v-if="showProgress"
      :percentage="progressPercentage"
      :color="progressColor"
      :show-indicator="false"
      :height="4"
      class="signal-progress"
    />

    <!-- 迷你图表 -->
    <div v-if="showMiniChart && historyData.length > 0" class="mini-chart">
      <div class="mini-chart-container" ref="miniChartRef"></div>
    </div>

    <!-- 更新时间 -->
    <div v-if="lastUpdate" class="signal-update-time">
      更新于 {{ formatTime(lastUpdate) }}
    </div>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { NCard, NTag, NIcon, NProgress } from 'naive-ui'
import { 
  TrendingUpOutline, 
  TrendingDownOutline, 
  RemoveOutline 
} from '@vicons/ionicons5'

// Props
const props = defineProps({
  signal: {
    type: Object,
    required: true
  },
  value: {
    type: [Number, String, Boolean],
    default: null
  },
  previousValue: {
    type: [Number, String, Boolean],
    default: null
  },
  historyData: {
    type: Array,
    default: () => []
  },
  lastUpdate: {
    type: [String, Date],
    default: null
  },
  showTrend: {
    type: Boolean,
    default: true
  },
  showMiniChart: {
    type: Boolean,
    default: false
  }
})

// Emits
defineEmits(['click'])

const miniChartRef = ref(null)

// 格式化值
const formattedValue = computed(() => {
  if (props.value === null || props.value === undefined) return '-'

  switch (props.signal.data_type) {
    case 'float':
    case 'double':
      return typeof props.value === 'number' ? props.value.toFixed(2) : String(props.value)
    case 'int':
    case 'bigint':
      return String(Math.round(Number(props.value)))
    case 'bool':
    case 'boolean':
      return props.value ? '开启' : '关闭'
    default:
      return String(props.value)
  }
})

// 状态
const status = computed(() => {
  if (!props.signal.value_range || !isNumericType(props.signal.data_type)) {
    return null
  }

  const value = Number(props.value)
  const { min, max } = props.signal.value_range

  if ((min !== undefined && value < min) || (max !== undefined && value > max)) {
    return { type: 'error', text: value < min ? '过低' : '过高' }
  }

  if (min !== undefined && max !== undefined) {
    const range = max - min
    const warningLow = min + range * 0.1
    const warningHigh = max - range * 0.1
    if (value <= warningLow || value >= warningHigh) {
      return { type: 'warning', text: '警告' }
    }
  }

  return { type: 'success', text: '正常' }
})

// 卡片样式类
const cardClass = computed(() => {
  if (!status.value) return ''
  return `signal-card--${status.value.type}`
})

// 趋势
const trend = computed(() => {
  if (!isNumericType(props.signal.data_type) || props.previousValue === null) {
    return null
  }
  const current = Number(props.value)
  const previous = Number(props.previousValue)
  if (current > previous) return 'up'
  if (current < previous) return 'down'
  return 'stable'
})

// 趋势图标
const trendIcon = computed(() => {
  if (trend.value === 'up') return TrendingUpOutline
  if (trend.value === 'down') return TrendingDownOutline
  return RemoveOutline
})

// 趋势颜色
const trendColor = computed(() => {
  if (trend.value === 'up') return '#18a058'
  if (trend.value === 'down') return '#d03050'
  return '#999'
})

// 是否显示进度条
const showProgress = computed(() => {
  return props.signal.value_range && isNumericType(props.signal.data_type)
})

// 进度百分比
const progressPercentage = computed(() => {
  if (!props.signal.value_range) return 0
  const { min = 0, max = 100 } = props.signal.value_range
  const value = Number(props.value)
  return Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))
})

// 进度条颜色
const progressColor = computed(() => {
  if (!status.value) return '#2080f0'
  switch (status.value.type) {
    case 'success': return '#18a058'
    case 'warning': return '#f0a020'
    case 'error': return '#d03050'
    default: return '#2080f0'
  }
})

// 判断是否为数值类型
function isNumericType(dataType) {
  return ['float', 'int', 'double', 'bigint'].includes(dataType)
}

// 格式化时间
function formatTime(time) {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped>
.signal-card {
  transition: all 0.3s ease;
  cursor: pointer;
}

.signal-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.signal-card--success {
  border-left: 4px solid #18a058;
}

.signal-card--warning {
  border-left: 4px solid #f0a020;
}

.signal-card--error {
  border-left: 4px solid #d03050;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.signal-name {
  font-weight: 500;
  font-size: 14px;
  color: var(--n-text-color);
}

.signal-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.signal-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.value {
  font-size: 28px;
  font-weight: 600;
  color: var(--n-text-color);
  line-height: 1.2;
}

.unit {
  font-size: 12px;
  color: var(--n-text-color-3);
}

.signal-trend {
  display: flex;
  align-items: center;
}

.signal-progress {
  margin-top: 8px;
}

.mini-chart {
  margin-top: 12px;
}

.mini-chart-container {
  height: 40px;
  width: 100%;
}

.signal-update-time {
  margin-top: 8px;
  font-size: 11px;
  color: var(--n-text-color-3);
  text-align: right;
}
</style>
