/**
 * 主题一致性检查工具
 * 能够扫描和验证页面主题合规性
 */

import { THEME_COMPLIANCE_RULES, CSS_VARIABLE_MAPPING } from '@/config/theme-config.js'

/**
 * 主题合规性检查器类
 */
export class ThemeComplianceChecker {
  constructor() {
    this.rules = THEME_COMPLIANCE_RULES || {}
    this.variableMapping = CSS_VARIABLE_MAPPING || {}
    this.violations = []
  }

  /**
   * 检查页面主题合规性
   * @param {Element|string} target - 要检查的DOM元素或选择器
   * @returns {ComplianceReport} 合规性报告
   */
  checkPageCompliance(target = document.body) {
    this.violations = []
    const element = typeof target === 'string' ? document.querySelector(target) : target

    if (!element) {
      return this.generateReport('error', '未找到目标元素')
    }

    // 检查硬编码颜色
    this.checkHardcodedColors(element)

    // 检查CSS变量使用
    this.checkCSSVariableUsage(element)

    // 检查组件样式规范
    this.checkComponentCompliance(element)

    // 检查内联样式
    this.checkInlineStyles(element)

    return this.generateReport()
  }

  /**
   * 检查硬编码颜色使用
   * @param {Element} element - 要检查的元素
   */
  checkHardcodedColors(element) {
    const allElements = [element, ...element.querySelectorAll('*')]

    allElements.forEach((el) => {
      const computedStyle = window.getComputedStyle(el)
      const inlineStyle = el.style

      // 检查计算样式中的硬编码颜色
      this.checkStyleForHardcodedColors(computedStyle, el, 'computed')

      // 检查内联样式中的硬编码颜色
      if (inlineStyle.length > 0) {
        this.checkStyleForHardcodedColors(inlineStyle, el, 'inline')
      }
    })
  }

  /**
   * 检查样式对象中的硬编码颜色
   * @param {CSSStyleDeclaration} style - 样式对象
   * @param {Element} element - 元素
   * @param {string} type - 样式类型
   */
  checkStyleForHardcodedColors(style, element, type) {
    const colorProperties = [
      'color',
      'backgroundColor',
      'borderColor',
      'borderTopColor',
      'borderRightColor',
      'borderBottomColor',
      'borderLeftColor',
      'boxShadow',
      'textShadow',
      'outlineColor',
    ]

    colorProperties.forEach((prop) => {
      const value = style[prop]
      if (value && this.isHardcodedColor(value)) {
        this.addViolation({
          type: 'hardcoded-color',
          severity: 'high',
          element: this.getElementSelector(element),
          property: prop,
          value: value,
          styleType: type,
          message: `使用了硬编码颜色 ${value}，应使用CSS变量`,
        })
      }
    })
  }

  /**
   * 检查是否为硬编码颜色
   * @param {string} value - 颜色值
   * @returns {boolean}
   */
  isHardcodedColor(value) {
    if (
      !value ||
      value === 'none' ||
      value === 'transparent' ||
      value === 'inherit' ||
      value === 'initial'
    ) {
      return false
    }

    // 检查是否在禁用列表中
    const forbiddenColors = this.rules.forbiddenColors || []
    if (forbiddenColors.includes(value.toLowerCase())) {
      return true
    }

    // 检查十六进制颜色（但排除CSS变量）
    if (value.match(/^#[0-9a-fA-F]{3,8}$/) && !value.includes('var(')) {
      return true
    }

    // 检查rgb/rgba颜色（但排除CSS变量）
    if (value.match(/^rgba?\([^)]+\)$/) && !value.includes('var(')) {
      return true
    }

    // 检查hsl/hsla颜色（但排除CSS变量）
    if (value.match(/^hsla?\([^)]+\)$/) && !value.includes('var(')) {
      return true
    }

    return false
  }

  /**
   * 检查CSS变量使用情况
   * @param {Element} element - 要检查的元素
   */
  checkCSSVariableUsage(element) {
    const allElements = [element, ...element.querySelectorAll('*')]
    const usedVariables = new Set()
    const requiredVariables = this.getRequiredVariables()

    allElements.forEach((el) => {
      const computedStyle = window.getComputedStyle(el)

      // 扫描所有样式属性中的CSS变量
      for (let i = 0; i < computedStyle.length; i++) {
        const prop = computedStyle[i]
        const value = computedStyle.getPropertyValue(prop)

        if (value.includes('var(--')) {
          const variables = value.match(/var\(--[^)]+\)/g)
          if (variables) {
            variables.forEach((variable) => {
              const varName = variable.match(/var\((--[^,)]+)/)?.[1]
              if (varName) {
                usedVariables.add(varName)
              }
            })
          }
        }
      }
    })

    // 检查是否使用了推荐的变量
    requiredVariables.forEach((variable) => {
      if (!usedVariables.has(variable)) {
        this.addViolation({
          type: 'missing-css-variable',
          severity: 'medium',
          element: this.getElementSelector(element),
          variable: variable,
          message: `建议使用CSS变量 ${variable} 以保持主题一致性`,
        })
      }
    })
  }

  /**
   * 获取必需的CSS变量列表
   * @returns {string[]}
   */
  getRequiredVariables() {
    const variables = []
    Object.values(this.variableMapping).forEach((mapping) => {
      Object.keys(mapping).forEach((variable) => {
        variables.push(variable)
      })
    })
    return variables
  }

  /**
   * 检查组件样式合规性
   * @param {Element} element - 要检查的元素
   */
  checkComponentCompliance(element) {
    const componentRules = this.rules.componentRules || {}

    Object.entries(componentRules).forEach(([componentType, rules]) => {
      const components = this.findComponentElements(element, componentType)

      components.forEach((component) => {
        // 检查必需的CSS类
        if (rules.requiredClasses) {
          rules.requiredClasses.forEach((className) => {
            if (!component.classList.contains(className)) {
              this.addViolation({
                type: 'missing-css-class',
                severity: 'medium',
                element: this.getElementSelector(component),
                componentType: componentType,
                className: className,
                message: `${componentType}组件缺少必需的CSS类: ${className}`,
              })
            }
          })
        }

        // 检查必需的CSS变量
        if (rules.requiredVariables) {
          const computedStyle = window.getComputedStyle(component)
          rules.requiredVariables.forEach((variable) => {
            const value = computedStyle.getPropertyValue(variable)
            if (!value || value === 'initial' || value === 'inherit') {
              this.addViolation({
                type: 'missing-component-variable',
                severity: 'medium',
                element: this.getElementSelector(component),
                componentType: componentType,
                variable: variable,
                message: `${componentType}组件未使用必需的CSS变量: ${variable}`,
              })
            }
          })
        }
      })
    })
  }

  /**
   * 查找特定类型的组件元素
   * @param {Element} element - 根元素
   * @param {string} componentType - 组件类型
   * @returns {Element[]}
   */
  findComponentElements(element, componentType) {
    const selectors = {
      table: 'table, .n-data-table, .standard-table',
      form: 'form, .n-form, .standard-form',
      button: 'button, .n-button, .standard-button',
      modal: '.n-modal, .standard-modal',
    }

    const selector = selectors[componentType]
    if (!selector) return []

    return Array.from(element.querySelectorAll(selector))
  }

  /**
   * 检查内联样式
   * @param {Element} element - 要检查的元素
   */
  checkInlineStyles(element) {
    const allElements = [element, ...element.querySelectorAll('*')]

    allElements.forEach((el) => {
      if (el.style.length > 0) {
        // 检查是否有过多的内联样式
        if (el.style.length > 5) {
          this.addViolation({
            type: 'excessive-inline-styles',
            severity: 'low',
            element: this.getElementSelector(el),
            styleCount: el.style.length,
            message: `元素包含过多内联样式(${el.style.length}个)，建议使用CSS类`,
          })
        }

        // 检查内联样式中的主题相关属性
        const themeProperties = [
          'color',
          'backgroundColor',
          'borderColor',
          'fontSize',
          'padding',
          'margin',
        ]
        themeProperties.forEach((prop) => {
          if (el.style[prop]) {
            this.addViolation({
              type: 'inline-theme-style',
              severity: 'medium',
              element: this.getElementSelector(el),
              property: prop,
              value: el.style[prop],
              message: `内联样式中包含主题相关属性 ${prop}，建议使用CSS变量`,
            })
          }
        })
      }
    })
  }

  /**
   * 添加违规记录
   * @param {Object} violation - 违规信息
   */
  addViolation(violation) {
    this.violations.push({
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString(),
      ...violation,
    })
  }

  /**
   * 获取元素选择器
   * @param {Element} element - 元素
   * @returns {string}
   */
  getElementSelector(element) {
    if (element.id) {
      return `#${element.id}`
    }

    if (element.className) {
      const classes = Array.from(element.classList).slice(0, 2).join('.')
      return `.${classes}`
    }

    return element.tagName.toLowerCase()
  }

  /**
   * 生成合规性报告
   * @param {string} status - 报告状态
   * @param {string} error - 错误信息
   * @returns {ComplianceReport}
   */
  generateReport(status = 'success', error = null) {
    const report = {
      timestamp: new Date().toISOString(),
      status: error ? 'error' : this.violations.length === 0 ? 'compliant' : 'non-compliant',
      error: error,
      summary: {
        totalViolations: this.violations.length,
        highSeverity: this.violations.filter((v) => v.severity === 'high').length,
        mediumSeverity: this.violations.filter((v) => v.severity === 'medium').length,
        lowSeverity: this.violations.filter((v) => v.severity === 'low').length,
      },
      violations: this.violations,
      recommendations: this.generateRecommendations(),
    }

    return report
  }

  /**
   * 生成修复建议
   * @returns {string[]}
   */
  generateRecommendations() {
    const recommendations = []
    const violationTypes = [...new Set(this.violations.map((v) => v.type))]

    violationTypes.forEach((type) => {
      switch (type) {
        case 'hardcoded-color':
          recommendations.push(
            '将硬编码颜色替换为CSS变量，如使用 var(--primary-color) 替代 #1890ff'
          )
          break
        case 'missing-css-variable':
          recommendations.push('在组件中使用标准化的CSS变量以保持主题一致性')
          break
        case 'missing-css-class':
          recommendations.push('为组件添加标准化的CSS类名以确保样式一致性')
          break
        case 'excessive-inline-styles':
          recommendations.push('减少内联样式的使用，将样式移至CSS类中')
          break
        case 'inline-theme-style':
          recommendations.push('避免在内联样式中使用主题相关属性，使用CSS变量替代')
          break
      }
    })

    return [...new Set(recommendations)]
  }
}

/**
 * 创建主题合规性检查器实例
 * @returns {ThemeComplianceChecker}
 */
export function createThemeChecker() {
  return new ThemeComplianceChecker()
}

/**
 * 快速检查页面主题合规性
 * @param {Element|string} target - 目标元素或选择器
 * @returns {Promise<ComplianceReport>}
 */
export async function checkPageThemeCompliance(target) {
  const checker = createThemeChecker()
  return checker.checkPageCompliance(target)
}

/**
 * 批量检查系统管理页面
 * @returns {Promise<Object>} 批量检查结果
 */
export async function checkSystemPagesCompliance() {
  const systemPageSelectors = [
    '.system-user-page',
    '.system-role-page',
    '.system-menu-page',
    '.system-dept-page',
    '.system-api-page',
    '.system-dict-page',
  ]

  const results = {}
  const checker = createThemeChecker()

  for (const selector of systemPageSelectors) {
    const element = document.querySelector(selector)
    if (element) {
      results[selector] = checker.checkPageCompliance(element)
    }
  }

  return {
    timestamp: new Date().toISOString(),
    totalPages: Object.keys(results).length,
    results: results,
    overallCompliance: Object.values(results).every((r) => r.status === 'compliant'),
  }
}

export default {
  ThemeComplianceChecker,
  createThemeChecker,
  checkPageThemeCompliance,
  checkSystemPagesCompliance,
}
