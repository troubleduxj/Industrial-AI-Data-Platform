<template>
  <div
    ref="canvasContainer"
    class="workflow-canvas"
    @drop="handleDrop"
    @dragover="handleDragOver"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
  >
    <!-- 画布SVG -->
    <svg
      ref="canvasSvg"
      class="canvas-svg"
      :viewBox="viewBox"
      @wheel="handleWheel"
      @mousedown="handleCanvasMouseDown"
      @mousemove="handleCanvasMouseMove"
      @mouseup="handleCanvasMouseUp"
      @contextmenu="handleCanvasContextMenu"
    >
      <!-- 网格背景 -->
      <defs>
        <pattern id="grid" :width="gridSize" :height="gridSize" patternUnits="userSpaceOnUse">
          <path
            :d="`M ${gridSize} 0 L 0 0 0 ${gridSize}`"
            fill="none"
            stroke="#e0e0e0"
            stroke-width="1"
          />
        </pattern>
      </defs>

      <!-- 网格背景矩形 -->
      <rect v-if="showGrid" width="100%" height="100%" fill="url(#grid)" />

      <!-- 对齐辅助线 -->
      <g v-if="alignmentGuides.length > 0" class="alignment-guides">
        <line
          v-for="(guide, index) in alignmentGuides"
          :key="index"
          :x1="guide.x1 || guide.x"
          :y1="guide.y1 || guide.y"
          :x2="guide.x2 || guide.x"
          :y2="guide.y2 || guide.y"
          stroke="#ff6b6b"
          stroke-width="1"
          stroke-dasharray="5,5"
          class="alignment-guide"
        />
      </g>

      <!-- 连接线 -->
      <g class="connections">
        <path
          v-for="connection in connections"
          :key="connection.id"
          :d="getConnectionPath(connection)"
          :class="[
            'connection-path',
            {
              highlighted: highlightedConnections.includes(connection.id),
              selected: selectedConnections.includes(connection.id),
            },
          ]"
          @click="handleConnectionClick(connection)"
          @contextmenu="handleConnectionContextMenu($event, connection)"
        />
      </g>

      <!-- 临时连接线 -->
      <path v-if="tempConnection.show" :d="getTempConnectionPath()" class="temp-connection" />

      <!-- 磁性吸附指示器 -->
      <circle
        v-if="magneticTarget.show"
        :cx="magneticTarget.x"
        :cy="magneticTarget.y"
        r="8"
        class="magnetic-indicator"
      />
    </svg>

    <!-- 节点容器 -->
    <div class="nodes-container" :style="nodesContainerStyle">
      <WorkflowNode
        v-for="node in nodes"
        :key="node.id"
        :node="node"
        :selected="selectedNodes.includes(node.id)"
        :highlighted="highlightedNodes.includes(node.id)"
        :scale="scale"
        @node-click="handleNodeClick"
        @node-mousedown="handleNodeMouseDown"
        @node-contextmenu="handleNodeContextMenu"
        @connection-start="handleConnectionStart"
        @connection-point="handleConnectionPoint"
      />
    </div>

    <!-- 选择框 -->
    <div v-if="selectionBox.show" class="selection-box" :style="selectionBoxStyle" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, type PropType } from 'vue'
import WorkflowNode from '../Nodes/WorkflowNode.vue'
import {
  calculateConnectionPath,
  getConnectionPointPosition,
  calculateTempConnectionPath,
} from '../../utils/pathCalculator'
import {
  snapPointWithMagnetism,
  getAlignmentGuides,
  applyAlignmentSnap,
} from '../../utils/gridUtils'
import { validateConnection, isDuplicateConnection } from '../../utils/connectionValidator'
import type { WorkflowNode as WorkflowNodeType, Connection } from '../../stores/nodeStore'
import type { ConnectionType } from '../../utils/pathCalculator'

// Props
const props = defineProps({
  nodes: {
    type: Array as PropType<WorkflowNodeType[]>,
    default: () => [],
  },
  connections: {
    type: Array as PropType<Connection[]>,
    default: () => [],
  },
  selectedNodes: {
    type: Array as PropType<string[]>,
    default: () => [],
  },
  selectedConnections: {
    type: Array as PropType<string[]>,
    default: () => [],
  },
  highlightedNodes: {
    type: Array as PropType<string[]>,
    default: () => [],
  },
  highlightedConnections: {
    type: Array as PropType<string[]>,
    default: () => [],
  },
  showGrid: {
    type: Boolean,
    default: true,
  },
  gridSize: {
    type: Number,
    default: 20,
  },
  snapToGrid: {
    type: Boolean,
    default: true,
  },
})

// Emits
const emit = defineEmits([
  'node-click',
  'node-move',
  'node-contextmenu',
  'connection-click',
  'connection-add',
  'connection-contextmenu',
  'canvas-click',
  'canvas-contextmenu',
  'selection-change',
  'zoom-change',
  'node-drop',
])

// Refs
const canvasContainer = ref(null)
const canvasSvg = ref(null)

// 画布状态
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const isDragging = ref(false)
const isSelecting = ref(false)
const dragStartPos = ref({ x: 0, y: 0 })
const lastMousePos = ref({ x: 0, y: 0 })

// 连接状态
const isConnecting = ref(false)
const connectionStart = ref<{
  node: WorkflowNodeType
  type: ConnectionType
  x: number
  y: number
} | null>(null)
const tempConnection = ref<{
  show: boolean
  fromNode: WorkflowNodeType | null
  fromType: ConnectionType
  toX: number
  toY: number
}>({
  show: false,
  fromNode: null,
  fromType: 'output',
  toX: 0,
  toY: 0,
})

// 磁性吸附
const magneticTarget = ref<{
  show: boolean
  x: number
  y: number
  nodeId: string
  type: ConnectionType
}>({
  show: false,
  x: 0,
  y: 0,
  nodeId: '',
  type: 'input',
})

// 对齐辅助线
const alignmentGuides = ref<Array<{
  x?: number
  y?: number
  x1?: number
  y1?: number
  x2?: number
  y2?: number
}>>([])

// 选择框
const selectionBox = ref({
  show: false,
  startX: 0,
  startY: 0,
  endX: 0,
  endY: 0,
})

// 计算属性
const viewBox = computed(() => {
  const width = 4000
  const height = 3000
  return `${-translateX.value} ${-translateY.value} ${width / scale.value} ${height / scale.value}`
})

const nodesContainerStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`,
  transformOrigin: '0 0',
}))

const selectionBoxStyle = computed(() => {
  const { startX, startY, endX, endY } = selectionBox.value
  const left = Math.min(startX, endX)
  const top = Math.min(startY, endY)
  const width = Math.abs(endX - startX)
  const height = Math.abs(endY - startY)

  return {
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
    height: `${height}px`,
  }
})

// 方法
function handleWheel(event) {
  event.preventDefault()

  const delta = event.deltaY > 0 ? 0.9 : 1.1
  const newScale = Math.max(0.1, Math.min(3, scale.value * delta))

  // 计算缩放中心点
  const rect = canvasContainer.value.getBoundingClientRect()
  const centerX = event.clientX - rect.left
  const centerY = event.clientY - rect.top

  // 调整平移以保持缩放中心点不变
  const scaleRatio = newScale / scale.value
  translateX.value = centerX - (centerX - translateX.value) * scaleRatio
  translateY.value = centerY - (centerY - translateY.value) * scaleRatio

  scale.value = newScale
  emit('zoom-change', {
    scale: newScale,
    translateX: translateX.value,
    translateY: translateY.value,
  })
}

function handleCanvasMouseDown(event) {
  if (event.button === 0) {
    // 左键
    const rect = canvasContainer.value.getBoundingClientRect()
    const x = (event.clientX - rect.left - translateX.value) / scale.value
    const y = (event.clientY - rect.top - translateY.value) / scale.value

    if (event.ctrlKey || event.metaKey) {
      // 开始选择框
      isSelecting.value = true
      selectionBox.value = {
        show: true,
        startX: event.clientX - rect.left,
        startY: event.clientY - rect.top,
        endX: event.clientX - rect.left,
        endY: event.clientY - rect.top,
      }
    } else {
      // 开始拖拽画布
      isDragging.value = true
      dragStartPos.value = { x: event.clientX, y: event.clientY }
      lastMousePos.value = { x: translateX.value, y: translateY.value }
    }

    emit('canvas-click', { x, y, event })
  }
}

function handleCanvasMouseMove(event) {
  if (isSelecting.value) {
    const rect = canvasContainer.value.getBoundingClientRect()
    selectionBox.value.endX = event.clientX - rect.left
    selectionBox.value.endY = event.clientY - rect.top

    // 计算选择框内的节点
    updateSelectionBoxNodes()
  } else if (isDragging.value) {
    const deltaX = event.clientX - dragStartPos.value.x
    const deltaY = event.clientY - dragStartPos.value.y

    translateX.value = lastMousePos.value.x + deltaX
    translateY.value = lastMousePos.value.y + deltaY
  } else if (isConnecting.value) {
    // 更新临时连接线
    const rect = canvasContainer.value.getBoundingClientRect()
    const x = (event.clientX - rect.left - translateX.value) / scale.value
    const y = (event.clientY - rect.top - translateY.value) / scale.value

    tempConnection.value.toX = x
    tempConnection.value.toY = y

    // 检查磁性吸附
    checkMagneticSnap(x, y)
  }
}

function handleCanvasMouseUp(event) {
  if (isSelecting.value) {
    isSelecting.value = false
    selectionBox.value.show = false
  } else if (isDragging.value) {
    isDragging.value = false
  } else if (isConnecting.value) {
    // 结束连接
    handleConnectionEnd(event)
  }
}

function handleCanvasContextMenu(event) {
  event.preventDefault()
  const rect = canvasContainer.value.getBoundingClientRect()
  const x = (event.clientX - rect.left - translateX.value) / scale.value
  const y = (event.clientY - rect.top - translateY.value) / scale.value

  emit('canvas-contextmenu', { x, y, event })
}

function handleNodeClick(node, event) {
  emit('node-click', { node, event })
}

function handleNodeMouseDown(node, event) {
  // 节点拖拽逻辑将在NodeDragHandler中处理
}

function handleNodeContextMenu(node, event) {
  emit('node-contextmenu', { node, event })
}

function handleConnectionStart(data) {
  isConnecting.value = true
  connectionStart.value = data
  tempConnection.value = {
    show: true,
    fromNode: data.node,
    fromType: data.type,
    toX: data.x,
    toY: data.y,
  }
}

function handleConnectionPoint(data) {
  if (isConnecting.value && connectionStart.value) {
    const validation = validateConnection(
      connectionStart.value.node,
      data.node,
      connectionStart.value.type,
      data.type
    )

    if (validation.valid) {
      const isDuplicate = isDuplicateConnection(
        props.connections,
        connectionStart.value.node.id,
        data.node.id,
        connectionStart.value.type,
        data.type
      )

      if (!isDuplicate) {
        // 创建新连接
        const newConnection = {
          id: `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          fromNodeId: connectionStart.value.node.id,
          toNodeId: data.node.id,
          fromType: connectionStart.value.type,
          toType: data.type,
        }

        emit('connection-add', newConnection)
      }
    }

    // 重置连接状态
    resetConnectionState()
  }
}

function handleConnectionEnd(event) {
  if (magneticTarget.value.show) {
    // 使用磁性吸附目标
    const targetNode = props.nodes.find((node) => node.id === magneticTarget.value.nodeId)
    if (targetNode) {
      handleConnectionPoint({
        node: targetNode,
        type: magneticTarget.value.type,
        x: magneticTarget.value.x,
        y: magneticTarget.value.y,
      })
      return
    }
  }

  resetConnectionState()
}

function resetConnectionState() {
  isConnecting.value = false
  connectionStart.value = null
  tempConnection.value.show = false
  magneticTarget.value.show = false
}

function checkMagneticSnap(x, y) {
  const snapThreshold = 20
  let closestTarget = null
  let minDistance = Infinity

  props.nodes.forEach((node) => {
    if (node.id === connectionStart.value.node.id) return

    const inputPoint = getConnectionPointPosition(node, 'input')
    const distance = Math.sqrt(Math.pow(x - inputPoint.x, 2) + Math.pow(y - inputPoint.y, 2))

    if (distance < snapThreshold && distance < minDistance) {
      minDistance = distance
      closestTarget = {
        nodeId: node.id,
        type: 'input',
        x: inputPoint.x,
        y: inputPoint.y,
      }
    }
  })

  if (closestTarget) {
    magneticTarget.value = {
      show: true,
      ...closestTarget,
    }
  } else {
    magneticTarget.value.show = false
  }
}

function updateSelectionBoxNodes() {
  const { startX, startY, endX, endY } = selectionBox.value
  const left = Math.min(startX, endX)
  const top = Math.min(startY, endY)
  const right = Math.max(startX, endX)
  const bottom = Math.max(startY, endY)

  const selectedNodeIds = []

  props.nodes.forEach((node) => {
    const nodeLeft = node.x * scale.value + translateX.value
    const nodeTop = node.y * scale.value + translateY.value
    const nodeRight = nodeLeft + 150 * scale.value
    const nodeBottom = nodeTop + 80 * scale.value

    if (nodeLeft < right && nodeRight > left && nodeTop < bottom && nodeBottom > top) {
      selectedNodeIds.push(node.id)
    }
  })

  emit('selection-change', selectedNodeIds)
}

function handleConnectionClick(connection) {
  emit('connection-click', connection)
}

function handleConnectionContextMenu(event, connection) {
  event.preventDefault()
  emit('connection-contextmenu', { connection, event })
}

function getConnectionPath(connection) {
  const fromNode = props.nodes.find((node) => node.id === connection.fromNodeId)
  const toNode = props.nodes.find((node) => node.id === connection.toNodeId)

  if (!fromNode || !toNode) return ''

  const fromPoint = getConnectionPointPosition(fromNode, connection.fromType)
  const toPoint = getConnectionPointPosition(toNode, connection.toType)

  return calculateConnectionPath(fromPoint, toPoint, connection.fromType, connection.toType)
}

function getTempConnectionPath() {
  if (!tempConnection.value.show || !tempConnection.value.fromNode) return ''

  return calculateTempConnectionPath(tempConnection.value.fromNode, tempConnection.value.fromType, {
    x: tempConnection.value.toX,
    y: tempConnection.value.toY,
  })
}

// 拖拽放置事件处理
function handleDragOver(event) {
  console.log('WorkflowCanvas: handleDragOver 被调用')
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
}

function handleDragEnter(event) {
  console.log('WorkflowCanvas: handleDragEnter 被调用')
  event.preventDefault()
}

function handleDragLeave(event) {
  console.log('WorkflowCanvas: handleDragLeave 被调用')
  // 可以在这里添加视觉反馈
}

function handleDrop(event) {
  console.log('WorkflowCanvas: handleDrop 被调用')
  event.preventDefault()

  try {
    // 尝试多种数据格式
    let rawData =
      event.dataTransfer.getData('application/json') ||
      event.dataTransfer.getData('text/plain') ||
      event.dataTransfer.getData('text')

    console.log('拖拽数据原始内容:', rawData)
    console.log('可用的数据类型:', event.dataTransfer.types)

    if (!rawData) {
      console.warn('没有获取到拖拽数据')
      console.warn('可用的数据类型:', Array.from(event.dataTransfer.types))
      return
    }

    const data = JSON.parse(rawData)
    console.log('解析后的拖拽数据:', data)

    if (data.type === 'node') {
      // 计算放置位置
      const rect = canvasContainer.value.getBoundingClientRect()
      const x = (event.clientX - rect.left - translateX.value) / scale.value
      const y = (event.clientY - rect.top - translateY.value) / scale.value

      // 网格对齐
      const snappedX = props.snapToGrid ? Math.round(x / props.gridSize) * props.gridSize : x
      const snappedY = props.snapToGrid ? Math.round(y / props.gridSize) * props.gridSize : y

      console.log('计算的放置位置:', { x: snappedX, y: snappedY })

      // 发射节点放置事件
      emit('node-drop', {
        nodeType: data.nodeType,
        nodeData: data.nodeData,
        position: { x: snappedX, y: snappedY },
      })

      console.log('节点放置事件已发射')
    }
  } catch (error) {
    console.warn('Failed to parse drop data:', error)
  }
}

// 公共方法
function zoomIn() {
  const newScale = Math.min(3, scale.value * 1.2)
  scale.value = newScale
  emit('zoom-change', {
    scale: newScale,
    translateX: translateX.value,
    translateY: translateY.value,
  })
}

function zoomOut() {
  const newScale = Math.max(0.1, scale.value * 0.8)
  scale.value = newScale
  emit('zoom-change', {
    scale: newScale,
    translateX: translateX.value,
    translateY: translateY.value,
  })
}

function fitToScreen() {
  if (props.nodes.length === 0) return

  // 计算所有节点的边界
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity

  props.nodes.forEach((node) => {
    minX = Math.min(minX, node.x)
    minY = Math.min(minY, node.y)
    maxX = Math.max(maxX, node.x + 150)
    maxY = Math.max(maxY, node.y + 80)
  })

  const contentWidth = maxX - minX
  const contentHeight = maxY - minY
  const containerRect = canvasContainer.value.getBoundingClientRect()

  const scaleX = (containerRect.width - 100) / contentWidth
  const scaleY = (containerRect.height - 100) / contentHeight
  const newScale = Math.min(scaleX, scaleY, 1)

  scale.value = newScale
  translateX.value = (containerRect.width - contentWidth * newScale) / 2 - minX * newScale
  translateY.value = (containerRect.height - contentHeight * newScale) / 2 - minY * newScale

  emit('zoom-change', {
    scale: newScale,
    translateX: translateX.value,
    translateY: translateY.value,
  })
}

// 暴露方法
defineExpose({
  zoomIn,
  zoomOut,
  fitToScreen,
  resetConnectionState,
})

// 生命周期
onMounted(() => {
  // 添加全局事件监听
  document.addEventListener('mousemove', handleCanvasMouseMove)
  document.addEventListener('mouseup', handleCanvasMouseUp)
})

onUnmounted(() => {
  // 清理事件监听
  document.removeEventListener('mousemove', handleCanvasMouseMove)
  document.removeEventListener('mouseup', handleCanvasMouseUp)
})
</script>

<style scoped>
.workflow-canvas {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #f8f9fa;
  cursor: grab;
}

.workflow-canvas:active {
  cursor: grabbing;
}

.canvas-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: all;
}

.nodes-container {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.connection-path {
  fill: none;
  stroke: #666;
  stroke-width: 2;
  cursor: pointer;
  transition: stroke-width 0.2s;
}

.connection-path:hover {
  stroke-width: 3;
  stroke: #007bff;
}

.connection-path.highlighted {
  stroke: #28a745;
  stroke-width: 3;
}

.connection-path.selected {
  stroke: #007bff;
  stroke-width: 3;
  stroke-dasharray: 5, 5;
}

.temp-connection {
  fill: none;
  stroke: #007bff;
  stroke-width: 2;
  stroke-dasharray: 5, 5;
  pointer-events: none;
}

.magnetic-indicator {
  fill: #007bff;
  stroke: #fff;
  stroke-width: 2;
  pointer-events: none;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.2);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.alignment-guide {
  pointer-events: none;
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.selection-box {
  position: absolute;
  border: 2px dashed #007bff;
  background: rgba(0, 123, 255, 0.1);
  pointer-events: none;
  z-index: 1000;
}
</style>
