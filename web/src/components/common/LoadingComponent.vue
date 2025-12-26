<template>
  <div class="loading-component" :class="{ 'loading-component--fullscreen': fullscreen }">
    <div class="loading-content">
      <div class="loading-spinner" :class="`loading-spinner--${type}`">
        <div v-if="type === 'ring'" class="spinner-ring">
          <div></div>
          <div></div>
          <div></div>
          <div></div>
        </div>
        <div v-else-if="type === 'dots'" class="spinner-dots">
          <div></div>
          <div></div>
          <div></div>
        </div>
        <div v-else-if="type === 'pulse'" class="spinner-pulse">
          <div></div>
        </div>
        <div v-else class="spinner-wave">
          <div></div>
          <div></div>
          <div></div>
          <div></div>
          <div></div>
        </div>
      </div>
      <div v-if="text" class="loading-text">{{ text }}</div>
      <div v-if="showProgress" class="loading-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
        <div class="progress-text">{{ progress }}%</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  // 加载文本
  text: {
    type: String,
    default: '加载中...',
  },
  // 加载动画类型
  type: {
    type: String,
    default: 'ring',
    validator: (value) => ['ring', 'dots', 'pulse', 'wave'].includes(value),
  },
  // 是否全屏显示
  fullscreen: {
    type: Boolean,
    default: false,
  },
  // 是否显示进度条
  showProgress: {
    type: Boolean,
    default: false,
  },
  // 初始进度
  initialProgress: {
    type: Number,
    default: 0,
  },
  // 自动进度更新
  autoProgress: {
    type: Boolean,
    default: false,
  },
})

const progress = ref(props.initialProgress)
let progressTimer = null

// 自动进度更新
const startAutoProgress = () => {
  if (!props.autoProgress) return

  progressTimer = setInterval(() => {
    if (progress.value < 90) {
      progress.value += Math.random() * 10
    }
  }, 200)
}

const stopAutoProgress = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

onMounted(() => {
  startAutoProgress()
})

onUnmounted(() => {
  stopAutoProgress()
})

// 暴露方法给父组件
defineExpose({
  setProgress: (value) => {
    progress.value = Math.min(100, Math.max(0, value))
  },
  complete: () => {
    progress.value = 100
    stopAutoProgress()
  },
})
</script>

<style scoped>
.loading-component {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 20px;
}

.loading-component--fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(2px);
  z-index: 9999;
  min-height: 100vh;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-spinner {
  position: relative;
}

/* Ring Spinner */
.spinner-ring {
  display: inline-block;
  position: relative;
  width: 40px;
  height: 40px;
}

.spinner-ring div {
  box-sizing: border-box;
  display: block;
  position: absolute;
  width: 32px;
  height: 32px;
  margin: 4px;
  border: 3px solid #18a058;
  border-radius: 50%;
  animation: ring-spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
  border-color: #18a058 transparent transparent transparent;
}

.spinner-ring div:nth-child(1) {
  animation-delay: -0.45s;
}
.spinner-ring div:nth-child(2) {
  animation-delay: -0.3s;
}
.spinner-ring div:nth-child(3) {
  animation-delay: -0.15s;
}

@keyframes ring-spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Dots Spinner */
.spinner-dots {
  display: inline-block;
  position: relative;
  width: 40px;
  height: 10px;
}

.spinner-dots div {
  position: absolute;
  top: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #18a058;
  animation: dots-bounce 1.4s infinite ease-in-out both;
}

.spinner-dots div:nth-child(1) {
  left: 0;
  animation-delay: -0.32s;
}
.spinner-dots div:nth-child(2) {
  left: 16px;
  animation-delay: -0.16s;
}
.spinner-dots div:nth-child(3) {
  left: 32px;
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

/* Pulse Spinner */
.spinner-pulse {
  display: inline-block;
  width: 40px;
  height: 40px;
}

.spinner-pulse div {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #18a058;
  animation: pulse-scale 1s infinite ease-in-out;
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

/* Wave Spinner */
.spinner-wave {
  display: inline-block;
  width: 40px;
  height: 40px;
}

.spinner-wave div {
  display: inline-block;
  width: 4px;
  height: 100%;
  background: #18a058;
  animation: wave-stretch 1.2s infinite ease-in-out;
}

.spinner-wave div:nth-child(2) {
  animation-delay: -1.1s;
}
.spinner-wave div:nth-child(3) {
  animation-delay: -1s;
}
.spinner-wave div:nth-child(4) {
  animation-delay: -0.9s;
}
.spinner-wave div:nth-child(5) {
  animation-delay: -0.8s;
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

.loading-text {
  color: #666;
  font-size: 14px;
  text-align: center;
}

.loading-progress {
  width: 200px;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #18a058, #36ad6a);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #999;
}

/* 暗色主题适配 */
@media (prefers-color-scheme: dark) {
  .loading-component--fullscreen {
    background: rgba(0, 0, 0, 0.9);
  }

  .loading-text {
    color: #ccc;
  }

  .progress-bar {
    background: #333;
  }

  .progress-text {
    color: #999;
  }
}
</style>
