<template>
  <div
    :class="[
      'condition-node',
      {
        selected: isSelected,
        hovered: isHovered,
        dragging: isDragging,
        error: hasError,
        warning: hasWarning,
        evaluating: isEvaluating,
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
        <i class="icon-condition"></i>
      </div>
      <div class="node-title">
        <span class="node-label">{{ nodeData.label || '条件判断' }}</span>
        <span class="node-type">{{ getConditionTypeLabel(nodeData.conditionType) }}</span>
      </div>
      <div class="node-status">
        <div v-if="hasError" class="status-indicator error" title="错误">
          <i class="icon-exclamation-circle"></i>
        </div>
        <div v-else-if="hasWarning" class="status-indicator warning" title="警告">
          <i class="icon-exclamation-triangle"></i>
        </div>
        <div v-else-if="isEvaluating" class="status-indicator evaluating" title="评估中">
          <i class="icon-evaluating"></i>
        </div>
        <div v-else class="status-indicator ready" title="就绪">
          <i class="icon-check-circle"></i>
        </div>
      </div>
    </div>

    <!-- 节点内容 -->
    <div class="node-content">
      <div class="condition-info">
        <div class="condition-type" :class="nodeData.conditionType?.toLowerCase()">
          {{ getConditionTypeLabel(nodeData.conditionType) }}
        </div>

        <!-- 简单条件 -->
        <div v-if="nodeData.conditionType === 'simple'" class="simple-condition">
          <div class="condition-expression">
            <span class="variable">{{ formatVariable(nodeData.leftOperand) }}</span>
            <span class="operator">{{ getOperatorLabel(nodeData.operator) }}</span>
            <span class="value">{{ formatValue(nodeData.rightOperand) }}</span>
          </div>
        </div>

        <!-- 复合条件 -->
        <div v-else-if="nodeData.conditionType === 'compound'" class="compound-condition">
          <div class="conditions-list">
            <div
              v-for="(condition, index) in nodeData.conditions?.slice(0, 2)"
              :key="index"
              class="condition-item"
            >
              <span class="condition-text">{{ formatCondition(condition) }}</span>
            </div>
            <div v-if="nodeData.conditions?.length > 2" class="condition-more">
              +{{ nodeData.conditions.length - 2 }} 更多条件
            </div>
          </div>
          <div v-if="nodeData.logicalOperator" class="logical-operator">
            {{ getLogicalOperatorLabel(nodeData.logicalOperator) }}
          </div>
        </div>

        <!-- 脚本条件 -->
        <div v-else-if="nodeData.conditionType === 'script'" class="script-condition">
          <div class="script-preview">
            {{ formatScript(nodeData.script) }}
          </div>
          <div v-if="nodeData.language" class="script-language">
            {{ nodeData.language.toUpperCase() }}
          </div>
        </div>

        <!-- 正则表达式条件 -->
        <div v-else-if="nodeData.conditionType === 'regex'" class="regex-condition">
          <div class="regex-pattern">
            <span class="pattern">{{ nodeData.pattern }}</span>
            <span v-if="nodeData.flags" class="flags">{{ nodeData.flags }}</span>
          </div>
          <div class="regex-target">目标: {{ formatVariable(nodeData.target) }}</div>
        </div>
      </div>

      <div v-if="nodeData.description" class="node-description">
        {{ nodeData.description }}
      </div>

      <!-- 评估结果 -->
      <div v-if="evaluationResult" class="evaluation-result">
        <div class="result-header">
          <span class="result-label">评估结果:</span>
          <span :class="['result-value', evaluationResult.result ? 'true' : 'false']">
            {{ evaluationResult.result ? 'True' : 'False' }}
          </span>
        </div>
        <div v-if="evaluationResult.details" class="result-details">
          {{ evaluationResult.details }}
        </div>
      </div>

      <!-- 分支信息 -->
      <div class="branch-info">
        <div class="branch-item true-branch">
          <i class="icon-check"></i>
          <span>True 分支</span>
          <span v-if="getBranchCount('true')" class="branch-count">
            ({{ getBranchCount('true') }})
          </span>
        </div>
        <div class="branch-item false-branch">
          <i class="icon-close"></i>
          <span>False 分支</span>
          <span v-if="getBranchCount('false')" class="branch-count">
            ({{ getBranchCount('false') }})
          </span>
        </div>
      </div>

      <!-- 性能信息 -->
      <div v-if="performanceInfo" class="performance-info">
        <div class="performance-item">
          <span class="performance-label">执行时间:</span>
          <span class="performance-value">{{ performanceInfo.executionTime }}ms</span>
        </div>
        <div v-if="performanceInfo.evaluationCount" class="performance-item">
          <span class="performance-label">评估次数:</span>
          <span class="performance-value">{{ performanceInfo.evaluationCount }}</span>
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
  name: 'ConditionNode',
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
      default: () => ({ width: 200, height: 160 }),
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
    // 评估状态
    isEvaluating: {
      type: Boolean,
      default: false,
    },
    // 评估结果
    evaluationResult: {
      type: Object,
      default: null,
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
          { id: 'true', label: 'True', position: 'right', dataType: 'trigger', color: '#52c41a' },
          { id: 'false', label: 'False', position: 'right', dataType: 'trigger', color: '#ff4d4f' },
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

    // 获取条件类型标签
    const getConditionTypeLabel = (type) => {
      const typeMap = {
        simple: '简单条件',
        compound: '复合条件',
        script: '脚本条件',
        regex: '正则表达式',
        range: '范围条件',
        exists: '存在性检查',
      }
      return typeMap[type] || 'Condition'
    }

    // 获取操作符标签
    const getOperatorLabel = (operator) => {
      const operatorMap = {
        '==': '等于',
        '!=': '不等于',
        '>': '大于',
        '>=': '大于等于',
        '<': '小于',
        '<=': '小于等于',
        contains: '包含',
        startsWith: '开始于',
        endsWith: '结束于',
        in: '在...中',
        notIn: '不在...中',
        isEmpty: '为空',
        isNotEmpty: '不为空',
      }
      return operatorMap[operator] || operator
    }

    // 获取逻辑操作符标签
    const getLogicalOperatorLabel = (operator) => {
      const operatorMap = {
        and: '且',
        or: '或',
        not: '非',
      }
      return operatorMap[operator] || operator
    }

    // 格式化变量
    const formatVariable = (variable) => {
      if (!variable) return '未设置'
      if (typeof variable === 'string') return variable
      if (variable.path) return variable.path
      if (variable.name) return variable.name
      return JSON.stringify(variable)
    }

    // 格式化值
    const formatValue = (value) => {
      if (value === null || value === undefined) return 'null'
      if (typeof value === 'string') return `"${value}"`
      if (typeof value === 'boolean') return value.toString()
      if (typeof value === 'number') return value.toString()
      if (Array.isArray(value)) return `[${value.length} 项]`
      if (typeof value === 'object') return '{...}'
      return value.toString()
    }

    // 格式化条件
    const formatCondition = (condition) => {
      if (!condition) return ''
      const left = formatVariable(condition.leftOperand)
      const operator = getOperatorLabel(condition.operator)
      const right = formatValue(condition.rightOperand)
      return `${left} ${operator} ${right}`
    }

    // 格式化脚本
    const formatScript = (script) => {
      if (!script) return '无脚本'
      if (script.length > 50) {
        return script.substring(0, 47) + '...'
      }
      return script
    }

    // 获取分支连接数量
    const getBranchCount = (branch) => {
      const pointId = branch === 'true' ? 'true' : 'false'
      return props.connectedPoints.filter((id) => id === pointId).length
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
      getConditionTypeLabel,
      getOperatorLabel,
      getLogicalOperatorLabel,
      formatVariable,
      formatValue,
      formatCondition,
      formatScript,
      getBranchCount,
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
.condition-node {
  position: absolute;
  background: #ffffff;
  border: 2px solid #fa8c16;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  user-select: none;
  transition: all 0.2s ease;
  min-width: 200px;
  min-height: 160px;

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

  &.evaluating {
    border-color: #1890ff;
    animation: evaluating 1.5s infinite;
  }
}

@keyframes evaluating {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.4);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(24, 144, 255, 0);
  }
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(135deg, #fa8c16, #ffc53d);
  color: white;
  border-radius: 6px 6px 0 0;
  min-height: 36px;

  .node-icon {
    margin-right: 8px;
    font-size: 16px;

    .icon-condition::before {
      content: '🔀';
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

      &.evaluating {
        background: #1890ff;
        color: white;
        animation: pulse 1s infinite;
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

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.node-content {
  padding: 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .condition-info {
    .condition-type {
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      color: white;
      display: inline-block;
      margin-bottom: 8px;

      &.simple {
        background: #52c41a;
      }

      &.compound {
        background: #1890ff;
      }

      &.script {
        background: #722ed1;
      }

      &.regex {
        background: #eb2f96;
      }

      &.range {
        background: #13c2c2;
      }

      &.exists {
        background: #fa8c16;
      }
    }

    .simple-condition {
      .condition-expression {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        background: #f9f9f9;
        padding: 6px 8px;
        border-radius: 4px;
        border: 1px solid #e8e8e8;

        .variable {
          color: #1890ff;
          font-weight: 600;
          font-family: monospace;
        }

        .operator {
          color: #fa8c16;
          font-weight: 600;
          padding: 2px 4px;
          background: #fff7e6;
          border-radius: 2px;
        }

        .value {
          color: #52c41a;
          font-weight: 500;
          font-family: monospace;
        }
      }
    }

    .compound-condition {
      .conditions-list {
        margin-bottom: 6px;

        .condition-item {
          font-size: 10px;
          color: #666;
          margin-bottom: 2px;
          padding: 2px 6px;
          background: #f5f5f5;
          border-radius: 3px;
          font-family: monospace;

          .condition-text {
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
        }

        .condition-more {
          font-size: 9px;
          color: #999;
          font-style: italic;
          text-align: center;
          padding: 2px;
        }
      }

      .logical-operator {
        text-align: center;
        font-size: 10px;
        font-weight: 600;
        color: #fa8c16;
        background: #fff7e6;
        padding: 2px 8px;
        border-radius: 4px;
        display: inline-block;
      }
    }

    .script-condition {
      .script-preview {
        font-family: monospace;
        font-size: 10px;
        color: #666;
        background: #f5f5f5;
        padding: 6px 8px;
        border-radius: 4px;
        border: 1px solid #e8e8e8;
        white-space: pre-wrap;
        word-break: break-all;
      }

      .script-language {
        font-size: 9px;
        color: #722ed1;
        font-weight: 600;
        margin-top: 4px;
      }
    }

    .regex-condition {
      .regex-pattern {
        font-family: monospace;
        font-size: 11px;
        background: #f5f5f5;
        padding: 4px 6px;
        border-radius: 3px;
        margin-bottom: 4px;

        .pattern {
          color: #eb2f96;
          font-weight: 600;
        }

        .flags {
          color: #999;
          margin-left: 4px;
        }
      }

      .regex-target {
        font-size: 10px;
        color: #666;
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

  .evaluation-result {
    background: #f0f9ff;
    border: 1px solid #e6f7ff;
    border-radius: 4px;
    padding: 6px 8px;

    .result-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 4px;

      .result-label {
        font-size: 10px;
        color: #1890ff;
        font-weight: 600;
      }

      .result-value {
        font-size: 11px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 3px;

        &.true {
          background: #f6ffed;
          color: #52c41a;
          border: 1px solid #b7eb8f;
        }

        &.false {
          background: #fff2f0;
          color: #ff4d4f;
          border: 1px solid #ffb3b3;
        }
      }
    }

    .result-details {
      font-size: 9px;
      color: #666;
      line-height: 1.3;
    }
  }

  .branch-info {
    display: flex;
    justify-content: space-between;
    gap: 8px;

    .branch-item {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 10px;
      padding: 4px 6px;
      border-radius: 4px;
      border: 1px solid;

      &.true-branch {
        color: #52c41a;
        background: #f6ffed;
        border-color: #b7eb8f;
      }

      &.false-branch {
        color: #ff4d4f;
        background: #fff2f0;
        border-color: #ffb3b3;
      }

      .branch-count {
        margin-left: auto;
        font-weight: 600;
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

.icon-evaluating::before {
  content: '🔄';
}

.icon-check::before {
  content: '✓';
}

.icon-close::before {
  content: '✗';
}
</style>
