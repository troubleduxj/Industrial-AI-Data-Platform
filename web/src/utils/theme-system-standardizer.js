/**
 * 系统管理页面主题标准化工具
 * 用于统一应用主题变量和样式规范
 */

import { DESIGN_TOKENS, CSS_VARIABLE_MAPPING } from '@/config/theme-config.js'

/**
 * 系统管理页面主题标准化器
 */
export class SystemThemeStandardizer {
  constructor() {
    this.appliedPages = new Set()
    this.standardClasses = [
      'system-management-page',
      'standard-page',
      'standard-table',
      'standard-form',
      'standard-button',
      'standard-modal',
    ]
  }

  /**
   * 应用标准化主题到系统管理页面
   * @param {string} pageSelector - 页面选择器
   * @returns {Promise<boolean>} 是否成功应用
   */
  async applyStandardTheme(pageSelector = '.system-management-page') {
    try {
      const pages = document.querySelectorAll(pageSelector)

      for (const page of pages) {
        await this.standardizePage(page)
      }

      return true
    } catch (error) {
      console.error('应用标准化主题失败:', error)
      return false
    }
  }

  /**
   * 标准化单个页面
   * @param {Element} pageElement - 页面元素
   */
  async standardizePage(pageElement) {
    if (!pageElement) return

    // 添加标准化类名
    this.addStandardClasses(pageElement)

    // 应用CSS变量
    this.applyCSSVariables(pageElement)

    // 标准化表格组件
    this.standardizeTables(pageElement)

    // 标准化表单组件
    this.standardizeForms(pageElement)

    // 标准化按钮组件
    this.standardizeButtons(pageElement)

    // 标准化模态框组件
    this.standardizeModals(pageElement)

    // 标准化查询栏
    this.standardizeQueryBars(pageElement)

    // 标准化批量操作按钮
    this.standardizeBatchButtons(pageElement)

    // 记录已应用的页面
    const pageId = pageElement.id || pageElement.className
    this.appliedPages.add(pageId)
  }

  /**
   * 添加标准化CSS类名
   * @param {Element} element - 目标元素
   */
  addStandardClasses(element) {
    // 为页面容器添加标准类名
    if (!element.classList.contains('system-management-page')) {
      element.classList.add('system-management-page')
    }
    if (!element.classList.contains('standard-page')) {
      element.classList.add('standard-page')
    }

    // 为表格添加标准类名
    const tables = element.querySelectorAll('table, .n-data-table')
    tables.forEach((table) => {
      if (!table.classList.contains('standard-table')) {
        table.classList.add('standard-table')
      }
    })

    // 为表单添加标准类名
    const forms = element.querySelectorAll('form, .n-form')
    forms.forEach((form) => {
      if (!form.classList.contains('standard-form')) {
        form.classList.add('standard-form')
      }
    })

    // 为按钮添加标准类名
    const buttons = element.querySelectorAll('button, .n-button')
    buttons.forEach((button) => {
      if (!button.classList.contains('standard-button')) {
        button.classList.add('standard-button')
      }
    })

    // 为模态框添加标准类名
    const modals = element.querySelectorAll('.n-modal, .n-drawer')
    modals.forEach((modal) => {
      if (!modal.classList.contains('standard-modal')) {
        modal.classList.add('standard-modal')
      }
    })
  }

  /**
   * 应用CSS变量到元素
   * @param {Element} element - 目标元素
   */
  applyCSSVariables(element) {
    const style = element.style

    // 应用基础颜色变量
    style.setProperty('--text-color-primary', 'var(--text-color-primary)')
    style.setProperty('--text-color-secondary', 'var(--text-color-secondary)')
    style.setProperty('--background-color-base', 'var(--background-color-base)')
    style.setProperty('--background-color-light', 'var(--background-color-light)')
    style.setProperty('--border-color-base', 'var(--border-color-base)')
    style.setProperty('--border-color-light', 'var(--border-color-light)')
    style.setProperty('--primary-color', 'var(--primary-color)')
    style.setProperty('--primary-color-hover', 'var(--primary-color-hover)')

    // 应用间距变量
    style.setProperty('--spacing-xs', 'var(--spacing-xs)')
    style.setProperty('--spacing-sm', 'var(--spacing-sm)')
    style.setProperty('--spacing-md', 'var(--spacing-md)')
    style.setProperty('--spacing-lg', 'var(--spacing-lg)')
    style.setProperty('--spacing-xl', 'var(--spacing-xl)')

    // 应用字体变量
    style.setProperty('--font-size-xs', 'var(--font-size-xs)')
    style.setProperty('--font-size-sm', 'var(--font-size-sm)')
    style.setProperty('--font-size-base', 'var(--font-size-base)')
    style.setProperty('--font-size-lg', 'var(--font-size-lg)')
    style.setProperty('--font-weight-normal', 'var(--font-weight-normal)')
    style.setProperty('--font-weight-medium', 'var(--font-weight-medium)')
    style.setProperty('--font-weight-semibold', 'var(--font-weight-semibold)')
    style.setProperty('--font-weight-bold', 'var(--font-weight-bold)')

    // 应用边框圆角变量
    style.setProperty('--border-radius-sm', 'var(--border-radius-sm)')
    style.setProperty('--border-radius-base', 'var(--border-radius-base)')
    style.setProperty('--border-radius-lg', 'var(--border-radius-lg)')

    // 应用阴影变量
    style.setProperty('--shadow-sm', 'var(--shadow-sm)')
    style.setProperty('--shadow-base', 'var(--shadow-base)')
    style.setProperty('--shadow-md', 'var(--shadow-md)')
    style.setProperty('--shadow-lg', 'var(--shadow-lg)')
  }

  /**
   * 标准化表格组件
   * @param {Element} element - 页面元素
   */
  standardizeTables(element) {
    const tables = element.querySelectorAll('.n-data-table, table')

    tables.forEach((table) => {
      // 应用标准表格样式
      table.style.setProperty('--n-th-color', 'var(--background-color-light)')
      table.style.setProperty('--n-td-color', 'var(--background-color-base)')
      table.style.setProperty('--n-border-color', 'var(--border-color-light)')
      table.style.setProperty('--n-th-text-color', 'var(--text-color-primary)')
      table.style.setProperty('--n-td-text-color', 'var(--text-color-primary)')

      // 标准化表格容器
      const tableContainer = table.closest('.table-content, .n-data-table-wrapper')
      if (tableContainer) {
        tableContainer.style.background = 'var(--background-color-base)'
        tableContainer.style.borderRadius = 'var(--border-radius-lg)'
        tableContainer.style.border = '1px solid var(--border-color-light)'
      }
    })

    // 标准化复选框样式
    const checkboxes = element.querySelectorAll('.n-checkbox')
    checkboxes.forEach((checkbox) => {
      checkbox.style.setProperty('--n-border', '1px solid var(--border-color-base)')
      checkbox.style.setProperty('--n-border-hover', '1px solid var(--primary-color-hover)')
      checkbox.style.setProperty('--n-border-checked', '1px solid var(--primary-color)')
      checkbox.style.setProperty('--n-color-checked', 'var(--primary-color)')
    })
  }

  /**
   * 标准化表单组件
   * @param {Element} element - 页面元素
   */
  standardizeForms(element) {
    const forms = element.querySelectorAll('.n-form, form')

    forms.forEach((form) => {
      // 标准化表单项间距
      const formItems = form.querySelectorAll('.n-form-item')
      formItems.forEach((item) => {
        item.style.marginBottom = 'var(--spacing-md)'
      })

      // 标准化输入框
      const inputs = form.querySelectorAll('.n-input, input')
      inputs.forEach((input) => {
        input.style.setProperty('--n-color', 'var(--background-color-base)')
        input.style.setProperty('--n-border', '1px solid var(--border-color-base)')
        input.style.setProperty('--n-border-hover', '1px solid var(--primary-color-hover)')
        input.style.setProperty('--n-border-focus', '1px solid var(--primary-color)')
        input.style.setProperty('--n-text-color', 'var(--text-color-primary)')
        input.style.borderRadius = 'var(--border-radius-base)'
      })

      // 标准化标签
      const labels = form.querySelectorAll('.n-form-item-label, label')
      labels.forEach((label) => {
        label.style.color = 'var(--text-color-primary)'
        label.style.fontWeight = 'var(--font-weight-medium)'
      })
    })
  }

  /**
   * 标准化按钮组件
   * @param {Element} element - 页面元素
   */
  standardizeButtons(element) {
    const buttons = element.querySelectorAll('.n-button, button')

    buttons.forEach((button) => {
      button.style.borderRadius = 'var(--border-radius-base)'
      button.style.fontWeight = 'var(--font-weight-medium)'
      button.style.transition = 'all var(--transition-fast)'

      // 根据按钮类型应用不同样式
      if (button.classList.contains('n-button--primary-type') || button.type === 'primary') {
        button.style.setProperty('--n-color', 'var(--primary-color)')
        button.style.setProperty('--n-color-hover', 'var(--primary-color-hover)')
        button.style.setProperty('--n-color-pressed', 'var(--primary-color-pressed)')
        button.style.setProperty('--n-text-color', 'var(--primary-foreground)')
      }
    })
  }

  /**
   * 标准化模态框组件
   * @param {Element} element - 页面元素
   */
  standardizeModals(element) {
    const modals = element.querySelectorAll('.n-modal, .n-drawer')

    modals.forEach((modal) => {
      modal.style.setProperty('--n-color', 'var(--background-color-base)')
      modal.style.borderRadius = 'var(--border-radius-lg)'
      modal.style.boxShadow = 'var(--shadow-xl)'
      modal.style.border = '1px solid var(--border-color-light)'

      // 标准化模态框头部
      const header = modal.querySelector('.n-card-header, .n-drawer-header')
      if (header) {
        header.style.background = 'var(--background-color-light)'
        header.style.borderBottom = '1px solid var(--border-color-light)'
        header.style.padding = 'var(--spacing-lg)'
      }

      // 标准化模态框内容
      const content = modal.querySelector('.n-card__content, .n-drawer-body')
      if (content) {
        content.style.padding = 'var(--spacing-lg)'
        content.style.color = 'var(--text-color-primary)'
      }

      // 标准化模态框底部
      const footer = modal.querySelector('.n-card__action, .n-drawer-footer')
      if (footer) {
        footer.style.padding = 'var(--spacing-md) var(--spacing-lg)'
        footer.style.background = 'var(--background-color-light)'
        footer.style.borderTop = '1px solid var(--border-color-light)'
      }
    })
  }

  /**
   * 标准化查询栏组件
   * @param {Element} element - 页面元素
   */
  standardizeQueryBars(element) {
    const queryBars = element.querySelectorAll('.query-bar, .search-bar')

    queryBars.forEach((queryBar) => {
      queryBar.style.background = 'var(--background-color-base)'
      queryBar.style.border = '1px solid var(--border-color-light)'
      queryBar.style.borderRadius = 'var(--border-radius-base)'
      queryBar.style.padding = 'var(--spacing-md)'
      queryBar.style.marginBottom = 'var(--spacing-md)'

      // 标准化查询项
      const queryItems = queryBar.querySelectorAll('.query-bar-item')
      queryItems.forEach((item) => {
        item.style.marginBottom = 'var(--spacing-sm)'

        const label = item.querySelector('.query-bar-label, label')
        if (label) {
          label.style.color = 'var(--text-color-primary)'
          label.style.fontWeight = 'var(--font-weight-medium)'
        }
      })
    })
  }

  /**
   * 标准化批量操作按钮
   * @param {Element} element - 页面元素
   */
  standardizeBatchButtons(element) {
    const batchButtons = element.querySelectorAll('.batch-delete-button, [class*="batch"]')

    batchButtons.forEach((button) => {
      if (
        button.classList.contains('n-button--error-type') ||
        button.textContent.includes('删除')
      ) {
        button.style.setProperty('--n-color', 'var(--error-color)')
        button.style.setProperty('--n-color-hover', '#ff7875')
        button.style.setProperty('--n-color-pressed', '#d9363e')
        button.style.setProperty('--n-text-color', 'white')
      }
    })
  }

  /**
   * 检查页面主题合规性
   * @param {Element} element - 页面元素
   * @returns {Object} 合规性报告
   */
  checkCompliance(element = document.body) {
    const issues = []

    // 检查硬编码颜色
    const allElements = [element, ...element.querySelectorAll('*')]
    allElements.forEach((el) => {
      const style = window.getComputedStyle(el)
      const inlineStyle = el.style

      // 检查常见的硬编码颜色属性
      const colorProps = ['color', 'backgroundColor', 'borderColor']
      colorProps.forEach((prop) => {
        const computedValue = style[prop]
        const inlineValue = inlineStyle[prop]

        if (this.isHardcodedColor(computedValue) || this.isHardcodedColor(inlineValue)) {
          issues.push({
            element: this.getElementSelector(el),
            property: prop,
            value: inlineValue || computedValue,
            type: 'hardcoded-color',
          })
        }
      })
    })

    // 检查缺失的标准类名
    const requiredClasses = ['system-management-page', 'standard-page']
    requiredClasses.forEach((className) => {
      if (!element.classList.contains(className)) {
        issues.push({
          element: this.getElementSelector(element),
          type: 'missing-class',
          className: className,
        })
      }
    })

    return {
      compliant: issues.length === 0,
      issues: issues,
      timestamp: new Date().toISOString(),
    }
  }

  /**
   * 检查是否为硬编码颜色
   * @param {string} value - 颜色值
   * @returns {boolean}
   */
  isHardcodedColor(value) {
    if (!value || value === 'none' || value === 'transparent' || value === 'inherit') {
      return false
    }

    // 检查十六进制颜色
    if (value.match(/^#[0-9a-fA-F]{3,8}$/) && !value.includes('var(')) {
      return true
    }

    // 检查rgb颜色
    if (value.match(/^rgba?\([^)]+\)$/) && !value.includes('var(')) {
      return true
    }

    return false
  }

  /**
   * 获取元素选择器
   * @param {Element} element - 元素
   * @returns {string}
   */
  getElementSelector(element) {
    if (element.id) return `#${element.id}`
    if (element.className) {
      const classes = Array.from(element.classList).slice(0, 2).join('.')
      return `.${classes}`
    }
    return element.tagName.toLowerCase()
  }

  /**
   * 获取已应用标准化的页面列表
   * @returns {Array}
   */
  getAppliedPages() {
    return Array.from(this.appliedPages)
  }

  /**
   * 重置标准化状态
   */
  reset() {
    this.appliedPages.clear()
  }
}

/**
 * 创建系统主题标准化器实例
 * @returns {SystemThemeStandardizer}
 */
export function createSystemThemeStandardizer() {
  return new SystemThemeStandardizer()
}

/**
 * 应用系统管理页面主题标准化
 * @param {string} selector - 页面选择器
 * @returns {Promise<boolean>}
 */
export async function applySystemThemeStandardization(selector = '.system-management-page') {
  const standardizer = createSystemThemeStandardizer()
  return await standardizer.applyStandardTheme(selector)
}

/**
 * 检查系统管理页面主题合规性
 * @param {Element} element - 页面元素
 * @returns {Object}
 */
export function checkSystemThemeCompliance(element = document.body) {
  const standardizer = createSystemThemeStandardizer()
  return standardizer.checkCompliance(element)
}

// 导出默认实例
export default {
  SystemThemeStandardizer,
  createSystemThemeStandardizer,
  applySystemThemeStandardization,
  checkSystemThemeCompliance,
}
