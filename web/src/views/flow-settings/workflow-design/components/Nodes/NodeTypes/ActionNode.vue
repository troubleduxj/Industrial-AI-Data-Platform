<template>
  <div
    class="action-node"
    :class="{
      selected: isSelected,
      disabled: node.disabled,
      error: hasError,
    }"
    @click="handleClick"
    @mousedown="handleMouseDown"
    @contextmenu="handleContextMenu"
  >
    <div class="node-header">
      <div class="node-icon">
        <span class="icon">⚡</span>
      </div>
      <div class="node-title">
        {{ node.name || '动作节点' }}
      </div>
      <div v-if="node.status" class="node-status">
        <span class="status-indicator" :class="node.status"></span>
      </div>
    </div>

    <div class="node-content">
      <div v-if="node.description" class="node-description">
        {{ node.description }}
      </div>

      <div v-if="hasProperties" class="node-properties">
        <div v-if="node.properties.actionType" class="property-item">
          <span class="property-label">动作类型:</span>
          <span class="property-value">{{ getActionTypeLabel(node.properties.actionType) }}</span>
        </div>

        <div v-if="node.properties.target" class="property-item">
          <span class="property-label">目标:</span>
          <span class="property-value">{{ node.properties.target }}</span>
        </div>

        <div v-if="node.properties.method" class="property-item">
          <span class="property-label">方法:</span>
          <span class="property-value">{{ node.properties.method }}</span>
        </div>

        <div v-if="node.properties.async !== undefined" class="property-item">
          <span class="property-label">异步:</span>
          <span class="property-value">{{ node.properties.async ? '是' : '否' }}</span>
        </div>

        <div v-if="node.properties.timeout" class="property-item">
          <span class="property-label">超时:</span>
          <span class="property-value">{{ node.properties.timeout }}s</span>
        </div>
      </div>

      <!-- Action parameters -->
      <div v-if="node.properties.parameters" class="action-parameters">
        <div class="parameters-label">参数:</div>
        <div class="parameters-list">
          <div v-for="(value, key) in node.properties.parameters" :key="key" class="parameter-item">
            <span class="param-key">{{ key }}:</span>
            <span class="param-value">{{ formatParameterValue(value) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Connection Points -->
    <div class="connection-points">
      <!-- Input point -->
      <div
        class="connection-point input"
        :class="{ active: isConnecting }"
        @mousedown.stop="handleConnectionStart"
        @mouseenter="handleConnectionHover"
        @mouseleave="handleConnectionLeave"
      >
        <div class="connection-dot"></div>
        <div class="connection-label">输入</div>
      </div>

      <!-- Output points -->
      <div
        class="connection-point success output"
        :class="{ active: isConnecting }"
        @mousedown.stop="handleConnectionStart"
        @mouseenter="handleConnectionHover"
        @mouseleave="handleConnectionLeave"
      >
        <div class="connection-dot"></div>
        <div class="connection-label">成功</div>
      </div>

      <div
        class="connection-point output error"
        :class="{ active: isConnecting }"
        @mousedown.stop="handleConnectionStart"
        @mouseenter="handleConnectionHover"
        @mouseleave="handleConnectionLeave"
      >
        <div class="connection-dot"></div>
        <div class="connection-label">失败</div>
      </div>
    </div>

    <!-- Execution indicator -->
    <div v-if="node.status === 'running'" class="execution-indicator">
      <div class="spinner"></div>
    </div>

    <!-- Resize handles -->
    <div v-if="isSelected" class="resize-handles">
      <div class="resize-handle nw" @mousedown.stop="handleResize('nw')"></div>
      <div class="resize-handle ne" @mousedown.stop="handleResize('ne')"></div>
      <div class="resize-handle sw" @mousedown.stop="handleResize('sw')"></div>
      <div class="resize-handle se" @mousedown.stop="handleResize('se')"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Props
const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
  isSelected: {
    type: Boolean,
    default: false,
  },
  isConnecting: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits([
  'click',
  'mousedown',
  'contextmenu',
  'connection-start',
  'connection-hover',
  'connection-leave',
  'resize',
])

// Computed properties
const hasError = computed(() => {
  return props.node.status === 'error' || props.node.validationErrors?.length > 0
})

const hasProperties = computed(() => {
  return props.node.properties && Object.keys(props.node.properties).length > 0
})

// Methods
function handleClick(event) {
  emit('click', {
    node: props.node,
    event,
  })
}

function handleMouseDown(event) {
  emit('mousedown', {
    node: props.node,
    event,
  })
}

function handleContextMenu(event) {
  event.preventDefault()
  emit('contextmenu', {
    node: props.node,
    event,
  })
}

function handleConnectionStart(event) {
  const point = event.target.closest('.connection-point')
  const pointType = point.classList.contains('input') ? 'input' : 'output'
  const pointSubType = point.classList.contains('success')
    ? 'success'
    : point.classList.contains('error')
    ? 'error'
    : 'default'

  emit('connection-start', {
    node: props.node,
    point: pointType,
    subType: pointSubType,
    event,
  })
}

function handleConnectionHover(event) {
  const point = event.target.closest('.connection-point')
  const pointType = point.classList.contains('input') ? 'input' : 'output'
  const pointSubType = point.classList.contains('success')
    ? 'success'
    : point.classList.contains('error')
    ? 'error'
    : 'default'

  emit('connection-hover', {
    node: props.node,
    point: pointType,
    subType: pointSubType,
    event,
  })
}

function handleConnectionLeave(event) {
  const point = event.target.closest('.connection-point')
  const pointType = point.classList.contains('input') ? 'input' : 'output'
  const pointSubType = point.classList.contains('success')
    ? 'success'
    : point.classList.contains('error')
    ? 'error'
    : 'default'

  emit('connection-leave', {
    node: props.node,
    point: pointType,
    subType: pointSubType,
    event,
  })
}

function handleResize(direction) {
  emit('resize', {
    node: props.node,
    direction,
  })
}

function getActionTypeLabel(type) {
  const labels = {
    http: 'HTTP请求',
    database: '数据库操作',
    file: '文件操作',
    email: '发送邮件',
    notification: '发送通知',
    script: '执行脚本',
    webhook: '调用Webhook',
    api: 'API调用',
    transform: '数据转换',
    custom: '自定义动作',
  }
  return labels[type] || type
}

function formatParameterValue(value) {
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  if (typeof value === 'string' && value.length > 20) {
    return value.substring(0, 20) + '...'
  }
  return String(value)
}
</script>

<style scoped>
.action-node {
  position: relative;
  min-width: 200px;
  min-height: 100px;
  background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
  border: 2px solid #722ed1;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(114, 46, 209, 0.15);
}

.action-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(114, 46, 209, 0.25);
}

.action-node.selected {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.action-node.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-node.error {
  border-color: #ff4d4f;
  background: linear-gradient(135deg, #ff7875 0%, #ff9c6e 100%);
}

.node-header {
  display: flex;
  align-items: center;
  padding: 12px 16px 8px;
  gap: 8px;
}

.node-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
}

.node-icon .icon {
  font-size: 16px;
}

.node-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.node-status {
  display: flex;
  align-items: center;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #52c41a;
}

.status-indicator.running {
  background: #1890ff;
  animation: pulse 2s infinite;
}

.status-indicator.error {
  background: #ff4d4f;
}

.status-indicator.warning {
  background: #faad14;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.node-content {
  padding: 0 16px 12px;
}

.node-description {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 8px;
  line-height: 1.4;
}

.node-properties {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.property-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
}

.property-label {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.property-value {
  color: white;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.action-parameters {
  margin-top: 8px;
}

.parameters-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 4px;
  font-weight: 500;
}

.parameters-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.parameter-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
}

.param-key {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  min-width: 40px;
}

.param-value {
  color: white;
  background: rgba(0, 0, 0, 0.2);
  padding: 1px 4px;
  border-radius: 2px;
  font-family: 'Courier New', monospace;
  word-break: break-all;
}

.connection-points {
  position: absolute;
}

.connection-point {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: crosshair;
}

.connection-point.input {
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  flex-direction: row-reverse;
}

.connection-point.output.success {
  right: -12px;
  top: 35%;
  transform: translateY(-50%);
  flex-direction: row;
}

.connection-point.output.error {
  right: -12px;
  top: 65%;
  transform: translateY(-50%);
  flex-direction: row;
}

.connection-dot {
  width: 12px;
  height: 12px;
  background: white;
  border: 2px solid #722ed1;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.connection-point.output.success .connection-dot {
  border-color: #52c41a;
}

.connection-point.output.error .connection-dot {
  border-color: #ff4d4f;
}

.connection-point:hover .connection-dot,
.connection-point.active .connection-dot {
  transform: scale(1.2);
}

.connection-point.input:hover .connection-dot,
.connection-point.input.active .connection-dot {
  background: #722ed1;
}

.connection-point.output.success:hover .connection-dot,
.connection-point.output.success.active .connection-dot {
  background: #52c41a;
}

.connection-point.output.error:hover .connection-dot,
.connection-point.output.error.active .connection-dot {
  background: #ff4d4f;
}

.connection-label {
  font-size: 10px;
  color: #595959;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.connection-point:hover .connection-label {
  opacity: 1;
}

.execution-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 16px;
  height: 16px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.resize-handles {
  position: absolute;
  inset: -4px;
  pointer-events: none;
}

.resize-handle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #1890ff;
  border: 1px solid white;
  border-radius: 2px;
  pointer-events: all;
  cursor: nw-resize;
}

.resize-handle.nw {
  top: 0;
  left: 0;
  cursor: nw-resize;
}

.resize-handle.ne {
  top: 0;
  right: 0;
  cursor: ne-resize;
}

.resize-handle.sw {
  bottom: 0;
  left: 0;
  cursor: sw-resize;
}

.resize-handle.se {
  bottom: 0;
  right: 0;
  cursor: se-resize;
}
</style>
