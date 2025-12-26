<template>
  <BaseCard
    :title="device.name || '未命名设备'"
    :type="cardType"
    :size="size"
    :hoverable="clickable"
    :clickable="clickable"
    class="device-status-card"
    :class="deviceCardClass"
    @click="handleClick"
  >
    <!-- 设备头部信息 -->
    <template #header>
      <div class="device-header">
        <div class="device-info">
          <h3 class="device-name">{{ device.name || '未命名设备' }}</h3>
          <p class="device-id">ID: {{ device.id || 'N/A' }}</p>
        </div>
        <div class="device-badges">
          <n-tag :type="deviceTypeTagType" size="small" class="device-type-tag">
            {{ deviceTypeText }}
          </n-tag>
          <n-tag :type="statusTagType" size="medium" :bordered="false" class="device-status-tag">
            <template #icon>
              <n-icon :component="statusIcon" />
            </template>
            {{ statusText }}
          </n-tag>
        </div>
      </div>
    </template>

    <!-- 设备监控数据 -->
    <div v-if="showMetrics && hasMetrics" class="device-metrics">
      <div class="metrics-grid">
        <div v-for="metric in displayMetrics" :key="metric.key" class="metric-item">
          <div class="metric-icon">
            <TheIcon v-if="typeof metric.icon === 'string'" :icon="metric.icon" :size="16" />
            <n-icon v-else :component="metric.icon" :size="16" />
          </div>
          <div class="metric-content">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value" :class="getMetricValueClass(metric)">
              {{ formatMetricValue(metric) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 自定义内容插槽 -->
    <div v-if="$slots.content" class="device-content">
      <slot name="content" :device="device" />
    </div>

    <!-- 设备位置信息 -->
    <div v-if="showLocation && device.location" class="device-location">
      <n-icon :component="LocationOnOutline" :size="14" />
      <span>{{ device.location }}</span>
    </div>

    <!-- 最后更新时间 -->
    <div v-if="showLastUpdate && device.lastUpdate" class="device-last-update">
      <n-icon :component="TimeOutline" :size="14" />
      <span>{{ formatLastUpdate(device.lastUpdate) }}</span>
    </div>

    <!-- 操作按钮 -->
    <template #footer>
      <div v-if="showActions" class="device-actions">
        <slot name="actions" :device="device">
          <n-button
            v-if="showDetailsButton"
            type="primary"
            size="small"
            secondary
            @click.stop="handleViewDetails"
          >
            <template #icon>
              <n-icon :component="AnalyticsOutline" />
            </template>
            查看详情
          </n-button>

          <n-button
            v-if="showControlButton && canControl"
            :type="device.status === 'active' ? 'warning' : 'success'"
            size="small"
            @click.stop="handleToggleControl"
          >
            <template #icon>
              <n-icon :component="device.status === 'active' ? StopOutline : PlayOutline" />
            </template>
            {{ device.status === 'active' ? '停止' : '启动' }}
          </n-button>
        </slot>
      </div>
    </template>
  </BaseCard>
</template>

<script setup>
import { computed } from 'vue'
import { NTag, NButton, NIcon } from 'naive-ui'
import {
  CheckmarkCircleOutline,
  CloseCircleOutline,
  WarningOutline,
  RemoveCircleOutline,
  LocationOnOutline,
  TimeOutline,
  AnalyticsOutline,
  StopOutline,
  PlayOutline,
  FlashOutline,
  SpeedometerOutline,
  ThermometerOutline,
  BarChartOutline,
} from '@vicons/ionicons5'
import TheIcon from '@/components/icon/TheIcon.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

/**
 * 设备状态卡片组件
 * 用于显示设备的状态、监控数据和基本操作
 *
 * @component DeviceStatusCard
 * @example
 * <DeviceStatusCard
 *   :device="deviceData"
 *   :show-metrics="true"
 *   :clickable="true"
 *   @click="handleDeviceClick"
 *   @view-details="handleViewDetails"
 * />
 */

const props = defineProps({
  // 设备数据
  device: {
    type: Object,
    required: true,
    default: () => ({}),
  },

  // 卡片尺寸
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value),
  },

  // 是否可点击
  clickable: {
    type: Boolean,
    default: true,
  },

  // 是否显示监控指标
  showMetrics: {
    type: Boolean,
    default: true,
  },

  // 是否显示位置信息
  showLocation: {
    type: Boolean,
    default: true,
  },

  // 是否显示最后更新时间
  showLastUpdate: {
    type: Boolean,
    default: true,
  },

  // 是否显示操作按钮
  showActions: {
    type: Boolean,
    default: true,
  },

  // 是否显示详情按钮
  showDetailsButton: {
    type: Boolean,
    default: true,
  },

  // 是否显示控制按钮
  showControlButton: {
    type: Boolean,
    default: false,
  },

  // 监控字段配置
  monitoringFields: {
    type: Array,
    default: () => [],
  },

  // 自定义指标配置
  customMetrics: {
    type: Array,
    default: () => [],
  },

  // 指标显示数量限制
  maxMetrics: {
    type: Number,
    default: 4,
  },
})

const emit = defineEmits(['click', 'view-details', 'toggle-control', 'metric-click'])

// 设备状态映射
const statusConfig = {
  active: {
    text: '运行中',
    type: 'success',
    icon: CheckmarkCircleOutline,
  },
  inactive: {
    text: '离线',
    type: 'default',
    icon: RemoveCircleOutline,
  },
  maintenance: {
    text: '维护中',
    type: 'warning',
    icon: WarningOutline,
  },
  fault: {
    text: '故障',
    type: 'error',
    icon: CloseCircleOutline,
  },
}

// 设备类型映射
const deviceTypeConfig = {
  welding: { text: '焊接设备', type: 'info' },
  cutting: { text: '切割设备', type: 'warning' },
  assembly: { text: '装配设备', type: 'success' },
  inspection: { text: '检测设备', type: 'primary' },
}

// 默认指标配置
const defaultMetrics = [
  {
    key: 'preset_current',
    label: '预设电流',
    icon: FlashOutline,
    unit: 'A',
    format: (value) => Number(value).toFixed(1),
  },
  {
    key: 'preset_voltage',
    label: '预设电压',
    icon: SpeedometerOutline,
    unit: 'V',
    format: (value) => Number(value).toFixed(1),
  },
  {
    key: 'welding_current',
    label: '焊接电流',
    icon: FlashOutline,
    unit: 'A',
    format: (value) => Number(value).toFixed(1),
  },
  {
    key: 'welding_voltage',
    label: '焊接电压',
    icon: SpeedometerOutline,
    unit: 'V',
    format: (value) => Number(value).toFixed(1),
  },
  {
    key: 'temperature',
    label: '温度',
    icon: ThermometerOutline,
    unit: '°C',
    format: (value) => Number(value).toFixed(0),
  },
  {
    key: 'efficiency',
    label: '效率',
    icon: BarChartOutline,
    unit: '%',
    format: (value) => Number(value).toFixed(1),
  },
]

// 计算属性
const deviceCardClass = computed(() => ({
  [`device-status-card--${props.device.status || 'inactive'}`]: true,
  [`device-status-card--${props.size}`]: props.size !== 'medium',
}))

const cardType = computed(() => {
  const status = props.device.status || 'inactive'
  return statusConfig[status]?.type || 'default'
})

const statusText = computed(() => {
  const status = props.device.status || 'inactive'
  return statusConfig[status]?.text || '未知'
})

const statusTagType = computed(() => {
  const status = props.device.status || 'inactive'
  return statusConfig[status]?.type || 'default'
})

const statusIcon = computed(() => {
  const status = props.device.status || 'inactive'
  return statusConfig[status]?.icon || RemoveCircleOutline
})

const deviceTypeText = computed(() => {
  const type = props.device.device_type || props.device.type
  return deviceTypeConfig[type]?.text || '未知类型'
})

const deviceTypeTagType = computed(() => {
  const type = props.device.device_type || props.device.type
  return deviceTypeConfig[type]?.type || 'default'
})

const hasMetrics = computed(() => {
  return displayMetrics.value.length > 0
})

const displayMetrics = computed(() => {
  // 优先使用传入的监控字段配置
  if (props.monitoringFields && props.monitoringFields.length > 0) {
    return props.monitoringFields
      .filter((field) => field.is_default_visible !== false)
      .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
      .slice(0, props.maxMetrics)
      .map((field) => ({
        key: field.field_code,
        label: field.field_name,
        icon: field.display_config?.icon || 'material-symbols:circle',
        unit: field.unit,
        format: (value) => {
          if (value === undefined || value === null || value === '') return '--'
          if (field.field_type === 'float') {
            const num = Number(value)
            return isNaN(num) ? value : num.toFixed(2)
          }
          return value
        },
      }))
  }

  // 降级逻辑：使用默认或自定义指标
  const allMetrics = [...defaultMetrics, ...props.customMetrics]
  const availableMetrics = allMetrics.filter((metric) => {
    const value = props.device[metric.key]
    return value !== undefined && value !== null && value !== ''
  })

  return availableMetrics.slice(0, props.maxMetrics)
})

const canControl = computed(() => {
  // 根据设备状态和权限判断是否可以控制
  const status = props.device.status
  return status === 'active' || status === 'inactive'
})

// 方法
function handleClick(event) {
  emit('click', props.device, event)
}

function handleViewDetails() {
  emit('view-details', props.device)
}

function handleToggleControl() {
  emit('toggle-control', props.device)
}

function formatMetricValue(metric) {
  const value = props.device[metric.key]
  if (value === undefined || value === null) return 'N/A'

  const formattedValue = metric.format ? metric.format(value) : value
  return `${formattedValue}${metric.unit || ''}`
}

function getMetricValueClass(metric) {
  const value = props.device[metric.key]
  if (value === undefined || value === null) return 'metric-value--na'

  // 可以根据阈值添加不同的样式类
  if (metric.threshold) {
    if (value > metric.threshold.high) return 'metric-value--high'
    if (value < metric.threshold.low) return 'metric-value--low'
  }

  return 'metric-value--normal'
}

function formatLastUpdate(timestamp) {
  if (!timestamp) return 'N/A'

  try {
    const date = new Date(timestamp)
    return formatDistanceToNow(date, {
      addSuffix: true,
      locale: zhCN,
    })
  } catch (error) {
    return 'N/A'
  }
}
</script>

<style scoped>
.device-status-card {
  transition: all 0.3s ease;
}

/* 设备头部 */
.device-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 4px 0;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-id {
  font-size: 12px;
  color: var(--text-color-secondary);
  margin: 0;
  line-height: 1.2;
}

.device-badges {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.device-type-tag {
  font-size: 11px;
}

.device-status-tag {
  font-weight: 500;
}

/* 设备指标 */
.device-metrics {
  margin: 16px 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: var(--bg-color-secondary, #f8f9fa);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.metric-item:hover {
  background: var(--bg-color-hover, #e9ecef);
}

.metric-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: var(--primary-color-opacity, rgba(24, 160, 88, 0.1));
  color: var(--primary-color);
}

.metric-content {
  flex: 1;
  min-width: 0;
}

.metric-label {
  display: block;
  font-size: 11px;
  color: var(--text-color-secondary);
  line-height: 1.2;
  margin-bottom: 2px;
}

.metric-value {
  display: block;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
}

.metric-value--normal {
  color: var(--text-color);
}

.metric-value--high {
  color: var(--error-color);
}

.metric-value--low {
  color: var(--warning-color);
}

.metric-value--na {
  color: var(--text-color-disabled);
}

/* 设备内容 */
.device-content {
  margin: 16px 0;
}

/* 设备位置和更新时间 */
.device-location,
.device-last-update {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-color-secondary);
  margin: 8px 0;
}

/* 设备操作 */
.device-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 状态样式 */
.device-status-card--active {
  border-left: 4px solid var(--success-color);
}

.device-status-card--inactive {
  border-left: 4px solid var(--border-color);
}

.device-status-card--maintenance {
  border-left: 4px solid var(--warning-color);
}

.device-status-card--fault {
  border-left: 4px solid var(--error-color);
}

/* 尺寸变体 */
.device-status-card--small .device-name {
  font-size: 14px;
}

.device-status-card--small .device-id {
  font-size: 11px;
}

.device-status-card--small .metrics-grid {
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 8px;
}

.device-status-card--large .device-name {
  font-size: 18px;
}

.device-status-card--large .device-id {
  font-size: 13px;
}

.device-status-card--large .metrics-grid {
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

/* 暗色主题适配 */
.dark .metric-item {
  --bg-color-secondary: #2d2d30;
  --bg-color-hover: #3a3a3e;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .device-header {
    flex-direction: column;
    gap: 8px;
  }

  .device-badges {
    flex-direction: row;
    align-items: flex-start;
  }

  .metrics-grid {
    grid-template-columns: 1fr 1fr;
  }

  .device-actions {
    flex-direction: column;
  }
}
</style>
