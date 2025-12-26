<template>
  <!-- 边栏触发器 -->
  <SidebarTrigger
    v-if="chatWidgetStore.displayMode === 'collapsed' && chatWidgetStore.aiAssistantEnabled"
    @click="handleTriggerClick"
  />

  <!-- 浮动窗口 -->
  <Teleport to="body">
    <div
      v-if="chatWidgetStore.shouldShowFloating"
      class="floating-chat-widget"
      :class="{ fullscreen: isFullscreen }"
      :style="{
        left: chatWidgetStore.floatingPosition.x + 'px',
        top: chatWidgetStore.floatingPosition.y + 'px',
        width: chatWidgetStore.floatingSize.width + 'px',
        height: chatWidgetStore.floatingSize.height + 'px',
      }"
      @mousedown="handleMouseDown"
    >
      <!-- 窗口标题栏 -->
      <div ref="headerRef" class="floating-header">
        <div class="header-title">
          <Icon icon="mdi:robot" class="header-icon" />
          <span>AI 助手</span>
        </div>
        <div class="header-actions">
          <n-button quaternary size="small" class="action-btn" @click="minimizeToSidebar">
            <Icon icon="mdi:minus" />
          </n-button>
          <n-button quaternary size="small" class="action-btn" @click="toggleFullscreen">
            <Icon :icon="isFullscreen ? 'mdi:fullscreen-exit' : 'mdi:fullscreen'" />
          </n-button>
        </div>
      </div>

      <!-- 窗口内容 -->
      <div class="floating-content">
        <UnifiedChatContainer />
      </div>

      <!-- 调整大小手柄 -->
      <div v-if="!isFullscreen" class="resize-handle" @mousedown="handleResizeStart"></div>
    </div>
  </Teleport>

  <!-- 内嵌模式（在workbench页面中） -->
  <div v-if="chatWidgetStore.displayMode === 'expanded'" class="embedded-chat-widget">
    <ChatWidgetContainer />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useChatWidgetStore } from '@/store'
import { Icon } from '@iconify/vue'
import UnifiedChatContainer from './UnifiedChatContainer.vue'
import SidebarTrigger from './SidebarTrigger.vue'

const chatWidgetStore = useChatWidgetStore()
const headerRef = ref(null)
const isDragging = ref(false)
const isResizing = ref(false)
const isFullscreen = ref(false)
const dragOffset = ref({ x: 0, y: 0 })
const resizeStart = ref({ x: 0, y: 0, width: 0, height: 0 })
const originalSize = ref({ x: 0, y: 0, width: 0, height: 0 })

// 浮动窗口样式
const floatingStyle = computed(() => ({
  left: `${chatWidgetStore.floatingPosition.x}px`,
  top: `${chatWidgetStore.floatingPosition.y}px`,
  width: `${chatWidgetStore.floatingSize.width}px`,
  height: `${chatWidgetStore.floatingSize.height}px`,
  zIndex: 9999,
}))

// 处理边栏触发器点击
const handleTriggerClick = () => {
  chatWidgetStore.setDisplayMode('floating')
}

// 最小化到边栏
const minimizeToSidebar = () => {
  chatWidgetStore.setDisplayMode('collapsed')
}

// 切换全屏模式
const toggleFullscreen = () => {
  if (isFullscreen.value) {
    // 退出全屏，恢复原始大小和位置
    chatWidgetStore.setFloatingPosition({ x: originalSize.value.x, y: originalSize.value.y })
    chatWidgetStore.setFloatingSize({
      width: originalSize.value.width,
      height: originalSize.value.height,
    })
    isFullscreen.value = false
  } else {
    // 进入全屏，保存当前大小和位置
    originalSize.value = {
      x: chatWidgetStore.floatingPosition.x,
      y: chatWidgetStore.floatingPosition.y,
      width: chatWidgetStore.floatingSize.width,
      height: chatWidgetStore.floatingSize.height,
    }
    // 设置为全屏大小
    chatWidgetStore.setFloatingPosition({ x: 0, y: 0 })
    chatWidgetStore.setFloatingSize({ width: window.innerWidth, height: window.innerHeight })
    isFullscreen.value = true
  }
}

// 处理鼠标按下事件（拖拽开始）
const handleMouseDown = (e) => {
  // 只有点击标题栏才能拖拽，且不在全屏模式下
  if (!headerRef.value?.contains(e.target) || isFullscreen.value) return

  isDragging.value = true
  dragOffset.value = {
    x: e.clientX - chatWidgetStore.floatingPosition.x,
    y: e.clientY - chatWidgetStore.floatingPosition.y,
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  e.preventDefault()
}

// 处理鼠标移动事件（拖拽中）
const handleMouseMove = (e) => {
  if (isDragging.value) {
    const newPosition = {
      x: Math.max(
        0,
        Math.min(
          window.innerWidth - chatWidgetStore.floatingSize.width,
          e.clientX - dragOffset.value.x
        )
      ),
      y: Math.max(
        0,
        Math.min(
          window.innerHeight - chatWidgetStore.floatingSize.height,
          e.clientY - dragOffset.value.y
        )
      ),
    }
    chatWidgetStore.setFloatingPosition(newPosition)
  }

  if (isResizing.value) {
    const deltaX = e.clientX - resizeStart.value.x
    const deltaY = e.clientY - resizeStart.value.y

    const newSize = {
      width: Math.max(
        800,
        Math.min(
          window.innerWidth - chatWidgetStore.floatingPosition.x,
          resizeStart.value.width + deltaX
        )
      ),
      height: Math.max(
        400,
        Math.min(
          window.innerHeight - chatWidgetStore.floatingPosition.y,
          resizeStart.value.height + deltaY
        )
      ),
    }
    chatWidgetStore.setFloatingSize(newSize)
  }
}

// 处理鼠标释放事件（拖拽结束）
const handleMouseUp = () => {
  isDragging.value = false
  isResizing.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

// 处理调整大小开始
const handleResizeStart = (e) => {
  // 全屏模式下禁用调整大小
  if (isFullscreen.value) return

  isResizing.value = true
  resizeStart.value = {
    x: e.clientX,
    y: e.clientY,
    width: chatWidgetStore.floatingSize.width,
    height: chatWidgetStore.floatingSize.height,
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  e.preventDefault()
  e.stopPropagation()
}

// 组件挂载时初始化store
onMounted(() => {
  chatWidgetStore.initStore()
})

// 组件卸载时清理事件监听器
onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})
</script>

<style scoped>
/* 浮动窗口样式 */
.floating-chat-widget {
  position: fixed;
  background: rgba(240, 240, 240, 0.98);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid var(--n-border-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  user-select: none;
  backdrop-filter: blur(3px);
  transition: all 0.3s ease;
  z-index: 9999;
}

/* 全屏模式样式 */
.floating-chat-widget.fullscreen {
  border-radius: 0;
  border: none;
  box-shadow: none;
  background: #ffffff;
}

/* 暗色主题下的全屏模式 */
.dark .floating-chat-widget.fullscreen {
  background: #18181c;
}

.floating-chat-widget:hover {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
}

/* 浮动窗口标题栏 */
.floating-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #ff9a56 0%, #ff7b2c 100%);
  border-bottom: 1px solid var(--n-border-color);
  cursor: move;
  min-height: 48px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.header-icon {
  font-size: 18px;
  color: #8b5cf6;
}

.header-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--n-close-color-hover);
}

/* 浮动窗口内容 */
.floating-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 调整大小手柄 */
.resize-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 16px;
  height: 16px;
  cursor: se-resize;
  background: linear-gradient(
    -45deg,
    transparent 0%,
    transparent 40%,
    var(--n-border-color) 40%,
    var(--n-border-color) 60%,
    transparent 60%
  );
  background-size: 4px 4px;
}

.resize-handle:hover {
  background: linear-gradient(
    -45deg,
    transparent 0%,
    transparent 40%,
    var(--n-primary-color) 40%,
    var(--n-primary-color) 60%,
    transparent 60%
  );
}

/* 内嵌模式样式 */
.embedded-chat-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--n-card-color);
  border-radius: 12px;
  overflow: hidden;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .floating-chat-widget {
    left: 0 !important;
    top: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    border-radius: 0;
  }

  .resize-handle {
    display: none;
  }
}

/* 暗色主题适配 */
.dark .floating-chat-widget {
  background: rgba(24, 24, 28, 0.95);
  border-color: var(--n-border-color);
}

.dark .floating-header {
  background: var(--n-color-embedded);
  border-bottom-color: var(--n-border-color);
}

/* 动画效果 */
.floating-chat-widget {
  animation: slideInUp 0.3s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
