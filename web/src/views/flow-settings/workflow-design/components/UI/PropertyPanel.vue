<template>
  <div class="property-panel" :class="{ collapsed: isCollapsed }">
    <!-- 面板头部 -->
    <div class="panel-header">
      <div class="panel-title">
        <span class="icon">⚙️</span>
        <span class="title-text">属性面板</span>
      </div>
      <button
        class="collapse-btn"
        :title="isCollapsed ? '展开面板' : '收起面板'"
        @click="toggleCollapse"
      >
        <span class="icon">{{ isCollapsed ? '◀' : '▶' }}</span>
      </button>
    </div>

    <!-- 标签页导航 -->
    <div v-show="!isCollapsed" class="tab-navigation">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        :title="tab.tooltip"
        @click="setActiveTab(tab.id)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>

    <!-- 面板内容 -->
    <div v-show="!isCollapsed" class="panel-content">
      <!-- 属性标签页 -->
      <div v-if="activeTab === 'properties'" class="tab-content properties-tab">
        <!-- 无选择状态 -->
        <div v-if="!selectedItem" class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-text">请选择节点或连接线</div>
          <div class="empty-hint">选择后可在此编辑属性</div>
        </div>

        <!-- 节点属性编辑 -->
        <div v-else-if="selectedItem.type === 'node'" class="node-properties">
          <div class="property-section">
            <div class="section-title">
              <span class="icon">{{ nodeTypeConfig?.icon || '📦' }}</span>
              <span>{{ nodeTypeConfig?.name || '节点' }}属性</span>
            </div>

            <!-- 动态属性表单 -->
            <div v-if="nodePropertySchema" class="dynamic-form-wrapper">
              <DynamicPropertyForm
                :schema="nodePropertySchema"
                :model-value="nodeProperties"
                @update:model-value="nodeProperties = $event"
                @change="handleDynamicPropertyChange"
              />
            </div>

            <!-- 基础信息 -->
            <div class="property-group">
              <div class="group-title">基础信息</div>

              <!-- 节点名称 -->
              <div v-if="!nodePropertySchema" class="property-item">
                <label class="property-label">名称</label>
                <input
                  v-model="editingNode.name"
                  type="text"
                  class="property-input"
                  placeholder="请输入节点名称"
                  @input="handleNodeChange"
                />
              </div>

              <!-- 节点描述 -->
              <div class="property-item">
                <label class="property-label">描述</label>
                <textarea
                  v-model="editingNode.description"
                  class="property-textarea"
                  placeholder="请输入节点描述"
                  rows="3"
                  @input="handleNodeChange"
                ></textarea>
              </div>

              <!-- 节点状态 -->
              <div class="property-item">
                <label class="property-label">状态</label>
                <select
                  v-model="editingNode.status"
                  class="property-select"
                  @change="handleNodeChange"
                >
                  <option value="idle">空闲</option>
                  <option value="running">运行中</option>
                  <option value="success">成功</option>
                  <option value="error">错误</option>
                  <option value="warning">警告</option>
                </select>
              </div>
            </div>

            <!-- 位置信息 -->
            <div class="property-group">
              <div class="group-title">位置信息</div>

              <div class="property-row">
                <div class="property-item half">
                  <label class="property-label">X 坐标</label>
                  <input
                    v-model.number="editingNode.position.x"
                    type="number"
                    class="property-input"
                    @input="handleNodeChange"
                  />
                </div>

                <div class="property-item half">
                  <label class="property-label">Y 坐标</label>
                  <input
                    v-model.number="editingNode.position.y"
                    type="number"
                    class="property-input"
                    @input="handleNodeChange"
                  />
                </div>
              </div>
            </div>

            <!-- 节点配置 -->
            <div v-if="nodeTypeConfig?.properties && !nodePropertySchema" class="property-group">
              <div class="group-title">节点配置</div>

              <div
                v-for="(propConfig, propKey) in nodeTypeConfig.properties"
                :key="propKey"
                class="property-item"
              >
                <label class="property-label">
                  {{ propConfig.label || propKey }}
                  <span v-if="propConfig.required" class="required">*</span>
                </label>

                <!-- 文本输入 -->
                <input
                  v-if="propConfig.type === 'string'"
                  v-model="editingNode.properties[propKey]"
                  type="text"
                  class="property-input"
                  :placeholder="propConfig.placeholder"
                  @input="handleNodeChange"
                />

                <!-- 数字输入 -->
                <input
                  v-else-if="propConfig.type === 'number'"
                  v-model.number="editingNode.properties[propKey]"
                  type="number"
                  class="property-input"
                  :min="propConfig.min"
                  :max="propConfig.max"
                  :step="propConfig.step"
                  @input="handleNodeChange"
                />

                <!-- 布尔选择 -->
                <label v-else-if="propConfig.type === 'boolean'" class="property-checkbox">
                  <input
                    v-model="editingNode.properties[propKey]"
                    type="checkbox"
                    @change="handleNodeChange"
                  />
                  <span class="checkbox-label">{{ propConfig.label || '启用' }}</span>
                </label>

                <!-- 选择框 -->
                <select
                  v-else-if="propConfig.type === 'select'"
                  v-model="editingNode.properties[propKey]"
                  class="property-select"
                  @change="handleNodeChange"
                >
                  <option
                    v-for="option in propConfig.options"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>

                <!-- 多行文本 -->
                <textarea
                  v-else-if="propConfig.type === 'textarea'"
                  v-model="editingNode.properties[propKey]"
                  class="property-textarea"
                  :placeholder="propConfig.placeholder"
                  :rows="propConfig.rows || 3"
                  @input="handleNodeChange"
                ></textarea>

                <!-- 颜色选择 -->
                <input
                  v-else-if="propConfig.type === 'color'"
                  v-model="editingNode.properties[propKey]"
                  type="color"
                  class="property-color"
                  @input="handleNodeChange"
                />

                <!-- 文件选择 -->
                <input
                  v-else-if="propConfig.type === 'file'"
                  type="file"
                  class="property-file"
                  :accept="propConfig.accept"
                  @change="handleFileChange($event, propKey)"
                />

                <!-- 默认文本输入 -->
                <input
                  v-else
                  v-model="editingNode.properties[propKey]"
                  type="text"
                  class="property-input"
                  @input="handleNodeChange"
                />

                <!-- 属性描述 -->
                <div v-if="propConfig.description" class="property-description">
                  {{ propConfig.description }}
                </div>
              </div>
            </div>

            <!-- 连接点配置 -->
            <div class="property-group">
              <div class="group-title">连接点</div>

              <!-- 输入连接点 -->
              <div class="connector-section">
                <div class="connector-title">输入</div>
                <div
                  v-for="(input, index) in editingNode.inputs"
                  :key="index"
                  class="connector-item"
                >
                  <input
                    v-model="input.name"
                    type="text"
                    class="property-input small"
                    placeholder="连接点名称"
                    @input="handleNodeChange"
                  />
                  <select
                    v-model="input.type"
                    class="property-select small"
                    @change="handleNodeChange"
                  >
                    <option value="any">任意</option>
                    <option value="string">字符串</option>
                    <option value="number">数字</option>
                    <option value="boolean">布尔</option>
                    <option value="object">对象</option>
                    <option value="array">数组</option>
                  </select>
                  <button class="remove-btn" title="删除输入" @click="removeInput(index)">✕</button>
                </div>
                <button class="add-btn" @click="addInput">+ 添加输入</button>
              </div>

              <!-- 输出连接点 -->
              <div class="connector-section">
                <div class="connector-title">输出</div>
                <div
                  v-for="(output, index) in editingNode.outputs"
                  :key="index"
                  class="connector-item"
                >
                  <input
                    v-model="output.name"
                    type="text"
                    class="property-input small"
                    placeholder="连接点名称"
                    @input="handleNodeChange"
                  />
                  <select
                    v-model="output.type"
                    class="property-select small"
                    @change="handleNodeChange"
                  >
                    <option value="any">任意</option>
                    <option value="string">字符串</option>
                    <option value="number">数字</option>
                    <option value="boolean">布尔</option>
                    <option value="object">对象</option>
                    <option value="array">数组</option>
                  </select>
                  <button class="remove-btn" title="删除输出" @click="removeOutput(index)">
                    ✕
                  </button>
                </div>
                <button class="add-btn" @click="addOutput">+ 添加输出</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 连接线属性编辑 -->
        <div v-else-if="selectedItem.type === 'connection'" class="connection-properties">
          <div class="property-section">
            <div class="section-title">
              <span class="icon">🔗</span>
              <span>连接线属性</span>
            </div>

            <!-- 基础信息 -->
            <div class="property-group">
              <div class="group-title">基础信息</div>

              <!-- 连接标签 -->
              <div class="property-item">
                <label class="property-label">标签</label>
                <input
                  v-model="editingConnection.label"
                  type="text"
                  class="property-input"
                  placeholder="请输入连接标签"
                  @input="handleConnectionChange"
                />
              </div>

              <!-- 连接条件 -->
              <div class="property-item">
                <label class="property-label">条件</label>
                <input
                  v-model="editingConnection.condition"
                  type="text"
                  class="property-input"
                  placeholder="请输入连接条件"
                  @input="handleConnectionChange"
                />
              </div>

              <!-- 连接类型 -->
              <div class="property-item">
                <label class="property-label">类型</label>
                <select
                  v-model="editingConnection.type"
                  class="property-select"
                  @change="handleConnectionChange"
                >
                  <option value="default">默认</option>
                  <option value="success">成功</option>
                  <option value="error">错误</option>
                  <option value="conditional">条件</option>
                </select>
              </div>
            </div>

            <!-- 连接信息 -->
            <div class="property-group">
              <div class="group-title">连接信息</div>

              <div class="connection-info">
                <div class="info-item">
                  <span class="info-label">源节点:</span>
                  <span class="info-value">{{ sourceNodeName }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">源输出:</span>
                  <span class="info-value">{{ editingConnection.sourceOutput }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">目标节点:</span>
                  <span class="info-value">{{ targetNodeName }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">目标输入:</span>
                  <span class="info-value">{{ editingConnection.targetInput }}</span>
                </div>
              </div>
            </div>

            <!-- 样式配置 -->
            <div class="property-group">
              <div class="group-title">样式配置</div>

              <!-- 线条颜色 -->
              <div class="property-item">
                <label class="property-label">颜色</label>
                <input
                  v-model="editingConnection.style.color"
                  type="color"
                  class="property-color"
                  @input="handleConnectionChange"
                />
              </div>

              <!-- 线条宽度 -->
              <div class="property-item">
                <label class="property-label">宽度</label>
                <input
                  v-model.number="editingConnection.style.width"
                  type="number"
                  class="property-input"
                  min="1"
                  max="10"
                  @input="handleConnectionChange"
                />
              </div>

              <!-- 线条样式 -->
              <div class="property-item">
                <label class="property-label">样式</label>
                <select
                  v-model="editingConnection.style.dashArray"
                  class="property-select"
                  @change="handleConnectionChange"
                >
                  <option value="">实线</option>
                  <option value="5,5">虚线</option>
                  <option value="2,3">点线</option>
                  <option value="5,2,2,2">点划线</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 多选状态 -->
      <div v-else-if="selectedItem.type === 'multiple'" class="multiple-selection">
        <div class="property-section">
          <div class="section-title">
            <span class="icon">📦</span>
            <span>批量操作</span>
          </div>

          <div class="selection-info">
            <div class="info-item">
              <span class="info-label">选中项目:</span>
              <span class="info-value">{{ selectedItem.count }} 个</span>
            </div>
            <div class="info-item">
              <span class="info-label">节点:</span>
              <span class="info-value">{{ selectedItem.nodes }} 个</span>
            </div>
            <div class="info-item">
              <span class="info-label">连接:</span>
              <span class="info-value">{{ selectedItem.connections }} 个</span>
            </div>
          </div>

          <div class="batch-actions">
            <button class="action-btn" @click="handleBatchAlign('left')">
              <span class="icon">⫷</span>
              <span>左对齐</span>
            </button>
            <button class="action-btn" @click="handleBatchAlign('center')">
              <span class="icon">⫸</span>
              <span>居中对齐</span>
            </button>
            <button class="action-btn" @click="handleBatchAlign('right')">
              <span class="icon">⫸</span>
              <span>右对齐</span>
            </button>
            <button class="action-btn" @click="handleBatchDistribute('horizontal')">
              <span class="icon">↔</span>
              <span>水平分布</span>
            </button>
            <button class="action-btn" @click="handleBatchDistribute('vertical')">
              <span class="icon">↕</span>
              <span>垂直分布</span>
            </button>
            <button class="action-btn danger" @click="handleBatchDelete">
              <span class="icon">🗑️</span>
              <span>批量删除</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 信息标签页 -->
      <div v-else-if="activeTab === 'info'" class="tab-content info-tab">
        <div class="info-section">
          <div class="section-title">
            <span class="icon">ℹ️</span>
            <span>节点信息</span>
          </div>

          <div v-if="selectedItem?.type === 'node'" class="node-info">
            <div class="info-item">
              <span class="info-label">节点类型:</span>
              <span class="info-value">{{ nodeTypeConfig?.name || '未知' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">节点ID:</span>
              <span class="info-value">{{ selectedItem.data.id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">创建时间:</span>
              <span class="info-value">{{ formatDate(selectedItem.data.createdAt) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">输入数量:</span>
              <span class="info-value">{{ selectedItem.data.inputs?.length || 0 }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">输出数量:</span>
              <span class="info-value">{{ selectedItem.data.outputs?.length || 0 }}</span>
            </div>

            <div v-if="nodeTypeConfig?.description" class="node-description">
              <div class="description-title">节点说明</div>
              <div class="description-content">{{ nodeTypeConfig.description }}</div>
            </div>
          </div>

          <div v-else-if="selectedItem?.type === 'connection'" class="connection-info">
            <div class="info-item">
              <span class="info-label">连接ID:</span>
              <span class="info-value">{{ selectedItem.data.id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">源节点:</span>
              <span class="info-value">{{ sourceNodeName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">目标节点:</span>
              <span class="info-value">{{ targetNodeName }}</span>
            </div>
          </div>

          <div v-else class="empty-info">
            <div class="empty-icon">ℹ️</div>
            <div class="empty-text">请选择节点或连接线</div>
            <div class="empty-hint">查看详细信息</div>
          </div>
        </div>
      </div>

      <!-- 调试标签页 -->
      <div v-else-if="activeTab === 'debug'" class="tab-content debug-tab">
        <div class="debug-section">
          <div class="section-title">
            <span class="icon">🐛</span>
            <span>调试信息</span>
          </div>

          <div class="debug-controls">
            <button class="debug-btn" @click="clearDebugLog">
              <span class="icon">🗑️</span>
              <span>清空日志</span>
            </button>
            <button class="debug-btn" @click="exportDebugLog">
              <span class="icon">📤</span>
              <span>导出日志</span>
            </button>
          </div>

          <div class="debug-log">
            <div v-for="(log, index) in debugLogs" :key="index" class="log-item" :class="log.level">
              <div class="log-time">{{ formatTime(log.timestamp) }}</div>
              <div class="log-level">{{ log.level.toUpperCase() }}</div>
              <div class="log-message">{{ log.message }}</div>
            </div>

            <div v-if="debugLogs.length === 0" class="empty-log">
              <div class="empty-icon">📝</div>
              <div class="empty-text">暂无调试信息</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 小地图标签页 -->
      <div v-else-if="activeTab === 'minimap'" class="tab-content minimap-tab">
        <div class="minimap-section">
          <div class="section-title">
            <span class="icon">🗺️</span>
            <span>小地图</span>
          </div>

          <div class="minimap-container">
            <div class="minimap-placeholder">
              <div class="placeholder-icon">🗺️</div>
              <div class="placeholder-text">小地图功能</div>
              <div class="placeholder-hint">即将推出</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, inject } from 'vue'
import { NODE_TYPES } from '../../utils/nodeTypes'
import DynamicPropertyForm from './DynamicPropertyForm.vue'
import { getNodePropertySchema, type NodePropertySchema } from '../../utils/nodePropertySchemas'

// 简单的防抖函数实现
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Props
const props = defineProps({
  selectedItem: {
    type: Object,
    default: null,
  },
})

// 事件定义
const emit = defineEmits([
  'update-node',
  'update-connection',
  'batch-align',
  'batch-distribute',
  'batch-delete',
  'toggle-collapse',
])

// 注入的依赖
const workflowStore = inject('workflowStore')

// 响应式数据
const isCollapsed = ref(false)
const editingNode = ref(null)
const editingConnection = ref(null)
const activeTab = ref('properties')
const debugLogs = ref([])

// 标签页配置
const tabs = ref([
  {
    id: 'properties',
    label: '属性',
    icon: '⚙️',
    tooltip: '编辑节点和连接属性',
  },
  {
    id: 'info',
    label: '信息',
    icon: 'ℹ️',
    tooltip: '查看节点详细信息',
  },
  {
    id: 'debug',
    label: '调试',
    icon: '🐛',
    tooltip: '查看调试日志',
  },
  {
    id: 'minimap',
    label: '地图',
    icon: '🗺️',
    tooltip: '工作流小地图',
  },
])

// 计算属性
const nodeTypeConfig = computed(() => {
  if (!editingNode.value) return null
  return NODE_TYPES[editingNode.value.type] || null
})

// 动态表单模式配置
const nodePropertySchema = computed<NodePropertySchema | null>(() => {
  if (!editingNode.value) return null
  return getNodePropertySchema(editingNode.value.type)
})

// 节点属性数据
const nodeProperties = computed({
  get: () => {
    if (!editingNode.value) return {}
    return {
      name: editingNode.value.name,
      description: editingNode.value.description,
      ...editingNode.value.properties
    }
  },
  set: (value) => {
    if (editingNode.value) {
      const { name, description, ...properties } = value
      editingNode.value.name = name || editingNode.value.name
      editingNode.value.description = description || ''
      editingNode.value.properties = { ...editingNode.value.properties, ...properties }
    }
  }
})

// 处理动态表单属性变化
function handleDynamicPropertyChange(field: string, value: any) {
  if (!editingNode.value) return
  
  if (field === 'name') {
    editingNode.value.name = value
  } else if (field === 'description') {
    editingNode.value.description = value
  } else {
    if (!editingNode.value.properties) {
      editingNode.value.properties = {}
    }
    editingNode.value.properties[field] = value
  }
  
  handleNodeChange()
}

const sourceNodeName = computed(() => {
  if (!editingConnection.value) return ''
  const node = workflowStore.getNode(editingConnection.value.sourceNodeId)
  return node?.name || '未知节点'
})

const targetNodeName = computed(() => {
  if (!editingConnection.value) return ''
  const node = workflowStore.getNode(editingConnection.value.targetNodeId)
  return node?.name || '未知节点'
})

// 监听选中项变化
watch(
  () => props.selectedItem,
  (newItem) => {
    if (newItem?.type === 'node') {
      editingNode.value = JSON.parse(JSON.stringify(newItem.data))
      editingConnection.value = null
    } else if (newItem?.type === 'connection') {
      editingConnection.value = JSON.parse(JSON.stringify(newItem.data))
      editingNode.value = null
    } else {
      editingNode.value = null
      editingConnection.value = null
    }
  },
  { immediate: true }
)

// 防抖的更新函数
const debouncedUpdateNode = debounce((node) => {
  emit('update-node', node)
}, 300)

const debouncedUpdateConnection = debounce((connection) => {
  emit('update-connection', connection)
}, 300)

// 方法
function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function handleNodeChange() {
  if (editingNode.value) {
    debouncedUpdateNode(editingNode.value)
  }
}

function handleConnectionChange() {
  if (editingConnection.value) {
    debouncedUpdateConnection(editingConnection.value)
  }
}

function handleFileChange(event, propKey) {
  const file = event.target.files[0]
  if (file && editingNode.value) {
    // 这里可以处理文件上传逻辑
    editingNode.value.properties[propKey] = file.name
    handleNodeChange()
  }
}

function addInput() {
  if (editingNode.value) {
    editingNode.value.inputs.push({
      name: `input_${editingNode.value.inputs.length + 1}`,
      type: 'any',
      required: false,
    })
    handleNodeChange()
  }
}

function removeInput(index) {
  if (editingNode.value) {
    editingNode.value.inputs.splice(index, 1)
    handleNodeChange()
  }
}

function addOutput() {
  if (editingNode.value) {
    editingNode.value.outputs.push({
      name: `output_${editingNode.value.outputs.length + 1}`,
      type: 'any',
    })
    handleNodeChange()
  }
}

function removeOutput(index) {
  if (editingNode.value) {
    editingNode.value.outputs.splice(index, 1)
    handleNodeChange()
  }
}

function handleBatchAlign(direction) {
  emit('batch-align', direction)
}

function handleBatchDistribute(direction) {
  emit('batch-distribute', direction)
}

function handleBatchDelete() {
  emit('batch-delete')
}

// 标签页相关方法
function setActiveTab(tabId) {
  activeTab.value = tabId
}

// 格式化日期
function formatDate(timestamp) {
  if (!timestamp) return '未知'
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString('zh-CN')
}

// 调试日志相关方法
function clearDebugLog() {
  debugLogs.value = []
}

function exportDebugLog() {
  const logText = debugLogs.value
    .map((log) => `[${formatTime(log.timestamp)}] ${log.level.toUpperCase()}: ${log.message}`)
    .join('\n')

  const blob = new Blob([logText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflow-debug-${Date.now()}.log`
  a.click()
  URL.revokeObjectURL(url)
}

// 添加调试日志
function addDebugLog(level, message) {
  debugLogs.value.unshift({
    timestamp: Date.now(),
    level,
    message,
  })

  // 限制日志数量
  if (debugLogs.value.length > 100) {
    debugLogs.value = debugLogs.value.slice(0, 100)
  }
}

// 暴露方法给父组件
defineExpose({
  addDebugLog,
})
</script>

<style scoped>
.property-panel {
  display: flex;
  flex-direction: column;
  width: 300px;
  height: 100%;
  background: #ffffff;
  border-left: 1px solid #e8e8e8;
  transition: width 0.3s ease;
}

.property-panel.collapsed {
  width: 40px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #262626;
}

.collapsed .title-text {
  display: none;
}

.collapse-btn {
  padding: 4px;
  border: none;
  background: none;
  cursor: pointer;
  color: #8c8c8c;
  transition: color 0.15s ease;
}

.collapse-btn:hover {
  color: #1890ff;
}

.tab-navigation {
  display: flex;
  background: #f5f5f5;
  border-bottom: 1px solid #e8e8e8;
  overflow-x: auto;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  background: none;
  cursor: pointer;
  color: #8c8c8c;
  font-size: 12px;
  white-space: nowrap;
  transition: all 0.15s ease;
  border-bottom: 2px solid transparent;
}

.tab-btn:hover {
  color: #1890ff;
  background: #e6f7ff;
}

.tab-btn.active {
  color: #1890ff;
  background: #ffffff;
  border-bottom-color: #1890ff;
}

.tab-icon {
  font-size: 14px;
}

.tab-label {
  font-weight: 500;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
}

.tab-content {
  padding: 16px;
  height: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  text-align: center;
  color: #8c8c8c;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
}

.property-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  padding-bottom: 8px;
  border-bottom: 2px solid #1890ff;
}

.property-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  color: #595959;
  margin-bottom: 8px;
}

.info-section,
.debug-section,
.minimap-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.node-info,
.connection-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-label {
  font-size: 13px;
  color: #8c8c8c;
  font-weight: 500;
}

.info-value {
  font-size: 13px;
  color: #262626;
  font-weight: 500;
  text-align: right;
  max-width: 60%;
  word-break: break-all;
}

.node-description {
  margin-top: 16px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
}

.description-title {
  font-size: 13px;
  font-weight: 600;
  color: #595959;
  margin-bottom: 8px;
}

.description-content {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.5;
}

.empty-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  text-align: center;
  color: #8c8c8c;
}

.debug-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.debug-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  background: #ffffff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #595959;
  transition: all 0.15s ease;
}

.debug-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.debug-log {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background: #fafafa;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.log-item:last-child {
  border-bottom: none;
}

.log-item.info {
  background: #f6ffed;
  border-left: 3px solid #52c41a;
}

.log-item.warn {
  background: #fffbe6;
  border-left: 3px solid #faad14;
}

.log-item.error {
  background: #fff2f0;
  border-left: 3px solid #ff4d4f;
}

.log-time {
  color: #8c8c8c;
  white-space: nowrap;
  min-width: 80px;
}

.log-level {
  font-weight: 600;
  min-width: 50px;
}

.log-level.INFO {
  color: #52c41a;
}

.log-level.WARN {
  color: #faad14;
}

.log-level.ERROR {
  color: #ff4d4f;
}

.log-message {
  flex: 1;
  color: #262626;
  word-break: break-word;
}

.empty-log {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 120px;
  color: #8c8c8c;
}

.minimap-container {
  height: 300px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.minimap-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  color: #8c8c8c;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.placeholder-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.placeholder-hint {
  font-size: 12px;
}

.property-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.property-item.half {
  flex: 1;
}

.property-row {
  display: flex;
  gap: 12px;
}

.property-label {
  font-size: 13px;
  font-weight: 500;
  color: #262626;
}

.required {
  color: #ff4d4f;
  margin-left: 2px;
}

.property-input,
.property-select,
.property-textarea {
  padding: 6px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  transition: border-color 0.15s ease;
}

.property-input:focus,
.property-select:focus,
.property-textarea:focus {
  outline: none;
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.property-input.small,
.property-select.small {
  padding: 4px 6px;
  font-size: 12px;
}

.property-textarea {
  resize: vertical;
  min-height: 60px;
}

.property-color {
  width: 40px;
  height: 32px;
  padding: 2px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
}

.property-file {
  font-size: 12px;
}

.property-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label {
  font-size: 13px;
  color: #262626;
}

.property-description {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.connector-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.connector-title {
  font-size: 13px;
  font-weight: 500;
  color: #595959;
}

.connector-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.remove-btn {
  padding: 2px 6px;
  border: 1px solid #ff4d4f;
  border-radius: 3px;
  background: #fff2f0;
  color: #ff4d4f;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.remove-btn:hover {
  background: #ff4d4f;
  color: white;
}

.add-btn {
  padding: 6px 12px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  background: #fafafa;
  color: #595959;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.add-btn:hover {
  border-color: #40a9ff;
  color: #1890ff;
  background: #f6ffed;
}

.connection-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 12px;
  color: #8c8c8c;
}

.info-value {
  font-size: 12px;
  font-weight: 500;
  color: #262626;
}

.selection-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #f6ffed;
  border-radius: 6px;
  margin-bottom: 16px;
}

.batch-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: #ffffff;
  color: #262626;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  border-color: #40a9ff;
  color: #1890ff;
  background: #f6ffed;
}

.action-btn.danger {
  border-color: #ff4d4f;
  color: #ff4d4f;
}

.action-btn.danger:hover {
  background: #ff4d4f;
  color: white;
}

/* 滚动条样式 */
.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.panel-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
