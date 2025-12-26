<template>
  <div
    class="workflow-node"
    :class="[
      `node-${node.type}`,
      {
        selected: selected,
        highlighted: highlighted,
        dragging: isDragging,
      },
    ]"
    :style="nodeStyle"
    @click="handleClick"
    @mousedown="handleMouseDown"
    @contextmenu="handleContextMenu"
  >
    <!-- 节点主体 -->
    <div class="node-content">
      <!-- 节点图标 -->
      <div class="node-icon">
        <i :class="getNodeIcon(node.type)"></i>
      </div>

      <!-- 节点信息 -->
      <div class="node-info">
        <div class="node-title">{{ node.name || getNodeTypeName(node.type) }}</div>
        <div class="node-description">
          {{ node.description || getNodeTypeDescription(node.type) }}
        </div>
      </div>

      <!-- 节点状态 -->
      <div v-if="node.status" class="node-status">
        <i :class="getStatusIcon(node.status)" :style="{ color: getStatusColor(node.status) }"></i>
      </div>
    </div>

    <!-- 输入连接点 -->
    <div
      v-if="hasInput"
      class="connection-point input-point"
      :class="{ active: isInputActive }"
      @mousedown.stop="handleConnectionStart('input')"
      @mouseenter="handleConnectionPointEnter('input')"
      @mouseleave="handleConnectionPointLeave('input')"
    >
      <div class="connection-dot"></div>
      <div class="connection-label">输入</div>
    </div>

    <!-- 输出连接点 -->
    <div
      v-if="hasOutput"
      class="connection-point output-point"
      :class="{ active: isOutputActive }"
      @mousedown.stop="handleConnectionStart('output')"
      @mouseenter="handleConnectionPointEnter('output')"
      @mouseleave="handleConnectionPointLeave('output')"
    >
      <div class="connection-dot"></div>
      <div class="connection-label">输出</div>
    </div>

    <!-- 节点操作按钮 -->
    <div v-if="selected" class="node-actions">
      <button class="action-btn" title="编辑" @click.stop="handleEdit">
        <i class="fas fa-edit"></i>
      </button>
      <button class="action-btn" title="复制" @click.stop="handleCopy">
        <i class="fas fa-copy"></i>
      </button>
      <button class="action-btn danger" title="删除" @click.stop="handleDelete">
        <i class="fas fa-trash"></i>
      </button>
    </div>

    <!-- 节点错误提示 -->
    <div v-if="node.error" class="node-error">
      <i class="fas fa-exclamation-triangle"></i>
      <span>{{ node.error }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  NODE_TYPES,
  getNodeIcon,
  getNodeTypeName,
  getNodeTypeDescription,
} from '../../utils/nodeTypes'
import { getConnectionPointPosition } from '../../utils/pathCalculator'

// Props
const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
  selected: {
    type: Boolean,
    default: false,
  },
  highlighted: {
    type: Boolean,
    default: false,
  },
  scale: {
    type: Number,
    default: 1,
  },
})

// Emits
const emit = defineEmits([
  'node-click',
  'node-mousedown',
  'node-contextmenu',
  'connection-start',
  'connection-point',
  'node-edit',
  'node-copy',
  'node-delete',
])

// 响应式数据
const isDragging = ref(false)
const isInputActive = ref(false)
const isOutputActive = ref(false)

// 计算属性
const nodeStyle = computed(() => ({
  left: `${props.node.x}px`,
  top: `${props.node.y}px`,
  transform: `scale(${Math.max(0.5, Math.min(1, props.scale))})`,
}))

const hasInput = computed(() => {
  const nodeType = NODE_TYPES[props.node.type]
  return nodeType && nodeType.inputs && nodeType.inputs.length > 0
})

const hasOutput = computed(() => {
  const nodeType = NODE_TYPES[props.node.type]
  return nodeType && nodeType.outputs && nodeType.outputs.length > 0
})

// 方法
function handleClick(event) {
  event.stopPropagation()
  emit('node-click', props.node, event)
}

function handleMouseDown(event) {
  event.stopPropagation()
  isDragging.value = true
  emit('node-mousedown', props.node, event)
}

function handleContextMenu(event) {
  event.preventDefault()
  event.stopPropagation()
  emit('node-contextmenu', props.node, event)
}

function handleConnectionStart(type) {
  const connectionPoint = getConnectionPointPosition(props.node, type)
  emit('connection-start', {
    node: props.node,
    type,
    x: connectionPoint.x,
    y: connectionPoint.y,
  })
}

function handleConnectionPointEnter(type) {
  if (type === 'input') {
    isInputActive.value = true
  } else {
    isOutputActive.value = true
  }

  const connectionPoint = getConnectionPointPosition(props.node, type)
  emit('connection-point', {
    node: props.node,
    type,
    x: connectionPoint.x,
    y: connectionPoint.y,
  })
}

function handleConnectionPointLeave(type) {
  if (type === 'input') {
    isInputActive.value = false
  } else {
    isOutputActive.value = false
  }
}

function handleEdit() {
  emit('node-edit', props.node)
}

function handleCopy() {
  emit('node-copy', props.node)
}

function handleDelete() {
  emit('node-delete', props.node)
}

function getStatusIcon(status) {
  const icons = {
    running: 'fas fa-play-circle',
    success: 'fas fa-check-circle',
    error: 'fas fa-exclamation-circle',
    warning: 'fas fa-exclamation-triangle',
    pending: 'fas fa-clock',
    stopped: 'fas fa-stop-circle',
  }
  return icons[status] || 'fas fa-circle'
}

function getStatusColor(status) {
  const colors = {
    running: '#007bff',
    success: '#28a745',
    error: '#dc3545',
    warning: '#ffc107',
    pending: '#6c757d',
    stopped: '#6c757d',
  }
  return colors[status] || '#6c757d'
}

// 生命周期
onMounted(() => {
  // 添加鼠标事件监听
  document.addEventListener('mouseup', handleMouseUp)
})

onUnmounted(() => {
  // 清理事件监听
  document.removeEventListener('mouseup', handleMouseUp)
})

function handleMouseUp() {
  isDragging.value = false
}
</script>

<style scoped>
.workflow-node {
  position: absolute;
  width: 150px;
  min-height: 80px;
  background: #fff;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  pointer-events: all;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.workflow-node:hover {
  border-color: #007bff;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.workflow-node.selected {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.workflow-node.highlighted {
  border-color: #28a745;
  box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.25);
}

.workflow-node.dragging {
  opacity: 0.8;
  transform: rotate(2deg);
}

/* 节点类型样式 */
.node-start {
  border-color: #28a745;
}

.node-end {
  border-color: #dc3545;
}

.node-condition {
  border-color: #ffc107;
}

.node-action {
  border-color: #007bff;
}

.node-integration {
  border-color: #6f42c1;
}

.node-content {
  padding: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.node-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 16px;
}

.node-info {
  flex: 1;
  min-width: 0;
}

.node-title {
  font-size: 12px;
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-description {
  font-size: 10px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-status {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

/* 连接点样式 */
.connection-point {
  position: absolute;
  width: 12px;
  height: 12px;
  cursor: crosshair;
  z-index: 20;
}

.input-point {
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
}

.output-point {
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
}

.connection-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #666;
  transition: all 0.2s ease;
}

.connection-point:hover .connection-dot,
.connection-point.active .connection-dot {
  background: #007bff;
  border-color: #007bff;
  transform: scale(1.2);
}

.connection-label {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #666;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 4px;
  border-radius: 2px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.connection-point:hover .connection-label,
.connection-point.active .connection-label {
  opacity: 1;
}

/* 节点操作按钮 */
.node-actions {
  position: absolute;
  top: -30px;
  right: 0;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.workflow-node.selected .node-actions {
  opacity: 1;
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: #fff;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: #f8f9fa;
  color: #333;
}

.action-btn.danger:hover {
  background: #dc3545;
  color: #fff;
}

/* 节点错误提示 */
.node-error {
  position: absolute;
  bottom: -25px;
  left: 0;
  right: 0;
  background: #dc3545;
  color: #fff;
  font-size: 10px;
  padding: 2px 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 30;
}

.node-error i {
  font-size: 10px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .workflow-node {
    width: 120px;
    min-height: 60px;
  }

  .node-content {
    padding: 6px;
  }

  .node-title {
    font-size: 11px;
  }

  .node-description {
    font-size: 9px;
  }
}

/* 动画效果 */
@keyframes nodeAppear {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.workflow-node {
  animation: nodeAppear 0.3s ease-out;
}

/* 连接点悬停效果 */
.connection-point::before {
  content: '';
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-radius: 50%;
  background: rgba(0, 123, 255, 0.1);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.connection-point:hover::before,
.connection-point.active::before {
  opacity: 1;
}
</style>
