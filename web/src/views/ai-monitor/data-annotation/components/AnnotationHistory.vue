<template>
  <div class="annotation-history">
    <div v-if="loading" class="loading">
      <n-spin size="small" />
      <n-text depth="3" style="margin-left: 8px; font-size: 12px">加载中...</n-text>
    </div>

    <div v-else-if="annotations.length === 0" class="no-history">
      <n-empty description="暂无历史记录" size="small" />
    </div>

    <div v-else class="history-list">
      <n-timeline>
        <n-timeline-item
          v-for="annotation in annotations"
          :key="annotation.id"
          :type="getTimelineType(annotation.action)"
          :title="getActionText(annotation.action)"
          :time="formatTime(annotation.timestamp)"
        >
          <template #icon>
            <n-icon>
              <checkmark-circle-outline v-if="annotation.action === 'annotated'" />
              <eye-outline v-else-if="annotation.action === 'reviewed'" />
              <create-outline v-else />
            </n-icon>
          </template>

          <div class="timeline-content">
            <n-space vertical size="small">
              <div>
                <n-text depth="3" style="font-size: 12px">
                  数据ID: {{ annotation.dataId }} · {{ annotation.annotator }}
                </n-text>
              </div>

              <div v-if="annotation.quality">
                <n-tag :type="annotation.quality === 'good' ? 'success' : 'warning'" size="small">
                  {{ annotation.quality === 'good' ? '质量良好' : '需要复审' }}
                </n-tag>
              </div>
            </n-space>
          </div>
        </n-timeline-item>
      </n-timeline>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NSpin, NText, NEmpty, NTimeline, NTimelineItem, NIcon, NSpace, NTag } from 'naive-ui'
import { CheckmarkCircleOutline, EyeOutline, CreateOutline } from '@vicons/ionicons5'

// Props
const props = defineProps({
  annotations: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

// 获取时间线类型
const getTimelineType = (action) => {
  const typeMap = {
    annotated: 'success',
    reviewed: 'info',
    edited: 'warning',
  }
  return typeMap[action] || 'default'
}

// 获取操作文本
const getActionText = (action) => {
  const actionMap = {
    annotated: '完成标注',
    reviewed: '质量审核',
    edited: '编辑标注',
  }
  return actionMap[action] || action
}

// 格式化时间
const formatTime = (timestamp) => {
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
    // 1天内
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleDateString()
  }
}
</script>

<style scoped>
.annotation-history {
  height: 100%;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.no-history {
  padding: 20px 0;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.timeline-content {
  margin-top: 4px;
}
</style>
