<template>
  <div class="connection-manager">
    <!-- Temporary connection line during dragging -->
    <svg v-if="tempConnection.active" class="temp-connection-svg" :style="svgStyle">
      <defs>
        <marker
          id="temp-arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#1890ff" opacity="0.8" />
        </marker>
      </defs>

      <path
        :d="tempConnectionPath"
        stroke="#1890ff"
        stroke-width="2"
        fill="none"
        stroke-dasharray="5,5"
        opacity="0.8"
        marker-end="url(#temp-arrowhead)"
      />
    </svg>

    <!-- Connection lines -->
    <svg v-if="connections.length > 0" class="connections-svg" :style="svgStyle">
      <defs>
        <marker
          v-for="connection in connections"
          :id="`arrowhead-${connection.id}`"
          :key="`marker-${connection.id}`"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" :fill="getConnectionColor(connection)" />
        </marker>

        <!-- Gradient definitions for animated connections -->
        <linearGradient
          v-for="connection in animatedConnections"
          :id="`gradient-${connection.id}`"
          :key="`gradient-${connection.id}`"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" :stop-color="getConnectionColor(connection)" stop-opacity="0.3" />
          <stop offset="50%" :stop-color="getConnectionColor(connection)" stop-opacity="1" />
          <stop offset="100%" :stop-color="getConnectionColor(connection)" stop-opacity="0.3" />
          <animateTransform
            attributeName="gradientTransform"
            type="translate"
            values="-100 0;100 0;-100 0"
            dur="2s"
            repeatCount="indefinite"
          />
        </linearGradient>
      </defs>

      <!-- Connection paths -->
      <g v-for="connection in connections" :key="connection.id">
        <!-- Main connection path -->
        <path
          :d="getConnectionPath(connection)"
          :stroke="getConnectionStroke(connection)"
          :stroke-width="getConnectionWidth(connection)"
          fill="none"
          :class="{
            'connection-path': true,
            selected: selectedConnections.includes(connection.id),
            highlighted: highlightedConnections.includes(connection.id),
            error: connection.status === 'error',
            active: connection.status === 'active',
          }"
          :marker-end="`url(#arrowhead-${connection.id})`"
          @click="handleConnectionClick(connection, $event)"
          @contextmenu="handleConnectionContextMenu(connection, $event)"
          @mouseenter="handleConnectionHover(connection, $event)"
          @mouseleave="handleConnectionLeave(connection, $event)"
        />

        <!-- Connection label -->
        <text
          v-if="connection.label && showLabels"
          :x="getConnectionLabelPosition(connection).x"
          :y="getConnectionLabelPosition(connection).y"
          class="connection-label"
          text-anchor="middle"
          dominant-baseline="middle"
        >
          {{ connection.label }}
        </text>

        <!-- Connection data flow indicator -->
        <circle
          v-if="connection.status === 'active' && showDataFlow"
          :r="3"
          :fill="getConnectionColor(connection)"
          class="data-flow-indicator"
        >
          <animateMotion :dur="getDataFlowDuration(connection)" repeatCount="indefinite">
            <mpath :href="`#path-${connection.id}`" />
          </animateMotion>
        </circle>

        <!-- Hidden path for animation reference -->
        <path
          :id="`path-${connection.id}`"
          :d="getConnectionPath(connection)"
          fill="none"
          stroke="none"
          style="display: none"
        />
      </g>
    </svg>

    <!-- Connection context menu -->
    <div
      v-if="contextMenu.visible"
      class="connection-context-menu"
      :style="{
        left: contextMenu.x + 'px',
        top: contextMenu.y + 'px',
      }"
      @click.stop
    >
      <div class="context-menu-item" @click="editConnection">
        <span class="menu-icon">✏️</span>
        编辑连接
      </div>
      <div class="context-menu-item" @click="duplicateConnection">
        <span class="menu-icon">📋</span>
        复制连接
      </div>
      <div class="context-menu-divider"></div>
      <div class="context-menu-item danger" @click="deleteConnection">
        <span class="menu-icon">🗑️</span>
        删除连接
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

// Props
const props = defineProps({
  connections: {
    type: Array,
    default: () => [],
  },
  nodes: {
    type: Array,
    default: () => [],
  },
  selectedConnections: {
    type: Array,
    default: () => [],
  },
  highlightedConnections: {
    type: Array,
    default: () => [],
  },
  canvasSize: {
    type: Object,
    default: () => ({ width: 1000, height: 1000 }),
  },
  showLabels: {
    type: Boolean,
    default: true,
  },
  showDataFlow: {
    type: Boolean,
    default: false,
  },
  connectionStyle: {
    type: String,
    default: 'bezier',
    validator: (value: string) => ['bezier', 'straight', 'orthogonal'].includes(value),
  },
})

// Emits
const emit = defineEmits([
  'connection-start',
  'connection-end',
  'connection-click',
  'connection-contextmenu',
  'connection-hover',
  'connection-leave',
  'connection-create',
  'connection-update',
  'connection-delete',
])

// Reactive data
const tempConnection = ref({
  active: false,
  startNode: null,
  startPoint: null,
  endPosition: { x: 0, y: 0 },
})

const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  connection: null,
})

const mousePosition = ref({ x: 0, y: 0 })

// Computed properties
const svgStyle = computed(() => ({
  position: 'absolute',
  top: 0,
  left: 0,
  width: props.canvasSize.width + 'px',
  height: props.canvasSize.height + 'px',
  pointerEvents: 'none',
  zIndex: 1,
}))

const tempConnectionPath = computed(() => {
  if (!tempConnection.value.active) return ''

  const start = getNodeConnectionPoint(
    tempConnection.value.startNode,
    tempConnection.value.startPoint
  )
  const end = tempConnection.value.endPosition

  return generatePath(start, end, props.connectionStyle)
})

const animatedConnections = computed(() => {
  return props.connections.filter((conn) => conn.status === 'active')
})

// Methods
function startConnection(nodeId, pointType, pointPosition) {
  const node = props.nodes.find((n) => n.id === nodeId)
  if (!node) return

  tempConnection.value = {
    active: true,
    startNode: node,
    startPoint: { type: pointType, position: pointPosition },
    endPosition: mousePosition.value,
  }

  emit('connection-start', {
    nodeId,
    pointType,
    pointPosition,
  })
}

function endConnection(nodeId, pointType, pointPosition) {
  if (!tempConnection.value.active) return

  const startNode = tempConnection.value.startNode
  const endNode = props.nodes.find((n) => n.id === nodeId)

  if (startNode && endNode && startNode.id !== endNode.id) {
    const newConnection = {
      id: `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      sourceNodeId: startNode.id,
      sourcePoint: tempConnection.value.startPoint,
      targetNodeId: endNode.id,
      targetPoint: { type: pointType, position: pointPosition },
      status: 'idle',
      createdAt: new Date().toISOString(),
    }

    emit('connection-create', newConnection)
  }

  tempConnection.value.active = false

  emit('connection-end', {
    nodeId,
    pointType,
    pointPosition,
  })
}

function cancelConnection() {
  tempConnection.value.active = false
}

function getConnectionPath(connection) {
  const sourceNode = props.nodes.find((n) => n.id === connection.sourceNodeId)
  const targetNode = props.nodes.find((n) => n.id === connection.targetNodeId)

  if (!sourceNode || !targetNode) return ''

  const start = getNodeConnectionPoint(sourceNode, connection.sourcePoint)
  const end = getNodeConnectionPoint(targetNode, connection.targetPoint)

  return generatePath(start, end, props.connectionStyle)
}

function getNodeConnectionPoint(node, point) {
  const baseX = node.position.x + (node.width || 200) / 2
  const baseY = node.position.y + (node.height || 100) / 2

  switch (point.position) {
    case 'top':
      return { x: baseX, y: node.position.y }
    case 'bottom':
      return { x: baseX, y: node.position.y + (node.height || 100) }
    case 'left':
      return { x: node.position.x, y: baseY }
    case 'right':
    default:
      return { x: node.position.x + (node.width || 200), y: baseY }
  }
}

function generatePath(start, end, style) {
  switch (style) {
    case 'straight':
      return `M ${start.x} ${start.y} L ${end.x} ${end.y}`

    case 'orthogonal':
      const midX = (start.x + end.x) / 2
      return `M ${start.x} ${start.y} L ${midX} ${start.y} L ${midX} ${end.y} L ${end.x} ${end.y}`

    case 'bezier':
    default:
      const dx = end.x - start.x
      const dy = end.y - start.y
      const controlOffset = Math.abs(dx) * 0.5

      const cp1x = start.x + controlOffset
      const cp1y = start.y
      const cp2x = end.x - controlOffset
      const cp2y = end.y

      return `M ${start.x} ${start.y} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${end.x} ${end.y}`
  }
}

function getConnectionColor(connection) {
  switch (connection.status) {
    case 'active':
      return '#52c41a'
    case 'error':
      return '#ff4d4f'
    case 'warning':
      return '#faad14'
    default:
      return '#1890ff'
  }
}

function getConnectionStroke(connection) {
  if (connection.status === 'active' && props.showDataFlow) {
    return `url(#gradient-${connection.id})`
  }
  return getConnectionColor(connection)
}

function getConnectionWidth(connection) {
  if (props.selectedConnections.includes(connection.id)) {
    return 3
  }
  if (props.highlightedConnections.includes(connection.id)) {
    return 2.5
  }
  return 2
}

function getConnectionLabelPosition(connection) {
  const sourceNode = props.nodes.find((n) => n.id === connection.sourceNodeId)
  const targetNode = props.nodes.find((n) => n.id === connection.targetNodeId)

  if (!sourceNode || !targetNode) return { x: 0, y: 0 }

  const start = getNodeConnectionPoint(sourceNode, connection.sourcePoint)
  const end = getNodeConnectionPoint(targetNode, connection.targetPoint)

  return {
    x: (start.x + end.x) / 2,
    y: (start.y + end.y) / 2 - 10,
  }
}

function getDataFlowDuration(connection) {
  // Base duration on connection length
  const sourceNode = props.nodes.find((n) => n.id === connection.sourceNodeId)
  const targetNode = props.nodes.find((n) => n.id === connection.targetNodeId)

  if (!sourceNode || !targetNode) return '2s'

  const start = getNodeConnectionPoint(sourceNode, connection.sourcePoint)
  const end = getNodeConnectionPoint(targetNode, connection.targetPoint)
  const distance = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2))

  const duration = Math.max(1, Math.min(5, distance / 100))
  return `${duration}s`
}

function handleConnectionClick(connection, event) {
  event.stopPropagation()
  emit('connection-click', { connection, event })
}

function handleConnectionContextMenu(connection, event) {
  event.preventDefault()
  event.stopPropagation()

  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    connection,
  }

  emit('connection-contextmenu', { connection, event })
}

function handleConnectionHover(connection, event) {
  emit('connection-hover', { connection, event })
}

function handleConnectionLeave(connection, event) {
  emit('connection-leave', { connection, event })
}

function editConnection() {
  if (contextMenu.value.connection) {
    emit('connection-update', contextMenu.value.connection)
  }
  hideContextMenu()
}

function duplicateConnection() {
  if (contextMenu.value.connection) {
    const newConnection = {
      ...contextMenu.value.connection,
      id: `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date().toISOString(),
    }
    emit('connection-create', newConnection)
  }
  hideContextMenu()
}

function deleteConnection() {
  if (contextMenu.value.connection) {
    emit('connection-delete', contextMenu.value.connection.id)
  }
  hideContextMenu()
}

function hideContextMenu() {
  contextMenu.value.visible = false
}

function handleMouseMove(event) {
  mousePosition.value = {
    x: event.clientX,
    y: event.clientY,
  }

  if (tempConnection.value.active) {
    tempConnection.value.endPosition = mousePosition.value
  }
}

function handleMouseUp() {
  if (tempConnection.value.active) {
    cancelConnection()
  }
}

function handleClickOutside() {
  hideContextMenu()
}

// Lifecycle
onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  document.removeEventListener('click', handleClickOutside)
})

// Expose methods
defineExpose({
  startConnection,
  endConnection,
  cancelConnection,
})
</script>

<style scoped>
.connection-manager {
  position: relative;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.temp-connection-svg,
.connections-svg {
  position: absolute;
  top: 0;
  left: 0;
  overflow: visible;
}

.connection-path {
  cursor: pointer;
  pointer-events: stroke;
  transition: all 0.2s ease;
}

.connection-path:hover {
  stroke-width: 3;
  filter: drop-shadow(0 0 4px rgba(24, 144, 255, 0.4));
}

.connection-path.selected {
  stroke-width: 3;
  filter: drop-shadow(0 0 6px rgba(24, 144, 255, 0.6));
}

.connection-path.highlighted {
  stroke-width: 2.5;
  filter: drop-shadow(0 0 4px rgba(250, 173, 20, 0.4));
}

.connection-path.error {
  stroke-dasharray: 5, 5;
  animation: errorPulse 1s ease-in-out infinite;
}

.connection-path.active {
  animation: activePulse 2s ease-in-out infinite;
}

@keyframes errorPulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

@keyframes activePulse {
  0%,
  100% {
    filter: drop-shadow(0 0 2px rgba(82, 196, 26, 0.4));
  }
  50% {
    filter: drop-shadow(0 0 8px rgba(82, 196, 26, 0.8));
  }
}

.connection-label {
  font-size: 11px;
  fill: #595959;
  font-weight: 500;
  pointer-events: none;
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8);
}

.data-flow-indicator {
  filter: drop-shadow(0 0 3px rgba(82, 196, 26, 0.6));
}

.connection-context-menu {
  position: fixed;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 140px;
  pointer-events: all;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: #262626;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.context-menu-item:hover {
  background: #f5f5f5;
}

.context-menu-item.danger {
  color: #ff4d4f;
}

.context-menu-item.danger:hover {
  background: #fff2f0;
}

.menu-icon {
  font-size: 12px;
}

.context-menu-divider {
  height: 1px;
  background: #e8e8e8;
  margin: 4px 0;
}
</style>
