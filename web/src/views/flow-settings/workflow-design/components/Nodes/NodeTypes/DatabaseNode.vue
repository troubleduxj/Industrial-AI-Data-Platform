<template>
  <div
    :class="[
      'database-node',
      {
        selected: isSelected,
        hovered: isHovered,
        dragging: isDragging,
        error: hasError,
        warning: hasWarning,
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
        <i class="icon-database"></i>
      </div>
      <div class="node-title">
        <span class="node-label">{{ nodeData.label || '数据库操作' }}</span>
        <span class="node-type">{{ getDatabaseTypeLabel(nodeData.dbType) }}</span>
      </div>
      <div class="node-status">
        <div v-if="hasError" class="status-indicator error" title="错误">
          <i class="icon-exclamation-circle"></i>
        </div>
        <div v-else-if="hasWarning" class="status-indicator warning" title="警告">
          <i class="icon-exclamation-triangle"></i>
        </div>
        <div v-else class="status-indicator success" title="正常">
          <i class="icon-check-circle"></i>
        </div>
      </div>
    </div>

    <!-- 节点内容 -->
    <div class="node-content">
      <div class="database-info">
        <div class="operation-type" :class="nodeData.operation?.toLowerCase()">
          {{ getOperationLabel(nodeData.operation) }}
        </div>
        <div class="table-name">
          {{ nodeData.tableName || '未指定表' }}
        </div>
      </div>

      <div v-if="nodeData.description" class="node-description">
        {{ nodeData.description }}
      </div>

      <!-- SQL预览 -->
      <div v-if="nodeData.sql" class="sql-preview">
        <div class="sql-label">SQL:</div>
        <div class="sql-content">
          {{ formatSql(nodeData.sql) }}
        </div>
      </div>

      <!-- 连接信息 -->
      <div v-if="nodeData.connection" class="connection-info">
        <div class="connection-name">连接: {{ nodeData.connection.name || '默认连接' }}</div>
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
  name: 'DatabaseNode',
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
      default: () => ({ width: 160, height: 120 }),
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
    // 连接点配置
    connectionPoints: {
      type: Object,
      default: () => ({
        inputs: [
          { id: 'input', label: '输入', position: 'left', dataType: 'any', color: '#1890ff' },
        ],
        outputs: [
          { id: 'result', label: '结果', position: 'right', dataType: 'array', color: '#52c41a' },
          { id: 'error', label: '错误', position: 'bottom', dataType: 'error', color: '#ff4d4f' },
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

    // 获取数据库类型标签
    const getDatabaseTypeLabel = (dbType) => {
      const typeMap = {
        mysql: 'MySQL',
        postgresql: 'PostgreSQL',
        mongodb: 'MongoDB',
        redis: 'Redis',
        sqlite: 'SQLite',
        oracle: 'Oracle',
        sqlserver: 'SQL Server',
        elasticsearch: 'Elasticsearch',
      }
      return typeMap[dbType] || 'Database'
    }

    // 获取操作标签
    const getOperationLabel = (operation) => {
      const operationMap = {
        select: 'SELECT',
        insert: 'INSERT',
        update: 'UPDATE',
        delete: 'DELETE',
        create: 'CREATE',
        drop: 'DROP',
        alter: 'ALTER',
        query: 'QUERY',
      }
      return operationMap[operation] || 'QUERY'
    }

    // 格式化SQL
    const formatSql = (sql) => {
      if (!sql) return ''
      if (sql.length > 50) {
        return sql.substring(0, 47) + '...'
      }
      return sql
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
      getDatabaseTypeLabel,
      getOperationLabel,
      formatSql,
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
.database-node {
  position: absolute;
  background: #ffffff;
  border: 2px solid #722ed1;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  user-select: none;
  transition: all 0.2s ease;
  min-width: 160px;
  min-height: 120px;

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

    .icon-database::before {
      content: '🗄️';
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

      &.success {
        background: #52c41a;
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

.node-content {
  padding: 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .database-info {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;

    .operation-type {
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      color: white;

      &.select {
        background: #52c41a;
      }

      &.insert {
        background: #1890ff;
      }

      &.update {
        background: #fa8c16;
      }

      &.delete {
        background: #ff4d4f;
      }

      &.create {
        background: #722ed1;
      }

      &.query {
        background: #13c2c2;
      }
    }

    .table-name {
      flex: 1;
      font-size: 11px;
      color: #666;
      font-family: monospace;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
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

  .sql-preview {
    background: #f5f5f5;
    border-radius: 4px;
    padding: 6px;
    font-family: monospace;

    .sql-label {
      font-size: 9px;
      color: #999;
      margin-bottom: 2px;
    }

    .sql-content {
      font-size: 10px;
      color: #333;
      line-height: 1.2;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }

  .connection-info {
    .connection-name {
      font-size: 10px;
      color: #999;
      background: #f0f0f0;
      padding: 2px 6px;
      border-radius: 3px;
      display: inline-block;
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
</style>
