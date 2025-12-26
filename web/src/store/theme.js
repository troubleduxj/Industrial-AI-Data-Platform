import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getThemeManagementService } from '@/services/theme-management-service.js'
import { THEME_PRESETS } from '@/config/theme-config.js'

/**
 * 主题管理Store
 * 功能：管理应用主题色、主题模式等主题相关状态
 * 集成标准化主题管理系统
 * 参数：无
 * 返回值：主题管理相关的状态和方法
 */
export const useThemeStore = defineStore('theme', () => {
  // 主题色
  const primaryColor = ref('#F4511E')

  // 主题模式 (light/dark)
  const themeMode = ref('light')

  // 是否启用主题切换
  const themeSwitcherEnabled = ref(true)

  // 预设主题色方案（使用标准化配置）
  const themePresets = ref(THEME_PRESETS)

  // 主题管理服务实例
  const themeService = ref(null)

  // 计算属性
  const isDarkMode = computed(() => themeMode.value === 'dark')

  const currentThemePreset = computed(() => {
    return themePresets.value.find((preset) => preset.primaryColor === primaryColor.value) || null
  })

  // 生成主题色变体
  const themeColorVariants = computed(() => {
    const color = primaryColor.value
    return {
      primary: color,
      primaryHover: lightenColor(color, 10),
      primaryPressed: darkenColor(color, 10),
      primarySuppl: color,
      primaryLight: lightenColor(color, 30),
      primaryDark: darkenColor(color, 20),
    }
  })

  const naiveThemeOverrides = computed(() => {
    const color = primaryColor.value
    return {
      common: {
        primaryColor: color,
        primaryColorHover: lightenColor(color, 10),
        primaryColorPressed: darkenColor(color, 10),
        primaryColorSuppl: color,
        // 确保所有可能的颜色属性都使用 hex 格式
        textColorBase: themeMode.value === 'dark' ? '#ffffff' : '#000000',
        textColor1: themeMode.value === 'dark' ? '#ffffff' : '#262626',
        textColor2: themeMode.value === 'dark' ? '#ffffffd1' : '#525252',
        textColor3: themeMode.value === 'dark' ? '#ffffff73' : '#8c8c8c',
        textColorDisabled: themeMode.value === 'dark' ? '#ffffff4d' : '#c0c0c0',
        placeholderColor: themeMode.value === 'dark' ? '#ffffff4d' : '#c0c0c0',
        placeholderColorDisabled: themeMode.value === 'dark' ? '#ffffff26' : '#e0e0e0',
        iconColor: themeMode.value === 'dark' ? '#ffffff73' : '#8c8c8c',
        iconColorHover: themeMode.value === 'dark' ? '#ffffffd1' : '#525252',
        iconColorPressed: themeMode.value === 'dark' ? '#ffffff4d' : '#c0c0c0',
        iconColorDisabled: themeMode.value === 'dark' ? '#ffffff26' : '#e0e0e0',
        opacity1: '0.82',
        opacity2: '0.72',
        opacity3: '0.38',
        opacity4: '0.24',
        opacity5: '0.18',
        dividerColor: themeMode.value === 'dark' ? '#ffffff17' : '#efeff5',
        borderColor: themeMode.value === 'dark' ? '#ffffff17' : '#efeff5',
        closeIconColor: themeMode.value === 'dark' ? '#ffffff73' : '#8c8c8c',
        closeIconColorHover: themeMode.value === 'dark' ? '#ffffffd1' : '#525252',
        closeIconColorPressed: themeMode.value === 'dark' ? '#ffffff4d' : '#c0c0c0',
        clearColor: themeMode.value === 'dark' ? '#ffffff73' : '#8c8c8c',
        clearColorHover: themeMode.value === 'dark' ? '#ffffffd1' : '#525252',
        clearColorPressed: themeMode.value === 'dark' ? '#ffffff4d' : '#c0c0c0',
        scrollbarColor: themeMode.value === 'dark' ? '#ffffff26' : '#d9d9d9',
        scrollbarColorHover: themeMode.value === 'dark' ? '#ffffff4d' : '#b3b3b3',
        scrollbarWidth: '5px',
        scrollbarHeight: '5px',
        scrollbarBorderRadius: '5px',
        progressRailColor: themeMode.value === 'dark' ? '#ffffff17' : '#efeff5',
        railColor: themeMode.value === 'dark' ? '#ffffff17' : '#efeff5',
        popoverColor: themeMode.value === 'dark' ? '#48484e' : '#ffffff',
        tableColor: themeMode.value === 'dark' ? '#000000' : '#ffffff',
        cardColor: themeMode.value === 'dark' ? '#18181c' : '#ffffff',
        modalColor: themeMode.value === 'dark' ? '#18181c' : '#ffffff',
        bodyColor: themeMode.value === 'dark' ? '#101014' : '#ffffff',
        tagColor: themeMode.value === 'dark' ? '#18181c' : '#ffffff',
        avatarColor: themeMode.value === 'dark' ? '#ffffff17' : '#efeff5',
        invertedColor: themeMode.value === 'dark' ? '#ffffff' : '#000000',
        inputColor: themeMode.value === 'dark' ? '#ffffff00' : '#ffffff00',
        codeColor: themeMode.value === 'dark' ? '#ffffff17' : '#efeff5',
        tabColor: themeMode.value === 'dark' ? '#18181c' : '#ffffff',
        actionColor: themeMode.value === 'dark' ? '#ffffff17' : '#efeff5',
        tableHeaderColor: themeMode.value === 'dark' ? '#ffffff0f' : '#fafafc',
        hoverColor: themeMode.value === 'dark' ? '#ffffff0f' : '#f5f5f5',
        tableColorHover: themeMode.value === 'dark' ? '#ffffff0f' : '#f5f5f5',
        tableColorStriped: themeMode.value === 'dark' ? '#ffffff0a' : '#fafafc',
        pressedColor: themeMode.value === 'dark' ? '#ffffff17' : '#e5e5e5',
        opacityDisabled: '0.5',
        inputColorDisabled: themeMode.value === 'dark' ? '#ffffff0a' : '#f5f5f5',
        buttonColor2: themeMode.value === 'dark' ? '#ffffff17' : '#efeff5',
        buttonColor2Hover: themeMode.value === 'dark' ? '#ffffff26' : '#e5e5e5',
        buttonColor2Pressed: themeMode.value === 'dark' ? '#ffffff0f' : '#d9d9d9',
        boxShadow1:
          '0 1px 2px -2px rgba(0, 0, 0, .08), 0 3px 6px 0 rgba(0, 0, 0, .06), 0 5px 12px 4px rgba(0, 0, 0, .04)',
        boxShadow2:
          '0 3px 6px -4px rgba(0, 0, 0, .12), 0 6px 16px 0 rgba(0, 0, 0, .08), 0 9px 28px 8px rgba(0, 0, 0, .05)',
        boxShadow3:
          '0 6px 16px -9px rgba(0, 0, 0, .08), 0 9px 28px 0 rgba(0, 0, 0, .05), 0 12px 48px 16px rgba(0, 0, 0, .03)',
      },
      // 强制覆盖可能生成 oklch 颜色的组件
      Input: {
        color: themeMode.value === 'dark' ? '#ffffff00' : '#ffffff00', // 透明背景
        colorDisabled: themeMode.value === 'dark' ? '#ffffff0a' : '#f5f5f5',
        textColor: themeMode.value === 'dark' ? '#ffffff' : '#000000',
        textColorDisabled: themeMode.value === 'dark' ? '#ffffff4d' : '#c0c0c0',
        placeholderColor: themeMode.value === 'dark' ? '#ffffff4d' : '#c0c0c0',
        placeholderColorDisabled: themeMode.value === 'dark' ? '#ffffff26' : '#e0e0e0',
        caretColor: color,
        border: `1px solid ${themeMode.value === 'dark' ? '#ffffff17' : '#efeff5'}`,
        borderHover: `1px solid ${lightenColor(color, 10)}`,
        borderFocus: `1px solid ${color}`,
        borderDisabled: `1px solid ${themeMode.value === 'dark' ? '#ffffff0f' : '#f0f0f0'}`,
        borderError: `1px solid ${themeMode.value === 'dark' ? '#ff6b6b' : '#ff4d4f'}`,
        borderWarning: `1px solid ${themeMode.value === 'dark' ? '#ffa940' : '#faad14'}`,
        boxShadowFocus: `0 0 0 2px ${color}25`,
      },
    }
  })

  // Actions

  /**
   * 设置主题色
   * 功能：更新主题色并应用到CSS变量
   * 参数：color - 任意格式的颜色值
   * 返回值：无
   */
  const setPrimaryColor = (color) => {
    // 确保颜色是十六进制格式
    const hexColor = convertColorToHex(color)
    primaryColor.value = hexColor
    applyThemeColorToCSSVariables(hexColor)
    saveThemeToStorage()
  }

  /**
   * 设置主题模式
   * 功能：切换明暗主题模式
   * 参数：mode - 'light' 或 'dark'
   * 返回值：无
   */
  const setThemeMode = (mode) => {
    themeMode.value = mode
    applyThemeModeToDocument(mode)
    saveThemeToStorage()
  }

  /**
   * 切换主题模式
   * 功能：在明暗主题间切换
   * 参数：无
   * 返回值：无
   */
  const toggleThemeMode = () => {
    const newMode = themeMode.value === 'light' ? 'dark' : 'light'
    setThemeMode(newMode)
  }

  /**
   * 应用预设主题
   * 功能：应用预设的主题方案，集成标准化主题管理
   * 参数：presetKey - 预设主题的key
   * 返回值：Promise<boolean> - 是否成功应用
   */
  const applyThemePreset = async (presetKey) => {
    try {
      // 使用标准化主题管理服务
      if (!themeService.value) {
        themeService.value = await getThemeManagementService()
      }

      const success = await themeService.value.applyThemePreset(presetKey)

      if (success) {
        const preset = themePresets.value.find((p) => p.key === presetKey)
        if (preset) {
          setPrimaryColor(preset.primaryColor)
        }
      }

      return success
    } catch (error) {
      console.error('应用主题预设失败:', error)
      // 降级到原有逻辑
      const preset = themePresets.value.find((p) => p.key === presetKey)
      if (preset) {
        setPrimaryColor(preset.primaryColor)
        return true
      }
      return false
    }
  }

  /**
   * 重置主题为默认
   * 功能：重置所有主题设置为默认值
   * 参数：无
   * 返回值：无
   */
  const resetTheme = () => {
    setPrimaryColor('#222222')
    setThemeMode('light')
  }

  /**
   * 初始化主题
   * 功能：应用当前主题色到CSS变量
   * 参数：无
   * 返回值：无
   */
  const initTheme = () => {
    applyThemeColorToCSSVariables(primaryColor.value)
    applyThemeModeToDocument(themeMode.value)
  }

  /**
   * 从本地存储加载主题
   * 功能：从localStorage恢复主题设置，集成标准化主题管理
   * 参数：无
   * 返回值：Promise<void>
   */
  const loadThemeFromStorage = async () => {
    try {
      // 初始化主题管理服务
      if (!themeService.value) {
        themeService.value = await getThemeManagementService()
      }

      // 加载标准化主题偏好
      const presetKey = themeService.value.loadThemePreference()
      if (presetKey) {
        await applyThemePreset(presetKey)
        return
      }

      // 降级到原有逻辑
      const savedTheme = localStorage.getItem('app-theme-settings')
      if (savedTheme) {
        const theme = JSON.parse(savedTheme)
        if (theme.primaryColor) {
          setPrimaryColor(theme.primaryColor)
        }
        if (theme.themeMode) {
          setThemeMode(theme.themeMode)
        }
      } else {
        // 本地存储为空时，应用默认主题设置
        console.log('本地存储为空，应用默认主题设置')
        initTheme()
      }
    } catch (error) {
      console.warn('加载主题设置失败:', error)
      // 发生错误时也应用默认主题
      initTheme()
    }
  }

  /**
   * 检查当前页面主题合规性
   * 功能：使用标准化检查工具验证主题合规性
   * 参数：target - 目标元素或选择器
   * 返回值：Promise<Object> - 合规性报告
   */
  const checkThemeCompliance = async (target = document.body) => {
    try {
      if (!themeService.value) {
        themeService.value = await getThemeManagementService()
      }

      return await themeService.value.checkCurrentPageCompliance(target)
    } catch (error) {
      console.error('主题合规性检查失败:', error)
      return {
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString(),
      }
    }
  }

  /**
   * 批量检查系统管理页面合规性
   * 功能：检查所有系统管理页面的主题合规性
   * 参数：无
   * 返回值：Promise<Object> - 批量检查结果
   */
  const checkSystemPagesCompliance = async () => {
    try {
      if (!themeService.value) {
        themeService.value = await getThemeManagementService()
      }

      return await themeService.value.checkSystemPagesCompliance()
    } catch (error) {
      console.error('系统页面合规性检查失败:', error)
      return {
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString(),
      }
    }
  }

  /**
   * 获取主题配置信息
   * 功能：获取完整的主题配置信息
   * 参数：无
   * 返回值：Promise<Object> - 主题配置
   */
  const getThemeConfiguration = async () => {
    try {
      if (!themeService.value) {
        themeService.value = await getThemeManagementService()
      }

      return themeService.value.getThemeConfiguration()
    } catch (error) {
      console.error('获取主题配置失败:', error)
      return null
    }
  }

  /**
   * 获取合规性摘要
   * 功能：获取主题合规性摘要信息
   * 参数：无
   * 返回值：Promise<Object> - 合规性摘要
   */
  const getComplianceSummary = async () => {
    try {
      if (!themeService.value) {
        themeService.value = await getThemeManagementService()
      }

      return themeService.value.generateComplianceSummary()
    } catch (error) {
      console.error('获取合规性摘要失败:', error)
      return {
        status: 'error',
        message: error.message,
      }
    }
  }

  /**
   * 保存主题到本地存储
   * 功能：将当前主题设置保存到localStorage
   * 参数：无
   * 返回值：无
   */
  const saveThemeToStorage = () => {
    try {
      const themeSettings = {
        primaryColor: primaryColor.value,
        themeMode: themeMode.value,
        timestamp: Date.now(),
      }
      localStorage.setItem('app-theme-settings', JSON.stringify(themeSettings))
    } catch (error) {
      console.warn('保存主题设置失败:', error)
    }
  }

  // 内部工具函数

  /**
   * 应用主题色到CSS变量
   * 功能：将主题色应用到CSS自定义属性
   * 参数：color - 十六进制颜色值
   * 返回值：无
   */
  const applyThemeColorToCSSVariables = (color) => {
    const root = document.documentElement
    const variants = {
      '--primary': color,
      '--primary-color': color,
      '--primary-color-hover': lightenColor(color, 10),
      '--primary-color-pressed': darkenColor(color, 10),
      '--primary-color-suppl': color,
      '--primary-color-light': lightenColor(color, 30),
      '--primary-color-lighter': lightenColor(color, 40),
      '--primary-color-dark': darkenColor(color, 20),
    }

    Object.entries(variants).forEach(([property, value]) => {
      root.style.setProperty(property, value)
    })
  }

  /**
   * 应用主题模式到文档
   * 功能：在document上添加/移除dark类名
   * 参数：mode - 'light' 或 'dark'
   * 返回值：无
   */
  const applyThemeModeToDocument = (mode) => {
    const html = document.documentElement
    if (mode === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  // 颜色工具函数

  /**
   * 颜色格式转换函数
   * 功能：将oklch、hsl、rgb等格式转换为十六进制格式
   * 参数：color - 任意格式的颜色值
   * 返回值：十六进制格式的颜色值
   */
  const convertColorToHex = (color) => {
    // 如果已经是十六进制格式，直接返回
    if (typeof color === 'string' && color.startsWith('#')) {
      return color
    }

    // 特殊处理 oklch(0.205 0 0) 这个有问题的颜色值
    if (typeof color === 'string' && color.includes('oklch(0.205 0 0)')) {
      return '#343434' // 返回对应的深灰色
    }

    // 处理其他 oklch 格式，直接转换为安全的颜色
    if (typeof color === 'string' && color.includes('oklch')) {
      console.warn('检测到 oklch 颜色格式，转换为默认颜色:', color)
      return '#1890ff' // 默认蓝色
    }

    // 处理hsl、rgb等格式
    if (typeof color === 'string' && (color.includes('hsl') || color.includes('rgb'))) {
      try {
        // 创建一个临时元素来转换颜色
        const tempElement = document.createElement('div')
        tempElement.style.color = color
        document.body.appendChild(tempElement)

        // 获取计算后的颜色值
        const computedColor = window.getComputedStyle(tempElement).color
        document.body.removeChild(tempElement)

        // 将rgb格式转换为十六进制
        if (computedColor.startsWith('rgb')) {
          const rgbMatch = computedColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/)
          if (rgbMatch) {
            const r = parseInt(rgbMatch[1])
            const g = parseInt(rgbMatch[2])
            const b = parseInt(rgbMatch[3])
            return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)
          }
        }
      } catch (error) {
        console.warn('颜色转换失败，使用默认颜色:', error)
        return '#1890ff' // 默认蓝色
      }
    }

    return color || '#1890ff'
  }

  /**
   * 颜色变亮
   * 功能：将颜色变亮指定百分比
   * 参数：color - 十六进制颜色值, percent - 变亮百分比
   * 返回值：变亮后的十六进制颜色值
   */
  const lightenColor = (color, percent) => {
    // 确保颜色是十六进制格式
    const hexColor = convertColorToHex(color)
    const num = parseInt(hexColor.replace('#', ''), 16)
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
   * 功能：将颜色变暗指定百分比
   * 参数：color - 十六进制颜色值, percent - 变暗百分比
   * 返回值：变暗后的十六进制颜色值
   */
  const darkenColor = (color, percent) => {
    // 确保颜色是十六进制格式
    const hexColor = convertColorToHex(color)
    const num = parseInt(hexColor.replace('#', ''), 16)
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

  return {
    // 状态
    primaryColor,
    themeMode,
    themeSwitcherEnabled,
    themePresets,
    themeService,

    // 计算属性
    isDarkMode,
    currentThemePreset,
    themeColorVariants,
    naiveThemeOverrides,

    // 基础方法
    setPrimaryColor,
    setThemeMode,
    toggleThemeMode,
    applyThemePreset,
    resetTheme,
    initTheme,
    loadThemeFromStorage,
    saveThemeToStorage,

    // 标准化主题管理方法
    checkThemeCompliance,
    checkSystemPagesCompliance,
    getThemeConfiguration,
    getComplianceSummary,

    // 工具函数
    lightenColor,
    darkenColor,
  }
})
