/**
 * Dropdown位置修复工具
 * 动态监听页面变化，确保dropdown菜单不会超出视口
 */

class DropdownPositionFixer {
  constructor() {
    this.observers = new Set()
    this.isInitialized = false
  }

  /**
   * 初始化dropdown位置修复
   */
  init() {
    if (this.isInitialized) return

    this.setupGlobalObserver()
    this.setupResizeListener()
    this.setupMutationObserver()
    this.isInitialized = true

    console.log('🔧 Dropdown位置修复器已初始化')
  }

  /**
   * 设置全局观察器
   */
  setupGlobalObserver() {
    // 监听所有dropdown菜单的显示
    document.addEventListener('click', (e) => {
      // 延迟执行，确保dropdown已经渲染
      setTimeout(() => {
        this.fixAllDropdowns()
      }, 50)
    })

    // 监听窗口滚动
    window.addEventListener(
      'scroll',
      () => {
        this.fixAllDropdowns()
      },
      { passive: true }
    )
  }

  /**
   * 设置窗口大小变化监听
   */
  setupResizeListener() {
    let resizeTimer = null
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(() => {
        this.fixAllDropdowns()
      }, 100)
    })
  }

  /**
   * 设置DOM变化监听
   */
  setupMutationObserver() {
    const observer = new MutationObserver((mutations) => {
      let shouldFix = false

      mutations.forEach((mutation) => {
        // 检查是否有新的dropdown菜单添加
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1) {
              // Element node
              if (
                node.classList?.contains('n-dropdown-menu') ||
                node.querySelector?.('.n-dropdown-menu')
              ) {
                shouldFix = true
              }
            }
          })
        }

        // 检查class变化（可能是菜单展开/收起）
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          const target = mutation.target
          if (
            target.classList?.contains('n-layout-sider') ||
            target.classList?.contains('layout-header') ||
            target.closest?.('.layout-header')
          ) {
            shouldFix = true
          }
        }
      })

      if (shouldFix) {
        setTimeout(() => {
          this.fixAllDropdowns()
        }, 50)
      }
    })

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'style'],
    })

    this.observers.add(observer)
  }

  /**
   * 修复所有可见的dropdown菜单
   */
  fixAllDropdowns() {
    const dropdowns = document.querySelectorAll('.n-dropdown-menu')

    dropdowns.forEach((dropdown) => {
      if (this.isVisible(dropdown)) {
        this.fixDropdownPosition(dropdown)
      }
    })
  }

  /**
   * 检查元素是否可见
   */
  isVisible(element) {
    const style = window.getComputedStyle(element)
    return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0'
  }

  /**
   * 修复单个dropdown的位置
   */
  fixDropdownPosition(dropdown) {
    const rect = dropdown.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    let needsAdjustment = false
    let newStyle = {}

    // 检查右边界
    if (rect.right > viewportWidth - 10) {
      const overflow = rect.right - viewportWidth + 20
      newStyle.transform = `translateX(-${overflow}px)`
      needsAdjustment = true
    }

    // 检查左边界
    if (rect.left < 10) {
      const underflow = 10 - rect.left
      newStyle.transform = `translateX(${underflow}px)`
      needsAdjustment = true
    }

    // 检查底部边界
    if (rect.bottom > viewportHeight - 10) {
      newStyle.maxHeight = `${viewportHeight - rect.top - 20}px`
      newStyle.overflowY = 'auto'
      needsAdjustment = true
    }

    // 应用调整
    if (needsAdjustment) {
      Object.assign(dropdown.style, newStyle)

      // 添加调试信息
      if (process.env.NODE_ENV === 'development') {
        console.log('🔧 调整dropdown位置:', {
          element: dropdown,
          originalRect: rect,
          adjustments: newStyle,
          viewport: { width: viewportWidth, height: viewportHeight },
        })
      }
    }
  }

  /**
   * 销毁观察器
   */
  destroy() {
    this.observers.forEach((observer) => observer.disconnect())
    this.observers.clear()
    this.isInitialized = false
  }
}

// 创建全局实例
const dropdownFixer = new DropdownPositionFixer()

// 自动初始化
if (typeof window !== 'undefined') {
  // 确保DOM加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      dropdownFixer.init()
    })
  } else {
    dropdownFixer.init()
  }
}

export default dropdownFixer
