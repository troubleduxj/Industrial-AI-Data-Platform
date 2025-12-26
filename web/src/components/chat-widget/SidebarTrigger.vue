<template>
  <div class="sidebar-trigger" @click="handleClick">
    <!-- 触发器按钮 -->
    <div class="trigger-button" :class="{ 'has-notification': hasUnreadMessages }">
      <Icon icon="mdi:robot" class="trigger-icon" />

      <!-- 未读消息提示 -->
      <div v-if="hasUnreadMessages" class="notification-badge">
        <span>{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
      </div>
    </div>

    <!-- 悬停预览 -->
    <Transition name="preview-fade">
      <div v-if="showPreview" class="hover-preview">
        <div class="preview-header">
          <Icon icon="mdi:robot" class="preview-icon" />
          <span class="preview-title">AI 助手</span>
        </div>

        <div class="preview-content">
          <!-- 显示最近的消息或欢迎信息 -->
          <div v-if="lastMessage" class="last-message">
            <div class="message-preview">
              <span class="message-type">{{ lastMessage.type === 'user' ? '您' : 'AI' }}:</span>
              <span class="message-text">{{ truncateMessage(lastMessage.content) }}</span>
            </div>
            <div class="message-time">{{ formatTime(lastMessage.timestamp) }}</div>
          </div>

          <div v-else class="welcome-preview">
            <p>点击打开AI助手</p>
            <p class="preview-hint">智能对话 · 功能导航</p>
          </div>
        </div>

        <div class="preview-footer">
          <span class="click-hint">点击展开</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useChatWidgetStore } from '@/store'
import { Icon } from '@iconify/vue'

const emit = defineEmits(['click'])
const chatWidgetStore = useChatWidgetStore()

const showPreview = ref(false)
const hoverTimer = ref(null)
const leaveTimer = ref(null)

// 计算属性
const hasUnreadMessages = computed(() => {
  // 这里可以实现未读消息逻辑
  return false
})

const unreadCount = computed(() => {
  // 这里可以实现未读消息计数逻辑
  return 0
})

const lastMessage = computed(() => {
  const sessions = chatWidgetStore.chatSessions
  if (sessions.length === 0) return null

  // 获取最新会话的最后一条消息
  const latestSession = sessions[0]
  const messages =
    chatWidgetStore.chatHistory.find((s) => s.id === latestSession.id)?.messages || []
  return messages[messages.length - 1] || null
})

// 处理点击事件
const handleClick = () => {
  emit('click')
  hidePreview()
}

// 显示预览
const showPreviewWithDelay = () => {
  clearTimeout(leaveTimer.value)
  hoverTimer.value = setTimeout(() => {
    showPreview.value = true
  }, 500) // 500ms延迟显示
}

// 隐藏预览
const hidePreview = () => {
  clearTimeout(hoverTimer.value)
  showPreview.value = false
}

// 延迟隐藏预览
const hidePreviewWithDelay = () => {
  leaveTimer.value = setTimeout(() => {
    hidePreview()
  }, 200) // 200ms延迟隐藏
}

// 截断消息文本
const truncateMessage = (text) => {
  if (!text) return ''
  return text.length > 30 ? text.slice(0, 30) + '...' : text
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) {
    // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) {
    // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    // 24小时内
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleDateString()
  }
}

// 组件挂载时添加事件监听器
onMounted(() => {
  const triggerEl = document.querySelector('.sidebar-trigger')
  if (triggerEl) {
    triggerEl.addEventListener('mouseenter', showPreviewWithDelay)
    triggerEl.addEventListener('mouseleave', hidePreviewWithDelay)
  }
})

// 组件卸载时清理事件监听器
onUnmounted(() => {
  clearTimeout(hoverTimer.value)
  clearTimeout(leaveTimer.value)

  const triggerEl = document.querySelector('.sidebar-trigger')
  if (triggerEl) {
    triggerEl.removeEventListener('mouseenter', showPreviewWithDelay)
    triggerEl.removeEventListener('mouseleave', hidePreviewWithDelay)
  }
})
</script>

<style scoped>
.sidebar-trigger {
  position: fixed;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 9998;
  user-select: none;
}

/* 触发器按钮 */
.trigger-button {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #a855f7, #9333ea);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.trigger-button::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.trigger-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
}

.trigger-button:hover::before {
  opacity: 1;
}

.trigger-button:active {
  transform: scale(0.95);
}

.trigger-button.has-notification {
}

/* 触发器按钮 */
.trigger-button {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #a855f7, #9333ea);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.trigger-button::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.trigger-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
}

.trigger-button:hover::before {
  opacity: 1;
}

.trigger-button:active {
  transform: scale(0.95);
}

.trigger-button.has-notification {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15), 0 0 0 0 rgba(var(--n-primary-color-rgb), 0.7);
  }
  70% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15), 0 0 0 10px rgba(var(--n-primary-color-rgb), 0);
  }
  100% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15), 0 0 0 0 rgba(var(--n-primary-color-rgb), 0);
  }
}

.trigger-icon {
  font-size: 28px;
  color: white;
  z-index: 1;
}

/* 未读消息提示 */
.notification-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  background: #ff4757;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: white;
  border: 2px solid white;
  z-index: 2;
}

/* 悬停预览 */
.hover-preview {
  position: absolute;
  right: 70px;
  top: 50%;
  transform: translateY(-50%);
  width: 280px;
  background: var(--n-card-color);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--n-border-color);
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--n-color-embedded);
  border-bottom: 1px solid var(--n-border-color);
}

.preview-icon {
  font-size: 18px;
  color: var(--n-primary-color);
}

.preview-title {
  font-weight: 600;
  color: var(--n-text-color);
  font-size: 14px;
}

.preview-content {
  padding: 16px;
}

.last-message {
  margin-bottom: 8px;
}

.message-preview {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
}

.message-type {
  font-weight: 600;
  color: var(--n-primary-color);
  font-size: 12px;
  flex-shrink: 0;
}

.message-text {
  color: var(--n-text-color);
  font-size: 12px;
  line-height: 1.4;
  word-wrap: break-word;
}

.message-time {
  font-size: 11px;
  color: var(--n-text-color-disabled);
}

.welcome-preview p {
  margin: 0;
  color: var(--n-text-color);
  font-size: 13px;
  line-height: 1.4;
}

.preview-hint {
  color: var(--n-text-color-disabled) !important;
  font-size: 11px !important;
  margin-top: 4px !important;
}

.preview-footer {
  padding: 8px 16px;
  background: var(--n-color-embedded);
  border-top: 1px solid var(--n-border-color);
  text-align: center;
}

.click-hint {
  font-size: 11px;
  color: var(--n-text-color-disabled);
}

/* 预览动画 */
.preview-fade-enter-active,
.preview-fade-leave-active {
  transition: all 0.3s ease;
}

.preview-fade-enter-from {
  opacity: 0;
  transform: translateY(-50%) translateX(10px) scale(0.95);
}

.preview-fade-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(10px) scale(0.95);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar-trigger {
    right: 16px;
  }

  .trigger-button {
    width: 48px;
    height: 48px;
  }

  .trigger-icon {
    font-size: 24px;
  }

  .hover-preview {
    width: 240px;
    right: 60px;
  }
}

/* 暗色主题适配 */
.dark .hover-preview {
  background: var(--n-card-color);
  border-color: var(--n-border-color);
}

.dark .preview-header,
.dark .preview-footer {
  background: var(--n-color-embedded);
  border-color: var(--n-border-color);
}

/* 高对比度模式 */
@media (prefers-contrast: high) {
  .trigger-button {
    border: 2px solid var(--n-border-color);
  }

  .hover-preview {
    border-width: 2px;
  }
}

/* 减少动画模式 */
@media (prefers-reduced-motion: reduce) {
  .trigger-button,
  .preview-fade-enter-active,
  .preview-fade-leave-active {
    transition: none;
  }

  .trigger-button.has-notification {
    animation: none;
  }
}
</style>
