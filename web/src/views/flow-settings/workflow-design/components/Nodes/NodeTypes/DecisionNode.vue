<template>
  <div
    class="decision-node"
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
        <span class="icon">🔀</span>
      </div>
      <div class="node-title">
        {{ node.name || '判断节点' }}
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
        <div v-if="node.properties.conditionType" class="property-item">
          <span class="property-label">条件类型:</span>
          <span class="property-value">{{
            getConditionTypeLabel(node.properties.conditionType)
          }}</span>
        </div>

        <div v-if="node.properties.operator" class="property-item">
          <span class="property-label">操作符:</span>
          <span class="property-value">{{ getOperatorLabel(node.properties.operator) }}</span>
        </div>

        <div v-if="node.properties.value" class="property-item">
          <span class="property-label">比较值:</span>
          <span class="property-value">{{ node.properties.value }}</span>
        </div>

        <div v-if="node.properties.caseSensitive !== undefined" class="property-item">
          <span class="property-label">大小写:</span>
          <span class="property-value">{{
            node.properties.caseSensitive ? '敏感' : '不敏感'
          }}</span>
        </div>
      </div>

      <!-- Condition expression -->
      <div v-if="node.properties.expression" class="condition-expression">
        <div class="expression-label">条件表达式:</div>
        <div class="expression-code">{{ node.properties.expression }}</div>
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

      <!-- True output -->
      <div
        class="connection-point output true"
        :class="{ active: isConnecting }"
        @mousedown.stop="handleConnectionStart"
        @mouseenter="handleConnectionHover"
        @mouseleave="handleConnectionLeave"
      >
        <div class="connection-dot"></div>
        <div class="connection-label">True</div>
      </div>

      <!-- False output -->
      <div
        class="connection-point output false"
        :class="{ active: isConnecting }"
        @mousedown.stop="handleConnectionStart"
        @mouseenter="handleConnectionHover"
        @mouseleave="handleConnectionLeave"
      >
        <div class="connection-dot"></div>
        <div class="connection-label">False</div>
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
  const point = event.target.closest('.connection-point')
  const pointType = point.classList.contains('input') ? 'input' : 'output'
  const pointSubType = point.classList.contains('true')
    ? 'true'
    : point.classList.contains('false')
    ? 'false'
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
  const pointSubType = point.classList.contains('true')
    ? 'true'
    : point.classList.contains('false')
    ? 'false'
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
  const pointSubType = point.classList.contains('true')
    ? 'true'
    : point.classList.contains('false')
    ? 'false'
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

function getConditionTypeLabel(type) {
  const labels = {
    value: '值比较',
    expression: '表达式',
    regex: '正则表达式',
    range: '范围判断',
    exists: '存在性检查',
    type: '类型检查',
  }
  return labels[type] || type
}

function getOperatorLabel(operator) {
  const labels = {
    '==': '等于',
    '!=': '不等于',
    '>': '大于',
    '>=': '大于等于',
    '<': '小于',
    '<=': '小于等于',
    contains: '包含',
    startsWith: '开始于',
    endsWith: '结束于',
    matches: '匹配',
    in: '在范围内',
    notIn: '不在范围内',
  }
  return labels[operator] || operator
}
</script>

<style scoped>
.decision-node {
  position: relative;
  min-width: 180px;
  min-height: 120px;
  background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);
  border: 2px solid #faad14;
  border-radius: 50% 8px 50% 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(250, 173, 20, 0.15);
}

.decision-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(250, 173, 20, 0.25);
}

.decision-node.selected {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.decision-node.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.decision-node.error {
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

.condition-expression {
  margin-top: 8px;
}

.expression-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 4px;
  font-weight: 500;
}

.expression-code {
  font-size: 11px;
  color: white;
  background: rgba(0, 0, 0, 0.2);
  padding: 6px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  word-break: break-all;
  line-height: 1.3;
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

.connection-point.output.true {
  right: -12px;
  top: 30%;
  transform: translateY(-50%);
  flex-direction: row;
}

.connection-point.output.false {
  right: -12px;
  top: 70%;
  transform: translateY(-50%);
  flex-direction: row;
}

.connection-dot {
  width: 12px;
  height: 12px;
  background: white;
  border: 2px solid #faad14;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.connection-point.output.true .connection-dot {
  border-color: #52c41a;
}

.connection-point.output.false .connection-dot {
  border-color: #ff4d4f;
}

.connection-point:hover .connection-dot,
.connection-point.active .connection-dot {
  transform: scale(1.2);
}

.connection-point.input:hover .connection-dot,
.connection-point.input.active .connection-dot {
  background: #faad14;
}

.connection-point.output.true:hover .connection-dot,
.connection-point.output.true.active .connection-dot {
  background: #52c41a;
}

.connection-point.output.false:hover .connection-dot,
.connection-point.output.false.active .connection-dot {
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
