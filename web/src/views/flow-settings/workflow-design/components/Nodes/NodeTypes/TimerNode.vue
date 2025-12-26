<template>
  <div
    :class="[
      'timer-node',
      {
        selected: isSelected,
        hovered: isHovered,
        dragging: isDragging,
        error: hasError,
        warning: hasWarning,
        running: isRunning,
        paused: isPaused,
      },
    ]"
    :style="nodeStyle"
    @mousedown="handleMouseDown"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @contextmenu="handleContextMenu"
  >
    <!-- 节点头部 -->
    <div class="node-header">
      <div class="node-icon">
        <i class="icon-timer"></i>
      </div>
      <div class="node-title">
        <span class="node-label">{{ nodeData.label || '定时器' }}</span>
        <span class="node-type">{{ getTimerTypeLabel(nodeData.timerType) }}</span>
      </div>
      <div class="node-status">
        <div v-if="hasError" class="status-indicator error" title="错误">
          <i class="icon-exclamation-circle"></i>
        </div>
        <div v-else-if="hasWarning" class="status-indicator warning" title="警告">
          <i class="icon-exclamation-triangle"></i>
        </div>
        <div v-else-if="isRunning" class="status-indicator running" title="运行中">
          <i class="icon-play"></i>
        </div>
        <div v-else-if="isPaused" class="status-indicator paused" title="已暂停">
          <i class="icon-pause"></i>
        </div>
        <div v-else class="status-indicator ready" title="就绪">
          <i class="icon-clock"></i>
        </div>
      </div>
    </div>

    <!-- 节点内容 -->
    <div class="node-content">
      <div class="timer-info">
        <div class="timer-config">
          <div class="config-item">
            <span class="config-label">间隔:</span>
            <span class="config-value">{{ formatInterval(nodeData.interval) }}</span>
          </div>
          <div v-if="nodeData.timerType === 'cron'" class="config-item">
            <span class="config-label">Cron:</span>
            <span class="config-value cron">{{ nodeData.cronExpression || '* * * * *' }}</span>
          </div>
          <div v-if="nodeData.repeat" class="config-item">
            <span class="config-label">重复:</span>
            <span class="config-value">{{ formatRepeat(nodeData.repeat) }}</span>
          </div>
        </div>
      </div>

      <div v-if="nodeData.description" class="node-description">
        {{ nodeData.description }}
      </div>

      <!-- 执行状态 -->
      <div v-if="executionInfo" class="execution-info">
        <div class="execution-item">
          <span class="execution-label">下次执行:</span>
          <span class="execution-value">{{
            formatNextExecution(executionInfo.nextExecution)
          }}</span>
        </div>
        <div v-if="executionInfo.lastExecution" class="execution-item">
          <span class="execution-label">上次执行:</span>
          <span class="execution-value">{{
            formatLastExecution(executionInfo.lastExecution)
          }}</span>
        </div>
        <div v-if="executionInfo.executionCount" class="execution-item">
          <span class="execution-label">执行次数:</span>
          <span class="execution-value">{{ executionInfo.executionCount }}</span>
        </div>
      </div>

      <!-- 进度条 -->
      <div v-if="showProgress && progressInfo" class="progress-info">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progressInfo.percentage}%` }"></div>
        </div>
        <div class="progress-text">
          {{ progressInfo.text }}
        </div>
      </div>
    </div>

    <!-- 连接点 -->
    <ConnectionPoint
      v-for="point in connectionPoints.inputs"
      :key="point.id"
      :type="'input'"
      :position="point.position"
      :label="point.label"
      :data-type="point.dataType"
      :color="point.color"
      :active="activeConnections.includes(point.id)"
      :connected="connectedPoints.includes(point.id)"
      :hover="hoveredPoint === point.id"
      :compatible="compatiblePoints.includes(point.id)"
      :incompatible="incompatiblePoints.includes(point.id)"
      :connection-count="getConnectionCount(point.id)"
      :show-label="showConnectionLabels"
      :show-data-type="showDataTypes"
      :offset="getConnectionPointOffset(point.position)"
      @mousedown="handleConnectionMouseDown(point, $event)"
      @mouseenter="handleConnectionMouseEnter(point)"
      @mouseleave="handleConnectionMouseLeave(point)"
      @click="handleConnectionClick(point, $event)"
    />

    <ConnectionPoint
      v-for="point in connectionPoints.outputs"
      :key="point.id"
      :type="'output'"
      :position="point.position"
      :label="point.label"
      :data-type="point.dataType"
      :color="point.color"
      :active="activeConnections.includes(point.id)"
      :connected="connectedPoints.includes(point.id)"
      :hover="hoveredPoint === point.id"
      :compatible="compatiblePoints.includes(point.id)"
      :incompatible="incompatiblePoints.includes(point.id)"
      :connection-count="getConnectionCount(point.id)"
      :show-label="showConnectionLabels"
      :show-data-type="showDataTypes"
      :offset="getConnectionPointOffset(point.position)"
      @mousedown="handleConnectionMouseDown(point, $event)"
      @mouseenter="handleConnectionMouseEnter(point)"
      @mouseleave="handleConnectionMouseLeave(point)"
      @click="handleConnectionClick(point, $event)"
    />

    <!-- 调整大小手柄 -->
    <div v-if="isSelected && allowResize" class="resize-handles">
      <div
        v-for="handle in resizeHandles"
        :key="handle.position"
        :class="['resize-handle', handle.position]"
        @mousedown="handleResizeMouseDown(handle, $event)"
      ></div>
    </div>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import ConnectionPoint from '../../Connections/ConnectionPoint.vue'

export default {
  name: 'TimerNode',
  components: {
    ConnectionPoint,
  },
  props: {
    // 节点数据
    nodeData: {
      type: Object,
      required: true,
    },
    // 节点位置
    position: {
      type: Object,
      default: () => ({ x: 0, y: 0 }),
    },
    // 节点大小
    size: {
      type: Object,
      default: () => ({ width: 180, height: 140 }),
    },
    // 选中状态
    isSelected: {
      type: Boolean,
      default: false,
    },
    // 悬停状态
    isHovered: {
      type: Boolean,
      default: false,
    },
    // 拖拽状态
    isDragging: {
      type: Boolean,
      default: false,
    },
    // 错误状态
    hasError: {
      type: Boolean,
      default: false,
    },
    // 警告状态
    hasWarning: {
      type: Boolean,
      default: false,
    },
    // 运行状态
    isRunning: {
      type: Boolean,
      default: false,
    },
    // 暂停状态
    isPaused: {
      type: Boolean,
      default: false,
    },
    // 执行信息
    executionInfo: {
      type: Object,
      default: null,
    },
    // 进度信息
    progressInfo: {
      type: Object,
      default: null,
    },
    // 显示进度
    showProgress: {
      type: Boolean,
      default: false,
    },
    // 连接点配置
    connectionPoints: {
      type: Object,
      default: () => ({
        inputs: [
          { id: 'start', label: '启动', position: 'left', dataType: 'trigger', color: '#52c41a' },
          { id: 'stop', label: '停止', position: 'left', dataType: 'trigger', color: '#ff4d4f' },
        ],
        outputs: [
          { id: 'tick', label: '触发', position: 'right', dataType: 'trigger', color: '#1890ff' },
          {
            id: 'complete',
            label: '完成',
            position: 'bottom',
            dataType: 'trigger',
            color: '#52c41a',
          },
        ],
      }),
    },
    // 活跃连接
    activeConnections: {
      type: Array,
      default: () => [],
    },
    // 已连接的点
    connectedPoints: {
      type: Array,
      default: () => [],
    },
    // 悬停的连接点
    hoveredPoint: {
      type: String,
      default: null,
    },
    // 兼容的连接点
    compatiblePoints: {
      type: Array,
      default: () => [],
    },
    // 不兼容的连接点
    incompatiblePoints: {
      type: Array,
      default: () => [],
    },
    // 显示连接标签
    showConnectionLabels: {
      type: Boolean,
      default: true,
    },
    // 显示数据类型
    showDataTypes: {
      type: Boolean,
      default: false,
    },
    // 允许调整大小
    allowResize: {
      type: Boolean,
      default: true,
    },
  },
  emits: [
    'mousedown',
    'mouseenter',
    'mouseleave',
    'contextmenu',
    'connection-mousedown',
    'connection-mouseenter',
    'connection-mouseleave',
    'connection-click',
    'resize-mousedown',
  ],
  setup(props, { emit }) {
    // 调整大小手柄
    const resizeHandles = ref([
      { position: 'top-left', cursor: 'nw-resize' },
      { position: 'top-right', cursor: 'ne-resize' },
      { position: 'bottom-left', cursor: 'sw-resize' },
      { position: 'bottom-right', cursor: 'se-resize' },
    ])

    // 节点样式
    const nodeStyle = computed(() => ({
      left: `${props.position.x}px`,
      top: `${props.position.y}px`,
      width: `${props.size.width}px`,
      height: `${props.size.height}px`,
    }))

    // 获取定时器类型标签
    const getTimerTypeLabel = (timerType) => {
      const typeMap = {
        interval: '间隔定时器',
        timeout: '延时定时器',
        cron: 'Cron定时器',
        schedule: '计划任务',
      }
      return typeMap[timerType] || 'Timer'
    }

    // 格式化间隔时间
    const formatInterval = (interval) => {
      if (!interval) return '未设置'

      if (typeof interval === 'number') {
        if (interval < 1000) return `${interval}ms`
        if (interval < 60000) return `${Math.round(interval / 1000)}s`
        if (interval < 3600000) return `${Math.round(interval / 60000)}m`
        return `${Math.round(interval / 3600000)}h`
      }

      return interval.toString()
    }

    // 格式化重复次数
    const formatRepeat = (repeat) => {
      if (repeat === -1 || repeat === Infinity) return '无限'
      if (repeat === 1) return '一次'
      return `${repeat}次`
    }

    // 格式化下次执行时间
    const formatNextExecution = (nextExecution) => {
      if (!nextExecution) return '未知'

      const now = new Date()
      const next = new Date(nextExecution)
      const diff = next.getTime() - now.getTime()

      if (diff < 0) return '已过期'
      if (diff < 60000) return `${Math.round(diff / 1000)}秒后`
      if (diff < 3600000) return `${Math.round(diff / 60000)}分钟后`
      if (diff < 86400000) return `${Math.round(diff / 3600000)}小时后`

      return next.toLocaleString()
    }

    // 格式化上次执行时间
    const formatLastExecution = (lastExecution) => {
      if (!lastExecution) return '从未执行'

      const now = new Date()
      const last = new Date(lastExecution)
      const diff = now.getTime() - last.getTime()

      if (diff < 60000) return `${Math.round(diff / 1000)}秒前`
      if (diff < 3600000) return `${Math.round(diff / 60000)}分钟前`
      if (diff < 86400000) return `${Math.round(diff / 3600000)}小时前`

      return last.toLocaleString()
    }

    // 获取连接点偏移
    const getConnectionPointOffset = (position) => {
      const offsetMap = {
        left: { x: -8, y: 0 },
        right: { x: 8, y: 0 },
        top: { x: 0, y: -8 },
        bottom: { x: 0, y: 8 },
      }
      return offsetMap[position] || { x: 0, y: 0 }
    }

    // 获取连接数量
    const getConnectionCount = (pointId) => {
      return props.connectedPoints.filter((id) => id === pointId).length
    }

    // 事件处理
    const handleMouseDown = (event) => {
      emit('mousedown', event)
    }

    const handleMouseEnter = (event) => {
      emit('mouseenter', event)
    }

    const handleMouseLeave = (event) => {
      emit('mouseleave', event)
    }

    const handleContextMenu = (event) => {
      event.preventDefault()
      emit('contextmenu', event)
    }

    const handleConnectionMouseDown = (point, event) => {
      event.stopPropagation()
      emit('connection-mousedown', { point, event })
    }

    const handleConnectionMouseEnter = (point) => {
      emit('connection-mouseenter', point)
    }

    const handleConnectionMouseLeave = (point) => {
      emit('connection-mouseleave', point)
    }

    const handleConnectionClick = (point, event) => {
      event.stopPropagation()
      emit('connection-click', { point, event })
    }

    const handleResizeMouseDown = (handle, event) => {
      event.stopPropagation()
      emit('resize-mousedown', { handle, event })
    }

    return {
      resizeHandles,
      nodeStyle,
      getTimerTypeLabel,
      formatInterval,
      formatRepeat,
      formatNextExecution,
      formatLastExecution,
      getConnectionPointOffset,
      getConnectionCount,
      handleMouseDown,
      handleMouseEnter,
      handleMouseLeave,
      handleContextMenu,
      handleConnectionMouseDown,
      handleConnectionMouseEnter,
      handleConnectionMouseLeave,
      handleConnectionClick,
      handleResizeMouseDown,
    }
  },
}
</script>

<style lang="scss" scoped>
.timer-node {
  position: absolute;
  background: #ffffff;
  border: 2px solid #fa8c16;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  user-select: none;
  transition: all 0.2s ease;
  min-width: 180px;
  min-height: 140px;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transform: translateY(-1px);
  }

  &.selected {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }

  &.hovered {
    border-color: #40a9ff;
  }

  &.dragging {
    opacity: 0.8;
    transform: rotate(2deg);
  }

  &.error {
    border-color: #ff4d4f;
    background: #fff2f0;
  }

  &.warning {
    border-color: #faad14;
    background: #fffbe6;
  }

  &.running {
    border-color: #52c41a;
    animation: pulse 2s infinite;
  }

  &.paused {
    border-color: #faad14;
    opacity: 0.8;
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(82, 196, 26, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(82, 196, 26, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(82, 196, 26, 0);
  }
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(135deg, #fa8c16, #ffa940);
  color: white;
  border-radius: 6px 6px 0 0;
  min-height: 36px;

  .node-icon {
    margin-right: 8px;
    font-size: 16px;

    .icon-timer::before {
      content: '⏰';
    }
  }

  .node-title {
    flex: 1;
    min-width: 0;

    .node-label {
      display: block;
      font-weight: 600;
      font-size: 12px;
      line-height: 1.2;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .node-type {
      display: block;
      font-size: 10px;
      opacity: 0.8;
      line-height: 1;
    }
  }

  .node-status {
    margin-left: 8px;

    .status-indicator {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;

      &.ready {
        background: #d9d9d9;
        color: #666;
      }

      &.running {
        background: #52c41a;
        color: white;
        animation: spin 1s linear infinite;
      }

      &.paused {
        background: #faad14;
        color: white;
      }

      &.warning {
        background: #faad14;
        color: white;
      }

      &.error {
        background: #ff4d4f;
        color: white;
      }
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.node-content {
  padding: 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .timer-info {
    .timer-config {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .config-item {
        display: flex;
        align-items: center;
        font-size: 11px;

        .config-label {
          color: #666;
          margin-right: 6px;
          min-width: 40px;
        }

        .config-value {
          flex: 1;
          font-weight: 500;
          color: #333;

          &.cron {
            font-family: monospace;
            background: #f5f5f5;
            padding: 1px 4px;
            border-radius: 2px;
          }
        }
      }
    }
  }

  .node-description {
    font-size: 11px;
    color: #666;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .execution-info {
    background: #f9f9f9;
    border-radius: 4px;
    padding: 6px;
    font-size: 10px;

    .execution-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 2px;

      &:last-child {
        margin-bottom: 0;
      }

      .execution-label {
        color: #999;
      }

      .execution-value {
        color: #333;
        font-weight: 500;
      }
    }
  }

  .progress-info {
    .progress-bar {
      width: 100%;
      height: 4px;
      background: #f0f0f0;
      border-radius: 2px;
      overflow: hidden;
      margin-bottom: 4px;

      .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #fa8c16, #ffa940);
        transition: width 0.3s ease;
      }
    }

    .progress-text {
      font-size: 10px;
      color: #666;
      text-align: center;
    }
  }
}

.resize-handles {
  .resize-handle {
    position: absolute;
    width: 8px;
    height: 8px;
    background: #1890ff;
    border: 1px solid #ffffff;
    border-radius: 2px;
    z-index: 10;

    &.top-left {
      top: -4px;
      left: -4px;
      cursor: nw-resize;
    }

    &.top-right {
      top: -4px;
      right: -4px;
      cursor: ne-resize;
    }

    &.bottom-left {
      bottom: -4px;
      left: -4px;
      cursor: sw-resize;
    }

    &.bottom-right {
      bottom: -4px;
      right: -4px;
      cursor: se-resize;
    }

    &:hover {
      background: #40a9ff;
      transform: scale(1.2);
    }
  }
}

// 图标样式
.icon-exclamation-circle::before {
  content: '⚠️';
}

.icon-exclamation-triangle::before {
  content: '⚠️';
}

.icon-play::before {
  content: '▶️';
}

.icon-pause::before {
  content: '⏸️';
}

.icon-clock::before {
  content: '🕐';
}
</style>
