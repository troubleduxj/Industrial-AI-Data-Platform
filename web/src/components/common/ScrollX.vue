<template>
  <div ref="wrapperRef" class="scroll-x-wrapper" :class="wrapperClass" @wheel.prevent="handleWheel">
    <!-- 左侧滚动按钮 -->
    <div
      v-if="showArrows && isOverflow && showLeftArrow"
      class="scroll-arrow scroll-arrow--left"
      :class="{ 'scroll-arrow--disabled': !canScrollLeft }"
      @click="scrollLeft"
    >
      <n-icon :size="arrowSize">
        <ChevronBackOutline />
      </n-icon>
    </div>

    <!-- 右侧滚动按钮 -->
    <div
      v-if="showArrows && isOverflow && showRightArrow"
      class="scroll-arrow scroll-arrow--right"
      :class="{ 'scroll-arrow--disabled': !canScrollRight }"
      @click="scrollRight"
    >
      <n-icon :size="arrowSize">
        <ChevronForwardOutline />
      </n-icon>
    </div>

    <!-- 滚动内容容器 -->
    <div ref="contentRef" class="scroll-content" :class="contentClass" :style="contentStyle">
      <slot />
    </div>

    <!-- 滚动指示器 -->
    <div v-if="showIndicator && isOverflow" class="scroll-indicator">
      <div class="scroll-indicator-bar" :style="indicatorStyle" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { NIcon } from 'naive-ui'
import { ChevronBackOutline, ChevronForwardOutline } from '@vicons/ionicons5'
import { debounce } from '@/utils'

/**
 * 水平滚动组件
 * 提供平滑的水平滚动功能，支持鼠标滚轮和箭头按钮
 *
 * @component ScrollX
 * @example
 * <ScrollX :show-arrows="true" :show-indicator="true">
 *   <div class="flex gap-4">
 *     <div v-for="item in items" :key="item.id">{{ item.name }}</div>
 *   </div>
 * </ScrollX>
 */

const props = defineProps({
  // 是否显示滚动箭头
  showArrows: {
    type: Boolean,
    default: true,
  },

  // 是否显示滚动指示器
  showIndicator: {
    type: Boolean,
    default: false,
  },

  // 滚动步长（像素）
  scrollStep: {
    type: Number,
    default: 120,
  },

  // 箭头图标大小
  arrowSize: {
    type: Number,
    default: 18,
  },

  // 是否显示左箭头
  showLeftArrow: {
    type: Boolean,
    default: true,
  },

  // 是否显示右箭头
  showRightArrow: {
    type: Boolean,
    default: true,
  },

  // 滚动动画持续时间
  scrollDuration: {
    type: Number,
    default: 300,
  },

  // 是否启用平滑滚动
  smoothScroll: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['scroll', 'scroll-start', 'scroll-end'])

// 响应式引用
const wrapperRef = ref(null)
const contentRef = ref(null)
const translateX = ref(0)
const isOverflow = ref(false)
const isScrolling = ref(false)

// 计算属性
const wrapperClass = computed(() => ({
  'scroll-x-wrapper--overflow': isOverflow.value,
  'scroll-x-wrapper--scrolling': isScrolling.value,
}))

const contentClass = computed(() => ({
  'scroll-content--smooth': props.smoothScroll,
  'scroll-content--overflow': isOverflow.value && props.showArrows,
}))

const contentStyle = computed(() => ({
  transform: `translateX(${translateX.value}px)`,
  transitionDuration: props.smoothScroll ? `${props.scrollDuration}ms` : '0ms',
}))

const canScrollLeft = computed(() => translateX.value < 0)
const canScrollRight = computed(() => {
  if (!wrapperRef.value || !contentRef.value) return false
  const wrapperWidth = wrapperRef.value.offsetWidth
  const contentWidth = contentRef.value.offsetWidth
  return Math.abs(translateX.value) < contentWidth - wrapperWidth
})

const indicatorStyle = computed(() => {
  if (!wrapperRef.value || !contentRef.value) return {}

  const wrapperWidth = wrapperRef.value.offsetWidth
  const contentWidth = contentRef.value.offsetWidth
  const scrollRatio = Math.abs(translateX.value) / (contentWidth - wrapperWidth)
  const indicatorWidth = (wrapperWidth / contentWidth) * 100
  const indicatorLeft = scrollRatio * (100 - indicatorWidth)

  return {
    width: `${indicatorWidth}%`,
    left: `${indicatorLeft}%`,
  }
})

// 防抖的溢出检查
const checkOverflow = debounce(() => {
  if (!wrapperRef.value || !contentRef.value) return

  const wrapperWidth = wrapperRef.value.offsetWidth
  const contentWidth = contentRef.value.offsetWidth
  isOverflow.value = contentWidth > wrapperWidth

  // 重置位置
  resetTranslateX()
}, 100)

// 重置滚动位置
const resetTranslateX = debounce(() => {
  if (!wrapperRef.value || !contentRef.value) return

  const wrapperWidth = wrapperRef.value.offsetWidth
  const contentWidth = contentRef.value.offsetWidth

  if (!isOverflow.value) {
    translateX.value = 0
  } else {
    // 确保不超出边界
    const maxTranslateX = 0
    const minTranslateX = wrapperWidth - contentWidth
    translateX.value = Math.max(minTranslateX, Math.min(maxTranslateX, translateX.value))
  }
}, 50)

// 滚动方法
function scrollTo(targetX, smooth = props.smoothScroll) {
  if (!wrapperRef.value || !contentRef.value) return

  const wrapperWidth = wrapperRef.value.offsetWidth
  const contentWidth = contentRef.value.offsetWidth

  if (contentWidth <= wrapperWidth) return

  const maxTranslateX = 0
  const minTranslateX = wrapperWidth - contentWidth
  const clampedX = Math.max(minTranslateX, Math.min(maxTranslateX, targetX))

  if (smooth) {
    isScrolling.value = true
    setTimeout(() => {
      isScrolling.value = false
    }, props.scrollDuration)
  }

  translateX.value = clampedX
  emit('scroll', {
    translateX: clampedX,
    canScrollLeft: clampedX < 0,
    canScrollRight: Math.abs(clampedX) < contentWidth - wrapperWidth,
  })
}

function scrollLeft() {
  if (!canScrollLeft.value) return
  emit('scroll-start', 'left')
  scrollTo(translateX.value + props.scrollStep)
}

function scrollRight() {
  if (!canScrollRight.value) return
  emit('scroll-start', 'right')
  scrollTo(translateX.value - props.scrollStep)
}

function handleWheel(event) {
  if (!isOverflow.value) return

  const delta = event.deltaY || event.wheelDelta
  const scrollAmount = delta > 0 ? -props.scrollStep : props.scrollStep

  scrollTo(translateX.value + scrollAmount)
}

// 滚动到指定元素
function scrollToElement(element, offset = 0) {
  if (!wrapperRef.value || !contentRef.value || !element) return

  const wrapperWidth = wrapperRef.value.offsetWidth
  const elementRect = element.getBoundingClientRect()
  const wrapperRect = wrapperRef.value.getBoundingClientRect()
  const elementLeft = elementRect.left - wrapperRect.left + Math.abs(translateX.value)

  // 计算目标位置
  let targetX = translateX.value

  // 如果元素在左侧不可见区域
  if (elementLeft < Math.abs(translateX.value)) {
    targetX = -(elementLeft - offset)
  }
  // 如果元素在右侧不可见区域
  else if (elementLeft + elementRect.width > Math.abs(translateX.value) + wrapperWidth) {
    targetX = -(elementLeft + elementRect.width - wrapperWidth + offset)
  }

  scrollTo(targetX)
}

// 生命周期
onMounted(() => {
  checkOverflow()

  // 监听窗口大小变化
  window.addEventListener('resize', checkOverflow)

  // 监听内容变化
  if (contentRef.value) {
    const resizeObserver = new ResizeObserver(checkOverflow)
    resizeObserver.observe(contentRef.value)

    onUnmounted(() => {
      resizeObserver.disconnect()
    })
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkOverflow)
})

// 暴露方法
defineExpose({
  scrollTo,
  scrollLeft,
  scrollRight,
  scrollToElement,
  checkOverflow,
  reset: () => scrollTo(0),
})
</script>

<style scoped>
.scroll-x-wrapper {
  position: relative;
  display: flex;
  overflow: hidden;
  background-color: var(--bg-color, #fff);
  border-radius: var(--border-radius, 6px);
  transition: all 0.3s ease;
}

.scroll-x-wrapper--overflow {
  /* 溢出时的样式 */
}

.scroll-x-wrapper--scrolling {
  /* 滚动时的样式 */
}

/* 滚动内容 */
.scroll-content {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  padding: 0 12px;
  transition: transform 0.3s ease;
  min-width: 100%;
}

.scroll-content--smooth {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.scroll-content--overflow {
  padding-left: 40px;
  padding-right: 40px;
}

/* 滚动箭头 */
.scroll-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-color, #fff);
  border: 1px solid var(--border-color, #e0e0e6);
  border-radius: 50%;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.scroll-arrow:hover {
  background-color: var(--hover-bg-color, #f5f5f5);
  border-color: var(--primary-color, #18a058);
  transform: translateY(-50%) scale(1.05);
}

.scroll-arrow:active {
  transform: translateY(-50%) scale(0.95);
}

.scroll-arrow--disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

.scroll-arrow--left {
  left: 8px;
}

.scroll-arrow--right {
  right: 8px;
}

/* 滚动指示器 */
.scroll-indicator {
  position: absolute;
  bottom: 4px;
  left: 12px;
  right: 12px;
  height: 2px;
  background-color: var(--indicator-bg-color, #e0e0e6);
  border-radius: 1px;
  overflow: hidden;
}

.scroll-indicator-bar {
  height: 100%;
  background-color: var(--primary-color, #18a058);
  border-radius: 1px;
  transition: all 0.3s ease;
}

/* 暗色主题适配 */
.dark .scroll-x-wrapper {
  --bg-color: #2d2d30;
  --border-color: #48484e;
  --hover-bg-color: #3a3a3e;
  --indicator-bg-color: #48484e;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .scroll-content {
    padding: 0 8px;
  }

  .scroll-content--overflow {
    padding-left: 36px;
    padding-right: 36px;
  }

  .scroll-arrow {
    width: 28px;
    height: 28px;
  }

  .scroll-arrow--left {
    left: 6px;
  }

  .scroll-arrow--right {
    right: 6px;
  }

  .scroll-indicator {
    left: 8px;
    right: 8px;
  }
}

/* 动画效果 */
@keyframes scrollArrowPulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.scroll-x-wrapper--scrolling .scroll-arrow {
  animation: scrollArrowPulse 0.6s ease-in-out;
}

/* 无障碍访问 */
.scroll-arrow:focus {
  outline: 2px solid var(--primary-color, #18a058);
  outline-offset: 2px;
}

/* 高对比度模式 */
@media (prefers-contrast: high) {
  .scroll-arrow {
    border-width: 2px;
  }

  .scroll-indicator-bar {
    background-color: var(--text-color, #000);
  }
}

/* 减少动画模式 */
@media (prefers-reduced-motion: reduce) {
  .scroll-content,
  .scroll-content--smooth,
  .scroll-arrow,
  .scroll-indicator-bar {
    transition: none;
  }
}
</style>
