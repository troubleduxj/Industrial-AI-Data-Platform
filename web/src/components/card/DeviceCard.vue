<template>
  <NCard
    class="device-card"
    :class="cardClass"
    hoverable
    v-bind="$attrs"
    :theme-overrides="{ common: { transition: 'none' } }"
    @click="handleClick"
  >
    <!-- 设备头部信息 -->
    <div class="device-header">
      <div class="device-info">
        <h3 class="device-name">{{ device.name || '未命名设备' }}</h3>
        <p class="device-id">{{ device.id || 'N/A' }}</p>
      </div>
      <div class="device-type">
        <NTag :type="getDeviceTypeTagType(device.device_type)" size="small">
          {{ getDeviceTypeText(device.device_type) }}
        </NTag>
      </div>
    </div>

    <!-- 设备状态 -->
    <div class="device-status">
      <NTag :type="getStatusTagType(device.status)" size="medium" :bordered="false">
        {{ getStatusText(device.status) }}
      </NTag>
    </div>

    <!-- 设备监控数据 -->
    <div v-if="showMonitoringData" class="monitoring-data">
      <!-- 使用动态组件渲染 -->
      <GroupedMonitoringData
        v-if="monitoringFields && monitoringFields.length > 0"
        :monitoring-fields="monitoringFields"
        :realtime-data="device"
        :loading="false"
      />
      <!-- 降级显示：硬编码数据 (仅当没有字段配置时显示) -->
      <div v-else class="data-row">
        <span class="data-label">⚡ 预设电流:</span>
        <span class="data-value">{{ device.preset_current || '274.0' }} A</span>
        <span class="data-label ml-20">🔌 预设电压:</span>
        <span class="data-value">{{ device.preset_voltage || '26.8' }} V</span>
      </div>
    </div>

    <!-- 自定义内容插槽 -->
    <div v-if="$slots.content" class="device-content">
      <slot name="content" :device="device"></slot>
    </div>

    <!-- 设备位置 -->
    <div v-if="showLocation" class="device-location">
      <TheIcon icon="material-symbols:location-on" :size="14" class="mr-5" />
      {{ device.location || '未设置' }}
    </div>

    <!-- 操作按钮 -->
    <div v-if="showActions" class="device-actions">
      <slot name="actions" :device="device">
        <NButton type="primary" size="small" secondary @click.stop="$emit('view-details', device)">
          <TheIcon icon="material-symbols:analytics" :size="14" class="mr-5" />
          查看详情
        </NButton>
      </slot>
    </div>
  </NCard>
</template>

<script setup>
import { NCard, NTag, NButton } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import GroupedMonitoringData from '@/components/device/GroupedMonitoringData.vue'
import { computed } from 'vue'

/**
 * 设备卡片组件
 * 用于显示设备信息，支持不同状态和类型的设备
 */
const props = defineProps({
  // 设备数据
  device: {
    type: Object,
    required: true,
    default: () => ({}),
  },
  // 监控字段配置
  monitoringFields: {
    type: Array,
    default: () => [],
  },
  // 是否显示监控数据
  showMonitoringData: {
    type: Boolean,
    default: true,
  },
  // 是否显示位置信息
  showLocation: {
    type: Boolean,
    default: true,
  },
  // 是否显示操作按钮
  showActions: {
    type: Boolean,
    default: true,
  },
  // 卡片尺寸
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value),
  },
})

const emit = defineEmits(['click', 'view-details'])

// 卡片样式类
const cardClass = computed(() => {
  const status = props.device.status || 'inactive'
  return {
    [`device-card--${status}`]: true,
    [`device-card--${props.size}`]: props.size !== 'medium',
  }
})

/**
 * 获取设备状态文本
 */
function getStatusText(status) {
  const statusMap = {
    active: '运行中',
    online: '运行中',
    inactive: '离线',
    offline: '离线',
    maintenance: '维护中',
    fault: '故障',
    error: '故障',
  }
  return statusMap[status] || '未知'
}

/**
 * 获取设备状态标签类型
 */
function getStatusTagType(status) {
  const typeMap = {
    active: 'success',
    online: 'success',
    inactive: 'default',
    offline: 'default',
    maintenance: 'warning',
    fault: 'error',
    error: 'error',
  }
  return typeMap[status] || 'default'
}

/**
 * 获取设备类型文本
 */
function getDeviceTypeText(deviceType) {
  const typeMap = {
    welding: '焊接设备',
    cutting: '切割设备',
    assembly: '装配设备',
    inspection: '检测设备',
  }
  return typeMap[deviceType] || '未知类型'
}

/**
 * 获取设备类型标签类型
 */
function getDeviceTypeTagType(deviceType) {
  const typeMap = {
    welding: 'info',
    cutting: 'warning',
    assembly: 'success',
    inspection: 'primary',
  }
  return typeMap[deviceType] || 'default'
}

/**
 * 处理卡片点击事件
 */
function handleClick(event) {
  emit('click', props.device, event)
}
</script>

<style scoped>
.device-card {
  position: relative;
  cursor: pointer;
  transition: none !important;
  border-left: 4px solid var(--n-border-color);
  background: var(--n-color);
  animation: none !important;
  will-change: auto;
  transform: translateZ(0);
  backface-visibility: hidden;
  perspective: 1000px;
}

.device-card:hover {
  box-shadow: 0 2px 8px var(--n-box-shadow-color);
}

/* 状态边框颜色 */
.device-card--active {
  border-left-color: var(--n-success-color);
}

.device-card--inactive {
  border-left-color: var(--n-border-color);
}

.device-card--maintenance {
  border-left-color: var(--n-warning-color);
}

.device-card--fault {
  border-left-color: var(--n-error-color);
}

.device-card--online {
  border-left-color: var(--n-success-color);
}

.device-card--offline {
  border-left-color: var(--n-border-color);
}

.device-card--error {
  border-left-color: var(--n-error-color);
}

/* 设备头部 */
.device-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  padding-right: 24px;
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin: 0 0 4px 0;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-id {
  font-size: 12px;
  color: var(--n-secondary-text-color);
  margin: 0;
  line-height: 1.2;
}

.device-type {
  flex-shrink: 0;
  margin-left: 12px;
}

/* 设备状态 */
.device-status {
  margin-bottom: 16px;
}

/* 监控数据 */
.monitoring-data {
  margin-bottom: 16px;
}

.data-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  line-height: 1.2;
}

.data-row:last-child {
  margin-bottom: 0;
}

.data-label {
  color: var(--n-secondary-text-color);
  margin-right: 4px;
}

.data-value {
  color: var(--n-text-color);
  font-weight: 500;
  margin-right: 16px;
}

/* 自定义内容 */
.device-content {
  margin-bottom: 16px;
}

/* 设备位置 */
.device-location {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--n-secondary-text-color);
  margin-bottom: 16px;
}

/* 操作按钮 */
.device-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 尺寸变体 */
.device-card--small {
  font-size: 12px;
}

.device-card--small .device-name {
  font-size: 14px;
}

.device-card--small .device-id {
  font-size: 11px;
}

.device-card--large {
  font-size: 14px;
}

.device-card--large .device-name {
  font-size: 18px;
}

.device-card--large .device-id {
  font-size: 13px;
}
</style>
