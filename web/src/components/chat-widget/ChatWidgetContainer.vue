<template>
  <div class="chat-widget-container">
    <!-- 标签页导航 -->
    <div v-if="chatWidgetStore.hasChatHistory" class="tab-navigation">
      <n-tabs
        v-model:value="chatWidgetStore.activeTab"
        type="line"
        size="small"
        @update:value="chatWidgetStore.setActiveTab"
      >
        <n-tab-pane name="chat" tab="当前对话">
          <template #tab>
            <div class="tab-item">
              <Icon icon="mdi:chat" />
              <span>当前对话</span>
            </div>
          </template>
        </n-tab-pane>
        <n-tab-pane name="history" tab="历史记录">
          <template #tab>
            <div class="tab-item">
              <Icon icon="mdi:history" />
              <span>历史记录</span>
              <n-badge
                v-if="chatWidgetStore.chatSessions.length > 0"
                :value="chatWidgetStore.chatSessions.length"
                :max="99"
                size="small"
              />
            </div>
          </template>
        </n-tab-pane>
        <n-tab-pane name="menu" tab="功能菜单">
          <template #tab>
            <div class="tab-item">
              <Icon icon="mdi:apps" />
              <span>功能菜单</span>
            </div>
          </template>
        </n-tab-pane>
      </n-tabs>
    </div>

    <!-- 内容区域 -->
    <div class="content-area">
      <!-- 当前对话标签页 -->
      <div
        v-if="chatWidgetStore.activeTab === 'chat' || !chatWidgetStore.hasChatHistory"
        class="chat-content"
      >
        <!-- 聊天消息区域 -->
        <div class="chat-messages-container">
          <!-- 欢迎消息（无聊天记录时） -->
          <div v-if="!chatWidgetStore.hasChatHistory" class="welcome-message">
            <div class="welcome-icon">
              <Icon icon="mdi:robot" />
            </div>
            <h4>你好！我是AI助手</h4>
            <p>请选择功能菜单或直接向我提问</p>
          </div>

          <!-- 建议区域（无聊天记录时） -->
          <div v-if="!chatWidgetStore.hasChatHistory" class="suggestions-area">
            <div class="suggestions-header">
              <h5>Suggested:</h5>
            </div>
            <div class="suggestions-list">
              <div
                v-for="(suggestion, index) in suggestions"
                :key="index"
                class="suggestion-item"
                @click="handleSuggestionClick(suggestion)"
              >
                <span class="suggestion-number">{{ index + 1 }}）</span>
                <span class="suggestion-text">{{ suggestion.text }}</span>
              </div>
            </div>
          </div>

          <!-- 消息列表 -->
          <div
            v-if="chatWidgetStore.currentSessionMessages.length > 0"
            ref="messagesListRef"
            class="messages-list"
          >
            <div
              v-for="message in chatWidgetStore.currentSessionMessages"
              :key="message.id"
              class="message-item"
              :class="message.type"
            >
              <div class="message-avatar">
                <div v-if="message.type === 'ai'" class="robot-avatar">
                  <Icon icon="mdi:robot" class="robot-icon" />
                </div>
                <div v-else class="user-avatar">
                  <Icon icon="mdi:account" />
                </div>
              </div>
              <div class="message-content">
                <div class="message-text">{{ message.content }}</div>
                <div class="message-time">{{ message.time }}</div>
              </div>
            </div>

            <!-- AI 打字指示器 -->
            <div v-if="chatWidgetStore.isTyping" class="message-item ai">
              <div class="message-avatar">
                <div class="robot-avatar">
                  <Icon icon="mdi:robot" class="robot-icon" />
                </div>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入框区域 -->
        <div class="chat-input-area">
          <div class="input-container">
            <n-input
              v-model:value="chatWidgetStore.inputMessage"
              type="textarea"
              placeholder="输入消息..."
              :autosize="{ minRows: 1, maxRows: 4 }"
              class="chat-input"
              @keydown.enter.prevent="handleSendMessage"
            />
            <n-button
              type="primary"
              :loading="chatWidgetStore.isTyping"
              class="send-button"
              :disabled="!chatWidgetStore.inputMessage.trim()"
              @click="handleSendMessage"
            >
              <Icon icon="ant-design:send-outlined" />
            </n-button>
          </div>
        </div>
      </div>

      <!-- 历史记录标签页 -->
      <div v-if="chatWidgetStore.activeTab === 'history'" class="history-content">
        <ChatHistoryList />
      </div>

      <!-- 功能菜单标签页 -->
      <div v-if="chatWidgetStore.activeTab === 'menu'" class="menu-content">
        <MenuCardGrid />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted } from 'vue'
import { useChatWidgetStore, useUserStore } from '@/store'
import { Icon } from '@iconify/vue'
import { useRouter } from 'vue-router'
import ChatHistoryList from './ChatHistoryList.vue'
import MenuCardGrid from './MenuCardGrid.vue'

const chatWidgetStore = useChatWidgetStore()
const userStore = useUserStore()
const router = useRouter()
const messagesListRef = ref(null)

// 用户头像
const userAvatar = computed(() => userStore.avatar || '/default-avatar.png')

// 建议列表数据
const suggestions = [
  { text: '查看设备监控状态', action: 'device-status' },
  { text: '生成数据分析报告', action: 'data-report' },
  { text: '检查系统告警信息', action: 'check-alerts' },
  { text: '配置自动化流程', action: 'setup-workflow' },
  { text: 'AI智能诊断建议', action: 'ai-diagnosis' },
]

// 处理发送消息
const handleSendMessage = async () => {
  const message = chatWidgetStore.inputMessage.trim()
  if (!message || chatWidgetStore.isTyping) return

  // 添加用户消息
  chatWidgetStore.addMessage({
    type: 'user',
    content: message,
  })

  // 清空输入框
  chatWidgetStore.setInputMessage('')

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 模拟AI回复
  chatWidgetStore.setTypingStatus(true)

  setTimeout(() => {
    const aiResponse = getAIResponse(message)
    chatWidgetStore.addMessage({
      type: 'ai',
      content: aiResponse,
    })

    chatWidgetStore.setTypingStatus(false)

    // 滚动到底部
    nextTick(() => {
      scrollToBottom()
    })
  }, 1500)
}

// 滚动到消息列表底部
const scrollToBottom = () => {
  if (messagesListRef.value) {
    messagesListRef.value.scrollTop = messagesListRef.value.scrollHeight
  }
}

// 模拟AI回复逻辑
const getAIResponse = (question) => {
  const responses = {
    设备: '关于设备监控，您可以通过"监测看板"查看实时设备状态，或使用"数据统计"分析设备运行数据。',
    告警: '告警功能可以在"告警中心"中查看和管理。系统会自动检测设备异常并发送通知。',
    数据: '数据相关功能包括实时监控和历史数据分析，您可以在"数据统计"模块中查看详细报表。',
    流程: '"流程编排"功能可以帮助您配置自动化工作流程，提高运维效率。',
    AI: 'AI监测功能提供智能分析和预测性维护，帮助您提前发现潜在问题。',
    系统: '系统管理包括用户权限、角色配置等功能，您可以在"系统管理"中进行相关设置。',
  }

  for (const [key, response] of Object.entries(responses)) {
    if (question.includes(key)) {
      return response
    }
  }

  return '感谢您的提问！我会尽力帮助您。如果您需要使用特定功能，可以点击功能菜单进行操作。'
}

// 处理建议点击
const handleSuggestionClick = (suggestion) => {
  console.log('点击建议:', suggestion.text)

  // 将建议作为用户消息添加到聊天中
  chatWidgetStore.addMessage({
    type: 'user',
    content: suggestion.text,
  })

  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })

  // 模拟AI回复
  chatWidgetStore.setTypingStatus(true)

  setTimeout(() => {
    const aiResponse = getAIResponse(suggestion.text)
    chatWidgetStore.addMessage({
      type: 'ai',
      content: aiResponse,
    })

    chatWidgetStore.setTypingStatus(false)
    nextTick(() => {
      scrollToBottom()
    })
  }, 1000)
}

// 处理快速操作
const handleQuickAction = (menu) => {
  // 添加AI消息
  chatWidgetStore.addMessage({
    type: 'ai',
    content: `您点击了"${menu.title}"功能。${menu.description}`,
  })

  // 可以在这里添加路由跳转逻辑
  // router.push(menu.route)
  window.$message?.info(`即将跳转到${menu.title}页面`)
}

// 组件挂载时滚动到底部
onMounted(() => {
  nextTick(() => {
    scrollToBottom()
  })
})
</script>

<style scoped>
.chat-widget-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--n-card-color);
}

/* 标签页导航 */
.tab-navigation {
  padding: 12px 16px 0;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-color-embedded);
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

/* 内容区域 */
.content-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 聊天内容 */
.chat-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-messages-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 欢迎消息 */
.welcome-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--n-primary-color), var(--n-primary-color-hover));
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.welcome-icon .iconify {
  font-size: 40px;
  color: white;
}

.welcome-message h4 {
  margin: 0 0 12px 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--n-text-color);
}

.welcome-message p {
  margin: 0 0 24px 0;
  font-size: 14px;
  color: var(--n-text-color-disabled);
  line-height: 1.5;
}

/* 建议区域样式 */
.suggestions-area {
  padding: 20px;
  border-bottom: 1px solid var(--n-border-color);
}

.suggestions-header {
  margin-bottom: 16px;
}

.suggestions-header h5 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--n-text-color);
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  background: var(--n-color-embedded);
  border: 1px solid var(--n-border-color);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.suggestion-item:hover {
  border-color: var(--n-primary-color);
  background: var(--n-primary-color-suppl);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.suggestion-number {
  color: var(--n-primary-color);
  font-weight: 600;
  margin-right: 8px;
  flex-shrink: 0;
}

.suggestion-text {
  color: var(--n-text-color);
  line-height: 1.4;
}

/* 快速建议样式 */
.quick-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 20px;
}

.suggestion-btn {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 16px;
  border: 1px solid var(--n-border-color);
  background: var(--n-color-embedded);
  transition: all 0.3s ease;
}

.suggestion-btn:hover {
  border-color: var(--n-primary-color);
  background: var(--n-primary-color-suppl);
  color: var(--n-primary-color);
  transform: translateY(-1px);
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.quick-action-btn:hover {
  background: var(--n-primary-color-hover);
  color: white;
}

/* 消息列表 */
.messages-list {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.message-item {
  display: flex;
  margin-bottom: 16px;
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.user {
  justify-content: flex-end;
}

.message-item.ai {
  justify-content: flex-start;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 8px;
  flex-shrink: 0;
}

.robot-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #a855f7, #9333ea);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.robot-icon {
  font-size: 18px;
  color: white;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #4f46e5;
  color: white !important;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
}

.user-avatar .iconify {
  color: white !important;
  font-size: 16px !important;
}

.message-content {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 16px;
  background: var(--n-color-embedded);
  border: 1px solid var(--n-border-color);
  position: relative;
}

.message-item.user .message-content {
  background: var(--n-color-embedded);
  color: var(--n-text-color);
  border-color: var(--n-border-color);
}

.message-text {
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-item.user .message-text {
  color: var(--n-text-color);
}

.message-time {
  font-size: 11px;
  color: var(--n-text-color-disabled);
  margin-top: 4px;
}

.message-item.user .message-time {
  color: rgba(255, 255, 255, 0.8);
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--n-text-color-disabled);
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 输入框区域 */
.chat-input-area {
  padding: 16px;
  border-top: 1px solid var(--n-border-color);
  background: var(--n-color-embedded);
}

.input-container {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
}

.send-button {
  flex-shrink: 0;
  height: 36px;
  width: 36px;
  border-radius: 8px;
}

/* 历史记录和菜单内容 */
.history-content,
.menu-content {
  flex: 1;
  overflow: hidden;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .welcome-message {
    padding: 20px 16px;
  }

  .welcome-icon {
    width: 60px;
    height: 60px;
  }

  .welcome-icon .iconify {
    font-size: 30px;
  }

  .welcome-message h4 {
    font-size: 18px;
  }

  .quick-actions {
    flex-direction: column;
    align-items: center;
  }

  .message-content {
    max-width: 85%;
  }
}
</style>
