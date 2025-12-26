<template>
  <div class="loading-feedback">
    <!-- 全局加载遮罩 -->
    <NSpin 
      v-if="globalLoading" 
      :show="globalLoading"
      size="large"
      class="global-loading"
    >
      <div class="loading-content">
        <div class="loading-text">{{ loadingText }}</div>
        <div class="loading-progress" v-if="showProgress">
          <NProgress 
            :percentage="progress" 
            :show-indicator="true"
            type="line"
            status="info"
          />
        </div>
      </div>
    </NSpin>

    <!-- 操作反馈提示 -->
    <div v-if="feedbackVisible" class="feedback-container">
      <NAlert
        :type="feedbackType"
        :title="feedbackTitle"
        :show-icon="true"
        closable
        @close="hideFeedback"
      >
        {{ feedbackMessage }}
      </NAlert>
    </div>

    <!-- 操作确认对话框 -->
    <NModal
      v-model:show="confirmVisible"
      preset="dialog"
      :title="confirmTitle"
      :content="confirmContent"
      :positive-text="confirmPositiveText"
      :negative-text="confirmNegativeText"
      @positive-click="handleConfirmPositive"
      @negative-click="handleConfirmNegative"
    />

    <!-- 批量操作进度 -->
    <NModal
      v-model:show="batchProgressVisible"
      :mask-closable="false"
      preset="card"
      title="批量操作进度"
      style="width: 500px;"
    >
      <div class="batch-progress">
        <div class="progress-info">
          <span>正在处理：{{ currentBatchItem }}</span>
          <span>{{ batchProgress.current }} / {{ batchProgress.total }}</span>
        </div>
        <NProgress 
          :percentage="batchProgressPercentage" 
          :show-indicator="true"
          type="line"
          :status="batchProgressStatus"
        />
        <div class="progress-details" v-if="batchDetails.length > 0">
          <div 
            v-for="(detail, index) in batchDetails" 
            :key="index"
            class="detail-item"
            :class="detail.status"
          >
            <TheIcon 
              :icon="getStatusIcon(detail.status)" 
              :size="16" 
              class="status-icon"
            />
            <span>{{ detail.message }}</span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="flex justify-end">
          <NButton 
            v-if="batchProgress.current >= batchProgress.total"
            type="primary" 
            @click="closeBatchProgress"
          >
            完成
          </NButton>
          <NButton 
            v-else
            @click="cancelBatchOperation"
          >
            取消
          </NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, type Ref } from 'vue'
import { NSpin, NAlert, NModal, NProgress, NButton } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

// ==================== 类型定义 ====================

interface Props {
  globalLoading?: boolean
  loadingText?: string
  showProgress?: boolean
  progress?: number
}

interface Emits {
  (e: 'confirm-positive'): void
  (e: 'confirm-negative'): void
  (e: 'batch-cancel'): void
  (e: 'batch-complete'): void
}

type FeedbackType = 'info' | 'success' | 'warning' | 'error'
type BatchStatus = 'success' | 'error' | 'warning' | 'info'

interface BatchProgress {
  current: number
  total: number
}

interface BatchDetail {
  status: BatchStatus
  message: string
}

// Props
const props = withDefaults(defineProps<Props>(), {
  globalLoading: false,
  loadingText: '加载中...',
  showProgress: false,
  progress: 0
})

// Emits
const emit = defineEmits<Emits>()

// 反馈状态
const feedbackVisible = ref<boolean>(false)
const feedbackType = ref<FeedbackType>('info')
const feedbackTitle = ref<string>('')
const feedbackMessage = ref<string>('')

// 确认对话框状态
const confirmVisible = ref<boolean>(false)
const confirmTitle = ref<string>('')
const confirmContent = ref<string>('')
const confirmPositiveText = ref<string>('确定')
const confirmNegativeText = ref<string>('取消')
const confirmCallback = ref<((result: boolean) => void) | null>(null)

// 批量操作进度状态
const batchProgressVisible = ref<boolean>(false)
const currentBatchItem = ref<string>('')
const batchProgress = ref<BatchProgress>({ current: 0, total: 0 })
const batchDetails = ref<BatchDetail[]>([])
const batchCancelled = ref<boolean>(false)

// 计算属性
const batchProgressPercentage = computed(() => {
  if (batchProgress.value.total === 0) return 0
  return Math.round((batchProgress.value.current / batchProgress.value.total) * 100)
})

const batchProgressStatus = computed(() => {
  if (batchCancelled.value) return 'error'
  if (batchProgress.value.current >= batchProgress.value.total) return 'success'
  return 'info'
})

// 方法
const showFeedback = (type, title, message, duration = 3000) => {
  feedbackType.value = type
  feedbackTitle.value = title
  feedbackMessage.value = message
  feedbackVisible.value = true
  
  if (duration > 0) {
    setTimeout(() => {
      hideFeedback()
    }, duration)
  }
}

const hideFeedback = () => {
  feedbackVisible.value = false
}

const showConfirm = (title, content, callback, positiveText = '确定', negativeText = '取消') => {
  confirmTitle.value = title
  confirmContent.value = content
  confirmPositiveText.value = positiveText
  confirmNegativeText.value = negativeText
  confirmCallback.value = callback
  confirmVisible.value = true
}

const handleConfirmPositive = () => {
  if (confirmCallback.value) {
    confirmCallback.value(true)
  }
  emit('confirm-positive')
  confirmVisible.value = false
}

const handleConfirmNegative = () => {
  if (confirmCallback.value) {
    confirmCallback.value(false)
  }
  emit('confirm-negative')
  confirmVisible.value = false
}

const startBatchProgress = (total, title = '批量操作进度') => {
  batchProgress.value = { current: 0, total }
  batchDetails.value = []
  batchCancelled.value = false
  currentBatchItem.value = ''
  batchProgressVisible.value = true
}

const updateBatchProgress = (current, itemName = '', status = 'success', message = '') => {
  batchProgress.value.current = current
  currentBatchItem.value = itemName
  
  if (message) {
    batchDetails.value.push({
      status,
      message: `${itemName}: ${message}`
    })
  }
}

const completeBatchProgress = () => {
  batchProgress.value.current = batchProgress.value.total
  currentBatchItem.value = '操作完成'
}

const cancelBatchOperation = () => {
  batchCancelled.value = true
  currentBatchItem.value = '操作已取消'
  emit('batch-cancel')
}

const closeBatchProgress = () => {
  batchProgressVisible.value = false
  emit('batch-complete')
}

const getStatusIcon = (status) => {
  switch (status) {
    case 'success':
      return 'material-symbols:check-circle'
    case 'error':
      return 'material-symbols:error'
    case 'warning':
      return 'material-symbols:warning'
    default:
      return 'material-symbols:info'
  }
}

// 预定义的反馈方法
const showSuccess = (message, title = '操作成功') => {
  showFeedback('success', title, message)
}

const showError = (message, title = '操作失败') => {
  showFeedback('error', title, message, 5000)
}

const showWarning = (message, title = '警告') => {
  showFeedback('warning', title, message, 4000)
}

const showInfo = (message, title = '提示') => {
  showFeedback('info', title, message)
}

// 暴露方法
defineExpose({
  showFeedback,
  hideFeedback,
  showConfirm,
  startBatchProgress,
  updateBatchProgress,
  completeBatchProgress,
  cancelBatchOperation,
  closeBatchProgress,
  showSuccess,
  showError,
  showWarning,
  showInfo
})
</script>

<style scoped>
.loading-feedback {
  position: relative;
}

.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-content {
  text-align: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  min-width: 300px;
}

.loading-text {
  font-size: 16px;
  color: #333;
  margin-bottom: 16px;
}

.loading-progress {
  margin-top: 16px;
}

.feedback-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9998;
  max-width: 400px;
}

.batch-progress {
  padding: 16px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #666;
}

.progress-details {
  margin-top: 16px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e0e0e6;
  border-radius: 4px;
  padding: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
}

.detail-item.success {
  color: #18a058;
}

.detail-item.error {
  color: #d03050;
}

.detail-item.warning {
  color: #f0a020;
}

.status-icon {
  flex-shrink: 0;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .feedback-container {
    top: 10px;
    right: 10px;
    left: 10px;
    max-width: none;
  }
  
  .loading-content {
    min-width: 250px;
    margin: 0 20px;
  }
}

/* 动画效果 */
.feedback-container {
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.batch-progress {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>