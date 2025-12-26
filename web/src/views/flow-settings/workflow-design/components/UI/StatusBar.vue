<template>
  <div class="status-bar">
    <!-- 左侧状态信息 -->
    <div class="status-left">
      <!-- 工作流状态 -->
      <div class="workflow-status status-item">
        <span class="status-icon" :class="workflowStatusClass">{{ workflowStatusIcon }}</span>
        <span class="status-text">{{ workflowStatusText }}</span>
      </div>

      <!-- 分隔符 -->
      <div class="separator"></div>

      <!-- 节点统计 -->
      <div class="status-item nodes-count">
        <span class="icon">📦</span>
        <span class="text">节点: {{ stats.nodeCount }}</span>
      </div>

      <!-- 连接统计 -->
      <div class="status-item connections-count">
        <span class="icon">🔗</span>
        <span class="text">连接: {{ stats.connectionCount }}</span>
      </div>

      <!-- 选择统计 -->
      <div v-if="stats.selectedCount > 0" class="status-item selection-count">
        <span class="icon">✅</span>
        <span class="text">已选: {{ stats.selectedCount }}</span>
      </div>

      <!-- 分隔符 -->
      <div class="separator"></div>

      <!-- 验证状态 -->
      <div class="status-item validation-status" :class="validationStatusClass">
        <span class="icon">{{ validationIcon }}</span>
        <span class="text">{{ validationText }}</span>
        <span v-if="validation && !validation.isValid" class="error-count">
          {{ validation.errors.length }}
        </span>
      </div>
    </div>

    <!-- 中间操作提示 -->
    <div class="status-center">
      <div v-if="currentAction" class="action-hint">
        <span class="action-icon">{{ currentAction.icon }}</span>
        <span class="action-text">{{ currentAction.text }}</span>
        <span v-if="currentAction.shortcut" class="action-shortcut">
          {{ currentAction.shortcut }}
        </span>
      </div>

      <!-- 拖拽提示 -->
      <div v-if="isDragging" class="drag-hint">
        <span class="icon">🖱️</span>
        <span class="text">{{ dragHintText }}</span>
      </div>

      <!-- 连接提示 -->
      <div v-if="isConnecting" class="connect-hint">
        <span class="icon">🔗</span>
        <span class="text">{{ connectHintText }}</span>
      </div>
    </div>

    <!-- 右侧信息 -->
    <div class="status-right">
      <!-- 缩放信息 -->
      <div class="status-item zoom-info">
        <span class="icon">🔍</span>
        <span class="text">{{ Math.round(scale * 100) }}%</span>
      </div>

      <!-- 分隔符 -->
      <div class="separator"></div>

      <!-- 画布位置 -->
      <div class="status-item canvas-position">
        <span class="icon">📍</span>
        <span class="text">{{ canvasPositionText }}</span>
      </div>

      <!-- 分隔符 -->
      <div class="separator"></div>

      <!-- 网格状态 -->
      <div class="status-item grid-status" :class="{ active: showGrid }">
        <span class="icon">⚏</span>
        <span class="text">网格</span>
      </div>

      <!-- 对齐状态 -->
      <div class="status-item snap-status" :class="{ active: snapToGrid }">
        <span class="icon">🧲</span>
        <span class="text">对齐</span>
      </div>

      <!-- 分隔符 -->
      <div class="separator"></div>

      <!-- 性能信息 -->
      <div v-if="showPerformance" class="status-item performance-info">
        <span class="icon">⚡</span>
        <span class="text">{{ performanceText }}</span>
      </div>

      <!-- 保存状态 -->
      <div class="status-item save-status" :class="saveStatusClass">
        <span class="icon">{{ saveStatusIcon }}</span>
        <span class="text">{{ saveStatusText }}</span>
      </div>

      <!-- 时间信息 -->
      <div class="status-item time-info">
        <span class="icon">🕐</span>
        <span class="text">{{ currentTime }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Props
const props = defineProps({
  // 工作流状态
  workflowStatus: {
    type: String,
    default: 'idle', // idle, running, success, error
  },

  // 统计信息
  stats: {
    type: Object,
    default: () => ({
      nodeCount: 0,
      connectionCount: 0,
      selectedCount: 0,
    }),
  },

  // 验证结果
  validation: {
    type: Object,
    default: null,
  },

  // 当前操作
  currentAction: {
    type: Object,
    default: null,
  },

  // 拖拽状态
  isDragging: {
    type: Boolean,
    default: false,
  },

  // 连接状态
  isConnecting: {
    type: Boolean,
    default: false,
  },

  // 缩放比例
  scale: {
    type: Number,
    default: 1,
  },

  // 画布位置
  canvasPosition: {
    type: Object,
    default: () => ({ x: 0, y: 0 }),
  },

  // 网格显示
  showGrid: {
    type: Boolean,
    default: true,
  },

  // 网格对齐
  snapToGrid: {
    type: Boolean,
    default: true,
  },

  // 保存状态
  saveStatus: {
    type: String,
    default: 'saved', // saved, saving, unsaved, error
  },

  // 显示性能信息
  showPerformance: {
    type: Boolean,
    default: false,
  },

  // 性能数据
  performance: {
    type: Object,
    default: () => ({
      fps: 60,
      renderTime: 0,
    }),
  },
})

// 响应式数据
const currentTime = ref('')

// 计算属性
const workflowStatusClass = computed(() => {
  return `status-${props.workflowStatus}`
})

const workflowStatusIcon = computed(() => {
  const icons = {
    idle: '⏸️',
    running: '▶️',
    success: '✅',
    error: '❌',
    warning: '⚠️',
  }
  return icons[props.workflowStatus] || '⏸️'
})

const workflowStatusText = computed(() => {
  const texts = {
    idle: '空闲',
    running: '运行中',
    success: '成功',
    error: '错误',
    warning: '警告',
  }
  return texts[props.workflowStatus] || '未知'
})

const validationStatusClass = computed(() => {
  if (!props.validation) return 'status-unknown'
  return props.validation.isValid ? 'status-valid' : 'status-invalid'
})

const validationIcon = computed(() => {
  if (!props.validation) return '❓'
  return props.validation.isValid ? '✅' : '❌'
})

const validationText = computed(() => {
  if (!props.validation) return '未验证'
  return props.validation.isValid ? '验证通过' : '验证失败'
})

const dragHintText = computed(() => {
  return '拖拽移动节点 | 按住 Shift 复制 | 按 Esc 取消'
})

const connectHintText = computed(() => {
  return '点击目标连接点完成连接 | 按 Esc 取消'
})

const canvasPositionText = computed(() => {
  const x = Math.round(props.canvasPosition.x)
  const y = Math.round(props.canvasPosition.y)
  return `${x}, ${y}`
})

const saveStatusClass = computed(() => {
  return `save-${props.saveStatus}`
})

const saveStatusIcon = computed(() => {
  const icons = {
    saved: '💾',
    saving: '⏳',
    unsaved: '📝',
    error: '❌',
  }
  return icons[props.saveStatus] || '💾'
})

const saveStatusText = computed(() => {
  const texts = {
    saved: '已保存',
    saving: '保存中',
    unsaved: '未保存',
    error: '保存失败',
  }
  return texts[props.saveStatus] || '未知'
})

const performanceText = computed(() => {
  const fps = Math.round(props.performance.fps)
  const renderTime = Math.round(props.performance.renderTime * 100) / 100
  return `${fps}fps ${renderTime}ms`
})

// 方法
function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

// 生命周期
let timeInterval = null

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 32px;
  padding: 0 16px;
  background: #fafafa;
  border-top: 1px solid #e8e8e8;
  font-size: 12px;
  color: #595959;
  user-select: none;
}

.status-left,
.status-center,
.status-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-center {
  flex: 1;
  justify-content: center;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 3px;
  transition: all 0.15s ease;
}

.status-item.active {
  background: #e6f7ff;
  color: #1890ff;
}

.status-item .icon {
  font-size: 12px;
  flex-shrink: 0;
}

.status-item .text {
  font-size: 12px;
  white-space: nowrap;
}

.separator {
  width: 1px;
  height: 16px;
  background: #d9d9d9;
  margin: 0 4px;
}

/* 工作流状态样式 */
.workflow-status {
  font-weight: 500;
}

.workflow-status.status-idle {
  color: #8c8c8c;
}

.workflow-status.status-running {
  color: #1890ff;
  background: #e6f7ff;
}

.workflow-status.status-success {
  color: #52c41a;
  background: #f6ffed;
}

.workflow-status.status-error {
  color: #ff4d4f;
  background: #fff2f0;
}

.workflow-status.status-warning {
  color: #fa8c16;
  background: #fff7e6;
}

/* 验证状态样式 */
.validation-status.status-valid {
  color: #52c41a;
}

.validation-status.status-invalid {
  color: #ff4d4f;
}

.validation-status.status-unknown {
  color: #8c8c8c;
}

.error-count {
  background: #ff4d4f;
  color: white;
  border-radius: 8px;
  padding: 1px 4px;
  font-size: 10px;
  font-weight: bold;
  min-width: 14px;
  text-align: center;
  margin-left: 4px;
}

/* 操作提示样式 */
.action-hint,
.drag-hint,
.connect-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  color: #1890ff;
  font-weight: 500;
}

.action-shortcut {
  background: #1890ff;
  color: white;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: bold;
}

.drag-hint {
  background: #fff7e6;
  border-color: #ffd591;
  color: #fa8c16;
}

.connect-hint {
  background: #f6ffed;
  border-color: #b7eb8f;
  color: #52c41a;
}

/* 保存状态样式 */
.save-status.save-saved {
  color: #52c41a;
}

.save-status.save-saving {
  color: #1890ff;
  background: #e6f7ff;
}

.save-status.save-unsaved {
  color: #fa8c16;
  background: #fff7e6;
}

.save-status.save-error {
  color: #ff4d4f;
  background: #fff2f0;
}

/* 性能信息样式 */
.performance-info {
  font-family: 'Courier New', monospace;
  background: #f0f0f0;
  border-radius: 3px;
  padding: 2px 6px;
}

/* 时间信息样式 */
.time-info {
  font-family: 'Courier New', monospace;
  color: #8c8c8c;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .performance-info {
    display: none;
  }
}

@media (max-width: 900px) {
  .canvas-position,
  .time-info {
    display: none;
  }
}

@media (max-width: 600px) {
  .status-bar {
    padding: 0 8px;
    gap: 4px;
  }

  .separator {
    display: none;
  }

  .status-item .text {
    display: none;
  }

  .action-hint .action-text,
  .drag-hint .text,
  .connect-hint .text {
    display: none;
  }
}

/* 动画效果 */
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.workflow-status.status-running .status-icon,
.save-status.save-saving .icon {
  animation: pulse 1.5s infinite;
}

/* 悬停效果 */
.status-item:hover {
  background: #f0f0f0;
  cursor: default;
}

.grid-status:hover,
.snap-status:hover {
  cursor: pointer;
  background: #e6f7ff;
  color: #1890ff;
}

/* 工具提示 */
.status-item[title] {
  cursor: help;
}
</style>
