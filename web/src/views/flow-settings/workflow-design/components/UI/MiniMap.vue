<template>
  <div class="mini-map" :class="{ collapsed: isCollapsed, hidden: isHidden }">
    <!-- 头部控制 -->
    <div class="minimap-header">
      <div class="minimap-title">
        <span class="icon">🗺️</span>
        <span class="title-text">导航</span>
      </div>
      <div class="minimap-controls">
        <button class="control-btn" :title="isCollapsed ? '展开' : '收起'" @click="toggleCollapse">
          {{ isCollapsed ? '▲' : '▼' }}
        </button>
        <button class="control-btn" title="隐藏" @click="toggleHidden">✕</button>
      </div>
    </div>

    <!-- 迷你地图内容 -->
    <div v-show="!isCollapsed" class="minimap-content">
      <!-- SVG 画布 -->
      <svg
        ref="minimapSvg"
        class="minimap-svg"
        :width="minimapWidth"
        :height="minimapHeight"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseLeave"
      >
        <!-- 背景 -->
        <rect
          class="minimap-background"
          :width="minimapWidth"
          :height="minimapHeight"
          fill="#fafafa"
          stroke="#e8e8e8"
        />

        <!-- 网格 -->
        <defs v-if="showGrid">
          <pattern
            id="minimap-grid"
            :width="gridSize"
            :height="gridSize"
            patternUnits="userSpaceOnUse"
          >
            <path
              :d="`M ${gridSize} 0 L 0 0 0 ${gridSize}`"
              fill="none"
              stroke="#f0f0f0"
              stroke-width="0.5"
            />
          </pattern>
        </defs>
        <rect
          v-if="showGrid"
          :width="minimapWidth"
          :height="minimapHeight"
          fill="url(#minimap-grid)"
        />

        <!-- 连接线 -->
        <g class="minimap-connections">
          <path
            v-for="connection in visibleConnections"
            :key="connection.id"
            :d="getConnectionPath(connection)"
            class="minimap-connection"
            :class="{
              selected: connection.selected,
              highlighted: connection.highlighted,
            }"
            fill="none"
            stroke="#1890ff"
            stroke-width="1"
            opacity="0.6"
          />
        </g>

        <!-- 节点 -->
        <g class="minimap-nodes">
          <rect
            v-for="node in visibleNodes"
            :key="node.id"
            :x="getNodeX(node)"
            :y="getNodeY(node)"
            :width="getNodeWidth(node)"
            :height="getNodeHeight(node)"
            :rx="2"
            class="minimap-node"
            :class="{
              selected: node.selected,
              highlighted: node.highlighted,
              error: node.status === 'error',
              success: node.status === 'success',
              running: node.status === 'running',
            }"
            :fill="getNodeColor(node)"
            :stroke="getNodeStroke(node)"
            stroke-width="1"
          />
        </g>

        <!-- 视口框 -->
        <rect
          class="viewport-box"
          :x="viewportBox.x"
          :y="viewportBox.y"
          :width="viewportBox.width"
          :height="viewportBox.height"
          fill="rgba(24, 144, 255, 0.1)"
          stroke="#1890ff"
          stroke-width="2"
          rx="2"
        />

        <!-- 拖拽手柄 -->
        <circle
          v-if="isDragging"
          class="drag-handle"
          :cx="dragPosition.x"
          :cy="dragPosition.y"
          r="4"
          fill="#1890ff"
          stroke="white"
          stroke-width="2"
        />
      </svg>

      <!-- 缩放控制 -->
      <div class="zoom-controls">
        <button class="zoom-btn" title="放大" @click="zoomIn">+</button>
        <div class="zoom-level">{{ Math.round(scale * 100) }}%</div>
        <button class="zoom-btn" title="缩小" @click="zoomOut">-</button>
        <button class="zoom-btn fit" title="适应视图" @click="fitToView">⌂</button>
      </div>

      <!-- 统计信息 -->
      <div class="minimap-stats">
        <div class="stat-item">
          <span class="stat-label">节点:</span>
          <span class="stat-value">{{ stats.nodeCount }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">连接:</span>
          <span class="stat-value">{{ stats.connectionCount }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { pathCalculator } from '../../utils/pathCalculator'

// Props
const props = defineProps({
  // 节点数据
  nodes: {
    type: Array,
    default: () => [],
  },

  // 连接数据
  connections: {
    type: Array,
    default: () => [],
  },

  // 画布状态
  canvasState: {
    type: Object,
    default: () => ({
      scale: 1,
      offset: { x: 0, y: 0 },
      bounds: { x: 0, y: 0, width: 800, height: 600 },
    }),
  },

  // 视口大小
  viewportSize: {
    type: Object,
    default: () => ({ width: 800, height: 600 }),
  },

  // 显示网格
  showGrid: {
    type: Boolean,
    default: true,
  },

  // 迷你地图大小
  width: {
    type: Number,
    default: 200,
  },

  height: {
    type: Number,
    default: 150,
  },
})

// Emits
const emit = defineEmits(['viewport-change', 'zoom-change', 'fit-to-view'])

// 响应式数据
const isCollapsed = ref(false)
const isHidden = ref(false)
const isDragging = ref(false)
const dragPosition = ref({ x: 0, y: 0 })
const minimapSvg = ref(null)

// 计算属性
const minimapWidth = computed(() => props.width)
const minimapHeight = computed(() => props.height)

const scale = computed(() => props.canvasState.scale)

const gridSize = computed(() => {
  return Math.max(4, 20 / scale.value)
})

// 计算工作流边界
const workflowBounds = computed(() => {
  if (props.nodes.length === 0) {
    return { x: 0, y: 0, width: 800, height: 600 }
  }

  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity

  props.nodes.forEach((node) => {
    const nodeWidth = node.size?.width || 120
    const nodeHeight = node.size?.height || 80

    minX = Math.min(minX, node.position.x)
    minY = Math.min(minY, node.position.y)
    maxX = Math.max(maxX, node.position.x + nodeWidth)
    maxY = Math.max(maxY, node.position.y + nodeHeight)
  })

  // 添加边距
  const padding = 50
  return {
    x: minX - padding,
    y: minY - padding,
    width: maxX - minX + padding * 2,
    height: maxY - minY + padding * 2,
  }
})

// 计算缩放比例
const minimapScale = computed(() => {
  const scaleX = minimapWidth.value / workflowBounds.value.width
  const scaleY = minimapHeight.value / workflowBounds.value.height
  return Math.min(scaleX, scaleY, 1)
})

// 计算偏移
const minimapOffset = computed(() => {
  const scaledWidth = workflowBounds.value.width * minimapScale.value
  const scaledHeight = workflowBounds.value.height * minimapScale.value

  return {
    x: (minimapWidth.value - scaledWidth) / 2 - workflowBounds.value.x * minimapScale.value,
    y: (minimapHeight.value - scaledHeight) / 2 - workflowBounds.value.y * minimapScale.value,
  }
})

// 可见节点
const visibleNodes = computed(() => {
  return props.nodes.filter((node) => {
    const x = getNodeX(node)
    const y = getNodeY(node)
    const width = getNodeWidth(node)
    const height = getNodeHeight(node)

    return x + width >= 0 && x <= minimapWidth.value && y + height >= 0 && y <= minimapHeight.value
  })
})

// 可见连接
const visibleConnections = computed(() => {
  return props.connections.filter((connection) => {
    const sourceNode = props.nodes.find((n) => n.id === connection.sourceNodeId)
    const targetNode = props.nodes.find((n) => n.id === connection.targetNodeId)
    return sourceNode && targetNode
  })
})

// 视口框
const viewportBox = computed(() => {
  const viewportWidth = props.viewportSize.width / props.canvasState.scale
  const viewportHeight = props.viewportSize.height / props.canvasState.scale

  // 安全检查 offset 是否存在
  const offset = props.canvasState.offset || { x: 0, y: 0 }

  const x = (-offset.x / props.canvasState.scale) * minimapScale.value + minimapOffset.value.x
  const y = (-offset.y / props.canvasState.scale) * minimapScale.value + minimapOffset.value.y
  const width = viewportWidth * minimapScale.value
  const height = viewportHeight * minimapScale.value

  return {
    x: Math.max(0, Math.min(x, minimapWidth.value - width)),
    y: Math.max(0, Math.min(y, minimapHeight.value - height)),
    width: Math.min(width, minimapWidth.value),
    height: Math.min(height, minimapHeight.value),
  }
})

// 统计信息
const stats = computed(() => {
  return {
    nodeCount: props.nodes.length,
    connectionCount: props.connections.length,
  }
})

// 方法
function getNodeX(node) {
  return node.position.x * minimapScale.value + minimapOffset.value.x
}

function getNodeY(node) {
  return node.position.y * minimapScale.value + minimapOffset.value.y
}

function getNodeWidth(node) {
  const width = node.size?.width || 120
  return Math.max(4, width * minimapScale.value)
}

function getNodeHeight(node) {
  const height = node.size?.height || 80
  return Math.max(3, height * minimapScale.value)
}

function getNodeColor(node) {
  if (node.selected) return '#1890ff'
  if (node.highlighted) return '#40a9ff'

  switch (node.status) {
    case 'error':
      return '#ff4d4f'
    case 'success':
      return '#52c41a'
    case 'running':
      return '#1890ff'
    case 'warning':
      return '#fa8c16'
    default:
      return '#f0f0f0'
  }
}

function getNodeStroke(node) {
  if (node.selected) return '#0050b3'
  if (node.highlighted) return '#096dd9'
  return '#d9d9d9'
}

function getConnectionPath(connection) {
  const sourceNode = props.nodes.find((n) => n.id === connection.sourceNodeId)
  const targetNode = props.nodes.find((n) => n.id === connection.targetNodeId)

  if (!sourceNode || !targetNode) return ''

  const sourceX = getNodeX(sourceNode) + getNodeWidth(sourceNode)
  const sourceY = getNodeY(sourceNode) + getNodeHeight(sourceNode) / 2
  const targetX = getNodeX(targetNode)
  const targetY = getNodeY(targetNode) + getNodeHeight(targetNode) / 2

  return pathCalculator.calculateBezierPath({ x: sourceX, y: sourceY }, { x: targetX, y: targetY })
}

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function toggleHidden() {
  isHidden.value = !isHidden.value
}

function handleMouseDown(event) {
  const rect = minimapSvg.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  // 检查是否点击在视口框内
  const vb = viewportBox.value
  if (x >= vb.x && x <= vb.x + vb.width && y >= vb.y && y <= vb.y + vb.height) {
    isDragging.value = true
    dragPosition.value = { x, y }
  } else {
    // 点击空白区域，移动视口到该位置
    moveViewportTo(x, y)
  }

  event.preventDefault()
}

function handleMouseMove(event) {
  if (!isDragging.value) return

  const rect = minimapSvg.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  dragPosition.value = { x, y }
  moveViewportTo(x, y)
}

function handleMouseUp() {
  isDragging.value = false
}

function handleMouseLeave() {
  isDragging.value = false
}

function moveViewportTo(x, y) {
  // 将迷你地图坐标转换为画布坐标
  const canvasX = (x - minimapOffset.value.x) / minimapScale.value
  const canvasY = (y - minimapOffset.value.y) / minimapScale.value

  // 计算新的偏移量（使点击位置成为视口中心）
  const viewportCenterX = props.viewportSize.width / 2 / props.canvasState.scale
  const viewportCenterY = props.viewportSize.height / 2 / props.canvasState.scale

  const newOffsetX = -(canvasX - viewportCenterX) * props.canvasState.scale
  const newOffsetY = -(canvasY - viewportCenterY) * props.canvasState.scale

  emit('viewport-change', {
    offset: { x: newOffsetX, y: newOffsetY },
  })
}

function zoomIn() {
  const newScale = Math.min(props.canvasState.scale * 1.2, 3)
  emit('zoom-change', newScale)
}

function zoomOut() {
  const newScale = Math.max(props.canvasState.scale / 1.2, 0.1)
  emit('zoom-change', newScale)
}

function fitToView() {
  emit('fit-to-view')
}

// 监听画布状态变化
watch(
  () => [props.nodes, props.connections],
  () => {
    nextTick(() => {
      // 重新计算边界和缩放
    })
  },
  { deep: true }
)
</script>

<style scoped>
.mini-map {
  position: absolute;
  top: 16px;
  right: 16px;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  transition: all 0.3s ease;
  user-select: none;
}

.mini-map.collapsed {
  height: auto;
}

.mini-map.hidden {
  transform: translateX(calc(100% + 16px));
}

.minimap-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
  border-radius: 8px 8px 0 0;
}

.minimap-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #262626;
}

.minimap-controls {
  display: flex;
  gap: 4px;
}

.control-btn {
  padding: 2px 4px;
  border: none;
  background: none;
  color: #8c8c8c;
  cursor: pointer;
  font-size: 12px;
  border-radius: 3px;
  transition: all 0.15s ease;
}

.control-btn:hover {
  background: #e6f7ff;
  color: #1890ff;
}

.minimap-content {
  padding: 8px;
}

.minimap-svg {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  cursor: pointer;
  display: block;
}

.minimap-background {
  cursor: pointer;
}

.minimap-node {
  cursor: pointer;
  transition: all 0.15s ease;
}

.minimap-node:hover {
  stroke-width: 2;
  filter: brightness(1.1);
}

.minimap-node.selected {
  stroke-width: 2;
  filter: brightness(1.2);
}

.minimap-node.highlighted {
  stroke-width: 2;
  filter: brightness(1.1);
}

.minimap-node.error {
  animation: pulse-error 2s infinite;
}

.minimap-node.running {
  animation: pulse-running 1.5s infinite;
}

.minimap-connection {
  cursor: pointer;
  transition: all 0.15s ease;
}

.minimap-connection:hover {
  stroke-width: 2;
  opacity: 0.8;
}

.minimap-connection.selected {
  stroke-width: 2;
  opacity: 1;
}

.minimap-connection.highlighted {
  stroke-width: 2;
  opacity: 0.8;
}

.viewport-box {
  cursor: move;
  transition: all 0.15s ease;
}

.viewport-box:hover {
  fill: rgba(24, 144, 255, 0.2);
}

.drag-handle {
  cursor: move;
}

.zoom-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 8px;
  padding: 4px;
  background: #f5f5f5;
  border-radius: 4px;
}

.zoom-btn {
  width: 24px;
  height: 24px;
  border: 1px solid #d9d9d9;
  border-radius: 3px;
  background: #ffffff;
  color: #595959;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.zoom-btn:hover {
  border-color: #40a9ff;
  color: #1890ff;
  background: #f6ffed;
}

.zoom-btn.fit {
  font-size: 14px;
  font-weight: normal;
}

.zoom-level {
  font-size: 11px;
  color: #8c8c8c;
  min-width: 35px;
  text-align: center;
  font-family: 'Courier New', monospace;
}

.minimap-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  padding: 4px 6px;
  background: #f9f9f9;
  border-radius: 3px;
  font-size: 10px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 2px;
}

.stat-label {
  color: #8c8c8c;
}

.stat-value {
  color: #262626;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

/* 动画效果 */
@keyframes pulse-error {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

@keyframes pulse-running {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .mini-map {
    top: 8px;
    right: 8px;
    width: 150px;
  }

  .minimap-stats {
    font-size: 9px;
  }

  .zoom-controls {
    gap: 2px;
  }

  .zoom-btn {
    width: 20px;
    height: 20px;
    font-size: 10px;
  }
}
</style>
