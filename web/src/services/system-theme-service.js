/**
 * 系统管理主题服务
 * 提供主题切换功能在系统管理模块的完整支持
 */

import { useThemeStore } from '@/store/theme.js'
import { THEME_PRESETS } from '@/config/theme-config.js'
import { applySystemThemeStandardization } from '@/utils/theme-system-standardizer.js'

/**
 * 系统管理主题服务类
 */
export class SystemThemeService {
  constructor() {
    this.themeStore = null
    this.currentTheme = 'default'
    this.systemPages = [
      '.system-user-page',
      '.system-role-page',
      '.system-menu-page',
      '.system-dept-page',
      '.system-api-page',
      '.system-api-groups-page',
      '.system-dict-type-page',
      '.system-dict-data-page',
      '.system-param-page',
      '.system-auditlog-page',
    ]
  }

  /**
   * 初始化主题服务
   */
  async initialize() {
    if (!this.themeStore) {
      this.themeStore = useThemeStore()
    }

    // 加载保存的主题设置
    await this.themeStore.loadThemeFromStorage()

    // 应用主题到系统管理页面
    await this.applyThemeToSystemPages()

    return true
  }

  /**
   * 切换主题
   * @param {string} themeKey - 主题键值
   * @returns {Promise<boolean>}
   */
  async switchTheme(themeKey) {
    try {
      if (!this.themeStore) {
        await this.initialize()
      }

      // 应用主题预设
      const success = await this.themeStore.applyThemePreset(themeKey)

      if (success) {
        this.currentTheme = themeKey

        // 应用主题到系统管理页面
        await this.applyThemeToSystemPages()

        // 触发主题变更事件
        this.emitThemeChangeEvent(themeKey)

        return true
      }

      return false
    } catch (error) {
      console.error('切换主题失败:', error)
      return false
    }
  }

  /**
   * 应用主题到系统管理页面
   * @returns {Promise<void>}
   */
  async applyThemeToSystemPages() {
    try {
      // 应用标准化主题到所有系统管理页面
      for (const pageSelector of this.systemPages) {
        await applySystemThemeStandardization(pageSelector)
      }

      // 应用当前主题的CSS类
      this.applyThemeClass()

      // 更新CSS变量
      this.updateCSSVariables()
    } catch (error) {
      console.error('应用主题到系统管理页面失败:', error)
    }
  }

  /**
   * 应用主题CSS类
   */
  applyThemeClass() {
    const html = document.documentElement

    // 移除所有主题类
    THEME_PRESETS.forEach((preset) => {
      html.classList.remove(preset.cssClass)
    })

    // 添加当前主题类
    const currentPreset = THEME_PRESETS.find((p) => p.key === this.currentTheme)
    if (currentPreset) {
      html.classList.add(currentPreset.cssClass)
    }
  }

  /**
   * 更新CSS变量
   */
  updateCSSVariables() {
    if (!this.themeStore) return

    const root = document.documentElement
    const currentPreset = THEME_PRESETS.find((p) => p.key === this.currentTheme)

    if (currentPreset) {
      // 更新主色调
      root.style.setProperty('--primary-color', currentPreset.primaryColor)

      // 生成主色调变体
      const variants = this.generateColorVariants(currentPreset.primaryColor)
      Object.entries(variants).forEach(([property, value]) => {
        root.style.setProperty(property, value)
      })
    }
  }

  /**
   * 生成颜色变体
   * @param {string} baseColor - 基础颜色
   * @returns {Object}
   */
  generateColorVariants(baseColor) {
    return {
      '--primary-color-hover': this.lightenColor(baseColor, 10),
      '--primary-color-pressed': this.darkenColor(baseColor, 10),
      '--primary-color-light': this.lightenColor(baseColor, 30),
      '--primary-color-lighter': this.lightenColor(baseColor, 40),
      '--primary-color-dark': this.darkenColor(baseColor, 20),
    }
  }

  /**
   * 颜色变亮
   * @param {string} color - 十六进制颜色
   * @param {number} percent - 变亮百分比
   * @returns {string}
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
   * @param {string} color - 十六进制颜色
   * @param {number} percent - 变暗百分比
   * @returns {string}
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
   * 获取当前主题信息
   * @returns {Object}
   */
  getCurrentTheme() {
    const preset = THEME_PRESETS.find((p) => p.key === this.currentTheme)
    return {
      key: this.currentTheme,
      name: preset?.name || '默认',
      primaryColor: preset?.primaryColor || '#343434',
      description: preset?.description || '',
      cssClass: preset?.cssClass || 'theme-default',
    }
  }

  /**
   * 获取所有可用主题
   * @returns {Array}
   */
  getAvailableThemes() {
    return THEME_PRESETS.map((preset) => ({
      key: preset.key,
      name: preset.name,
      primaryColor: preset.primaryColor,
      description: preset.description,
      cssClass: preset.cssClass,
    }))
  }

  /**
   * 检查主题是否支持系统管理模块
   * @param {string} themeKey - 主题键值
   * @returns {boolean}
   */
  isThemeSupportedForSystem(themeKey) {
    return THEME_PRESETS.some((preset) => preset.key === themeKey)
  }

  /**
   * 预览主题效果
   * @param {string} themeKey - 主题键值
   * @returns {Promise<void>}
   */
  async previewTheme(themeKey) {
    const originalTheme = this.currentTheme

    try {
      // 临时应用主题
      await this.switchTheme(themeKey)

      // 3秒后恢复原主题
      setTimeout(async () => {
        await this.switchTheme(originalTheme)
      }, 3000)
    } catch (error) {
      console.error('预览主题失败:', error)
      // 恢复原主题
      await this.switchTheme(originalTheme)
    }
  }

  /**
   * 触发主题变更事件
   * @param {string} themeKey - 主题键值
   */
  emitThemeChangeEvent(themeKey) {
    const event = new CustomEvent('system-theme-changed', {
      detail: {
        themeKey,
        theme: this.getCurrentTheme(),
        timestamp: new Date().toISOString(),
      },
    })

    document.dispatchEvent(event)
  }

  /**
   * 监听主题变更事件
   * @param {Function} callback - 回调函数
   * @returns {Function} 取消监听函数
   */
  onThemeChange(callback) {
    const handler = (event) => {
      callback(event.detail)
    }

    document.addEventListener('system-theme-changed', handler)

    // 返回取消监听函数
    return () => {
      document.removeEventListener('system-theme-changed', handler)
    }
  }

  /**
   * 重置主题为默认
   * @returns {Promise<boolean>}
   */
  async resetTheme() {
    return await this.switchTheme('default')
  }

  /**
   * 保存主题设置
   */
  saveThemeSettings() {
    if (this.themeStore) {
      this.themeStore.saveThemeToStorage()
    }

    // 额外保存系统管理模块特定设置
    const systemThemeSettings = {
      currentTheme: this.currentTheme,
      appliedPages: this.systemPages,
      timestamp: Date.now(),
    }

    localStorage.setItem('system-theme-settings', JSON.stringify(systemThemeSettings))
  }

  /**
   * 加载主题设置
   */
  loadThemeSettings() {
    try {
      const settings = localStorage.getItem('system-theme-settings')
      if (settings) {
        const parsed = JSON.parse(settings)
        this.currentTheme = parsed.currentTheme || 'default'
      }
    } catch (error) {
      console.warn('加载系统主题设置失败:', error)
      this.currentTheme = 'default'
    }
  }
}

// 创建单例实例
let systemThemeServiceInstance = null

/**
 * 获取系统主题服务实例
 * @returns {SystemThemeService}
 */
export function getSystemThemeService() {
  if (!systemThemeServiceInstance) {
    systemThemeServiceInstance = new SystemThemeService()
  }
  return systemThemeServiceInstance
}

/**
 * 初始化系统主题服务
 * @returns {Promise<SystemThemeService>}
 */
export async function initializeSystemThemeService() {
  const service = getSystemThemeService()
  await service.initialize()
  return service
}

/**
 * 快速切换系统管理主题
 * @param {string} themeKey - 主题键值
 * @returns {Promise<boolean>}
 */
export async function switchSystemTheme(themeKey) {
  const service = getSystemThemeService()
  return await service.switchTheme(themeKey)
}

/**
 * 获取当前系统主题
 * @returns {Object}
 */
export function getCurrentSystemTheme() {
  const service = getSystemThemeService()
  return service.getCurrentTheme()
}

// 导出默认配置
export default {
  SystemThemeService,
  getSystemThemeService,
  initializeSystemThemeService,
  switchSystemTheme,
  getCurrentSystemTheme,
}
