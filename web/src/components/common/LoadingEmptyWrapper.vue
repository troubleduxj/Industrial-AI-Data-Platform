<template>
  <div v-if="reloadFlag" class="loading-empty-wrapper">
    <!-- 主要内容 -->
    <div class="wrapper-content">
      <slot />
    </div>

    <!-- 占位符覆盖层 -->
    <div v-show="showPlaceholder" class="wrapper-overlay" :class="overlayClass">
      <!-- 加载状态 -->
      <div v-show="loading" class="state-container state-container--loading">
        <n-spin :show="true" :size="loadingSize" />
        <p v-if="loadingText" class="state-text">{{ loadingText }}</p>
      </div>

      <!-- 空数据状态 -->
      <div v-show="isEmpty" class="state-container state-container--empty">
        <div class="state-icon">
          <slot name="empty-icon">
            <icon-custom-no-data :class="iconClass" />
          </slot>
        </div>
        <p class="state-text">{{ emptyDescription }}</p>
        <div v-if="$slots['empty-action']" class="state-action">
          <slot name="empty-action" />
        </div>
      </div>

      <!-- 网络错误状态 -->
      <div v-show="!network" class="state-container state-container--error">
        <div
          class="state-icon"
          :class="{ 'state-icon--clickable': showNetworkReload }"
          @click="handleReload"
        >
          <slot name="error-icon">
            <icon-custom-network-error :class="iconClass" />
          </slot>
        </div>
        <p class="state-text">{{ networkErrorDescription }}</p>
        <div v-if="showNetworkReload" class="state-action">
          <n-button size="small" @click="handleReload">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            重试
          </n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { NButton, NIcon } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'

/**
 * 加载和空状态包装器组件
 * 提供统一的加载、空数据和网络错误状态展示
 *
 * @component LoadingEmptyWrapper
 * @example
 * <LoadingEmptyWrapper
 *   :loading="isLoading"
 *   :empty="isEmpty"
 *   empty-description="暂无数据"
 *   :show-network-reload="true"
 * >
 *   <YourContent />
 * </LoadingEmptyWrapper>
 */

const NETWORK_ERROR_MSG = '网络似乎开了小差~'

const props = defineProps({
  // 加载状态
  loading: {
    type: Boolean,
    default: false,
  },

  // 空数据状态
  empty: {
    type: Boolean,
    default: false,
  },

  // 加载指示器尺寸
  loadingSize: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value),
  },

  // 加载文本
  loadingText: {
    type: String,
    default: '',
  },

  // 空数据描述
  emptyDescription: {
    type: String,
    default: '暂无数据',
  },

  // 图标样式类
  iconClass: {
    type: String,
    default: 'text-320px text-primary',
  },

  // 是否显示网络重试
  showNetworkReload: {
    type: Boolean,
    default: false,
  },

  // 覆盖层样式类
  overlayClass: {
    type: String,
    default: '',
  },

  // 最小高度
  minHeight: {
    type: [String, Number],
    default: '200px',
  },
})

const emit = defineEmits(['reload', 'retry'])

// 网络状态
const network = ref(window.navigator.onLine)
const reloadFlag = ref(true)

// 计算属性
const isEmpty = computed(() => props.empty && !props.loading && network.value)

const showPlaceholder = computed(() => props.loading || isEmpty.value || !network.value)

const networkErrorDescription = computed(() =>
  props.showNetworkReload ? `${NETWORK_ERROR_MSG}，点击重试` : NETWORK_ERROR_MSG
)

const overlayClass = computed(() => ['wrapper-overlay--default', props.overlayClass])

// 方法
function handleReload() {
  if (!props.showNetworkReload) return

  emit('reload')
  emit('retry')

  reloadFlag.value = false
  nextTick(() => {
    reloadFlag.value = true
  })
}

// 监听网络状态变化
function updateNetworkStatus() {
  network.value = window.navigator.onLine
}

// 监听加载状态变化
const stopLoadingWatch = watch(
  () => props.loading,
  (newValue) => {
    // 结束加载时检查网络状态
    if (!newValue) {
      updateNetworkStatus()
    }
  }
)

// 生命周期
onMounted(() => {
  window.addEventListener('online', updateNetworkStatus)
  window.addEventListener('offline', updateNetworkStatus)
})

onUnmounted(() => {
  window.removeEventListener('online', updateNetworkStatus)
  window.removeEventListener('offline', updateNetworkStatus)
  stopLoadingWatch()
})
</script>

<style scoped>
.loading-empty-wrapper {
  position: relative;
  width: 100%;
  min-height: v-bind(minHeight);
}

.wrapper-content {
  width: 100%;
  height: 100%;
}

.wrapper-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.wrapper-overlay--default {
  background-color: var(--bg-color, #fff);
  transition: background-color 0.3s ease;
}

/* 状态容器 */
.state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px;
  max-width: 400px;
}

.state-container--loading {
  gap: 16px;
}

.state-container--empty,
.state-container--error {
  gap: 12px;
}

/* 状态图标 */
.state-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.state-icon--clickable {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.state-icon--clickable:hover {
  transform: scale(1.05);
}

.state-icon--clickable:active {
  transform: scale(0.95);
}

/* 状态文本 */
.state-text {
  margin: 0;
  font-size: 14px;
  color: var(--text-color-secondary, #666);
  line-height: 1.5;
}

.state-container--loading .state-text {
  font-size: 16px;
  color: var(--text-color, #333);
}

/* 状态操作 */
.state-action {
  margin-top: 16px;
}

/* 暗色主题适配 */
.dark .wrapper-overlay--default {
  --bg-color: #18181c;
  --text-color: #fff;
  --text-color-secondary: #a0a0a0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .state-container {
    padding: 16px;
    max-width: 300px;
  }

  .state-text {
    font-size: 13px;
  }

  .state-container--loading .state-text {
    font-size: 14px;
  }
}

/* 动画效果 */
.wrapper-overlay {
  animation: fadeIn 0.3s ease;
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
