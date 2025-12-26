<template>
  <div class="workflow-toolbar" :class="{ vertical: vertical }">
    <!-- 基础工具组 -->
    <div class="toolbar-group basic-tools">
      <div class="group-label">基础工具</div>

      <!-- 选择工具 -->
      <button
        class="toolbar-btn"
        :class="{ active: activeTool === 'select' }"
        title="选择工具 (V)"
        @click="setActiveTool('select')"
      >
        <span class="icon">🔍</span>
        <span class="label">选择</span>
      </button>

      <!-- 拖拽工具 -->
      <button
        class="toolbar-btn"
        :class="{ active: activeTool === 'pan' }"
        title="拖拽画布 (H)"
        @click="setActiveTool('pan')"
      >
        <span class="icon">✋</span>
        <span class="label">拖拽</span>
      </button>

      <!-- 连接工具 -->
      <button
        class="toolbar-btn"
        :class="{ active: activeTool === 'connect' }"
        title="连接工具 (C)"
        @click="setActiveTool('connect')"
      >
        <span class="icon">🔗</span>
        <span class="label">连接</span>
      </button>
    </div>

    <!-- 节点工具组 -->
    <div class="toolbar-group node-tools">
      <div class="group-label">节点类型</div>

      <button
        v-for="nodeType in nodeTypes"
        :key="nodeType.type"
        class="toolbar-btn node-btn"
        :class="{ active: activeTool === `node:${nodeType.type}` }"
        :title="`添加${nodeType.name} (${nodeType.shortcut || ''})`"
        @click="setActiveTool(`node:${nodeType.type}`)"
      >
        <span class="icon">{{ nodeType.icon }}</span>
        <span class="label">{{ nodeType.name }}</span>
      </button>
    </div>

    <!-- 编辑工具组 -->
    <div class="toolbar-group edit-tools">
      <div class="group-label">编辑</div>

      <!-- 撤销 -->
      <button class="toolbar-btn" :disabled="!canUndo" title="撤销 (Ctrl+Z)" @click="handleUndo">
        <span class="icon">↶</span>
        <span class="label">撤销</span>
      </button>

      <!-- 重做 -->
      <button class="toolbar-btn" :disabled="!canRedo" title="重做 (Ctrl+Y)" @click="handleRedo">
        <span class="icon">↷</span>
        <span class="label">重做</span>
      </button>

      <!-- 复制 -->
      <button
        class="toolbar-btn"
        :disabled="!hasSelection"
        title="复制 (Ctrl+C)"
        @click="handleCopy"
      >
        <span class="icon">📋</span>
        <span class="label">复制</span>
      </button>

      <!-- 粘贴 -->
      <button
        class="toolbar-btn"
        :disabled="!hasClipboard"
        title="粘贴 (Ctrl+V)"
        @click="handlePaste"
      >
        <span class="icon">📄</span>
        <span class="label">粘贴</span>
      </button>

      <!-- 删除 -->
      <button
        class="toolbar-btn"
        :disabled="!hasSelection"
        title="删除 (Delete)"
        @click="handleDelete"
      >
        <span class="icon">🗑️</span>
        <span class="label">删除</span>
      </button>
    </div>

    <!-- 视图工具组 -->
    <div class="toolbar-group view-tools">
      <div class="group-label">视图</div>

      <!-- 缩放控制 -->
      <div class="zoom-controls">
        <button class="toolbar-btn small" title="缩小 (-)" @click="handleZoomOut">
          <span class="icon">🔍-</span>
        </button>

        <div class="zoom-display" title="重置缩放 (0)" @click="handleZoomReset">
          {{ Math.round(scale * 100) }}%
        </div>

        <button class="toolbar-btn small" title="放大 (+)" @click="handleZoomIn">
          <span class="icon">🔍+</span>
        </button>
      </div>

      <!-- 适应画布 -->
      <button class="toolbar-btn" title="适应画布 (F)" @click="handleFitToScreen">
        <span class="icon">📐</span>
        <span class="label">适应</span>
      </button>

      <!-- 网格切换 -->
      <button
        class="toolbar-btn"
        :class="{ active: showGrid }"
        title="显示网格 (G)"
        @click="toggleGrid"
      >
        <span class="icon">⚏</span>
        <span class="label">网格</span>
      </button>

      <!-- 对齐切换 -->
      <button
        class="toolbar-btn"
        :class="{ active: snapToGrid }"
        title="网格对齐 (S)"
        @click="toggleSnap"
      >
        <span class="icon">🧲</span>
        <span class="label">对齐</span>
      </button>
    </div>

    <!-- 布局工具组 -->
    <div class="toolbar-group layout-tools">
      <div class="group-label">布局</div>

      <!-- 自动排列 -->
      <button class="toolbar-btn" title="自动排列" @click="handleAutoLayout">
        <span class="icon">📊</span>
        <span class="label">排列</span>
      </button>

      <!-- 对齐工具 -->
      <div class="align-tools">
        <button
          class="toolbar-btn small"
          :disabled="!hasMultipleSelection"
          title="左对齐"
          @click="handleAlign('left')"
        >
          <span class="icon">⫷</span>
        </button>

        <button
          class="toolbar-btn small"
          :disabled="!hasMultipleSelection"
          title="居中对齐"
          @click="handleAlign('center')"
        >
          <span class="icon">⫸</span>
        </button>

        <button
          class="toolbar-btn small"
          :disabled="!hasMultipleSelection"
          title="右对齐"
          @click="handleAlign('right')"
        >
          <span class="icon">⫸</span>
        </button>
      </div>
    </div>

    <!-- 验证工具组 -->
    <div class="toolbar-group validation-tools">
      <div class="group-label">验证</div>

      <!-- 验证工作流 -->
      <button
        class="toolbar-btn"
        :class="{
          active: showValidation,
          error: validationResult && !validationResult.isValid,
          success: validationResult && validationResult.isValid,
        }"
        title="验证工作流"
        @click="toggleValidation"
      >
        <span class="icon">✓</span>
        <span class="label">验证</span>
        <span v-if="validationResult && !validationResult.isValid" class="error-count">
          {{ validationResult.errors.length }}
        </span>
      </button>

      <!-- 运行预览 -->
      <button
        class="toolbar-btn"
        :disabled="!validationResult?.isValid"
        title="运行预览"
        @click="handlePreview"
      >
        <span class="icon">▶️</span>
        <span class="label">预览</span>
      </button>
    </div>

    <!-- 文件工具组 -->
    <div class="toolbar-group file-tools">
      <div class="group-label">文件</div>

      <!-- 新建 -->
      <button class="toolbar-btn" title="新建工作流 (Ctrl+N)" @click="handleNew">
        <span class="icon">📄</span>
        <span class="label">新建</span>
      </button>

      <!-- 打开 -->
      <button class="toolbar-btn" title="打开工作流 (Ctrl+O)" @click="handleOpen">
        <span class="icon">📁</span>
        <span class="label">打开</span>
      </button>

      <!-- 保存 -->
      <button
        class="toolbar-btn"
        :class="{ active: isDirty }"
        title="保存工作流 (Ctrl+S)"
        @click="handleSave"
      >
        <span class="icon">💾</span>
        <span class="label">保存</span>
      </button>

      <!-- 导出 -->
      <button class="toolbar-btn" title="导出工作流" @click="handleExport">
        <span class="icon">📤</span>
        <span class="label">导出</span>
      </button>
    </div>

    <!-- 自定义工具 -->
    <div v-if="customTools.length > 0" class="toolbar-group custom-tools">
      <div class="group-label">工具</div>

      <button
        v-for="tool in customTools"
        :key="tool.id"
        class="toolbar-btn"
        :disabled="tool.disabled"
        :title="tool.tooltip || tool.label"
        @click="tool.action"
      >
        <span class="icon">{{ tool.icon }}</span>
        <span class="label">{{ tool.label }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import { NODE_TYPES } from '../../utils/nodeTypes'

// Props
const props = defineProps({
  activeTool: {
    type: String,
    default: 'select',
  },
  scale: {
    type: Number,
    default: 1,
  },
  showGrid: {
    type: Boolean,
    default: true,
  },
  snapToGrid: {
    type: Boolean,
    default: true,
  },
  showValidation: {
    type: Boolean,
    default: false,
  },
  validationResult: {
    type: Object,
    default: null,
  },
  canUndo: {
    type: Boolean,
    default: false,
  },
  canRedo: {
    type: Boolean,
    default: false,
  },
  hasSelection: {
    type: Boolean,
    default: false,
  },
  hasMultipleSelection: {
    type: Boolean,
    default: false,
  },
  hasClipboard: {
    type: Boolean,
    default: false,
  },
  isDirty: {
    type: Boolean,
    default: false,
  },
  vertical: {
    type: Boolean,
    default: false,
  },
  customTools: {
    type: Array,
    default: () => [],
  },
})

// Emits
const emit = defineEmits([
  'tool-change',
  'undo',
  'redo',
  'copy',
  'paste',
  'delete',
  'zoom-in',
  'zoom-out',
  'zoom-reset',
  'fit-to-screen',
  'toggle-grid',
  'toggle-snap',
  'auto-layout',
  'align',
  'toggle-validation',
  'preview',
  'new',
  'open',
  'save',
  'export',
])

// 注入的依赖
const workflowStore = inject('workflowStore')

// 计算属性
const nodeTypes = computed(() => {
  return Object.values(NODE_TYPES).map((type) => ({
    type: type.type,
    name: type.name,
    icon: type.icon,
    shortcut: type.shortcut,
  }))
})

// 方法
function setActiveTool(tool) {
  emit('tool-change', tool)
}

function handleUndo() {
  emit('undo')
}

function handleRedo() {
  emit('redo')
}

function handleCopy() {
  emit('copy')
}

function handlePaste() {
  emit('paste')
}

function handleDelete() {
  emit('delete')
}

function handleZoomIn() {
  emit('zoom-in')
}

function handleZoomOut() {
  emit('zoom-out')
}

function handleZoomReset() {
  emit('zoom-reset')
}

function handleFitToScreen() {
  emit('fit-to-screen')
}

function toggleGrid() {
  emit('toggle-grid')
}

function toggleSnap() {
  emit('toggle-snap')
}

function handleAutoLayout() {
  emit('auto-layout')
}

function handleAlign(direction) {
  emit('align', direction)
}

function toggleValidation() {
  emit('toggle-validation')
}

function handlePreview() {
  emit('preview')
}

function handleNew() {
  emit('new')
}

function handleOpen() {
  emit('open')
}

function handleSave() {
  emit('save')
}

function handleExport() {
  emit('export')
}
</script>

<style scoped>
.workflow-toolbar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: #ffffff;
  border-right: 1px solid #e8e8e8;
  min-width: 200px;
  max-width: 250px;
  height: 100%;
  overflow-y: auto;
  user-select: none;
}

.workflow-toolbar.vertical {
  flex-direction: row;
  min-width: auto;
  max-width: none;
  width: 100%;
  height: auto;
  border-right: none;
  border-bottom: 1px solid #e8e8e8;
  overflow-x: auto;
  overflow-y: hidden;
}

.toolbar-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.vertical .toolbar-group {
  flex-direction: row;
  align-items: center;
  gap: 12px;
}

.group-label {
  font-size: 12px;
  font-weight: 600;
  color: #8c8c8c;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.vertical .group-label {
  margin-bottom: 0;
  margin-right: 8px;
  white-space: nowrap;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #ffffff;
  color: #262626;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
  min-height: 36px;
}

.toolbar-btn:hover {
  border-color: #40a9ff;
  color: #1890ff;
  background: #f6ffed;
}

.toolbar-btn.active {
  border-color: #1890ff;
  background: #e6f7ff;
  color: #1890ff;
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f5f5f5;
}

.toolbar-btn:disabled:hover {
  border-color: #d9d9d9;
  color: #262626;
  background: #f5f5f5;
}

.toolbar-btn.small {
  padding: 4px 8px;
  min-height: 28px;
  font-size: 12px;
}

.toolbar-btn.error {
  border-color: #ff4d4f;
  background: #fff2f0;
  color: #ff4d4f;
}

.toolbar-btn.success {
  border-color: #52c41a;
  background: #f6ffed;
  color: #52c41a;
}

.icon {
  font-size: 16px;
  flex-shrink: 0;
}

.label {
  flex: 1;
  text-align: left;
  white-space: nowrap;
}

.vertical .label {
  display: none;
}

.error-count {
  background: #ff4d4f;
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: bold;
  min-width: 16px;
  text-align: center;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.zoom-display {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: #fafafa;
  font-size: 12px;
  font-weight: 500;
  color: #262626;
  cursor: pointer;
  min-width: 50px;
  text-align: center;
  transition: all 0.15s ease;
}

.zoom-display:hover {
  border-color: #40a9ff;
  background: #f6ffed;
}

.align-tools {
  display: flex;
  gap: 2px;
}

.node-btn {
  position: relative;
}

.node-btn::after {
  content: attr(title);
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
  z-index: 1000;
  margin-left: 8px;
}

.node-btn:hover::after {
  opacity: 1;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .workflow-toolbar {
    min-width: 180px;
    max-width: 200px;
  }

  .toolbar-btn {
    padding: 6px 8px;
    font-size: 12px;
    min-height: 32px;
  }

  .icon {
    font-size: 14px;
  }

  .label {
    font-size: 12px;
  }
}

/* 滚动条样式 */
.workflow-toolbar::-webkit-scrollbar {
  width: 6px;
}

.workflow-toolbar::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.workflow-toolbar::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.workflow-toolbar::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
