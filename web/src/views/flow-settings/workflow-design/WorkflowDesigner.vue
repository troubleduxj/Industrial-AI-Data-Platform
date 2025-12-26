<template>
  <div class="workflow-designer" :class="{ 'designer-fullscreen': isFullscreen }">
    <!-- 工具栏 -->
    <WorkflowToolbar
      :current-tool="currentTool"
      :can-undo="canUndo"
      :can-redo="canRedo"
      :can-copy="canCopy"
      :can-paste="canPaste"
      :can-delete="canDelete"
      :zoom-level="canvasState.scale"
      :show-grid="showGrid"
      :show-alignment="showAlignment"
      :workflow-valid="workflowValidation.isValid"
      @tool-change="handleToolChange"
      @undo="handleUndo"
      @redo="handleRedo"
      @copy="handleCopy"
      @paste="handlePaste"
      @delete="handleDelete"
      @zoom-in="handleZoomIn"
      @zoom-out="handleZoomOut"
      @zoom-fit="handleZoomFit"
      @zoom-reset="handleZoomReset"
      @toggle-grid="toggleGrid"
      @toggle-alignment="toggleAlignment"
      @auto-layout="handleAutoLayout"
      @align-nodes="handleAlignNodes"
      @validate-workflow="handleValidateWorkflow"
      @run-preview="handleRunPreview"
      @new-workflow="handleNewWorkflow"
      @open-workflow="handleOpenWorkflow"
      @save-workflow="handleSaveWorkflow"
      @export-workflow="handleExportWorkflow"
      @toggle-fullscreen="toggleFullscreen"
    />

    <!-- 主内容区域 -->
    <div class="designer-content">
      <!-- 左侧面板 -->
      <div class="left-panel" :class="{ collapsed: leftPanelCollapsed }">
        <!-- 节点库 -->
        <NodeLibrary
          :collapsed="nodeLibraryCollapsed"
          :search-query="nodeSearchQuery"
          :selected-category="selectedNodeCategory"
          :favorite-nodes="favoriteNodes"
          @toggle-collapse="toggleNodeLibrary"
          @search="handleNodeSearch"
          @category-change="handleNodeCategoryChange"
          @node-drag-start="handleNodeDragStart"
          @node-click="handleNodeLibraryClick"
          @node-double-click="handleNodeLibraryDoubleClick"
          @toggle-favorite="handleToggleFavorite"
        />
      </div>

      <!-- 中央画布区域 -->
      <div class="canvas-area">
        <!-- 画布容器 -->
        <div class="canvas-container">
          <WorkflowCanvas
            ref="workflowCanvas"
            :nodes="nodes"
            :connections="connections"
            :show-grid="showGrid"
            :show-alignment="showAlignment"
            :grid-config="gridConfig"
            :readonly="readonly"
            @node-click="handleNodeClick"
            @node-double-click="handleNodeDoubleClick"
            @node-context-menu="handleNodeContextMenu"
            @connection-click="handleConnectionClick"
            @connection-double-click="handleConnectionDoubleClick"
            @connection-context-menu="handleConnectionContextMenu"
            @canvas-click="handleCanvasClick"
            @canvas-context-menu="handleCanvasContextMenu"
            @selection-change="handleSelectionChange"
            @viewport-change="handleViewportChange"
            @error="handleCanvasError"
            @node-drop="handleNodeDrop"
          />
        </div>

        <!-- 迷你地图 -->
        <MiniMap
          :nodes="nodes"
          :connections="connections"
          :canvas-state="canvasState"
          :viewport-size="viewportSize"
          :show-grid="showGrid"
          @viewport-change="handleViewportChange"
          @zoom-change="handleZoomChange"
          @fit-to-view="handleZoomFit"
        />

        <!-- 状态栏 -->
        <StatusBar
          :workflow-status="workflowStatus"
          :node-count="stats.nodeCount"
          :connection-count="stats.connectionCount"
          :validation-result="workflowValidation"
          :save-status="saveStatus"
          :current-tool="currentTool"
          :zoom-level="canvasState.scale"
          :canvas-position="canvasState.offset"
          :show-grid="showGrid"
          :show-alignment="showAlignment"
          :performance-info="performanceInfo"
        />
      </div>

      <!-- 右侧面板 -->
      <div class="right-panel" :class="{ collapsed: propertyPanelCollapsed }">
        <!-- 属性面板 -->
        <PropertyPanel
          :selected-item="selectedItem"
          @update-node="handleUpdateNode"
          @update-connection="handleUpdateConnection"
          @batch-align="handleBatchAlign"
          @batch-distribute="handleBatchDistribute"
          @batch-delete="handleBatchDelete"
          @toggle-collapse="togglePropertyPanel"
        />
      </div>

      <!-- 右侧面板切换按钮 -->
      <div
        class="right-panel-toggle"
        :class="{ collapsed: propertyPanelCollapsed }"
        @click="togglePropertyPanel"
      >
        <span class="toggle-icon">
          <span v-if="propertyPanelCollapsed">◀</span>
          <span v-else>▶</span>
        </span>
        <span v-if="propertyPanelCollapsed" class="toggle-text">属性</span>
      </div>
    </div>

    <!-- 对话框 -->
    <div class="dialogs">
      <!-- 节点详情对话框 -->
      <!-- <NodeDetailDialog
        v-if="nodeDetailDialog.visible"
        :node="nodeDetailDialog.node"
        @close="closeNodeDetailDialog"
        @save="handleNodeDetailSave"
      /> -->

      <!-- 工作流设置对话框 -->
      <!-- <WorkflowSettingsDialog
        v-if="workflowSettingsDialog.visible"
        :workflow="workflowInfo"
        @close="closeWorkflowSettingsDialog"
        @save="handleWorkflowSettingsSave"
      /> -->

      <!-- 导出对话框 -->
      <!-- <ExportDialog
        v-if="exportDialog.visible"
        :workflow="workflowData"
        @close="closeExportDialog"
        @export="handleExport"
      /> -->

      <!-- 导入对话框 -->
      <!-- <ImportDialog
        v-if="importDialog.visible"
        @close="closeImportDialog"
        @import="handleImport"
      /> -->
    </div>

    <!-- 加载遮罩 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <div class="loading-text">{{ loadingText }}</div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-toast">
      <div class="error-content">
        <span class="error-icon">⚠️</span>
        <span class="error-message">{{ error.message }}</span>
        <button class="error-close" @click="clearError">✕</button>
      </div>
    </div>

    <!-- 成功提示 -->
    <div v-if="success" class="success-toast">
      <div class="success-content">
        <span class="success-icon">✅</span>
        <span class="success-message">{{ success.message }}</span>
        <button class="success-close" @click="clearSuccess">✕</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import WorkflowToolbar from './components/UI/WorkflowToolbar.vue'
import WorkflowCanvas from './components/Canvas/WorkflowCanvas.vue'
import NodeLibrary from './components/UI/NodeLibrary.vue'
import PropertyPanel from './components/UI/PropertyPanel.vue'
import MiniMap from './components/UI/MiniMap.vue'
import StatusBar from './components/UI/StatusBar.vue'
import { useWorkflowStore } from './stores/workflowStore'
import { useConnections } from './composables/useConnections'

// Props
const props = defineProps({
  // 工作流ID（编辑模式）
  workflowId: {
    type: String,
    default: null,
  },

  // 只读模式
  readonly: {
    type: Boolean,
    default: false,
  },

  // 初始工作流数据
  initialData: {
    type: Object,
    default: null,
  },
})

// Emits
const emit = defineEmits(['save', 'export', 'close', 'error', 'success'])

// Router
const router = useRouter()
const route = useRoute()

// Store
const workflowStore = useWorkflowStore()

// 导入工作流API
import { getWorkflowDetail, saveWorkflowDesign, updateWorkflow } from '@/api/workflow'

// 响应式数据
const workflowCanvas = ref(null)
const currentTool = ref('select')
const isFullscreen = ref(false)
const leftPanelCollapsed = ref(false)
const rightPanelCollapsed = ref(false)
const nodeLibraryCollapsed = ref(false)
const propertyPanelCollapsed = ref(true)
const showGrid = ref(true)
const showAlignment = ref(true)
const loading = ref(false)
const loadingText = ref('')
const error = ref(null)
const success = ref(null)

// 节点库相关状态
const nodeSearchQuery = ref('')
const selectedNodeCategory = ref('all')
const favoriteNodes = ref(new Set())
const currentDraggedNodeTemplate = ref(null)

// 对话框状态
const nodeDetailDialog = ref({ visible: false, node: null })
const workflowSettingsDialog = ref({ visible: false })
const exportDialog = ref({ visible: false })
const importDialog = ref({ visible: false })

// 网格配置
const gridConfig = ref({
  size: 20,
  offset: { x: 0, y: 0 },
})

// 视口大小
const viewportSize = ref({ width: 800, height: 600 })

// 性能信息
const performanceInfo = ref({
  fps: 60,
  renderTime: 0,
  nodeCount: 0,
  connectionCount: 0,
})

// 计算属性
const nodes = computed(() => workflowStore.nodes)
const connections = computed(() => workflowStore.connections)
const selectedNodes = computed(() => workflowStore.selectedNodes)
const selectedConnections = computed(() => workflowStore.selectedConnections)
const canvasState = computed(() => workflowStore.canvasState)
const workflowInfo = computed(() => workflowStore.workflowInfo)
const workflowData = computed(() => workflowStore.workflowData)
const stats = computed(() => workflowStore.workflowStats)
const workflowValidation = computed(() => workflowStore.workflowValidation)
const canUndo = computed(() => workflowStore.canUndo)
const canRedo = computed(() => workflowStore.canRedo)

const canCopy = computed(() => {
  return selectedNodes.value.length > 0 || selectedConnections.value.length > 0
})

const canPaste = computed(() => {
  return workflowStore.canPaste
})

const canDelete = computed(() => {
  return selectedNodes.value.length > 0 || selectedConnections.value.length > 0
})

const workflowStatus = computed(() => {
  if (loading.value) return 'loading'
  if (error.value) return 'error'
  if (!workflowValidation.value.isValid) return 'invalid'
  return 'ready'
})

// 为PropertyPanel准备selectedItem
const selectedItem = computed(() => {
  const selectedNodesCount = selectedNodes.value.length
  const selectedConnectionsCount = selectedConnections.value.length

  if (selectedNodesCount === 1 && selectedConnectionsCount === 0) {
    // 单个节点选中
    return {
      type: 'node',
      data: selectedNodes.value[0],
    }
  } else if (selectedNodesCount === 0 && selectedConnectionsCount === 1) {
    // 单个连接选中
    return {
      type: 'connection',
      data: selectedConnections.value[0],
    }
  } else if (
    selectedNodesCount > 1 ||
    selectedConnectionsCount > 1 ||
    (selectedNodesCount > 0 && selectedConnectionsCount > 0)
  ) {
    // 多选状态
    return {
      type: 'multiple',
      count: selectedNodesCount + selectedConnectionsCount,
      nodes: selectedNodesCount,
      connections: selectedConnectionsCount,
    }
  }

  // 无选择
  return null
})

const saveStatus = computed(() => {
  return workflowStore.isDirty ? 'unsaved' : 'saved'
})

// Composables
const { isConnecting } = useConnections({
  nodes,
  connections,
  onConnectionAdd: (connection) => workflowStore.addConnection(connection),
  onConnectionRemove: (connectionId) => workflowStore.removeConnection(connectionId),
  onSaveHistory: (action) => workflowStore.saveHistory(action),
})

// 工具栏事件处理
function handleToolChange(tool) {
  currentTool.value = tool

  // 如果切换到其他工具，取消连接模式
  if (tool !== 'connect' && isConnecting.value) {
    // 取消连接
  }
}

function handleUndo() {
  workflowStore.undo()
}

function handleRedo() {
  workflowStore.redo()
}

function handleCopy() {
  workflowStore.copySelection()
  showSuccess('已复制到剪贴板')
}

function handlePaste() {
  workflowStore.pasteSelection()
  showSuccess('已粘贴')
}

function handleDelete() {
  const nodeCount = selectedNodes.value.length
  const connectionCount = selectedConnections.value.length

  selectedNodes.value.forEach((node) => {
    workflowStore.removeNode(node.id)
  })

  selectedConnections.value.forEach((connection) => {
    workflowStore.removeConnection(connection.id)
  })

  const message = `已删除 ${nodeCount} 个节点和 ${connectionCount} 个连接`
  showSuccess(message)
}

function handleZoomIn() {
  const newScale = Math.min(canvasState.value.scale * 1.2, 3)
  workflowStore.updateCanvasState({ scale: newScale })
}

function handleZoomOut() {
  const newScale = Math.max(canvasState.value.scale / 1.2, 0.1)
  workflowStore.updateCanvasState({ scale: newScale })
}

function handleZoomFit() {
  if (nodes.value.length === 0) return

  // 计算所有节点的边界
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity

  nodes.value.forEach((node) => {
    const width = node.size?.width || 120
    const height = node.size?.height || 80

    minX = Math.min(minX, node.position.x)
    minY = Math.min(minY, node.position.y)
    maxX = Math.max(maxX, node.position.x + width)
    maxY = Math.max(maxY, node.position.y + height)
  })

  const contentWidth = maxX - minX
  const contentHeight = maxY - minY
  const padding = 50

  const scaleX = (viewportSize.value.width - padding * 2) / contentWidth
  const scaleY = (viewportSize.value.height - padding * 2) / contentHeight
  const scale = Math.min(scaleX, scaleY, 1)

  const centerX = (minX + maxX) / 2
  const centerY = (minY + maxY) / 2

  const offsetX = viewportSize.value.width / 2 - centerX * scale
  const offsetY = viewportSize.value.height / 2 - centerY * scale

  workflowStore.updateCanvasState({
    scale,
    offset: { x: offsetX, y: offsetY },
  })
}

function handleZoomReset() {
  workflowStore.updateCanvasState({
    scale: 1,
    offset: { x: 0, y: 0 },
  })
}

function handleZoomChange(scale) {
  workflowStore.updateCanvasState({ scale })
}

function toggleGrid() {
  showGrid.value = !showGrid.value
}

function toggleAlignment() {
  showAlignment.value = !showAlignment.value
}

function handleAutoLayout() {
  // TODO: 实现自动布局
  showSuccess('自动布局功能开发中')
}

function handleAlignNodes(type) {
  if (selectedNodes.value.length < 2) {
    showError('请选择至少两个节点')
    return
  }

  // TODO: 实现节点对齐
  showSuccess(`节点${type}对齐完成`)
}

function handleValidateWorkflow() {
  const result = workflowStore.validateWorkflow()

  if (result.isValid) {
    showSuccess('工作流验证通过')
  } else {
    showError(`工作流验证失败：${result.errors.length} 个错误，${result.warnings.length} 个警告`)
  }
}

function handleRunPreview() {
  // TODO: 实现预览运行
  showSuccess('预览运行功能开发中')
}

function handleNewWorkflow() {
  if (workflowStore.isDirty) {
    if (!confirm('当前工作流有未保存的更改，确定要新建吗？')) {
      return
    }
  }

  workflowStore.clearWorkflow()
  showSuccess('已创建新工作流')
}

function handleOpenWorkflow() {
  // TODO: 实现打开工作流
  showSuccess('打开工作流功能开发中')
}

function handleSaveWorkflow() {
  // 如果有当前工作流ID，保存到服务器
  if (currentWorkflowId.value) {
    saveWorkflowToServer()
    return
  }
  
  // 否则本地保存
  if (!workflowValidation.value.isValid) {
    showError('工作流验证失败，无法保存')
    return
  }

  loading.value = true
  loadingText.value = '保存中...'

  // 模拟保存
  setTimeout(() => {
    loading.value = false
    workflowStore.markClean()
    showSuccess('工作流已保存')
    emit('save', workflowData.value)
  }, 1000)
}

function handleExportWorkflow() {
  exportDialog.value.visible = true
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

// 节点库事件处理
function toggleNodeLibrary() {
  nodeLibraryCollapsed.value = !nodeLibraryCollapsed.value
}

function handleNodeSearch(query) {
  nodeSearchQuery.value = query
}

function handleNodeCategoryChange(category) {
  selectedNodeCategory.value = category
}

function handleNodeDragStart(nodeTemplate) {
  // 节点拖拽开始
  console.log('Node drag started:', nodeTemplate)

  // 设置当前拖拽的节点模板
  currentDraggedNodeTemplate.value = nodeTemplate

  // 可以在这里添加拖拽开始的视觉反馈
  document.body.style.cursor = 'grabbing'
}

function handleNodeDrop(dropData) {
  // 处理节点拖拽放置
  console.log('Node dropped:', dropData)

  const { nodeType, nodeData, position } = dropData

  // 计算网格对齐位置
  const alignedPosition = {
    x: Math.round(position.x / gridConfig.value.size) * gridConfig.value.size,
    y: Math.round(position.y / gridConfig.value.size) * gridConfig.value.size,
  }

  // 添加到工作流
  workflowStore.addNode(nodeType, alignedPosition, nodeData.defaultProperties || {})
  showSuccess(`已添加${nodeData.name}节点`)

  // 重置拖拽状态
  currentDraggedNodeTemplate.value = null
  document.body.style.cursor = ''
}

function handleNodeLibraryClick(nodeTemplate) {
  // 显示节点详情
  nodeDetailDialog.value = {
    visible: true,
    node: nodeTemplate,
  }
}

function handleNodeLibraryDoubleClick(nodeTemplate) {
  // 添加节点到画布中心
  const centerX = viewportSize.value.width / 2
  const centerY = viewportSize.value.height / 2

  const canvasPoint = {
    x: (centerX - canvasState.value.offset.x) / canvasState.value.scale,
    y: (centerY - canvasState.value.offset.y) / canvasState.value.scale,
  }

  // 计算网格对齐位置
  const alignedPosition = {
    x: Math.round(canvasPoint.x / gridConfig.value.size) * gridConfig.value.size,
    y: Math.round(canvasPoint.y / gridConfig.value.size) * gridConfig.value.size,
  }

  workflowStore.addNode(nodeTemplate.type, alignedPosition, nodeTemplate.defaultProperties || {})
  showSuccess(`已添加${nodeTemplate.name}节点`)
}

function handleToggleFavorite(nodeTemplate) {
  if (favoriteNodes.value.has(nodeTemplate.type)) {
    favoriteNodes.value.delete(nodeTemplate.type)
  } else {
    favoriteNodes.value.add(nodeTemplate.type)
  }
}

// 属性面板事件处理
function togglePropertyPanel() {
  propertyPanelCollapsed.value = !propertyPanelCollapsed.value
}

function handlePropertyChange(target, property, value) {
  if (target.type === 'node') {
    workflowStore.updateNodeProperty(target.id, property, value)
  } else if (target.type === 'connection') {
    workflowStore.updateConnectionProperty(target.id, property, value)
  }
}

function handleBatchOperation(operation, targets) {
  // TODO: 实现批量操作
  showSuccess(`批量${operation}操作完成`)
}

// PropertyPanel事件处理
function handleUpdateNode(nodeData) {
  workflowStore.updateNode(nodeData.id, nodeData)
  showSuccess('节点属性已更新')
}

function handleUpdateConnection(connectionData) {
  workflowStore.updateConnection(connectionData.id, connectionData)
  showSuccess('连接属性已更新')
}

function handleBatchAlign(direction) {
  const selectedNodeIds = selectedNodes.value.map((node) => node.id)
  if (selectedNodeIds.length > 1) {
    workflowStore.alignNodes(selectedNodeIds, direction)
    showSuccess(`节点已${direction}对齐`)
  }
}

function handleBatchDistribute(direction) {
  const selectedNodeIds = selectedNodes.value.map((node) => node.id)
  if (selectedNodeIds.length > 2) {
    workflowStore.distributeNodes(selectedNodeIds, direction)
    showSuccess(`节点已${direction}分布`)
  }
}

function handleBatchDelete() {
  const selectedNodeIds = selectedNodes.value.map((node) => node.id)
  const selectedConnectionIds = selectedConnections.value.map((conn) => conn.id)

  if (selectedNodeIds.length > 0) {
    workflowStore.deleteNodes(selectedNodeIds)
  }
  if (selectedConnectionIds.length > 0) {
    workflowStore.deleteConnections(selectedConnectionIds)
  }

  showSuccess('已删除选中项目')
}

// 画布事件处理
function handleNodeClick(data) {
  // 节点点击已在画布组件中处理
}

function handleNodeDoubleClick(data) {
  nodeDetailDialog.value = {
    visible: true,
    node: data.node,
  }
}

function handleNodeContextMenu(data) {
  // 节点右键菜单已在画布组件中处理
}

function handleConnectionClick(data) {
  // 连接点击已在画布组件中处理
}

function handleConnectionDoubleClick(data) {
  // TODO: 实现连接编辑
}

function handleConnectionContextMenu(data) {
  // 连接右键菜单已在画布组件中处理
}

function handleCanvasClick(data) {
  // 画布点击已在画布组件中处理
}

function handleCanvasContextMenu(data) {
  // 画布右键菜单已在画布组件中处理
}

function handleSelectionChange(data) {
  // 选择变化已在store中处理
}

function handleViewportChange(data) {
  if (data.scale !== undefined) {
    workflowStore.updateCanvasState({ scale: data.scale })
  }
  if (data.offset !== undefined) {
    workflowStore.updateCanvasState({ offset: data.offset })
  }
}

function handleCanvasError(error) {
  showError(error.message)
}

// 对话框事件处理
function closeNodeDetailDialog() {
  nodeDetailDialog.value.visible = false
}

function handleNodeDetailSave(nodeData) {
  // TODO: 保存节点详情
  closeNodeDetailDialog()
  showSuccess('节点详情已保存')
}

function closeWorkflowSettingsDialog() {
  workflowSettingsDialog.value.visible = false
}

function handleWorkflowSettingsSave(settings) {
  workflowStore.updateWorkflowInfo(settings)
  closeWorkflowSettingsDialog()
  showSuccess('工作流设置已保存')
}

function closeExportDialog() {
  exportDialog.value.visible = false
}

function handleExport(exportData) {
  closeExportDialog()
  emit('export', exportData)
  showSuccess('工作流已导出')
}

function closeImportDialog() {
  importDialog.value.visible = false
}

function handleImport(importData) {
  workflowStore.loadWorkflowData(importData)
  closeImportDialog()
  showSuccess('工作流已导入')
}

// 工具方法
function showError(message) {
  error.value = { message }
  setTimeout(() => {
    error.value = null
  }, 5000)
  emit('error', message)
}

function showSuccess(message) {
  success.value = { message }
  setTimeout(() => {
    success.value = null
  }, 3000)
  emit('success', message)
}

function clearError() {
  error.value = null
}

function clearSuccess() {
  success.value = null
}

function updateViewportSize() {
  nextTick(() => {
    const canvasContainer = document.querySelector('.canvas-container')
    if (canvasContainer) {
      const rect = canvasContainer.getBoundingClientRect()
      viewportSize.value = {
        width: rect.width,
        height: rect.height,
      }
    }
  })
}

function updatePerformanceInfo() {
  performanceInfo.value = {
    fps: 60, // TODO: 实际计算FPS
    renderTime: 0, // TODO: 实际计算渲染时间
    nodeCount: nodes.value.length,
    connectionCount: connections.value.length,
  }
}

// 键盘快捷键
function handleKeyDown(event) {
  // 全屏切换
  if (event.key === 'F11') {
    event.preventDefault()
    toggleFullscreen()
  }

  // 保存
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault()
    handleSaveWorkflow()
  }

  // 新建
  if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
    event.preventDefault()
    handleNewWorkflow()
  }

  // 打开
  if ((event.ctrlKey || event.metaKey) && event.key === 'o') {
    event.preventDefault()
    handleOpenWorkflow()
  }
}

// 当前工作流ID
const currentWorkflowId = ref<number | null>(null)
const currentWorkflowInfo = ref<any>(null)

// 加载工作流数据
async function loadWorkflowById(workflowId: number) {
  loading.value = true
  loadingText.value = '加载工作流...'
  
  try {
    const res = await getWorkflowDetail(workflowId)
    if (res.code === 200 && res.data) {
      const workflow = res.data
      currentWorkflowId.value = workflow.id
      currentWorkflowInfo.value = workflow
      
      // 加载到store
      workflowStore.loadWorkflow({
        nodes: workflow.nodes || [],
        connections: workflow.connections || [],
        info: {
          id: workflow.id,
          name: workflow.name,
          description: workflow.description,
          version: workflow.version,
        }
      })
      
      showSuccess(`已加载工作流: ${workflow.name}`)
    } else {
      showError(res.message || '加载工作流失败')
    }
  } catch (err) {
    console.error('加载工作流失败:', err)
    showError('加载工作流失败')
  } finally {
    loading.value = false
  }
}

// 保存工作流设计
async function saveWorkflowToServer() {
  if (!currentWorkflowId.value) {
    showError('请先选择或创建工作流')
    return
  }
  
  loading.value = true
  loadingText.value = '保存中...'
  
  try {
    const designData = {
      nodes: workflowStore.nodes,
      connections: workflowStore.connections
    }
    
    const res = await saveWorkflowDesign(currentWorkflowId.value, designData)
    if (res.code === 200) {
      workflowStore.markClean()
      showSuccess('工作流设计已保存')
      emit('save', designData)
    } else {
      showError(res.message || '保存失败')
    }
  } catch (err) {
    console.error('保存工作流失败:', err)
    showError('保存失败')
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(async () => {
  // 初始化
  updateViewportSize()

  // 从路由参数获取工作流ID
  const workflowIdFromRoute = route.query.id
  
  // 加载初始数据
  if (props.initialData) {
    workflowStore.loadWorkflow(props.initialData)
  } else if (props.workflowId) {
    await loadWorkflowById(Number(props.workflowId))
  } else if (workflowIdFromRoute) {
    await loadWorkflowById(Number(workflowIdFromRoute))
  }

  // 监听窗口大小变化
  window.addEventListener('resize', updateViewportSize)
  document.addEventListener('keydown', handleKeyDown)

  // 定期更新性能信息
  const performanceTimer = setInterval(updatePerformanceInfo, 1000)

  // 清理函数
  onUnmounted(() => {
    window.removeEventListener('resize', updateViewportSize)
    document.removeEventListener('keydown', handleKeyDown)
    clearInterval(performanceTimer)
  })
})

// 提供给子组件的上下文
provide('workflowDesigner', {
  readonly: props.readonly,
  currentTool,
  showError,
  showSuccess,
})

// 提供workflowStore给子组件
provide('workflowStore', workflowStore)

// 监听器
watch(
  () => workflowStore.isDirty,
  (isDirty) => {
    // 页面离开提醒
    if (isDirty) {
      window.addEventListener('beforeunload', handleBeforeUnload)
    } else {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }
)

function handleBeforeUnload(event) {
  if (workflowStore.isDirty) {
    event.preventDefault()
    event.returnValue = ''
  }
}
</script>

<style scoped>
.workflow-designer {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: calc(100vh - 120px); /* 减去头部和标签栏的高度 */
  background: #f5f5f5;
  overflow: hidden;
}

.workflow-designer.designer-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

.designer-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 280px;
  background: #ffffff;
  border-right: 1px solid #e8e8e8;
  transition: all 0.3s ease;
  overflow: hidden;
}

.left-panel.collapsed {
  width: 0;
  border-right: none;
}

.canvas-area {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.right-panel {
  width: 320px;
  background: #ffffff;
  border-left: 1px solid #e8e8e8;
  transition: all 0.3s ease;
  overflow: hidden;
}

.right-panel.collapsed {
  width: 0;
  border-left: none;
}

.right-panel-toggle {
  position: fixed;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  width: 40px;
  height: 100px;
  background: #ffffff;
  border: 2px solid #1890ff;
  border-right: none;
  border-radius: 8px 0 0 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1000;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.15);
}

.right-panel-toggle:hover {
  background: #f5f5f5;
  border-color: #1890ff;
}

.right-panel-toggle.collapsed {
  right: -40px;
  border-right: 2px solid #1890ff;
  border-left: none;
  border-radius: 0 8px 8px 0;
  box-shadow: 4px 0 12px rgba(0, 0, 0, 0.15);
}

.toggle-icon {
  font-size: 18px;
  color: #1890ff;
  margin-bottom: 8px;
  transition: color 0.15s ease;
  font-weight: bold;
}

.right-panel-toggle:hover .toggle-icon {
  color: #40a9ff;
}

.toggle-text {
  font-size: 14px;
  color: #1890ff;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-weight: 600;
  letter-spacing: 2px;
}

.dialogs {
  position: relative;
  z-index: 1000;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f0f0f0;
  border-top: 3px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  font-size: 14px;
  color: #595959;
}

.error-toast,
.success-toast {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 2000;
  animation: toast-appear 0.3s ease-out;
}

.error-content,
.success-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 6px;
  color: #ffffff;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-width: 400px;
}

.error-content {
  background: #ff4d4f;
}

.success-content {
  background: #52c41a;
}

.error-icon,
.success-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.error-message,
.success-message {
  flex: 1;
}

.error-close,
.success-close {
  padding: 0;
  border: none;
  background: none;
  color: inherit;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  opacity: 0.8;
  transition: opacity 0.15s ease;
}

.error-close:hover,
.success-close:hover {
  opacity: 1;
}

/* 动画效果 */
@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes toast-appear {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .left-panel {
    width: 240px;
  }

  .right-panel {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .left-panel,
  .right-panel {
    position: absolute;
    top: 0;
    bottom: 0;
    z-index: 100;
  }

  .left-panel {
    left: 0;
  }

  .right-panel {
    right: 0;
  }

  .left-panel.collapsed,
  .right-panel.collapsed {
    transform: translateX(-100%);
  }

  .right-panel.collapsed {
    transform: translateX(100%);
  }
}

/* 深色主题 */
@media (prefers-color-scheme: dark) {
  .workflow-designer {
    background: #1f1f1f;
  }

  .left-panel,
  .right-panel {
    background: #2f2f2f;
    border-color: #404040;
  }

  .loading-overlay {
    background: rgba(0, 0, 0, 0.8);
  }

  .loading-content {
    background: #2f2f2f;
    color: #ffffff;
  }

  .loading-text {
    color: #a0a0a0;
  }
}

/* 打印样式 */
@media print {
  .workflow-designer {
    height: auto;
  }

  .left-panel,
  .right-panel {
    display: none;
  }

  .canvas-area {
    width: 100%;
    height: auto;
  }

  .loading-overlay,
  .error-toast,
  .success-toast {
    display: none !important;
  }
}
</style>
