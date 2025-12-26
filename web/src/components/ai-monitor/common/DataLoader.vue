<template>
  <div class="data-loader">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <n-spin :size="spinSize">
        <template v-if="loadingText" #description>
          {{ loadingText }}
        </template>
      </n-spin>

      <!-- 进度条 -->
      <div v-if="showProgress && progress > 0" class="progress-container">
        <n-progress
          type="line"
          :percentage="progress"
          :show-indicator="true"
          :status="progressStatus"
        />
        <div v-if="progressText" class="progress-text">
          {{ progressText }}
        </div>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <n-result status="error" :title="errorTitle" :description="errorDescription">
        <template #footer>
          <n-space>
            <n-button :loading="retrying" @click="retry">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              重试
            </n-button>
            <n-button v-if="showCancel" secondary @click="$emit('cancel')"> 取消 </n-button>
          </n-space>
        </template>
      </n-result>
    </div>

    <!-- 空数据状态 -->
    <div v-else-if="isEmpty" class="empty-state">
      <n-empty :description="emptyDescription" :size="emptySize">
        <template v-if="showEmptyAction" #extra>
          <n-button @click="$emit('load-data')">
            <template #icon>
              <n-icon><AddOutline /></n-icon>
            </template>
            {{ emptyActionText }}
          </n-button>
        </template>
      </n-empty>
    </div>

    <!-- 成功状态 - 显示内容 -->
    <div v-else class="content-state">
      <slot></slot>

      <!-- 刷新按钮 -->
      <div v-if="showRefresh" class="refresh-container">
        <n-button text size="small" :loading="refreshing" @click="refresh">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新数据
        </n-button>
      </div>
    </div>

    <!-- 自动刷新指示器 -->
    <div v-if="autoRefresh && autoRefreshInterval > 0" class="auto-refresh-indicator">
      <n-tag size="small" type="info">
        <template #icon>
          <n-icon><TimeOutline /></n-icon>
        </template>
        自动刷新: {{ formatTime(nextRefreshTime) }}
      </n-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { RefreshOutline, AddOutline, TimeOutline } from '@vicons/ionicons5'
import { useMessage } from 'naive-ui'

// Props
const props = defineProps({
  // 加载状态
  loading: {
    type: Boolean,
    default: false,
  },
  // 错误信息
  error: {
    type: [String, Object, Error],
    default: null,
  },
  // 是否为空数据
  isEmpty: {
    type: Boolean,
    default: false,
  },
  // 加载文本
  loadingText: {
    type: String,
    default: '数据加载中...',
  },
  // 错误标题
  errorTitle: {
    type: String,
    default: '数据加载失败',
  },
  // 错误描述
  errorDescription: {
    type: String,
    default: '',
  },
  // 空数据描述
  emptyDescription: {
    type: String,
    default: '暂无数据',
  },
  // 空数据操作文本
  emptyActionText: {
    type: String,
    default: '加载数据',
  },
  // 是否显示空数据操作
  showEmptyAction: {
    type: Boolean,
    default: true,
  },
  // 是否显示取消按钮
  showCancel: {
    type: Boolean,
    default: false,
  },
  // 是否显示刷新按钮
  showRefresh: {
    type: Boolean,
    default: true,
  },
  // 是否显示进度条
  showProgress: {
    type: Boolean,
    default: false,
  },
  // 进度值 (0-100)
  progress: {
    type: Number,
    default: 0,
  },
  // 进度状态
  progressStatus: {
    type: String,
    default: 'default',
  },
  // 进度文本
  progressText: {
    type: String,
    default: '',
  },
  // 加载器大小
  spinSize: {
    type: String,
    default: 'medium',
  },
  // 空状态大小
  emptySize: {
    type: String,
    default: 'medium',
  },
  // 自动刷新
  autoRefresh: {
    type: Boolean,
    default: false,
  },
  // 自动刷新间隔(秒)
  autoRefreshInterval: {
    type: Number,
    default: 30,
  },
  // 重试次数限制
  maxRetries: {
    type: Number,
    default: 3,
  },
})

// Emits
const emit = defineEmits(['retry', 'refresh', 'cancel', 'load-data', 'auto-refresh'])

// 响应式数据
const retrying = ref(false)
const refreshing = ref(false)
const retryCount = ref(0)
const autoRefreshTimer = ref(null)
const nextRefreshTime = ref(0)
const countdownTimer = ref(null)
const message = useMessage()

// 计算属性
const computedErrorDescription = computed(() => {
  if (props.errorDescription) return props.errorDescription

  if (typeof props.error === 'string') {
    return props.error
  } else if (props.error?.message) {
    return props.error.message
  } else if (props.error?.response?.data?.message) {
    return props.error.response.data.message
  }

  return '请检查网络连接或联系管理员'
})

// 重试操作
const retry = async () => {
  if (retryCount.value >= props.maxRetries) {
    message.error(`已达到最大重试次数 (${props.maxRetries})`)
    return
  }

  retrying.value = true
  retryCount.value++

  try {
    emit('retry')
    // 重试成功后重置计数
    setTimeout(() => {
      if (!props.error) {
        retryCount.value = 0
      }
    }, 1000)
  } finally {
    retrying.value = false
  }
}

// 刷新操作
const refresh = async () => {
  refreshing.value = true
  try {
    emit('refresh')
  } finally {
    refreshing.value = false
  }
}

// 启动自动刷新
const startAutoRefresh = () => {
  if (!props.autoRefresh || props.autoRefreshInterval <= 0) return

  stopAutoRefresh()

  // 设置下次刷新时间
  nextRefreshTime.value = Date.now() + props.autoRefreshInterval * 1000

  // 启动倒计时
  countdownTimer.value = setInterval(() => {
    const remaining = nextRefreshTime.value - Date.now()
    if (remaining <= 0) {
      clearInterval(countdownTimer.value)
    }
  }, 1000)

  // 设置自动刷新定时器
  autoRefreshTimer.value = setTimeout(() => {
    if (!props.loading && !props.error) {
      emit('auto-refresh')
      startAutoRefresh() // 递归启动下一次
    }
  }, props.autoRefreshInterval * 1000)
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (autoRefreshTimer.value) {
    clearTimeout(autoRefreshTimer.value)
    autoRefreshTimer.value = null
  }

  if (countdownTimer.value) {
    clearInterval(countdownTimer.value)
    countdownTimer.value = null
  }

  nextRefreshTime.value = 0
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''

  const remaining = Math.max(0, timestamp - Date.now())
  const seconds = Math.ceil(remaining / 1000)

  if (seconds <= 0) return '即将刷新'

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60

  if (minutes > 0) {
    return `${minutes}分${remainingSeconds}秒`
  }

  return `${remainingSeconds}秒`
}

// 监听自动刷新设置变化
watch(
  () => props.autoRefresh,
  (newVal) => {
    if (newVal) {
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  }
)

watch(
  () => props.autoRefreshInterval,
  () => {
    if (props.autoRefresh) {
      startAutoRefresh()
    }
  }
)

// 监听加载状态变化
watch(
  () => props.loading,
  (newVal) => {
    if (!newVal && props.autoRefresh) {
      // 加载完成后重新启动自动刷新
      setTimeout(() => {
        startAutoRefresh()
      }, 1000)
    }
  }
)

// 监听错误状态变化
watch(
  () => props.error,
  (newVal) => {
    if (newVal) {
      stopAutoRefresh()
    }
  }
)

// 生命周期
onMounted(() => {
  if (props.autoRefresh) {
    startAutoRefresh()
  }
})

onBeforeUnmount(() => {
  stopAutoRefresh()
})

// 暴露方法
defineExpose({
  retry,
  refresh,
  startAutoRefresh,
  stopAutoRefresh,
  getRetryCount: () => retryCount.value,
})
</script>

<style scoped>
.data-loader {
  width: 100%;
  position: relative;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 40px 20px;
}

.progress-container {
  width: 100%;
  max-width: 300px;
  margin-top: 20px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.error-state {
  padding: 40px 20px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 40px 20px;
}

.content-state {
  position: relative;
}

.refresh-container {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}

.auto-refresh-indicator {
  position: absolute;
  bottom: 10px;
  right: 10px;
  z-index: 10;
}

/* 响应式 */
@media (max-width: 768px) {
  .loading-state,
  .empty-state {
    min-height: 150px;
    padding: 20px 10px;
  }

  .error-state {
    padding: 20px 10px;
  }

  .refresh-container,
  .auto-refresh-indicator {
    position: relative;
    top: auto;
    right: auto;
    bottom: auto;
    margin-top: 10px;
    text-align: center;
  }
}
</style>
