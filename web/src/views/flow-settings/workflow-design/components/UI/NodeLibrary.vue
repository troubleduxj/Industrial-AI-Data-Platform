<template>
  <div class="node-library" :class="{ collapsed: isCollapsed }">
    <!-- 面板头部 -->
    <div class="library-header">
      <div class="library-title">
        <span class="icon">📚</span>
        <span class="title-text">节点库</span>
      </div>
      <button
        class="collapse-btn"
        :title="isCollapsed ? '展开面板' : '收起面板'"
        @click="toggleCollapse"
      >
        <span class="icon">{{ isCollapsed ? '◀' : '▶' }}</span>
      </button>
    </div>

    <!-- 搜索栏 -->
    <div v-show="!isCollapsed" class="search-section">
      <div class="search-input-wrapper">
        <span class="search-icon">🔍</span>
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="搜索节点..."
          @input="emit('search', searchQuery)"
        />
        <button v-if="searchQuery" class="clear-btn" title="清除搜索" @click="clearSearch">
          ✕
        </button>
      </div>

      <!-- 分类筛选 -->
      <div class="category-filter">
        <button
          v-for="category in categories"
          :key="category.key"
          class="category-btn"
          :class="{ active: selectedCategory === category.key }"
          :title="category.description"
          @click="setCategory(category.key)"
        >
          <span class="icon">{{ category.icon }}</span>
          <span class="label">{{ category.name }}</span>
        </button>
      </div>
    </div>

    <!-- 节点列表 -->
    <div v-show="!isCollapsed" class="node-list">
      <!-- 分组显示 -->
      <div v-for="group in filteredGroups" :key="group.category" class="node-group">
        <div class="group-header">
          <span class="group-icon">{{ group.icon }}</span>
          <span class="group-title">{{ group.name }}</span>
          <span class="group-count">({{ group.nodes.length }})</span>
          <button
            class="group-toggle"
            :title="collapsedGroups.has(group.category) ? '展开分组' : '收起分组'"
            @click="toggleGroup(group.category)"
          >
            {{ collapsedGroups.has(group.category) ? '▶' : '▼' }}
          </button>
        </div>

        <div v-show="!collapsedGroups.has(group.category)" class="group-content">
          <div
            v-for="node in group.nodes"
            :key="node.type"
            class="node-item"
            :class="{
              dragging: draggedNode === node.type,
              disabled: node.disabled,
            }"
            :draggable="!node.disabled"
            :title="getNodeTooltip(node)"
            @dragstart="handleDragStart($event, node)"
            @dragend="handleDragEnd"
            @click="handleNodeClick(node)"
            @dblclick="handleNodeDoubleClick(node)"
          >
            <div class="node-icon">
              <span class="icon">{{ node.icon }}</span>
              <div v-if="node.badge" class="node-badge">{{ node.badge }}</div>
            </div>

            <div class="node-info">
              <div class="node-name">{{ node.name }}</div>
              <div class="node-description">{{ node.description }}</div>

              <!-- 节点标签 -->
              <div v-if="node.tags && node.tags.length > 0" class="node-tags">
                <span v-for="tag in node.tags.slice(0, 3)" :key="tag" class="node-tag">
                  {{ tag }}
                </span>
                <span v-if="node.tags.length > 3" class="more-tags">
                  +{{ node.tags.length - 3 }}
                </span>
              </div>
            </div>

            <!-- 节点操作 -->
            <div class="node-actions">
              <button class="action-btn" title="查看详情" @click.stop="showNodeInfo(node)">
                ℹ️
              </button>

              <button
                v-if="node.configurable"
                class="action-btn"
                title="配置节点"
                @click.stop="configureNode(node)"
              >
                ⚙️
              </button>

              <button
                v-if="favoriteNodes.has(node.type)"
                class="action-btn favorite active"
                title="取消收藏"
                @click.stop="toggleFavorite(node)"
              >
                ⭐
              </button>
              <button
                v-else
                class="action-btn favorite"
                title="添加收藏"
                @click.stop="toggleFavorite(node)"
              >
                ☆
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredGroups.length === 0" class="empty-state">
        <div class="empty-icon">🔍</div>
        <div class="empty-text">未找到匹配的节点</div>
        <div class="empty-hint">尝试调整搜索条件或分类筛选</div>
      </div>
    </div>

    <!-- 拖拽预览 -->
    <div v-if="draggedNode" class="drag-preview" :style="dragPreviewStyle">
      <div class="preview-node">
        <span class="preview-icon">{{ draggedNodeData?.icon }}</span>
        <span class="preview-name">{{ draggedNodeData?.name }}</span>
      </div>
    </div>
  </div>

  <!-- 节点详情弹窗 -->
  <div v-if="showInfoModal" class="modal-overlay" @click="closeInfoModal">
    <div class="info-modal" @click.stop>
      <div class="modal-header">
        <div class="modal-title">
          <span class="icon">{{ selectedNodeInfo?.icon }}</span>
          <span>{{ selectedNodeInfo?.name }}</span>
        </div>
        <button class="close-btn" @click="closeInfoModal">✕</button>
      </div>

      <div class="modal-content">
        <div class="info-section">
          <h4>描述</h4>
          <p>{{ selectedNodeInfo?.description }}</p>
        </div>

        <div v-if="selectedNodeInfo?.inputs?.length > 0" class="info-section">
          <h4>输入参数</h4>
          <div class="param-list">
            <div v-for="input in selectedNodeInfo.inputs" :key="input.name" class="param-item">
              <span class="param-name">{{ input.name }}</span>
              <span class="param-type">{{ input.type }}</span>
              <span v-if="input.required" class="param-required">必需</span>
            </div>
          </div>
        </div>

        <div v-if="selectedNodeInfo?.outputs?.length > 0" class="info-section">
          <h4>输出参数</h4>
          <div class="param-list">
            <div v-for="output in selectedNodeInfo.outputs" :key="output.name" class="param-item">
              <span class="param-name">{{ output.name }}</span>
              <span class="param-type">{{ output.type }}</span>
            </div>
          </div>
        </div>

        <div v-if="selectedNodeInfo?.properties" class="info-section">
          <h4>配置属性</h4>
          <div class="property-list">
            <div
              v-for="(prop, key) in selectedNodeInfo.properties"
              :key="key"
              class="property-item"
            >
              <span class="property-name">{{ prop.label || key }}</span>
              <span class="property-type">{{ prop.type }}</span>
              <span v-if="prop.required" class="property-required">必需</span>
              <div v-if="prop.description" class="property-desc">
                {{ prop.description }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="selectedNodeInfo?.examples" class="info-section">
          <h4>使用示例</h4>
          <div class="example-list">
            <div
              v-for="(example, index) in selectedNodeInfo.examples"
              :key="index"
              class="example-item"
            >
              <div class="example-title">{{ example.title }}</div>
              <div class="example-desc">{{ example.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="secondary btn" @click="closeInfoModal">关闭</button>
        <button class="btn primary" @click="addNodeFromModal">
          <span class="icon">➕</span>
          <span>添加到画布</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NODE_TYPES } from '../../utils/nodeTypes'

// Props
const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false,
  },
  searchQuery: {
    type: String,
    default: '',
  },
  selectedCategory: {
    type: String,
    default: 'all',
  },
  favoriteNodes: {
    type: Set,
    default: () => new Set(),
  },
})

// Emits
const emit = defineEmits([
  'node-drag-start',
  'node-drag-end',
  'add-node',
  'configure-node',
  'toggle-collapse',
  'search',
  'categoryChange',
  'nodeClick',
  'nodeDoubleClick',
  'toggleFavorite',
])

// 响应式数据
const isCollapsed = ref(props.collapsed)
const searchQuery = ref(props.searchQuery)
const selectedCategory = ref(props.selectedCategory)
const collapsedGroups = ref(new Set())
const favoriteNodes = ref(props.favoriteNodes)
const draggedNode = ref(null)
const draggedNodeData = ref(null)
const dragPreviewStyle = ref({})
const showInfoModal = ref(false)
const selectedNodeInfo = ref(null)

// 分类配置
const categories = [
  { key: 'all', name: '全部', icon: '📦', description: '显示所有节点' },
  { key: 'input', name: '输入', icon: '📥', description: '数据输入节点' },
  { key: 'process', name: '处理', icon: '⚙️', description: '数据处理节点' },
  { key: 'output', name: '输出', icon: '📤', description: '数据输出节点' },
  { key: 'control', name: '控制', icon: '🎛️', description: '流程控制节点' },
  { key: 'logic', name: '逻辑', icon: '🧠', description: '逻辑判断节点' },
  { key: 'integration', name: '集成', icon: '🔌', description: '外部系统集成' },
  { key: 'device', name: '设备', icon: '🏭', description: '设备相关节点' },
  { key: 'alarm', name: '报警', icon: '🚨', description: '报警相关节点' },
  { key: 'notification', name: '通知', icon: '📢', description: '消息通知节点' },
  { key: 'utility', name: '工具', icon: '🔧', description: '实用工具节点' },
  { key: 'favorite', name: '收藏', icon: '⭐', description: '收藏的节点' },
]

// 计算属性
const nodeGroups = computed(() => {
  const groups = new Map()

  Object.values(NODE_TYPES).forEach((nodeType) => {
    const category = nodeType.category || 'utility'
    if (!groups.has(category)) {
      const categoryInfo = categories.find((c) => c.key === category) || {
        key: category,
        name: category,
        icon: '📦',
      }
      groups.set(category, {
        category,
        name: categoryInfo.name,
        icon: categoryInfo.icon,
        nodes: [],
      })
    }
    groups.get(category).nodes.push(nodeType)
  })

  return Array.from(groups.values())
})

const filteredGroups = computed(() => {
  let groups = nodeGroups.value

  // 分类筛选
  if (selectedCategory.value === 'favorite') {
    groups = groups
      .map((group) => ({
        ...group,
        nodes: group.nodes.filter((node) => favoriteNodes.value.has(node.type)),
      }))
      .filter((group) => group.nodes.length > 0)
  } else if (selectedCategory.value !== 'all') {
    groups = groups.filter((group) => group.category === selectedCategory.value)
  }

  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    groups = groups
      .map((group) => ({
        ...group,
        nodes: group.nodes.filter(
          (node) =>
            node.name.toLowerCase().includes(query) ||
            node.description.toLowerCase().includes(query) ||
            (node.tags && node.tags.some((tag) => tag.toLowerCase().includes(query)))
        ),
      }))
      .filter((group) => group.nodes.length > 0)
  }

  return groups
})

// 方法
function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
  emit('toggle-collapse', isCollapsed.value)
}

function clearSearch() {
  searchQuery.value = ''
  emit('search', '')
}

function setCategory(category) {
  selectedCategory.value = category
  emit('categoryChange', category)
}

function toggleGroup(category) {
  if (collapsedGroups.value.has(category)) {
    collapsedGroups.value.delete(category)
  } else {
    collapsedGroups.value.add(category)
  }
}

function toggleFavorite(node) {
  emit('toggleFavorite', node)
}

function handleDragStart(event, node) {
  console.log('NodeLibrary: 拖拽开始 - 节点数据:', node)
  console.log('节点是否禁用:', node.disabled)

  if (node.disabled) {
    console.log('节点被禁用，阻止拖拽')
    event.preventDefault()
    return
  }

  draggedNode.value = node.type
  draggedNodeData.value = node

  // 设置拖拽数据 - 使用多种格式确保兼容性
  const dragData = {
    type: 'node',
    nodeType: node.type,
    nodeData: node,
  }

  const jsonData = JSON.stringify(dragData)
  console.log('设置拖拽数据:', jsonData)

  // 设置多种数据格式以确保兼容性
  event.dataTransfer.setData('application/json', jsonData)
  event.dataTransfer.setData('text/plain', jsonData)
  event.dataTransfer.setData('text', jsonData)

  event.dataTransfer.effectAllowed = 'copy'

  console.log('拖拽数据已设置，触发事件')
  emit('node-drag-start', node)
}

function handleDragEnd() {
  draggedNode.value = null
  draggedNodeData.value = null
  dragPreviewStyle.value = {}

  emit('node-drag-end')
}

function handleNodeClick(node) {
  if (node.disabled) return

  // 单击选中节点（可以用于预览等）
  console.log('Node clicked:', node)
  emit('nodeClick', node)
}

function handleNodeDoubleClick(node) {
  if (node.disabled) return

  // 双击添加节点到画布中心
  emit('nodeDoubleClick', node)
}

function showNodeInfo(node) {
  selectedNodeInfo.value = node
  showInfoModal.value = true
}

function closeInfoModal() {
  showInfoModal.value = false
  selectedNodeInfo.value = null
}

function addNodeFromModal() {
  if (selectedNodeInfo.value) {
    emit('add-node', {
      type: selectedNodeInfo.value.type,
      position: { x: 400, y: 300 },
    })
    closeInfoModal()
  }
}

function configureNode(node) {
  emit('configure-node', node)
}

function getNodeTooltip(node) {
  let tooltip = `${node.name}\n${node.description}`

  if (node.shortcut) {
    tooltip += `\n快捷键: ${node.shortcut}`
  }

  if (node.disabled) {
    tooltip += '\n状态: 已禁用'
  }

  return tooltip
}

// 鼠标移动事件处理（用于拖拽预览）
function handleMouseMove(event) {
  if (draggedNode.value) {
    dragPreviewStyle.value = {
      left: `${event.clientX + 10}px`,
      top: `${event.clientY + 10}px`,
    }
  }
}

// 生命周期
onMounted(() => {
  // 加载收藏节点
  const saved = localStorage.getItem('workflow-favorite-nodes')
  if (saved) {
    try {
      const favorites = JSON.parse(saved)
      favoriteNodes.value = new Set(favorites)
    } catch (e) {
      console.warn('Failed to load favorite nodes:', e)
    }
  }

  // 添加鼠标移动监听
  document.addEventListener('mousemove', handleMouseMove)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<style scoped>
.node-library {
  display: flex;
  flex-direction: column;
  width: 280px;
  height: 100%;
  background: #ffffff;
  border-right: 1px solid #e8e8e8;
  transition: width 0.3s ease;
}

.node-library.collapsed {
  width: 40px;
}

.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.library-title {
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

.search-section {
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.search-input-wrapper {
  position: relative;
  margin-bottom: 12px;
}

.search-icon {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: #8c8c8c;
  font-size: 14px;
}

.search-input {
  width: 100%;
  padding: 8px 32px 8px 32px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.15s ease;
}

.search-input:focus {
  outline: none;
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  padding: 2px;
  border: none;
  background: none;
  color: #8c8c8c;
  cursor: pointer;
  font-size: 12px;
}

.clear-btn:hover {
  color: #ff4d4f;
}

.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.category-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: #ffffff;
  color: #595959;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.category-btn:hover {
  border-color: #40a9ff;
  color: #1890ff;
}

.category-btn.active {
  border-color: #1890ff;
  background: #e6f7ff;
  color: #1890ff;
}

.node-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.node-group {
  margin-bottom: 16px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 6px;
  cursor: pointer;
  user-select: none;
}

.group-header:hover {
  background: #e6f7ff;
}

.group-icon {
  font-size: 16px;
}

.group-title {
  flex: 1;
  font-weight: 600;
  color: #262626;
}

.group-count {
  font-size: 12px;
  color: #8c8c8c;
}

.group-toggle {
  padding: 2px;
  border: none;
  background: none;
  color: #8c8c8c;
  cursor: pointer;
  font-size: 12px;
}

.group-content {
  padding: 8px 0;
}

.node-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #ffffff;
  cursor: grab;
  transition: all 0.15s ease;
  margin-bottom: 8px;
  position: relative;
}

.node-item:hover {
  border-color: #40a9ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.node-item.dragging {
  opacity: 0.5;
  cursor: grabbing;
}

.node-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f5f5f5;
}

.node-item.disabled:hover {
  border-color: #e8e8e8;
  box-shadow: none;
  transform: none;
}

.node-icon {
  position: relative;
  flex-shrink: 0;
}

.node-icon .icon {
  font-size: 24px;
  display: block;
}

.node-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ff4d4f;
  color: white;
  border-radius: 8px;
  padding: 2px 4px;
  font-size: 10px;
  font-weight: bold;
  min-width: 16px;
  text-align: center;
}

.node-info {
  flex: 1;
  min-width: 0;
}

.node-name {
  font-weight: 600;
  color: #262626;
  margin-bottom: 4px;
  font-size: 14px;
}

.node-description {
  color: #8c8c8c;
  font-size: 12px;
  line-height: 1.4;
  margin-bottom: 6px;
}

.node-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.node-tag {
  background: #f0f0f0;
  color: #595959;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 500;
}

.more-tags {
  color: #8c8c8c;
  font-size: 10px;
}

.node-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.node-item:hover .node-actions {
  opacity: 1;
}

.action-btn {
  padding: 4px;
  border: none;
  background: #f0f0f0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: #e6f7ff;
  color: #1890ff;
}

.action-btn.favorite.active {
  background: #fff7e6;
  color: #fa8c16;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
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

.drag-preview {
  position: fixed;
  z-index: 10000;
  pointer-events: none;
  transform: translate(-50%, -50%);
}

.preview-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #ffffff;
  border: 2px solid #1890ff;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.preview-icon {
  font-size: 16px;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.info-modal {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  max-width: 600px;
  max-height: 80vh;
  width: 90%;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.close-btn {
  padding: 4px 8px;
  border: none;
  background: none;
  color: #8c8c8c;
  cursor: pointer;
  font-size: 16px;
}

.close-btn:hover {
  color: #ff4d4f;
}

.modal-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.info-section {
  margin-bottom: 20px;
}

.info-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.info-section p {
  margin: 0;
  color: #595959;
  line-height: 1.6;
}

.param-list,
.property-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-item,
.property-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 4px;
}

.param-name,
.property-name {
  font-weight: 500;
  color: #262626;
  min-width: 100px;
}

.param-type,
.property-type {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 500;
}

.param-required,
.property-required {
  background: #fff2f0;
  color: #ff4d4f;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 500;
}

.property-desc {
  flex: 1;
  color: #8c8c8c;
  font-size: 12px;
  margin-top: 4px;
}

.example-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.example-item {
  padding: 12px;
  background: #f6ffed;
  border-left: 4px solid #52c41a;
  border-radius: 4px;
}

.example-title {
  font-weight: 600;
  color: #262626;
  margin-bottom: 4px;
}

.example-desc {
  color: #595959;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e8e8e8;
}

.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn.secondary {
  background: #ffffff;
  color: #595959;
}

.btn.secondary:hover {
  border-color: #40a9ff;
  color: #1890ff;
}

.btn.primary {
  background: #1890ff;
  border-color: #1890ff;
  color: #ffffff;
}

.btn.primary:hover {
  background: #40a9ff;
  border-color: #40a9ff;
}

/* 滚动条样式 */
.node-list::-webkit-scrollbar,
.modal-content::-webkit-scrollbar {
  width: 6px;
}

.node-list::-webkit-scrollbar-track,
.modal-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.node-list::-webkit-scrollbar-thumb,
.modal-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.node-list::-webkit-scrollbar-thumb:hover,
.modal-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
