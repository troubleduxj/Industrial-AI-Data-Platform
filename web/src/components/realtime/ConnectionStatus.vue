<template>
  <div class="connection-status" :class="statusClass">
    <!-- 简洁模式 -->
    <template v-if="mode === 'compact'">
      <n-tooltip :disabled="!showTooltip">
        <template #trigger>
          <div class="status-indicator" :class="statusClass">
            <span class="status-dot" :class="{ 'pulse': isPulsing }"></span>
            <span v-if="showLabel" class="status-label">{{ statusText }}</span>
          </div>
        </template>
        <div class="status-tooltip">
          <div class="tooltip-row">
            <span>状态:</span>
            <span>{{ statusText }}</span>
          </div>
          <div v-if="reconnectAttempts > 0" class="tooltip-row">
            <span>重连次数:</span>
            <span>{{ reconnectAttempts }}</span>
          </div>
          <div v-if="lastConnectedTime" class="tooltip-row">
            <span>上次连接:</span>
            <span>{{ formatTime(lastConnectedTime) }}</span>
          </div>
        </div>
      </n-tooltip>
    </template>

    <!-- 详细模式 -->
    <template v-else-if="mode === 'detailed'">
      <n-card size="small" class="status-card">
        <div class="status-header">
          <div class="status-indicator" :class="statusClass">
            <span class="status-dot" :class="{ 'pulse': isPulsing }"></span>
            <span class="status-label">{{ statusText }}</span>
          </div>
          <n-button-group size="small">
            <n-button 
              v-if="state === 'disconnected' || state === 'error'" 
              type="primary"
              @click="$emit('connect')"
            >
              连接
            </n-button>
            <n-button 
              v-else-if="state === 'connected'" 
              @click="$emit('disconnect')"
            >
              断开
            </n-button>
            <n-button 
              v-if="state === 'reconnecting'" 
              @click="$emit('cancel-reconnect')"
            >
              取消
            </n-button>
          </n-button-group>
        </div>

        <n-divider style="margin: 12px 0" />

        <div class="status-details">
          <div class="detail-row">
            <span class="detail-label">连接状态</span>
            <n-tag :type="statusTagType" size="small">{{ statusText }}</n-tag>
          </div>
          <div v-if="reconnectAttempts > 0" class="detail-row">
            <span class="detail-label">重连次数</span>
            <span class="detail-value">{{ reconnectAttempts }} / {{ maxReconnectAttempts }}</span>
          </div>
          <div v-if="subscribedCount > 0" class="detail-row">
            <span class="detail-label">订阅资产</span>
            <span class="detail-value">{{ subscribedCount }} 个</span>
          </div>
          <div v-if="lastConnectedTime" class="detail-row">
            <span class="detail-label">上次连接</span>
            <span class="detail-value">{{ formatTime(lastConnectedTime) }}</span>
          </div>
          <div v-if="lastMessageTime" class="detail-row">
            <span class="detail-label">最后消息</span>
            <span class="detail-value">{{ formatTime(lastMessageTime) }}</span>
          </div>
        </div>

        <!-- 连接质量指示 -->
        <div v-if="state === 'connected' && showQuality" class="connection-quality">
          <div class="quality-label">连接质量</div>
          <div class="quality-bars">
            <span 
              v-for="i in 4" 
              :key="i" 
              class="quality-bar"
              :class="{ 'active': i <= qualityLevel }"
            ></span>
          </div>
          <span class="quality-text">{{ qualityText }}</span>
        </div>
      </n-card>
    </template>

    <!-- 徽章模式 -->
    <template v-else-if="mode === 'badge'">
      <n-badge :dot="true" :type="badgeType" :processing="isPulsing">
        <slot>
          <n-icon :component="WifiOutline" :size="20" />
        </slot>
      </n-badge>
    </template>
  </div>
</template>

<script setup>
/**
 * 连接状态指示器组件
 * 
 * 需求: 7.6 - 当网络断开时，前端应显示连接状态并自动重连
 */
import { ref, computed, watch } from 'vue'
import { NTooltip, NCard, NButton, NButtonGroup, NTag, NBadge, NIcon, NDivider } from 'naive-ui'
import { WifiOutline } from '@vicons/ionicons5'
import { ConnectionState } from '@/utils/websocket'

// Props
const props = defineProps({
  // 连接状态
  state: {
    type: String,
    default: ConnectionState.DISCONNECTED,
    validator: (value) => Object.values(ConnectionState).includes(value)
  },
  // 显示模式: compact, detailed, badge
  mode: {
    type: String,
    default: 'compact',
    validator: (value) => ['compact', 'detailed', 'badge'].includes(value)
  },
  // 是否显示标签
  showLabel: {
    type: Boolean,
    default: true
  },
  // 是否显示提示
  showTooltip: {
    type: Boolean,
    default: true
  },
  // 是否显示连接质量
  showQuality: {
    type: Boolean,
    default: true
  },
  // 重连次数
  reconnectAttempts: {
    type: Number,
    default: 0
  },
  // 最大重连次数
  maxReconnectAttempts: {
    type: Number,
    default: 10
  },
  // 订阅数量
  subscribedCount: {
    type: Number,
    default: 0
  },
  // 上次连接时间
  lastConnectedTime: {
    type: [Date, String],
    default: null
  },
  // 最后消息时间
  lastMessageTime: {
    type: [Date, String],
    default: null
  },
  // 延迟（毫秒）
  latency: {
    type: Number,
    default: 0
  }
})

// Emits
const emit = defineEmits(['connect', 'disconnect', 'cancel-reconnect'])

// 状态文本映射
const statusTextMap = {
  [ConnectionState.DISCONNECTED]: '未连接',
  [ConnectionState.CONNECTING]: '连接中',
  [ConnectionState.CONNECTED]: '已连接',
  [ConnectionState.RECONNECTING]: '重连中',
  [ConnectionState.ERROR]: '连接错误'
}

// 状态文本
const statusText = computed(() => statusTextMap[props.state] || '未知')

// 状态样式类
const statusClass = computed(() => {
  switch (props.state) {
    case ConnectionState.CONNECTED: return 'status--connected'
    case ConnectionState.CONNECTING:
    case ConnectionState.RECONNECTING: return 'status--connecting'
    case ConnectionState.ERROR: return 'status--error'
    default: return 'status--disconnected'
  }
})

// 状态标签类型
const statusTagType = computed(() => {
  switch (props.state) {
    case ConnectionState.CONNECTED: return 'success'
    case ConnectionState.CONNECTING:
    case ConnectionState.RECONNECTING: return 'warning'
    case ConnectionState.ERROR: return 'error'
    default: return 'default'
  }
})

// 徽章类型
const badgeType = computed(() => {
  switch (props.state) {
    case ConnectionState.CONNECTED: return 'success'
    case ConnectionState.CONNECTING:
    case ConnectionState.RECONNECTING: return 'warning'
    case ConnectionState.ERROR: return 'error'
    default: return 'default'
  }
})

// 是否显示脉冲动画
const isPulsing = computed(() => {
  return props.state === ConnectionState.CONNECTING || 
         props.state === ConnectionState.RECONNECTING ||
         props.state === ConnectionState.CONNECTED
})

// 连接质量等级 (1-4)
const qualityLevel = computed(() => {
  if (props.state !== ConnectionState.CONNECTED) return 0
  if (props.latency === 0) return 4
  if (props.latency < 100) return 4
  if (props.latency < 300) return 3
  if (props.latency < 500) return 2
  return 1
})

// 连接质量文本
const qualityText = computed(() => {
  switch (qualityLevel.value) {
    case 4: return '优秀'
    case 3: return '良好'
    case 2: return '一般'
    case 1: return '较差'
    default: return '-'
  }
})

// 格式化时间
function formatTime(time) {
  if (!time) return '-'
  const date = time instanceof Date ? time : new Date(time)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.connection-status {
  display: inline-flex;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: default;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: currentColor;
}

.status-dot.pulse {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

.status--connected {
  color: #18a058;
}

.status--connected .status-indicator {
  background: rgba(24, 160, 88, 0.1);
}

.status--connecting {
  color: #f0a020;
}

.status--connecting .status-indicator {
  background: rgba(240, 160, 32, 0.1);
}

.status--error {
  color: #d03050;
}

.status--error .status-indicator {
  background: rgba(208, 48, 80, 0.1);
}

.status--disconnected {
  color: #999;
}

.status--disconnected .status-indicator {
  background: rgba(153, 153, 153, 0.1);
}

.status-label {
  font-weight: 500;
}

.status-tooltip {
  font-size: 12px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 2px 0;
}

/* 详细模式样式 */
.status-card {
  min-width: 250px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 12px;
  color: var(--n-text-color-3);
}

.detail-value {
  font-size: 12px;
  color: var(--n-text-color);
}

.connection-quality {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--n-border-color);
}

.quality-label {
  font-size: 12px;
  color: var(--n-text-color-3);
}

.quality-bars {
  display: flex;
  gap: 2px;
  align-items: flex-end;
}

.quality-bar {
  width: 4px;
  background: var(--n-border-color);
  border-radius: 1px;
}

.quality-bar:nth-child(1) { height: 6px; }
.quality-bar:nth-child(2) { height: 10px; }
.quality-bar:nth-child(3) { height: 14px; }
.quality-bar:nth-child(4) { height: 18px; }

.quality-bar.active {
  background: #18a058;
}

.quality-text {
  font-size: 11px;
  color: var(--n-text-color-2);
}
</style>
