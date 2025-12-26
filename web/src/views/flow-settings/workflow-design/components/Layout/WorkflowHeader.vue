<template>
  <div
    class="workflow-header"
    :class="{
      'workflow-header--dark': isDark,
      'workflow-header--compact': compact,
    }"
  >
    <!-- 左侧区域 -->
    <div class="workflow-header__left">
      <!-- 返回按钮 -->
      <button class="header-btn header-btn--back" title="返回工作流列表" @click="handleBack">
        <i class="icon-arrow-left"></i>
      </button>

      <!-- 工作流信息 -->
      <div class="workflow-info">
        <div class="workflow-info__main">
          <h1 v-if="!editingTitle" class="workflow-title" @dblclick="startEditTitle">
            {{ workflowTitle }}
          </h1>
          <input
            v-else
            ref="titleInput"
            v-model="editTitle"
            class="workflow-title-input"
            @blur="saveTitle"
            @keyup.enter="saveTitle"
            @keyup.escape="cancelEditTitle"
          />
          <div class="workflow-status">
            <span class="status-indicator" :class="`status-indicator--${workflowStatus}`">
              <i :class="statusIcon"></i>
              {{ statusText }}
            </span>
            <span class="workflow-version">v{{ workflowVersion }}</span>
          </div>
        </div>
        <div v-if="!compact" class="workflow-info__meta">
          <span class="meta-item">
            <i class="icon-calendar"></i>
            最后修改: {{ lastModified }}
          </span>
          <span class="meta-item">
            <i class="icon-user"></i>
            创建者: {{ creator }}
          </span>
        </div>
      </div>
    </div>

    <!-- 中间区域 - 快捷操作 -->
    <div class="workflow-header__center">
      <div class="quick-actions">
        <!-- 运行控制 -->
        <div class="action-group">
          <button
            class="header-btn header-btn--primary"
            :class="{ 'header-btn--loading': isRunning }"
            :disabled="!canRun"
            title="运行工作流"
            @click="handleRun"
          >
            <i v-if="!isRunning" class="icon-play"></i>
            <i v-else class="icon-loading icon-spin"></i>
            <span>{{ isRunning ? '运行中' : '运行' }}</span>
          </button>

          <button class="header-btn" :disabled="!isRunning" title="停止运行" @click="handleStop">
            <i class="icon-stop"></i>
          </button>

          <button class="header-btn" :disabled="!canDebug" title="调试模式" @click="handleDebug">
            <i class="icon-bug"></i>
          </button>
        </div>

        <!-- 编辑操作 -->
        <div class="action-group">
          <button class="header-btn" title="验证工作流" @click="handleValidate">
            <i class="icon-check-circle"></i>
            <span v-if="!compact">验证</span>
          </button>

          <button class="header-btn" title="格式化布局" @click="handleFormat">
            <i class="icon-layout"></i>
            <span v-if="!compact">格式化</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 右侧区域 -->
    <div class="workflow-header__right">
      <!-- 视图控制 -->
      <div class="view-controls">
        <button
          class="header-btn"
          :class="{ 'header-btn--active': showMinimap }"
          title="切换缩略图"
          @click="toggleMinimap"
        >
          <i class="icon-map"></i>
        </button>

        <button class="header-btn" title="全屏模式" @click="toggleFullscreen">
          <i :class="isFullscreen ? 'icon-minimize' : 'icon-maximize'"></i>
        </button>
      </div>

      <!-- 保存状态 -->
      <div class="save-status">
        <span
          class="save-indicator"
          :class="`save-indicator--${saveStatus}`"
          :title="saveStatusText"
        >
          <i :class="saveStatusIcon"></i>
          <span v-if="!compact">{{ saveStatusText }}</span>
        </span>
      </div>

      <!-- 操作菜单 -->
      <div class="action-menu">
        <button
          class="header-btn"
          :disabled="!hasChanges"
          title="保存工作流 (Ctrl+S)"
          @click="handleSave"
        >
          <i class="icon-save"></i>
          <span v-if="!compact">保存</span>
        </button>

        <div ref="moreDropdown" class="dropdown">
          <button class="header-btn" title="更多操作" @click="toggleMoreMenu">
            <i class="icon-more-vertical"></i>
          </button>

          <div v-show="showMoreMenu" class="dropdown-menu">
            <button class="dropdown-item" @click="handleExport">
              <i class="icon-download"></i>
              <span>导出工作流</span>
            </button>
            <button class="dropdown-item" @click="handleImport">
              <i class="icon-upload"></i>
              <span>导入工作流</span>
            </button>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item" @click="handleDuplicate">
              <i class="icon-copy"></i>
              <span>复制工作流</span>
            </button>
            <button class="dropdown-item" @click="handleTemplate">
              <i class="icon-bookmark"></i>
              <span>保存为模板</span>
            </button>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item" @click="handleSettings">
              <i class="icon-settings"></i>
              <span>工作流设置</span>
            </button>
            <button class="dropdown-item dropdown-item--danger" @click="handleDelete">
              <i class="icon-trash"></i>
              <span>删除工作流</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useWorkflowStore } from '../../stores/workflowStore'
import { useCanvasStore } from '../../stores/canvasStore'

export default {
  name: 'WorkflowHeader',
  props: {
    isDark: {
      type: Boolean,
      default: false,
    },
    compact: {
      type: Boolean,
      default: false,
    },
  },
  emits: [
    'back',
    'run',
    'stop',
    'debug',
    'validate',
    'format',
    'save',
    'export',
    'import',
    'duplicate',
    'template',
    'settings',
    'delete',
    'toggle-minimap',
    'toggle-fullscreen',
  ],
  setup(props, { emit }) {
    const workflowStore = useWorkflowStore()
    const canvasStore = useCanvasStore()

    // 标题编辑
    const editingTitle = ref(false)
    const editTitle = ref('')
    const titleInput = ref(null)

    // 更多菜单
    const showMoreMenu = ref(false)
    const moreDropdown = ref(null)

    // 工作流信息
    const workflowTitle = computed(() => workflowStore.currentWorkflow?.name || '未命名工作流')
    const workflowStatus = computed(() => workflowStore.currentWorkflow?.status || 'draft')
    const workflowVersion = computed(() => workflowStore.currentWorkflow?.version || '1.0.0')
    const lastModified = computed(() => {
      const date = workflowStore.currentWorkflow?.updatedAt
      return date ? new Date(date).toLocaleString() : '未知'
    })
    const creator = computed(() => workflowStore.currentWorkflow?.creator || '未知')

    // 状态计算
    const isRunning = computed(() => workflowStore.isRunning)
    const canRun = computed(() => workflowStore.canRun)
    const canDebug = computed(() => workflowStore.canDebug)
    const hasChanges = computed(() => workflowStore.hasUnsavedChanges)
    const saveStatus = computed(() => workflowStore.saveStatus) // 'saved', 'saving', 'error'
    const showMinimap = computed(() => canvasStore.showMinimap)
    const isFullscreen = computed(() => canvasStore.isFullscreen)

    // 状态图标和文本
    const statusIcon = computed(() => {
      const icons = {
        draft: 'icon-edit',
        published: 'icon-check-circle',
        running: 'icon-play-circle',
        error: 'icon-alert-circle',
        stopped: 'icon-stop-circle',
      }
      return icons[workflowStatus.value] || 'icon-help-circle'
    })

    const statusText = computed(() => {
      const texts = {
        draft: '草稿',
        published: '已发布',
        running: '运行中',
        error: '错误',
        stopped: '已停止',
      }
      return texts[workflowStatus.value] || '未知'
    })

    const saveStatusIcon = computed(() => {
      const icons = {
        saved: 'icon-check',
        saving: 'icon-loading icon-spin',
        error: 'icon-alert-triangle',
      }
      return icons[saveStatus.value] || 'icon-help'
    })

    const saveStatusText = computed(() => {
      const texts = {
        saved: '已保存',
        saving: '保存中...',
        error: '保存失败',
      }
      return texts[saveStatus.value] || '未知状态'
    })

    // 标题编辑
    const startEditTitle = () => {
      editingTitle.value = true
      editTitle.value = workflowTitle.value
      nextTick(() => {
        titleInput.value?.focus()
        titleInput.value?.select()
      })
    }

    const saveTitle = () => {
      if (editTitle.value.trim() && editTitle.value !== workflowTitle.value) {
        workflowStore.updateWorkflowName(editTitle.value.trim())
      }
      editingTitle.value = false
    }

    const cancelEditTitle = () => {
      editingTitle.value = false
      editTitle.value = workflowTitle.value
    }

    // 更多菜单
    const toggleMoreMenu = () => {
      showMoreMenu.value = !showMoreMenu.value
    }

    const closeMoreMenu = (event) => {
      if (moreDropdown.value && !moreDropdown.value.contains(event.target)) {
        showMoreMenu.value = false
      }
    }

    // 事件处理
    const handleBack = () => emit('back')
    const handleRun = () => emit('run')
    const handleStop = () => emit('stop')
    const handleDebug = () => emit('debug')
    const handleValidate = () => emit('validate')
    const handleFormat = () => emit('format')
    const handleSave = () => emit('save')
    const handleExport = () => {
      emit('export')
      showMoreMenu.value = false
    }
    const handleImport = () => {
      emit('import')
      showMoreMenu.value = false
    }
    const handleDuplicate = () => {
      emit('duplicate')
      showMoreMenu.value = false
    }
    const handleTemplate = () => {
      emit('template')
      showMoreMenu.value = false
    }
    const handleSettings = () => {
      emit('settings')
      showMoreMenu.value = false
    }
    const handleDelete = () => {
      emit('delete')
      showMoreMenu.value = false
    }
    const toggleMinimap = () => emit('toggle-minimap')
    const toggleFullscreen = () => emit('toggle-fullscreen')

    // 生命周期
    onMounted(() => {
      document.addEventListener('click', closeMoreMenu)
    })

    onUnmounted(() => {
      document.removeEventListener('click', closeMoreMenu)
    })

    return {
      // 数据
      editingTitle,
      editTitle,
      titleInput,
      showMoreMenu,
      moreDropdown,

      // 计算属性
      workflowTitle,
      workflowStatus,
      workflowVersion,
      lastModified,
      creator,
      isRunning,
      canRun,
      canDebug,
      hasChanges,
      saveStatus,
      showMinimap,
      isFullscreen,
      statusIcon,
      statusText,
      saveStatusIcon,
      saveStatusText,

      // 方法
      startEditTitle,
      saveTitle,
      cancelEditTitle,
      toggleMoreMenu,
      handleBack,
      handleRun,
      handleStop,
      handleDebug,
      handleValidate,
      handleFormat,
      handleSave,
      handleExport,
      handleImport,
      handleDuplicate,
      handleTemplate,
      handleSettings,
      handleDelete,
      toggleMinimap,
      toggleFullscreen,
    }
  },
}
</script>

<style lang="scss" scoped>
.workflow-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 16px;
  background: var(--bg-color, #ffffff);
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  position: relative;
  z-index: 100;

  &--dark {
    background: var(--bg-color-dark, #1f2937);
    border-bottom-color: var(--border-color-dark, #374151);
    color: var(--text-color-dark, #f9fafb);
  }

  &--compact {
    height: 48px;
    padding: 0 12px;
  }

  &__left {
    display: flex;
    align-items: center;
    gap: 16px;
    flex: 1;
    min-width: 0;
  }

  &__center {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 0 0 auto;
  }
}

.header-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--border-color, #d1d5db);
  background: var(--bg-color, #ffffff);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-color, #374151);
  transition: all 0.2s ease;
  white-space: nowrap;

  &:hover:not(:disabled) {
    background: var(--bg-color-hover, #f9fafb);
    border-color: var(--border-color-hover, #9ca3af);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &--back {
    padding: 8px;
    border: none;
    background: transparent;

    &:hover {
      background: var(--bg-color-hover, #f3f4f6);
    }
  }

  &--primary {
    background: var(--primary-color, #3b82f6);
    border-color: var(--primary-color, #3b82f6);
    color: white;

    &:hover:not(:disabled) {
      background: var(--primary-color-hover, #2563eb);
      border-color: var(--primary-color-hover, #2563eb);
    }

    &--loading {
      cursor: wait;
    }
  }

  &--active {
    background: var(--primary-color, #3b82f6);
    border-color: var(--primary-color, #3b82f6);
    color: white;
  }

  i {
    font-size: 16px;
  }
}

.workflow-info {
  min-width: 0;

  &__main {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 4px;
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 12px;
    color: var(--text-color-secondary, #6b7280);
  }
}

.workflow-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color, #111827);
  margin: 0;
  cursor: pointer;

  &:hover {
    color: var(--primary-color, #3b82f6);
  }
}

.workflow-title-input {
  font-size: 18px;
  font-weight: 600;
  border: 1px solid var(--primary-color, #3b82f6);
  border-radius: 4px;
  padding: 4px 8px;
  background: var(--bg-color, #ffffff);
  color: var(--text-color, #111827);
  outline: none;
}

.workflow-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;

  &--draft {
    background: var(--warning-bg, #fef3c7);
    color: var(--warning-text, #92400e);
  }

  &--published {
    background: var(--success-bg, #d1fae5);
    color: var(--success-text, #065f46);
  }

  &--running {
    background: var(--info-bg, #dbeafe);
    color: var(--info-text, #1e40af);
  }

  &--error {
    background: var(--error-bg, #fee2e2);
    color: var(--error-text, #991b1b);
  }

  &--stopped {
    background: var(--gray-bg, #f3f4f6);
    color: var(--gray-text, #374151);
  }
}

.workflow-version {
  padding: 2px 6px;
  background: var(--bg-color-secondary, #f3f4f6);
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-color-secondary, #6b7280);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;

  i {
    font-size: 12px;
  }
}

.quick-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.view-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.save-status {
  display: flex;
  align-items: center;
}

.save-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;

  &--saved {
    color: var(--success-text, #065f46);
  }

  &--saving {
    color: var(--info-text, #1e40af);
  }

  &--error {
    color: var(--error-text, #991b1b);
  }
}

.action-menu {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dropdown {
  position: relative;

  &-menu {
    position: absolute;
    top: 100%;
    right: 0;
    min-width: 180px;
    background: var(--bg-color, #ffffff);
    border: 1px solid var(--border-color, #e5e7eb);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    padding: 4px 0;
    z-index: 1000;
    margin-top: 4px;
  }

  &-item {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 12px;
    border: none;
    background: transparent;
    text-align: left;
    cursor: pointer;
    font-size: 14px;
    color: var(--text-color, #374151);
    transition: background-color 0.2s ease;

    &:hover {
      background: var(--bg-color-hover, #f3f4f6);
    }

    &--danger {
      color: var(--error-text, #dc2626);

      &:hover {
        background: var(--error-bg, #fee2e2);
      }
    }

    i {
      font-size: 16px;
      width: 16px;
    }
  }

  &-divider {
    height: 1px;
    background: var(--border-color, #e5e7eb);
    margin: 4px 0;
  }
}

// 动画
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.icon-spin {
  animation: spin 1s linear infinite;
}

// 暗色主题
.workflow-header--dark {
  .header-btn {
    background: var(--bg-color-dark, #374151);
    border-color: var(--border-color-dark, #4b5563);
    color: var(--text-color-dark, #f9fafb);

    &:hover:not(:disabled) {
      background: var(--bg-color-hover-dark, #4b5563);
      border-color: var(--border-color-hover-dark, #6b7280);
    }

    &--back {
      background: transparent;

      &:hover {
        background: var(--bg-color-hover-dark, #374151);
      }
    }
  }

  .workflow-title {
    color: var(--text-color-dark, #f9fafb);
  }

  .workflow-title-input {
    background: var(--bg-color-dark, #374151);
    color: var(--text-color-dark, #f9fafb);
    border-color: var(--primary-color, #3b82f6);
  }

  .workflow-version {
    background: var(--bg-color-secondary-dark, #111827);
    color: var(--text-color-secondary-dark, #9ca3af);
  }

  .meta-item {
    color: var(--text-color-secondary-dark, #9ca3af);
  }

  .dropdown-menu {
    background: var(--bg-color-dark, #374151);
    border-color: var(--border-color-dark, #4b5563);
  }

  .dropdown-item {
    color: var(--text-color-dark, #f9fafb);

    &:hover {
      background: var(--bg-color-hover-dark, #4b5563);
    }

    &--danger {
      color: var(--error-text, #f87171);

      &:hover {
        background: var(--error-bg-dark, #7f1d1d);
      }
    }
  }

  .dropdown-divider {
    background: var(--border-color-dark, #4b5563);
  }
}

// 紧凑模式
.workflow-header--compact {
  .workflow-info__meta {
    display: none;
  }

  .header-btn {
    padding: 6px 8px;

    span {
      display: none;
    }

    &--back {
      padding: 6px;
    }
  }

  .workflow-title {
    font-size: 16px;
  }

  .action-group {
    gap: 2px;
  }

  .quick-actions {
    gap: 8px;
  }
}
</style>
