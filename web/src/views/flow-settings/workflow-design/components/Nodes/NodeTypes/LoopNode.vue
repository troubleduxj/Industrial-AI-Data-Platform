<template>
  <div
    :class="[
      'loop-node',
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
        <i class="icon-loop"></i>
      </div>
      <div class="node-title">
        <span class="node-label">{{ nodeData.label || '循环' }}</span>
        <span class="node-type">{{ getLoopTypeLabel(nodeData.loopType) }}</span>
      </div>
      <div class="node-status">
        <div v-if="hasError" class="status-indicator error" title="错误">
          <i class="icon-exclamation-circle"></i>
        </div>
        <div v-else-if="hasWarning" class="status-indicator warning" title="警告">
          <i class="icon-exclamation-triangle"></i>
        </div>
        <div v-else-if="isRunning" class="status-indicator running" title="运行中">
          <i class="icon-running"></i>
        </div>
        <div v-else-if="isPaused" class="status-indicator paused" title="已暂停">
          <i class="icon-paused"></i>
        </div>
        <div v-else class="status-indicator ready" title="就绪">
          <i class="icon-check-circle"></i>
        </div>
      </div>
    </div>

    <!-- 节点内容 -->
    <div class="node-content">
      <div class="loop-info">
        <div class="loop-type" :class="nodeData.loopType?.toLowerCase()">
          {{ getLoopTypeLabel(nodeData.loopType) }}
        </div>

        <!-- For 循环 -->
        <div v-if="nodeData.loopType === 'for'" class="for-loop">
          <div class="loop-config">
            <div class="config-item">
              <span class="config-label">起始:</span>
              <span class="config-value">{{ nodeData.startValue || 0 }}</span>
            </div>
            <div class="config-item">
              <span class="config-label">结束:</span>
              <span class="config-value">{{ nodeData.endValue || 10 }}</span>
            </div>
            <div class="config-item">
              <span class="config-label">步长:</span>
              <span class="config-value">{{ nodeData.stepValue || 1 }}</span>
            </div>
          </div>
        </div>

        <!-- While 循环 -->
        <div v-else-if="nodeData.loopType === 'while'" class="while-loop">
          <div class="condition-info">
            <span class="condition-label">条件:</span>
            <span class="condition-value">{{ formatCondition(nodeData.condition) }}</span>
          </div>
        </div>

        <!-- ForEach 循环 -->
        <div v-else-if="nodeData.loopType === 'forEach'" class="foreach-loop">
          <div class="collection-info">
            <span class="collection-label">集合:</span>
            <span class="collection-value">{{ formatCollection(nodeData.collection) }}</span>
          </div>
          <div v-if="nodeData.itemVariable" class="variable-info">
            <span class="variable-label">变量:</span>
            <span class="variable-value">{{ nodeData.itemVariable }}</span>
          </div>
        </div>

        <!-- DoWhile 循环 -->
        <div v-else-if="nodeData.loopType === 'doWhile'" class="dowhile-loop">
          <div class="condition-info">
            <span class="condition-label">条件:</span>
            <span class="condition-value">{{ formatCondition(nodeData.condition) }}</span>
          </div>
          <div class="execution-note">至少执行一次</div>
        </div>
      </div>

      <div v-if="nodeData.description" class="node-description">
        {{ nodeData.description }}
      </div>

      <!-- 执行信息 -->
      <div v-if="executionInfo" class="execution-info">
        <div class="execution-header">
          <span class="execution-label">执行状态:</span>
          <span :class="['execution-status', executionInfo.status]">
            {{ getExecutionStatusLabel(executionInfo.status) }}
          </span>
        </div>
        <div class="execution-details">
          <div class="detail-item">
            <span class="detail-label">当前迭代:</span>
            <span class="detail-value">{{ executionInfo.currentIteration || 0 }}</span>
          </div>
          <div v-if="executionInfo.totalIterations" class="detail-item">
            <span class="detail-label">总迭代数:</span>
            <span class="detail-value">{{ executionInfo.totalIterations }}</span>
          </div>
          <div v-if="executionInfo.executionTime" class="detail-item">
            <span class="detail-label">执行时间:</span>
            <span class="detail-value">{{ formatExecutionTime(executionInfo.executionTime) }}</span>
          </div>
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

      <!-- 循环控制 -->
      <div class="loop-controls">
        <div class="control-item">
          <i class="icon-max-iterations"></i>
          <span class="control-label">最大迭代:</span>
          <span class="control-value">{{ nodeData.maxIterations || '无限制' }}</span>
        </div>
        <div v-if="nodeData.breakCondition" class="control-item">
          <i class="icon-break"></i>
          <span class="control-label">中断条件:</span>
          <span class="control-value">{{ formatCondition(nodeData.breakCondition) }}</span>
        </div>
        <div v-if="nodeData.continueCondition" class="control-item">
          <i class="icon-continue"></i>
          <span class="control-label">跳过条件:</span>
          <span class="control-value">{{ formatCondition(nodeData.continueCondition) }}</span>
        </div>
      </div>

      <!-- 性能信息 -->
      <div v-if="performanceInfo" class="performance-info">
        <div class="performance-item">
          <span class="performance-label">平均迭代时间:</span>
          <span class="performance-value">{{ performanceInfo.avgIterationTime }}ms</span>
        </div>
        <div v-if="performanceInfo.memoryUsage" class="performance-item">
          <span class="performance-label">内存使用:</span>
          <span class="performance-value">{{
            formatMemoryUsage(performanceInfo.memoryUsage)
          }}</span>
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
  name: 'LoopNode',
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
      default: () => ({ width: 220, height: 180 }),
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
    // 性能信息
    performanceInfo: {
      type: Object,
      default: null,
    },
    // 连接点配置
    connectionPoints: {
      type: Object,
      default: () => ({
        inputs: [
          { id: 'trigger', label: '触发', position: 'left', dataType: 'trigger', color: '#1890ff' },
          { id: 'data', label: '数据', position: 'left', dataType: 'any', color: '#52c41a' },
        ],
        outputs: [
          {
            id: 'body',
            label: '循环体',
            position: 'bottom',
            dataType: 'trigger',
            color: '#1890ff',
          },
          {
            id: 'complete',
            label: '完成',
            position: 'right',
            dataType: 'trigger',
            color: '#52c41a',
          },
          { id: 'break', label: '中断', position: 'right', dataType: 'trigger', color: '#ff4d4f' },
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

    // 获取循环类型标签
    const getLoopTypeLabel = (type) => {
      const typeMap = {
        for: 'For 循环',
        while: 'While 循环',
        forEach: 'ForEach 循环',
        doWhile: 'DoWhile 循环',
        repeat: '重复循环',
        infinite: '无限循环',
      }
      return typeMap[type] || 'Loop'
    }

    // 获取执行状态标签
    const getExecutionStatusLabel = (status) => {
      const statusMap = {
        idle: '空闲',
        running: '运行中',
        paused: '已暂停',
        completed: '已完成',
        error: '错误',
        cancelled: '已取消',
      }
      return statusMap[status] || status
    }

    // 格式化条件
    const formatCondition = (condition) => {
      if (!condition) return '未设置'
      if (typeof condition === 'string') return condition
      if (condition.expression) return condition.expression
      if (condition.leftOperand && condition.operator && condition.rightOperand) {
        return `${condition.leftOperand} ${condition.operator} ${condition.rightOperand}`
      }
      return JSON.stringify(condition)
    }

    // 格式化集合
    const formatCollection = (collection) => {
      if (!collection) return '未设置'
      if (typeof collection === 'string') return collection
      if (Array.isArray(collection)) return `[${collection.length} 项]`
      if (collection.source) return collection.source
      if (collection.path) return collection.path
      return JSON.stringify(collection)
    }

    // 格式化执行时间
    const formatExecutionTime = (time) => {
      if (time < 1000) return `${time}ms`
      if (time < 60000) return `${(time / 1000).toFixed(1)}s`
      return `${Math.floor(time / 60000)}m ${Math.floor((time % 60000) / 1000)}s`
    }

    // 格式化内存使用
    const formatMemoryUsage = (usage) => {
      if (usage < 1024) return `${usage} B`
      if (usage < 1024 * 1024) return `${(usage / 1024).toFixed(1)} KB`
      if (usage < 1024 * 1024 * 1024) return `${(usage / (1024 * 1024)).toFixed(1)} MB`
      return `${(usage / (1024 * 1024 * 1024)).toFixed(1)} GB`
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
      getLoopTypeLabel,
      getExecutionStatusLabel,
      formatCondition,
      formatCollection,
      formatExecutionTime,
      formatMemoryUsage,
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
.loop-node {
  position: absolute;
  background: #ffffff;
  border: 2px solid #722ed1;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  user-select: none;
  transition: all 0.2s ease;
  min-width: 220px;
  min-height: 180px;

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
    border-color: #1890ff;
    animation: running 2s infinite;
  }

  &.paused {
    border-color: #faad14;
    animation: paused 1s infinite;
  }
}

@keyframes running {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(24, 144, 255, 0);
  }
}

@keyframes paused {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(135deg, #722ed1, #9254de);
  color: white;
  border-radius: 6px 6px 0 0;
  min-height: 36px;

  .node-icon {
    margin-right: 8px;
    font-size: 16px;

    .icon-loop::before {
      content: '🔄';
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
        background: #52c41a;
        color: white;
      }

      &.running {
        background: #1890ff;
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

  .loop-info {
    .loop-type {
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      color: white;
      display: inline-block;
      margin-bottom: 8px;

      &.for {
        background: #52c41a;
      }

      &.while {
        background: #1890ff;
      }

      &.foreach {
        background: #13c2c2;
      }

      &.dowhile {
        background: #fa8c16;
      }

      &.repeat {
        background: #eb2f96;
      }

      &.infinite {
        background: #722ed1;
      }
    }

    .for-loop {
      .loop-config {
        background: #f9f9f9;
        border-radius: 4px;
        padding: 6px 8px;
        border: 1px solid #e8e8e8;

        .config-item {
          display: flex;
          justify-content: space-between;
          font-size: 11px;
          margin-bottom: 3px;

          &:last-child {
            margin-bottom: 0;
          }

          .config-label {
            color: #666;
            font-weight: 500;
          }

          .config-value {
            color: #333;
            font-weight: 600;
            font-family: monospace;
          }
        }
      }
    }

    .while-loop,
    .dowhile-loop {
      .condition-info {
        background: #f0f9ff;
        border: 1px solid #e6f7ff;
        border-radius: 4px;
        padding: 6px 8px;
        font-size: 11px;

        .condition-label {
          color: #1890ff;
          font-weight: 600;
          margin-right: 6px;
        }

        .condition-value {
          color: #333;
          font-family: monospace;
          word-break: break-all;
        }
      }

      .execution-note {
        font-size: 9px;
        color: #999;
        font-style: italic;
        text-align: center;
        margin-top: 4px;
      }
    }

    .foreach-loop {
      .collection-info,
      .variable-info {
        display: flex;
        align-items: center;
        font-size: 11px;
        margin-bottom: 4px;

        &:last-child {
          margin-bottom: 0;
        }

        .collection-label,
        .variable-label {
          color: #666;
          margin-right: 6px;
          min-width: 40px;
        }

        .collection-value,
        .variable-value {
          color: #333;
          font-weight: 500;
          font-family: monospace;
          flex: 1;
          word-break: break-all;
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
    background: #f0f9ff;
    border: 1px solid #e6f7ff;
    border-radius: 4px;
    padding: 6px 8px;

    .execution-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;

      .execution-label {
        font-size: 10px;
        color: #1890ff;
        font-weight: 600;
      }

      .execution-status {
        font-size: 10px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 3px;

        &.idle {
          background: #f5f5f5;
          color: #999;
        }

        &.running {
          background: #e6f7ff;
          color: #1890ff;
        }

        &.paused {
          background: #fff7e6;
          color: #fa8c16;
        }

        &.completed {
          background: #f6ffed;
          color: #52c41a;
        }

        &.error {
          background: #fff2f0;
          color: #ff4d4f;
        }

        &.cancelled {
          background: #f5f5f5;
          color: #999;
        }
      }
    }

    .execution-details {
      .detail-item {
        display: flex;
        justify-content: space-between;
        font-size: 10px;
        margin-bottom: 2px;

        &:last-child {
          margin-bottom: 0;
        }

        .detail-label {
          color: #666;
        }

        .detail-value {
          color: #333;
          font-weight: 500;
          font-family: monospace;
        }
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
        background: linear-gradient(90deg, #722ed1, #9254de);
        transition: width 0.3s ease;
      }
    }

    .progress-text {
      font-size: 10px;
      color: #666;
      text-align: center;
    }
  }

  .loop-controls {
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 4px;
    padding: 6px;

    .control-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 10px;
      margin-bottom: 3px;

      &:last-child {
        margin-bottom: 0;
      }

      i {
        font-size: 9px;
        color: #722ed1;
      }

      .control-label {
        color: #666;
        min-width: 60px;
      }

      .control-value {
        color: #333;
        font-weight: 500;
        font-family: monospace;
        flex: 1;
        word-break: break-all;
      }
    }
  }

  .performance-info {
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 4px;
    padding: 6px;

    .performance-item {
      display: flex;
      justify-content: space-between;
      font-size: 9px;
      margin-bottom: 2px;

      &:last-child {
        margin-bottom: 0;
      }

      .performance-label {
        color: #999;
      }

      .performance-value {
        color: #333;
        font-weight: 500;
        font-family: monospace;
      }
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

.icon-check-circle::before {
  content: '✅';
}

.icon-running::before {
  content: '▶️';
}

.icon-paused::before {
  content: '⏸️';
}

.icon-max-iterations::before {
  content: '🔢';
}

.icon-break::before {
  content: '🛑';
}

.icon-continue::before {
  content: '⏭️';
}
</style>
