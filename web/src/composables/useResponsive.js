/**
 * 响应式布局组合式函数
 * 提供响应式断点检测和屏幕尺寸监听功能
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'

// 默认断点配置
const DEFAULT_BREAKPOINTS = {
  xs: 0, // 超小屏幕 <576px
  sm: 576, // 小屏幕 ≥576px
  md: 768, // 中等屏幕 ≥768px
  lg: 992, // 大屏幕 ≥992px
  xl: 1200, // 超大屏幕 ≥1200px
  xxl: 1600, // 超超大屏幕 ≥1600px
}

// 全局状态（单例模式）
let globalScreenWidth = ref(0)
let globalScreenHeight = ref(0)
let globalListeners = new Set()
let isInitialized = false

/**
 * 初始化全局屏幕尺寸监听
 */
function initializeGlobalListener() {
  if (isInitialized) return

  function updateGlobalScreenSize() {
    globalScreenWidth.value = window.innerWidth
    globalScreenHeight.value = window.innerHeight

    // 通知所有监听器
    globalListeners.forEach((callback) => callback())
  }

  function handleGlobalResize() {
    updateGlobalScreenSize()
  }

  // 初始化尺寸
  updateGlobalScreenSize()

  // 监听窗口大小变化
  window.addEventListener('resize', handleGlobalResize)

  isInitialized = true
}

/**
 * 响应式断点检测
 * @param {Object} customBreakpoints - 自定义断点配置
 * @param {number} debounce - 防抖延迟（毫秒）
 * @returns {Object} 响应式断点信息
 */
export function useResponsive(customBreakpoints = {}, debounce = 100) {
  // 合并断点配置
  const breakpoints = { ...DEFAULT_BREAKPOINTS, ...customBreakpoints }

  // 初始化全局监听器
  if (typeof window !== 'undefined') {
    initializeGlobalListener()
  }

  // 本地响应式数据
  const screenWidth = ref(globalScreenWidth.value)
  const screenHeight = ref(globalScreenHeight.value)
  const resizeTimer = ref(null)

  // 计算当前断点
  const currentBreakpoint = computed(() => {
    const width = screenWidth.value

    if (width >= breakpoints.xxl) return 'xxl'
    if (width >= breakpoints.xl) return 'xl'
    if (width >= breakpoints.lg) return 'lg'
    if (width >= breakpoints.md) return 'md'
    if (width >= breakpoints.sm) return 'sm'
    return 'xs'
  })

  // 设备类型判断
  const isMobile = computed(() => {
    return ['xs', 'sm'].includes(currentBreakpoint.value)
  })

  const isTablet = computed(() => {
    return currentBreakpoint.value === 'md'
  })

  const isDesktop = computed(() => {
    return ['lg', 'xl', 'xxl'].includes(currentBreakpoint.value)
  })

  // 具体断点判断
  const isXs = computed(() => currentBreakpoint.value === 'xs')
  const isSm = computed(() => currentBreakpoint.value === 'sm')
  const isMd = computed(() => currentBreakpoint.value === 'md')
  const isLg = computed(() => currentBreakpoint.value === 'lg')
  const isXl = computed(() => currentBreakpoint.value === 'xl')
  const isXxl = computed(() => currentBreakpoint.value === 'xxl')

  // 断点范围判断
  const isSmAndUp = computed(() => screenWidth.value >= breakpoints.sm)
  const isMdAndUp = computed(() => screenWidth.value >= breakpoints.md)
  const isLgAndUp = computed(() => screenWidth.value >= breakpoints.lg)
  const isXlAndUp = computed(() => screenWidth.value >= breakpoints.xl)
  const isXxlAndUp = computed(() => screenWidth.value >= breakpoints.xxl)

  const isSmAndDown = computed(() => screenWidth.value < breakpoints.md)
  const isMdAndDown = computed(() => screenWidth.value < breakpoints.lg)
  const isLgAndDown = computed(() => screenWidth.value < breakpoints.xl)
  const isXlAndDown = computed(() => screenWidth.value < breakpoints.xxl)

  // 屏幕方向
  const isLandscape = computed(() => screenWidth.value > screenHeight.value)
  const isPortrait = computed(() => screenWidth.value <= screenHeight.value)

  // 屏幕密度
  const pixelRatio = ref(1)
  const isHighDensity = computed(() => pixelRatio.value > 1.5)

  // 更新本地尺寸的防抖函数
  function updateLocalScreenSize() {
    if (resizeTimer.value) {
      clearTimeout(resizeTimer.value)
    }

    resizeTimer.value = setTimeout(() => {
      screenWidth.value = globalScreenWidth.value
      screenHeight.value = globalScreenHeight.value

      // 更新像素密度
      if (typeof window !== 'undefined') {
        pixelRatio.value = window.devicePixelRatio || 1
      }
    }, debounce)
  }

  // 注册到全局监听器
  onMounted(() => {
    if (typeof window !== 'undefined') {
      // 初始化数据
      screenWidth.value = globalScreenWidth.value
      screenHeight.value = globalScreenHeight.value
      pixelRatio.value = window.devicePixelRatio || 1

      // 注册监听器
      globalListeners.add(updateLocalScreenSize)
    }
  })

  onUnmounted(() => {
    // 清理定时器
    if (resizeTimer.value) {
      clearTimeout(resizeTimer.value)
    }

    // 移除监听器
    globalListeners.delete(updateLocalScreenSize)
  })

  return {
    // 屏幕尺寸
    screenWidth: readonly(screenWidth),
    screenHeight: readonly(screenHeight),
    pixelRatio: readonly(pixelRatio),

    // 断点信息
    breakpoints,
    currentBreakpoint: readonly(currentBreakpoint),

    // 设备类型
    isMobile: readonly(isMobile),
    isTablet: readonly(isTablet),
    isDesktop: readonly(isDesktop),

    // 具体断点
    isXs: readonly(isXs),
    isSm: readonly(isSm),
    isMd: readonly(isMd),
    isLg: readonly(isLg),
    isXl: readonly(isXl),
    isXxl: readonly(isXxl),

    // 断点范围
    isSmAndUp: readonly(isSmAndUp),
    isMdAndUp: readonly(isMdAndUp),
    isLgAndUp: readonly(isLgAndUp),
    isXlAndUp: readonly(isXlAndUp),
    isXxlAndUp: readonly(isXxlAndUp),

    isSmAndDown: readonly(isSmAndDown),
    isMdAndDown: readonly(isMdAndDown),
    isLgAndDown: readonly(isLgAndDown),
    isXlAndDown: readonly(isXlAndDown),

    // 屏幕方向
    isLandscape: readonly(isLandscape),
    isPortrait: readonly(isPortrait),

    // 屏幕密度
    isHighDensity: readonly(isHighDensity),
  }
}

/**
 * 响应式值选择器
 * 根据当前断点返回对应的值
 * @param {Object} values - 断点值映射
 * @param {*} defaultValue - 默认值
 * @returns {ComputedRef} 响应式值
 */
export function useResponsiveValue(values, defaultValue = null) {
  const { currentBreakpoint } = useResponsive()

  return computed(() => {
    const breakpoint = currentBreakpoint.value

    // 按优先级查找值
    const priorities = ['xxl', 'xl', 'lg', 'md', 'sm', 'xs']
    const currentIndex = priorities.indexOf(breakpoint)

    // 从当前断点开始向下查找
    for (let i = currentIndex; i < priorities.length; i++) {
      const key = priorities[i]
      if (values[key] !== undefined) {
        return values[key]
      }
    }

    return defaultValue
  })
}

/**
 * 媒体查询匹配器
 * @param {string} query - 媒体查询字符串
 * @returns {Object} 匹配结果
 */
export function useMediaQuery(query) {
  const matches = ref(false)
  let mediaQuery = null

  function updateMatches() {
    if (mediaQuery) {
      matches.value = mediaQuery.matches
    }
  }

  onMounted(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      mediaQuery = window.matchMedia(query)
      matches.value = mediaQuery.matches

      // 监听变化
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', updateMatches)
      } else {
        // 兼容旧版本
        mediaQuery.addListener(updateMatches)
      }
    }
  })

  onUnmounted(() => {
    if (mediaQuery) {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', updateMatches)
      } else {
        // 兼容旧版本
        mediaQuery.removeListener(updateMatches)
      }
    }
  })

  return {
    matches: readonly(matches),
  }
}

/**
 * 容器查询（实验性功能）
 * @param {Ref} containerRef - 容器引用
 * @param {Object} breakpoints - 容器断点配置
 * @returns {Object} 容器查询结果
 */
export function useContainerQuery(containerRef, breakpoints = {}) {
  const containerWidth = ref(0)
  const containerHeight = ref(0)
  const resizeObserver = ref(null)

  const currentBreakpoint = computed(() => {
    const width = containerWidth.value

    const sortedBreakpoints = Object.entries(breakpoints).sort(([, a], [, b]) => b - a)

    for (const [name, minWidth] of sortedBreakpoints) {
      if (width >= minWidth) {
        return name
      }
    }

    return 'xs'
  })

  onMounted(() => {
    if (containerRef.value && typeof ResizeObserver !== 'undefined') {
      resizeObserver.value = new ResizeObserver((entries) => {
        for (const entry of entries) {
          containerWidth.value = entry.contentRect.width
          containerHeight.value = entry.contentRect.height
        }
      })

      resizeObserver.value.observe(containerRef.value)
    }
  })

  onUnmounted(() => {
    if (resizeObserver.value) {
      resizeObserver.value.disconnect()
    }
  })

  return {
    containerWidth: readonly(containerWidth),
    containerHeight: readonly(containerHeight),
    currentBreakpoint: readonly(currentBreakpoint),
  }
}

// 工具函数
export const breakpointUtils = {
  /**
   * 格式化尺寸值
   * @param {number|string} size - 尺寸值
   * @returns {string} 格式化后的CSS值
   */
  formatSize(size) {
    if (typeof size === 'number') {
      return `${size}px`
    }
    return size
  },

  /**
   * 获取断点范围
   * @param {string} breakpoint - 断点名称
   * @param {Object} breakpoints - 断点配置
   * @returns {Object} 断点范围信息
   */
  getBreakpointRange(breakpoint, breakpoints = DEFAULT_BREAKPOINTS) {
    const keys = Object.keys(breakpoints).sort((a, b) => breakpoints[a] - breakpoints[b])
    const index = keys.indexOf(breakpoint)

    return {
      min: breakpoints[breakpoint],
      max: index < keys.length - 1 ? breakpoints[keys[index + 1]] - 1 : Infinity,
      name: breakpoint,
    }
  },

  /**
   * 生成媒体查询字符串
   * @param {string} breakpoint - 断点名称
   * @param {Object} breakpoints - 断点配置
   * @param {string} type - 查询类型 ('min' | 'max' | 'only')
   * @returns {string} 媒体查询字符串
   */
  generateMediaQuery(breakpoint, breakpoints = DEFAULT_BREAKPOINTS, type = 'min') {
    const range = this.getBreakpointRange(breakpoint, breakpoints)

    switch (type) {
      case 'min':
        return `(min-width: ${range.min}px)`
      case 'max':
        return `(max-width: ${range.max}px)`
      case 'only':
        return range.max === Infinity
          ? `(min-width: ${range.min}px)`
          : `(min-width: ${range.min}px) and (max-width: ${range.max}px)`
      default:
        return `(min-width: ${range.min}px)`
    }
  },
}
