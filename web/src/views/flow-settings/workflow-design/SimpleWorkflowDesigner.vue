<template>
  <div class="simple-workflow-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-toolbar">
      <div class="toolbar-left">
        <div class="workflow-title">
          <input 
            v-model="workflowName" 
            class="title-input" 
            placeholder="未命名工作流"
          />
        </div>
      </div>
      <div class="toolbar-center">
        <button class="tool-btn" title="撤销" @click="handleUndo">
          <span class="icon">↩</span>
        </button>
        <button class="tool-btn" title="重做" @click="handleRedo">
          <span class="icon">↪</span>
        </button>
        <div class="toolbar-divider"></div>
        <button class="tool-btn" title="放大" @click="handleZoomIn">
          <span class="icon">+</span>
        </button>
        <span class="zoom-level">{{ Math.round(scale * 100) }}%</span>
        <button class="tool-btn" title="缩小" @click="handleZoomOut">
          <span class="icon">−</span>
        </button>
        <button class="tool-btn" title="适应画布" @click="handleZoomFit">
          <span class="icon">⊡</span>
        </button>
        <div class="toolbar-divider"></div>
        <button class="tool-btn" :class="{ active: showGrid }" title="显示网格" @click="showGrid = !showGrid">
          <span class="icon">#</span>
        </button>
        <div class="toolbar-divider"></div>
        <button class="tool-btn" title="自动布局" @click="handleAutoLayout">
          <span class="icon">⊞</span>
        </button>
      </div>
      <div class="toolbar-right">
        <button class="action-btn secondary" @click="handleImport" title="导入工作流">
          <span class="icon">📥</span>
          <span>导入</span>
        </button>
        <button class="action-btn secondary" @click="handleExport" title="导出工作流">
          <span class="icon">📤</span>
          <span>导出</span>
        </button>
        <div class="toolbar-divider"></div>
        <button class="action-btn secondary" @click="showVersionManager = true" title="版本管理">
          <span class="icon">📋</span>
          <span>版本</span>
        </button>
        <div class="toolbar-divider"></div>
        <button class="action-btn secondary" @click="handleValidate">
          <span class="icon">✓</span>
          <span>验证</span>
        </button>
        <button class="action-btn primary" @click="handleSave">
          <span class="icon">💾</span>
          <span>保存</span>
        </button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="designer-main">
      <!-- 左侧节点面板 -->
      <div class="node-panel" :class="{ collapsed: nodePanelCollapsed }">
        <!-- 边缘收起按钮 -->
        <button class="edge-collapse-btn left" @click="nodePanelCollapsed = !nodePanelCollapsed">
          {{ nodePanelCollapsed ? '▶' : '◀' }}
        </button>
        <div class="panel-header">
          <span class="panel-title">节点库</span>
        </div>
        
        <div v-show="!nodePanelCollapsed" class="panel-content">
          <!-- 搜索框 -->
          <div class="search-box">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="搜索节点..." 
              class="search-input"
            />
          </div>
          
          <!-- 节点分类 -->
          <div class="node-categories">
            <div 
              v-for="category in filteredCategories" 
              :key="category.key" 
              class="category-section"
            >
              <div 
                class="category-header" 
                @click="toggleCategory(category.key)"
              >
                <span class="category-icon">{{ category.icon }}</span>
                <span class="category-name">{{ category.name }}</span>
                <span class="category-toggle">{{ expandedCategories.has(category.key) ? '▼' : '▶' }}</span>
              </div>
              
              <div v-show="expandedCategories.has(category.key)" class="category-nodes">
                <div
                  v-for="node in category.nodes"
                  :key="node.type"
                  class="node-item"
                  draggable="true"
                  @dragstart="handleDragStart($event, node)"
                  @dragend="handleDragEnd"
                >
                  <div class="node-icon" :style="{ background: node.color }">
                    {{ node.icon }}
                  </div>
                  <div class="node-info">
                    <div class="node-name">{{ node.name }}</div>
                    <div class="node-desc">{{ node.description }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中央画布 -->
      <div 
        ref="canvasContainer"
        class="canvas-container"
        @dragover.prevent="handleDragOver"
        @drop="handleDrop"
        @mousedown="handleCanvasMouseDown"
        @mousemove="handleCanvasMouseMove"
        @mouseup="handleCanvasMouseUp"
        @wheel="handleWheel"
      >
        <!-- 网格背景 -->
        <svg v-if="showGrid" class="canvas-grid">
          <defs>
            <pattern id="grid" :width="20 * scale" :height="20 * scale" patternUnits="userSpaceOnUse">
              <path :d="`M ${20 * scale} 0 L 0 0 0 ${20 * scale}`" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>

        <!-- 画布内容 -->
        <div 
          class="canvas-content"
          :style="canvasTransform"
        >
          <!-- 节点 -->
          <div
            v-for="node in nodes"
            :key="node.id"
            :data-node-id="node.id"
            class="workflow-node"
            :class="{ 
              selected: selectedNodeId === node.id, 
              [node.type]: true,
              'port-hover': hoverPort?.nodeId === node.id
            }"
            :style="{ left: node.x + 'px', top: node.y + 'px' }"
            @mousedown.stop="handleNodeMouseDown($event, node)"
            @click.stop="selectNode(node)"
          >
            <!-- 输入端口 - 左侧边缘（开始节点不显示） -->
            <div 
              v-if="node.type !== 'start'"
              class="port input-port" 
              :class="{ 'can-connect': isDrawingConnection && connectionStart?.nodeId !== node.id }"
              title="输入端口"
              @mouseup.stop="handlePortMouseUp(node, 'input')"
              @mouseenter="handlePortMouseEnter(node, 'input')"
              @mouseleave="handlePortMouseLeave"
            ></div>
            <!-- 输出端口 - 右侧边缘（结束节点不显示） -->
            <div 
              v-if="node.type !== 'end'"
              class="port output-port" 
              title="输出端口 - 拖拽创建连接"
              @mousedown.stop="handlePortMouseDown($event, node, 'output')"
            ></div>
            <div class="node-header" :style="{ background: getNodeColor(node.type) }">
              <span class="node-type-icon">{{ getNodeIcon(node.type) }}</span>
              <span class="node-title">{{ node.name }}</span>
            </div>
            <div class="node-body">
              <span class="node-type-label">{{ getNodeTypeName(node.type) }}</span>
            </div>
          </div>

          <!-- 连接线 -->
          <svg class="connections-layer">
            <!-- 正在绘制的临时连接线 -->
            <path
              v-if="isDrawingConnection"
              :d="tempConnectionPath"
              class="connection-line temp"
            />
            <!-- 已有连接线 -->
            <g v-for="conn in connections" :key="conn.id" class="connection-group">
              <path
                :d="getConnectionPath(conn)"
                class="connection-line"
                :class="{ selected: selectedConnectionId === conn.id }"
                @click.stop="selectConnection(conn)"
              />
              <!-- 连接线中点的删除按钮 -->
              <g 
                v-if="selectedConnectionId === conn.id"
                class="connection-delete-btn"
                :transform="`translate(${getConnectionMidpoint(conn).x}, ${getConnectionMidpoint(conn).y})`"
                @click.stop="deleteConnection(conn.id)"
              >
                <circle r="12" class="delete-btn-bg" />
                <text x="0" y="4" text-anchor="middle" class="delete-btn-icon">×</text>
              </g>
            </g>
          </svg>
        </div>

        <!-- 空状态提示 -->
        <div v-if="nodes.length === 0" class="empty-canvas">
          <div class="empty-icon">📋</div>
          <div class="empty-text">从左侧拖拽节点到画布开始设计</div>
        </div>
      </div>

      <!-- 右侧属性面板 -->
      <div class="property-panel" :class="{ collapsed: propertyPanelCollapsed }">
        <!-- 边缘收起按钮 -->
        <button class="edge-collapse-btn right" @click="propertyPanelCollapsed = !propertyPanelCollapsed">
          {{ propertyPanelCollapsed ? '◀' : '▶' }}
        </button>
        <div class="panel-header">
          <span class="panel-title">属性</span>
        </div>
        
        <div v-show="!propertyPanelCollapsed" class="panel-content">
          <div v-if="selectedNode" class="property-form">
            <!-- 基础信息 -->
            <div class="form-section">
              <div class="section-title">基础信息</div>
              <div class="form-group">
                <label>节点名称</label>
                <input v-model="selectedNode.name" type="text" class="form-input" @input="markUnsaved" />
              </div>
              <div class="form-group">
                <label>节点类型</label>
                <div class="form-value">{{ getNodeTypeName(selectedNode.type) }}</div>
              </div>
              <div class="form-group">
                <label>描述</label>
                <textarea v-model="selectedNode.description" class="form-textarea" rows="2" @input="markUnsaved"></textarea>
              </div>
            </div>
            
            <!-- 节点特殊属性 -->
            <div v-if="getNodePropertyFields(selectedNode.type).length > 0" class="form-section">
              <div class="section-title">节点配置</div>
              <template v-for="field in getNodePropertyFields(selectedNode.type)" :key="field.field">
                <div class="form-group" v-if="shouldShowPropertyField(field, selectedNode.properties)">
                  <label>
                    {{ field.label }}
                    <span v-if="field.required" class="required">*</span>
                  </label>
                  
                  <!-- 文本输入 -->
                  <input 
                    v-if="field.type === 'input'" 
                    v-model="selectedNode.properties[field.field]" 
                    type="text" 
                    class="form-input"
                    :placeholder="field.placeholder"
                    @input="markUnsaved"
                  />
                  
                  <!-- 数字输入 -->
                  <input 
                    v-else-if="field.type === 'number'" 
                    v-model.number="selectedNode.properties[field.field]" 
                    type="number" 
                    class="form-input"
                    :placeholder="field.placeholder"
                    :min="field.props?.min"
                    :max="field.props?.max"
                    @input="markUnsaved"
                  />
                  
                  <!-- 多行文本 -->
                  <textarea 
                    v-else-if="field.type === 'textarea'" 
                    v-model="selectedNode.properties[field.field]" 
                    class="form-textarea"
                    :placeholder="field.placeholder"
                    :rows="field.props?.rows || 3"
                    @input="markUnsaved"
                  ></textarea>
                  
                  <!-- 下拉选择 -->
                  <select 
                    v-else-if="field.type === 'select'" 
                    v-model="selectedNode.properties[field.field]" 
                    class="form-select"
                    @change="markUnsaved"
                  >
                    <option v-for="opt in field.options" :key="String(opt.value)" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                  
                  <!-- 多选 -->
                  <div v-else-if="field.type === 'multiselect'" class="multiselect-group">
                    <label v-for="opt in field.options" :key="String(opt.value)" class="checkbox-item">
                      <input 
                        type="checkbox" 
                        :value="opt.value"
                        :checked="(selectedNode.properties[field.field] || []).includes(opt.value)"
                        @change="toggleMultiSelect(field.field, opt.value)"
                      />
                      {{ opt.label }}
                    </label>
                  </div>
                  
                  <!-- 开关 -->
                  <label v-else-if="field.type === 'switch'" class="switch-label">
                    <input 
                      type="checkbox" 
                      v-model="selectedNode.properties[field.field]"
                      @change="markUnsaved"
                    />
                    <span class="switch-text">{{ selectedNode.properties[field.field] ? '是' : '否' }}</span>
                  </label>
                  
                  <!-- JSON编辑 -->
                  <textarea 
                    v-else-if="field.type === 'json'" 
                    v-model="selectedNode.properties[field.field]" 
                    class="form-textarea code"
                    :placeholder="field.placeholder || '{}'"
                    rows="4"
                    @input="markUnsaved"
                  ></textarea>
                  
                  <!-- 代码编辑 -->
                  <textarea 
                    v-else-if="field.type === 'code'" 
                    v-model="selectedNode.properties[field.field]" 
                    class="form-textarea code"
                    :placeholder="field.placeholder"
                    :rows="field.props?.height ? Math.floor(field.props.height / 20) : 6"
                    @input="markUnsaved"
                  ></textarea>
                  
                  <!-- 默认文本输入 -->
                  <input 
                    v-else
                    v-model="selectedNode.properties[field.field]" 
                    type="text" 
                    class="form-input"
                    :placeholder="field.placeholder"
                    @input="markUnsaved"
                  />
                  
                  <!-- 字段描述 -->
                  <div v-if="field.description" class="field-desc">{{ field.description }}</div>
                </div>
              </template>
            </div>
            
            <div class="form-actions">
              <button class="btn-delete" @click="deleteSelectedNode">删除节点</button>
            </div>
          </div>
          <div v-else class="no-selection">
            <div class="no-selection-icon">👆</div>
            <div class="no-selection-text">选择节点查看属性</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 执行监控面板 -->
    <ExecutionMonitor
      v-if="showExecutionMonitor"
      :workflow-id="workflowId"
      :nodes="nodes"
      :connections="connections"
      @highlight-node="highlightNode"
      @execution-complete="handleExecutionComplete"
    />

    <!-- 导入导出对话框 -->
    <ImportExportDialog
      :visible="showImportExportDialog"
      :mode="importExportMode"
      :workflow-data="workflowExportData"
      @close="showImportExportDialog = false"
      @import="handleImportData"
      @export="handleExportComplete"
    />

    <!-- 版本管理对话框 -->
    <VersionManager 
      v-model="showVersionManager" 
      :workflow-id="workflowId"
      @rollback="handleVersionRollback"
    />

    <!-- 状态栏 -->
    <div class="designer-statusbar">
      <div class="status-left">
        <span class="status-item">节点: {{ nodes.length }}</span>
        <span class="status-item">连接: {{ connections.length }}</span>
        <button 
          class="status-btn" 
          :class="{ active: showExecutionMonitor }"
          @click="showExecutionMonitor = !showExecutionMonitor"
        >
          📊 执行监控
        </button>
      </div>
      <div class="status-right">
        <span class="status-item">{{ saveStatus }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import ExecutionMonitor from './components/UI/ExecutionMonitor.vue'
import ImportExportDialog from './components/UI/ImportExportDialog.vue'
import VersionManager from './components/UI/VersionManager.vue'
import { getNodePropertySchema, shouldShowField } from './utils/nodePropertySchemas'

// 路由
const route = useRoute()

// 基础状态
const workflowId = ref<string | null>(null)
const workflowName = ref('未命名工作流')
const scale = ref(1)
const showGrid = ref(true)
const nodePanelCollapsed = ref(false)
const propertyPanelCollapsed = ref(false)
const saveStatus = ref('未保存')

// 执行监控状态
const showExecutionMonitor = ref(false)

// 导入导出状态
const showImportExportDialog = ref(false)
const importExportMode = ref<'import' | 'export'>('export')

// 版本管理状态
const showVersionManager = ref(false)

// 画布状态
const canvasContainer = ref<HTMLElement | null>(null)
const offset = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const draggedNode = ref<any>(null)
const draggingNodeId = ref<string | null>(null)
const nodeStartPos = ref({ x: 0, y: 0 })

// 节点和连接
const nodes = ref<any[]>([])
const connections = ref<any[]>([])
const selectedNodeId = ref<string | null>(null)
const selectedConnectionId = ref<string | null>(null)
const searchQuery = ref('')
const expandedCategories = ref(new Set(['basic', 'logic', 'action']))

// 连接线绘制状态
const isDrawingConnection = ref(false)
const connectionStart = ref<{ nodeId: string; portType: string } | null>(null)
const connectionEndPos = ref({ x: 0, y: 0 })
const hoverPort = ref<{ nodeId: string; portType: string } | null>(null)

// 节点分类定义
const nodeCategories = [
  {
    key: 'basic',
    name: '基础节点',
    icon: '📦',
    nodes: [
      { type: 'start', name: '开始', icon: '▶', color: '#52c41a', description: '流程开始' },
      { type: 'end', name: '结束', icon: '⏹', color: '#ff4d4f', description: '流程结束' },
    ]
  },
  {
    key: 'logic',
    name: '逻辑控制',
    icon: '🔀',
    nodes: [
      { type: 'condition', name: '条件判断', icon: '❓', color: '#faad14', description: '条件分支' },
      { type: 'loop', name: '循环', icon: '🔄', color: '#722ed1', description: '循环执行' },
      { type: 'parallel', name: '并行', icon: '⫘', color: '#13c2c2', description: '并行执行' },
      { type: 'switch', name: '多路分支', icon: '🔀', color: '#9254de', description: '多条件分支' },
    ]
  },
  {
    key: 'integration',
    name: '集成节点',
    icon: '🔌',
    nodes: [
      { type: 'metadata_analysis', name: '元数据分析', icon: '📈', color: '#722ed1', description: '执行元数据模型分析' },
    ]
  },
  {
    key: 'device',
    name: '设备节点',
    icon: '🔧',
    nodes: [
      { type: 'device_query', name: '设备查询', icon: '🔍', color: '#1890ff', description: '查询设备信息' },
      { type: 'device_control', name: '设备控制', icon: '🎮', color: '#52c41a', description: '控制设备操作' },
      { type: 'device_data', name: '数据采集', icon: '📊', color: '#13c2c2', description: '采集设备数据' },
      { type: 'device_status', name: '状态检测', icon: '📡', color: '#faad14', description: '检测设备状态' },
    ]
  },
  {
    key: 'alarm',
    name: '报警节点',
    icon: '🚨',
    nodes: [
      { type: 'alarm_trigger', name: '触发报警', icon: '⚠️', color: '#ff4d4f', description: '触发报警事件' },
      { type: 'alarm_check', name: '报警检测', icon: '🔔', color: '#fa8c16', description: '检测报警条件' },
      { type: 'alarm_clear', name: '清除报警', icon: '✅', color: '#52c41a', description: '清除报警状态' },
    ]
  },
  {
    key: 'action',
    name: '动作节点',
    icon: '⚡',
    nodes: [
      { type: 'api', name: 'API调用', icon: '🌐', color: '#1890ff', description: '调用外部API' },
      { type: 'database', name: '数据库', icon: '🗄', color: '#eb2f96', description: '数据库操作' },
      { type: 'script', name: '脚本', icon: '📜', color: '#fa8c16', description: '执行脚本' },
      { type: 'delay', name: '延时', icon: '⏱', color: '#a0d911', description: '延时等待' },
      { type: 'http', name: 'HTTP请求', icon: '🔗', color: '#722ed1', description: '发送HTTP请求' },
      { type: 'transform', name: '数据转换', icon: '🔄', color: '#13c2c2', description: '转换数据格式' },
    ]
  },
  {
    key: 'notify',
    name: '通知节点',
    icon: '📢',
    nodes: [
      { type: 'notification', name: '站内通知', icon: '🔔', color: '#2f54eb', description: '发送站内通知' },
      { type: 'email', name: '邮件', icon: '📧', color: '#f5222d', description: '发送邮件' },
      { type: 'sms', name: '短信', icon: '📱', color: '#52c41a', description: '发送短信' },
      { type: 'webhook', name: 'Webhook', icon: '🪝', color: '#722ed1', description: '调用Webhook' },
    ]
  }
]

// 计算属性
const filteredCategories = computed(() => {
  if (!searchQuery.value) return nodeCategories
  
  const query = searchQuery.value.toLowerCase()
  return nodeCategories.map(cat => ({
    ...cat,
    nodes: cat.nodes.filter(n => 
      n.name.toLowerCase().includes(query) || 
      n.description.toLowerCase().includes(query)
    )
  })).filter(cat => cat.nodes.length > 0)
})

const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return nodes.value.find(n => n.id === selectedNodeId.value)
})

const canvasTransform = computed(() => ({
  transform: `translate(${offset.value.x}px, ${offset.value.y}px) scale(${scale.value})`
}))

// 节点尺寸常量
// CSS: .workflow-node { width: 160px; border: 2px solid; }
// 端口 CSS: .port { width: 12px; height: 12px; border: 2px solid; position: absolute; }
// 端口 border-box 尺寸: 12 + 2*2 = 16px
// 输入端口: .input-port { left: -8px; top: 50%; transform: translateY(-50%); }
// 输出端口: .output-port { right: -8px; top: 50%; transform: translateY(-50%); }
//
// 端口定位是相对于节点的 padding-box（border 内边缘）
// 输入端口中心 X = node.x + node_border - offset + port_border_box/2 = node.x + 2 - 8 + 8 = node.x + 2
// 输出端口中心 X = node.x + node_border + content + offset - port_border_box/2 = node.x + 2 + 160 + 8 - 8 = node.x + 162
const NODE_CONTENT_WIDTH = 160  // CSS content width
const NODE_BORDER = 2           // CSS border width
const PORT_CONTENT_SIZE = 12    // 端口 content 尺寸
const PORT_BORDER = 2           // 端口 border 宽度
const PORT_TOTAL_SIZE = PORT_CONTENT_SIZE + PORT_BORDER * 2  // 端口 border-box 尺寸 = 16px
const PORT_OFFSET = 8           // 端口偏移量 (left: -8px / right: -8px)

// 缓存节点高度，避免重复计算
const nodeHeightCache = new Map<string, number>()

// 获取节点实际渲染高度
function getNodeHeight(nodeId: string): number {
  // 先检查缓存
  if (nodeHeightCache.has(nodeId)) {
    return nodeHeightCache.get(nodeId)!
  }
  
  // 尝试从 DOM 获取实际高度（使用 data-node-id 属性）
  // 注意：offsetHeight 不受 CSS transform 影响，返回的是元素的布局高度
  const nodeEl = document.querySelector(`[data-node-id="${nodeId}"]`) as HTMLElement
  if (nodeEl) {
    const height = nodeEl.offsetHeight
    if (height > 0) {
      nodeHeightCache.set(nodeId, height)
      return height
    }
  }
  
  // 默认高度估算：
  // header: padding 10px*2 + line-height ~20px = 40px
  // body: padding 8px*2 + line-height ~16px = 32px
  // border: 2px*2 = 4px (但 offsetHeight 已包含)
  // 总计约 72-76px
  return 76
}

// 清除节点高度缓存（节点变化时调用）
function clearNodeHeightCache(nodeId?: string) {
  if (nodeId) {
    nodeHeightCache.delete(nodeId)
  } else {
    nodeHeightCache.clear()
  }
}

// 获取输出端口位置（节点右侧中间）
// 端口 CSS: right: -8px, border-box 尺寸 16px
// 端口定位是相对于节点的 padding box（border 内边缘）
// 端口右边缘位置 = padding box 右边缘 + 8 = node.x + 2 + 160 + 8 = node.x + 170
// 端口中心 X = 端口右边缘 - 端口 border-box 半径 = node.x + 170 - 8 = node.x + 162
function getOutputPortPosition(node: any) {
  const nodeHeight = getNodeHeight(node.id)
  return {
    x: node.x + NODE_BORDER + NODE_CONTENT_WIDTH + PORT_OFFSET - PORT_TOTAL_SIZE / 2,  // = node.x + 2 + 160 + 8 - 8 = node.x + 162
    y: node.y + nodeHeight / 2
  }
}

// 获取输入端口位置（节点左侧中间）
// 端口 CSS: left: -8px, border-box 尺寸 16px
// 端口定位是相对于节点的 padding box（border 内边缘）
// 端口左边缘位置 = padding box 左边缘 - 8 = node.x + 2 - 8 = node.x - 6
// 端口中心 X = 端口左边缘 + 端口 border-box 半径 = node.x - 6 + 8 = node.x + 2
function getInputPortPosition(node: any) {
  const nodeHeight = getNodeHeight(node.id)
  return {
    x: node.x + NODE_BORDER - PORT_OFFSET + PORT_TOTAL_SIZE / 2,  // = node.x + 2 - 8 + 8 = node.x + 2
    y: node.y + nodeHeight / 2
  }
}

// 临时连接线路径
const tempConnectionPath = computed(() => {
  if (!isDrawingConnection.value || !connectionStart.value) return ''
  const fromNode = nodes.value.find(n => n.id === connectionStart.value!.nodeId)
  if (!fromNode) return ''
  
  // 输出端口位置
  const outputPos = getOutputPortPosition(fromNode)
  const x1 = outputPos.x
  const y1 = outputPos.y
  const x2 = connectionEndPos.value.x
  const y2 = connectionEndPos.value.y
  
  return createBezierPath(x1, y1, x2, y2)
})

// 创建平滑贝塞尔曲线路径
function createBezierPath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = Math.abs(x2 - x1)
  const dy = Math.abs(y2 - y1)
  // 控制点偏移量，根据距离动态调整
  const offset = Math.min(Math.max(dx * 0.5, 50), 150)
  
  const cx1 = x1 + offset
  const cy1 = y1
  const cx2 = x2 - offset
  const cy2 = y2
  
  return `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`
}

// 节点颜色和图标
const nodeColorMap: Record<string, string> = {
  // 基础节点
  start: '#52c41a', end: '#ff4d4f',
  // 逻辑控制
  condition: '#faad14', loop: '#722ed1', parallel: '#13c2c2', switch: '#9254de',
  // 集成节点
  metadata_analysis: '#722ed1',
  // 设备节点
  device_query: '#1890ff', device_control: '#52c41a', device_data: '#13c2c2', device_status: '#faad14',
  // 报警节点
  alarm_trigger: '#ff4d4f', alarm_check: '#fa8c16', alarm_clear: '#52c41a',
  // 动作节点
  api: '#1890ff', database: '#eb2f96', script: '#fa8c16', delay: '#a0d911',
  http: '#722ed1', transform: '#13c2c2',
  // 通知节点
  notification: '#2f54eb', email: '#f5222d', sms: '#52c41a', webhook: '#722ed1'
}

const nodeIconMap: Record<string, string> = {
  // 基础节点
  start: '▶', end: '⏹',
  // 逻辑控制
  condition: '❓', loop: '🔄', parallel: '⫘', switch: '🔀',
  // 集成节点
  metadata_analysis: '📈',
  // 设备节点
  device_query: '🔍', device_control: '🎮', device_data: '📊', device_status: '📡',
  // 报警节点
  alarm_trigger: '⚠️', alarm_check: '🔔', alarm_clear: '✅',
  // 动作节点
  api: '🌐', database: '🗄', script: '📜', delay: '⏱', http: '🔗', transform: '🔄',
  // 通知节点
  notification: '🔔', email: '📧', sms: '📱', webhook: '🪝'
}

const nodeNameMap: Record<string, string> = {
  // 基础节点
  start: '开始', end: '结束',
  // 逻辑控制
  condition: '条件判断', loop: '循环', parallel: '并行', switch: '多路分支',
  // 集成节点
  metadata_analysis: '元数据分析',
  // 设备节点
  device_query: '设备查询', device_control: '设备控制', device_data: '数据采集', device_status: '状态检测',
  // 报警节点
  alarm_trigger: '触发报警', alarm_check: '报警检测', alarm_clear: '清除报警',
  // 动作节点
  api: 'API调用', database: '数据库', script: '脚本', delay: '延时', http: 'HTTP请求', transform: '数据转换',
  // 通知节点
  notification: '站内通知', email: '邮件', sms: '短信', webhook: 'Webhook'
}

function getNodeColor(type: string) { return nodeColorMap[type] || '#1890ff' }
function getNodeIcon(type: string) { return nodeIconMap[type] || '📦' }
function getNodeTypeName(type: string) { return nodeNameMap[type] || type }

// 获取节点属性字段配置
function getNodePropertyFields(nodeType: string) {
  const schema = getNodePropertySchema(nodeType)
  // 过滤掉基础字段（name, description），只返回特殊属性
  return schema.fields.filter(f => !['name', 'description'].includes(f.field))
}

// 判断属性字段是否应该显示
function shouldShowPropertyField(field: any, properties: any) {
  return shouldShowField(field, properties || {})
}

// 标记未保存
function markUnsaved() {
  saveStatus.value = '未保存'
}

// 多选切换
function toggleMultiSelect(fieldName: string, value: any) {
  if (!selectedNode.value) return
  if (!selectedNode.value.properties) {
    selectedNode.value.properties = {}
  }
  const arr = selectedNode.value.properties[fieldName] || []
  const index = arr.indexOf(value)
  if (index > -1) {
    arr.splice(index, 1)
  } else {
    arr.push(value)
  }
  selectedNode.value.properties[fieldName] = arr
  markUnsaved()
}

// 确保节点有properties对象
watch(selectedNodeId, (newId) => {
  if (newId) {
    const node = nodes.value.find(n => n.id === newId)
    if (node && !node.properties) {
      node.properties = {}
    }
  }
})

// 分类展开/折叠
function toggleCategory(key: string) {
  if (expandedCategories.value.has(key)) {
    expandedCategories.value.delete(key)
  } else {
    expandedCategories.value.add(key)
  }
}

// 拖拽处理
function handleDragStart(event: DragEvent, node: any) {
  draggedNode.value = node
  event.dataTransfer!.effectAllowed = 'copy'
  event.dataTransfer!.setData('text/plain', JSON.stringify(node))
}

function handleDragEnd() {
  draggedNode.value = null
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'copy'
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  if (!draggedNode.value || !canvasContainer.value) return
  
  const rect = canvasContainer.value.getBoundingClientRect()
  const x = (event.clientX - rect.left - offset.value.x) / scale.value
  const y = (event.clientY - rect.top - offset.value.y) / scale.value
  
  // 创建新节点
  const newNode = {
    id: `node_${Date.now()}`,
    type: draggedNode.value.type,
    name: draggedNode.value.name,
    description: '',
    x: Math.round(x / 20) * 20, // 对齐网格
    y: Math.round(y / 20) * 20,
    properties: {}
  }
  
  nodes.value.push(newNode)
  selectNode(newNode)
  saveStatus.value = '未保存'
  draggedNode.value = null
  
  // 等待 DOM 更新后清除高度缓存，以便重新计算
  nextTick(() => {
    clearNodeHeightCache(newNode.id)
  })
}

// 画布操作
function handleCanvasMouseDown(event: MouseEvent) {
  if (event.target === canvasContainer.value || (event.target as HTMLElement).classList.contains('canvas-content')) {
    isDragging.value = true
    dragStart.value = { x: event.clientX - offset.value.x, y: event.clientY - offset.value.y }
    selectedNodeId.value = null
    selectedConnectionId.value = null
  }
}

function handleCanvasMouseMove(event: MouseEvent) {
  if (isDragging.value) {
    offset.value = {
      x: event.clientX - dragStart.value.x,
      y: event.clientY - dragStart.value.y
    }
  } else if (draggingNodeId.value) {
    const node = nodes.value.find(n => n.id === draggingNodeId.value)
    if (node && canvasContainer.value) {
      const rect = canvasContainer.value.getBoundingClientRect()
      const x = (event.clientX - rect.left - offset.value.x) / scale.value - nodeStartPos.value.x
      const y = (event.clientY - rect.top - offset.value.y) / scale.value - nodeStartPos.value.y
      node.x = Math.round(x / 20) * 20
      node.y = Math.round(y / 20) * 20
    }
  } else if (isDrawingConnection.value && canvasContainer.value) {
    // 更新临时连接线的结束位置
    const rect = canvasContainer.value.getBoundingClientRect()
    const mouseX = (event.clientX - rect.left - offset.value.x) / scale.value
    const mouseY = (event.clientY - rect.top - offset.value.y) / scale.value
    
    // 检查是否接近某个端口，实现吸附效果
    const nearbyPort = findNearbyPort(mouseX, mouseY)
    if (nearbyPort) {
      // 吸附到端口圆点中心位置
      const targetNode = nodes.value.find(n => n.id === nearbyPort.nodeId)
      if (targetNode) {
        const inputPos = getInputPortPosition(targetNode)
        connectionEndPos.value = {
          x: inputPos.x,
          y: inputPos.y
        }
        hoverPort.value = nearbyPort
      }
    } else {
      connectionEndPos.value = { x: mouseX, y: mouseY }
      hoverPort.value = null
    }
  }
}

function handleCanvasMouseUp() {
  isDragging.value = false
  draggingNodeId.value = null
  
  // 处理连接线绘制
  if (isDrawingConnection.value && connectionStart.value) {
    // 如果有吸附的端口，创建连接
    if (hoverPort.value) {
      createConnection(connectionStart.value.nodeId, hoverPort.value.nodeId)
    } else {
      // 取消连接线绘制
      isDrawingConnection.value = false
      connectionStart.value = null
      hoverPort.value = null
    }
  }
}

// 端口事件处理
function handlePortMouseDown(event: MouseEvent, node: any, portType: string) {
  event.preventDefault()
  event.stopPropagation()
  isDrawingConnection.value = true
  connectionStart.value = { nodeId: node.id, portType }
  
  // 初始化结束位置
  if (canvasContainer.value) {
    const rect = canvasContainer.value.getBoundingClientRect()
    connectionEndPos.value = {
      x: (event.clientX - rect.left - offset.value.x) / scale.value,
      y: (event.clientY - rect.top - offset.value.y) / scale.value
    }
  }
}

function handlePortMouseUp(node: any, portType: string) {
  if (isDrawingConnection.value && connectionStart.value) {
    createConnection(connectionStart.value.nodeId, node.id)
  }
}

// 创建连接（带验证）
function createConnection(fromNodeId: string, toNodeId: string) {
  // 不能连接到自己
  if (fromNodeId === toNodeId) {
    isDrawingConnection.value = false
    connectionStart.value = null
    hoverPort.value = null
    return
  }
  
  // 检查是否已存在相同连接
  const exists = connections.value.some(c => 
    c.fromNodeId === fromNodeId && c.toNodeId === toNodeId
  )
  
  if (!exists) {
    // 创建新连接
    const newConnection = {
      id: `conn_${Date.now()}`,
      fromNodeId: fromNodeId,
      toNodeId: toNodeId
    }
    connections.value.push(newConnection)
    saveStatus.value = '未保存'
  }
  
  isDrawingConnection.value = false
  connectionStart.value = null
  hoverPort.value = null
}

// 检查是否接近某个端口（用于吸附）
function findNearbyPort(x: number, y: number): { nodeId: string; portType: string } | null {
  const SNAP_DISTANCE = 25 // 吸附距离
  
  for (const node of nodes.value) {
    // 不能连接到自己
    if (connectionStart.value?.nodeId === node.id) continue
    
    // 检查输入端口位置
    const inputPos = getInputPortPosition(node)
    const inputDist = Math.sqrt(Math.pow(x - inputPos.x, 2) + Math.pow(y - inputPos.y, 2))
    
    if (inputDist < SNAP_DISTANCE) {
      return { nodeId: node.id, portType: 'input' }
    }
  }
  
  return null
}

function handlePortMouseEnter(node: any, portType: string) {
  if (isDrawingConnection.value) {
    hoverPort.value = { nodeId: node.id, portType }
  }
}

function handlePortMouseLeave() {
  hoverPort.value = null
}

function handleNodeMouseDown(event: MouseEvent, node: any) {
  draggingNodeId.value = node.id
  const rect = (event.target as HTMLElement).closest('.workflow-node')!.getBoundingClientRect()
  const containerRect = canvasContainer.value!.getBoundingClientRect()
  nodeStartPos.value = {
    x: (event.clientX - rect.left),
    y: (event.clientY - rect.top)
  }
}

function handleWheel(event: WheelEvent) {
  event.preventDefault()
  const delta = event.deltaY > 0 ? -0.1 : 0.1
  scale.value = Math.max(0.25, Math.min(2, scale.value + delta))
}

// 缩放操作
function handleZoomIn() { scale.value = Math.min(2, scale.value + 0.1) }
function handleZoomOut() { scale.value = Math.max(0.25, scale.value - 0.1) }
function handleZoomFit() { scale.value = 1; offset.value = { x: 0, y: 0 } }

// 撤销/重做
function handleUndo() { console.log('Undo') }
function handleRedo() { console.log('Redo') }

// 选择
function selectNode(node: any) {
  selectedNodeId.value = node.id
  selectedConnectionId.value = null
}

function selectConnection(conn: any) {
  selectedConnectionId.value = conn.id
  selectedNodeId.value = null
}

function deleteSelectedNode() {
  if (!selectedNodeId.value) return
  nodes.value = nodes.value.filter(n => n.id !== selectedNodeId.value)
  connections.value = connections.value.filter(c => 
    c.fromNodeId !== selectedNodeId.value && c.toNodeId !== selectedNodeId.value
  )
  selectedNodeId.value = null
  saveStatus.value = '未保存'
}

// 删除连接线
function deleteConnection(connId: string) {
  connections.value = connections.value.filter(c => c.id !== connId)
  selectedConnectionId.value = null
  saveStatus.value = '未保存'
}

// 获取连接线中点位置（用于放置删除按钮）
function getConnectionMidpoint(conn: any): { x: number; y: number } {
  const fromNode = nodes.value.find(n => n.id === conn.fromNodeId)
  const toNode = nodes.value.find(n => n.id === conn.toNodeId)
  if (!fromNode || !toNode) return { x: 0, y: 0 }
  
  const outputPos = getOutputPortPosition(fromNode)
  const inputPos = getInputPortPosition(toNode)
  
  // 贝塞尔曲线中点近似计算
  return {
    x: (outputPos.x + inputPos.x) / 2,
    y: (outputPos.y + inputPos.y) / 2
  }
}

// 连接线路径
function getConnectionPath(conn: any): string {
  const fromNode = nodes.value.find(n => n.id === conn.fromNodeId)
  const toNode = nodes.value.find(n => n.id === conn.toNodeId)
  if (!fromNode || !toNode) return ''
  
  // 输出端口位置（源节点右侧）
  const outputPos = getOutputPortPosition(fromNode)
  // 输入端口位置（目标节点左侧）
  const inputPos = getInputPortPosition(toNode)
  
  return createBezierPath(outputPos.x, outputPos.y, inputPos.x, inputPos.y)
}

// 验证和保存
function handleValidate() {
  const hasStart = nodes.value.some(n => n.type === 'start')
  const hasEnd = nodes.value.some(n => n.type === 'end')
  
  if (!hasStart) {
    alert('工作流缺少开始节点')
    return
  }
  if (!hasEnd) {
    alert('工作流缺少结束节点')
    return
  }
  alert('工作流验证通过！')
}

// handleSave 已移至文件末尾的生命周期部分

// 自动布局功能
function handleAutoLayout() {
  if (nodes.value.length === 0) {
    alert('没有节点需要布局')
    return
  }
  
  // 使用层次布局算法
  const layoutResult = calculateHierarchicalLayout()
  
  // 应用布局结果
  layoutResult.forEach(({ id, x, y }) => {
    const node = nodes.value.find(n => n.id === id)
    if (node) {
      node.x = x
      node.y = y
    }
  })
  
  // 清除节点高度缓存
  clearNodeHeightCache()
  saveStatus.value = '未保存'
}

// 层次布局算法
function calculateHierarchicalLayout() {
  const NODE_WIDTH = 180
  const NODE_HEIGHT = 80
  const HORIZONTAL_GAP = 100
  const VERTICAL_GAP = 60
  const START_X = 100
  const START_Y = 100
  
  // 构建邻接表
  const adjacency: Map<string, string[]> = new Map()
  const inDegree: Map<string, number> = new Map()
  
  nodes.value.forEach(node => {
    adjacency.set(node.id, [])
    inDegree.set(node.id, 0)
  })
  
  connections.value.forEach(conn => {
    const fromId = conn.fromNodeId
    const toId = conn.toNodeId
    if (adjacency.has(fromId)) {
      adjacency.get(fromId)!.push(toId)
    }
    inDegree.set(toId, (inDegree.get(toId) || 0) + 1)
  })
  
  // 拓扑排序，按层级分组
  const levels: string[][] = []
  const visited = new Set<string>()
  
  // 找到所有入度为0的节点作为第一层
  let currentLevel: string[] = []
  nodes.value.forEach(node => {
    if (inDegree.get(node.id) === 0) {
      currentLevel.push(node.id)
      visited.add(node.id)
    }
  })
  
  // 如果没有入度为0的节点，从开始节点开始
  if (currentLevel.length === 0) {
    const startNode = nodes.value.find(n => n.type === 'start')
    if (startNode) {
      currentLevel.push(startNode.id)
      visited.add(startNode.id)
    } else if (nodes.value.length > 0) {
      currentLevel.push(nodes.value[0].id)
      visited.add(nodes.value[0].id)
    }
  }
  
  while (currentLevel.length > 0) {
    levels.push(currentLevel)
    const nextLevel: string[] = []
    
    currentLevel.forEach(nodeId => {
      const neighbors = adjacency.get(nodeId) || []
      neighbors.forEach(neighborId => {
        if (!visited.has(neighborId)) {
          visited.add(neighborId)
          nextLevel.push(neighborId)
        }
      })
    })
    
    currentLevel = nextLevel
  }
  
  // 添加未访问的节点到最后一层
  nodes.value.forEach(node => {
    if (!visited.has(node.id)) {
      if (levels.length === 0) {
        levels.push([])
      }
      levels[levels.length - 1].push(node.id)
    }
  })
  
  // 计算每个节点的位置
  const result: { id: string; x: number; y: number }[] = []
  
  levels.forEach((level, levelIndex) => {
    const levelWidth = level.length * NODE_WIDTH + (level.length - 1) * VERTICAL_GAP
    const startY = START_Y + (levels.reduce((max, l) => Math.max(max, l.length), 0) * (NODE_HEIGHT + VERTICAL_GAP) - levelWidth) / 2
    
    level.forEach((nodeId, nodeIndex) => {
      result.push({
        id: nodeId,
        x: Math.round((START_X + levelIndex * (NODE_WIDTH + HORIZONTAL_GAP)) / 20) * 20,
        y: Math.round((START_Y + nodeIndex * (NODE_HEIGHT + VERTICAL_GAP)) / 20) * 20
      })
    })
  })
  
  return result
}

// 导入导出功能
const workflowExportData = computed(() => ({
  name: workflowName.value,
  description: '',
  nodes: nodes.value,
  connections: connections.value
}))

function handleImport() {
  importExportMode.value = 'import'
  showImportExportDialog.value = true
}

function handleExport() {
  importExportMode.value = 'export'
  showImportExportDialog.value = true
}

function handleImportData(data: any) {
  // 导入工作流数据
  workflowName.value = data.name || '导入的工作流'
  nodes.value = data.nodes || []
  connections.value = data.connections || []
  saveStatus.value = '未保存'
  
  // 清除高度缓存
  clearNodeHeightCache()
  
  alert('工作流导入成功！')
}

function handleExportComplete() {
  console.log('工作流已导出')
}

// 执行监控功能
function highlightNode(nodeId: string) {
  selectedNodeId.value = nodeId
  // 可以添加滚动到节点的逻辑
}

function handleExecutionComplete(result: any) {
  console.log('执行完成:', result)
  if (result.status === 'completed') {
    saveStatus.value = '执行完成'
  } else if (result.status === 'failed') {
    saveStatus.value = '执行失败'
  }
}

// 版本回滚处理
function handleVersionRollback(data: any) {
  // 回滚后重新加载工作流数据
  if (workflowId.value) {
    loadWorkflow(workflowId.value)
    $message?.success('版本回滚成功，已加载回滚后的数据')
  }
}

// API导入
import { getWorkflowDetail, saveWorkflowDesign } from '@/api/workflow'

// 消息提示
const $message = (window as any).$message

// 加载工作流数据
async function loadWorkflow(id: string) {
  try {
    const res = await getWorkflowDetail(id)
    if (res.code === 200 && res.data) {
      const data = res.data
      workflowName.value = data.name || '未命名工作流'
      nodes.value = data.nodes || []
      connections.value = data.connections || []
      saveStatus.value = '已加载'
      
      // 清除高度缓存
      clearNodeHeightCache()
    }
  } catch (error) {
    console.error('加载工作流失败:', error)
    $message?.error('加载工作流失败')
  }
}

// 保存工作流
async function handleSave() {
  if (!workflowId.value) {
    $message?.warning('请先选择或创建工作流')
    return
  }
  
  saveStatus.value = '保存中...'
  try {
    const res = await saveWorkflowDesign(workflowId.value, {
      nodes: nodes.value,
      connections: connections.value
    })
    
    if (res.code === 200) {
      saveStatus.value = '已保存'
      $message?.success('保存成功')
    } else {
      saveStatus.value = '保存失败'
      $message?.error(res.message || '保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    saveStatus.value = '保存失败'
    $message?.error('保存失败')
  }
}

// 生命周期
onMounted(() => {
  // 从路由获取工作流ID
  const id = route.query.id as string
  if (id) {
    workflowId.value = id
    loadWorkflow(id)
  }
})
</script>

<style scoped>
.simple-workflow-designer {
  position: relative;
  height: 100%;
  width: 100%;
  background: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

/* 工具栏 - 绝对定位在顶部 */
.designer-toolbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  z-index: 10;
  box-sizing: border-box;
}

.toolbar-left { display: flex; align-items: center; gap: 16px; }
.toolbar-center { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; align-items: center; gap: 12px; }

.workflow-title .title-input {
  border: none;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  background: transparent;
  padding: 8px 12px;
  border-radius: 6px;
  width: 200px;
}
.workflow-title .title-input:hover { background: #f5f5f5; }
.workflow-title .title-input:focus { outline: none; background: #e6f7ff; }

.tool-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f5f5f5;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.tool-btn:hover { background: #e6f7ff; color: #1890ff; }
.tool-btn.active { background: #1890ff; color: #fff; }

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: #e8e8e8;
  margin: 0 8px;
}

.zoom-level {
  font-size: 13px;
  color: #8c8c8c;
  min-width: 50px;
  text-align: center;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.action-btn.secondary { background: #f5f5f5; color: #595959; }
.action-btn.secondary:hover { background: #e8e8e8; }
.action-btn.primary { background: #1890ff; color: #fff; }
.action-btn.primary:hover { background: #40a9ff; }

/* 主内容区域 - 使用绝对定位确保高度 */
.designer-main {
  position: absolute;
  top: 56px; /* 工具栏高度 */
  bottom: 32px; /* 状态栏高度 */
  left: 0;
  right: 0;
  display: flex;
  overflow: hidden;
}

/* 节点面板 */
.node-panel {
  position: relative;
  width: 280px;
  height: 100%; /* 强制100%高度 */
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s;
  box-sizing: border-box;
}
.node-panel.collapsed { 
  width: 20px;
  border-right: none;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0; /* 防止被压缩 */
}
.panel-title { font-weight: 600; color: #262626; }
/* 收起状态下隐藏标题和header */
.node-panel.collapsed .panel-title,
.property-panel.collapsed .panel-title { display: none; }
.node-panel.collapsed .panel-header,
.property-panel.collapsed .panel-header { display: none; }

/* 边缘收起按钮 */
.edge-collapse-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 48px;
  border: none;
  background: #fff;
  cursor: pointer;
  font-size: 10px;
  color: #8c8c8c;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.edge-collapse-btn:hover {
  background: #1890ff;
  color: #fff;
}
.edge-collapse-btn.left {
  right: -10px;
  border-radius: 0 4px 4px 0;
}
.edge-collapse-btn.right {
  left: -10px;
  border-radius: 4px 0 0 4px;
}
/* 收起状态下调整按钮位置 */
.node-panel.collapsed .edge-collapse-btn.left {
  right: -10px;
}
.property-panel.collapsed .edge-collapse-btn.right {
  left: -10px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.search-box { margin-bottom: 16px; }
.search-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 14px;
}
.search-input:focus { outline: none; border-color: #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.2); }

.category-section { margin-bottom: 8px; }
.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.category-header:hover { background: #f0f0f0; }
.category-icon { font-size: 16px; }
.category-name { flex: 1; font-weight: 500; color: #262626; font-size: 14px; }
.category-toggle { font-size: 10px; color: #8c8c8c; }

.category-nodes { padding: 8px 0; }
.node-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  margin: 4px 0;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s;
}
.node-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24,144,255,0.15);
  transform: translateX(4px);
}
.node-item:active { cursor: grabbing; }

.node-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #fff;
}
.node-info { flex: 1; min-width: 0; }
.node-name { font-weight: 500; color: #262626; font-size: 14px; }
.node-desc { font-size: 12px; color: #8c8c8c; margin-top: 2px; }

/* 画布容器 */
.canvas-container {
  flex: 1;
  height: 100%; /* 强制100%高度 */
  min-width: 0;
  position: relative;
  overflow: hidden;
  background: #fafafa;
  box-sizing: border-box;
}

.canvas-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.canvas-content {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transform-origin: 0 0;
}

/* 工作流节点 */
.workflow-node {
  position: absolute;
  width: 160px;
  background: #fff;
  border-radius: 8px;
  border: 2px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  cursor: move;
  transition: all 0.2s;
  user-select: none;
}
.workflow-node:hover { 
  border-color: #d0d0d0;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12); 
}
.workflow-node.selected {
  border-color: #1890ff;
  box-shadow: 0 0 0 3px rgba(24,144,255,0.2), 0 4px 16px rgba(24,144,255,0.15);
}
.workflow-node.port-hover {
  border-color: #52c41a;
  box-shadow: 0 0 0 3px rgba(82,196,26,0.2);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px 6px 0 0;
  color: #fff;
}
.node-type-icon { font-size: 16px; }
.node-title {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-body {
  padding: 8px 12px;
  text-align: center;
}
.node-type-label {
  font-size: 11px;
  color: #8c8c8c;
}

/* 端口 - 放置在节点边缘 */
.port {
  position: absolute;
  width: 12px;
  height: 12px;
  background: #fff;
  border: 2px solid #d9d9d9;
  border-radius: 50%;
  cursor: crosshair;
  transition: all 0.15s ease;
  z-index: 10;
}
.port:hover {
  transform: scale(1.5);
  border-color: #1890ff;
  background: #1890ff;
  box-shadow: 0 0 0 4px rgba(24,144,255,0.2);
}
/* 输入端口 - 左侧中间 */
.input-port {
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
}
.input-port:hover {
  transform: translateY(-50%) scale(1.5);
}
/* 输出端口 - 右侧中间 */
.output-port {
  right: -8px;
  top: 50%;
  transform: translateY(-50%);
}
.output-port:hover {
  transform: translateY(-50%) scale(1.5);
}
/* 可连接状态 - 吸附效果 */
.port.can-connect {
  border-color: #52c41a;
  animation: port-pulse 1s ease infinite;
}
.port.can-connect:hover {
  background: #52c41a;
  border-color: #52c41a;
  transform: translateY(-50%) scale(1.8);
  box-shadow: 0 0 0 6px rgba(82,196,26,0.3);
}
@keyframes port-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(82,196,26,0.4); }
  50% { box-shadow: 0 0 0 6px rgba(82,196,26,0); }
}

/* 连接线 */
.connections-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: visible;
}
.connection-line {
  fill: none;
  stroke: #8c8c8c;
  stroke-width: 2;
  stroke-linecap: round;
  pointer-events: stroke;
  cursor: pointer;
  transition: stroke 0.2s, stroke-width 0.2s;
}
.connection-group {
  pointer-events: auto;
}
.connection-line:hover { 
  stroke: #1890ff; 
  stroke-width: 3; 
}
.connection-line.selected { 
  stroke: #1890ff; 
  stroke-width: 3; 
}
/* 临时连接线 - 拖拽时显示 */
.connection-line.temp {
  stroke: #1890ff;
  stroke-width: 2;
  stroke-dasharray: 8 4;
  pointer-events: none;
  animation: dash 0.5s linear infinite;
}
@keyframes dash {
  to { stroke-dashoffset: -12; }
}

/* 连接线删除按钮 */
.connection-delete-btn {
  cursor: pointer;
  pointer-events: auto;
}
.connection-delete-btn .delete-btn-bg {
  fill: #ff4d4f;
  transition: all 0.2s;
}
.connection-delete-btn:hover .delete-btn-bg {
  fill: #ff7875;
  r: 14;
}
.connection-delete-btn .delete-btn-icon {
  fill: #fff;
  font-size: 16px;
  font-weight: bold;
}

/* 空状态 */
.empty-canvas {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #8c8c8c;
  pointer-events: none;
}
.empty-icon { font-size: 64px; margin-bottom: 16px; opacity: 0.5; }
.empty-text { font-size: 16px; }

/* 属性面板 */
.property-panel {
  position: relative;
  width: 300px;
  height: 100%; /* 强制100%高度 */
  background: #fff;
  border-left: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s;
  box-sizing: border-box;
}
.property-panel.collapsed { 
  width: 20px;
  border-left: none;
}

.property-form { padding: 4px 0; }
.form-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.form-section:last-of-type {
  border-bottom: none;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}
.form-group {
  margin-bottom: 14px;
}
.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #595959;
  margin-bottom: 6px;
}
.form-group label .required {
  color: #ff4d4f;
  margin-left: 2px;
}
.form-input, .form-textarea, .form-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 13px;
  box-sizing: border-box;
}
.form-select {
  background: #fff;
  cursor: pointer;
}
.form-input:focus, .form-textarea:focus, .form-select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24,144,255,0.2);
}
.form-textarea.code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  background: #fafafa;
}
.form-value {
  padding: 8px 10px;
  background: #fafafa;
  border-radius: 6px;
  font-size: 13px;
  color: #595959;
}
.field-desc {
  font-size: 11px;
  color: #8c8c8c;
  margin-top: 4px;
}
.multiselect-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.checkbox-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  cursor: pointer;
}
.checkbox-item input {
  cursor: pointer;
}
.switch-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.switch-text {
  font-size: 13px;
  color: #595959;
}
.form-actions { margin-top: 20px; }
.btn-delete {
  width: 100%;
  padding: 10px;
  border: 1px solid #ff4d4f;
  background: #fff;
  color: #ff4d4f;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}
.btn-delete:hover { background: #ff4d4f; color: #fff; }

.no-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #8c8c8c;
}
.no-selection-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.5; }
.no-selection-text { font-size: 14px; }

/* 状态栏 - 绝对定位在底部 */
.designer-statusbar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #fff;
  border-top: 1px solid #e8e8e8;
  font-size: 12px;
  color: #8c8c8c;
  z-index: 10;
  box-sizing: border-box;
}
.status-left, .status-right { display: flex; align-items: center; gap: 16px; }
.status-item { display: flex; align-items: center; gap: 4px; }

.status-btn {
  padding: 2px 8px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}
.status-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}
.status-btn.active {
  border-color: #1890ff;
  background: #e6f7ff;
  color: #1890ff;
}

/* 滚动条 */
.panel-content::-webkit-scrollbar { width: 6px; }
.panel-content::-webkit-scrollbar-track { background: #f5f5f5; }
.panel-content::-webkit-scrollbar-thumb { background: #d9d9d9; border-radius: 3px; }
.panel-content::-webkit-scrollbar-thumb:hover { background: #bfbfbf; }
</style>
