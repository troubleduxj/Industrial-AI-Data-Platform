<template>
  <div
    class="left-toolbar"
    :class="{
      'left-toolbar--collapsed': collapsed,
      'left-toolbar--dark': isDark,
      'left-toolbar--floating': floating,
    }"
    :style="{ width: collapsed ? '48px' : width + 'px' }"
  >
    <!-- 工具栏头部 -->
    <div class="left-toolbar__header">
      <div v-if="!collapsed" class="left-toolbar__title">
        <i class="icon-tools"></i>
        <span>工具箱</span>
      </div>
      <button
        class="left-toolbar__toggle"
        :title="collapsed ? '展开工具栏' : '收起工具栏'"
        @click="toggleCollapse"
      >
        <i :class="collapsed ? 'icon-chevron-right' : 'icon-chevron-left'"></i>
      </button>
    </div>

    <!-- 工具分组 -->
    <div class="left-toolbar__content">
      <!-- 基础工具 -->
      <div class="tool-group">
        <div v-if="!collapsed" class="tool-group__header">
          <span>基础工具</span>
        </div>
        <div class="tool-group__items">
          <button
            v-for="tool in basicTools"
            :key="tool.id"
            class="tool-item"
            :class="{ 'tool-item--active': activeTool === tool.id }"
            :title="tool.name"
            @click="selectTool(tool.id)"
          >
            <i :class="tool.icon"></i>
            <span v-if="!collapsed" class="tool-item__label">{{ tool.name }}</span>
          </button>
        </div>
      </div>

      <!-- 节点工具 -->
      <div class="tool-group">
        <div v-if="!collapsed" class="tool-group__header">
          <span>节点工具</span>
        </div>
        <div class="tool-group__items">
          <button
            v-for="tool in nodeTools"
            :key="tool.id"
            class="tool-item"
            :class="{ 'tool-item--active': activeTool === tool.id }"
            :title="tool.name"
            :draggable="true"
            @click="selectTool(tool.id)"
            @dragstart="handleDragStart($event, tool)"
          >
            <i :class="tool.icon"></i>
            <span v-if="!collapsed" class="tool-item__label">{{ tool.name }}</span>
          </button>
        </div>
      </div>

      <!-- 编辑工具 -->
      <div class="tool-group">
        <div v-if="!collapsed" class="tool-group__header">
          <span>编辑工具</span>
        </div>
        <div class="tool-group__items">
          <button
            v-for="tool in editTools"
            :key="tool.id"
            class="tool-item"
            :class="{ 'tool-item--disabled': tool.disabled }"
            :title="tool.name"
            :disabled="tool.disabled"
            @click="executeTool(tool.id)"
          >
            <i :class="tool.icon"></i>
            <span v-if="!collapsed" class="tool-item__label">{{ tool.name }}</span>
            <kbd v-if="!collapsed && tool.shortcut" class="tool-item__shortcut">{{
              tool.shortcut
            }}</kbd>
          </button>
        </div>
      </div>

      <!-- 视图工具 -->
      <div class="tool-group">
        <div v-if="!collapsed" class="tool-group__header">
          <span>视图工具</span>
        </div>
        <div class="tool-group__items">
          <button
            v-for="tool in viewTools"
            :key="tool.id"
            class="tool-item"
            :title="tool.name"
            @click="executeTool(tool.id)"
          >
            <i :class="tool.icon"></i>
            <span v-if="!collapsed" class="tool-item__label">{{ tool.name }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 工具栏底部 -->
    <div v-if="!collapsed" class="left-toolbar__footer">
      <div class="toolbar-info">
        <div class="toolbar-info__item">
          <span class="label">活动工具:</span>
          <span class="value">{{ activeToolName }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useWorkflowStore } from '../../stores/workflowStore'
import { useCanvasStore } from '../../stores/canvasStore'

export default {
  name: 'LeftToolbar',
  props: {
    collapsed: {
      type: Boolean,
      default: false,
    },
    width: {
      type: Number,
      default: 200,
    },
    floating: {
      type: Boolean,
      default: false,
    },
    isDark: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['toggle-collapse', 'tool-select', 'tool-execute'],
  setup(props, { emit }) {
    const workflowStore = useWorkflowStore()
    const canvasStore = useCanvasStore()

    const activeTool = ref('select')

    // 基础工具
    const basicTools = ref([
      { id: 'select', name: '选择', icon: 'icon-cursor' },
      { id: 'pan', name: '平移', icon: 'icon-hand' },
      { id: 'connect', name: '连接', icon: 'icon-link' },
    ])

    // 节点工具
    const nodeTools = ref([
      { id: 'start', name: '开始节点', icon: 'icon-play-circle', type: 'start' },
      { id: 'process', name: '处理节点', icon: 'icon-cpu', type: 'process' },
      { id: 'condition', name: '条件节点', icon: 'icon-git-branch', type: 'condition' },
      { id: 'api', name: 'API节点', icon: 'icon-cloud', type: 'api' },
      { id: 'database', name: '数据库节点', icon: 'icon-database', type: 'database' },
      { id: 'timer', name: '定时器节点', icon: 'icon-clock', type: 'timer' },
      { id: 'email', name: '邮件节点', icon: 'icon-mail', type: 'email' },
      { id: 'file', name: '文件节点', icon: 'icon-file', type: 'file' },
      { id: 'loop', name: '循环节点', icon: 'icon-repeat', type: 'loop' },
      { id: 'end', name: '结束节点', icon: 'icon-stop-circle', type: 'end' },
    ])

    // 编辑工具
    const editTools = computed(() => [
      {
        id: 'undo',
        name: '撤销',
        icon: 'icon-undo',
        shortcut: 'Ctrl+Z',
        disabled: !workflowStore.canUndo,
      },
      {
        id: 'redo',
        name: '重做',
        icon: 'icon-redo',
        shortcut: 'Ctrl+Y',
        disabled: !workflowStore.canRedo,
      },
      {
        id: 'copy',
        name: '复制',
        icon: 'icon-copy',
        shortcut: 'Ctrl+C',
        disabled: !workflowStore.hasSelection,
      },
      {
        id: 'paste',
        name: '粘贴',
        icon: 'icon-paste',
        shortcut: 'Ctrl+V',
        disabled: !workflowStore.hasClipboard,
      },
      {
        id: 'delete',
        name: '删除',
        icon: 'icon-trash',
        shortcut: 'Del',
        disabled: !workflowStore.hasSelection,
      },
    ])

    // 视图工具
    const viewTools = ref([
      { id: 'zoom-in', name: '放大', icon: 'icon-zoom-in' },
      { id: 'zoom-out', name: '缩小', icon: 'icon-zoom-out' },
      { id: 'zoom-fit', name: '适应屏幕', icon: 'icon-maximize' },
      { id: 'zoom-reset', name: '重置缩放', icon: 'icon-refresh' },
      { id: 'grid-toggle', name: '切换网格', icon: 'icon-grid' },
      { id: 'snap-toggle', name: '切换吸附', icon: 'icon-magnet' },
    ])

    // 当前活动工具名称
    const activeToolName = computed(() => {
      const allTools = [...basicTools.value, ...nodeTools.value]
      const tool = allTools.find((t) => t.id === activeTool.value)
      return tool ? tool.name : '未知工具'
    })

    // 切换收起状态
    const toggleCollapse = () => {
      emit('toggle-collapse')
    }

    // 选择工具
    const selectTool = (toolId) => {
      activeTool.value = toolId
      emit('tool-select', toolId)
    }

    // 执行工具
    const executeTool = (toolId) => {
      emit('tool-execute', toolId)
    }

    // 处理拖拽开始
    const handleDragStart = (event, tool) => {
      event.dataTransfer.setData(
        'application/json',
        JSON.stringify({
          type: 'node',
          nodeType: tool.type,
          toolId: tool.id,
        })
      )
      event.dataTransfer.effectAllowed = 'copy'
    }

    return {
      activeTool,
      basicTools,
      nodeTools,
      editTools,
      viewTools,
      activeToolName,
      toggleCollapse,
      selectTool,
      executeTool,
      handleDragStart,
    }
  },
}
</script>

<style lang="scss" scoped>
.left-toolbar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color, #ffffff);
  border-right: 1px solid var(--border-color, #e5e7eb);
  transition: width 0.3s ease;
  position: relative;

  &--collapsed {
    .tool-group__header {
      display: none;
    }

    .tool-item {
      justify-content: center;

      &__label,
      &__shortcut {
        display: none;
      }
    }
  }

  &--dark {
    background: var(--bg-color-dark, #1f2937);
    border-right-color: var(--border-color-dark, #374151);
    color: var(--text-color-dark, #f9fafb);
  }

  &--floating {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border-radius: 8px;
    border: 1px solid var(--border-color, #e5e7eb);
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    border-bottom: 1px solid var(--border-color, #e5e7eb);
    min-height: 48px;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: var(--text-color, #374151);

    i {
      font-size: 16px;
    }
  }

  &__toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: none;
    background: transparent;
    border-radius: 4px;
    cursor: pointer;
    color: var(--text-color-secondary, #6b7280);
    transition: all 0.2s ease;

    &:hover {
      background: var(--bg-color-hover, #f3f4f6);
      color: var(--text-color, #374151);
    }
  }

  &__content {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  &__footer {
    padding: 12px;
    border-top: 1px solid var(--border-color, #e5e7eb);
    background: var(--bg-color-secondary, #f9fafb);
  }
}

.tool-group {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }

  &__header {
    padding: 8px 4px 4px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-color-secondary, #6b7280);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  &__items {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-color, #374151);
  transition: all 0.2s ease;
  text-align: left;
  position: relative;

  &:hover:not(&--disabled) {
    background: var(--bg-color-hover, #f3f4f6);
  }

  &--active {
    background: var(--primary-color, #3b82f6);
    color: white;

    &:hover {
      background: var(--primary-color-hover, #2563eb);
    }
  }

  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  i {
    font-size: 16px;
    width: 16px;
    text-align: center;
  }

  &__label {
    flex: 1;
    font-size: 14px;
  }

  &__shortcut {
    font-size: 11px;
    padding: 2px 4px;
    background: var(--bg-color-tertiary, #e5e7eb);
    border-radius: 3px;
    color: var(--text-color-secondary, #6b7280);
  }
}

.toolbar-info {
  &__item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;

    .label {
      color: var(--text-color-secondary, #6b7280);
    }

    .value {
      font-weight: 500;
      color: var(--text-color, #374151);
    }
  }
}

// 暗色主题
.left-toolbar--dark {
  .left-toolbar__header {
    border-bottom-color: var(--border-color-dark, #374151);
  }

  .left-toolbar__title {
    color: var(--text-color-dark, #f9fafb);
  }

  .left-toolbar__toggle {
    color: var(--text-color-secondary-dark, #9ca3af);

    &:hover {
      background: var(--bg-color-hover-dark, #374151);
      color: var(--text-color-dark, #f9fafb);
    }
  }

  .left-toolbar__footer {
    border-top-color: var(--border-color-dark, #374151);
    background: var(--bg-color-secondary-dark, #111827);
  }

  .tool-group__header {
    color: var(--text-color-secondary-dark, #9ca3af);
  }

  .tool-item {
    color: var(--text-color-dark, #f9fafb);

    &:hover:not(&--disabled) {
      background: var(--bg-color-hover-dark, #374151);
    }

    &__shortcut {
      background: var(--bg-color-tertiary-dark, #374151);
      color: var(--text-color-secondary-dark, #9ca3af);
    }
  }

  .toolbar-info__item {
    .label {
      color: var(--text-color-secondary-dark, #9ca3af);
    }

    .value {
      color: var(--text-color-dark, #f9fafb);
    }
  }
}
</style>
