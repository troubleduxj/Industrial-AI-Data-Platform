<template>
  <div
    class="right-sidebar"
    :class="{
      'right-sidebar--collapsed': collapsed,
      'right-sidebar--dark': isDark,
      'right-sidebar--floating': floating,
    }"
    :style="{ width: collapsed ? '48px' : width + 'px' }"
  >
    <!-- 侧边栏头部 -->
    <div class="right-sidebar__header">
      <div v-if="!collapsed" class="right-sidebar__title">
        <i class="icon-settings"></i>
        <span>属性面板</span>
      </div>
      <button
        class="right-sidebar__toggle"
        :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
        @click="toggleCollapse"
      >
        <i :class="collapsed ? 'icon-chevron-left' : 'icon-chevron-right'"></i>
      </button>
    </div>

    <!-- 标签页导航 -->
    <div v-if="!collapsed" class="right-sidebar__tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-item"
        :class="{ 'tab-item--active': activeTab === tab.id }"
        :title="tab.name"
        @click="setActiveTab(tab.id)"
      >
        <i :class="tab.icon"></i>
        <span>{{ tab.name }}</span>
      </button>
    </div>

    <!-- 内容区域 -->
    <div class="right-sidebar__content">
      <!-- 节点属性面板 -->
      <div v-if="activeTab === 'properties' && !collapsed" class="panel-content">
        <div v-if="!selectedNode" class="empty-state">
          <i class="icon-mouse-pointer"></i>
          <p>选择一个节点查看属性</p>
        </div>

        <div v-else class="node-properties">
          <!-- 基本信息 -->
          <div class="property-section">
            <div class="section-header">
              <h3>基本信息</h3>
              <button class="section-toggle" @click="toggleSection('basic')">
                <i :class="expandedSections.basic ? 'icon-chevron-down' : 'icon-chevron-right'"></i>
              </button>
            </div>
            <div v-show="expandedSections.basic" class="section-content">
              <div class="property-item">
                <label>节点名称</label>
                <input
                  v-model="selectedNode.name"
                  type="text"
                  class="property-input"
                  @input="updateNodeProperty('name', $event.target.value)"
                />
              </div>
              <div class="property-item">
                <label>节点类型</label>
                <div class="property-value">{{ selectedNode.type }}</div>
              </div>
              <div class="property-item">
                <label>描述</label>
                <textarea
                  v-model="selectedNode.description"
                  class="property-textarea"
                  placeholder="输入节点描述..."
                  @input="updateNodeProperty('description', $event.target.value)"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- 位置信息 -->
          <div class="property-section">
            <div class="section-header">
              <h3>位置信息</h3>
              <button class="section-toggle" @click="toggleSection('position')">
                <i
                  :class="expandedSections.position ? 'icon-chevron-down' : 'icon-chevron-right'"
                ></i>
              </button>
            </div>
            <div v-show="expandedSections.position" class="section-content">
              <div class="property-row">
                <div class="property-item">
                  <label>X 坐标</label>
                  <input
                    v-model.number="selectedNode.x"
                    type="number"
                    class="property-input"
                    @input="updateNodeProperty('x', $event.target.value)"
                  />
                </div>
                <div class="property-item">
                  <label>Y 坐标</label>
                  <input
                    v-model.number="selectedNode.y"
                    type="number"
                    class="property-input"
                    @input="updateNodeProperty('y', $event.target.value)"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- 节点配置 -->
          <div class="property-section">
            <div class="section-header">
              <h3>节点配置</h3>
              <button class="section-toggle" @click="toggleSection('config')">
                <i
                  :class="expandedSections.config ? 'icon-chevron-down' : 'icon-chevron-right'"
                ></i>
              </button>
            </div>
            <div v-show="expandedSections.config" class="section-content">
              <component
                :is="getConfigComponent(selectedNode.type)"
                :node="selectedNode"
                @update="updateNodeConfig"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 画布设置面板 -->
      <div v-if="activeTab === 'canvas' && !collapsed" class="panel-content">
        <div class="canvas-settings">
          <!-- 网格设置 -->
          <div class="property-section">
            <div class="section-header">
              <h3>网格设置</h3>
              <button class="section-toggle" @click="toggleSection('grid')">
                <i :class="expandedSections.grid ? 'icon-chevron-down' : 'icon-chevron-right'"></i>
              </button>
            </div>
            <div v-show="expandedSections.grid" class="section-content">
              <div class="property-item">
                <label class="checkbox-label">
                  <input
                    v-model="canvasSettings.showGrid"
                    type="checkbox"
                    @change="updateCanvasSetting('showGrid', $event.target.checked)"
                  />
                  <span>显示网格</span>
                </label>
              </div>
              <div class="property-item">
                <label>网格大小</label>
                <input
                  v-model.number="canvasSettings.gridSize"
                  type="number"
                  class="property-input"
                  min="10"
                  max="100"
                  @input="updateCanvasSetting('gridSize', $event.target.value)"
                />
              </div>
              <div class="property-item">
                <label class="checkbox-label">
                  <input
                    v-model="canvasSettings.snapToGrid"
                    type="checkbox"
                    @change="updateCanvasSetting('snapToGrid', $event.target.checked)"
                  />
                  <span>吸附到网格</span>
                </label>
              </div>
            </div>
          </div>

          <!-- 缩放设置 -->
          <div class="property-section">
            <div class="section-header">
              <h3>缩放设置</h3>
              <button class="section-toggle" @click="toggleSection('zoom')">
                <i :class="expandedSections.zoom ? 'icon-chevron-down' : 'icon-chevron-right'"></i>
              </button>
            </div>
            <div v-show="expandedSections.zoom" class="section-content">
              <div class="property-item">
                <label>当前缩放</label>
                <div class="zoom-control">
                  <span class="zoom-value">{{ Math.round(canvasSettings.zoom * 100) }}%</span>
                  <div class="zoom-buttons">
                    <button class="zoom-btn" @click="zoomIn">+</button>
                    <button class="zoom-btn" @click="zoomOut">-</button>
                    <button class="zoom-btn" @click="resetZoom">重置</button>
                  </div>
                </div>
              </div>
              <div class="property-item">
                <label>最小缩放</label>
                <input
                  v-model.number="canvasSettings.minZoom"
                  type="number"
                  class="property-input"
                  min="0.1"
                  max="1"
                  step="0.1"
                  @input="updateCanvasSetting('minZoom', $event.target.value)"
                />
              </div>
              <div class="property-item">
                <label>最大缩放</label>
                <input
                  v-model.number="canvasSettings.maxZoom"
                  type="number"
                  class="property-input"
                  min="1"
                  max="5"
                  step="0.1"
                  @input="updateCanvasSetting('maxZoom', $event.target.value)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 工作流信息面板 -->
      <div v-if="activeTab === 'info' && !collapsed" class="panel-content">
        <div class="workflow-info">
          <!-- 统计信息 -->
          <div class="property-section">
            <div class="section-header">
              <h3>统计信息</h3>
            </div>
            <div class="section-content">
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">节点数量</div>
                  <div class="info-value">{{ workflowStats.nodeCount }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">连接数量</div>
                  <div class="info-value">{{ workflowStats.connectionCount }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">错误数量</div>
                  <div class="info-value error">{{ workflowStats.errorCount }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">警告数量</div>
                  <div class="info-value warning">{{ workflowStats.warningCount }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 验证结果 -->
          <div class="property-section">
            <div class="section-header">
              <h3>验证结果</h3>
              <button class="section-toggle" @click="toggleSection('validation')">
                <i
                  :class="expandedSections.validation ? 'icon-chevron-down' : 'icon-chevron-right'"
                ></i>
              </button>
            </div>
            <div v-show="expandedSections.validation" class="section-content">
              <div v-if="validationResults.length === 0" class="empty-state">
                <i class="icon-check-circle"></i>
                <p>工作流验证通过</p>
              </div>
              <div v-else class="validation-list">
                <div
                  v-for="result in validationResults"
                  :key="result.id"
                  class="validation-item"
                  :class="`validation-item--${result.type}`"
                >
                  <i :class="getValidationIcon(result.type)"></i>
                  <div class="validation-content">
                    <div class="validation-message">{{ result.message }}</div>
                    <div v-if="result.nodeId" class="validation-node">
                      节点: {{ result.nodeId }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 侧边栏底部 -->
    <div v-if="!collapsed" class="right-sidebar__footer">
      <div class="footer-actions">
        <button class="footer-btn" title="刷新面板" @click="refreshPanel">
          <i class="icon-refresh"></i>
        </button>
        <button class="footer-btn" title="重置面板" @click="resetPanel">
          <i class="icon-rotate-ccw"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useWorkflowStore } from '../../stores/workflowStore'
import { useCanvasStore } from '../../stores/canvasStore'
import { useSelectionStore } from '../../stores/selectionStore'
import MetadataNodeConfig from '../Nodes/NodeTypes/MetadataNodeConfig.vue'

export default {
  name: 'RightSidebar',
  components: {
    MetadataNodeConfig
  },
  props: {
    collapsed: {
      type: Boolean,
      default: false,
    },
    width: {
      type: Number,
      default: 300,
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
  emits: ['toggle-collapse', 'update-node', 'update-canvas'],
  setup(props, { emit }) {
    const workflowStore = useWorkflowStore()
    const canvasStore = useCanvasStore()
    const selectionStore = useSelectionStore()

    // 标签页
    const activeTab = ref('properties')
    const tabs = ref([
      { id: 'properties', name: '属性', icon: 'icon-settings' },
      { id: 'canvas', name: '画布', icon: 'icon-layout' },
      { id: 'info', name: '信息', icon: 'icon-info' },
    ])

    // 展开的区域
    const expandedSections = ref({
      basic: true,
      position: false,
      config: true,
      grid: true,
      zoom: false,
      validation: true,
    })

    // 选中的节点
    const selectedNode = computed(() => selectionStore.selectedNode)

    // 画布设置
    const canvasSettings = computed(() => canvasStore.settings)

    // 工作流统计
    const workflowStats = computed(() => ({
      nodeCount: workflowStore.nodes.length,
      connectionCount: workflowStore.connections.length,
      errorCount: workflowStore.validationErrors.length,
      warningCount: workflowStore.validationWarnings.length,
    }))

    // 验证结果
    const validationResults = computed(() => [
      ...workflowStore.validationErrors.map((error) => ({ ...error, type: 'error' })),
      ...workflowStore.validationWarnings.map((warning) => ({ ...warning, type: 'warning' })),
    ])

    // 切换收起状态
    const toggleCollapse = () => {
      emit('toggle-collapse')
    }

    // 设置活动标签
    const setActiveTab = (tabId) => {
      activeTab.value = tabId
    }

    // 切换区域展开状态
    const toggleSection = (sectionId) => {
      expandedSections.value[sectionId] = !expandedSections.value[sectionId]
    }

    // 更新节点属性
    const updateNodeProperty = (property, value) => {
      if (selectedNode.value) {
        emit('update-node', {
          nodeId: selectedNode.value.id,
          property,
          value,
        })
      }
    }

    // 更新节点配置
    const updateNodeConfig = (config) => {
      if (selectedNode.value) {
        emit('update-node', {
          nodeId: selectedNode.value.id,
          property: 'config',
          value: config,
        })
      }
    }

    // 更新画布设置
    const updateCanvasSetting = (setting, value) => {
      emit('update-canvas', {
        setting,
        value,
      })
    }

    // 缩放控制
    const zoomIn = () => {
      canvasStore.zoomIn()
    }

    const zoomOut = () => {
      canvasStore.zoomOut()
    }

    const resetZoom = () => {
      canvasStore.resetZoom()
    }

    // 获取配置组件
    const getConfigComponent = (nodeType) => {
      // 根据节点类型返回对应的配置组件
      const componentMap = {
        api: 'ApiNodeConfig',
        database: 'DatabaseNodeConfig',
        timer: 'TimerNodeConfig',
        email: 'EmailNodeConfig',
        file: 'FileNodeConfig',
        condition: 'ConditionNodeConfig',
        loop: 'LoopNodeConfig',
        metadata_analysis: 'MetadataNodeConfig',
      }
      return componentMap[nodeType] || 'DefaultNodeConfig'
    }

    // 获取验证图标
    const getValidationIcon = (type) => {
      const iconMap = {
        error: 'icon-alert-circle',
        warning: 'icon-alert-triangle',
        info: 'icon-info',
      }
      return iconMap[type] || 'icon-help-circle'
    }

    // 刷新面板
    const refreshPanel = () => {
      // 刷新当前面板数据
      workflowStore.validateWorkflow()
    }

    // 重置面板
    const resetPanel = () => {
      // 重置面板状态
      expandedSections.value = {
        basic: true,
        position: false,
        config: true,
        grid: true,
        zoom: false,
        validation: true,
      }
      activeTab.value = 'properties'
    }

    return {
      // 数据
      activeTab,
      tabs,
      expandedSections,

      // 计算属性
      selectedNode,
      canvasSettings,
      workflowStats,
      validationResults,

      // 方法
      toggleCollapse,
      setActiveTab,
      toggleSection,
      updateNodeProperty,
      updateNodeConfig,
      updateCanvasSetting,
      zoomIn,
      zoomOut,
      resetZoom,
      getConfigComponent,
      getValidationIcon,
      refreshPanel,
      resetPanel,
    }
  },
}
</script>

<style lang="scss" scoped>
.right-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color, #ffffff);
  border-left: 1px solid var(--border-color, #e5e7eb);
  transition: width 0.3s ease;
  position: relative;

  &--collapsed {
    .right-sidebar__tabs,
    .right-sidebar__footer {
      display: none;
    }
  }

  &--dark {
    background: var(--bg-color-dark, #1f2937);
    border-left-color: var(--border-color-dark, #374151);
    color: var(--text-color-dark, #f9fafb);
  }

  &--floating {
    position: absolute;
    top: 0;
    right: 0;
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

  &__tabs {
    display: flex;
    border-bottom: 1px solid var(--border-color, #e5e7eb);
  }

  &__content {
    flex: 1;
    overflow-y: auto;
  }

  &__footer {
    padding: 12px;
    border-top: 1px solid var(--border-color, #e5e7eb);
    background: var(--bg-color-secondary, #f9fafb);
  }
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-color-secondary, #6b7280);
  transition: all 0.2s ease;
  border-bottom: 2px solid transparent;

  &:hover {
    background: var(--bg-color-hover, #f3f4f6);
    color: var(--text-color, #374151);
  }

  &--active {
    color: var(--primary-color, #3b82f6);
    border-bottom-color: var(--primary-color, #3b82f6);
    background: var(--primary-bg, #eff6ff);
  }

  i {
    font-size: 16px;
  }
}

.panel-content {
  padding: 16px;
}

.property-section {
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;

  h3 {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-color, #374151);
    margin: 0;
  }
}

.section-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
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

  i {
    font-size: 12px;
  }
}

.section-content {
  padding-left: 4px;
}

.property-item {
  margin-bottom: 12px;

  &:last-child {
    margin-bottom: 0;
  }

  label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-color-secondary, #6b7280);
    margin-bottom: 4px;

    &.checkbox-label {
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;

      input[type='checkbox'] {
        margin: 0;
      }
    }
  }
}

.property-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--border-color, #d1d5db);
  border-radius: 4px;
  font-size: 14px;
  color: var(--text-color, #374151);
  background: var(--bg-color, #ffffff);
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: var(--primary-color, #3b82f6);
  }
}

.property-textarea {
  width: 100%;
  min-height: 60px;
  padding: 6px 8px;
  border: 1px solid var(--border-color, #d1d5db);
  border-radius: 4px;
  font-size: 14px;
  color: var(--text-color, #374151);
  background: var(--bg-color, #ffffff);
  resize: vertical;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: var(--primary-color, #3b82f6);
  }
}

.property-value {
  padding: 6px 8px;
  background: var(--bg-color-secondary, #f3f4f6);
  border-radius: 4px;
  font-size: 14px;
  color: var(--text-color-secondary, #6b7280);
}

.property-row {
  display: flex;
  gap: 8px;

  .property-item {
    flex: 1;
  }
}

.zoom-control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.zoom-value {
  font-weight: 500;
  color: var(--text-color, #374151);
}

.zoom-buttons {
  display: flex;
  gap: 4px;
}

.zoom-btn {
  padding: 4px 8px;
  border: 1px solid var(--border-color, #d1d5db);
  background: var(--bg-color, #ffffff);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-color, #374151);
  transition: all 0.2s ease;

  &:hover {
    background: var(--bg-color-hover, #f9fafb);
    border-color: var(--border-color-hover, #9ca3af);
  }
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.info-item {
  text-align: center;
  padding: 12px;
  background: var(--bg-color-secondary, #f9fafb);
  border-radius: 6px;
}

.info-label {
  font-size: 12px;
  color: var(--text-color-secondary, #6b7280);
  margin-bottom: 4px;
}

.info-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color, #374151);

  &.error {
    color: var(--error-text, #dc2626);
  }

  &.warning {
    color: var(--warning-text, #d97706);
  }
}

.validation-list {
  max-height: 200px;
  overflow-y: auto;
}

.validation-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  margin-bottom: 8px;
  border-radius: 6px;

  &--error {
    background: var(--error-bg, #fee2e2);
    color: var(--error-text, #991b1b);
  }

  &--warning {
    background: var(--warning-bg, #fef3c7);
    color: var(--warning-text, #92400e);
  }

  &--info {
    background: var(--info-bg, #dbeafe);
    color: var(--info-text, #1e40af);
  }

  i {
    font-size: 16px;
    margin-top: 2px;
  }
}

.validation-content {
  flex: 1;
}

.validation-message {
  font-size: 14px;
  margin-bottom: 2px;
}

.validation-node {
  font-size: 12px;
  opacity: 0.8;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--text-color-secondary, #6b7280);

  i {
    font-size: 48px;
    margin-bottom: 12px;
    opacity: 0.5;
  }

  p {
    margin: 0;
    font-size: 14px;
  }
}

.footer-actions {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.footer-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border-color, #d1d5db);
  background: var(--bg-color, #ffffff);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-color-secondary, #6b7280);
  transition: all 0.2s ease;

  &:hover {
    background: var(--bg-color-hover, #f9fafb);
    border-color: var(--border-color-hover, #9ca3af);
    color: var(--text-color, #374151);
  }

  i {
    font-size: 14px;
  }
}

// 暗色主题
.right-sidebar--dark {
  .right-sidebar__header {
    border-bottom-color: var(--border-color-dark, #374151);
  }

  .right-sidebar__title {
    color: var(--text-color-dark, #f9fafb);
  }

  .right-sidebar__toggle {
    color: var(--text-color-secondary-dark, #9ca3af);

    &:hover {
      background: var(--bg-color-hover-dark, #374151);
      color: var(--text-color-dark, #f9fafb);
    }
  }

  .right-sidebar__tabs {
    border-bottom-color: var(--border-color-dark, #374151);
  }

  .right-sidebar__footer {
    border-top-color: var(--border-color-dark, #374151);
    background: var(--bg-color-secondary-dark, #111827);
  }

  .tab-item {
    color: var(--text-color-secondary-dark, #9ca3af);

    &:hover {
      background: var(--bg-color-hover-dark, #374151);
      color: var(--text-color-dark, #f9fafb);
    }

    &--active {
      background: var(--primary-bg-dark, #1e3a8a);
    }
  }

  .section-header h3 {
    color: var(--text-color-dark, #f9fafb);
  }

  .section-toggle {
    color: var(--text-color-secondary-dark, #9ca3af);

    &:hover {
      background: var(--bg-color-hover-dark, #374151);
      color: var(--text-color-dark, #f9fafb);
    }
  }

  .property-item label {
    color: var(--text-color-secondary-dark, #9ca3af);
  }

  .property-input,
  .property-textarea {
    background: var(--bg-color-dark, #374151);
    border-color: var(--border-color-dark, #4b5563);
    color: var(--text-color-dark, #f9fafb);

    &:focus {
      border-color: var(--primary-color, #3b82f6);
    }
  }

  .property-value {
    background: var(--bg-color-secondary-dark, #111827);
    color: var(--text-color-secondary-dark, #9ca3af);
  }

  .zoom-value {
    color: var(--text-color-dark, #f9fafb);
  }

  .zoom-btn {
    background: var(--bg-color-dark, #374151);
    border-color: var(--border-color-dark, #4b5563);
    color: var(--text-color-dark, #f9fafb);

    &:hover {
      background: var(--bg-color-hover-dark, #4b5563);
      border-color: var(--border-color-hover-dark, #6b7280);
    }
  }

  .info-item {
    background: var(--bg-color-secondary-dark, #111827);
  }

  .info-label {
    color: var(--text-color-secondary-dark, #9ca3af);
  }

  .info-value {
    color: var(--text-color-dark, #f9fafb);
  }

  .footer-btn {
    background: var(--bg-color-dark, #374151);
    border-color: var(--border-color-dark, #4b5563);
    color: var(--text-color-secondary-dark, #9ca3af);

    &:hover {
      background: var(--bg-color-hover-dark, #4b5563);
      border-color: var(--border-color-hover-dark, #6b7280);
      color: var(--text-color-dark, #f9fafb);
    }
  }
}
</style>
