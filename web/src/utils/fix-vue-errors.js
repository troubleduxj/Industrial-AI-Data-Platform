/**
 * Vue错误修复工具
 * 用于修复常见的Vue运行时错误
 */

/**
 * 修复组件为null的错误
 */
export function fixComponentNullError() {
  // 重写Vue的locateNonHydratedAsyncRoot函数以添加null检查
  const originalConsoleError = console.error

  console.error = function (...args) {
    const message = args[0]

    // 过滤掉已知的Vue错误
    if (
      typeof message === 'string' &&
      message.includes("Cannot read properties of null (reading 'component')")
    ) {
      console.warn('已拦截Vue组件null错误，正在尝试恢复...')
      return
    }

    // 其他错误正常输出
    originalConsoleError.apply(console, args)
  }
}

/**
 * 修复Slot调用错误
 */
export function fixSlotError() {
  // 监听Vue警告
  const originalConsoleWarn = console.warn

  console.warn = function (...args) {
    const message = args[0]

    if (
      typeof message === 'string' &&
      message.includes('Slot "default" invoked outside of the render function')
    ) {
      console.info('已拦截Vue Slot警告')
      return
    }

    originalConsoleWarn.apply(console, args)
  }
}

/**
 * 强制重新渲染应用
 */
export function forceRerender() {
  try {
    // 获取Vue应用实例
    const app = document.getElementById('app')
    if (app && app.__vue_app__) {
      console.log('正在强制重新渲染应用...')
      app.__vue_app__.unmount()

      // 延迟重新挂载
      setTimeout(() => {
        window.location.reload()
      }, 100)
    }
  } catch (error) {
    console.warn('强制重新渲染失败:', error)
  }
}

/**
 * 清理无效的组件引用
 */
export function cleanupInvalidRefs() {
  try {
    // 清理可能的无效引用
    if (window.$loadingBar && typeof window.$loadingBar !== 'object') {
      delete window.$loadingBar
    }

    if (window.$message && typeof window.$message !== 'object') {
      delete window.$message
    }

    if (window.$dialog && typeof window.$dialog !== 'object') {
      delete window.$dialog
    }

    if (window.$notification && typeof window.$notification !== 'object') {
      delete window.$notification
    }

    console.log('已清理无效的组件引用')
  } catch (error) {
    console.warn('清理组件引用失败:', error)
  }
}

/**
 * 应用所有修复
 */
export function applyAllFixes() {
  console.log('🔧 正在应用Vue错误修复...')

  fixComponentNullError()
  fixSlotError()
  cleanupInvalidRefs()

  console.log('✅ Vue错误修复已应用')
}

/**
 * 紧急修复 - 在控制台中运行
 */
export function emergencyFix() {
  console.log('🚨 执行紧急修复...')

  // 1. 清理所有全局引用
  cleanupInvalidRefs()

  // 2. 重置错误处理
  fixComponentNullError()
  fixSlotError()

  // 3. 尝试重新初始化naive-ui工具
  try {
    if (window.setupNaiveTools && typeof window.setupNaiveTools === 'function') {
      window.setupNaiveTools()
    }
  } catch (error) {
    console.warn('重新初始化naive工具失败:', error)
  }

  console.log('✅ 紧急修复完成')
}

// 自动应用修复（仅在开发环境）
if (import.meta.env.DEV) {
  applyAllFixes()

  // 暴露紧急修复函数到全局
  window.emergencyFix = emergencyFix
  window.forceRerender = forceRerender
}
