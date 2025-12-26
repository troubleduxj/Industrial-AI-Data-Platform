<template>
  <NPopover trigger="click" placement="bottom-end" :width="360">
    <template #trigger>
      <NBadge :value="unreadCount" :max="99" :show="unreadCount > 0">
        <NButton quaternary circle>
          <template #icon>
            <TheIcon icon="material-symbols:notifications-outline" :size="20" />
          </template>
        </NButton>
      </NBadge>
    </template>

    <div class="notification-popover">
      <div class="notification-header">
        <span class="title">通知中心</span>
        <NButton v-if="unreadCount > 0" text size="small" @click="handleMarkAllRead">
          全部已读
        </NButton>
      </div>

      <div class="notification-list">
        <NSpin :show="loading">
          <template v-if="notifications.length > 0">
            <div
              v-for="item in notifications"
              :key="item.id"
              class="notification-item"
              :class="{ unread: !item.is_read }"
              @click="handleClick(item)"
            >
              <div class="notification-icon" :class="item.level">
                <TheIcon :icon="getIcon(item.notification_type)" :size="16" />
              </div>
              <div class="notification-content">
                <div class="notification-title">{{ item.title }}</div>
                <div class="notification-time">{{ formatTime(item.publish_time) }}</div>
              </div>
              <div v-if="!item.is_read" class="unread-dot"></div>
            </div>
          </template>
          <NEmpty v-else description="暂无通知" />
        </NSpin>
      </div>

      <div class="notification-footer">
        <NButton text block @click="goToNotificationCenter">
          查看全部通知
        </NButton>
      </div>
    </div>
  </NPopover>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { NPopover, NBadge, NButton, NSpin, NEmpty, useMessage } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { userNotificationApi } from '@/api/notification'
import { useUserStore } from '@/store'

const router = useRouter()
const message = useMessage()
const userStore = useUserStore()

const loading = ref(false)
const unreadCount = ref(0)
const notifications = ref([])
let refreshTimer = null

// 获取用户ID
const getUserId = () => {
  return userStore.userInfo?.id || 1
}

// 加载通知
const loadNotifications = async () => {
  loading.value = true
  try {
    const userId = getUserId()
    
    // 获取未读数量
    const countRes = await userNotificationApi.getUnreadCount(userId)
    if (countRes.success && countRes.data) {
      unreadCount.value = countRes.data.unread_count || 0
    }

    // 获取最近通知
    const listRes = await userNotificationApi.list({
      user_id: userId,
      page: 1,
      page_size: 5,
    })
    if (listRes.success && listRes.data) {
      notifications.value = listRes.data.items || listRes.data || []
    }
  } catch (error) {
    console.error('加载通知失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取图标
const getIcon = (type) => {
  const iconMap = {
    announcement: 'material-symbols:campaign',
    alarm: 'material-symbols:warning',
    task: 'material-symbols:task',
    system: 'material-symbols:info',
  }
  return iconMap[type] || 'material-symbols:notifications'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return date.toLocaleDateString()
}

// 点击通知
const handleClick = async (item) => {
  if (!item.is_read) {
    try {
      await userNotificationApi.markAsRead(item.id, getUserId())
      item.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }

  if (item.link_url) {
    router.push(item.link_url)
  }
}

// 全部标记已读
const handleMarkAllRead = async () => {
  try {
    const res = await userNotificationApi.markAllAsRead(getUserId())
    if (res.success) {
      message.success('已全部标记为已读')
      notifications.value.forEach((n) => (n.is_read = true))
      unreadCount.value = 0
    }
  } catch (error) {
    console.error('标记已读失败:', error)
    message.error('操作失败')
  }
}

// 跳转通知中心
const goToNotificationCenter = () => {
  router.push('/notification-center')
}

// 生命周期
onMounted(() => {
  loadNotifications()
  // 每分钟刷新一次
  refreshTimer = setInterval(loadNotifications, 60000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})

// 暴露刷新方法
defineExpose({
  refresh: loadNotifications,
})
</script>

<style scoped>
.notification-popover {
  margin: -12px;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.notification-header .title {
  font-weight: 600;
  font-size: 14px;
}

.notification-list {
  max-height: 320px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.notification-item:hover {
  background-color: #f5f5f5;
}

.notification-item.unread {
  background-color: #f0f9ff;
}

.notification-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
  background-color: #e6f7ff;
  color: #1890ff;
}

.notification-icon.warning {
  background-color: #fff7e6;
  color: #fa8c16;
}

.notification-icon.error {
  background-color: #fff1f0;
  color: #f5222d;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 14px;
  color: #333;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #f5222d;
  margin-left: 8px;
  flex-shrink: 0;
}

.notification-footer {
  padding: 8px 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
