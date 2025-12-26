<template>
  <div class="canvas-toolbar">
    <!-- History controls -->
    <div class="toolbar-group">
      <button class="toolbar-btn" :disabled="!canUndo" title="撤销 (Ctrl+Z)" @click="handleUndo">
        <span class="icon">↶</span>
      </button>
      <button class="toolbar-btn" :disabled="!canRedo" title="重做 (Ctrl+Y)" @click="handleRedo">
        <span class="icon">↷</span>
      </button>
    </div>

    <!-- Zoom controls -->
    <div class="toolbar-group">
      <button class="toolbar-btn" title="缩小 (-)" @click="handleZoomOut">
        <span class="icon">−</span>
      </button>
      <span class="zoom-display">{{ Math.round(zoomLevel * 100) }}%</span>
      <button class="toolbar-btn" title="放大 (+)" @click="handleZoomIn">
        <span class="icon">+</span>
      </button>
      <button class="toolbar-btn" title="适应屏幕 (Ctrl+0)" @click="handleZoomFit">
        <span class="icon">⌂</span>
      </button>
      <button class="toolbar-btn" title="重置缩放 (Ctrl+1)" @click="handleZoomReset">
        <span class="icon">1:1</span>
      </button>
    </div>

    <!-- Layout controls -->
    <div class="toolbar-group">
      <button class="toolbar-btn" title="自动布局" @click="handleAutoLayout">
        <span class="icon">⚏</span>
      </button>
      <button
        class="toolbar-btn"
        :class="{ active: showGrid }"
        title="显示/隐藏网格"
        @click="handleToggleGrid"
      >
        <span class="icon">#</span>
      </button>
      <button
        class="toolbar-btn"
        :class="{ active: showAlignment }"
        title="显示/隐藏对齐线"
        @click="handleToggleAlignment"
      >
        <span class="icon">⫽</span>
      </button>
    </div>

    <!-- Selection controls -->
    <div class="toolbar-group">
      <button class="toolbar-btn" title="全选 (Ctrl+A)" @click="handleSelectAll">
        <span class="icon">⬚</span>
      </button>
      <button
        class="toolbar-btn"
        :disabled="!hasSelection"
        title="复制 (Ctrl+C)"
        @click="handleCopy"
      >
        <span class="icon">⧉</span>
      </button>
      <button class="toolbar-btn" :disabled="!canPaste" title="粘贴 (Ctrl+V)" @click="handlePaste">
        <span class="icon">📋</span>
      </button>
      <button
        class="toolbar-btn"
        :disabled="!hasSelection"
        title="删除 (Delete)"
        @click="handleDelete"
      >
        <span class="icon">🗑</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Props
const props = defineProps({
  // History state
  canUndo: {
    type: Boolean,
    default: false,
  },
  canRedo: {
    type: Boolean,
    default: false,
  },

  // Zoom state
  zoomLevel: {
    type: Number,
    default: 1,
  },

  // Display options
  showGrid: {
    type: Boolean,
    default: true,
  },
  showAlignment: {
    type: Boolean,
    default: true,
  },

  // Selection state
  hasSelection: {
    type: Boolean,
    default: false,
  },
  canPaste: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits([
  'undo',
  'redo',
  'zoom-in',
  'zoom-out',
  'zoom-fit',
  'zoom-reset',
  'auto-layout',
  'toggle-grid',
  'toggle-alignment',
  'select-all',
  'copy',
  'paste',
  'delete',
])

// Event handlers
function handleUndo() {
  emit('undo')
}

function handleRedo() {
  emit('redo')
}

function handleZoomIn() {
  emit('zoom-in')
}

function handleZoomOut() {
  emit('zoom-out')
}

function handleZoomFit() {
  emit('zoom-fit')
}

function handleZoomReset() {
  emit('zoom-reset')
}

function handleAutoLayout() {
  emit('auto-layout')
}

function handleToggleGrid() {
  emit('toggle-grid')
}

function handleToggleAlignment() {
  emit('toggle-alignment')
}

function handleSelectAll() {
  emit('select-all')
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
</script>

<style scoped>
.canvas-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
  border-right: 1px solid #e8e8e8;
}

.toolbar-group:last-child {
  border-right: none;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: #666;
}

.toolbar-btn:hover:not(:disabled) {
  background: #f5f5f5;
  color: #333;
}

.toolbar-btn:active:not(:disabled) {
  background: #e8e8e8;
}

.toolbar-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.toolbar-btn.active {
  background: #1890ff;
  color: white;
}

.toolbar-btn.active:hover {
  background: #40a9ff;
}

.icon {
  font-size: 14px;
  font-weight: bold;
}

.zoom-display {
  min-width: 48px;
  text-align: center;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}
</style>
