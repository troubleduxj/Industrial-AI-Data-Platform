# 交互组件库

本目录包含统一的交互状态和动画组件，提供一致的用户反馈和视觉体验。

## 组件列表

### LoadingState
统一加载状态组件，提供多种加载指示器和进度显示。

**功能特性:**
- 多种加载指示器类型（spinner、dots、pulse、wave、skeleton、progress）
- 可配置的尺寸和颜色主题
- 进度条显示
- 全屏覆盖模式
- 自定义加载文本
- 响应式设计

**使用示例:**
```vue
<template>
  <!-- 基础加载状态 -->
  <LoadingState 
    type="spinner" 
    text="正在加载..." 
    size="medium"
  />
  
  <!-- 带进度的加载状态 -->
  <LoadingState 
    type="progress"
    text="上传中..."
    :progress="uploadProgress"
    :show-progress="true"
  />
  
  <!-- 全屏覆盖加载 -->
  <LoadingState 
    :overlay="true"
    text="系统初始化中..."
    type="pulse"
  />
  
  <!-- 骨架屏加载 -->
  <LoadingState 
    type="skeleton"
    size="large"
  />
</template>

<script setup>
const uploadProgress = ref(0)

// 模拟上传进度
const simulateUpload = () => {
  const timer = setInterval(() => {
    uploadProgress.value += 10
    if (uploadProgress.value >= 100) {
      clearInterval(timer)
    }
  }, 200)
}
</script>
```

### TransitionWrapper
过渡动画包装器组件，提供统一的过渡动画效果。

**功能特性:**
- 多种预定义动画类型
- 可配置的动画持续时间和缓动函数
- 支持自定义过渡名称
- 动画事件回调
- 延迟动画支持
- 减少动画模式适配

**使用示例:**
```vue
<template>
  <!-- 基础淡入淡出 -->
  <TransitionWrapper type="fade" :duration="300">
    <div v-if="show">淡入淡出内容</div>
  </TransitionWrapper>
  
  <!-- 滑动动画 -->
  <TransitionWrapper type="slide-up" :duration="400" easing="ease-out">
    <Card v-if="showCard">卡片内容</Card>
  </TransitionWrapper>
  
  <!-- 缩放动画 -->
  <TransitionWrapper 
    type="scale" 
    mode="out-in"
    @before-enter="handleBeforeEnter"
    @after-leave="handleAfterLeave"
  >
    <component :is="currentComponent" :key="componentKey" />
  </TransitionWrapper>
  
  <!-- 弹跳动画 -->
  <TransitionWrapper type="bounce" :delay="100">
    <Button v-if="showButton" @click="handleClick">
      点击我
    </Button>
  </TransitionWrapper>
</template>

<script setup>
const show = ref(true)
const showCard = ref(false)
const currentComponent = ref('ComponentA')

const toggleShow = () => {
  show.value = !show.value
}

const handleBeforeEnter = (el) => {
  console.log('动画开始前')
}

const handleAfterLeave = (el) => {
  console.log('动画结束后')
}
</script>
```

### FeedbackToast
反馈提示组件，提供统一的消息提示和反馈机制。

**功能特性:**
- 多种提示类型（success、info、warning、error）
- 可配置的显示位置
- 自动关闭和手动关闭
- 进度条显示
- 鼠标悬停暂停
- 最大显示数量限制
- 响应式设计

**使用示例:**
```vue
<template>
  <div>
    <n-space>
      <n-button @click="showSuccess">成功提示</n-button>
      <n-button @click="showWarning">警告提示</n-button>
      <n-button @click="showError">错误提示</n-button>
      <n-button @click="showProgress">进度提示</n-button>
    </n-space>
    
    <!-- Toast容器 -->
    <FeedbackToast 
      ref="toastRef"
      position="top-right"
      :max-count="3"
    />
  </div>
</template>

<script setup>
const toastRef = ref()

const showSuccess = () => {
  toastRef.value.success('操作成功！', {
    title: '成功',
    duration: 3000
  })
}

const showWarning = () => {
  toastRef.value.warning('请注意检查输入', {
    title: '警告',
    closable: true
  })
}

const showError = () => {
  toastRef.value.error('操作失败，请重试', {
    title: '错误',
    duration: 5000,
    onClick: (toast) => {
      console.log('点击了错误提示', toast)
    }
  })
}

const showProgress = () => {
  toastRef.value.show({
    type: 'info',
    message: '文件上传中...',
    showProgress: true,
    duration: 5000
  })
}
</script>
```

## 组合式函数

### useLoading
加载状态管理组合式函数。

**使用示例:**
```vue
<script setup>
import { useLoading } from '@/composables/useInteraction'

const { 
  loading, 
  loadingText, 
  loadingProgress,
  startLoading, 
  updateProgress,
  stopLoading, 
  withLoading 
} = useLoading()

// 基础用法
const handleSubmit = async () => {
  startLoading('提交中...')
  try {
    await submitData()
  } finally {
    stopLoading()
  }
}

// 带进度的加载
const handleUpload = async () => {
  startLoading('上传中...')
  
  for (let i = 0; i <= 100; i += 10) {
    updateProgress(i, `上传进度 ${i}%`)
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  
  stopLoading()
}

// 异步操作包装器
const handleSave = async () => {
  const result = await withLoading(
    () => saveData(),
    '保存中...',
    true // 显示全局加载
  )
  console.log('保存结果:', result)
}
</script>

<template>
  <div>
    <LoadingState 
      v-if="loading"
      :text="loadingText"
      :progress="loadingProgress"
      :show-progress="loadingProgress !== null"
    />
    
    <n-button @click="handleSubmit" :loading="loading">
      提交
    </n-button>
  </div>
</template>
```

### useFeedback
反馈提示管理组合式函数。

**使用示例:**
```vue
<script setup>
import { useFeedback } from '@/composables/useInteraction'

const { 
  toastRef,
  success, 
  info, 
  warning, 
  error,
  removeToast,
  clearToasts 
} = useFeedback()

const handleSuccess = () => {
  success('操作成功！', {
    title: '成功',
    duration: 3000
  })
}

const handleError = () => {
  const toastId = error('操作失败', {
    title: '错误',
    duration: 0, // 不自动关闭
    onClick: () => {
      removeToast(toastId)
    }
  })
}

const handleClearAll = () => {
  clearToasts()
}
</script>

<template>
  <div>
    <n-space>
      <n-button @click="handleSuccess">显示成功</n-button>
      <n-button @click="handleError">显示错误</n-button>
      <n-button @click="handleClearAll">清除所有</n-button>
    </n-space>
    
    <FeedbackToast ref="toastRef" />
  </div>
</template>
```

### useAnimation
动画控制管理组合式函数。

**使用示例:**
```vue
<script setup>
import { useAnimation } from '@/composables/useInteraction'

const { 
  animating,
  fadeIn, 
  fadeOut, 
  slideIn, 
  slideOut,
  scale,
  shake,
  bounce 
} = useAnimation()

const elementRef = ref()

const handleFadeIn = async () => {
  await fadeIn(elementRef.value, 500)
  console.log('淡入完成')
}

const handleShake = () => {
  shake(elementRef.value, 15, 600)
}

const handleBounce = () => {
  bounce(elementRef.value, 30, 800)
}

const handleScale = async () => {
  await scale(elementRef.value, 0, 1.2, 300)
  await scale(elementRef.value, 1.2, 1, 200)
}
</script>

<template>
  <div>
    <div ref="elementRef" class="animated-element">
      动画元素
    </div>
    
    <n-space>
      <n-button @click="handleFadeIn" :disabled="animating">
        淡入
      </n-button>
      <n-button @click="handleShake">
        震动
      </n-button>
      <n-button @click="handleBounce">
        弹跳
      </n-button>
      <n-button @click="handleScale">
        缩放
      </n-button>
    </n-space>
  </div>
</template>
```

### useInteraction
交互状态组合管理函数。

**使用示例:**
```vue
<script setup>
import { useInteraction } from '@/composables/useInteraction'

const {
  loading,
  success,
  error,
  withFeedback,
  animatedToggle,
  confirm
} = useInteraction()

const elementRef = ref()
const showElement = ref(true)

// 带反馈的异步操作
const handleSave = async () => {
  await withFeedback(
    () => saveData(),
    {
      loadingText: '保存中...',
      successMessage: '保存成功',
      errorMessage: '保存失败'
    }
  )
}

// 带动画的状态切换
const toggleElement = async () => {
  showElement.value = !showElement.value
  await animatedToggle(elementRef.value, showElement.value)
}

// 确认对话框
const handleDelete = async () => {
  const confirmed = await confirm('确定要删除这个项目吗？', {
    title: '删除确认',
    type: 'error'
  })
  
  if (confirmed) {
    await withFeedback(
      () => deleteItem(),
      {
        loadingText: '删除中...',
        successMessage: '删除成功',
        errorMessage: '删除失败'
      }
    )
  }
}
</script>

<template>
  <div>
    <div ref="elementRef" v-show="showElement">
      可切换的元素
    </div>
    
    <n-space>
      <n-button @click="handleSave" :loading="loading">
        保存
      </n-button>
      <n-button @click="toggleElement">
        切换显示
      </n-button>
      <n-button @click="handleDelete" type="error">
        删除
      </n-button>
    </n-space>
  </div>
</template>
```

### useFormInteraction
表单交互增强函数。

**使用示例:**
```vue
<script setup>
import { useFormInteraction } from '@/composables/useInteraction'

const formRef = ref()
const formData = ref({
  name: '',
  email: ''
})

const {
  submitting,
  validating,
  submitForm,
  resetForm,
  success,
  error
} = useFormInteraction(formRef)

const handleSubmit = async () => {
  await submitForm(
    () => submitFormData(formData.value),
    {
      loadingText: '提交中...',
      successMessage: '提交成功',
      errorMessage: '提交失败，请检查输入'
    }
  )
}

const handleReset = () => {
  resetForm(true) // 显示确认对话框
}
</script>

<template>
  <StandardForm
    ref="formRef"
    v-model="formData"
    :fields="formFields"
    @submit="handleSubmit"
  >
    <template #actions>
      <n-space>
        <n-button 
          @click="handleReset"
          :disabled="submitting"
        >
          重置
        </n-button>
        <n-button 
          type="primary"
          @click="handleSubmit"
          :loading="submitting || validating"
        >
          提交
        </n-button>
      </n-space>
    </template>
  </StandardForm>
</template>
```

## 动画类型

### 预定义动画
- `fade` - 淡入淡出
- `slide-up` - 向上滑动
- `slide-down` - 向下滑动
- `slide-left` - 向左滑动
- `slide-right` - 向右滑动
- `scale` - 缩放
- `zoom` - 放大
- `flip` - 翻转
- `bounce` - 弹跳
- `elastic` - 弹性
- `rotate` - 旋转

### 自定义动画
```vue
<template>
  <TransitionWrapper 
    custom-name="my-custom-transition"
    :duration="500"
  >
    <div v-if="show">自定义动画内容</div>
  </TransitionWrapper>
</template>

<style>
.my-custom-transition-enter-active,
.my-custom-transition-leave-active {
  transition: all 0.5s ease;
}

.my-custom-transition-enter-from {
  opacity: 0;
  transform: translateX(-100px) rotate(-180deg);
}

.my-custom-transition-leave-to {
  opacity: 0;
  transform: translateX(100px) rotate(180deg);
}
</style>
```

## 配置选项

### 全局配置
```javascript
import { INTERACTION_CONFIG } from '@/components/interaction'

// 修改默认配置
INTERACTION_CONFIG.durations.normal = 400
INTERACTION_CONFIG.toast.defaultDuration = 4000
INTERACTION_CONFIG.loading.defaultText = '请稍候...'
```

### 主题定制
```css
:root {
  /* 加载状态主题 */
  --loading-primary-color: #18a058;
  --loading-bg-color: rgba(255, 255, 255, 0.9);
  --loading-text-color: #333;
  
  /* Toast主题 */
  --toast-success-color: #18a058;
  --toast-info-color: #2080f0;
  --toast-warning-color: #f0a020;
  --toast-error-color: #d03050;
  --toast-bg-color: #fff;
  --toast-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  
  /* 动画主题 */
  --animation-duration-fast: 150ms;
  --animation-duration-normal: 300ms;
  --animation-duration-slow: 500ms;
}

.dark {
  --loading-bg-color: rgba(24, 24, 28, 0.9);
  --loading-text-color: #fff;
  --toast-bg-color: #2d2d30;
}
```

## 无障碍访问

### ARIA支持
```vue
<template>
  <!-- 加载状态 -->
  <LoadingState 
    role="status"
    aria-live="polite"
    :aria-label="loadingText"
  />
  
  <!-- Toast提示 -->
  <FeedbackToast 
    role="alert"
    aria-live="assertive"
  />
</template>
```

### 键盘导航
```vue
<template>
  <div
    tabindex="0"
    @keydown.enter="handleAction"
    @keydown.space="handleAction"
    @keydown.esc="handleCancel"
  >
    交互元素
  </div>
</template>
```

## 性能优化

### 动画性能
```css
/* 使用transform和opacity进行动画 */
.optimized-animation {
  will-change: transform, opacity;
  transform: translateZ(0); /* 启用硬件加速 */
}

/* 减少重绘和回流 */
.smooth-animation {
  backface-visibility: hidden;
  perspective: 1000px;
}
```

### 内存管理
```javascript
// 清理定时器和事件监听器
onUnmounted(() => {
  clearToasts()
  // 清理其他资源
})
```

## 测试指南

### 单元测试
```javascript
import { mount } from '@vue/test-utils'
import LoadingState from '../LoadingState.vue'

describe('LoadingState', () => {
  it('shows loading text', () => {
    const wrapper = mount(LoadingState, {
      props: { text: '加载中...' }
    })
    
    expect(wrapper.find('.loading-text').text()).toBe('加载中...')
  })
  
  it('shows progress when provided', () => {
    const wrapper = mount(LoadingState, {
      props: { 
        progress: 50,
        showProgress: true
      }
    })
    
    expect(wrapper.find('.progress-text').text()).toBe('50%')
  })
})
```

### 集成测试
```javascript
import { useInteraction } from '@/composables/useInteraction'

describe('useInteraction', () => {
  it('manages loading state correctly', async () => {
    const { loading, withLoading } = useInteraction()
    
    expect(loading.value).toBe(false)
    
    const promise = withLoading(async () => {
      expect(loading.value).toBe(true)
      await new Promise(resolve => setTimeout(resolve, 100))
      return 'result'
    })
    
    const result = await promise
    expect(loading.value).toBe(false)
    expect(result).toBe('result')
  })
})
```

## 最佳实践

1. **一致性**: 在整个应用中使用统一的交互模式
2. **反馈及时**: 为用户操作提供即时的视觉反馈
3. **性能优先**: 使用高性能的动画属性（transform、opacity）
4. **可访问性**: 确保交互组件支持键盘导航和屏幕阅读器
5. **渐进增强**: 在不支持动画的环境中提供降级方案

## 常见问题

### Q: 如何自定义加载指示器？
A: 可以通过 `type` 属性选择不同类型，或使用 `customStyle` 属性自定义样式。

### Q: 如何控制Toast的显示位置？
A: 使用 `position` 属性设置显示位置，支持6个预定义位置。

### Q: 如何实现复杂的动画序列？
A: 使用 `useAnimation` 组合式函数，结合 `async/await` 实现动画序列。

### Q: 如何在减少动画模式下优化体验？
A: 组件已内置 `prefers-reduced-motion` 媒体查询支持，会自动禁用动画。