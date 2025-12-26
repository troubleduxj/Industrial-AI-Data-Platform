<template>
  <div
    :class="[
      'file-node',
      {
        selected: isSelected,
        hovered: isHovered,
        dragging: isDragging,
        error: hasError,
        warning: hasWarning,
        processing: isProcessing,
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
        <i class="icon-file"></i>
      </div>
      <div class="node-title">
        <span class="node-label">{{ nodeData.label || '文件操作' }}</span>
        <span class="node-type">{{ getFileOperationLabel(nodeData.operation) }}</span>
      </div>
      <div class="node-status">
        <div v-if="hasError" class="status-indicator error" title="错误">
          <i class="icon-exclamation-circle"></i>
        </div>
        <div v-else-if="hasWarning" class="status-indicator warning" title="警告">
          <i class="icon-exclamation-triangle"></i>
        </div>
        <div v-else-if="isProcessing" class="status-indicator processing" title="处理中">
          <i class="icon-processing"></i>
        </div>
        <div v-else class="status-indicator ready" title="就绪">
          <i class="icon-check-circle"></i>
        </div>
      </div>
    </div>

    <!-- 节点内容 -->
    <div class="node-content">
      <div class="file-info">
        <div class="operation-info">
          <div class="operation-type" :class="nodeData.operation?.toLowerCase()">
            {{ getFileOperationLabel(nodeData.operation) }}
          </div>
        </div>

        <div class="path-info">
          <div class="info-item">
            <span class="info-label">路径:</span>
            <span class="info-value path">{{ formatPath(nodeData.path) }}</span>
          </div>
          <div v-if="nodeData.targetPath" class="info-item">
            <span class="info-label">目标:</span>
            <span class="info-value path">{{ formatPath(nodeData.targetPath) }}</span>
          </div>
        </div>
      </div>

      <div v-if="nodeData.description" class="node-description">
        {{ nodeData.description }}
      </div>

      <!-- 文件详情 -->
      <div v-if="fileDetails" class="file-details">
        <div class="detail-item">
          <span class="detail-label">类型:</span>
          <span class="detail-value">{{ getFileTypeLabel(fileDetails.type) }}</span>
        </div>
        <div v-if="fileDetails.size" class="detail-item">
          <span class="detail-label">大小:</span>
          <span class="detail-value">{{ formatFileSize(fileDetails.size) }}</span>
        </div>
        <div v-if="fileDetails.encoding" class="detail-item">
          <span class="detail-label">编码:</span>
          <span class="detail-value">{{ fileDetails.encoding }}</span>
        </div>
      </div>

      <!-- 过滤条件 -->
      <div v-if="nodeData.filters && nodeData.filters.length" class="filters-info">
        <div class="filters-label">过滤条件:</div>
        <div class="filters-list">
          <div
            v-for="(filter, index) in nodeData.filters.slice(0, 2)"
            :key="index"
            class="filter-item"
          >
            {{ formatFilter(filter) }}
          </div>
          <div v-if="nodeData.filters.length > 2" class="filter-more">
            +{{ nodeData.filters.length - 2 }} 更多
          </div>
        </div>
      </div>

      <!-- 处理选项 -->
      <div v-if="nodeData.options" class="options-info">
        <div v-if="nodeData.options.backup" class="option-item">
          <i class="icon-backup"></i>
          <span>备份</span>
        </div>
        <div v-if="nodeData.options.overwrite" class="option-item">
          <i class="icon-overwrite"></i>
          <span>覆盖</span>
        </div>
        <div v-if="nodeData.options.createDir" class="option-item">
          <i class="icon-create-dir"></i>
          <span>创建目录</span>
        </div>
      </div>

      <!-- 进度信息 -->
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
  name: 'FileNode',
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
    // 处理状态
    isProcessing: {
      type: Boolean,
      default: false,
    },
    // 文件详情
    fileDetails: {
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
          { id: 'trigger', label: '触发', position: 'left', dataType: 'trigger', color: '#1890ff' },
          { id: 'path', label: '路径', position: 'left', dataType: 'string', color: '#52c41a' },
        ],
        outputs: [
          { id: 'result', label: '结果', position: 'right', dataType: 'any', color: '#52c41a' },
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

    // 获取文件操作标签
    const getFileOperationLabel = (operation) => {
      const operationMap = {
        read: '读取',
        write: '写入',
        copy: '复制',
        move: '移动',
        delete: '删除',
        create: '创建',
        rename: '重命名',
        compress: '压缩',
        extract: '解压',
        upload: '上传',
        download: '下载',
      }
      return operationMap[operation] || 'File'
    }

    // 格式化路径
    const formatPath = (path) => {
      if (!path) return '未设置'
      if (path.length > 30) {
        return '...' + path.substring(path.length - 27)
      }
      return path
    }

    // 获取文件类型标签
    const getFileTypeLabel = (type) => {
      const typeMap = {
        file: '文件',
        directory: '目录',
        image: '图片',
        video: '视频',
        audio: '音频',
        document: '文档',
        archive: '压缩包',
        text: '文本',
        binary: '二进制',
      }
      return typeMap[type] || type
    }

    // 格式化文件大小
    const formatFileSize = (size) => {
      if (!size) return '未知'
      if (size < 1024) return `${size} B`
      if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
      if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`
      return `${(size / (1024 * 1024 * 1024)).toFixed(1)} GB`
    }

    // 格式化过滤条件
    const formatFilter = (filter) => {
      if (typeof filter === 'string') return filter
      if (filter.type === 'extension') return `*.${filter.value}`
      if (filter.type === 'name') return filter.value
      if (filter.type === 'size') return `${filter.operator} ${formatFileSize(filter.value)}`
      return JSON.stringify(filter)
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
      getFileOperationLabel,
      formatPath,
      getFileTypeLabel,
      formatFileSize,
      formatFilter,
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
.file-node {
  position: absolute;
  background: #ffffff;
  border: 2px solid #eb2f96;
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

  &.processing {
    border-color: #1890ff;
    animation: processing 2s infinite;
  }
}

@keyframes processing {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(24, 144, 255, 0);
  }
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(135deg, #eb2f96, #f759ab);
  color: white;
  border-radius: 6px 6px 0 0;
  min-height: 36px;

  .node-icon {
    margin-right: 8px;
    font-size: 16px;

    .icon-file::before {
      content: '📁';
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

      &.processing {
        background: #1890ff;
        color: white;
        animation: spin 1s linear infinite;
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

  .file-info {
    .operation-info {
      margin-bottom: 6px;

      .operation-type {
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        color: white;
        display: inline-block;

        &.read {
          background: #52c41a;
        }

        &.write {
          background: #1890ff;
        }

        &.copy {
          background: #13c2c2;
        }

        &.move {
          background: #fa8c16;
        }

        &.delete {
          background: #ff4d4f;
        }

        &.create {
          background: #722ed1;
        }

        &.compress {
          background: #eb2f96;
        }

        &.upload {
          background: #52c41a;
        }

        &.download {
          background: #1890ff;
        }
      }
    }

    .path-info {
      .info-item {
        display: flex;
        align-items: flex-start;
        font-size: 11px;
        margin-bottom: 3px;

        .info-label {
          color: #666;
          margin-right: 6px;
          min-width: 35px;
          flex-shrink: 0;
        }

        .info-value {
          flex: 1;
          font-weight: 500;
          color: #333;
          line-height: 1.3;
          word-break: break-all;

          &.path {
            font-family: monospace;
            background: #f5f5f5;
            padding: 1px 4px;
            border-radius: 2px;
            font-size: 10px;
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

  .file-details {
    background: #f9f9f9;
    border-radius: 4px;
    padding: 6px;
    font-size: 10px;

    .detail-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 2px;

      &:last-child {
        margin-bottom: 0;
      }

      .detail-label {
        color: #999;
      }

      .detail-value {
        color: #333;
        font-weight: 500;
      }
    }
  }

  .filters-info {
    background: #f0f9ff;
    border: 1px solid #e6f7ff;
    border-radius: 4px;
    padding: 6px;

    .filters-label {
      font-size: 10px;
      color: #1890ff;
      margin-bottom: 4px;
      font-weight: 600;
    }

    .filters-list {
      .filter-item {
        font-size: 9px;
        color: #666;
        margin-bottom: 1px;
        font-family: monospace;
        background: #f5f5f5;
        padding: 1px 4px;
        border-radius: 2px;
        display: inline-block;
        margin-right: 4px;
      }

      .filter-more {
        font-size: 9px;
        color: #999;
        font-style: italic;
      }
    }
  }

  .options-info {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;

    .option-item {
      display: flex;
      align-items: center;
      gap: 2px;
      font-size: 9px;
      color: #666;
      background: #f5f5f5;
      padding: 2px 4px;
      border-radius: 3px;

      i {
        font-size: 8px;
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
        background: linear-gradient(90deg, #eb2f96, #f759ab);
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

.icon-check-circle::before {
  content: '✅';
}

.icon-processing::before {
  content: '⚙️';
}

.icon-backup::before {
  content: '💾';
}

.icon-overwrite::before {
  content: '🔄';
}

.icon-create-dir::before {
  content: '📁';
}
</style>
