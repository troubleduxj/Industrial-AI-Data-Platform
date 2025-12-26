import { defineStore } from 'pinia'
import { lStorage } from '@/utils'
import { getCachedConfig } from '@/api/index.js'

// 聊天记录存储key
const CHAT_HISTORY_KEY = 'chat_widget_history'
const CHAT_WIDGET_STATE_KEY = 'chat_widget_state'

export const useChatWidgetStore = defineStore('chatWidget', {
  state() {
    return {
      // 组件显示状态
      isVisible: true, // 是否可见
      displayMode: 'collapsed', // 显示模式: 'expanded' | 'collapsed' | 'floating'
      aiAssistantEnabled: true, // AI助手是否启用（从系统参数获取）

      // 浮动窗口状态
      floatingPosition: { x: 100, y: 100 }, // 浮动窗口位置
      floatingSize: { width: 1000, height: 650 }, // 浮动窗口大小
      isDragging: false, // 是否正在拖拽
      isResizing: false, // 是否正在调整大小
      isCollapsed: false, // 浮动窗口是否收缩
      collapsedWidth: 60, // 收缩时的宽度

      // 聊天相关状态
      chatHistory: [], // 聊天历史记录
      currentSessionId: null, // 当前会话ID
      isTyping: false, // AI是否正在输入
      inputMessage: '', // 当前输入内容

      // UI状态
      activeTab: 'chat', // 当前激活的标签: 'chat' | 'history' | 'menu'
      searchKeyword: '', // 搜索关键词

      // 功能菜单数据
      menuCards: [
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
          title: 'AI监测',
          description: '智能分析和预测性维护',
          icon: 'ant-design:robot-outlined',
          iconColor: '#eb2f96',
          route: '/ai-monitoring',
        },
      ],
    }
  },

  getters: {
    // 获取当前会话的消息
    currentSessionMessages: (state) => {
      if (!state.currentSessionId) return []
      const session = state.chatHistory.find((s) => s.id === state.currentSessionId)
      return session ? session.messages : []
    },

    // 获取聊天会话列表（用于历史记录显示）
    chatSessions: (state) => {
      return state.chatHistory.map((session) => ({
        id: session.id,
        title: session.title,
        lastMessage: session.messages[session.messages.length - 1]?.content || '',
        lastTime: session.lastTime,
        messageCount: session.messages.length,
      }))
    },

    // 过滤后的聊天会话（支持搜索）
    filteredChatSessions: (state) => {
      if (!state.searchKeyword) return state.chatHistory
      return state.chatHistory.filter(
        (session) =>
          session.title.toLowerCase().includes(state.searchKeyword.toLowerCase()) ||
          session.messages.some((msg) =>
            msg.content.toLowerCase().includes(state.searchKeyword.toLowerCase())
          )
      )
    },

    // 是否有聊天记录
    hasChatHistory: (state) => state.chatHistory.length > 0,

    // 是否应该显示浮动窗口
    shouldShowFloating: (state) =>
      state.displayMode === 'floating' && state.isVisible && state.aiAssistantEnabled,
  },

  actions: {
    // 初始化store，从本地存储加载数据
    async initStore() {
      const savedHistory = lStorage.get(CHAT_HISTORY_KEY)
      const savedState = lStorage.get(CHAT_WIDGET_STATE_KEY)

      if (savedHistory) {
        this.chatHistory = savedHistory
      }

      if (savedState) {
        this.displayMode = savedState.displayMode || 'collapsed'
        this.floatingPosition = savedState.floatingPosition || { x: 100, y: 100 }
        this.floatingSize = savedState.floatingSize || { width: 1000, height: 650 }
        this.currentSessionId = savedState.currentSessionId
        this.isCollapsed = savedState.isCollapsed || false
      }

      await this.fetchAiAssistantStatus()
    },

    // 获取AI助手启用状态
    async fetchAiAssistantStatus() {
      try {
        const response = await getCachedConfig('AI_ASSISTANT_ENABLED')
        if (response && response.data) {
          this.aiAssistantEnabled = response.data.param_value === 'true'
        }
      } catch (error) {
        console.error('Failed to fetch AI_ASSISTANT_ENABLED config:', error)
        // 如果获取失败，默认启用AI助手
        this.aiAssistantEnabled = true
      }
    },

    // 设置AI助手启用状态
    setAiAssistantEnabled(enabled) {
      this.aiAssistantEnabled = enabled
    },

    // 保存状态到本地存储
    saveToStorage() {
      lStorage.set(CHAT_HISTORY_KEY, this.chatHistory)
      lStorage.set(CHAT_WIDGET_STATE_KEY, {
        displayMode: this.displayMode,
        floatingPosition: this.floatingPosition,
        floatingSize: this.floatingSize,
        currentSessionId: this.currentSessionId,
        isCollapsed: this.isCollapsed,
      })
    },

    // 切换显示模式
    setDisplayMode(mode) {
      this.displayMode = mode
      this.saveToStorage()
    },

    // 切换可见性
    toggleVisibility() {
      this.isVisible = !this.isVisible
    },

    // 设置浮动窗口位置
    setFloatingPosition(position) {
      this.floatingPosition = { ...position }
      this.saveToStorage()
    },

    // 设置浮动窗口大小
    setFloatingSize(size) {
      this.floatingSize = { ...size }
      this.saveToStorage()
    },

    // 切换浮动窗口收缩状态
    toggleFloatingCollapse() {
      this.isCollapsed = !this.isCollapsed
      this.saveToStorage()
    },

    // 设置浮动窗口收缩状态
    setFloatingCollapse(collapsed) {
      this.isCollapsed = collapsed
      this.saveToStorage()
    },

    // 创建新的聊天会话
    createNewSession(title = '新对话') {
      const sessionId = Date.now().toString()
      const newSession = {
        id: sessionId,
        title,
        messages: [],
        createTime: new Date().toISOString(),
        lastTime: new Date().toISOString(),
      }

      this.chatHistory.unshift(newSession)
      this.currentSessionId = sessionId
      this.saveToStorage()

      return sessionId
    },

    // 切换到指定会话
    switchToSession(sessionId) {
      this.currentSessionId = sessionId
      this.saveToStorage()
    },

    // 删除会话
    deleteSession(sessionId) {
      const index = this.chatHistory.findIndex((s) => s.id === sessionId)
      if (index > -1) {
        this.chatHistory.splice(index, 1)

        // 如果删除的是当前会话，切换到第一个会话或创建新会话
        if (this.currentSessionId === sessionId) {
          if (this.chatHistory.length > 0) {
            this.currentSessionId = this.chatHistory[0].id
          } else {
            this.currentSessionId = null
          }
        }

        this.saveToStorage()
      }
    },

    // 添加消息到当前会话
    addMessage(message) {
      if (!this.currentSessionId) {
        this.createNewSession()
      }

      const session = this.chatHistory.find((s) => s.id === this.currentSessionId)
      if (session) {
        const newMessage = {
          id: Date.now().toString(),
          type: message.type, // 'user' | 'ai'
          content: message.content,
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          timestamp: new Date().toISOString(),
        }

        session.messages.push(newMessage)
        session.lastTime = new Date().toISOString()

        // 如果是第一条消息，更新会话标题
        if (session.messages.length === 1 && message.type === 'user') {
          session.title = message.content.slice(0, 20) + (message.content.length > 20 ? '...' : '')
        }

        this.saveToStorage()
      }
    },

    // 设置AI输入状态
    setTypingStatus(isTyping) {
      this.isTyping = isTyping
    },

    // 设置输入消息
    setInputMessage(message) {
      this.inputMessage = message
    },

    // 设置激活的标签
    setActiveTab(tab) {
      this.activeTab = tab
    },

    // 设置搜索关键词
    setSearchKeyword(keyword) {
      this.searchKeyword = keyword
    },

    // 清空所有聊天记录
    clearAllHistory() {
      this.chatHistory = []
      this.currentSessionId = null
      this.saveToStorage()
    },
  },
})
