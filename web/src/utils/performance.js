/**
 * 前端性能监控工具
 * 提供性能指标收集、分析和优化建议
 */

/**
 * 性能监控类
 */
export class PerformanceMonitor {
  constructor() {
    this.metrics = new Map()
    this.observers = new Map()
    this.isSupported = this.checkSupport()
    this.init()
  }

  /**
   * 检查浏览器支持
   */
  checkSupport() {
    return !!(
      window.performance &&
      window.performance.mark &&
      window.performance.measure &&
      window.PerformanceObserver
    )
  }

  /**
   * 初始化监控
   */
  init() {
    if (!this.isSupported) {
      console.warn('Performance monitoring is not supported in this browser')
      return
    }

    this.observeNavigationTiming()
    this.observeResourceTiming()
    this.observeLargestContentfulPaint()
    this.observeFirstInputDelay()
    this.observeCumulativeLayoutShift()
    this.observeLongTasks()
  }

  /**
   * 观察导航时间
   */
  observeNavigationTiming() {
    if (window.performance.getEntriesByType) {
      const navigationEntries = window.performance.getEntriesByType('navigation')
      if (navigationEntries.length > 0) {
        const entry = navigationEntries[0]
        this.recordMetric('navigation', {
          dns: entry.domainLookupEnd - entry.domainLookupStart,
          tcp: entry.connectEnd - entry.connectStart,
          ssl: entry.secureConnectionStart > 0 ? entry.connectEnd - entry.secureConnectionStart : 0,
          ttfb: entry.responseStart - entry.requestStart,
          download: entry.responseEnd - entry.responseStart,
          domParse: entry.domContentLoadedEventStart - entry.responseEnd,
          domReady: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
          loadComplete: entry.loadEventEnd - entry.loadEventStart,
          total: entry.loadEventEnd - entry.navigationStart,
        })
      }
    }
  }

  /**
   * 观察资源加载时间
   */
  observeResourceTiming() {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'resource') {
          this.recordResourceMetric(entry)
        }
      })
    })

    observer.observe({ entryTypes: ['resource'] })
    this.observers.set('resource', observer)
  }

  /**
   * 观察最大内容绘制 (LCP)
   */
  observeLargestContentfulPaint() {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      const lastEntry = entries[entries.length - 1]

      this.recordMetric('lcp', {
        value: lastEntry.startTime,
        element: lastEntry.element?.tagName || 'unknown',
        url: lastEntry.url || '',
        timestamp: Date.now(),
      })
    })

    observer.observe({ entryTypes: ['largest-contentful-paint'] })
    this.observers.set('lcp', observer)
  }

  /**
   * 观察首次输入延迟 (FID)
   */
  observeFirstInputDelay() {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        this.recordMetric('fid', {
          value: entry.processingStart - entry.startTime,
          eventType: entry.name,
          timestamp: Date.now(),
        })
      })
    })

    observer.observe({ entryTypes: ['first-input'] })
    this.observers.set('fid', observer)
  }

  /**
   * 观察累积布局偏移 (CLS)
   */
  observeCumulativeLayoutShift() {
    let clsValue = 0
    let clsEntries = []

    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (!entry.hadRecentInput) {
          clsValue += entry.value
          clsEntries.push(entry)
        }
      })

      this.recordMetric('cls', {
        value: clsValue,
        entries: clsEntries.length,
        timestamp: Date.now(),
      })
    })

    observer.observe({ entryTypes: ['layout-shift'] })
    this.observers.set('cls', observer)
  }

  /**
   * 观察长任务
   */
  observeLongTasks() {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        this.recordMetric('longtask', {
          duration: entry.duration,
          startTime: entry.startTime,
          attribution: entry.attribution || [],
          timestamp: Date.now(),
        })
      })
    })

    observer.observe({ entryTypes: ['longtask'] })
    this.observers.set('longtask', observer)
  }

  /**
   * 记录资源指标
   */
  recordResourceMetric(entry) {
    const resourceType = this.getResourceType(entry.name)
    const size = entry.transferSize || entry.encodedBodySize || 0
    const duration = entry.responseEnd - entry.startTime

    if (!this.metrics.has('resources')) {
      this.metrics.set('resources', {
        total: 0,
        byType: {},
        slowest: [],
        largest: [],
      })
    }

    const resources = this.metrics.get('resources')
    resources.total++

    if (!resources.byType[resourceType]) {
      resources.byType[resourceType] = {
        count: 0,
        totalSize: 0,
        totalDuration: 0,
        avgSize: 0,
        avgDuration: 0,
      }
    }

    const typeStats = resources.byType[resourceType]
    typeStats.count++
    typeStats.totalSize += size
    typeStats.totalDuration += duration
    typeStats.avgSize = typeStats.totalSize / typeStats.count
    typeStats.avgDuration = typeStats.totalDuration / typeStats.count

    // 记录最慢的资源
    resources.slowest.push({ name: entry.name, duration, type: resourceType })
    resources.slowest.sort((a, b) => b.duration - a.duration)
    resources.slowest = resources.slowest.slice(0, 10)

    // 记录最大的资源
    if (size > 0) {
      resources.largest.push({ name: entry.name, size, type: resourceType })
      resources.largest.sort((a, b) => b.size - a.size)
      resources.largest = resources.largest.slice(0, 10)
    }
  }

  /**
   * 获取资源类型
   */
  getResourceType(url) {
    if (url.includes('.js')) return 'script'
    if (url.includes('.css')) return 'stylesheet'
    if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)$/i)) return 'image'
    if (url.match(/\.(woff|woff2|ttf|eot)$/i)) return 'font'
    if (url.includes('api/') || url.includes('/api')) return 'xhr'
    return 'other'
  }

  /**
   * 记录自定义指标
   */
  recordMetric(name, data) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, [])
    }

    const metrics = this.metrics.get(name)
    if (Array.isArray(metrics)) {
      metrics.push({
        ...data,
        timestamp: data.timestamp || Date.now(),
      })
    } else {
      this.metrics.set(name, data)
    }
  }

  /**
   * 开始性能标记
   */
  mark(name) {
    if (this.isSupported) {
      performance.mark(`${name}-start`)
    }
  }

  /**
   * 结束性能标记并测量
   */
  measure(name) {
    if (this.isSupported) {
      performance.mark(`${name}-end`)
      performance.measure(name, `${name}-start`, `${name}-end`)

      const measures = performance.getEntriesByName(name, 'measure')
      if (measures.length > 0) {
        const measure = measures[measures.length - 1]
        this.recordMetric('custom', {
          name,
          duration: measure.duration,
          timestamp: Date.now(),
        })
      }
    }
  }

  /**
   * 获取所有指标
   */
  getMetrics() {
    return Object.fromEntries(this.metrics)
  }

  /**
   * 获取性能报告
   */
  getPerformanceReport() {
    const metrics = this.getMetrics()
    const report = {
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      connection: this.getConnectionInfo(),
      vitals: this.getWebVitals(metrics),
      resources: metrics.resources || {},
      custom: metrics.custom || [],
      recommendations: this.getRecommendations(metrics),
    }

    return report
  }

  /**
   * 获取连接信息
   */
  getConnectionInfo() {
    if (navigator.connection) {
      return {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt,
        saveData: navigator.connection.saveData,
      }
    }
    return null
  }

  /**
   * 获取Web Vitals指标
   */
  getWebVitals(metrics) {
    const vitals = {}

    // LCP (Largest Contentful Paint)
    if (metrics.lcp) {
      vitals.lcp = {
        value: metrics.lcp.value,
        rating: this.rateLCP(metrics.lcp.value),
        element: metrics.lcp.element,
      }
    }

    // FID (First Input Delay)
    if (metrics.fid) {
      vitals.fid = {
        value: metrics.fid.value,
        rating: this.rateFID(metrics.fid.value),
        eventType: metrics.fid.eventType,
      }
    }

    // CLS (Cumulative Layout Shift)
    if (metrics.cls) {
      vitals.cls = {
        value: metrics.cls.value,
        rating: this.rateCLS(metrics.cls.value),
        entries: metrics.cls.entries,
      }
    }

    // TTFB (Time to First Byte)
    if (metrics.navigation) {
      vitals.ttfb = {
        value: metrics.navigation.ttfb,
        rating: this.rateTTFB(metrics.navigation.ttfb),
      }
    }

    return vitals
  }

  /**
   * LCP评级
   */
  rateLCP(value) {
    if (value <= 2500) return 'good'
    if (value <= 4000) return 'needs-improvement'
    return 'poor'
  }

  /**
   * FID评级
   */
  rateFID(value) {
    if (value <= 100) return 'good'
    if (value <= 300) return 'needs-improvement'
    return 'poor'
  }

  /**
   * CLS评级
   */
  rateCLS(value) {
    if (value <= 0.1) return 'good'
    if (value <= 0.25) return 'needs-improvement'
    return 'poor'
  }

  /**
   * TTFB评级
   */
  rateTTFB(value) {
    if (value <= 800) return 'good'
    if (value <= 1800) return 'needs-improvement'
    return 'poor'
  }

  /**
   * 获取优化建议
   */
  getRecommendations(metrics) {
    const recommendations = []

    // LCP优化建议
    if (metrics.lcp && metrics.lcp.value > 2500) {
      recommendations.push({
        type: 'lcp',
        priority: 'high',
        message: 'LCP时间过长，建议优化关键资源加载',
        suggestions: [
          '优化服务器响应时间',
          '使用CDN加速资源加载',
          '压缩和优化图片',
          '预加载关键资源',
          '移除阻塞渲染的资源',
        ],
      })
    }

    // FID优化建议
    if (metrics.fid && metrics.fid.value > 100) {
      recommendations.push({
        type: 'fid',
        priority: 'high',
        message: 'FID时间过长，建议优化JavaScript执行',
        suggestions: [
          '减少JavaScript执行时间',
          '代码分割和懒加载',
          '使用Web Workers处理复杂计算',
          '优化第三方脚本',
          '减少主线程工作',
        ],
      })
    }

    // CLS优化建议
    if (metrics.cls && metrics.cls.value > 0.1) {
      recommendations.push({
        type: 'cls',
        priority: 'medium',
        message: 'CLS值过高，建议减少布局偏移',
        suggestions: [
          '为图片和视频设置尺寸属性',
          '避免在现有内容上方插入内容',
          '使用transform动画替代改变布局的动画',
          '预留广告和嵌入内容的空间',
        ],
      })
    }

    // 长任务优化建议
    if (metrics.longtask && metrics.longtask.length > 0) {
      recommendations.push({
        type: 'longtask',
        priority: 'medium',
        message: '检测到长任务，建议优化JavaScript性能',
        suggestions: [
          '将长任务分解为小任务',
          '使用requestIdleCallback',
          '优化算法复杂度',
          '使用Web Workers',
        ],
      })
    }

    // 资源优化建议
    if (metrics.resources) {
      const { largest, slowest } = metrics.resources

      if (largest && largest.length > 0) {
        const largeResources = largest.filter((r) => r.size > 1024 * 1024) // > 1MB
        if (largeResources.length > 0) {
          recommendations.push({
            type: 'resource-size',
            priority: 'medium',
            message: '发现大型资源，建议优化',
            suggestions: [
              '压缩图片和视频',
              '使用现代图片格式(WebP, AVIF)',
              '实现懒加载',
              '使用适当的图片尺寸',
            ],
            resources: largeResources,
          })
        }
      }

      if (slowest && slowest.length > 0) {
        const slowResources = slowest.filter((r) => r.duration > 1000) // > 1s
        if (slowResources.length > 0) {
          recommendations.push({
            type: 'resource-speed',
            priority: 'high',
            message: '发现加载缓慢的资源，建议优化',
            suggestions: ['使用CDN加速', '启用HTTP/2', '优化服务器配置', '减少重定向'],
            resources: slowResources,
          })
        }
      }
    }

    return recommendations
  }

  /**
   * 清理观察器
   */
  disconnect() {
    this.observers.forEach((observer) => {
      observer.disconnect()
    })
    this.observers.clear()
  }
}

/**
 * 性能工具函数
 */
export const performanceUtils = {
  /**
   * 测量函数执行时间
   */
  measureFunction: (fn, name = 'function') => {
    return async (...args) => {
      const start = performance.now()
      const result = await fn(...args)
      const end = performance.now()

      console.log(`${name} execution time: ${(end - start).toFixed(2)}ms`)
      return result
    }
  },

  /**
   * 防抖函数
   */
  debounce: (func, wait, immediate = false) => {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        timeout = null
        if (!immediate) func(...args)
      }
      const callNow = immediate && !timeout
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
      if (callNow) func(...args)
    }
  },

  /**
   * 节流函数
   */
  throttle: (func, limit) => {
    let inThrottle
    return function executedFunction(...args) {
      if (!inThrottle) {
        func.apply(this, args)
        inThrottle = true
        setTimeout(() => (inThrottle = false), limit)
      }
    }
  },

  /**
   * 空闲时执行
   */
  runWhenIdle: (callback, options = {}) => {
    if (window.requestIdleCallback) {
      return window.requestIdleCallback(callback, options)
    } else {
      return setTimeout(callback, 1)
    }
  },

  /**
   * 预加载资源
   */
  preloadResource: (url, as = 'fetch') => {
    const link = document.createElement('link')
    link.rel = 'preload'
    link.href = url
    link.as = as
    document.head.appendChild(link)
    return link
  },

  /**
   * 预连接域名
   */
  preconnect: (url) => {
    const link = document.createElement('link')
    link.rel = 'preconnect'
    link.href = url
    document.head.appendChild(link)
    return link
  },

  /**
   * 获取内存使用情况
   */
  getMemoryUsage: () => {
    if (performance.memory) {
      return {
        used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
        total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
        limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024),
      }
    }
    return null
  },

  /**
   * 检查是否为慢速连接
   */
  isSlowConnection: () => {
    if (navigator.connection) {
      return (
        navigator.connection.effectiveType === 'slow-2g' ||
        navigator.connection.effectiveType === '2g' ||
        navigator.connection.saveData
      )
    }
    return false
  },
}

// 全局性能监控实例
export const performanceMonitor = new PerformanceMonitor()

// 页面卸载时生成报告
window.addEventListener('beforeunload', () => {
  const report = performanceMonitor.getPerformanceReport()

  // 发送性能数据到服务器（如果需要）
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/performance', JSON.stringify(report))
  }

  // 清理资源
  performanceMonitor.disconnect()
})

export default {
  PerformanceMonitor,
  performanceMonitor,
  performanceUtils,
}
