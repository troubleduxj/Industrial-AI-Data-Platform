<template>
  <div
    ref="containerRef"
    class="virtual-scroll-container"
    :style="containerStyle"
    @scroll="handleScroll"
  >
    <!-- 占位元素，用于撑开滚动条 -->
    <div class="virtual-scroll-phantom" :style="{ height: totalHeight + 'px' }"></div>

    <!-- 可视区域内容 -->
    <div class="virtual-scroll-content" :style="contentStyle">
      <div
        v-for="(item, index) in visibleItems"
        :key="getItemKey(item, startIndex + index)"
        class="virtual-scroll-item"
        :style="getItemStyle(startIndex + index)"
        :data-index="startIndex + index"
      >
        <slot :item="item" :index="startIndex + index" :is-visible="true">
          {{ item }}
        </slot>
      </div>
    </div>

    <!-- 加载更多指示器 -->
    <div v-if="hasMore && isLoadingMore" class="virtual-scroll-loading">
      <slot name="loading">
        <div class="loading-indicator">
          <div class="loading-spinner"></div>
          <span>加载中...</span>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick, reactive } from 'vue'

const props = defineProps({
  // 数据列表
  items: {
    type: Array,
    required: true,
  },
  // 每项的高度（固定高度模式）
  itemHeight: {
    type: Number,
    default: 50,
  },
  // 容器高度
  height: {
    type: [Number, String],
    default: 400,
  },
  // 缓冲区大小（渲染可视区域外的项目数量）
  buffer: {
    type: Number,
    default: 5,
  },
  // 是否启用动态高度
  dynamicHeight: {
    type: Boolean,
    default: false,
  },
  // 预估项目高度（动态高度模式）
  estimatedItemHeight: {
    type: Number,
    default: 50,
  },
  // 获取项目唯一键的函数
  keyField: {
    type: [String, Function],
    default: 'id',
  },
  // 是否支持无限滚动
  infinite: {
    type: Boolean,
    default: false,
  },
  // 是否还有更多数据
  hasMore: {
    type: Boolean,
    default: false,
  },
  // 触发加载更多的距离
  loadMoreThreshold: {
    type: Number,
    default: 100,
  },
  // 是否正在加载更多
  isLoadingMore: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['scroll', 'load-more', 'visible-change'])

// 引用
const containerRef = ref(null)

// 状态
const state = reactive({
  scrollTop: 0,
  containerHeight: 0,
  startIndex: 0,
  endIndex: 0,
  itemHeights: new Map(), // 动态高度缓存
  totalHeight: 0,
  isScrolling: false,
  scrollTimer: null,
})

// 计算属性
const containerStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  overflow: 'auto',
  position: 'relative',
}))

const visibleItems = computed(() => {
  return props.items.slice(state.startIndex, state.endIndex + 1)
})

const contentStyle = computed(() => ({
  transform: `translateY(${getOffsetY()}px)`,
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
}))

// 获取项目唯一键
const getItemKey = (item, index) => {
  if (typeof props.keyField === 'function') {
    return props.keyField(item, index)
  }
  return item[props.keyField] || index
}

// 获取项目样式
const getItemStyle = (index) => {
  if (props.dynamicHeight) {
    return {}
  }
  return {
    height: `${props.itemHeight}px`,
    lineHeight: `${props.itemHeight}px`,
  }
}

// 获取偏移量
const getOffsetY = () => {
  if (props.dynamicHeight) {
    let offset = 0
    for (let i = 0; i < state.startIndex; i++) {
      offset += state.itemHeights.get(i) || props.estimatedItemHeight
    }
    return offset
  }
  return state.startIndex * props.itemHeight
}

// 计算总高度
const calculateTotalHeight = () => {
  if (props.dynamicHeight) {
    let height = 0
    for (let i = 0; i < props.items.length; i++) {
      height += state.itemHeights.get(i) || props.estimatedItemHeight
    }
    state.totalHeight = height
  } else {
    state.totalHeight = props.items.length * props.itemHeight
  }
}

// 计算可视范围
const calculateVisibleRange = () => {
  const containerHeight = state.containerHeight
  const scrollTop = state.scrollTop

  if (props.dynamicHeight) {
    // 动态高度模式
    let startIndex = 0
    let endIndex = 0
    let accumulatedHeight = 0

    // 找到开始索引
    for (let i = 0; i < props.items.length; i++) {
      const itemHeight = state.itemHeights.get(i) || props.estimatedItemHeight
      if (accumulatedHeight + itemHeight > scrollTop) {
        startIndex = Math.max(0, i - props.buffer)
        break
      }
      accumulatedHeight += itemHeight
    }

    // 找到结束索引
    accumulatedHeight = getOffsetY()
    for (let i = startIndex; i < props.items.length; i++) {
      const itemHeight = state.itemHeights.get(i) || props.estimatedItemHeight
      accumulatedHeight += itemHeight
      if (
        accumulatedHeight >
        scrollTop + containerHeight + props.buffer * props.estimatedItemHeight
      ) {
        endIndex = i
        break
      }
    }

    if (endIndex === 0) {
      endIndex = props.items.length - 1
    }

    state.startIndex = startIndex
    state.endIndex = Math.min(endIndex, props.items.length - 1)
  } else {
    // 固定高度模式
    const visibleStart = Math.floor(scrollTop / props.itemHeight)
    const visibleEnd = Math.ceil((scrollTop + containerHeight) / props.itemHeight)

    state.startIndex = Math.max(0, visibleStart - props.buffer)
    state.endIndex = Math.min(props.items.length - 1, visibleEnd + props.buffer)
  }
}

// 处理滚动事件
const handleScroll = (event) => {
  const { scrollTop, scrollHeight, clientHeight } = event.target

  state.scrollTop = scrollTop
  state.isScrolling = true

  // 清除之前的定时器
  if (state.scrollTimer) {
    clearTimeout(state.scrollTimer)
  }

  // 设置滚动结束定时器
  state.scrollTimer = setTimeout(() => {
    state.isScrolling = false
  }, 150)

  // 计算可视范围
  calculateVisibleRange()

  // 发出滚动事件
  emit('scroll', {
    scrollTop,
    scrollHeight,
    clientHeight,
    startIndex: state.startIndex,
    endIndex: state.endIndex,
  })

  // 检查是否需要加载更多
  if (props.infinite && props.hasMore && !props.isLoadingMore) {
    const distanceToBottom = scrollHeight - scrollTop - clientHeight
    if (distanceToBottom <= props.loadMoreThreshold) {
      emit('load-more')
    }
  }

  // 发出可视区域变化事件
  emit('visible-change', {
    startIndex: state.startIndex,
    endIndex: state.endIndex,
    visibleItems: visibleItems.value,
  })
}

// 更新项目高度（动态高度模式）
const updateItemHeight = (index, height) => {
  if (props.dynamicHeight) {
    const oldHeight = state.itemHeights.get(index) || props.estimatedItemHeight
    if (oldHeight !== height) {
      state.itemHeights.set(index, height)
      calculateTotalHeight()
    }
  }
}

// 滚动到指定索引
const scrollToIndex = (index, behavior = 'smooth') => {
  if (!containerRef.value) return

  let scrollTop = 0

  if (props.dynamicHeight) {
    for (let i = 0; i < index; i++) {
      scrollTop += state.itemHeights.get(i) || props.estimatedItemHeight
    }
  } else {
    scrollTop = index * props.itemHeight
  }

  containerRef.value.scrollTo({
    top: scrollTop,
    behavior,
  })
}

// 滚动到顶部
const scrollToTop = (behavior = 'smooth') => {
  if (containerRef.value) {
    containerRef.value.scrollTo({
      top: 0,
      behavior,
    })
  }
}

// 滚动到底部
const scrollToBottom = (behavior = 'smooth') => {
  if (containerRef.value) {
    containerRef.value.scrollTo({
      top: state.totalHeight,
      behavior,
    })
  }
}

// 获取可视区域信息
const getVisibleRange = () => ({
  startIndex: state.startIndex,
  endIndex: state.endIndex,
  visibleItems: visibleItems.value,
})

// 初始化
const init = () => {
  if (!containerRef.value) return

  state.containerHeight = containerRef.value.clientHeight
  calculateTotalHeight()
  calculateVisibleRange()
}

// 监听数据变化
watch(
  () => props.items,
  () => {
    nextTick(() => {
      calculateTotalHeight()
      calculateVisibleRange()
    })
  },
  { deep: true }
)

// 监听容器高度变化
const resizeObserver = ref(null)

onMounted(() => {
  init()

  // 监听容器大小变化
  if (window.ResizeObserver) {
    resizeObserver.value = new ResizeObserver((entries) => {
      for (const entry of entries) {
        state.containerHeight = entry.contentRect.height
        calculateVisibleRange()
      }
    })

    if (containerRef.value) {
      resizeObserver.value.observe(containerRef.value)
    }
  }

  // 动态高度模式下，观察项目高度变化
  if (props.dynamicHeight) {
    nextTick(() => {
      const items = containerRef.value?.querySelectorAll('.virtual-scroll-item')
      items?.forEach((item, index) => {
        const actualIndex = state.startIndex + index
        const height = item.offsetHeight
        updateItemHeight(actualIndex, height)
      })
    })
  }
})

onUnmounted(() => {
  if (state.scrollTimer) {
    clearTimeout(state.scrollTimer)
  }

  if (resizeObserver.value) {
    resizeObserver.value.disconnect()
  }
})

// 暴露方法
defineExpose({
  scrollToIndex,
  scrollToTop,
  scrollToBottom,
  getVisibleRange,
  updateItemHeight,
})
</script>

<style scoped>
.virtual-scroll-container {
  position: relative;
  overflow: auto;
}

.virtual-scroll-phantom {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: -1;
}

.virtual-scroll-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
}

.virtual-scroll-item {
  box-sizing: border-box;
}

.virtual-scroll-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  position: sticky;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #18a058;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 滚动条样式 */
.virtual-scroll-container::-webkit-scrollbar {
  width: 6px;
}

.virtual-scroll-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.virtual-scroll-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.virtual-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 暗色主题适配 */
@media (prefers-color-scheme: dark) {
  .virtual-scroll-loading {
    background: rgba(0, 0, 0, 0.9);
  }

  .loading-indicator {
    color: #ccc;
  }

  .virtual-scroll-container::-webkit-scrollbar-track {
    background: #2d3748;
  }

  .virtual-scroll-container::-webkit-scrollbar-thumb {
    background: #4a5568;
  }

  .virtual-scroll-container::-webkit-scrollbar-thumb:hover {
    background: #718096;
  }
}
</style>
