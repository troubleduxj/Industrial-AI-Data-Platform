<template>
  <div class="breakpoint-provider">
    <slot
      :breakpoint="currentBreakpoint"
      :breakpoints="breakpoints"
      :is-mobile="isMobile"
      :is-tablet="isTablet"
      :is-desktop="isDesktop"
      :screen-width="screenWidth"
      :screen-height="screenHeight"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

/**
 * 断点提供者组件
 * 监听屏幕尺寸变化，提供当前断点信息
 *
 * @component BreakpointProvider
 * @example
 * <BreakpointProvider>
 *   <template #default="{ breakpoint, isMobile }">
 *     <div v-if="isMobile">移动端内容</div>
 *     <div v-else>桌面端内容</div>
 *   </template>
 * </BreakpointProvider>
 */

const props = defineProps({
  // 自定义断点配置
  breakpoints: {
    type: Object,
    default: () => ({
      xs: 0, // 超小屏幕
      sm: 576, // 小屏幕
      md: 768, // 中等屏幕
      lg: 992, // 大屏幕
      xl: 1200, // 超大屏幕
      xxl: 1600, // 超超大屏幕
    }),
  },

  // 防抖延迟（毫秒）
  debounce: {
    type: Number,
    default: 100,
  },
})

const emit = defineEmits(['breakpoint-change', 'resize'])

// 响应式数据
const screenWidth = ref(0)
const screenHeight = ref(0)
const resizeTimer = ref(null)

// 计算属性
const currentBreakpoint = computed(() => {
  const width = screenWidth.value
  const breakpoints = props.breakpoints

  if (width >= breakpoints.xxl) return 'xxl'
  if (width >= breakpoints.xl) return 'xl'
  if (width >= breakpoints.lg) return 'lg'
  if (width >= breakpoints.md) return 'md'
  if (width >= breakpoints.sm) return 'sm'
  return 'xs'
})

const isMobile = computed(() => {
  return ['xs', 'sm'].includes(currentBreakpoint.value)
})

const isTablet = computed(() => {
  return currentBreakpoint.value === 'md'
})

const isDesktop = computed(() => {
  return ['lg', 'xl', 'xxl'].includes(currentBreakpoint.value)
})

// 方法
function updateScreenSize() {
  screenWidth.value = window.innerWidth
  screenHeight.value = window.innerHeight
}

function handleResize() {
  if (resizeTimer.value) {
    clearTimeout(resizeTimer.value)
  }

  resizeTimer.value = setTimeout(() => {
    const oldBreakpoint = currentBreakpoint.value
    updateScreenSize()

    // 如果断点发生变化，触发事件
    if (oldBreakpoint !== currentBreakpoint.value) {
      emit('breakpoint-change', {
        from: oldBreakpoint,
        to: currentBreakpoint.value,
        width: screenWidth.value,
        height: screenHeight.value,
      })
    }

    emit('resize', {
      width: screenWidth.value,
      height: screenHeight.value,
      breakpoint: currentBreakpoint.value,
    })
  }, props.debounce)
}

// 生命周期
onMounted(() => {
  updateScreenSize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeTimer.value) {
    clearTimeout(resizeTimer.value)
  }
})

// 暴露方法和数据
defineExpose({
  currentBreakpoint,
  screenWidth,
  screenHeight,
  isMobile,
  isTablet,
  isDesktop,
  breakpoints: props.breakpoints,
})
</script>

<style scoped>
.breakpoint-provider {
  width: 100%;
  height: 100%;
}
</style>
