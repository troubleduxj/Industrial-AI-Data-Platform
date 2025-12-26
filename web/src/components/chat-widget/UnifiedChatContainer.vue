<template>
  <div class="unified-chat-container">
    <!-- 左侧功能菜单 -->
    <div class="left-menu-panel" :class="{ collapsed: isLeftPanelCollapsed }">
      <!-- 左侧菜单栏 -->
      <div class="left-menu-header">
        <n-button
          quaternary
          size="small"
          class="collapse-btn"
          :title="isLeftPanelCollapsed ? '展开' : '收缩'"
          @click="toggleLeftPanel"
        >
          <Icon :icon="isLeftPanelCollapsed ? 'tabler:align-right-2' : 'tabler:align-left-2'" />
        </n-button>
      </div>
      <div v-if="!isLeftPanelCollapsed" class="menu-list">
        <div
          v-for="menu in menuData"
          :key="menu.id"
          class="menu-item-card"
          @click="handleMenuClick(menu)"
        >
          <div class="menu-item-icon" :style="{ background: getIconBackground(menu.iconColor) }">
            <Icon :icon="menu.icon" />
          </div>
          <div class="menu-item-content">
            <div class="menu-item-title">{{ menu.title }}</div>
            <div class="menu-item-description">{{ menu.description }}</div>
          </div>
        </div>
      </div>

      <!-- 收缩状态下的图标列表 -->
      <div v-else class="collapsed-menu-list">
        <div
          v-for="menu in menuData"
          :key="menu.id"
          class="collapsed-menu-item"
          :title="menu.title"
          @click="handleMenuClick(menu)"
        >
          <div
            class="collapsed-menu-icon"
            :style="{ background: getIconBackground(menu.iconColor) }"
          >
            <Icon :icon="menu.icon" />
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧聊天面板 -->
    <div class="right-chat-panel">
      <!-- 右侧菜单栏 -->
      <div class="right-menu-header">
        <div class="menu-header-title">
          <Icon icon="mdi:robot" class="menu-header-icon" />
          <span>AI 助手</span>
        </div>
        <div class="header-actions">
          <n-button quaternary size="small" class="action-btn" title="新建对话">
            <Icon icon="mdi:plus" />
          </n-button>
          <n-button quaternary size="small" class="action-btn" title="历史记录">
            <Icon icon="mdi:history" />
          </n-button>
        </div>
      </div>
      <!-- 聊天内容区域 -->
      <div class="chat-content">
        <!-- 聊天消息列表 -->
        <div v-if="chatWidgetStore.currentSessionMessages.length > 0" class="chat-messages">
          <div
            v-for="message in chatWidgetStore.currentSessionMessages"
            :key="message.id"
            class="message-item"
            :class="message.type"
          >
            <div class="message-avatar">
              <div v-if="message.type === 'ai'" class="robot-avatar">
                <Icon icon="mdi:robot" />
              </div>
              <div v-else class="user-avatar">
                <Icon icon="mdi:account" />
              </div>
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
        </div>

        <!-- 话题建议区域（初始化时显示） -->
        <div v-if="chatWidgetStore.currentSessionMessages.length === 0" class="suggestions-area">
          <h5>Suggested</h5>
          <div class="suggestions-list">
            <div
              v-for="suggestion in suggestions"
              :key="suggestion.id"
              class="suggestion-item"
              @click="handleSuggestionClick(suggestion)"
            >
              <Icon :icon="suggestion.icon" class="suggestion-icon" />
              <span class="suggestion-text">{{ suggestion.text }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 聊天输入区域 -->
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
            <Icon icon="mdi:send" />
          </n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useChatWidgetStore } from '@/store'
import { Icon } from '@iconify/vue'

const chatWidgetStore = useChatWidgetStore()
const isLeftPanelCollapsed = ref(false)

// 切换左侧面板收缩状态
const toggleLeftPanel = () => {
  isLeftPanelCollapsed.value = !isLeftPanelCollapsed.value
}

// 功能菜单数据
const menuData = [
  {
    id: 1,
    title: '监测看板',
    description: '实时监控设备状态和运行数据',
    icon: 'ant-design:dashboard-outlined',
    iconColor: '#1890ff',
    route: '/dashboard',
  },
  {
    id: 2,
    title: '数据统计',
    description: '设备数据分析和统计报表',
    icon: 'ant-design:bar-chart-outlined',
    iconColor: '#52c41a',
    route: '/statistics',
  },
  {
    id: 3,
    title: '告警中心',
    description: '设备异常告警和通知管理',
    icon: 'ant-design:bell-outlined',
    iconColor: '#fa8c16',
    route: '/alerts',
  },
  {
    id: 4,
    title: '流程编排',
    description: '自动化流程配置和管理',
    icon: 'ant-design:node-index-outlined',
    iconColor: '#722ed1',
    route: '/workflow',
  },
  {
    id: 5,
    title: 'AI监测',
    description: '智能分析和预测性维护',
    icon: 'ant-design:robot-outlined',
    iconColor: '#eb2f96',
    route: '/ai-monitoring',
  },
  {
    id: 6,
    title: '系统管理',
    description: '用户权限和系统配置管理',
    icon: 'ant-design:setting-outlined',
    iconColor: '#13c2c2',
    route: '/system',
  },
  {
    id: 7,
    title: '高级设置',
    description: '系统高级配置和维护工具',
    icon: 'ant-design:tool-outlined',
    iconColor: '#f5222d',
    route: '/advanced',
  },
]

// 建议列表
const suggestions = [
  {
    id: 1,
    text: '查看设备监控状态',
    icon: 'mdi:monitor-dashboard',
  },
  {
    id: 2,
    text: '生成数据分析报告',
    icon: 'mdi:chart-line',
  },
  {
    id: 3,
    text: '检查系统告警信息',
    icon: 'mdi:alert-circle',
  },
  {
    id: 4,
    text: '配置自动化流程',
    icon: 'mdi:cog',
  },
  {
    id: 5,
    text: 'AI智能诊断建议',
    icon: 'mdi:brain',
  },
]

// 获取图标背景渐变
const getIconBackground = (color) => {
  const colorMap = {
    '#1890ff': 'linear-gradient(135deg, #1890ff, #40a9ff)',
    '#52c41a': 'linear-gradient(135deg, #52c41a, #73d13d)',
    '#fa8c16': 'linear-gradient(135deg, #fa8c16, #ffa940)',
    '#eb2f96': 'linear-gradient(135deg, #eb2f96, #f759ab)',
    '#722ed1': 'linear-gradient(135deg, #722ed1, #9254de)',
    '#13c2c2': 'linear-gradient(135deg, #13c2c2, #36cfc9)',
    '#f5222d': 'linear-gradient(135deg, #f5222d, #ff4d4f)',
  }

  return colorMap[color] || `linear-gradient(135deg, ${color}, ${color}dd)`
}

// 处理菜单点击
const handleMenuClick = (menu) => {
  console.log('点击菜单:', menu.title)

  // 添加AI消息记录
  chatWidgetStore.addMessage({
    type: 'ai',
    content: `您点击了"${menu.title}"功能。${menu.description}`,
  })

  window.$message?.info(`即将跳转到${menu.title}页面`)
}

// 处理建议点击
const handleSuggestionClick = (suggestion) => {
  // 添加用户消息
  chatWidgetStore.addMessage({
    type: 'user',
    content: suggestion.text,
  })

  // 模拟AI回复
  chatWidgetStore.setTypingStatus(true)
  setTimeout(() => {
    const responses = {
      查看设备监控状态: '当前系统运行正常，所有设备状态良好。您可以在"监测看板"中查看详细信息。',
      生成数据分析报告:
        '正在为您生成最新的数据分析报告，请稍候。您也可以在"数据统计"模块中查看历史报告。',
      检查系统告警信息: '系统当前无严重告警，有2条提醒信息。详情请查看"告警中心"。',
      配置自动化流程: '自动化流程配置功能可以帮助您提高工作效率。请访问"流程编排"模块进行设置。',
      AI智能诊断建议: '基于当前数据分析，建议您关注设备温度变化趋势，可在"AI监测"中查看详细建议。',
    }

    const aiResponse =
      responses[suggestion.text] || `关于"${suggestion.text}"，我正在为您处理相关信息。`

    chatWidgetStore.addMessage({
      type: 'ai',
      content: aiResponse,
    })

    chatWidgetStore.setTypingStatus(false)
  }, 1000)
}

// 处理发送消息
const handleSendMessage = () => {
  const message = chatWidgetStore.inputMessage.trim()
  if (!message) return

  // 添加用户消息
  chatWidgetStore.addMessage({
    type: 'user',
    content: message,
  })

  // 清空输入框
  chatWidgetStore.setInputMessage('')

  // 模拟AI回复
  chatWidgetStore.setTypingStatus(true)
  setTimeout(() => {
    const aiResponse = `收到您的消息："${message}"。我正在为您处理相关信息，请稍候。`

    chatWidgetStore.addMessage({
      type: 'ai',
      content: aiResponse,
    })

    chatWidgetStore.setTypingStatus(false)
  }, 1000)
}

// 格式化时间
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
/* 统一聊天容器 */
.unified-chat-container {
  display: flex;
  height: 100%;
  background: var(--n-card-color);
  overflow: hidden;
}

/* 左侧菜单面板 */
.left-menu-panel {
  width: 280px;
  background: linear-gradient(135deg, #ffe4d6 0%, #ffd4b3 50%, #ffb380 100%);
  border-right: 1px solid var(--n-border-color);
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s ease;
}

.left-menu-panel.collapsed {
  width: 60px;
}

/* 左侧菜单栏 */
.left-menu-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  background: linear-gradient(135deg, #ffe4d6 0%, #ffd4b3 50%, #ffb380 100%);
  backdrop-filter: blur(10px);
}

.left-menu-panel.collapsed .left-menu-header {
  justify-content: center;
  padding: 12px 8px;
}

.menu-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.menu-header-icon {
  font-size: 18px;
  color: #ff8c42;
}

.collapse-btn {
  color: #666;
  transition: all 0.2s ease;
}

.collapse-btn:hover {
  color: #ff8c42;
  background: rgba(255, 140, 66, 0.1);
}

.left-menu-panel.collapsed .collapse-btn {
  /* 移除绝对定位，避免与菜单列表重叠 */
}

/* 收缩状态下的菜单列表 */
.collapsed-menu-list {
  padding: 8px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 0;
  min-height: 0;
}

.collapsed-menu-item {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 44px;
  height: 44px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.collapsed-menu-item:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.collapsed-menu-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

/* 右侧菜单栏 */
.right-menu-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-card-color);
  margin-bottom: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  color: var(--n-text-color-disabled);
  transition: all 0.2s ease;
}

.action-btn:hover {
  color: var(--n-primary-color);
  background: rgba(139, 92, 246, 0.1);
}

.menu-list {
  padding: 8px 16px 16px 16px;
  flex: 1;
  overflow-y: auto;
  color: #333;
  min-height: 0;
}

.menu-item-card {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  gap: 12px;
  align-items: center;
  text-align: left;
  backdrop-filter: blur(10px);
  color: #333;
}

.menu-item-card:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
  color: #333;
}

.menu-item-card.active {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(255, 255, 255, 0.8);
  color: #333;
  font-weight: 600;
}

.menu-item-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 20px;
  flex-shrink: 0;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.menu-item-content {
  flex: 1;
  min-width: 0;
}

.menu-item-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-item-description {
  font-size: 11px;
  color: #666;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 右侧聊天面板 */
.right-chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--n-card-color);
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
  overflow: hidden;
  min-width: 0;
  padding: 0 10%;
}

/* 聊天内容 */
.chat-content {
  flex: 1;
  padding: 8px 0 20px 0;
  overflow-y: auto;
  min-height: 0;
}

/* 聊天消息 */
.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.robot-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #a855f7, #9333ea);
  color: white;
  border: none;
  font-size: 18px;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar {
  background: #4f46e5;
  color: white !important;
  border-radius: 50%;
  width: 32px;
  height: 32px;
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
  flex: 1;
  max-width: 70%;
}

.message-item.user .message-content {
  flex: 0;
  max-width: 80%;
  width: fit-content;
  margin-left: auto;
}

.message-text {
  background: var(--n-color-embedded);
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  color: var(--n-text-color);
  border: 1px solid var(--n-border-color);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: relative;
  word-wrap: break-word;
  word-break: break-word;
  display: inline-block;
  min-width: 60px;
}

.message-item.user .message-text {
  background: var(--n-color-embedded);
  color: var(--n-text-color);
  border: 1px solid var(--n-border-color);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.message-time {
  font-size: 12px;
  color: var(--n-text-color-disabled);
  margin-top: 4px;
  padding: 0 16px;
  white-space: nowrap;
  text-align: right;
}

.message-item.user .message-time {
  text-align: right;
}

/* 建议区域 */
.suggestions-area {
  text-align: center;
}

.suggestions-area h5 {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color);
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 400px;
  margin: 0 auto;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--n-color-embedded);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.suggestion-item:hover {
  border-color: var(--n-primary-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.suggestion-icon {
  font-size: 16px;
  color: var(--n-primary-color);
  margin-right: 12px;
  flex-shrink: 0;
}

.suggestion-text {
  color: var(--n-text-color);
  font-size: 14px;
  text-align: left;
}

/* 输入区域 */
.chat-input-area {
  padding: 12px 0 20px 0;
  border-top: 1px solid var(--n-border-color);
  background: var(--n-color-embedded);
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  justify-content: center;
}

.chat-input {
  width: 80%;
  height: 80px;
  border-radius: 12px;
}

.send-button {
  flex-shrink: 0;
  height: 40px;
  width: 40px;
  border-radius: 8px;
}
</style>
