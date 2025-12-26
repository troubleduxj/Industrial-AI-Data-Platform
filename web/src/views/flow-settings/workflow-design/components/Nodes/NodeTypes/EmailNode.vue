<template>
  <div
    :class="[
      'email-node',
      {
        selected: isSelected,
        hovered: isHovered,
        dragging: isDragging,
        error: hasError,
        warning: hasWarning,
        sending: isSending,
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
        <i class="icon-email"></i>
      </div>
      <div class="node-title">
        <span class="node-label">{{ nodeData.label || '邮件发送' }}</span>
        <span class="node-type">{{ getEmailTypeLabel(nodeData.emailType) }}</span>
      </div>
      <div class="node-status">
        <div v-if="hasError" class="status-indicator error" title="错误">
          <i class="icon-exclamation-circle"></i>
        </div>
        <div v-else-if="hasWarning" class="status-indicator warning" title="警告">
          <i class="icon-exclamation-triangle"></i>
        </div>
        <div v-else-if="isSending" class="status-indicator sending" title="发送中">
          <i class="icon-sending"></i>
        </div>
        <div v-else class="status-indicator ready" title="就绪">
          <i class="icon-check-circle"></i>
        </div>
      </div>
    </div>

    <!-- 节点内容 -->
    <div class="node-content">
      <div class="email-info">
        <div class="recipient-info">
          <div class="info-item">
            <span class="info-label">收件人:</span>
            <span class="info-value">{{ formatRecipients(nodeData.to) }}</span>
          </div>
          <div v-if="nodeData.cc && nodeData.cc.length" class="info-item">
            <span class="info-label">抄送:</span>
            <span class="info-value">{{ formatRecipients(nodeData.cc) }}</span>
          </div>
        </div>

        <div class="subject-info">
          <div class="info-item">
            <span class="info-label">主题:</span>
            <span class="info-value subject">{{ nodeData.subject || '无主题' }}</span>
          </div>
        </div>
      </div>

      <div v-if="nodeData.description" class="node-description">
        {{ nodeData.description }}
      </div>

      <!-- 邮件内容预览 -->
      <div v-if="nodeData.content" class="content-preview">
        <div class="content-label">内容预览:</div>
        <div class="content-text">
          {{ formatContent(nodeData.content) }}
        </div>
      </div>

      <!-- 附件信息 -->
      <div v-if="hasAttachments" class="attachments-info">
        <div class="attachments-label">
          <i class="icon-attachment"></i>
          附件 ({{ nodeData.attachments.length }})
        </div>
        <div class="attachments-list">
          <div
            v-for="(attachment, index) in nodeData.attachments.slice(0, 2)"
            :key="index"
            class="attachment-item"
          >
            {{ getFileName(attachment) }}
          </div>
          <div v-if="nodeData.attachments.length > 2" class="attachment-more">
            +{{ nodeData.attachments.length - 2 }} 更多
          </div>
        </div>
      </div>

      <!-- 发送配置 -->
      <div v-if="nodeData.config" class="config-info">
        <div v-if="nodeData.config.priority" class="config-item">
          <span class="priority-indicator" :class="nodeData.config.priority">
            {{ getPriorityLabel(nodeData.config.priority) }}
          </span>
        </div>
        <div v-if="nodeData.config.template" class="config-item">
          <span class="template-name">模板: {{ nodeData.config.template }}</span>
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
  name: 'EmailNode',
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
    // 发送状态
    isSending: {
      type: Boolean,
      default: false,
    },
    // 连接点配置
    connectionPoints: {
      type: Object,
      default: () => ({
        inputs: [
          { id: 'trigger', label: '触发', position: 'left', dataType: 'trigger', color: '#1890ff' },
          { id: 'data', label: '数据', position: 'left', dataType: 'object', color: '#52c41a' },
        ],
        outputs: [
          {
            id: 'success',
            label: '成功',
            position: 'right',
            dataType: 'boolean',
            color: '#52c41a',
          },
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

    // 是否有附件
    const hasAttachments = computed(() => {
      return props.nodeData.attachments && props.nodeData.attachments.length > 0
    })

    // 获取邮件类型标签
    const getEmailTypeLabel = (emailType) => {
      const typeMap = {
        notification: '通知邮件',
        alert: '告警邮件',
        report: '报告邮件',
        marketing: '营销邮件',
        system: '系统邮件',
      }
      return typeMap[emailType] || 'Email'
    }

    // 格式化收件人
    const formatRecipients = (recipients) => {
      if (!recipients) return '未设置'
      if (Array.isArray(recipients)) {
        if (recipients.length === 0) return '未设置'
        if (recipients.length === 1) return recipients[0]
        if (recipients.length <= 3) return recipients.join(', ')
        return `${recipients.slice(0, 2).join(', ')} +${recipients.length - 2}人`
      }
      return recipients.toString()
    }

    // 格式化内容
    const formatContent = (content) => {
      if (!content) return ''
      if (content.length > 60) {
        return content.substring(0, 57) + '...'
      }
      return content
    }

    // 获取文件名
    const getFileName = (attachment) => {
      if (typeof attachment === 'string') {
        return attachment.split('/').pop() || attachment
      }
      return attachment.name || attachment.filename || '未知文件'
    }

    // 获取优先级标签
    const getPriorityLabel = (priority) => {
      const priorityMap = {
        high: '高',
        normal: '普通',
        low: '低',
      }
      return priorityMap[priority] || '普通'
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
      hasAttachments,
      getEmailTypeLabel,
      formatRecipients,
      formatContent,
      getFileName,
      getPriorityLabel,
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
.email-node {
  position: absolute;
  background: #ffffff;
  border: 2px solid #13c2c2;
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

  &.sending {
    border-color: #1890ff;
    animation: sending 1.5s infinite;
  }
}

@keyframes sending {
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
  background: linear-gradient(135deg, #13c2c2, #36cfc9);
  color: white;
  border-radius: 6px 6px 0 0;
  min-height: 36px;

  .node-icon {
    margin-right: 8px;
    font-size: 16px;

    .icon-email::before {
      content: '📧';
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

      &.sending {
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

  .email-info {
    .recipient-info,
    .subject-info {
      margin-bottom: 6px;

      .info-item {
        display: flex;
        align-items: flex-start;
        font-size: 11px;
        margin-bottom: 3px;

        .info-label {
          color: #666;
          margin-right: 6px;
          min-width: 50px;
          flex-shrink: 0;
        }

        .info-value {
          flex: 1;
          font-weight: 500;
          color: #333;
          line-height: 1.3;
          word-break: break-all;

          &.subject {
            font-style: italic;
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

  .content-preview {
    background: #f9f9f9;
    border-radius: 4px;
    padding: 6px;
    font-size: 10px;

    .content-label {
      color: #999;
      margin-bottom: 3px;
    }

    .content-text {
      color: #333;
      line-height: 1.3;
      font-style: italic;
    }
  }

  .attachments-info {
    background: #f0f9ff;
    border: 1px solid #e6f7ff;
    border-radius: 4px;
    padding: 6px;

    .attachments-label {
      display: flex;
      align-items: center;
      font-size: 10px;
      color: #1890ff;
      margin-bottom: 4px;
      font-weight: 600;

      .icon-attachment {
        margin-right: 4px;

        &::before {
          content: '📎';
        }
      }
    }

    .attachments-list {
      .attachment-item {
        font-size: 9px;
        color: #666;
        margin-bottom: 1px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .attachment-more {
        font-size: 9px;
        color: #999;
        font-style: italic;
      }
    }
  }

  .config-info {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;

    .config-item {
      .priority-indicator {
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 9px;
        font-weight: 600;
        color: white;

        &.high {
          background: #ff4d4f;
        }

        &.normal {
          background: #52c41a;
        }

        &.low {
          background: #d9d9d9;
          color: #666;
        }
      }

      .template-name {
        font-size: 9px;
        color: #666;
        background: #f5f5f5;
        padding: 2px 6px;
        border-radius: 3px;
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

.icon-sending::before {
  content: '📤';
}
</style>
