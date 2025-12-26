<template>
  <n-card v-if="aiModuleStore.isEnabled" size="small" class="ai-module-status">
    <template #header>
      <div class="status-header">
        <n-icon :component="BrainIcon" size="20" />
        <span class="title">AI模块状态</span>
      </div>
    </template>

    <n-space vertical :size="12">
      <!-- 模块状态 -->
      <div class="status-item">
        <span class="label">模块状态:</span>
        <n-tag :type="statusTagType" size="small">
          {{ statusText }}
        </n-tag>
      </div>

      <!-- 加载状态 -->
      <div class="status-item">
        <span class="label">加载状态:</span>
        <n-tag :type="aiModuleStore.isLoaded ? 'success' : 'warning'" size="small">
          {{ aiModuleStore.isLoaded ? '已加载' : '未加载' }}
        </n-tag>
      </div>

      <!-- 资源使用情况 -->
      <div v-if="aiModuleStore.resources" class="status-item">
        <span class="label">资源状态:</span>
        <n-tag :type="resourceStatusTagType" size="small">
          {{ resourceStatusText }}
        </n-tag>
      </div>

      <!-- 资源使用详情 -->
      <div v-if="aiModuleStore.resourceUsage" class="resource-details">
        <div class="resource-item">
          <span class="resource-label">内存使用:</span>
          <n-progress
            type="line"
            :percentage="aiModuleStore.resourceUsage.memory"
            :status="getProgressStatus(aiModuleStore.resourceUsage.memory)"
            :height="8"
          />
        </div>
        <div class="resource-item">
          <span class="resource-label">CPU使用:</span>
          <n-progress
            type="line"
            :percentage="aiModuleStore.resourceUsage.cpu"
            :status="getProgressStatus(aiModuleStore.resourceUsage.cpu)"
            :height="8"
          />
        </div>
      </div>

      <!-- 已启用的功能 -->
      <div v-if="aiModuleStore.enabledFeatures.length > 0" class="status-item">
        <span class="label">启用功能:</span>
        <n-space :size="4">
          <n-tag
            v-for="feature in aiModuleStore.enabledFeatures"
            :key="feature"
            type="info"
            size="small"
          >
            {{ feature }}
          </n-tag>
        </n-space>
      </div>

      <!-- 最后更新时间 -->
      <div v-if="aiModuleStore.lastUpdate" class="status-item">
        <span class="label">最后更新:</span>
        <span class="value">{{ formatTime(aiModuleStore.lastUpdate) }}</span>
      </div>

      <!-- 操作按钮 -->
      <n-space>
        <n-button size="small" @click="handleRefresh" :loading="aiModuleStore.loading">
          <template #icon>
            <n-icon :component="RefreshIcon" />
          </template>
          刷新
        </n-button>
      </n-space>

      <!-- 错误信息 -->
      <n-alert
        v-if="aiModuleStore.error"
        type="error"
        :title="aiModuleStore.error"
        closable
        @close="aiModuleStore.error = null"
      />
    </n-space>
  </n-card>
</template>

<script setup>
import { computed } from 'vue'
import {
  NCard,
  NSpace,
  NTag,
  NIcon,
  NButton,
  NProgress,
  NAlert,
} from 'naive-ui'
import { Refresh as RefreshIcon } from '@vicons/ionicons5'
import { Brain as BrainIcon } from '@vicons/tabler'
import { useAIModuleStore } from '@/store/modules/ai'

const aiModuleStore = useAIModuleStore()

// 状态标签类型
const statusTagType = computed(() => {
  switch (aiModuleStore.aiStatus) {
    case 'running':
      return 'success'
    case 'disabled':
      return 'default'
    case 'error':
      return 'error'
    default:
      return 'warning'
  }
})

// 状态文本
const statusText = computed(() => {
  switch (aiModuleStore.aiStatus) {
    case 'running':
      return '运行中'
    case 'disabled':
      return '已禁用'
    case 'error':
      return '错误'
    default:
      return '未知'
  }
})

// 资源状态标签类型
const resourceStatusTagType = computed(() => {
  switch (aiModuleStore.resourceStatus) {
    case 'healthy':
      return 'success'
    case 'warning':
      return 'warning'
    case 'critical':
      return 'error'
    default:
      return 'default'
  }
})

// 资源状态文本
const resourceStatusText = computed(() => {
  switch (aiModuleStore.resourceStatus) {
    case 'healthy':
      return '健康'
    case 'warning':
      return '警告'
    case 'critical':
      return '严重'
    default:
      return '未知'
  }
})

// 进度条状态
const getProgressStatus = (percentage) => {
  if (percentage >= 90) return 'error'
  if (percentage >= 70) return 'warning'
  return 'success'
}

// 格式化时间
const formatTime = (date) => {
  if (!date) return '--'
  const now = new Date()
  const diff = Math.floor((now - date) / 1000) // 秒

  if (diff < 60) return `${diff}秒前`
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return date.toLocaleString('zh-CN')
}

// 刷新
const handleRefresh = () => {
  aiModuleStore.refresh()
}
</script>

<style scoped>
.ai-module-status {
  min-width: 280px;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-header .title {
  font-weight: 500;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-item .label {
  font-size: 13px;
  color: var(--n-text-color-3);
  min-width: 80px;
}

.status-item .value {
  font-size: 13px;
  color: var(--n-text-color-2);
}

.resource-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px;
  background-color: var(--n-color-target);
  border-radius: 4px;
}

.resource-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.resource-label {
  font-size: 12px;
  color: var(--n-text-color-3);
}
</style>

