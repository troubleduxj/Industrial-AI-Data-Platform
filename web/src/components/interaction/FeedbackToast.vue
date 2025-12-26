<template>
  <teleport to="body">
    <transition-group name="toast" tag="div" class="toast-container" :class="containerClass">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast-item"
        :class="getToastClass(toast)"
        @click="handleToastClick(toast)"
        @mouseenter="handleMouseEnter(toast)"
        @mouseleave="handleMouseLeave(toast)"
      >
        <!-- 图标 -->
        <div class="toast-icon">
          <n-icon :component="getToastIcon(toast.type)" :size="20" />
        </div>

        <!-- 内容 -->
        <div class="toast-content">
          <div v-if="toast.title" class="toast-title">
            {{ toast.title }}
          </div>
          <div class="toast-message">
            {{ toast.message }}
          </div>
        </div>

        <!-- 关闭按钮 -->
        <div
          v-if="toast.closable !== false"
          class="toast-close"
          @click.stop="removeToast(toast.id)"
        >
          <n-icon :component="CloseOutline" :size="16" />
        </div>

        <!-- 进度条 -->
        <div
          v-if="toast.showProgress"
          class="toast-progress"
          :style="{ width: `${toast.progress}%` }"
        />
      </div>
    </transition-group>
  </teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NIcon } from 'naive-ui'
import {
  CheckmarkCircleOutline,
  InformationCircleOutline,
  WarningOutline,
  CloseCircleOutline,
  CloseOutline,
} from '@vicons/ionicons5'

/**
 * 反馈提示组件
 * 提供统一的消息提示和反馈机制
 *
 * @component FeedbackToast
 * @example
 * <FeedbackToast ref="toastRef" />
 *
 * // 在组件中使用
 * toastRef.value.show({
 *   type: 'success',
 *   message: '操作成功',
 *   duration: 3000
 * })
 */

const props = defineProps({
  // 容器位置
  position: {
    type: String,
    default: 'top-right',
    validator: (value) =>
      [
        'top-left',
        'top-center',
        'top-right',
        'bottom-left',
        'bottom-center',
        'bottom-right',
      ].includes(value),
  },

  // 最大显示数量
  maxCount: {
    type: Number,
    default: 5,
  },

  // 默认持续时间
  defaultDuration: {
    type: Number,
    default: 3000,
  },

  // 是否可关闭
  closable: {
    type: Boolean,
    default: true,
  },

  // 是否显示进度条
  showProgress: {
    type: Boolean,
    default: false,
  },
})

// 响应式数据
const toasts = ref([])
const timers = new Map()

// 计算属性
const containerClass = computed(() => ({
  [`toast-container--${props.position}`]: true,
}))

// 图标映射
const iconMap = {
  success: CheckmarkCircleOutline,
  info: InformationCircleOutline,
  warning: WarningOutline,
  error: CloseCircleOutline,
}

// 方法
function generateId() {
  return Date.now() + Math.random().toString(36).substr(2, 9)
}

function getToastIcon(type) {
  return iconMap[type] || InformationCircleOutline
}

function getToastClass(toast) {
  return {
    [`toast-item--${toast.type}`]: true,
    'toast-item--closable': toast.closable !== false,
    'toast-item--with-progress': toast.showProgress,
  }
}

function show(options) {
  const toast = {
    id: generateId(),
    type: options.type || 'info',
    title: options.title || '',
    message: options.message || '',
    duration: options.duration ?? props.defaultDuration,
    closable: options.closable ?? props.closable,
    showProgress: options.showProgress ?? props.showProgress,
    progress: 100,
    onClick: options.onClick,
    onClose: options.onClose,
  }

  // 限制最大数量
  if (toasts.value.length >= props.maxCount) {
    const oldestToast = toasts.value[0]
    removeToast(oldestToast.id)
  }

  toasts.value.push(toast)

  // 设置自动关闭
  if (toast.duration > 0) {
    startTimer(toast)
  }

  return toast.id
}

function startTimer(toast) {
  if (toast.showProgress) {
    // 进度条动画
    const interval = 50
    const step = (interval / toast.duration) * 100

    const progressTimer = setInterval(() => {
      toast.progress -= step
      if (toast.progress <= 0) {
        clearInterval(progressTimer)
        removeToast(toast.id)
      }
    }, interval)

    timers.set(toast.id, progressTimer)
  } else {
    // 简单定时器
    const timer = setTimeout(() => {
      removeToast(toast.id)
    }, toast.duration)

    timers.set(toast.id, timer)
  }
}

function pauseTimer(toastId) {
  const timer = timers.get(toastId)
  if (timer) {
    clearTimeout(timer)
    clearInterval(timer)
  }
}

function resumeTimer(toast) {
  if (toast.duration > 0) {
    startTimer(toast)
  }
}

function removeToast(toastId) {
  const index = toasts.value.findIndex((t) => t.id === toastId)
  if (index > -1) {
    const toast = toasts.value[index]

    // 清理定时器
    const timer = timers.get(toastId)
    if (timer) {
      clearTimeout(timer)
      clearInterval(timer)
      timers.delete(toastId)
    }

    // 触发关闭回调
    if (toast.onClose) {
      toast.onClose(toast)
    }

    toasts.value.splice(index, 1)
  }
}

function clear() {
  // 清理所有定时器
  timers.forEach((timer) => {
    clearTimeout(timer)
    clearInterval(timer)
  })
  timers.clear()

  toasts.value = []
}

function handleToastClick(toast) {
  if (toast.onClick) {
    toast.onClick(toast)
  }
}

function handleMouseEnter(toast) {
  pauseTimer(toast.id)
}

function handleMouseLeave(toast) {
  resumeTimer(toast)
}

// 便捷方法
function success(message, options = {}) {
  return show({ ...options, type: 'success', message })
}

function info(message, options = {}) {
  return show({ ...options, type: 'info', message })
}

function warning(message, options = {}) {
  return show({ ...options, type: 'warning', message })
}

function error(message, options = {}) {
  return show({ ...options, type: 'error', message })
}

// 生命周期
onUnmounted(() => {
  clear()
})

// 暴露方法
defineExpose({
  show,
  success,
  info,
  warning,
  error,
  removeToast,
  clear,
})
</script>

<style scoped>
.toast-container {
  position: fixed;
  z-index: 10000;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  max-width: 400px;
  width: auto;
}

/* 位置样式 */
.toast-container--top-left {
  top: 0;
  left: 0;
}

.toast-container--top-center {
  top: 0;
  left: 50%;
  transform: translateX(-50%);
}

.toast-container--top-right {
  top: 0;
  right: 0;
}

.toast-container--bottom-left {
  bottom: 0;
  left: 0;
  flex-direction: column-reverse;
}

.toast-container--bottom-center {
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  flex-direction: column-reverse;
}

.toast-container--bottom-right {
  bottom: 0;
  right: 0;
  flex-direction: column-reverse;
}

/* Toast项样式 */
.toast-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--bg-color, #fff);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-left: 4px solid var(--toast-color);
  pointer-events: auto;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  min-width: 300px;
  max-width: 400px;
}

.toast-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

/* Toast类型样式 */
.toast-item--success {
  --toast-color: var(--success-color, #18a058);
}

.toast-item--info {
  --toast-color: var(--info-color, #2080f0);
}

.toast-item--warning {
  --toast-color: var(--warning-color, #f0a020);
}

.toast-item--error {
  --toast-color: var(--error-color, #d03050);
}

/* Toast图标 */
.toast-icon {
  flex-shrink: 0;
  color: var(--toast-color);
  margin-top: 2px;
}

/* Toast内容 */
.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color, #333);
  margin-bottom: 4px;
  line-height: 1.4;
}

.toast-message {
  font-size: 13px;
  color: var(--text-color-secondary, #666);
  line-height: 1.5;
  word-break: break-word;
}

/* 关闭按钮 */
.toast-close {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  color: var(--text-color-secondary, #666);
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: -2px;
}

.toast-close:hover {
  background: var(--hover-bg-color, #f5f5f5);
  color: var(--text-color, #333);
}

/* 进度条 */
.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: var(--toast-color);
  transition: width 0.1s linear;
  border-radius: 0 0 8px 8px;
}

/* 过渡动画 */
.toast-enter-active {
  transition: all 0.3s ease;
}

.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* 从左侧进入的动画 */
.toast-container--top-left .toast-enter-from,
.toast-container--bottom-left .toast-enter-from {
  transform: translateX(-100%);
}

.toast-container--top-left .toast-leave-to,
.toast-container--bottom-left .toast-leave-to {
  transform: translateX(-100%);
}

/* 从中间进入的动画 */
.toast-container--top-center .toast-enter-from,
.toast-container--bottom-center .toast-enter-from {
  transform: translateY(-100%);
}

.toast-container--top-center .toast-leave-to,
.toast-container--bottom-center .toast-leave-to {
  transform: translateY(-100%);
}

/* 暗色主题适配 */
.dark .toast-item {
  --bg-color: #2d2d30;
  --text-color: #fff;
  --text-color-secondary: #a0a0a0;
  --hover-bg-color: #3a3a3e;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .toast-container {
    left: 8px !important;
    right: 8px !important;
    max-width: none;
    transform: none !important;
  }

  .toast-item {
    min-width: auto;
    max-width: none;
  }
}

/* 减少动画模式 */
@media (prefers-reduced-motion: reduce) {
  .toast-enter-active,
  .toast-leave-active {
    transition-duration: 0.01ms !important;
  }

  .toast-item {
    transition: none;
  }

  .toast-progress {
    transition: none;
  }
}
</style>
