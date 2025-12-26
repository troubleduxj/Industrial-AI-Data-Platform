/**
 * 主题管理服务
 * 统一管理主题配置、合规性检查和变量映射
 */

import { createThemeChecker } from '@/utils/theme-compliance-checker.js'
import { getGlobalThemeMapper, initializeThemeSystem } from '@/utils/theme-variable-mapper.js'
import { THEME_PRESETS, DESIGN_TOKENS } from '@/config/theme-config.js'

/**
 * 主题管理服务类
 */
export class ThemeManagementService {
  constructor() {
    this.mapper = null
    this.checker = null
    this.initialized = false
    this.complianceReports = new Map()
    this.listeners = new Set()
  }

  /**
   * 初始化主题管理服务
   */
  async initialize() {
    if (this.initialized) {
      return this
    }

    try {
      // 初始化主题映射器
      this.mapper = initializeThemeSystem()

      // 初始化合规性检查器
      this.checker = createThemeChecker()

      // 设置事件监听
      this.setupEventListeners()

      this.initialized = true
      console.log('主题管理服务已初始化')

      // 触发初始化完成事件
      this.notifyListeners('initialized', { service: this })
    } catch (error) {
      console.error('主题管理服务初始化失败:', error)
      throw error
    }

    return this
  }

  /**
   * 设置事件监听器
   */
  setupEventListeners() {
    // 监听主题变化
    document.addEventListener('themeChanged', (event) => {
      this.handleThemeChange(event.detail)
    })

    // 监听页面变化
    if (typeof window !== 'undefined' && window.addEventListener) {
      window.addEventListener('popstate', () => {
        this.scheduleComplianceCheck()
      })
    }
  }

  /**
   * 处理主题变化
   * @param {Object} themeData - 主题数据
   */
  handleThemeChange(themeData) {
    console.log('主题变化:', themeData)

    // 重新检查合规性
    this.scheduleComplianceCheck()

    // 通知监听器
    this.notifyListeners('themeChanged', themeData)
  }

  /**
   * 安排合规性检查
   */
  scheduleComplianceCheck() {
    // 防抖处理
    if (this.complianceCheckTimeout) {
      clearTimeout(this.complianceCheckTimeout)
    }

    this.complianceCheckTimeout = setTimeout(() => {
      this.checkCurrentPageCompliance()
    }, 500)
  }

  /**
   * 应用主题预设
   * @param {string} presetKey - 预设键名
   * @returns {Promise<boolean>} 是否成功应用
   */
  async applyThemePreset(presetKey) {
    if (!this.initialized) {
      await this.initialize()
    }

    try {
      const success = this.mapper.applyThemePreset(presetKey)

      if (success) {
        // 触发主题变化事件
        const preset = THEME_PRESETS.find((p) => p.key === presetKey)
        document.dispatchEvent(
          new CustomEvent('themeChanged', {
            detail: { preset, presetKey },
          })
        )

        // 保存到本地存储
        this.saveThemePreference(presetKey)

        console.log(`主题预设 ${presetKey} 应用成功`)
      }

      return success
    } catch (error) {
      console.error('应用主题预设失败:', error)
      return false
    }
  }

  /**
   * 检查当前页面合规性
   * @param {Element|string} target - 目标元素
   * @returns {Promise<Object>} 合规性报告
   */
  async checkCurrentPageCompliance(target = document.body) {
    if (!this.initialized) {
      await this.initialize()
    }

    try {
      const report = this.checker.checkPageCompliance(target)
      const pageId = this.getCurrentPageId()

      // 缓存报告
      this.complianceReports.set(pageId, {
        ...report,
        pageId,
        url: window.location.href,
      })

      // 通知监听器
      this.notifyListeners('complianceChecked', { pageId, report })

      return report
    } catch (error) {
      console.error('合规性检查失败:', error)
      return {
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString(),
      }
    }
  }

  /**
   * 批量检查系统管理页面合规性
   * @returns {Promise<Object>} 批量检查结果
   */
  async checkSystemPagesCompliance() {
    if (!this.initialized) {
      await this.initialize()
    }

    const systemPages = [
      { selector: '.system-user-page', name: '用户管理' },
      { selector: '.system-role-page', name: '角色管理' },
      { selector: '.system-menu-page', name: '菜单管理' },
      { selector: '.system-dept-page', name: '部门管理' },
      { selector: '.system-api-page', name: 'API管理' },
      { selector: '.system-dict-page', name: '字典管理' },
    ]

    const results = {}
    let totalViolations = 0
    let compliantPages = 0

    for (const page of systemPages) {
      const element = document.querySelector(page.selector)
      if (element) {
        const report = await this.checkCurrentPageCompliance(element)
        results[page.name] = {
          ...report,
          selector: page.selector,
          found: true,
        }

        totalViolations += report.summary?.totalViolations || 0
        if (report.status === 'compliant') {
          compliantPages++
        }
      } else {
        results[page.name] = {
          status: 'not-found',
          selector: page.selector,
          found: false,
          message: '页面元素未找到',
        }
      }
    }

    const batchResult = {
      timestamp: new Date().toISOString(),
      totalPages: systemPages.length,
      foundPages: Object.values(results).filter((r) => r.found).length,
      compliantPages,
      totalViolations,
      overallCompliance: compliantPages === Object.values(results).filter((r) => r.found).length,
      results,
    }

    // 缓存批量结果
    this.complianceReports.set('batch-system-pages', batchResult)

    // 通知监听器
    this.notifyListeners('batchComplianceChecked', batchResult)

    return batchResult
  }

  /**
   * 获取主题配置信息
   * @returns {Object} 主题配置
   */
  getThemeConfiguration() {
    if (!this.initialized) {
      return null
    }

    return {
      presets: THEME_PRESETS,
      tokens: DESIGN_TOKENS,
      currentPreset: this.mapper.getCurrentPreset(),
      appliedVariables: Object.fromEntries(this.mapper.getAppliedVariables()),
      isDarkMode: document.documentElement.classList.contains('dark'),
    }
  }

  /**
   * 获取合规性报告
   * @param {string} pageId - 页面ID
   * @returns {Object|null} 合规性报告
   */
  getComplianceReport(pageId = null) {
    if (pageId) {
      return this.complianceReports.get(pageId) || null
    }

    // 返回当前页面的报告
    const currentPageId = this.getCurrentPageId()
    return this.complianceReports.get(currentPageId) || null
  }

  /**
   * 获取所有合规性报告
   * @returns {Object} 所有报告
   */
  getAllComplianceReports() {
    return Object.fromEntries(this.complianceReports)
  }

  /**
   * 生成主题合规性摘要
   * @returns {Object} 合规性摘要
   */
  generateComplianceSummary() {
    const reports = Array.from(this.complianceReports.values())

    if (reports.length === 0) {
      return {
        status: 'no-data',
        message: '暂无合规性检查数据',
      }
    }

    const summary = {
      totalReports: reports.length,
      compliantPages: reports.filter((r) => r.status === 'compliant').length,
      nonCompliantPages: reports.filter((r) => r.status === 'non-compliant').length,
      errorPages: reports.filter((r) => r.status === 'error').length,
      totalViolations: reports.reduce((sum, r) => sum + (r.summary?.totalViolations || 0), 0),
      violationsByType: {},
      violationsBySeverity: {
        high: 0,
        medium: 0,
        low: 0,
      },
      lastChecked: Math.max(...reports.map((r) => new Date(r.timestamp).getTime())),
      overallCompliance: 0,
    }

    // 统计违规类型
    reports.forEach((report) => {
      if (report.violations) {
        report.violations.forEach((violation) => {
          // 按类型统计
          if (!summary.violationsByType[violation.type]) {
            summary.violationsByType[violation.type] = 0
          }
          summary.violationsByType[violation.type]++

          // 按严重程度统计
          if (summary.violationsBySeverity[violation.severity] !== undefined) {
            summary.violationsBySeverity[violation.severity]++
          }
        })
      }
    })

    // 计算总体合规率
    summary.overallCompliance =
      summary.totalReports > 0
        ? ((summary.compliantPages / summary.totalReports) * 100).toFixed(2)
        : 0

    return summary
  }

  /**
   * 修复主题违规问题
   * @param {string} pageId - 页面ID
   * @param {Array} violationIds - 要修复的违规ID列表
   * @returns {Promise<Object>} 修复结果
   */
  async fixThemeViolations(pageId, violationIds = []) {
    const report = this.getComplianceReport(pageId)
    if (!report || !report.violations) {
      return {
        success: false,
        message: '未找到违规报告',
      }
    }

    const fixResults = []
    const violationsToFix =
      violationIds.length > 0
        ? report.violations.filter((v) => violationIds.includes(v.id))
        : report.violations

    for (const violation of violationsToFix) {
      try {
        const result = await this.fixSingleViolation(violation)
        fixResults.push(result)
      } catch (error) {
        fixResults.push({
          violationId: violation.id,
          success: false,
          error: error.message,
        })
      }
    }

    // 重新检查合规性
    await this.checkCurrentPageCompliance()

    return {
      success: true,
      fixedCount: fixResults.filter((r) => r.success).length,
      totalCount: fixResults.length,
      results: fixResults,
    }
  }

  /**
   * 修复单个违规问题
   * @param {Object} violation - 违规信息
   * @returns {Promise<Object>} 修复结果
   */
  async fixSingleViolation(violation) {
    switch (violation.type) {
      case 'hardcoded-color':
        return this.fixHardcodedColor(violation)
      case 'missing-css-class':
        return this.fixMissingCSSClass(violation)
      case 'inline-theme-style':
        return this.fixInlineThemeStyle(violation)
      default:
        return {
          violationId: violation.id,
          success: false,
          message: `不支持自动修复违规类型: ${violation.type}`,
        }
    }
  }

  /**
   * 修复硬编码颜色
   * @param {Object} violation - 违规信息
   * @returns {Object} 修复结果
   */
  fixHardcodedColor(violation) {
    // 这里可以实现自动替换硬编码颜色为CSS变量的逻辑
    // 由于涉及DOM操作的复杂性，这里返回建议
    return {
      violationId: violation.id,
      success: false,
      message: '硬编码颜色需要手动修复',
      suggestion: `将 ${violation.value} 替换为相应的CSS变量`,
    }
  }

  /**
   * 修复缺失的CSS类
   * @param {Object} violation - 违规信息
   * @returns {Object} 修复结果
   */
  fixMissingCSSClass(violation) {
    try {
      const element = document.querySelector(violation.element)
      if (element) {
        element.classList.add(violation.className)
        return {
          violationId: violation.id,
          success: true,
          message: `已添加CSS类: ${violation.className}`,
        }
      }
    } catch (error) {
      // 处理错误
    }

    return {
      violationId: violation.id,
      success: false,
      message: '无法自动添加CSS类',
    }
  }

  /**
   * 修复内联主题样式
   * @param {Object} violation - 违规信息
   * @returns {Object} 修复结果
   */
  fixInlineThemeStyle(violation) {
    // 内联样式修复需要更复杂的逻辑
    return {
      violationId: violation.id,
      success: false,
      message: '内联样式需要手动修复',
      suggestion: '将内联样式移至CSS类中并使用CSS变量',
    }
  }

  /**
   * 保存主题偏好设置
   * @param {string} presetKey - 预设键名
   */
  saveThemePreference(presetKey) {
    try {
      localStorage.setItem(
        'theme-management-preference',
        JSON.stringify({
          presetKey,
          timestamp: Date.now(),
        })
      )
    } catch (error) {
      console.warn('保存主题偏好失败:', error)
    }
  }

  /**
   * 加载主题偏好设置
   * @returns {string|null} 预设键名
   */
  loadThemePreference() {
    try {
      const saved = localStorage.getItem('theme-management-preference')
      if (saved) {
        const { presetKey } = JSON.parse(saved)
        return presetKey
      }
    } catch (error) {
      console.warn('加载主题偏好失败:', error)
    }
    return null
  }

  /**
   * 获取当前页面ID
   * @returns {string} 页面ID
   */
  getCurrentPageId() {
    return window.location.pathname.replace(/\//g, '-') || 'root'
  }

  /**
   * 添加事件监听器
   * @param {Function} listener - 监听器函数
   */
  addListener(listener) {
    this.listeners.add(listener)
  }

  /**
   * 移除事件监听器
   * @param {Function} listener - 监听器函数
   */
  removeListener(listener) {
    this.listeners.delete(listener)
  }

  /**
   * 通知所有监听器
   * @param {string} event - 事件名称
   * @param {any} data - 事件数据
   */
  notifyListeners(event, data) {
    this.listeners.forEach((listener) => {
      try {
        listener(event, data)
      } catch (error) {
        console.error('监听器执行失败:', error)
      }
    })
  }

  /**
   * 销毁服务
   */
  destroy() {
    if (this.complianceCheckTimeout) {
      clearTimeout(this.complianceCheckTimeout)
    }

    this.listeners.clear()
    this.complianceReports.clear()
    this.initialized = false
  }
}

/**
 * 全局主题管理服务实例
 */
let globalThemeService = null

/**
 * 获取全局主题管理服务
 * @returns {Promise<ThemeManagementService>}
 */
export async function getThemeManagementService() {
  if (!globalThemeService) {
    globalThemeService = new ThemeManagementService()
    await globalThemeService.initialize()
  }
  return globalThemeService
}

/**
 * 快速应用主题预设
 * @param {string} presetKey - 预设键名
 * @returns {Promise<boolean>}
 */
export async function applyTheme(presetKey) {
  const service = await getThemeManagementService()
  return service.applyThemePreset(presetKey)
}

/**
 * 快速检查页面合规性
 * @param {Element|string} target - 目标元素
 * @returns {Promise<Object>}
 */
export async function checkThemeCompliance(target) {
  const service = await getThemeManagementService()
  return service.checkCurrentPageCompliance(target)
}

/**
 * 获取主题配置
 * @returns {Promise<Object>}
 */
export async function getThemeConfig() {
  const service = await getThemeManagementService()
  return service.getThemeConfiguration()
}

export default {
  ThemeManagementService,
  getThemeManagementService,
  applyTheme,
  checkThemeCompliance,
  getThemeConfig,
}
