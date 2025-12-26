<template>
  <div class="workflow-main-layout" :class="layoutClasses">
    <!-- 顶部工具栏区域 -->
    <div v-if="showHeader" class="layout-header">
      <slot name="header">
        <WorkflowToolbar
          :workflow="workflow"
          :is-modified="isModified"
          :is-running="isRunning"
          :zoom-level="zoomLevel"
          @save="$emit('save')"
          @run="$emit('run')"
          @stop="$emit('stop')"
          @export="$emit('export')"
          @import="$emit('import')"
          @undo="$emit('undo')"
          @redo="$emit('redo')"
          @zoom-in="$emit('zoom-in')"
          @zoom-out="$emit('zoom-out')"
          @zoom-fit="$emit('zoom-fit')"
          @zoom-reset="$emit('zoom-reset')"
        />
      </slot>
    </div>

    <!-- 主要内容区域 -->
    <div class="layout-main">
      <!-- 左侧面板 -->
      <div
        v-if="showLeftSidebar"
        class="layout-sidebar layout-sidebar-left"
        :style="{ width: leftSidebarWidth + 'px' }"
      >
        <div class="sidebar-header">
          <slot name="left-sidebar-header">
            <h3>节点库</h3>
          </slot>
        </div>
        <div class="sidebar-content">
          <slot name="left-sidebar">
            <NodeLibrary
              :categories="nodeCategories"
              :search-query="nodeSearchQuery"
              @node-drag-start="$emit('node-drag-start', $event)"
              @search="handleNodeSearch"
            />
          </slot>
        </div>
        <div class="sidebar-resizer sidebar-resizer-right" @mousedown="startResize('left')"></div>
      </div>

      <!-- 中央画布区域 -->
      <div class="layout-center">
        <div class="canvas-container">
          <slot name="canvas">
            <!-- 画布内容由父组件提供 -->
          </slot>
        </div>

        <!-- 小地图 -->
        <div v-if="showMiniMap" class="minimap-container">
          <MiniMap
            :workflow="workflow"
            :viewport="viewport"
            :zoom-level="zoomLevel"
            @viewport-change="$emit('viewport-change', $event)"
          />
        </div>
      </div>

      <!-- 右侧面板 -->
      <div
        v-if="showRightSidebar"
        class="layout-sidebar layout-sidebar-right"
        :style="{ width: rightSidebarWidth + 'px' }"
      >
        <div class="sidebar-resizer sidebar-resizer-left" @mousedown="startResize('right')"></div>
        <div class="sidebar-header">
          <slot name="right-sidebar-header">
            <h3>属性面板</h3>
          </slot>
        </div>
        <div class="sidebar-content">
          <slot name="right-sidebar">
            <PropertyPanel
              :selected-items="selectedItems"
              :workflow="workflow"
              @property-change="$emit('property-change', $event)"
            />
          </slot>
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <div v-if="showFooter" class="layout-footer">
      <slot name="footer">
        <StatusBar
          :workflow="workflow"
          :selected-count="selectedItems.length"
          :zoom-level="zoomLevel"
          :mouse-position="mousePosition"
          :is-modified="isModified"
          :is-running="isRunning"
        />
      </slot>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import WorkflowToolbar from '../UI/WorkflowToolbar.vue'
import NodeLibrary from '../UI/NodeLibrary.vue'
import PropertyPanel from '../UI/PropertyPanel.vue'
import MiniMap from '../UI/MiniMap.vue'
import StatusBar from '../UI/StatusBar.vue'

export default {
  name: 'MainLayout',
  components: {
    WorkflowToolbar,
    NodeLibrary,
    PropertyPanel,
    MiniMap,
    StatusBar,
  },
  props: {
    // 布局配置
    showHeader: {
      type: Boolean,
      default: true,
    },
    showFooter: {
      type: Boolean,
      default: true,
    },
    showLeftSidebar: {
      type: Boolean,
      default: true,
    },
    showRightSidebar: {
      type: Boolean,
      default: true,
    },
    showMiniMap: {
      type: Boolean,
      default: true,
    },

    // 侧边栏宽度
    defaultLeftSidebarWidth: {
      type: Number,
      default: 280,
    },
    defaultRightSidebarWidth: {
      type: Number,
      default: 320,
    },
    minSidebarWidth: {
      type: Number,
      default: 200,
    },
    maxSidebarWidth: {
      type: Number,
      default: 500,
    },

    // 工作流数据
    workflow: {
      type: Object,
      required: true,
    },
    selectedItems: {
      type: Array,
      default: () => [],
    },
    nodeCategories: {
      type: Array,
      default: () => [],
    },

    // 状态
    isModified: {
      type: Boolean,
      default: false,
    },
    isRunning: {
      type: Boolean,
      default: false,
    },
    zoomLevel: {
      type: Number,
      default: 1,
    },
    viewport: {
      type: Object,
      default: () => ({ x: 0, y: 0, width: 0, height: 0 }),
    },
    mousePosition: {
      type: Object,
      default: () => ({ x: 0, y: 0 }),
    },

    // 主题
    theme: {
      type: String,
      default: 'light',
      validator: (value: string) => ['light', 'dark'].includes(value),
    },

    // 布局模式
    layoutMode: {
      type: String,
      default: 'normal',
      validator: (value: string) => ['normal', 'compact', 'fullscreen'].includes(value),
    },
  },
  emits: [
    'save',
    'run',
    'stop',
    'export',
    'import',
    'undo',
    'redo',
    'zoom-in',
    'zoom-out',
    'zoom-fit',
    'zoom-reset',
    'node-drag-start',
    'property-change',
    'viewport-change',
  ],
  setup(props, { emit }) {
    // 侧边栏宽度
    const leftSidebarWidth = ref(props.defaultLeftSidebarWidth)
    const rightSidebarWidth = ref(props.defaultRightSidebarWidth)

    // 节点搜索
    const nodeSearchQuery = ref('')

    // 调整大小状态
    const isResizing = ref(false)
    const resizingPanel = ref('')
    const startX = ref(0)
    const startWidth = ref(0)

    // 布局类名
    const layoutClasses = computed(() => {
      return {
        [`theme-${props.theme}`]: true,
        [`layout-${props.layoutMode}`]: true,
        'is-running': props.isRunning,
        'is-modified': props.isModified,
        'no-left-sidebar': !props.showLeftSidebar,
        'no-right-sidebar': !props.showRightSidebar,
        'no-header': !props.showHeader,
        'no-footer': !props.showFooter,
      }
    })

    // 开始调整大小
    const startResize = (panel) => {
      isResizing.value = true
      resizingPanel.value = panel
      startX.value = event.clientX
      startWidth.value = panel === 'left' ? leftSidebarWidth.value : rightSidebarWidth.value

      document.addEventListener('mousemove', handleResize)
      document.addEventListener('mouseup', stopResize)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    }

    // 处理调整大小
    const handleResize = (event) => {
      if (!isResizing.value) return

      const deltaX = event.clientX - startX.value
      let newWidth

      if (resizingPanel.value === 'left') {
        newWidth = startWidth.value + deltaX
      } else {
        newWidth = startWidth.value - deltaX
      }

      // 限制宽度范围
      newWidth = Math.max(props.minSidebarWidth, Math.min(props.maxSidebarWidth, newWidth))

      if (resizingPanel.value === 'left') {
        leftSidebarWidth.value = newWidth
      } else {
        rightSidebarWidth.value = newWidth
      }
    }

    // 停止调整大小
    const stopResize = () => {
      isResizing.value = false
      resizingPanel.value = ''

      document.removeEventListener('mousemove', handleResize)
      document.removeEventListener('mouseup', stopResize)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    // 处理节点搜索
    const handleNodeSearch = (query) => {
      nodeSearchQuery.value = query
    }

    // 键盘快捷键
    const handleKeydown = (event) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 's':
            event.preventDefault()
            emit('save')
            break
          case 'z':
            event.preventDefault()
            if (event.shiftKey) {
              emit('redo')
            } else {
              emit('undo')
            }
            break
          case '=':
          case '+':
            event.preventDefault()
            emit('zoom-in')
            break
          case '-':
            event.preventDefault()
            emit('zoom-out')
            break
          case '0':
            event.preventDefault()
            emit('zoom-reset')
            break
        }
      }
    }

    onMounted(() => {
      document.addEventListener('keydown', handleKeydown)
    })

    onUnmounted(() => {
      document.removeEventListener('keydown', handleKeydown)
      document.removeEventListener('mousemove', handleResize)
      document.removeEventListener('mouseup', stopResize)
    })

    return {
      leftSidebarWidth,
      rightSidebarWidth,
      nodeSearchQuery,
      layoutClasses,
      startResize,
      handleNodeSearch,
    }
  },
}
</script>

<style scoped>
.workflow-main-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-color, #f5f5f5);
  color: var(--text-color, #333);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 主题样式 */
.theme-light {
  --bg-color: #f5f5f5;
  --text-color: #333;
  --border-color: #e0e0e0;
  --sidebar-bg: #fff;
  --header-bg: #fff;
  --footer-bg: #fff;
}

.theme-dark {
  --bg-color: #1e1e1e;
  --text-color: #fff;
  --border-color: #404040;
  --sidebar-bg: #252526;
  --header-bg: #2d2d30;
  --footer-bg: #2d2d30;
}

/* 头部 */
.layout-header {
  flex-shrink: 0;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  z-index: 100;
}

/* 主要内容区域 */
.layout-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 侧边栏 */
.layout-sidebar {
  flex-shrink: 0;
  background: var(--sidebar-bg);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: relative;
}

.layout-sidebar-left {
  border-right: 1px solid var(--border-color);
}

.layout-sidebar-right {
  border-left: 1px solid var(--border-color);
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--sidebar-bg);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}

.sidebar-content {
  flex: 1;
  overflow: hidden;
}

/* 调整大小手柄 */
.sidebar-resizer {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  background: transparent;
  z-index: 10;
}

.sidebar-resizer:hover {
  background: var(--primary-color, #007acc);
}

.sidebar-resizer-right {
  right: -2px;
}

.sidebar-resizer-left {
  left: -2px;
}

/* 中央区域 */
.layout-center {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.canvas-container {
  width: 100%;
  height: 100%;
  position: relative;
}

/* 小地图 */
.minimap-container {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 50;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: var(--sidebar-bg);
  border: 1px solid var(--border-color);
}

/* 底部 */
.layout-footer {
  flex-shrink: 0;
  background: var(--footer-bg);
  border-top: 1px solid var(--border-color);
  z-index: 100;
}

/* 布局模式 */
.layout-compact .sidebar-header {
  padding: 8px 12px;
}

.layout-compact .sidebar-header h3 {
  font-size: 12px;
}

.layout-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

.layout-fullscreen .layout-header,
.layout-fullscreen .layout-footer {
  display: none;
}

/* 隐藏侧边栏时的样式 */
.no-left-sidebar .layout-center,
.no-right-sidebar .layout-center {
  border: none;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .layout-sidebar {
    min-width: 200px;
  }
}

@media (max-width: 768px) {
  .layout-main {
    flex-direction: column;
  }

  .layout-sidebar {
    width: 100% !important;
    height: 200px;
    border: none;
    border-top: 1px solid var(--border-color);
  }

  .sidebar-resizer {
    display: none;
  }

  .minimap-container {
    display: none;
  }
}
</style>
