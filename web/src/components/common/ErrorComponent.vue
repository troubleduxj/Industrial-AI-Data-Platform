<template>
  <div class="error-component" :class="{ 'error-component--fullscreen': fullscreen }">
    <div class="error-content">
      <div class="error-icon">
        <svg
          width="64"
          height="64"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle cx="12" cy="12" r="10" stroke="#f56565" stroke-width="2" />
          <line x1="15" y1="9" x2="9" y2="15" stroke="#f56565" stroke-width="2" />
          <line x1="9" y1="9" x2="15" y2="15" stroke="#f56565" stroke-width="2" />
        </svg>
      </div>

      <div class="error-title">{{ title }}</div>

      <div v-if="message" class="error-message">{{ message }}</div>

      <div v-if="showDetails && error" class="error-details">
        <details>
          <summary>错误详情</summary>
          <pre>{{ errorDetails }}</pre>
        </details>
      </div>

      <div class="error-actions">
        <button v-if="showRetry" class="error-button error-button--primary" @click="handleRetry">
          重试
        </button>

        <button
          v-if="showGoBack"
          class="error-button error-button--secondary"
          @click="handleGoBack"
        >
          返回
        </button>

        <button
          v-if="showReload"
          class="error-button error-button--secondary"
          @click="handleReload"
        >
          刷新页面
        </button>
      </div>

      <div v-if="suggestions.length > 0" class="error-suggestions">
        <div class="suggestions-title">建议解决方案：</div>
        <ul class="suggestions-list">
          <li v-for="(suggestion, index) in suggestions" :key="index">
            {{ suggestion }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  // 错误对象
  error: {
    type: Error,
    default: null,
  },
  // 错误标题
  title: {
    type: String,
    default: '加载失败',
  },
  // 错误消息
  message: {
    type: String,
    default: '组件加载时发生错误，请稍后重试',
  },
  // 是否全屏显示
  fullscreen: {
    type: Boolean,
    default: false,
  },
  // 是否显示重试按钮
  showRetry: {
    type: Boolean,
    default: true,
  },
  // 是否显示返回按钮
  showGoBack: {
    type: Boolean,
    default: true,
  },
  // 是否显示刷新页面按钮
  showReload: {
    type: Boolean,
    default: false,
  },
  // 是否显示错误详情
  showDetails: {
    type: Boolean,
    default: false,
  },
  // 自定义建议
  customSuggestions: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['retry', 'go-back', 'reload'])

const router = useRouter()

// 错误详情
const errorDetails = computed(() => {
  if (!props.error) return ''

  return {
    name: props.error.name,
    message: props.error.message,
    stack: props.error.stack,
  }
})

// 建议解决方案
const suggestions = computed(() => {
  const defaultSuggestions = []

  if (props.error) {
    const errorMessage = props.error.message.toLowerCase()

    if (errorMessage.includes('loading chunk') || errorMessage.includes('loading css chunk')) {
      defaultSuggestions.push('网络连接可能不稳定，请检查网络连接后重试')
      defaultSuggestions.push('清除浏览器缓存后刷新页面')
    } else if (errorMessage.includes('network')) {
      defaultSuggestions.push('请检查网络连接是否正常')
      defaultSuggestions.push('确认服务器是否可访问')
    } else if (errorMessage.includes('timeout')) {
      defaultSuggestions.push('请求超时，请稍后重试')
      defaultSuggestions.push('检查网络连接速度')
    } else {
      defaultSuggestions.push('刷新页面重新加载')
      defaultSuggestions.push('清除浏览器缓存')
      defaultSuggestions.push('如问题持续存在，请联系技术支持')
    }
  }

  return [...defaultSuggestions, ...props.customSuggestions]
})

// 处理重试
const handleRetry = () => {
  emit('retry')
}

// 处理返回
const handleGoBack = () => {
  if (router.options.history.state.back) {
    router.back()
  } else {
    router.push('/')
  }
  emit('go-back')
}

// 处理刷新页面
const handleReload = () => {
  window.location.reload()
  emit('reload')
}
</script>

<style scoped>
.error-component {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 20px;
}

.error-component--fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(2px);
  z-index: 9999;
  min-height: 100vh;
}

.error-content {
  text-align: center;
  max-width: 500px;
  width: 100%;
}

.error-icon {
  margin-bottom: 20px;
  opacity: 0.8;
}

.error-title {
  font-size: 20px;
  font-weight: 600;
  color: #f56565;
  margin-bottom: 12px;
}

.error-message {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
  line-height: 1.5;
}

.error-details {
  margin-bottom: 20px;
  text-align: left;
}

.error-details details {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 12px;
}

.error-details summary {
  cursor: pointer;
  font-weight: 500;
  color: #495057;
  margin-bottom: 8px;
}

.error-details pre {
  font-size: 12px;
  color: #6c757d;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.error-button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 80px;
}

.error-button--primary {
  background: #18a058;
  color: white;
}

.error-button--primary:hover {
  background: #16a085;
  transform: translateY(-1px);
}

.error-button--secondary {
  background: #f8f9fa;
  color: #495057;
  border: 1px solid #dee2e6;
}

.error-button--secondary:hover {
  background: #e9ecef;
  transform: translateY(-1px);
}

.error-suggestions {
  text-align: left;
  background: #f8f9fa;
  border-radius: 4px;
  padding: 16px;
  border-left: 4px solid #18a058;
}

.suggestions-title {
  font-weight: 500;
  color: #495057;
  margin-bottom: 8px;
}

.suggestions-list {
  margin: 0;
  padding-left: 20px;
  color: #6c757d;
}

.suggestions-list li {
  margin-bottom: 4px;
  font-size: 14px;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .error-component {
    padding: 16px;
  }

  .error-content {
    max-width: 100%;
  }

  .error-actions {
    flex-direction: column;
    align-items: center;
  }

  .error-button {
    width: 100%;
    max-width: 200px;
  }
}

/* 暗色主题适配 */
@media (prefers-color-scheme: dark) {
  .error-component--fullscreen {
    background: rgba(0, 0, 0, 0.95);
  }

  .error-message {
    color: #ccc;
  }

  .error-details details {
    background: #2d3748;
    border-color: #4a5568;
  }

  .error-details summary {
    color: #e2e8f0;
  }

  .error-details pre {
    color: #a0aec0;
  }

  .error-button--secondary {
    background: #2d3748;
    color: #e2e8f0;
    border-color: #4a5568;
  }

  .error-button--secondary:hover {
    background: #4a5568;
  }

  .error-suggestions {
    background: #2d3748;
    border-left-color: #18a058;
  }

  .suggestions-title {
    color: #e2e8f0;
  }

  .suggestions-list {
    color: #a0aec0;
  }
}
</style>
