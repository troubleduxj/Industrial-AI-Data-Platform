<template>
  <div class="chat-history-list">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <n-input
        v-model:value="chatWidgetStore.searchKeyword"
        placeholder="搜索对话记录..."
        clearable
        @update:value="chatWidgetStore.setSearchKeyword"
      >
        <template #prefix>
          <Icon icon="mdi:magnify" />
        </template>
      </n-input>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <n-button size="small" type="primary" class="new-chat-btn" @click="createNewChat">
        <Icon icon="mdi:plus" />
        新建对话
      </n-button>

      <n-dropdown :options="moreOptions" trigger="click" @select="handleMoreAction">
        <n-button size="small" quaternary>
          <Icon icon="mdi:dots-vertical" />
        </n-button>
      </n-dropdown>
    </div>

    <!-- 历史记录列表 -->
    <div class="history-content">
      <div v-if="filteredSessions.length === 0" class="empty-state">
        <div class="empty-icon">
          <Icon icon="mdi:chat-outline" />
        </div>
        <p v-if="chatWidgetStore.searchKeyword">未找到匹配的对话记录</p>
        <p v-else>暂无对话记录</p>
        <n-button
          v-if="!chatWidgetStore.searchKeyword"
          size="small"
          type="primary"
          ghost
          @click="createNewChat"
        >
          开始新对话
        </n-button>
      </div>

      <div v-else class="sessions-list">
        <div
          v-for="session in filteredSessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === chatWidgetStore.currentSessionId }"
          @click="selectSession(session.id)"
        >
          <div class="session-content">
            <div class="session-header">
              <h4 class="session-title">{{ session.title }}</h4>
              <span class="session-time">{{ formatTime(session.lastTime) }}</span>
            </div>

            <p class="session-preview">{{ session.lastMessage }}</p>

            <div class="session-meta">
              <span class="message-count">
                <Icon icon="mdi:message-outline" />
                {{ session.messageCount }} 条消息
              </span>
            </div>
          </div>

          <div class="session-actions">
            <n-dropdown
              :options="getSessionOptions(session)"
              trigger="click"
              @select="(key) => handleSessionAction(key, session)"
              @click.stop
            >
              <n-button size="tiny" quaternary>
                <Icon icon="mdi:dots-vertical" />
              </n-button>
            </n-dropdown>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useChatWidgetStore } from '@/store'
import { Icon } from '@iconify/vue'

const chatWidgetStore = useChatWidgetStore()

// 过滤后的会话列表
const filteredSessions = computed(() => {
  return chatWidgetStore.filteredChatSessions
})

// 更多操作选项
const moreOptions = [
  {
    label: '清空所有记录',
    key: 'clear-all',
    icon: () => h(Icon, { icon: 'mdi:delete-outline' }),
  },
  {
    label: '导出记录',
    key: 'export',
    icon: () => h(Icon, { icon: 'mdi:download-outline' }),
  },
]

// 创建新对话
const createNewChat = () => {
  const sessionId = chatWidgetStore.createNewSession()
  chatWidgetStore.setActiveTab('chat')
}

// 选择会话
const selectSession = (sessionId) => {
  chatWidgetStore.switchToSession(sessionId)
  chatWidgetStore.setActiveTab('chat')
}

// 获取会话操作选项
const getSessionOptions = (session) => {
  return [
    {
      label: '重命名',
      key: 'rename',
      icon: () => h(Icon, { icon: 'mdi:pencil-outline' }),
    },
    {
      label: '复制内容',
      key: 'copy',
      icon: () => h(Icon, { icon: 'mdi:content-copy' }),
    },
    {
      type: 'divider',
    },
    {
      label: '删除',
      key: 'delete',
      icon: () => h(Icon, { icon: 'mdi:delete-outline' }),
      props: {
        style: 'color: var(--n-error-color)',
      },
    },
  ]
}

// 处理更多操作
const handleMoreAction = (key) => {
  switch (key) {
    case 'clear-all':
      $dialog.warning({
        title: '确认清空',
        content: '确定要清空所有对话记录吗？此操作不可恢复。',
        positiveText: '确定',
        negativeText: '取消',
        onPositiveClick: () => {
          chatWidgetStore.clearAllHistory()
          $message.success('已清空所有记录')
        },
      })
      break
    case 'export':
      exportChatHistory()
      break
  }
}

// 处理会话操作
const handleSessionAction = (key, session) => {
  switch (key) {
    case 'rename':
      renameSession(session)
      break
    case 'copy':
      copySessionContent(session)
      break
    case 'delete':
      deleteSession(session)
      break
  }
}

// 重命名会话
const renameSession = (session) => {
  $dialog.create({
    title: '重命名对话',
    content: () => {
      const inputRef = ref(session.title)
      return h('div', [
        h(
          'p',
          { style: 'margin-bottom: 12px; color: var(--n-text-color-disabled)' },
          '请输入新的对话名称：'
        ),
        h(NInput, {
          value: inputRef.value,
          'onUpdate:value': (val) => {
            inputRef.value = val
          },
          placeholder: '对话名称',
          maxlength: 50,
          showCount: true,
        }),
      ])
    },
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      // 这里需要在store中添加重命名方法
      $message.success('重命名成功')
    },
  })
}

// 复制会话内容
const copySessionContent = (session) => {
  const sessionData = chatWidgetStore.chatHistory.find((s) => s.id === session.id)
  if (!sessionData) return

  const content = sessionData.messages
    .map((msg) => {
      const sender = msg.type === 'user' ? '用户' : 'AI助手'
      return `${sender}: ${msg.content}`
    })
    .join('\n\n')

  navigator.clipboard
    .writeText(content)
    .then(() => {
      $message.success('已复制到剪贴板')
    })
    .catch(() => {
      $message.error('复制失败')
    })
}

// 删除会话
const deleteSession = (session) => {
  $dialog.warning({
    title: '确认删除',
    content: `确定要删除对话"${session.title}"吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => {
      chatWidgetStore.deleteSession(session.id)
      $message.success('已删除对话')
    },
  })
}

// 导出聊天记录
const exportChatHistory = () => {
  const data = {
    exportTime: new Date().toISOString(),
    sessions: chatWidgetStore.chatHistory,
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-history-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  $message.success('导出成功')
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
  } else if (diff < 604800000) {
    // 7天内
    return `${Math.floor(diff / 86400000)}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}
</script>

<style scoped>
.chat-history-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--n-card-color);
}

/* 搜索栏 */
.search-bar {
  padding: 16px;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-color-embedded);
}

/* 操作栏 */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-color-embedded);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 历史记录内容 */
.history-content {
  flex: 1;
  overflow: hidden;
}

/* 空状态 */
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--n-color-embedded);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-icon .iconify {
  font-size: 32px;
  color: var(--n-text-color-disabled);
}

.empty-state p {
  margin: 0 0 16px 0;
  color: var(--n-text-color-disabled);
  font-size: 14px;
}

/* 会话列表 */
.sessions-list {
  height: 100%;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  position: relative;
}

.session-item:hover {
  background: var(--n-color-embedded);
  border-color: var(--n-border-color);
}

.session-item.active {
  background: var(--n-primary-color-suppl);
  border-color: var(--n-primary-color);
}

.session-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--n-primary-color);
  border-radius: 0 2px 2px 0;
}

.session-content {
  flex: 1;
  min-width: 0;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.session-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--n-text-color);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}

.session-time {
  font-size: 11px;
  color: var(--n-text-color-disabled);
  flex-shrink: 0;
}

.session-preview {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: var(--n-text-color-disabled);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.message-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--n-text-color-disabled);
}

.session-actions {
  flex-shrink: 0;
  margin-left: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.session-item:hover .session-actions {
  opacity: 1;
}

/* 滚动条样式 */
.sessions-list::-webkit-scrollbar {
  width: 4px;
}

.sessions-list::-webkit-scrollbar-track {
  background: transparent;
}

.sessions-list::-webkit-scrollbar-thumb {
  background: var(--n-scrollbar-color);
  border-radius: 2px;
}

.sessions-list::-webkit-scrollbar-thumb:hover {
  background: var(--n-scrollbar-color-hover);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-bar,
  .action-bar {
    padding: 12px;
  }

  .session-item {
    padding: 10px;
  }

  .session-title {
    font-size: 13px;
  }

  .session-preview {
    font-size: 11px;
  }
}

/* 暗色主题适配 */
.dark .session-item:hover {
  background: var(--n-color-embedded);
}

.dark .session-item.active {
  background: var(--n-primary-color-suppl);
}

/* 高对比度模式 */
@media (prefers-contrast: high) {
  .session-item {
    border-width: 2px;
  }

  .session-item.active {
    border-width: 2px;
  }
}
</style>
