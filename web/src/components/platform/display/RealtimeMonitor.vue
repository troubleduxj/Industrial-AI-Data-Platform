<template>
  <div class="realtime-monitor">
    <!-- 监控头部 -->
    <div class="monitor-header">
      <div class="monitor-status">
        <n-badge :dot="true" :type="isConnected ? 'success' : 'error'" />
        <span>{{ isConnected ? '实时监控中' : '连接断开' }}</span>
      </div>
      <div class="monitor-actions">
        <n-button size="small" :loading="refreshing" @click="handleRefresh">
          <template #icon>
            <n-icon :component="RefreshOutline" />
          </template>
          刷新
        </n-button>
        <n-button size="small" :type="isPaused ? 'primary' : 'default'" @click="togglePause">
          <template #icon>
            <n-icon :component="isPaused ? PlayOutline : PauseOutline" />
          </template>
          {{ isPaused ? '继续' : '暂停' }}
        </n-button>
      </div>
    </div>

    <!-- 监控网格 -->
    <div class="monitor-grid">
      <div
        v-for="signal in signals"
        :key="signal.code"
        class="monitor-item"
        :class="getMonitorItemClass(signal)"
      >
        <div class="monitor-label">{{ signal.name }}</div>
        <div class="monitor-value">
          {{ formatValue(signal) }}
          <span v-if="signal.unit" class="monitor-unit">{{ signal.unit }}</span>
        </div>
        <div class="monitor-status-icon">
          <n-icon
            :component="getStatusIcon(signal)"
            :color="getStatusColor(signal)"
            :size="24"
          />
        </div>
        <!-- 范围指示器 -->
        <div v-if="signal.value_range" class="monitor-range">
          <div class="range-bar">
            <div 
              class="range-fill" 
              :style="{ 
                width: `${getRangePercentage(signal)}%`,
                backgroundColor: getStatusColor(signal)
              }"
            ></div>
            <div 
              class="range-indicator" 
              :style="{ left: `${getRangePercentage(signal)}%` }"
            ></div>
          </div>
          <div class="range-labels">
            <span>{{ signal.value_range.min }}</span>
            <span>{{ signal.value_range.max }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 最后更新时间 -->
    <div class="monitor-footer">
      <span>最后更新: {{ lastUpdateTime }}</span>
      <span>刷新间隔: {{ refreshInterval / 1000 }}秒</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NButton, NIcon, NBadge } from 'naive-ui'
import { 
  RefreshOutline, 
  PlayOutline, 
  PauseOutline,
  CheckmarkCircleOutline,
  WarningOutline,
  CloseCircleOutline
} from '@vicons/ionicons5'

// Props
const props = defineProps({
  signals: {
    type: Array,
    required: true
  },
  data: {
    type: Object,
    default: () => ({})
  },
  refreshInterval: {
    type: Number,
    default: 5000
  }
})

// Emits
const emit = defineEmits(['refresh'])

const isConnected = ref(true)
const isPaused = ref(false)
const refreshing = ref(false)
const lastUpdateTime = ref('-')
let refreshTimer = null

// 格式化值
function formatValue(signal) {
  const value = props.data[signal.code]
  if (value === null || value === undefined) return '-'

  switch (signal.data_type) {
    case 'float':
    case 'double':
      return typeof value === 'number' ? value.toFixed(2) : String(value)
    case 'int':
    case 'bigint':
      return String(Math.round(Number(value)))
    case 'bool':
    case 'boolean':
      return value ? '开启' : '关闭'
    default:
      return String(value)
  }
}

// 获取信号状态
function getSignalStatus(signal) {
  const value = props.data[signal.code]
  if (value === null || value === undefined) return 'unknown'

  if (!signal.value_range || !isNumericType(signal.data_type)) {
    return 'normal'
  }

  const numValue = Number(value)
  const { min, max } = signal.value_range

  if ((min !== undefined && numValue < min) || (max !== undefined && numValue > max)) {
    return 'error'
  }

  if (min !== undefined && max !== undefined) {
    const range = max - min
    const warningLow = min + range * 0.1
    const warningHigh = max - range * 0.1
    if (numValue <= warningLow || numValue >= warningHigh) {
      return 'warning'
    }
  }

  return 'normal'
}

// 获取监控项样式类
function getMonitorItemClass(signal) {
  const status = getSignalStatus(signal)
  return `monitor-item--${status}`
}

// 获取状态图标
function getStatusIcon(signal) {
  const status = getSignalStatus(signal)
  switch (status) {
    case 'normal': return CheckmarkCircleOutline
    case 'warning': return WarningOutline
    case 'error': return CloseCircleOutline
    default: return CheckmarkCircleOutline
  }
}

// 获取状态颜色
function getStatusColor(signal) {
  const status = getSignalStatus(signal)
  switch (status) {
    case 'normal': return '#18a058'
    case 'warning': return '#f0a020'
    case 'error': return '#d03050'
    default: return '#999'
  }
}

// 获取范围百分比
function getRangePercentage(signal) {
  const value = props.data[signal.code]
  if (value === null || value === undefined || !signal.value_range) return 0

  const { min = 0, max = 100 } = signal.value_range
  const numValue = Number(value)
  return Math.max(0, Math.min(100, ((numValue - min) / (max - min)) * 100))
}

// 判断是否为数值类型
function isNumericType(dataType) {
  return ['float', 'int', 'double', 'bigint'].includes(dataType)
}

// 处理刷新
async function handleRefresh() {
  refreshing.value = true
  try {
    emit('refresh')
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
  } finally {
    refreshing.value = false
  }
}

// 切换暂停
function togglePause() {
  isPaused.value = !isPaused.value
  if (isPaused.value) {
    stopAutoRefresh()
  } else {
    startAutoRefresh()
  }
}

// 开始自动刷新
function startAutoRefresh() {
  if (refreshTimer) return
  refreshTimer = setInterval(() => {
    if (!isPaused.value) {
      handleRefresh()
    }
  }, props.refreshInterval)
}

// 停止自动刷新
function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 生命周期
onMounted(() => {
  lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.realtime-monitor {
  width: 100%;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--n-border-color);
}

.monitor-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--n-text-color);
}

.monitor-actions {
  display: flex;
  gap: 8px;
}

.monitor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.monitor-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px;
  border-radius: 12px;
  background: var(--n-card-color);
  border: 2px solid var(--n-border-color);
  transition: all 0.3s ease;
}

.monitor-item:hover {
  transform: scale(1.02);
}

.monitor-item--normal {
  border-color: #18a058;
  background: linear-gradient(135deg, rgba(24, 160, 88, 0.08), transparent);
}

.monitor-item--warning {
  border-color: #f0a020;
  background: linear-gradient(135deg, rgba(240, 160, 32, 0.08), transparent);
}

.monitor-item--error {
  border-color: #d03050;
  background: linear-gradient(135deg, rgba(208, 48, 80, 0.08), transparent);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.monitor-label {
  font-size: 12px;
  color: var(--n-text-color-3);
  margin-bottom: 8px;
  text-align: center;
}

.monitor-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--n-text-color);
  margin-bottom: 8px;
  text-align: center;
}

.monitor-unit {
  font-size: 12px;
  color: var(--n-text-color-3);
  font-weight: normal;
  margin-left: 4px;
}

.monitor-status-icon {
  margin-bottom: 12px;
}

.monitor-range {
  width: 100%;
  margin-top: 8px;
}

.range-bar {
  position: relative;
  height: 6px;
  background: var(--n-border-color);
  border-radius: 3px;
  overflow: hidden;
}

.range-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.range-indicator {
  position: absolute;
  top: -2px;
  width: 10px;
  height: 10px;
  background: white;
  border: 2px solid currentColor;
  border-radius: 50%;
  transform: translateX(-50%);
  transition: left 0.3s ease;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 10px;
  color: var(--n-text-color-3);
}

.monitor-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--n-border-color);
  font-size: 12px;
  color: var(--n-text-color-3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .monitor-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }

  .monitor-item {
    padding: 16px 12px;
  }

  .monitor-value {
    font-size: 20px;
  }
}
</style>
