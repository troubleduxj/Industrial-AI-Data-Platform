<template>
  <div class="status-indicator" :class="indicatorClasses">
    <!-- 状态图标 -->
    <div v-if="showIcon" class="status-icon">
      <span v-if="!customIcon" class="icon">{{ statusIcon }}</span>
      <component :is="customIcon" v-else />

      <!-- 动画效果 -->
      <div
        v-if="pulse && (status === 'loading' || status === 'processing')"
        class="pulse-ring"
      ></div>
      <div v-if="ripple" class="ripple"></div>
    </div>

    <!-- 状态文本 -->
    <div v-if="showText || showDescription" class="status-content">
      <div v-if="showText" class="status-text">
        {{ statusText }}
      </div>
      <div v-if="showDescription && description" class="status-description">
        {{ description }}
      </div>
    </div>

    <!-- 进度条 -->
    <div v-if="showProgress && progress !== null" class="progress-container">
      <div class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: `${Math.min(100, Math.max(0, progress))}%` }"
        ></div>
      </div>
      <div v-if="showProgressText" class="progress-text">{{ Math.round(progress) }}%</div>
    </div>

    <!-- 操作按钮 -->
    <div v-if="actions.length > 0" class="status-actions">
      <button
        v-for="action in actions"
        :key="action.key"
        class="action-btn"
        :class="action.class"
        :disabled="action.disabled"
        :title="action.tooltip"
        @click="handleAction(action)"
      >
        <span v-if="action.icon" class="action-icon">{{ action.icon }}</span>
        <span v-if="action.text" class="action-text">{{ action.text }}</span>
      </button>
    </div>

    <!-- 时间戳 -->
    <div v-if="showTimestamp && timestamp" class="status-timestamp">
      {{ formatTimestamp(timestamp) }}
    </div>

    <!-- 详细信息 -->
    <div v-if="showDetails && details" class="status-details">
      <div class="details-toggle" @click="toggleDetails">
        <span class="toggle-icon">{{ detailsExpanded ? '▼' : '▶' }}</span>
        <span class="toggle-text">详细信息</span>
      </div>
      <div v-if="detailsExpanded" class="details-content">
        <pre class="details-text">{{ details }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatusIndicator',
  props: {
    // 状态类型
    status: {
      type: String,
      default: 'idle',
      validator: (value: string) =>
        [
          'idle',
          'loading',
          'processing',
          'success',
          'error',
          'warning',
          'info',
          'pending',
          'completed',
          'failed',
          'cancelled',
          'paused',
        ].includes(value),
    },
    // 状态文本
    text: {
      type: String,
      default: '',
    },
    // 状态描述
    description: {
      type: String,
      default: '',
    },
    // 自定义图标组件
    customIcon: {
      type: [String, Object],
      default: null,
    },
    // 进度值 (0-100)
    progress: {
      type: Number,
      default: null,
    },
    // 时间戳
    timestamp: {
      type: [Date, String, Number],
      default: null,
    },
    // 详细信息
    details: {
      type: [String, Object],
      default: null,
    },
    // 操作按钮
    actions: {
      type: Array,
      default: () => [],
    },
    // 显示选项
    showIcon: {
      type: Boolean,
      default: true,
    },
    showText: {
      type: Boolean,
      default: true,
    },
    showDescription: {
      type: Boolean,
      default: true,
    },
    showProgress: {
      type: Boolean,
      default: true,
    },
    showProgressText: {
      type: Boolean,
      default: true,
    },
    showTimestamp: {
      type: Boolean,
      default: false,
    },
    showDetails: {
      type: Boolean,
      default: false,
    },
    // 动画效果
    pulse: {
      type: Boolean,
      default: true,
    },
    ripple: {
      type: Boolean,
      default: false,
    },
    // 尺寸
    size: {
      type: String,
      default: 'medium',
      validator: (value: string) => ['small', 'medium', 'large'].includes(value),
    },
    // 布局
    layout: {
      type: String,
      default: 'horizontal',
      validator: (value: string) => ['horizontal', 'vertical', 'compact'].includes(value),
    },
    // 主题
    theme: {
      type: String,
      default: 'default',
      validator: (value: string) => ['default', 'minimal', 'card', 'badge'].includes(value),
    },
  },
  data() {
    return {
      detailsExpanded: false,
    }
  },
  computed: {
    indicatorClasses() {
      return {
        [`status-${this.status}`]: true,
        [`size-${this.size}`]: true,
        [`layout-${this.layout}`]: true,
        [`theme-${this.theme}`]: true,
        'has-progress': this.showProgress && this.progress !== null,
        'has-actions': this.actions.length > 0,
        clickable: this.actions.length > 0 || this.showDetails,
      }
    },
    statusIcon() {
      const icons = {
        idle: '⚪',
        loading: '🔄',
        processing: '⚙️',
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️',
        pending: '⏳',
        completed: '✅',
        failed: '❌',
        cancelled: '🚫',
        paused: '⏸️',
      }
      return icons[this.status] || '⚪'
    },
    statusText() {
      if (this.text) {
        return this.text
      }

      const defaultTexts = {
        idle: '空闲',
        loading: '加载中',
        processing: '处理中',
        success: '成功',
        error: '错误',
        warning: '警告',
        info: '信息',
        pending: '等待中',
        completed: '已完成',
        failed: '失败',
        cancelled: '已取消',
        paused: '已暂停',
      }
      return defaultTexts[this.status] || '未知状态'
    },
  },
  methods: {
    // 处理操作按钮点击
    handleAction(action) {
      if (action.disabled) return

      this.$emit('action', {
        key: action.key,
        action: action,
        status: this.status,
      })

      if (action.handler && typeof action.handler === 'function') {
        action.handler()
      }
    },

    // 切换详细信息
    toggleDetails() {
      this.detailsExpanded = !this.detailsExpanded
      this.$emit('details-toggle', this.detailsExpanded)
    },

    // 格式化时间戳
    formatTimestamp(timestamp) {
      try {
        const date = new Date(timestamp)
        const now = new Date()
        const diff = now - date

        // 小于1分钟
        if (diff < 60000) {
          return '刚刚'
        }

        // 小于1小时
        if (diff < 3600000) {
          const minutes = Math.floor(diff / 60000)
          return `${minutes}分钟前`
        }

        // 小于1天
        if (diff < 86400000) {
          const hours = Math.floor(diff / 3600000)
          return `${hours}小时前`
        }

        // 超过1天，显示具体时间
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
        })
      } catch (error) {
        return '无效时间'
      }
    },
  },
}
</script>

<style scoped>
.status-indicator {
  display: flex;
  align-items: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  transition: all 0.3s ease;
}

/* 布局样式 */
.status-indicator.layout-horizontal {
  flex-direction: row;
  gap: 8px;
}

.status-indicator.layout-vertical {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.status-indicator.layout-compact {
  flex-direction: row;
  gap: 4px;
}

/* 尺寸样式 */
.status-indicator.size-small {
  font-size: 12px;
}

.status-indicator.size-small .status-icon {
  width: 16px;
  height: 16px;
}

.status-indicator.size-medium {
  font-size: 14px;
}

.status-indicator.size-medium .status-icon {
  width: 20px;
  height: 20px;
}

.status-indicator.size-large {
  font-size: 16px;
}

.status-indicator.size-large .status-icon {
  width: 24px;
  height: 24px;
}

/* 主题样式 */
.status-indicator.theme-card {
  background: var(--bg-color, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-indicator.theme-badge {
  background: var(--badge-bg, #f0f0f0);
  border-radius: 16px;
  padding: 4px 8px;
}

.status-indicator.theme-minimal {
  background: none;
  border: none;
  padding: 0;
}

/* 状态图标 */
.status-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.status-icon .icon {
  font-size: inherit;
  line-height: 1;
}

/* 脉冲动画 */
.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  border: 2px solid currentColor;
  border-radius: 50%;
  opacity: 0;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0;
  }
}

/* 涟漪效果 */
.ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 0;
  height: 0;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.3;
  animation: ripple 1.5s infinite;
}

@keyframes ripple {
  0% {
    width: 0;
    height: 0;
    opacity: 0.3;
  }
  100% {
    width: 200%;
    height: 200%;
    opacity: 0;
  }
}

/* 状态内容 */
.status-content {
  flex: 1;
  min-width: 0;
}

.status-text {
  font-weight: 500;
  color: var(--text-color, #333333);
  margin-bottom: 2px;
}

.status-description {
  font-size: 0.9em;
  color: var(--text-color-secondary, #666666);
  line-height: 1.4;
}

/* 进度条 */
.progress-container {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.status-indicator.layout-horizontal .progress-container {
  width: auto;
  min-width: 100px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: var(--progress-bg, #e0e0e0);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--progress-color, #007bff);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.8em;
  color: var(--text-color-secondary, #666666);
  white-space: nowrap;
}

/* 操作按钮 */
.status-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  background: none;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 0.8em;
  color: var(--text-color, #333333);
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background: var(--hover-bg, #f0f0f0);
  border-color: var(--border-color-hover, #d0d0d0);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-icon {
  margin-right: 4px;
}

/* 时间戳 */
.status-timestamp {
  font-size: 0.8em;
  color: var(--text-color-tertiary, #999999);
  white-space: nowrap;
}

/* 详细信息 */
.status-details {
  width: 100%;
}

.details-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 0.9em;
  color: var(--text-color-secondary, #666666);
  padding: 4px 0;
  user-select: none;
}

.details-toggle:hover {
  color: var(--text-color, #333333);
}

.toggle-icon {
  transition: transform 0.2s ease;
}

.details-content {
  margin-top: 8px;
  padding: 8px;
  background: var(--details-bg, #f8f9fa);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 4px;
}

.details-text {
  margin: 0;
  font-size: 0.8em;
  color: var(--text-color-secondary, #666666);
  white-space: pre-wrap;
  word-break: break-word;
}

/* 状态特定样式 */
.status-idle {
  --status-color: #6c757d;
}

.status-loading,
.status-processing {
  --status-color: #007bff;
}

.status-loading .status-icon,
.status-processing .status-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.status-success,
.status-completed {
  --status-color: #28a745;
  --progress-color: #28a745;
}

.status-error,
.status-failed {
  --status-color: #dc3545;
  --progress-color: #dc3545;
}

.status-warning {
  --status-color: #ffc107;
  --progress-color: #ffc107;
}

.status-info {
  --status-color: #17a2b8;
  --progress-color: #17a2b8;
}

.status-pending {
  --status-color: #6f42c1;
  --progress-color: #6f42c1;
}

.status-cancelled {
  --status-color: #6c757d;
  --progress-color: #6c757d;
}

.status-paused {
  --status-color: #fd7e14;
  --progress-color: #fd7e14;
}

/* 应用状态颜色 */
.status-indicator .status-icon {
  color: var(--status-color, #6c757d);
}

.status-indicator.theme-badge {
  background: color-mix(in srgb, var(--status-color, #6c757d) 10%, transparent);
  color: var(--status-color, #6c757d);
}

/* 深色主题 */
@media (prefers-color-scheme: dark) {
  .status-indicator {
    --bg-color: #2d2d2d;
    --border-color: #4d4d4d;
    --text-color: #ffffff;
    --text-color-secondary: #cccccc;
    --text-color-tertiary: #999999;
    --hover-bg: #4d4d4d;
    --border-color-hover: #5d5d5d;
    --progress-bg: #4d4d4d;
    --details-bg: #3d3d3d;
    --badge-bg: #3d3d3d;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .status-indicator.layout-horizontal {
    flex-direction: column;
    align-items: flex-start;
  }

  .progress-container {
    width: 100%;
  }

  .status-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
