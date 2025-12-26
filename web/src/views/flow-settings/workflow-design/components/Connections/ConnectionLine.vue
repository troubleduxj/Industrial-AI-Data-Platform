<template>
  <g class="connection-line" :class="connectionClasses">
    <!-- 连接线路径 -->
    <path
      :d="connectionPath"
      class="connection"
      :class="{
        selected: isSelected,
        highlighted: isHighlighted,
        error: hasError,
      }"
      @click="handleClick"
      @dblclick="handleDoubleClick"
      @contextmenu="handleContextMenu"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    />

    <!-- 箭头标记 -->
    <defs v-if="showArrow">
      <marker
        :id="`arrow-${connection.id}`"
        viewBox="0 0 10 10"
        refX="9"
        refY="3"
        markerWidth="6"
        markerHeight="6"
        orient="auto"
        class="connection-arrow"
      >
        <path d="M0,0 L0,6 L9,3 z" :fill="arrowColor" />
      </marker>
    </defs>

    <!-- 连接线标签 -->
    <g v-if="connection.label" class="connection-label">
      <text
        :x="labelPosition.x"
        :y="labelPosition.y"
        text-anchor="middle"
        dominant-baseline="middle"
        class="label-text"
      >
        {{ connection.label }}
      </text>
      <rect
        :x="labelPosition.x - labelSize.width / 2"
        :y="labelPosition.y - labelSize.height / 2"
        :width="labelSize.width"
        :height="labelSize.height"
        class="label-background"
        rx="4"
      />
    </g>

    <!-- 条件标签 -->
    <g v-if="connection.condition" class="condition-label">
      <circle
        :cx="conditionPosition.x"
        :cy="conditionPosition.y"
        r="8"
        class="condition-background"
      />
      <text
        :x="conditionPosition.x"
        :y="conditionPosition.y"
        text-anchor="middle"
        dominant-baseline="middle"
        class="condition-text"
        font-size="10"
      >
        ?
      </text>
    </g>

    <!-- 删除按钮 -->
    <g v-if="showDeleteButton" class="delete-button" @click="handleDelete">
      <circle
        :cx="deleteButtonPosition.x"
        :cy="deleteButtonPosition.y"
        r="8"
        class="delete-background"
      />
      <text
        :x="deleteButtonPosition.x"
        :y="deleteButtonPosition.y"
        text-anchor="middle"
        dominant-baseline="middle"
        class="delete-icon"
        font-size="10"
      >
        ×
      </text>
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { calculateBezierPath, getConnectionMidpoint } from '../../utils/pathCalculator'

// Props
const props = defineProps({
  connection: {
    type: Object,
    required: true,
  },
  fromNode: {
    type: Object,
    required: true,
  },
  toNode: {
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
  showArrow: {
    type: Boolean,
    default: true,
  },
  showLabels: {
    type: Boolean,
    default: true,
  },
  editable: {
    type: Boolean,
    default: true,
  },
})

// Emits
const emit = defineEmits(['click', 'dblclick', 'contextmenu', 'delete', 'hover', 'unhover'])

// 响应式状态
const isHovered = ref(false)

// 计算属性
const connectionClasses = computed(() => {
  return {
    'connection-line': true,
    selected: props.isSelected,
    highlighted: props.isHighlighted,
    hovered: isHovered.value,
    error: hasError.value,
    editable: props.editable,
  }
})

const hasError = computed(() => {
  // 检查连接是否有错误
  return !props.fromNode || !props.toNode
})

const connectionPath = computed(() => {
  if (!props.fromNode || !props.toNode) {
    return ''
  }

  // 获取连接点位置
  const fromPosition = getConnectorPosition(
    props.fromNode,
    props.connection.fromConnectorId,
    'output'
  )
  const toPosition = getConnectorPosition(props.toNode, props.connection.toConnectorId, 'input')

  if (!fromPosition || !toPosition) {
    return ''
  }

  // 计算贝塞尔曲线路径
  return calculateBezierPath(fromPosition, toPosition, {
    curvature: 0.3,
    style: 'bezier',
  })
})

const arrowColor = computed(() => {
  if (props.isSelected) return '#1890ff'
  if (props.isHighlighted) return '#faad14'
  if (hasError.value) return '#ff4d4f'
  return '#8c8c8c'
})

const labelPosition = computed(() => {
  if (!props.connection.label || !connectionPath.value) {
    return { x: 0, y: 0 }
  }

  const fromPosition = getConnectorPosition(
    props.fromNode,
    props.connection.fromConnectorId,
    'output'
  )
  const toPosition = getConnectorPosition(props.toNode, props.connection.toConnectorId, 'input')

  if (!fromPosition || !toPosition) {
    return { x: 0, y: 0 }
  }

  return getConnectionMidpoint(fromPosition, toPosition)
})

const labelSize = computed(() => {
  if (!props.connection.label) {
    return { width: 0, height: 0 }
  }

  // 估算文本尺寸
  const textLength = props.connection.label.length
  return {
    width: Math.max(textLength * 8, 40),
    height: 20,
  }
})

const conditionPosition = computed(() => {
  if (!props.connection.condition || !connectionPath.value) {
    return { x: 0, y: 0 }
  }

  const fromPosition = getConnectorPosition(
    props.fromNode,
    props.connection.fromConnectorId,
    'output'
  )
  const toPosition = getConnectorPosition(props.toNode, props.connection.toConnectorId, 'input')

  if (!fromPosition || !toPosition) {
    return { x: 0, y: 0 }
  }

  // 条件标签位置在连接线的1/4处
  return {
    x: fromPosition.x + (toPosition.x - fromPosition.x) * 0.25,
    y: fromPosition.y + (toPosition.y - fromPosition.y) * 0.25,
  }
})

const deleteButtonPosition = computed(() => {
  if (!isHovered.value || !props.editable) {
    return { x: 0, y: 0 }
  }

  return labelPosition.value
})

const showDeleteButton = computed(() => {
  return isHovered.value && props.editable && !props.connection.label
})

// 方法
function getConnectorPosition(node, connectorId, type) {
  if (!node || !connectorId) {
    return null
  }

  // 查找连接器
  const connectors = type === 'input' ? node.connectors.input : node.connectors.output
  const connector = connectors.find((c) => c.id === connectorId)

  if (!connector) {
    // 如果找不到连接器，使用默认位置
    const defaultX = type === 'input' ? node.x : node.x + (node.width || 120)
    const defaultY = node.y + (node.height || 60) / 2
    return { x: defaultX, y: defaultY }
  }

  // 返回连接器的绝对位置
  return {
    x: node.x + connector.position.x,
    y: node.y + connector.position.y,
  }
}

function handleClick(event) {
  event.stopPropagation()
  emit('click', {
    connection: props.connection,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleDoubleClick(event) {
  event.stopPropagation()
  emit('dblclick', {
    connection: props.connection,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleContextMenu(event) {
  event.preventDefault()
  event.stopPropagation()
  emit('contextmenu', {
    connection: props.connection,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleMouseEnter(event) {
  isHovered.value = true
  emit('hover', {
    connection: props.connection,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleMouseLeave(event) {
  isHovered.value = false
  emit('unhover', {
    connection: props.connection,
    position: { x: event.clientX, y: event.clientY },
    originalEvent: event,
  })
}

function handleDelete(event) {
  event.stopPropagation()
  emit('delete', {
    connection: props.connection,
    originalEvent: event,
  })
}
</script>

<style scoped>
.connection-line {
  cursor: pointer;
}

.connection {
  fill: none;
  stroke: #8c8c8c;
  stroke-width: 2px;
  transition: all 0.15s ease;
  pointer-events: stroke;
  stroke-linecap: round;
}

.connection:hover {
  stroke: #1890ff;
  stroke-width: 3px;
}

.connection.selected {
  stroke: #1890ff;
  stroke-width: 3px;
}

.connection.highlighted {
  stroke: #faad14;
  stroke-width: 3px;
  animation: pulse 1s infinite;
}

.connection.error {
  stroke: #ff4d4f;
  stroke-dasharray: 5 5;
  animation: dash 1s linear infinite;
}

.connection-arrow {
  transition: fill 0.15s ease;
}

.connection-label {
  pointer-events: none;
}

.label-background {
  fill: white;
  stroke: #d9d9d9;
  stroke-width: 1px;
  opacity: 0.9;
}

.label-text {
  fill: #262626;
  font-size: 12px;
  font-weight: 500;
}

.condition-label {
  pointer-events: none;
}

.condition-background {
  fill: #faad14;
  stroke: white;
  stroke-width: 2px;
}

.condition-text {
  fill: white;
  font-weight: bold;
}

.delete-button {
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.connection-line.hovered .delete-button {
  opacity: 1;
}

.delete-background {
  fill: #ff4d4f;
  stroke: white;
  stroke-width: 2px;
}

.delete-icon {
  fill: white;
  font-weight: bold;
}

.delete-button:hover .delete-background {
  fill: #ff7875;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}
</style>
