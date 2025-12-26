/**
 * 布局组件统一导出
 * 提供响应式布局和容器组件
 */

// 响应式布局组件
export { default as ResponsiveGrid } from './ResponsiveGrid.vue'
export { default as ResponsiveGridItem } from './ResponsiveGridItem.vue'
export { default as ResponsiveContainer } from './ResponsiveContainer.vue'
export { default as BreakpointProvider } from './BreakpointProvider.vue'

// 异步导出 - 用于懒加载
export default {
  ResponsiveGrid: () => import('./ResponsiveGrid.vue'),
  ResponsiveGridItem: () => import('./ResponsiveGridItem.vue'),
  ResponsiveContainer: () => import('./ResponsiveContainer.vue'),
  BreakpointProvider: () => import('./BreakpointProvider.vue')
}

// 组件类型定义（用于TypeScript支持）
export interface LayoutComponentsMap {
  ResponsiveGrid: typeof import('./ResponsiveGrid.vue').default
  ResponsiveGridItem: typeof import('./ResponsiveGridItem.vue').default
  ResponsiveContainer: typeof import('./ResponsiveContainer.vue').default
  BreakpointProvider: typeof import('./BreakpointProvider.vue').default
}

// 组件安装函数（用于全局注册）
export function installLayoutComponents(app) {
  const components = {
    ResponsiveGrid: () => import('./ResponsiveGrid.vue'),
    ResponsiveGridItem: () => import('./ResponsiveGridItem.vue'),
    ResponsiveContainer: () => import('./ResponsiveContainer.vue'),
    BreakpointProvider: () => import('./BreakpointProvider.vue')
  }
  
  Object.entries(components).forEach(([name, component]) => {
    app.component(name, component)
  })
}

// 布局配置常量
export const LAYOUT_CONFIG = {
  // 默认断点配置
  breakpoints: {
    xs: 0,      // 超小屏幕 <576px
    sm: 576,    // 小屏幕 ≥576px
    md: 768,    // 中等屏幕 ≥768px
    lg: 992,    // 大屏幕 ≥992px
    xl: 1200,   // 超大屏幕 ≥1200px
    xxl: 1600   // 超超大屏幕 ≥1600px
  },
  
  // 容器最大宽度
  containerMaxWidths: {
    sm: '576px',
    md: '768px',
    lg: '992px',
    xl: '1200px',
    xxl: '1600px'
  },
  
  // 默认间距
  spacing: {
    xs: 8,
    sm: 12,
    md: 16,
    lg: 20,
    xl: 24,
    xxl: 32
  },
  
  // 默认内边距
  padding: {
    xs: 16,
    sm: 20,
    md: 24,
    lg: 32,
    xl: 40,
    xxl: 48
  }
}

// 布局工具函数
export const layoutUtils = {
  /**
   * 获取响应式值
   * @param {Object} values - 断点值映射
   * @param {string} currentBreakpoint - 当前断点
   * @param {*} defaultValue - 默认值
   * @returns {*} 对应断点的值
   */
  getResponsiveValue(values, currentBreakpoint, defaultValue = null) {
    if (typeof values !== 'object') return values
    
    const priorities = ['xxl', 'xl', 'lg', 'md', 'sm', 'xs']
    const currentIndex = priorities.indexOf(currentBreakpoint)
    
    // 从当前断点开始向下查找
    for (let i = currentIndex; i < priorities.length; i++) {
      const key = priorities[i]
      if (values[key] !== undefined) {
        return values[key]
      }
    }
    
    return defaultValue
  },
  
  /**
   * 格式化尺寸值
   * @param {number|string} size - 尺寸值
   * @returns {string} CSS尺寸值
   */
  formatSize(size) {
    if (typeof size === 'number') {
      return `${size}px`
    }
    return size
  },
  
  /**
   * 生成栅格列样式
   * @param {number|Object} cols - 列数配置
   * @returns {Object} CSS样式对象
   */
  generateGridColumns(cols) {
    if (typeof cols === 'number') {
      return { gridTemplateColumns: `repeat(${cols}, 1fr)` }
    }
    
    const styles = {}
    Object.entries(cols).forEach(([breakpoint, colCount]) => {
      styles[`--grid-cols-${breakpoint}`] = colCount
    })
    
    return styles
  },
  
  /**
   * 生成间距样式
   * @param {number|string|Object} gap - 间距配置
   * @returns {Object} CSS样式对象
   */
  generateGapStyles(gap) {
    if (typeof gap === 'object') {
      const styles = {}
      Object.entries(gap).forEach(([breakpoint, gapValue]) => {
        styles[`--gap-${breakpoint}`] = this.formatSize(gapValue)
      })
      return styles
    }
    
    return { gap: this.formatSize(gap) }
  }
}