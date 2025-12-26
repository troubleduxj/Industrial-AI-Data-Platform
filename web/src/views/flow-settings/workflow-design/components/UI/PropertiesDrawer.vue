<template>
  <div class="properties-drawer" :class="drawerClasses">
    <!-- 抽屉遮罩 -->
    <div v-if="visible && overlay" class="drawer-overlay" @click="handleOverlayClick"></div>

    <!-- 抽屉内容 -->
    <div class="drawer-content" :style="drawerStyle">
      <!-- 抽屉头部 -->
      <div class="drawer-header">
        <div class="header-content">
          <div class="drawer-title">
            <span v-if="titleIcon" class="title-icon">{{ titleIcon }}</span>
            <span class="title-text">{{ title }}</span>
            <span v-if="itemCount > 0" class="item-count">({{ itemCount }})</span>
          </div>
          <div v-if="subtitle" class="header-subtitle">
            {{ subtitle }}
          </div>
        </div>
        <div class="header-actions">
          <button v-if="resizable" class="action-btn" title="调整大小" @mousedown="startResize">
            <span class="icon">↔</span>
          </button>
          <button
            class="action-btn"
            :class="{ active: isPinned }"
            title="固定抽屉"
            @click="togglePin"
          >
            <span class="icon">📌</span>
          </button>
          <button class="action-btn close-btn" title="关闭抽屉" @click="handleClose">
            <span class="icon">✕</span>
          </button>
        </div>
      </div>

      <!-- 抽屉工具栏 -->
      <div v-if="showToolbar" class="drawer-toolbar">
        <div class="toolbar-left">
          <slot name="toolbar-left">
            <button class="toolbar-btn" title="刷新" @click="handleRefresh">
              <span class="icon">🔄</span>
            </button>
            <button class="toolbar-btn" title="展开全部" @click="handleExpandAll">
              <span class="icon">📂</span>
            </button>
            <button class="toolbar-btn" title="收起全部" @click="handleCollapseAll">
              <span class="icon">📁</span>
            </button>
          </slot>
        </div>
        <div class="toolbar-right">
          <slot name="toolbar-right">
            <div v-if="searchable" class="search-box">
              <input
                v-model="searchQuery"
                type="text"
                class="search-input"
                :placeholder="searchPlaceholder"
                @input="handleSearch"
              />
              <button v-if="searchQuery" class="search-clear" @click="clearSearch">
                <span class="icon">✕</span>
              </button>
            </div>
          </slot>
        </div>
      </div>

      <!-- 抽屉主体内容 -->
      <div ref="drawerBody" class="drawer-body">
        <div class="body-content">
          <!-- 默认插槽 -->
          <slot>
            <!-- 属性列表 -->
            <div v-if="properties.length > 0" class="properties-list">
              <div v-for="group in filteredGroups" :key="group.name" class="property-group">
                <div
                  class="group-header"
                  :class="{ collapsed: collapsedGroups.includes(group.name) }"
                  @click="toggleGroup(group.name)"
                >
                  <span class="group-icon">{{ group.collapsed ? '▶' : '▼' }}</span>
                  <span class="group-title">{{ group.title }}</span>
                  <span class="group-count">({{ group.properties.length }})</span>
                </div>
                <div v-if="!collapsedGroups.includes(group.name)" class="group-content">
                  <div
                    v-for="property in group.properties"
                    :key="property.key"
                    class="property-item"
                    :class="{
                      readonly: property.readonly,
                      required: property.required,
                      modified: property.modified,
                    }"
                  >
                    <div class="property-label">
                      <span class="label-text">{{ property.label }}</span>
                      <span v-if="property.required" class="required-mark">*</span>
                      <span v-if="property.modified" class="modified-mark">●</span>
                    </div>
                    <div class="property-value">
                      <component
                        :is="getPropertyComponent(property.type)"
                        v-model="property.value"
                        v-bind="property.props"
                        @change="handlePropertyChange(property)"
                      />
                    </div>
                    <div v-if="property.description" class="property-description">
                      {{ property.description }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-else class="empty-state">
              <div class="empty-icon">📄</div>
              <div class="empty-text">{{ emptyText }}</div>
            </div>
          </slot>
        </div>
      </div>

      <!-- 抽屉底部 -->
      <div v-if="showFooter" class="drawer-footer">
        <slot name="footer">
          <div class="footer-actions">
            <button class="footer-btn secondary" :disabled="!hasChanges" @click="handleReset">
              重置
            </button>
            <button class="footer-btn primary" :disabled="!hasChanges" @click="handleApply">
              应用
            </button>
          </div>
        </slot>
      </div>
    </div>

    <!-- 调整大小手柄 -->
    <div v-if="resizable && visible" class="resize-handle" @mousedown="startResize"></div>
  </div>
</template>

<script>
export default {
  name: 'PropertiesDrawer',
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    position: {
      type: String,
      default: 'right', // 'left', 'right', 'top', 'bottom'
      validator: (value: string) => ['left', 'right', 'top', 'bottom'].includes(value),
    },
    width: {
      type: [Number, String],
      default: 320,
    },
    height: {
      type: [Number, String],
      default: '100%',
    },
    title: {
      type: String,
      default: '属性',
    },
    titleIcon: {
      type: String,
      default: '⚙️',
    },
    subtitle: {
      type: String,
      default: '',
    },
    overlay: {
      type: Boolean,
      default: true,
    },
    closeOnOverlay: {
      type: Boolean,
      default: true,
    },
    resizable: {
      type: Boolean,
      default: true,
    },
    pinnable: {
      type: Boolean,
      default: true,
    },
    showToolbar: {
      type: Boolean,
      default: true,
    },
    showFooter: {
      type: Boolean,
      default: true,
    },
    searchable: {
      type: Boolean,
      default: true,
    },
    searchPlaceholder: {
      type: String,
      default: '搜索属性...',
    },
    properties: {
      type: Array,
      default: () => [],
    },
    emptyText: {
      type: String,
      default: '暂无属性',
    },
  },
  data() {
    return {
      isPinned: false,
      searchQuery: '',
      collapsedGroups: [],
      drawerWidth: this.width,
      drawerHeight: this.height,
      isResizing: false,
      resizeStartX: 0,
      resizeStartY: 0,
      resizeStartWidth: 0,
      resizeStartHeight: 0,
    }
  },
  computed: {
    drawerClasses() {
      return {
        visible: this.visible,
        pinned: this.isPinned,
        resizing: this.isResizing,
        [`position-${this.position}`]: true,
      }
    },
    drawerStyle() {
      const style = {}

      if (this.position === 'left' || this.position === 'right') {
        style.width =
          typeof this.drawerWidth === 'number' ? `${this.drawerWidth}px` : this.drawerWidth
        style.height = this.drawerHeight
      } else {
        style.width = this.drawerWidth
        style.height =
          typeof this.drawerHeight === 'number' ? `${this.drawerHeight}px` : this.drawerHeight
      }

      return style
    },
    itemCount() {
      return this.properties.length
    },
    groupedProperties() {
      const groups = {}

      this.properties.forEach((property) => {
        const groupName = property.group || 'default'
        if (!groups[groupName]) {
          groups[groupName] = {
            name: groupName,
            title: property.groupTitle || groupName,
            properties: [],
          }
        }
        groups[groupName].properties.push(property)
      })

      return Object.values(groups)
    },
    filteredGroups() {
      if (!this.searchQuery) {
        return this.groupedProperties
      }

      const query = this.searchQuery.toLowerCase()
      return this.groupedProperties
        .map((group) => ({
          ...group,
          properties: group.properties.filter(
            (property) =>
              property.label.toLowerCase().includes(query) ||
              property.key.toLowerCase().includes(query) ||
              (property.description && property.description.toLowerCase().includes(query))
          ),
        }))
        .filter((group) => group.properties.length > 0)
    },
    hasChanges() {
      return this.properties.some((property) => property.modified)
    },
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          this.adjustPosition()
        })
      }
    },
  },
  mounted() {
    this.setupResizeListeners()
  },
  beforeUnmount() {
    this.removeResizeListeners()
  },
  methods: {
    // 处理遮罩点击
    handleOverlayClick() {
      if (this.closeOnOverlay && !this.isPinned) {
        this.handleClose()
      }
    },

    // 关闭抽屉
    handleClose() {
      this.$emit('close')
    },

    // 切换固定状态
    togglePin() {
      this.isPinned = !this.isPinned
      this.$emit('pin-change', this.isPinned)
    },

    // 刷新
    handleRefresh() {
      this.$emit('refresh')
    },

    // 展开全部
    handleExpandAll() {
      this.collapsedGroups = []
    },

    // 收起全部
    handleCollapseAll() {
      this.collapsedGroups = this.groupedProperties.map((group) => group.name)
    },

    // 搜索处理
    handleSearch() {
      this.$emit('search', this.searchQuery)
    },

    // 清空搜索
    clearSearch() {
      this.searchQuery = ''
      this.handleSearch()
    },

    // 切换分组
    toggleGroup(groupName) {
      const index = this.collapsedGroups.indexOf(groupName)
      if (index > -1) {
        this.collapsedGroups.splice(index, 1)
      } else {
        this.collapsedGroups.push(groupName)
      }
    },

    // 获取属性组件
    getPropertyComponent(type) {
      const components = {
        text: 'input',
        number: 'input',
        boolean: 'input',
        select: 'select',
        textarea: 'textarea',
      }
      return components[type] || 'input'
    },

    // 属性值变化
    handlePropertyChange(property) {
      property.modified = true
      this.$emit('property-change', {
        key: property.key,
        value: property.value,
        property,
      })
    },

    // 重置
    handleReset() {
      this.$emit('reset')
    },

    // 应用
    handleApply() {
      this.$emit('apply')
    },

    // 开始调整大小
    startResize(event) {
      event.preventDefault()
      this.isResizing = true
      this.resizeStartX = event.clientX
      this.resizeStartY = event.clientY
      this.resizeStartWidth = parseInt(this.drawerWidth)
      this.resizeStartHeight = parseInt(this.drawerHeight)

      document.addEventListener('mousemove', this.handleResize)
      document.addEventListener('mouseup', this.stopResize)
    },

    // 处理调整大小
    handleResize(event) {
      if (!this.isResizing) return

      const deltaX = event.clientX - this.resizeStartX
      const deltaY = event.clientY - this.resizeStartY

      if (this.position === 'right') {
        this.drawerWidth = Math.max(200, this.resizeStartWidth - deltaX)
      } else if (this.position === 'left') {
        this.drawerWidth = Math.max(200, this.resizeStartWidth + deltaX)
      } else if (this.position === 'bottom') {
        this.drawerHeight = Math.max(200, this.resizeStartHeight - deltaY)
      } else if (this.position === 'top') {
        this.drawerHeight = Math.max(200, this.resizeStartHeight + deltaY)
      }
    },

    // 停止调整大小
    stopResize() {
      this.isResizing = false
      document.removeEventListener('mousemove', this.handleResize)
      document.removeEventListener('mouseup', this.stopResize)

      this.$emit('resize', {
        width: this.drawerWidth,
        height: this.drawerHeight,
      })
    },

    // 设置调整大小监听器
    setupResizeListeners() {
      // 可以添加窗口大小变化监听
    },

    // 移除调整大小监听器
    removeResizeListeners() {
      document.removeEventListener('mousemove', this.handleResize)
      document.removeEventListener('mouseup', this.stopResize)
    },

    // 调整位置
    adjustPosition() {
      // 根据屏幕大小调整抽屉位置
    },
  },
}
</script>

<style scoped>
.properties-drawer {
  position: fixed;
  z-index: 1000;
  transition: all 0.3s ease;
  pointer-events: none;
}

.properties-drawer.visible {
  pointer-events: auto;
}

/* 位置样式 */
.properties-drawer.position-right {
  top: 0;
  right: 0;
  height: 100vh;
}

.properties-drawer.position-right .drawer-content {
  transform: translateX(100%);
}

.properties-drawer.position-right.visible .drawer-content {
  transform: translateX(0);
}

.properties-drawer.position-left {
  top: 0;
  left: 0;
  height: 100vh;
}

.properties-drawer.position-left .drawer-content {
  transform: translateX(-100%);
}

.properties-drawer.position-left.visible .drawer-content {
  transform: translateX(0);
}

.properties-drawer.position-top {
  top: 0;
  left: 0;
  width: 100vw;
}

.properties-drawer.position-top .drawer-content {
  transform: translateY(-100%);
}

.properties-drawer.position-top.visible .drawer-content {
  transform: translateY(0);
}

.properties-drawer.position-bottom {
  bottom: 0;
  left: 0;
  width: 100vw;
}

.properties-drawer.position-bottom .drawer-content {
  transform: translateY(100%);
}

.properties-drawer.position-bottom.visible .drawer-content {
  transform: translateY(0);
}

/* 遮罩 */
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  z-index: -1;
}

/* 抽屉内容 */
.drawer-content {
  background: var(--bg-color, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: transform 0.3s ease;
}

.properties-drawer.position-right .drawer-content,
.properties-drawer.position-left .drawer-content {
  border-radius: 0;
}

.properties-drawer.position-top .drawer-content {
  border-radius: 0 0 8px 8px;
}

.properties-drawer.position-bottom .drawer-content {
  border-radius: 8px 8px 0 0;
}

/* 头部 */
.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--header-bg, #f5f5f5);
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.header-content {
  flex: 1;
  min-width: 0;
}

.drawer-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color, #333333);
  margin-bottom: 2px;
}

.title-icon {
  font-size: 18px;
}

.item-count {
  font-size: 12px;
  color: var(--text-color-secondary, #666666);
  font-weight: normal;
}

.header-subtitle {
  font-size: 12px;
  color: var(--text-color-secondary, #666666);
}

.header-actions {
  display: flex;
  gap: 4px;
  margin-left: 12px;
}

.action-btn {
  background: none;
  border: none;
  padding: 6px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-color-secondary, #666666);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--hover-bg, #e0e0e0);
  color: var(--text-color, #333333);
}

.action-btn.active {
  background: var(--primary-color, #007bff);
  color: white;
}

.close-btn:hover {
  background: #ff4757;
  color: white;
}

/* 工具栏 */
.drawer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--toolbar-bg, #fafafa);
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-btn {
  background: none;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-color-secondary, #666666);
  font-size: 12px;
  transition: all 0.2s ease;
}

.toolbar-btn:hover {
  background: var(--hover-bg, #e0e0e0);
}

.search-box {
  position: relative;
}

.search-input {
  width: 150px;
  padding: 4px 24px 4px 8px;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 4px;
  font-size: 12px;
  outline: none;
}

.search-input:focus {
  border-color: var(--primary-color, #007bff);
}

.search-clear {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-color-secondary, #666666);
  padding: 2px;
}

/* 主体内容 */
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.body-content {
  height: 100%;
}

/* 属性列表 */
.properties-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.property-group {
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 6px;
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--group-header-bg, #f8f9fa);
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease;
}

.group-header:hover {
  background: var(--hover-bg, #e9ecef);
}

.group-header.collapsed .group-icon {
  transform: rotate(-90deg);
}

.group-icon {
  transition: transform 0.2s ease;
}

.group-title {
  flex: 1;
  font-weight: 500;
  color: var(--text-color, #333333);
}

.group-count {
  font-size: 12px;
  color: var(--text-color-secondary, #666666);
}

.group-content {
  padding: 12px;
}

.property-item {
  margin-bottom: 12px;
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.property-item:last-child {
  margin-bottom: 0;
}

.property-item.modified {
  background: var(--modified-bg, #fff3cd);
  border-left: 3px solid var(--warning-color, #ffc107);
}

.property-item.readonly {
  opacity: 0.6;
}

.property-label {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color, #333333);
}

.required-mark {
  color: var(--error-color, #dc3545);
}

.modified-mark {
  color: var(--warning-color, #ffc107);
}

.property-value {
  margin-bottom: 4px;
}

.property-value input,
.property-value select,
.property-value textarea {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 4px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s ease;
}

.property-value input:focus,
.property-value select:focus,
.property-value textarea:focus {
  border-color: var(--primary-color, #007bff);
}

.property-description {
  font-size: 11px;
  color: var(--text-color-secondary, #666666);
  line-height: 1.4;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--text-color-secondary, #666666);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
}

/* 底部 */
.drawer-footer {
  padding: 12px 16px;
  background: var(--footer-bg, #f8f9fa);
  border-top: 1px solid var(--border-color, #e0e0e0);
}

.footer-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.footer-btn {
  padding: 6px 16px;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.footer-btn.secondary {
  background: var(--bg-color, #ffffff);
  color: var(--text-color, #333333);
}

.footer-btn.secondary:hover {
  background: var(--hover-bg, #f0f0f0);
}

.footer-btn.primary {
  background: var(--primary-color, #007bff);
  color: white;
  border-color: var(--primary-color, #007bff);
}

.footer-btn.primary:hover {
  background: var(--primary-color-dark, #0056b3);
}

.footer-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 调整大小手柄 */
.resize-handle {
  position: absolute;
  background: transparent;
  z-index: 1001;
}

.properties-drawer.position-right .resize-handle {
  left: -4px;
  top: 0;
  width: 8px;
  height: 100%;
  cursor: ew-resize;
}

.properties-drawer.position-left .resize-handle {
  right: -4px;
  top: 0;
  width: 8px;
  height: 100%;
  cursor: ew-resize;
}

.properties-drawer.position-top .resize-handle {
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 8px;
  cursor: ns-resize;
}

.properties-drawer.position-bottom .resize-handle {
  top: -4px;
  left: 0;
  width: 100%;
  height: 8px;
  cursor: ns-resize;
}

/* 深色主题 */
@media (prefers-color-scheme: dark) {
  .properties-drawer {
    --bg-color: #2d2d2d;
    --header-bg: #3d3d3d;
    --toolbar-bg: #3d3d3d;
    --footer-bg: #3d3d3d;
    --group-header-bg: #404040;
    --border-color: #4d4d4d;
    --text-color: #ffffff;
    --text-color-secondary: #cccccc;
    --hover-bg: #4d4d4d;
    --primary-color: #0084ff;
    --primary-color-dark: #0066cc;
    --error-color: #ff6b6b;
    --warning-color: #feca57;
    --modified-bg: #4a4a2a;
  }
}
</style>
