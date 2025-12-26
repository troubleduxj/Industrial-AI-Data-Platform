<template>
  <div class="loading-state" :class="loadingClass" :style="loadingStyle">
    <!-- 加载指示器 -->
    <div class="loading-indicator">
      <component :is="indicatorComponent" v-bind="indicatorProps" />
    </div>

    <!-- 加载文本 -->
    <div v-if="text" class="loading-text">
      {{ text }}
    </div>

    <!-- 进度条 -->
    <div v-if="showProgress && progress !== null" class="loading-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${progress}%` }" />
      </div>
      <div class="progress-text">{{ progress }}%</div>
    </div>

    <!-- 自定义内容 -->
    <div v-if="$slots.default" class="loading-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { NSpin, NProgress } from 'naive-ui'

/**
 * 统一加载状态组件
 * 提供多种加载指示器和进度显示
 *
 * @component LoadingState
 * @example
 * <LoadingState
 *   type="spinner"
 *   text="正在加载..."
 *   :progress="50"
 *   size="large"
 * />
 */

const props = defineProps({
  // 加载指示器类型
  type: {
    type: String,
    default: 'spinner',
    validator: (value) =>
      ['spinner', 'dots', 'pulse', 'wave', 'skeleton', 'progress'].includes(value),
  },

  // 尺寸
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value),
  },

  // 加载文本
  text: {
    type: String,
    default: '',
  },

  // 进度值 (0-100)
  progress: {
    type: Number,
    default: null,
    validator: (value) => value === null || (value >= 0 && value <= 100),
  },

  // 是否显示进度条
  showProgress: {
    type: Boolean,
    default: false,
  },

  // 主题色
  color: {
    type: String,
    default: 'primary',
  },

  // 是否全屏覆盖
  overlay: {
    type: Boolean,
    default: false,
  },

  // 背景透明度
  opacity: {
    type: Number,
    default: 0.8,
    validator: (value) => value >= 0 && value <= 1,
  },

  // 动画速度
  speed: {
    type: String,
    default: 'normal',
    validator: (value) => ['slow', 'normal', 'fast'].includes(value),
  },

  // 自定义样式
  customStyle: {
    type: Object,
    default: () => ({}),
  },
})

// 计算属性
const loadingClass = computed(() => ({
  [`loading-state--${props.type}`]: true,
  [`loading-state--${props.size}`]: props.size !== 'medium',
  [`loading-state--${props.color}`]: props.color !== 'primary',
  [`loading-state--${props.speed}`]: props.speed !== 'normal',
  'loading-state--overlay': props.overlay,
}))

const loadingStyle = computed(() => ({
  ...props.customStyle,
  '--loading-opacity': props.opacity,
  '--progress-value': props.progress ? `${props.progress}%` : '0%',
}))

const indicatorComponent = computed(() => {
  switch (props.type) {
    case 'spinner':
      return NSpin
    case 'progress':
      return NProgress
    case 'dots':
      return 'div'
    case 'pulse':
      return 'div'
    case 'wave':
      return 'div'
    case 'skeleton':
      return 'div'
    default:
      return NSpin
  }
})

const indicatorProps = computed(() => {
  const baseProps = {
    size: props.size === 'small' ? 'small' : props.size === 'large' ? 'large' : 'medium',
  }

  switch (props.type) {
    case 'spinner':
      return {
        ...baseProps,
        show: true,
      }
    case 'progress':
      return {
        ...baseProps,
        percentage: props.progress || 0,
        type: 'circle',
      }
    default:
      return baseProps
  }
})
</script>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 24px;
  text-align: center;
}

/* 覆盖层模式 */
.loading-state--overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, var(--loading-opacity, 0.8));
  z-index: 9999;
  backdrop-filter: blur(2px);
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 点状加载器 */
.loading-state--dots .loading-indicator {
  display: flex;
  gap: 4px;
}

.loading-state--dots .loading-indicator::before,
.loading-state--dots .loading-indicator::after,
.loading-state--dots .loading-indicator {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-color);
  animation: dots-bounce 1.4s ease-in-out infinite both;
}

.loading-state--dots .loading-indicator::before {
  animation-delay: -0.32s;
}

.loading-state--dots .loading-indicator::after {
  animation-delay: -0.16s;
}

@keyframes dots-bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* 脉冲加载器 */
.loading-state--pulse .loading-indicator {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-color);
  animation: pulse-scale 1s ease-in-out infinite;
}

@keyframes pulse-scale {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}

/* 波浪加载器 */
.loading-state--wave .loading-indicator {
  display: flex;
  gap: 2px;
}

.loading-state--wave .loading-indicator::before,
.loading-state--wave .loading-indicator::after {
  content: '';
  width: 4px;
  height: 20px;
  background: var(--primary-color);
  animation: wave-stretch 1.2s ease-in-out infinite;
}

.loading-state--wave .loading-indicator::before {
  animation-delay: -0.4s;
}

.loading-state--wave .loading-indicator::after {
  animation-delay: -0.2s;
}

.loading-state--wave .loading-indicator {
  width: 4px;
  height: 20px;
  background: var(--primary-color);
  animation: wave-stretch 1.2s ease-in-out infinite;
}

@keyframes wave-stretch {
  0%,
  40%,
  100% {
    transform: scaleY(0.4);
  }
  20% {
    transform: scaleY(1);
  }
}

/* 骨架屏加载器 */
.loading-state--skeleton .loading-indicator {
  width: 100%;
  max-width: 300px;
}

.loading-state--skeleton .loading-indicator::before {
  content: '';
  display: block;
  width: 100%;
  height: 20px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

.loading-state--skeleton .loading-indicator::after {
  content: '';
  display: block;
  width: 60%;
  height: 20px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: 4px;
  animation-delay: 0.2s;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* 加载文本 */
.loading-text {
  font-size: 14px;
  color: var(--text-color-secondary);
  margin-top: 8px;
}

/* 进度条 */
.loading-progress {
  width: 100%;
  max-width: 200px;
  margin-top: 16px;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: var(--text-color-secondary);
  text-align: center;
}

/* 自定义内容 */
.loading-content {
  margin-top: 16px;
}

/* 尺寸变体 */
.loading-state--small {
  padding: 16px;
  gap: 12px;
}

.loading-state--small .loading-text {
  font-size: 12px;
}

.loading-state--small .loading-indicator {
  transform: scale(0.8);
}

.loading-state--large {
  padding: 32px;
  gap: 20px;
}

.loading-state--large .loading-text {
  font-size: 16px;
}

.loading-state--large .loading-indicator {
  transform: scale(1.2);
}

/* 颜色主题 */
.loading-state--primary {
  --primary-color: var(--n-color-primary);
}

.loading-state--success {
  --primary-color: var(--n-color-success);
}

.loading-state--warning {
  --primary-color: var(--n-color-warning);
}

.loading-state--error {
  --primary-color: var(--n-color-error);
}

/* 动画速度 */
.loading-state--slow * {
  animation-duration: 2s !important;
}

.loading-state--fast * {
  animation-duration: 0.8s !important;
}

/* 暗色主题适配 */
.dark .loading-state--overlay {
  background: rgba(24, 24, 28, var(--loading-opacity, 0.8));
}

.dark .loading-state--skeleton .loading-indicator::before,
.dark .loading-state--skeleton .loading-indicator::after {
  background: linear-gradient(90deg, #2d2d30 25%, #3a3a3e 50%, #2d2d30 75%);
  background-size: 200% 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .loading-state {
    padding: 16px;
    gap: 12px;
  }

  .loading-text {
    font-size: 13px;
  }

  .loading-progress {
    max-width: 150px;
  }
}

/* 减少动画模式 */
@media (prefers-reduced-motion: reduce) {
  .loading-state * {
    animation: none !important;
  }

  .progress-fill {
    transition: none;
  }
}
</style>
