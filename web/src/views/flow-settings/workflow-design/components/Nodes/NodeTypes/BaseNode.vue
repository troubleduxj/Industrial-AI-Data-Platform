<template>
  <div
    class="base-node"
    :class="nodeClasses"
    :style="nodeStyles"
    @click="handleClick"
    @dblclick="handleDoubleClick"
    @contextmenu="handleContextMenu"
    @mousedown="handleMouseDown"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- 节点头部 -->
    <div class="node-header" :style="headerStyles">
      <div class="node-icon">
        <component :is="iconComponent" v-if="iconComponent" />
        <span v-else class="icon-text">{{ iconText }}</span>
      </div>
      <div class="node-title" :title="node.name">{{ node.name }}</div>
      <div v-if="showStatus" class="node-status" :class="node.status"></div>
    </div>

    <!-- 节点内容 -->
    <div class="node-content">
      <div v-if="node.description" class="node-description">
        {{ node.description }}
      </div>

      <!-- 自定义内容插槽 -->
      <slot name="content" :node="node">
        <div v-if="hasProperties" class="node-properties">
          <div v-for="(value, key) in displayProperties" :key="key" class="property-item">
            <span class="property-label">{{ formatPropertyLabel(key) }}:</span>
            <span class="property-value">{{ formatPropertyValue(value) }}</span>
          </div>
        </div>
      </slot>
    </div>

    <!-- 输入连接点 -->
    <div
      v-for="connector in inputConnectors"
      :key="connector.id"
      class="input node-connector"
      :class="{
        active: isConnectorActive(connector.id),
        magnetic: isConnectorMagnetic(connector.id),
        highlighted: isConnectorHighlighted(connector.id),
      }"
      :style="getConnectorStyle(connector, 'input')"
      :title="connector.label || '输入连接点'"
      @mousedown="handleConnectorMouseDown(connector, 'input', $event)"
      @mouseenter="handleConnectorMouseEnter(connector, 'input', $event)"
      @mouseleave="handleConnectorMouseLeave(connector, 'input', $event)"
    >
      <div class="connector-dot"></div>
      <div v-if="connector.label" class="connector-label">{{ connector.label }}</div>
    </div>

    <!-- 输出连接点 -->
    <div
      v-for="connector in outputConnectors"
      :key="connector.id"
      class="node-connector output"
      :class="{
        active: isConnectorActive(connector.id),
        magnetic: isConnectorMagnetic(connector.id),
        highlighted: isConnectorHighlighted(connector.id),
      }"
      :style="getConnectorStyle(connector, 'output')"
      :title="connector.label || '输出连接点'"
      @mousedown="handleConnectorMouseDown(connector, 'output', $event)"
      @mouseenter="handleConnectorMouseEnter(connector, 'output', $event)"
      @mouseleave="handleConnectorMouseLeave(connector, 'output', $event)"
    >
      <div class="connector-dot"></div>
      <div v-if="connector.label" class="connector-label">{{ connector.label }}</div>
    </div>

    <!-- 节点操作按钮 -->
    <div v-if="showActions" class="node-actions">
      <button v-if="editable" class="action-btn edit" title="编辑节点" @click="handleEdit">
        ✏️
      </button>
      <button v-if="copyable" class="action-btn copy" title="复制节点" @click="handleCopy">
        📋
      </button>
      <button v-if="deletable" class="action-btn delete" title="删除节点" @click="handleDelete">
        🗑️
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="hasError" class="node-error-tooltip">
      {{ errorMessage }}
    </div>

    <!-- 选择指示器 -->
    <div v-if="isSelected" class="selection-indicator"></div>

    <!-- 拖拽预览 -->
    <div v-if="isDragging" class="drag-preview"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import { getNodeTypeConfig } from './index'

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
  isHighlighted: {
    type: Boolean,
    default: false,
  },
  isDragging: {
    type: Boolean,
    default: false,
  },
  showStatus: {
    type: Boolean,
    default: true,
  },
  showActions: {
    type: Boolean,
    default: true,
  },
  editable: {
    type: Boolean,
    default: true,
  },
  copyable: {
    type: Boolean,
    default: true,
  },
  deletable: {
    type: Boolean,
    default: true,
  },
  activeConnectors: {
    type: Array,
    default: () => [],
  },
  magneticConnectors: {
    type: Array,
    default: () => [],
  },
  highlightedConnectors: {
    type: Array,
    default: () => [],
  },
})

// Emits
const emit = defineEmits([
  'click',
  'dblclick',
  'contextmenu',
  'mousedown',
  'mouseenter',
  'mouseleave',
  'edit',
  'copy',
  'delete',
  'connector-mousedown',
  'connector-mouseenter',
  'connector-mouseleave',
])

// 注入的依赖
const workflowConfig = inject('workflowConfig', {})

// 计算属性
const nodeTypeConfig = computed(() => {
  return getNodeTypeConfig(props.node.type)
})

const nodeClasses = computed(() => {
  return {
    'base-node': true,
    [`node-type-${props.node.type}`]: true,
    selected: props.isSelected,
    highlighted: props.isHighlighted,
    dragging: props.isDragging,
    error: hasError.value,
    disabled: props.node.status === 'disabled',
    running: props.node.status === 'running',
  }
})

const nodeStyles = computed(() => {
  const styles = {
    width: props.node.width ? `${props.node.width}px` : undefined,
    height: props.node.height ? `${props.node.height}px` : undefined,
  }

  // 应用主题颜色
  if (nodeTypeConfig.value?.color) {
    styles['--node-theme-color'] = nodeTypeConfig.value.color
  }

  return styles
})

const headerStyles = computed(() => {
  const styles = {}

  if (nodeTypeConfig.value?.color) {
    styles.borderLeftColor = nodeTypeConfig.value.color
    styles.borderLeftWidth = '4px'
    styles.borderLeftStyle = 'solid'
  }

  return styles
})

const iconComponent = computed(() => {
  return nodeTypeConfig.value?.iconComponent
})

const iconText = computed(() => {
  return nodeTypeConfig.value?.icon || props.node.type.charAt(0).toUpperCase()
})

const inputConnectors = computed(() => {
  return props.node.connectors?.input || []
})

const outputConnectors = computed(() => {
  return props.node.connectors?.output || []
})

const hasProperties = computed(() => {
  return Object.keys(displayProperties.value).length > 0
})

const displayProperties = computed(() => {
  const properties = props.node.properties || {}
  const config = nodeTypeConfig.value

  if (!config?.displayProperties) {
    return properties
  }

  const result = {}
  config.displayProperties.forEach((key) => {
    if (properties[key] !== undefined) {
      result[key] = properties[key]
    }
  })

  return result
})

const hasError = computed(() => {
  return props.node.status === 'error' || !!errorMessage.value
})

const errorMessage = computed(() => {
  // 检查节点配置错误
  const config = nodeTypeConfig.value
  if (config?.validation) {
    const errors = validateNodeProperties(props.node.properties, config.validation)
    if (errors.length > 0) {
      return errors[0].message
    }
  }

  // 检查连接错误
  if (inputConnectors.value.length === 0 && props.node.type !== 'start') {
    return '缺少输入连接'
  }

  if (outputConnectors.value.length === 0 && props.node.type !== 'end') {
    return '缺少输出连接'
  }

  return null
})

// 方法
function isConnectorActive(connectorId) {
  return props.activeConnectors.includes(connectorId)
}

function isConnectorMagnetic(connectorId) {
  return props.magneticConnectors.includes(connectorId)
}

function isConnectorHighlighted(connectorId) {
  return props.highlightedConnectors.includes(connectorId)
}

function getConnectorStyle(connector, type) {
  const styles = {
    left: type === 'input' ? `${connector.position.x}px` : undefined,
    right: type === 'output' ? `${connector.position.x}px` : undefined,
    top: `${connector.position.y}px`,
  }

  return styles
}

function formatPropertyLabel(key) {
  // 将驼峰命名转换为可读标签
  return key.replace(/([A-Z])/g, ' $1').replace(/^./, (str) => str.toUpperCase())
}

function formatPropertyValue(value) {
  if (typeof value === 'boolean') {
    return value ? '是' : '否'
  }

  if (typeof value === 'object') {
    return JSON.stringify(value)
  }

  if (typeof value === 'string' && value.length > 20) {
    return value.substring(0, 20) + '...'
  }

  return String(value)
}

function validateNodeProperties(properties, validation) {
  const errors = []

  if (validation.required) {
    validation.required.forEach((field) => {
      if (!properties[field]) {
        errors.push({
          field,
          message: `${formatPropertyLabel(field)} 是必填项`,
        })
      }
    })
  }

  if (validation.rules) {
    validation.rules.forEach((rule) => {
      const value = properties[rule.field]
      let isValid = true

      switch (rule.type) {
        case 'required':
          isValid = !!value
          break
        case 'pattern':
          isValid = !value || new RegExp(rule.value).test(value)
          break
        case 'range':
          if (typeof value === 'number') {
            isValid = value >= rule.value.min && value <= rule.value.max
          }
          break
        case 'custom':
          if (rule.validator) {
            isValid = rule.validator(value, props.node)
          }
          break
      }

      if (!isValid) {
        errors.push({
          field: rule.field,
          message: rule.message,
        })
      }
    })
  }

  return errors
}

// 事件处理
function handleClick(event) {
  emit('click', {
    node: props.node,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleDoubleClick(event) {
  emit('dblclick', {
    node: props.node,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleContextMenu(event) {
  event.preventDefault()
  emit('contextmenu', {
    node: props.node,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleMouseDown(event) {
  emit('mousedown', {
    node: props.node,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleMouseEnter(event) {
  emit('mouseenter', {
    node: props.node,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleMouseLeave(event) {
  emit('mouseleave', {
    node: props.node,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleEdit(event) {
  event.stopPropagation()
  emit('edit', {
    node: props.node,
    originalEvent: event,
  })
}

function handleCopy(event) {
  event.stopPropagation()
  emit('copy', {
    node: props.node,
    originalEvent: event,
  })
}

function handleDelete(event) {
  event.stopPropagation()
  emit('delete', {
    node: props.node,
    originalEvent: event,
  })
}

function handleConnectorMouseDown(connector, type, event) {
  event.stopPropagation()
  emit('connector-mousedown', {
    node: props.node,
    connector,
    type,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleConnectorMouseEnter(connector, type, event) {
  emit('connector-mouseenter', {
    node: props.node,
    connector,
    type,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleConnectorMouseLeave(connector, type, event) {
  emit('connector-mouseleave', {
    node: props.node,
    connector,
    type,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}
</script>

<style scoped>
.base-node {
  min-width: var(--node-min-width, 120px);
  min-height: var(--node-min-height, 60px);
  background: var(--node-bg, #ffffff);
  border: 2px solid var(--node-border, #d9d9d9);
  border-radius: var(--node-border-radius, 6px);
  box-shadow: 0 2px 8px var(--node-shadow, rgba(0, 0, 0, 0.1));
  cursor: pointer;
  transition: all var(--transition-fast, 0.15s ease);
  position: relative;
  display: flex;
  flex-direction: column;
  user-select: none;
}

.base-node:hover {
  box-shadow: 0 4px 16px var(--node-hover-shadow, rgba(0, 0, 0, 0.15));
  transform: translateY(-1px);
}

.base-node.selected {
  border-color: var(--node-selected-border, #1890ff);
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.base-node.highlighted {
  border-color: var(--workflow-warning, #faad14);
  box-shadow: 0 0 0 2px rgba(250, 173, 20, 0.3);
}

.base-node.dragging {
  opacity: 0.8;
  transform: rotate(2deg);
  z-index: 1000;
}

.base-node.error {
  border-color: var(--node-error-border, #ff4d4f);
}

.base-node.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.base-node.disabled:hover {
  transform: none;
}

.node-header {
  padding: 8px 12px;
  border-bottom: 1px solid var(--node-border, #d9d9d9);
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--node-border-radius, 6px) var(--node-border-radius, 6px) 0 0;
}

.node-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--node-theme-color, #1890ff);
}

.icon-text {
  font-weight: bold;
  font-size: 12px;
}

.node-title {
  font-weight: 500;
  font-size: 14px;
  color: #262626;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.node-status.success {
  background: var(--workflow-success, #52c41a);
}

.node-status.error {
  background: var(--workflow-error, #ff4d4f);
}

.node-status.warning {
  background: var(--workflow-warning, #faad14);
}

.node-status.running {
  background: var(--workflow-primary, #1890ff);
  animation: pulse 1s infinite;
}

.node-content {
  padding: 12px;
  flex: 1;
}

.node-description {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.4;
  margin-bottom: 8px;
}

.node-properties {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.property-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.property-label {
  color: #595959;
}

.property-value {
  color: #262626;
  font-weight: 500;
}

.node-connector {
  position: absolute;
  width: 12px;
  height: 12px;
  cursor: crosshair;
  z-index: 10;
}

.node-connector.input {
  left: -6px;
  transform: translateY(-50%);
}

.node-connector.output {
  right: -6px;
  transform: translateY(-50%);
}

.connector-dot {
  width: 100%;
  height: 100%;
  border: 2px solid var(--workflow-primary, #1890ff);
  background: var(--node-bg, #ffffff);
  border-radius: 50%;
  transition: all var(--transition-fast, 0.15s ease);
}

.node-connector:hover .connector-dot {
  transform: scale(1.2);
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.3);
}

.node-connector.active .connector-dot {
  background: var(--workflow-primary, #1890ff);
  transform: scale(1.3);
}

.node-connector.magnetic .connector-dot {
  background: var(--workflow-warning, #faad14);
  border-color: var(--workflow-warning, #faad14);
  animation: pulse 0.6s ease-in-out infinite;
}

.connector-label {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #8c8c8c;
  white-space: nowrap;
  margin-top: 2px;
}

.node-actions {
  position: absolute;
  top: -8px;
  right: -8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity var(--transition-fast, 0.15s ease);
}

.base-node:hover .node-actions {
  opacity: 1;
}

.action-btn {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all var(--transition-fast, 0.15s ease);
}

.action-btn.edit {
  background: var(--workflow-primary, #1890ff);
  color: white;
}

.action-btn.edit:hover {
  background: #40a9ff;
}

.action-btn.copy {
  background: var(--workflow-success, #52c41a);
  color: white;
}

.action-btn.copy:hover {
  background: #73d13d;
}

.action-btn.delete {
  background: var(--workflow-error, #ff4d4f);
  color: white;
}

.action-btn.delete:hover {
  background: #ff7875;
}

.node-error-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--workflow-error, #ff4d4f);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 1001;
}

.node-error-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: var(--workflow-error, #ff4d4f);
}

.selection-indicator {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border: 2px solid var(--workflow-primary, #1890ff);
  border-radius: var(--node-border-radius, 6px);
  pointer-events: none;
  animation: selection-pulse 1s ease-in-out infinite;
}

.drag-preview {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(24, 144, 255, 0.1);
  border: 2px dashed var(--workflow-primary, #1890ff);
  border-radius: var(--node-border-radius, 6px);
  pointer-events: none;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

@keyframes selection-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
