<template>
  <div class="sidebar-layout" :class="sidebarClasses">
    <!-- 侧边栏头部 -->
    <div v-if="showHeader" class="sidebar-header">
      <div class="sidebar-title">
        <slot name="title">
          <h3>{{ title }}</h3>
        </slot>
      </div>

      <!-- 头部操作按钮 -->
      <div v-if="showActions" class="sidebar-actions">
        <slot name="actions">
          <button
            v-if="collapsible"
            class="action-btn"
            :title="isCollapsed ? '展开' : '收起'"
            @click="toggleCollapse"
          >
            <i :class="isCollapsed ? 'icon-expand' : 'icon-collapse'"></i>
          </button>

          <button v-if="closable" class="action-btn" title="关闭" @click="$emit('close')">
            <i class="icon-close"></i>
          </button>
        </slot>
      </div>
    </div>

    <!-- 侧边栏内容 -->
    <div v-show="!isCollapsed" class="sidebar-content">
      <!-- 标签页 -->
      <div v-if="tabs.length > 0" class="sidebar-tabs">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="setActiveTab(tab.key)"
        >
          <i v-if="tab.icon" :class="tab.icon"></i>
          <span>{{ tab.label }}</span>
        </div>
      </div>

      <!-- 搜索框 -->
      <div v-if="searchable" class="sidebar-search">
        <div class="search-input-wrapper">
          <i class="icon-search"></i>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            :placeholder="searchPlaceholder"
            @input="handleSearch"
          />
          <button v-if="searchQuery" class="clear-btn" @click="clearSearch">
            <i class="icon-clear"></i>
          </button>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="sidebar-main">
        <slot :active-tab="activeTab" :search-query="searchQuery">
          <!-- 默认内容 -->
        </slot>
      </div>

      <!-- 底部操作区域 -->
      <div v-if="$slots.footer" class="sidebar-footer">
        <slot name="footer"></slot>
      </div>
    </div>

    <!-- 调整大小手柄 -->
    <div
      v-if="resizable && !isCollapsed"
      class="resize-handle"
      :class="`resize-handle-${position}`"
      @mousedown="startResize"
    ></div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'

export default {
  name: 'SidebarLayout',
  props: {
    // 基本配置
    title: {
      type: String,
      default: '',
    },
    position: {
      type: String,
      default: 'left',
      validator: (value: string) => ['left', 'right'].includes(value),
    },
    width: {
      type: Number,
      default: 280,
    },
    minWidth: {
      type: Number,
      default: 200,
    },
    maxWidth: {
      type: Number,
      default: 500,
    },

    // 显示控制
    showHeader: {
      type: Boolean,
      default: true,
    },
    showActions: {
      type: Boolean,
      default: true,
    },

    // 功能开关
    collapsible: {
      type: Boolean,
      default: true,
    },
    closable: {
      type: Boolean,
      default: false,
    },
    resizable: {
      type: Boolean,
      default: true,
    },
    searchable: {
      type: Boolean,
      default: false,
    },

    // 状态
    collapsed: {
      type: Boolean,
      default: false,
    },

    // 标签页
    tabs: {
      type: Array,
      default: () => [],
    },
    defaultActiveTab: {
      type: String,
      default: '',
    },

    // 搜索
    searchPlaceholder: {
      type: String,
      default: '搜索...',
    },

    // 主题
    theme: {
      type: String,
      default: 'light',
      validator: (value: string) => ['light', 'dark'].includes(value),
    },
  },
  emits: [
    'update:collapsed',
    'update:width',
    'close',
    'tab-change',
    'search',
    'resize-start',
    'resize',
    'resize-end',
  ],
  setup(props, { emit }) {
    // 状态
    const isCollapsed = ref(props.collapsed)
    const currentWidth = ref(props.width)
    const activeTab = ref(props.defaultActiveTab || props.tabs[0]?.key || '')
    const searchQuery = ref('')

    // 调整大小状态
    const isResizing = ref(false)
    const startX = ref(0)
    const startWidth = ref(0)

    // 计算样式类
    const sidebarClasses = computed(() => {
      return {
        [`position-${props.position}`]: true,
        [`theme-${props.theme}`]: true,
        collapsed: isCollapsed.value,
        resizable: props.resizable,
        'has-tabs': props.tabs.length > 0,
        searchable: props.searchable,
      }
    })

    // 监听collapsed属性变化
    watch(
      () => props.collapsed,
      (newVal) => {
        isCollapsed.value = newVal
      }
    )

    // 监听width属性变化
    watch(
      () => props.width,
      (newVal) => {
        currentWidth.value = newVal
      }
    )

    // 监听isCollapsed变化，发出事件
    watch(isCollapsed, (newVal) => {
      emit('update:collapsed', newVal)
    })

    // 监听currentWidth变化，发出事件
    watch(currentWidth, (newVal) => {
      emit('update:width', newVal)
    })

    // 切换折叠状态
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
    }

    // 设置活动标签
    const setActiveTab = (tabKey) => {
      if (activeTab.value !== tabKey) {
        activeTab.value = tabKey
        emit('tab-change', tabKey)
      }
    }

    // 处理搜索
    const handleSearch = () => {
      emit('search', searchQuery.value)
    }

    // 清除搜索
    const clearSearch = () => {
      searchQuery.value = ''
      emit('search', '')
    }

    // 开始调整大小
    const startResize = (event) => {
      if (!props.resizable) return

      isResizing.value = true
      startX.value = event.clientX
      startWidth.value = currentWidth.value

      document.addEventListener('mousemove', handleResize)
      document.addEventListener('mouseup', stopResize)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'

      emit('resize-start', {
        width: currentWidth.value,
        position: props.position,
      })
    }

    // 处理调整大小
    const handleResize = (event) => {
      if (!isResizing.value) return

      const deltaX = event.clientX - startX.value
      let newWidth

      if (props.position === 'left') {
        newWidth = startWidth.value + deltaX
      } else {
        newWidth = startWidth.value - deltaX
      }

      // 限制宽度范围
      newWidth = Math.max(props.minWidth, Math.min(props.maxWidth, newWidth))
      currentWidth.value = newWidth

      emit('resize', {
        width: newWidth,
        position: props.position,
      })
    }

    // 停止调整大小
    const stopResize = () => {
      if (!isResizing.value) return

      isResizing.value = false

      document.removeEventListener('mousemove', handleResize)
      document.removeEventListener('mouseup', stopResize)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''

      emit('resize-end', {
        width: currentWidth.value,
        position: props.position,
      })
    }

    return {
      isCollapsed,
      currentWidth,
      activeTab,
      searchQuery,
      sidebarClasses,
      toggleCollapse,
      setActiveTab,
      handleSearch,
      clearSearch,
      startResize,
    }
  },
}
</script>

<style scoped>
.sidebar-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--sidebar-bg, #fff);
  border: 1px solid var(--border-color, #e0e0e0);
  position: relative;
}

/* 主题样式 */
.theme-light {
  --sidebar-bg: #fff;
  --sidebar-header-bg: #f8f9fa;
  --text-color: #333;
  --text-secondary: #666;
  --border-color: #e0e0e0;
  --hover-bg: #f5f5f5;
  --active-bg: #e3f2fd;
  --active-color: #1976d2;
}

.theme-dark {
  --sidebar-bg: #252526;
  --sidebar-header-bg: #2d2d30;
  --text-color: #fff;
  --text-secondary: #ccc;
  --border-color: #404040;
  --hover-bg: #2a2d2e;
  --active-bg: #094771;
  --active-color: #4fc3f7;
}

/* 位置样式 */
.position-left {
  border-right: 1px solid var(--border-color);
}

.position-right {
  border-left: 1px solid var(--border-color);
}

/* 头部 */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--sidebar-header-bg);
  border-bottom: 1px solid var(--border-color);
  min-height: 48px;
}

.sidebar-title h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}

.sidebar-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--hover-bg);
  color: var(--text-color);
}

/* 内容区域 */
.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 标签页 */
.sidebar-tabs {
  display: flex;
  background: var(--sidebar-header-bg);
  border-bottom: 1px solid var(--border-color);
}

.tab-item {
  flex: 1;
  padding: 8px 12px;
  text-align: center;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.tab-item:hover {
  background: var(--hover-bg);
  color: var(--text-color);
}

.tab-item.active {
  color: var(--active-color);
  border-bottom-color: var(--active-color);
  background: var(--active-bg);
}

/* 搜索框 */
.sidebar-search {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  width: 100%;
  padding: 6px 8px 6px 28px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--sidebar-bg);
  color: var(--text-color);
  font-size: 12px;
}

.search-input:focus {
  outline: none;
  border-color: var(--active-color);
}

.icon-search {
  position: absolute;
  left: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  z-index: 1;
}

.clear-btn {
  position: absolute;
  right: 4px;
  width: 16px;
  height: 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-btn:hover {
  background: var(--hover-bg);
}

/* 主要内容 */
.sidebar-main {
  flex: 1;
  overflow: auto;
}

/* 底部 */
.sidebar-footer {
  border-top: 1px solid var(--border-color);
  padding: 8px 16px;
  background: var(--sidebar-header-bg);
}

/* 调整大小手柄 */
.resize-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  background: transparent;
  z-index: 10;
}

.resize-handle:hover {
  background: var(--active-color);
}

.resize-handle-left {
  right: -2px;
}

.resize-handle-right {
  left: -2px;
}

/* 折叠状态 */
.collapsed {
  width: 40px !important;
  min-width: 40px !important;
}

.collapsed .sidebar-content {
  display: none;
}

/* 图标字体 */
.icon-expand::before {
  content: '▶';
}
.icon-collapse::before {
  content: '◀';
}
.icon-close::before {
  content: '✕';
}
.icon-search::before {
  content: '🔍';
}
.icon-clear::before {
  content: '✕';
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar-layout {
    width: 100% !important;
    height: auto;
    max-height: 300px;
  }

  .resize-handle {
    display: none;
  }

  .sidebar-tabs {
    overflow-x: auto;
  }

  .tab-item {
    flex-shrink: 0;
    min-width: 80px;
  }
}
</style>
