<template>
  <div class="canvas-controls">
    <!-- Zoom controls -->
    <div class="zoom-controls">
      <button class="control-btn zoom-in" title="放大" @click="handleZoomIn">
        <span class="icon">+</span>
      </button>

      <div class="zoom-slider-container">
        <input
          type="range"
          class="zoom-slider"
          :min="minZoom * 100"
          :max="maxZoom * 100"
          :value="zoomLevel * 100"
          @input="handleZoomChange"
        />
        <div class="zoom-value">{{ Math.round(zoomLevel * 100) }}%</div>
      </div>

      <button class="control-btn zoom-out" title="缩小" @click="handleZoomOut">
        <span class="icon">−</span>
      </button>
    </div>

    <!-- Quick zoom buttons -->
    <div class="quick-zoom">
      <button class="control-btn" title="适应屏幕" @click="handleZoomFit">
        <span class="icon">⌂</span>
      </button>

      <button class="control-btn" title="重置缩放" @click="handleZoomReset">
        <span class="icon">1:1</span>
      </button>
    </div>

    <!-- Minimap toggle -->
    <div class="view-controls">
      <button
        class="control-btn"
        :class="{ active: showMinimap }"
        title="显示/隐藏缩略图"
        @click="handleToggleMinimap"
      >
        <span class="icon">🗺</span>
      </button>

      <button
        class="control-btn"
        :class="{ active: showGrid }"
        title="显示/隐藏网格"
        @click="handleToggleGrid"
      >
        <span class="icon">#</span>
      </button>
    </div>

    <!-- Fullscreen toggle -->
    <div class="screen-controls">
      <button
        class="control-btn"
        :title="isFullscreen ? '退出全屏' : '进入全屏'"
        @click="handleToggleFullscreen"
      >
        <span class="icon">{{ isFullscreen ? '⛶' : '⛶' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Props
const props = defineProps({
  // Zoom configuration
  zoomLevel: {
    type: Number,
    default: 1,
  },
  minZoom: {
    type: Number,
    default: 0.1,
  },
  maxZoom: {
    type: Number,
    default: 3,
  },

  // Display options
  showMinimap: {
    type: Boolean,
    default: true,
  },
  showGrid: {
    type: Boolean,
    default: true,
  },

  // Fullscreen state
  isFullscreen: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits([
  'zoom-change',
  'zoom-in',
  'zoom-out',
  'zoom-fit',
  'zoom-reset',
  'toggle-minimap',
  'toggle-grid',
  'toggle-fullscreen',
])

// Event handlers
function handleZoomIn() {
  emit('zoom-in')
}

function handleZoomOut() {
  emit('zoom-out')
}

function handleZoomChange(event) {
  const newZoom = parseFloat(event.target.value) / 100
  emit('zoom-change', newZoom)
}

function handleZoomFit() {
  emit('zoom-fit')
}

function handleZoomReset() {
  emit('zoom-reset')
}

function handleToggleMinimap() {
  emit('toggle-minimap')
}

function handleToggleGrid() {
  emit('toggle-grid')
}

function handleToggleFullscreen() {
  emit('toggle-fullscreen')
}
</script>

<style scoped>
.canvas-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 100;
}

.zoom-controls,
.quick-zoom,
.view-controls,
.screen-controls {
  display: flex;
  align-items: center;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.zoom-controls {
  padding: 8px;
  gap: 8px;
}

.quick-zoom,
.view-controls,
.screen-controls {
  flex-direction: column;
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  color: #666;
}

.control-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.control-btn:active {
  background: #e8e8e8;
}

.control-btn.active {
  background: #1890ff;
  color: white;
}

.control-btn.active:hover {
  background: #40a9ff;
}

.icon {
  font-size: 16px;
  font-weight: bold;
}

.zoom-slider-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.zoom-slider {
  width: 100px;
  height: 4px;
  background: #e8e8e8;
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.zoom-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: #1890ff;
  border-radius: 50%;
  cursor: pointer;
}

.zoom-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: #1890ff;
  border-radius: 50%;
  border: none;
  cursor: pointer;
}

.zoom-value {
  font-size: 12px;
  color: #666;
  font-weight: 500;
  min-width: 40px;
  text-align: center;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .canvas-controls {
    bottom: 10px;
    right: 10px;
    gap: 8px;
  }

  .control-btn {
    width: 32px;
    height: 32px;
  }

  .icon {
    font-size: 14px;
  }

  .zoom-slider {
    width: 80px;
  }
}
</style>
