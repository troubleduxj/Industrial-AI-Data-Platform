/**
 * 系统管理主题组合式函数
 * 提供系统管理页面的主题切换和标准化功能
 */

import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useThemeStore } from '@/store/theme.js'
import { getSystemThemeService } from '@/services/system-theme-service.js'
import {
  applySystemThemeStandardization,
  checkSystemThemeCompliance,
} from '@/utils/theme-system-standardizer.js'

/**
 * 系统管理主题组合式函数
 * @param {Object} options - 配置选项
 * @returns {Object} 主题相关的响应式数据和方法
 */
export function useSystemTheme(options = {}) {
  const {
    autoApply = true,
    enableCompliance = true,
    pageSelector = '.system-management-page',
  } = options

  // 响应式状态
  const currentTheme = ref('default')
  const isLoading = ref(false)
  const isApplied = ref(false)
  const complianceStatus = ref(null)
  const availableThemes = ref([])
  const themeService = ref(null)

  // Store 实例
  const themeStore = useThemeStore()

  // 计算属性
  const themeInfo = computed(() => {
    if (!themeService.value) return null
    return themeService.value.getCurrentTheme()
  })

  const isCompliant = computed(() => {
    return complianceStatus.value?.compliant === true
  })

  const complianceIssues = computed(() => {
    return complianceStatus.value?.issues || []
  })

  // 初始化主题服务
  const initializeTheme = async () => {
    try {
      isLoading.value = true

      if (!themeService.value) {
        themeService.value = getSystemThemeService()
      }

      await themeService.value.initialize()

      // 获取可用主题列表
      availableThemes.value = themeService.value.getAvailableThemes()

      // 获取当前主题
      const current = themeService.value.getCurrentTheme()
      currentTheme.value = current.key

      // 自动应用主题标准化
      if (autoApply) {
        await applyThemeStandardization()
      }

      // 检查合规性
      if (enableCompliance) {
        await checkCompliance()
      }

      isApplied.value = true
    } catch (error) {
      console.error('初始化系统主题失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  // 切换主题
  const switchTheme = async (themeKey) => {
    try {
      isLoading.value = true

      if (!themeService.value) {
        await initializeTheme()
      }

      const success = await themeService.value.switchTheme(themeKey)

      if (success) {
        currentTheme.value = themeKey

        // 重新应用标准化
        if (autoApply) {
          await applyThemeStandardization()
        }

        // 重新检查合规性
        if (enableCompliance) {
          await checkCompliance()
        }

        return true
      }

      return false
    } catch (error) {
      console.error('切换主题失败:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 应用主题标准化
  const applyThemeStandardization = async (selector = pageSelector) => {
    try {
      const success = await applySystemThemeStandardization(selector)

      if (success) {
        console.log('主题标准化应用成功')
      }

      return success
    } catch (error) {
      console.error('应用主题标准化失败:', error)
      return false
    }
  }

  // 检查主题合规性
  const checkCompliance = async (element = document.body) => {
    try {
      const result = checkSystemThemeCompliance(element)
      complianceStatus.value = result

      if (!result.compliant) {
        console.warn('主题合规性检查发现问题:', result.issues)
      }

      return result
    } catch (error) {
      console.error('主题合规性检查失败:', error)
      return { compliant: false, issues: [], error: error.message }
    }
  }

  // 预览主题
  const previewTheme = async (themeKey) => {
    if (!themeService.value) {
      await initializeTheme()
    }

    return await themeService.value.previewTheme(themeKey)
  }

  // 重置主题
  const resetTheme = async () => {
    return await switchTheme('default')
  }

  // 获取主题配置
  const getThemeConfig = () => {
    if (!themeService.value) return null
    return themeService.value.getCurrentTheme()
  }

  // 保存主题设置
  const saveThemeSettings = () => {
    if (themeService.value) {
      themeService.value.saveThemeSettings()
    }
    themeStore.saveThemeToStorage()
  }

  // 监听主题变更
  const onThemeChange = (callback) => {
    if (!themeService.value) return () => {}
    return themeService.value.onThemeChange(callback)
  }

  // 手动触发合规性检查
  const triggerComplianceCheck = async () => {
    return await checkCompliance()
  }

  // 修复合规性问题
  const fixComplianceIssues = async () => {
    try {
      // 重新应用标准化
      await applyThemeStandardization()

      // 重新检查
      await checkCompliance()

      return complianceStatus.value?.compliant === true
    } catch (error) {
      console.error('修复合规性问题失败:', error)
      return false
    }
  }

  // 获取主题统计信息
  const getThemeStats = () => {
    return {
      currentTheme: currentTheme.value,
      totalThemes: availableThemes.value.length,
      isApplied: isApplied.value,
      isCompliant: isCompliant.value,
      issueCount: complianceIssues.value.length,
      lastChecked: complianceStatus.value?.timestamp,
    }
  }

  // 监听主题 store 变化
  watch(
    () => themeStore.primaryColor,
    async (newColor) => {
      if (autoApply && isApplied.value) {
        await applyThemeStandardization()
      }
    }
  )

  // 监听主题模式变化
  watch(
    () => themeStore.themeMode,
    async (newMode) => {
      if (autoApply && isApplied.value) {
        await applyThemeStandardization()
      }
    }
  )

  // 生命周期钩子
  onMounted(async () => {
    await initializeTheme()
  })

  let themeChangeUnsubscribe = null
  onMounted(() => {
    // 监听全局主题变更事件
    themeChangeUnsubscribe = onThemeChange((detail) => {
      console.log('系统主题已变更:', detail)
    })
  })

  onUnmounted(() => {
    if (themeChangeUnsubscribe) {
      themeChangeUnsubscribe()
    }
  })

  return {
    // 响应式状态
    currentTheme,
    isLoading,
    isApplied,
    complianceStatus,
    availableThemes,
    themeInfo,
    isCompliant,
    complianceIssues,

    // 方法
    initializeTheme,
    switchTheme,
    applyThemeStandardization,
    checkCompliance,
    previewTheme,
    resetTheme,
    getThemeConfig,
    saveThemeSettings,
    onThemeChange,
    triggerComplianceCheck,
    fixComplianceIssues,
    getThemeStats,

    // Store 引用
    themeStore,
  }
}

/**
 * 系统管理页面主题组合式函数
 * 专门为系统管理页面优化的版本
 * @param {string} pageName - 页面名称
 * @returns {Object}
 */
export function useSystemPageTheme(pageName) {
  const pageSelector = `.system-${pageName}-page`

  const theme = useSystemTheme({
    autoApply: true,
    enableCompliance: true,
    pageSelector,
  })

  // 页面特定的主题应用
  const applyPageTheme = async () => {
    return await theme.applyThemeStandardization(pageSelector)
  }

  // 页面特定的合规性检查
  const checkPageCompliance = async () => {
    const pageElement = document.querySelector(pageSelector)
    if (pageElement) {
      return await theme.checkCompliance(pageElement)
    }
    return { compliant: false, issues: [{ type: 'page-not-found', message: '页面元素未找到' }] }
  }

  return {
    ...theme,
    pageName,
    pageSelector,
    applyPageTheme,
    checkPageCompliance,
  }
}

/**
 * 批量系统页面主题管理
 * @param {Array} pageNames - 页面名称数组
 * @returns {Object}
 */
export function useBatchSystemTheme(pageNames = []) {
  const themes = ref({})
  const batchStatus = ref({
    applied: 0,
    total: pageNames.length,
    compliant: 0,
    issues: [],
  })

  // 初始化所有页面主题
  const initializeAllPages = async () => {
    for (const pageName of pageNames) {
      themes.value[pageName] = useSystemPageTheme(pageName)
      await themes.value[pageName].initializeTheme()
    }

    updateBatchStatus()
  }

  // 批量应用主题
  const applyBatchTheme = async (themeKey) => {
    const results = []

    for (const pageName of pageNames) {
      if (themes.value[pageName]) {
        const success = await themes.value[pageName].switchTheme(themeKey)
        results.push({ pageName, success })
      }
    }

    updateBatchStatus()
    return results
  }

  // 批量检查合规性
  const checkBatchCompliance = async () => {
    const results = []

    for (const pageName of pageNames) {
      if (themes.value[pageName]) {
        const compliance = await themes.value[pageName].checkPageCompliance()
        results.push({ pageName, compliance })
      }
    }

    updateBatchStatus()
    return results
  }

  // 更新批量状态
  const updateBatchStatus = () => {
    let applied = 0
    let compliant = 0
    const issues = []

    Object.values(themes.value).forEach((theme) => {
      if (theme.isApplied) applied++
      if (theme.isCompliant) compliant++
      issues.push(...theme.complianceIssues)
    })

    batchStatus.value = {
      applied,
      total: pageNames.length,
      compliant,
      issues,
    }
  }

  return {
    themes,
    batchStatus,
    initializeAllPages,
    applyBatchTheme,
    checkBatchCompliance,
    updateBatchStatus,
  }
}

// 导出默认配置
export default {
  useSystemTheme,
  useSystemPageTheme,
  useBatchSystemTheme,
}
