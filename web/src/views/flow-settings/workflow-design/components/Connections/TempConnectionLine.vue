<template>
  <g v-if="tempConnection" class="temp-connection-line">
    <!-- 临时连接线路径 -->
    <path
      :d="tempConnectionPath"
      class="temp-connection"
      :class="{
        valid: isValidTarget,
        invalid: isInvalidTarget,
      }"
    />

    <!-- 起始点指示器 -->
    <circle :cx="startPosition.x" :cy="startPosition.y" r="4" class="start-indicator" />

    <!-- 目标点指示器 -->
    <circle
      v-if="targetPosition"
      :cx="targetPosition.x"
      :cy="targetPosition.y"
      r="4"
      class="target-indicator"
      :class="{
        valid: isValidTarget,
        invalid: isInvalidTarget,
      }"
    />

    <!-- 磁性吸附指示器 -->
    <circle
      v-if="magneticTarget"
      :cx="magneticTarget.position.x"
      :cy="magneticTarget.position.y"
      r="8"
      class="magnetic-indicator"
    />

    <!-- 连接提示文本 -->
    <g v-if="showHint" class="connection-hint">
      <rect
        :x="hintPosition.x - hintSize.width / 2"
        :y="hintPosition.y - hintSize.height / 2"
        :width="hintSize.width"
        :height="hintSize.height"
        class="hint-background"
        rx="4"
      />
      <text
        :x="hintPosition.x"
        :y="hintPosition.y"
        text-anchor="middle"
        dominant-baseline="middle"
        class="hint-text"
      >
        {{ hintText }}
      </text>
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { calculateBezierPath, calculateTempConnectionPath } from '../../utils/pathCalculator'
import { validateConnection } from '../../utils/connectionValidator'

// Props
const props = defineProps({
  tempConnection: {
    type: Object,
    default: null,
  },
  magneticTarget: {
    type: Object,
    default: null,
  },
  nodes: {
    type: Array,
    default: () => [],
  },
  connections: {
    type: Array,
    default: () => [],
  },
  showHint: {
    type: Boolean,
    default: true,
  },
})

// 计算属性
const startPosition = computed(() => {
  if (!props.tempConnection) {
    return { x: 0, y: 0 }
  }
  return props.tempConnection.fromPosition
})

const targetPosition = computed(() => {
  if (!props.tempConnection) {
    return null
  }

  // 如果有磁性目标，使用磁性目标位置
  if (props.magneticTarget) {
    return props.magneticTarget.position
  }

  // 否则使用当前鼠标位置
  return props.tempConnection.currentPosition
})

const tempConnectionPath = computed(() => {
  if (!props.tempConnection || !targetPosition.value) {
    return ''
  }

  return calculateTempConnectionPath(startPosition.value, targetPosition.value, {
    curvature: 0.3,
    style: 'bezier',
  })
})

const isValidTarget = computed(() => {
  if (!props.tempConnection || !props.magneticTarget) {
    return false
  }

  const fromNode = props.nodes.find((n) => n.id === props.tempConnection.fromNodeId)
  const toNode = props.nodes.find((n) => n.id === props.magneticTarget.nodeId)

  if (!fromNode || !toNode) {
    return false
  }

  const connectionData = {
    fromNodeId: props.tempConnection.fromNodeId,
    fromConnectorId: props.tempConnection.fromConnectorId,
    toNodeId: props.magneticTarget.nodeId,
    toConnectorId: props.magneticTarget.connectorId,
  }

  const validation = validateConnection(connectionData, fromNode, toNode, props.connections)

  return validation.isValid
})

const isInvalidTarget = computed(() => {
  if (!props.tempConnection || !props.magneticTarget) {
    return false
  }

  return !isValidTarget.value
})

const hintPosition = computed(() => {
  if (!props.tempConnection || !targetPosition.value) {
    return { x: 0, y: 0 }
  }

  // 提示文本显示在连接线中点上方
  const midX = (startPosition.value.x + targetPosition.value.x) / 2
  const midY = (startPosition.value.y + targetPosition.value.y) / 2

  return {
    x: midX,
    y: midY - 20,
  }
})

const hintText = computed(() => {
  if (!props.tempConnection) {
    return ''
  }

  if (props.magneticTarget) {
    if (isValidTarget.value) {
      return '释放以创建连接'
    } else {
      return '无效的连接目标'
    }
  }

  return '拖拽到目标连接点'
})

const hintSize = computed(() => {
  if (!hintText.value) {
    return { width: 0, height: 0 }
  }

  // 估算文本尺寸
  const textLength = hintText.value.length
  return {
    width: Math.max(textLength * 8, 80),
    height: 24,
  }
})
</script>

<style scoped>
.temp-connection-line {
  pointer-events: none;
}

.temp-connection {
  fill: none;
  stroke: #40a9ff;
  stroke-width: 2px;
  stroke-dasharray: 8 4;
  stroke-linecap: round;
  animation: dash 1s linear infinite;
  opacity: 0.8;
}

.temp-connection.valid {
  stroke: #52c41a;
  opacity: 1;
}

.temp-connection.invalid {
  stroke: #ff4d4f;
  opacity: 1;
}

.start-indicator {
  fill: #40a9ff;
  stroke: white;
  stroke-width: 2px;
  opacity: 0.9;
}

.target-indicator {
  fill: #40a9ff;
  stroke: white;
  stroke-width: 2px;
  opacity: 0.7;
  animation: pulse 1s ease-in-out infinite;
}

.target-indicator.valid {
  fill: #52c41a;
  opacity: 1;
}

.target-indicator.invalid {
  fill: #ff4d4f;
  opacity: 1;
}

.magnetic-indicator {
  fill: none;
  stroke: #1890ff;
  stroke-width: 3px;
  opacity: 0.8;
  animation: magnetic-pulse 0.8s ease-in-out infinite;
}

.connection-hint {
  pointer-events: none;
}

.hint-background {
  fill: rgba(0, 0, 0, 0.8);
  opacity: 0.9;
}

.hint-text {
  fill: white;
  font-size: 12px;
  font-weight: 500;
}

@keyframes dash {
  to {
    stroke-dashoffset: -12;
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.7;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

@keyframes magnetic-pulse {
  0%,
  100% {
    opacity: 0.8;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.3);
  }
}
</style>
