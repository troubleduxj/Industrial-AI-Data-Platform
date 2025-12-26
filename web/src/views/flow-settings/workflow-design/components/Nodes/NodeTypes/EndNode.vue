<template>
  <div
    class="end-node"
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
        <span class="icon">🏁</span>
      </div>
      <div class="node-title">
        {{ node.name || '结束节点' }}
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
        <div v-if="node.properties.resultType" class="property-item">
          <span class="property-label">结果类型:</span>
          <span class="property-value">{{ getResultTypeLabel(node.properties.resultType) }}</span>
        </div>

        <div v-if="node.properties.notification" class="property-item">
          <span class="property-label">通知:</span>
          <span class="property-value">{{ node.properties.notification ? '启用' : '禁用' }}</span>
        </div>

        <div v-if="node.properties.cleanup" class="property-item">
          <span class="property-label">清理:</span>
          <span class="property-value">{{ node.properties.cleanup ? '启用' : '禁用' }}</span>
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
  emit('connection-start', {
    node: props.node,
    point: 'input',
    event,
  })
}

function handleConnectionHover(event) {
  emit('connection-hover', {
    node: props.node,
    point: 'input',
    event,
  })
}

function handleConnectionLeave(event) {
  emit('connection-leave', {
    node: props.node,
    point: 'input',
    event,
  })
}

function handleResize(direction) {
  emit('resize', {
    node: props.node,
    direction,
  })
}

function getResultTypeLabel(type) {
  const labels = {
    success: '成功',
    failure: '失败',
    warning: '警告',
    info: '信息',
  }
  return labels[type] || type
}
</script>

<style scoped>
.end-node {
  position: relative;
  min-width: 180px;
  min-height: 80px;
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
  border: 2px solid #ff4d4f;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.15);
}

.end-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(255, 77, 79, 0.25);
}

.end-node.selected {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.end-node.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.end-node.error {
  border-color: #a8071a;
  background: linear-gradient(135deg, #a8071a 0%, #cf1322 100%);
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

.connection-dot {
  width: 12px;
  height: 12px;
  background: white;
  border: 2px solid #ff4d4f;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.connection-point:hover .connection-dot,
.connection-point.active .connection-dot {
  background: #ff4d4f;
  transform: scale(1.2);
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
