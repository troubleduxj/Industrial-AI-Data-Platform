<template>
  <div class="alert-notification-container">
    <!-- 告警徽章 -->
    <n-badge :value="unreadCount" :max="99" :show="unreadCount > 0">
      <n-button 
        :type="hasActiveAlerts ? 'error' : 'default'" 
        size="small"
        @click="showDrawer = true"
      >
        <template #icon>
          <n-icon :component="NotificationsOutline" :class="{ 'alert-icon-pulse': hasActiveAlerts }" />
        </template>
        告警
      </n-button>
    </n-badge>

    <!-- 实时告警弹窗 -->
    <n-notification-provider>
      <div ref="notificationContainer"></div>
    </n-notification-provider>

    <!-- 告警抽屉 -->
    <n-drawer v-model:show="showDrawer" :width="400" placement="right">
      <n-drawer-content title="实时告警" closable>
        <template #header-extra>
          <n-space>
            <n-button size="small" @click="markAllAsRead" :disabled="unreadCount === 0">
              全部已读
            </n-button>
            <n-button size="small" @click="clearAlerts" :disabled="alerts.length === 0">
              清空
            </n-button>
          </n-space>
        </template>

        <!-- 告警过滤 -->
        <div class="alert-filters">
          <n-select
            v-model:value="filterLevel"
            :options="levelOptions"
            placeholder="告警级别"
            size="small"
            clearable
            style="width: 120px"
          />
          <n-input
            v-model:value="searchKeyword"
            placeholder="搜索告警"
            size="small"
            clearable
            style="flex: 1"
          >
            <template #prefix>
              <n-icon :component="SearchOutline" />
            </template>
          </n-input>
        </div>

        <!-- 告警列表 -->
        <n-scrollbar style="max-height: calc(100vh - 200px)">
          <div v-if="filteredAlerts.length === 0" class="empty-alerts">
            <n-empty description="暂无告警" />
          </div>
          <div v-else class="alert-list">
            <div
              v-for="alert in filteredAlerts"
              :key="alert.id"
              class="alert-item"
              :class="[`alert-item--${alert.level}`, { 'alert-item--unread': !alert.read }]"
              @click="handleAlertClick(alert)"
            >
              <div class="alert-icon">
                <n-icon :component="getAlertIcon(alert.level)" :color="getAlertColor(alert.level)" :size="20" />
              </div>
              <div class="alert-content">
                <div class="alert-header">
                  <span class="alert-title">{{ alert.title }}</span>
                  <n-tag :type="getLevelTagType(alert.level)" size="small">
                    {{ getLevelText(alert.level) }}
                  </n-tag>
                </div>
                <div class="alert-message">{{ alert.message }}</div>
                <div class="alert-meta">
                  <span v-if="alert.asset_name">{{ alert.asset_name }}</span>
                  <span>{{ formatTime(alert.timestamp) }}</span>
                </div>
              </div>
              <div class="alert-actions">
                <n-button text size="small" @click.stop="dismissAlert(alert.id)">
                  <n-icon :component="CloseOutline" />
                </n-button>
              </div>
            </div>
          </div>
        </n-scrollbar>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
/**
 * 告警通知组件
 * 
 * 需求: 7.4 - 当告警触发时，前端应实时显示告警通知
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { 
  NButton, NIcon, NBadge, NDrawer, NDrawerContent, NSpace, 
  NSelect, NInput, NScrollbar, NEmpty, NTag, useNotification 
} from 'naive-ui'
import { 
  NotificationsOutline, SearchOutline, CloseOutline,
  WarningOutline, AlertCircleOutline, InformationCircleOutline, CheckmarkCircleOutline
} from '@vicons/ionicons5'

// Props
const props = defineProps({
  // 告警数据
  alerts: {
    type: Array,
    default: () => []
  },
  // 最大显示数量
  maxAlerts: {
    type: Number,
    default: 100
  },
  // 是否显示桌面通知
  showDesktopNotification: {
    type: Boolean,
    default: true
  },
  // 是否播放声音
  playSound: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['alert-click', 'alert-dismiss', 'alerts-clear'])

const notification = useNotification()
const showDrawer = ref(false)
const filterLevel = ref(null)
const searchKeyword = ref('')

// 内部告警列表（带已读状态）
const internalAlerts = ref([])

// 级别选项
const levelOptions = [
  { label: '紧急', value: 'critical' },
  { label: '警告', value: 'warning' },
  { label: '信息', value: 'info' }
]

// 未读数量
const unreadCount = computed(() => {
  return internalAlerts.value.filter(a => !a.read).length
})

// 是否有活跃告警
const hasActiveAlerts = computed(() => {
  return internalAlerts.value.some(a => a.level === 'critical' || a.level === 'warning')
})

// 过滤后的告警
const filteredAlerts = computed(() => {
  let result = [...internalAlerts.value]
  
  if (filterLevel.value) {
    result = result.filter(a => a.level === filterLevel.value)
  }
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(a => 
      a.title?.toLowerCase().includes(keyword) ||
      a.message?.toLowerCase().includes(keyword) ||
      a.asset_name?.toLowerCase().includes(keyword)
    )
  }
  
  return result.slice(0, props.maxAlerts)
})

// 获取告警图标
function getAlertIcon(level) {
  switch (level) {
    case 'critical': return AlertCircleOutline
    case 'warning': return WarningOutline
    case 'info': return InformationCircleOutline
    default: return CheckmarkCircleOutline
  }
}

// 获取告警颜色
function getAlertColor(level) {
  switch (level) {
    case 'critical': return '#d03050'
    case 'warning': return '#f0a020'
    case 'info': return '#2080f0'
    default: return '#18a058'
  }
}

// 获取级别标签类型
function getLevelTagType(level) {
  switch (level) {
    case 'critical': return 'error'
    case 'warning': return 'warning'
    case 'info': return 'info'
    default: return 'success'
  }
}

// 获取级别文本
function getLevelText(level) {
  switch (level) {
    case 'critical': return '紧急'
    case 'warning': return '警告'
    case 'info': return '信息'
    default: return '正常'
  }
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return date.toLocaleString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 显示实时通知
function showRealtimeNotification(alert) {
  const notificationConfig = {
    title: alert.title || '新告警',
    content: alert.message,
    duration: alert.level === 'critical' ? 0 : 5000,
    closable: true,
    meta: alert.asset_name || ''
  }
  
  switch (alert.level) {
    case 'critical':
      notification.error(notificationConfig)
      break
    case 'warning':
      notification.warning(notificationConfig)
      break
    case 'info':
      notification.info(notificationConfig)
      break
    default:
      notification.success(notificationConfig)
  }
  
  // 桌面通知
  if (props.showDesktopNotification && Notification.permission === 'granted') {
    new Notification(alert.title || '新告警', {
      body: alert.message,
      icon: '/favicon.ico',
      tag: alert.id
    })
  }
  
  // 播放声音
  if (props.playSound && alert.level === 'critical') {
    playAlertSound()
  }
}

// 播放告警声音
function playAlertSound() {
  try {
    const audio = new Audio('/sounds/alert.mp3')
    audio.volume = 0.5
    audio.play().catch(() => {})
  } catch (e) {
    // 忽略音频播放错误
  }
}

// 处理告警点击
function handleAlertClick(alert) {
  // 标记为已读
  alert.read = true
  emit('alert-click', alert)
}

// 关闭告警
function dismissAlert(alertId) {
  const index = internalAlerts.value.findIndex(a => a.id === alertId)
  if (index > -1) {
    internalAlerts.value.splice(index, 1)
    emit('alert-dismiss', alertId)
  }
}

// 标记全部已读
function markAllAsRead() {
  internalAlerts.value.forEach(a => { a.read = true })
}

// 清空告警
function clearAlerts() {
  internalAlerts.value = []
  emit('alerts-clear')
}

// 添加新告警
function addAlert(alert) {
  const newAlert = {
    id: alert.id || Date.now().toString(),
    title: alert.title || '系统告警',
    message: alert.message || '',
    level: alert.level || 'info',
    asset_id: alert.asset_id,
    asset_name: alert.asset_name,
    timestamp: alert.timestamp || new Date().toISOString(),
    read: false,
    data: alert.data
  }
  
  // 添加到列表开头
  internalAlerts.value.unshift(newAlert)
  
  // 限制数量
  if (internalAlerts.value.length > props.maxAlerts) {
    internalAlerts.value = internalAlerts.value.slice(0, props.maxAlerts)
  }
  
  // 显示通知
  showRealtimeNotification(newAlert)
}

// 监听外部告警数据变化
watch(() => props.alerts, (newAlerts, oldAlerts) => {
  if (!newAlerts || newAlerts.length === 0) return
  
  // 找出新增的告警
  const existingIds = new Set(internalAlerts.value.map(a => a.id))
  const newItems = newAlerts.filter(a => !existingIds.has(a.id))
  
  newItems.forEach(alert => {
    addAlert(alert)
  })
}, { deep: true })

// 请求桌面通知权限
onMounted(() => {
  if (props.showDesktopNotification && Notification.permission === 'default') {
    Notification.requestPermission()
  }
})

// 暴露方法
defineExpose({
  addAlert,
  markAllAsRead,
  clearAlerts,
  dismissAlert
})
</script>

<style scoped>
.alert-notification-container {
  display: inline-block;
}

.alert-icon-pulse {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.alert-filters {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.empty-alerts {
  padding: 40px 0;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: var(--n-card-color);
  border: 1px solid var(--n-border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.alert-item:hover {
  background: var(--n-color-hover);
}

.alert-item--unread {
  border-left: 3px solid var(--n-primary-color);
}

.alert-item--critical {
  background: rgba(208, 48, 80, 0.05);
  border-color: rgba(208, 48, 80, 0.3);
}

.alert-item--warning {
  background: rgba(240, 160, 32, 0.05);
  border-color: rgba(240, 160, 32, 0.3);
}

.alert-icon {
  flex-shrink: 0;
  padding-top: 2px;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.alert-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--n-text-color);
}

.alert-message {
  font-size: 13px;
  color: var(--n-text-color-2);
  margin-bottom: 8px;
  word-break: break-word;
}

.alert-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--n-text-color-3);
}

.alert-actions {
  flex-shrink: 0;
}
</style>
