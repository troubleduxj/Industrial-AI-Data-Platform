/**
 * 主题变量映射系统
 * 确保所有组件使用统一的设计令牌
 */

import { DESIGN_TOKENS, CSS_VARIABLE_MAPPING, THEME_PRESETS } from '@/config/theme-config.js'

/**
 * 主题变量映射器类
 */
export class ThemeVariableMapper {
  constructor() {
    this.tokens = DESIGN_TOKENS
    this.mapping = CSS_VARIABLE_MAPPING
    this.presets = THEME_PRESETS
    this.appliedVariables = new Map()
  }

  /**
   * 初始化主题变量映射
   */
  initialize() {
    this.applyDesignTokensToCSS()
    this.setupThemePresets()
    this.observeThemeChanges()
  }

  /**
   * 将设计令牌应用到CSS变量
   */
  applyDesignTokensToCSS() {
    const root = document.documentElement

    // 应用颜色令牌
    this.applyColorTokens(root)

    // 应用间距令牌
    this.applySpacingTokens(root)

    // 应用字体令牌
    this.applyTypographyTokens(root)

    // 应用边框圆角令牌
    this.applyBorderRadiusTokens(root)

    // 应用阴影令牌
    this.applyShadowTokens(root)

    console.log('主题变量映射已初始化')
  }

  /**
   * 应用颜色令牌
   * @param {HTMLElement} root - 根元素
   */
  applyColorTokens(root) {
    // 主色调
    Object.entries(this.tokens.colors.primary).forEach(([key, value]) => {
      const cssVar = `--primary-color-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })

    // 语义化颜色
    Object.entries(this.tokens.colors.semantic).forEach(([key, value]) => {
      const cssVar = `--${key}-color`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })

    // 中性色 - 文本
    Object.entries(this.tokens.colors.neutral.text).forEach(([key, value]) => {
      const cssVar = `--text-color-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })

    // 中性色 - 背景
    Object.entries(this.tokens.colors.neutral.background).forEach(([key, value]) => {
      const cssVar = `--background-color-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })

    // 中性色 - 边框
    Object.entries(this.tokens.colors.neutral.border).forEach(([key, value]) => {
      const cssVar = `--border-color-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })
  }

  /**
   * 应用间距令牌
   * @param {HTMLElement} root - 根元素
   */
  applySpacingTokens(root) {
    Object.entries(this.tokens.spacing).forEach(([key, value]) => {
      const cssVar = `--spacing-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })
  }

  /**
   * 应用字体令牌
   * @param {HTMLElement} root - 根元素
   */
  applyTypographyTokens(root) {
    // 字体大小
    Object.entries(this.tokens.typography.fontSizes).forEach(([key, value]) => {
      const cssVar = `--font-size-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })

    // 字体粗细
    Object.entries(this.tokens.typography.fontWeights).forEach(([key, value]) => {
      const cssVar = `--font-weight-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })

    // 行高
    Object.entries(this.tokens.typography.lineHeights).forEach(([key, value]) => {
      const cssVar = `--line-height-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })
  }

  /**
   * 应用边框圆角令牌
   * @param {HTMLElement} root - 根元素
   */
  applyBorderRadiusTokens(root) {
    Object.entries(this.tokens.borderRadius).forEach(([key, value]) => {
      const cssVar = `--border-radius-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })
  }

  /**
   * 应用阴影令牌
   * @param {HTMLElement} root - 根元素
   */
  applyShadowTokens(root) {
    Object.entries(this.tokens.shadows).forEach(([key, value]) => {
      const cssVar = `--shadow-${key}`
      root.style.setProperty(cssVar, value)
      this.appliedVariables.set(cssVar, value)
    })
  }

  /**
   * 设置主题预设
   */
  setupThemePresets() {
    this.presets.forEach((preset) => {
      this.createThemePresetCSS(preset)
    })
  }

  /**
   * 创建主题预设CSS
   * @param {Object} preset - 主题预设
   */
  createThemePresetCSS(preset) {
    const { key, primaryColor, cssClass } = preset

    // 生成主题色变体
    const variants = this.generateColorVariants(primaryColor)

    // 创建CSS规则
    const cssRules = []
    cssRules.push(`.${cssClass} {`)

    Object.entries(variants).forEach(([varName, value]) => {
      cssRules.push(`  --${varName}: ${value};`)
    })

    cssRules.push('}')

    // 暗色模式变体
    cssRules.push(`.dark .${cssClass} {`)
    const darkVariants = this.generateDarkColorVariants(primaryColor)
    Object.entries(darkVariants).forEach(([varName, value]) => {
      cssRules.push(`  --${varName}: ${value};`)
    })
    cssRules.push('}')

    // 将CSS规则添加到样式表
    this.injectCSS(cssRules.join('\n'), `theme-preset-${key}`)
  }

  /**
   * 生成颜色变体
   * @param {string} baseColor - 基础颜色
   * @returns {Object} 颜色变体对象
   */
  generateColorVariants(baseColor) {
    return {
      'primary-color': baseColor,
      'primary-color-hover': this.lightenColor(baseColor, 10),
      'primary-color-pressed': this.darkenColor(baseColor, 10),
      'primary-color-light': this.lightenColor(baseColor, 30),
      'primary-color-lighter': this.lightenColor(baseColor, 40),
      'primary-color-dark': this.darkenColor(baseColor, 20),
      'primary-foreground': this.getContrastColor(baseColor),
      ring: baseColor,
      'sidebar-primary': baseColor,
      'sidebar-primary-foreground': this.getContrastColor(baseColor),
      'sidebar-ring': baseColor,
    }
  }

  /**
   * 生成暗色模式颜色变体
   * @param {string} baseColor - 基础颜色
   * @returns {Object} 暗色模式颜色变体
   */
  generateDarkColorVariants(baseColor) {
    return {
      'primary-color': baseColor,
      'primary-color-hover': this.lightenColor(baseColor, 15),
      'primary-color-pressed': this.darkenColor(baseColor, 15),
      'primary-foreground': this.getDarkContrastColor(baseColor),
      ring: this.darkenColor(baseColor, 10),
      'sidebar-primary': baseColor,
      'sidebar-primary-foreground': this.getDarkContrastColor(baseColor),
      'sidebar-ring': this.darkenColor(baseColor, 10),
    }
  }

  /**
   * 颜色变亮
   * @param {string} color - 颜色值
   * @param {number} percent - 变亮百分比
   * @returns {string} 变亮后的颜色
   */
  lightenColor(color, percent) {
    const num = parseInt(color.replace('#', ''), 16)
    const amt = Math.round(2.55 * percent)
    const R = (num >> 16) + amt
    const G = ((num >> 8) & 0x00ff) + amt
    const B = (num & 0x0000ff) + amt
    return (
      '#' +
      (
        0x1000000 +
        (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
        (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
        (B < 255 ? (B < 1 ? 0 : B) : 255)
      )
        .toString(16)
        .slice(1)
    )
  }

  /**
   * 颜色变暗
   * @param {string} color - 颜色值
   * @param {number} percent - 变暗百分比
   * @returns {string} 变暗后的颜色
   */
  darkenColor(color, percent) {
    const num = parseInt(color.replace('#', ''), 16)
    const amt = Math.round(2.55 * percent)
    const R = (num >> 16) - amt
    const G = ((num >> 8) & 0x00ff) - amt
    const B = (num & 0x0000ff) - amt
    return (
      '#' +
      (
        0x1000000 +
        (R > 255 ? 255 : R < 0 ? 0 : R) * 0x10000 +
        (G > 255 ? 255 : G < 0 ? 0 : G) * 0x100 +
        (B > 255 ? 255 : B < 0 ? 0 : B)
      )
        .toString(16)
        .slice(1)
    )
  }

  /**
   * 获取对比色
   * @param {string} color - 基础颜色
   * @returns {string} 对比色
   */
  getContrastColor(color) {
    const brightness = this.getColorBrightness(color)
    return brightness > 128 ? '#000000' : '#ffffff'
  }

  /**
   * 获取暗色模式对比色
   * @param {string} color - 基础颜色
   * @returns {string} 暗色模式对比色
   */
  getDarkContrastColor(color) {
    const brightness = this.getColorBrightness(color)
    return brightness > 128 ? '#1a1a1a' : '#ffffff'
  }

  /**
   * 获取颜色亮度
   * @param {string} color - 颜色值
   * @returns {number} 亮度值
   */
  getColorBrightness(color) {
    const hex = color.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    return (r * 299 + g * 587 + b * 114) / 1000
  }

  /**
   * 注入CSS到页面
   * @param {string} css - CSS内容
   * @param {string} id - 样式表ID
   */
  injectCSS(css, id) {
    // 移除已存在的样式表
    const existingStyle = document.getElementById(id)
    if (existingStyle) {
      existingStyle.remove()
    }

    // 创建新的样式表
    const style = document.createElement('style')
    style.id = id
    style.textContent = css
    document.head.appendChild(style)
  }

  /**
   * 应用主题预设
   * @param {string} presetKey - 预设键名
   * @returns {boolean} 是否成功应用
   */
  applyThemePreset(presetKey) {
    const preset = this.presets.find((p) => p.key === presetKey)
    if (!preset) {
      console.warn(`未找到主题预设: ${presetKey}`)
      return false
    }

    // 移除所有主题类
    const body = document.body
    this.presets.forEach((p) => {
      body.classList.remove(p.cssClass)
    })

    // 应用新主题类
    body.classList.add(preset.cssClass)

    // 更新主色调变量
    this.updatePrimaryColor(preset.primaryColor)

    console.log(`已应用主题预设: ${preset.name}`)
    return true
  }

  /**
   * 更新主色调
   * @param {string} color - 新的主色调
   */
  updatePrimaryColor(color) {
    const root = document.documentElement
    const variants = this.generateColorVariants(color)

    Object.entries(variants).forEach(([varName, value]) => {
      root.style.setProperty(`--${varName}`, value)
      this.appliedVariables.set(`--${varName}`, value)
    })
  }

  /**
   * 获取当前应用的变量
   * @returns {Map} 当前变量映射
   */
  getAppliedVariables() {
    return new Map(this.appliedVariables)
  }

  /**
   * 获取变量值
   * @param {string} variableName - 变量名
   * @returns {string|null} 变量值
   */
  getVariableValue(variableName) {
    return this.appliedVariables.get(variableName) || null
  }

  /**
   * 验证变量映射
   * @returns {Object} 验证结果
   */
  validateMapping() {
    const result = {
      valid: true,
      missing: [],
      invalid: [],
    }

    // 检查所有映射的变量是否已应用
    Object.values(this.mapping).forEach((mapping) => {
      Object.keys(mapping).forEach((variable) => {
        if (!this.appliedVariables.has(variable)) {
          result.missing.push(variable)
          result.valid = false
        }
      })
    })

    return result
  }

  /**
   * 监听主题变化
   */
  observeThemeChanges() {
    // 监听暗色模式变化
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)')
    darkModeQuery.addEventListener('change', (e) => {
      this.handleSystemThemeChange(e.matches)
    })

    // 监听CSS变量变化
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
          this.handleStyleChange(mutation.target)
        }
      })
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['style'],
    })
  }

  /**
   * 处理系统主题变化
   * @param {boolean} isDark - 是否为暗色模式
   */
  handleSystemThemeChange(isDark) {
    console.log(`系统主题变化: ${isDark ? '暗色' : '亮色'}模式`)
    // 这里可以添加自动切换逻辑
  }

  /**
   * 处理样式变化
   * @param {Element} target - 目标元素
   */
  handleStyleChange(target) {
    if (target === document.documentElement) {
      // 根元素样式变化，可能是主题变量更新
      this.syncAppliedVariables()
    }
  }

  /**
   * 同步已应用的变量
   */
  syncAppliedVariables() {
    const root = document.documentElement
    const computedStyle = window.getComputedStyle(root)

    this.appliedVariables.forEach((value, variable) => {
      const currentValue = computedStyle.getPropertyValue(variable)
      if (currentValue && currentValue !== value) {
        this.appliedVariables.set(variable, currentValue)
      }
    })
  }

  /**
   * 重置所有主题变量
   */
  reset() {
    const root = document.documentElement

    this.appliedVariables.forEach((value, variable) => {
      root.style.removeProperty(variable)
    })

    this.appliedVariables.clear()

    // 重新初始化
    this.initialize()
  }

  /**
   * 导出当前主题配置
   * @returns {Object} 主题配置
   */
  exportThemeConfig() {
    return {
      timestamp: new Date().toISOString(),
      appliedVariables: Object.fromEntries(this.appliedVariables),
      currentPreset: this.getCurrentPreset(),
      tokens: this.tokens,
    }
  }

  /**
   * 获取当前主题预设
   * @returns {Object|null} 当前预设
   */
  getCurrentPreset() {
    const body = document.body
    return this.presets.find((preset) => body.classList.contains(preset.cssClass)) || null
  }
}

/**
 * 创建主题变量映射器实例
 * @returns {ThemeVariableMapper}
 */
export function createThemeMapper() {
  return new ThemeVariableMapper()
}

/**
 * 全局主题映射器实例
 */
let globalMapper = null

/**
 * 获取全局主题映射器
 * @returns {ThemeVariableMapper}
 */
export function getGlobalThemeMapper() {
  if (!globalMapper) {
    globalMapper = createThemeMapper()
    globalMapper.initialize()
  }
  return globalMapper
}

/**
 * 初始化主题系统
 */
export function initializeThemeSystem() {
  const mapper = getGlobalThemeMapper()
  console.log('主题系统已初始化')
  return mapper
}

// 导出工具函数
export const themeUtils = {
  /**
   * 获取CSS变量值
   * @param {string} variableName - 变量名
   * @returns {string} 变量值
   */
  getCSSVariable(variableName) {
    return getComputedStyle(document.documentElement).getPropertyValue(variableName).trim()
  },

  /**
   * 设置CSS变量值
   * @param {string} variableName - 变量名
   * @param {string} value - 变量值
   */
  setCSSVariable(variableName, value) {
    document.documentElement.style.setProperty(variableName, value)
  },

  /**
   * 检查是否为暗色模式
   * @returns {boolean}
   */
  isDarkMode() {
    return document.documentElement.classList.contains('dark')
  },

  /**
   * 切换暗色模式
   */
  toggleDarkMode() {
    document.documentElement.classList.toggle('dark')
  },
}

export default {
  ThemeVariableMapper,
  createThemeMapper,
  getGlobalThemeMapper,
  initializeThemeSystem,
  themeUtils,
}
