/**
 * 主题系统测试工具
 * 用于验证主题管理标准化基础设施的功能
 */

import { getThemeManagementService } from '@/services/theme-management-service.js'
import { createThemeChecker } from '@/utils/theme-compliance-checker.js'
import { getGlobalThemeMapper } from '@/utils/theme-variable-mapper.js'
import { THEME_PRESETS } from '@/config/theme-config.js'

/**
 * 主题系统测试类
 */
export class ThemeSystemTest {
  constructor() {
    this.results = []
    this.service = null
    this.checker = null
    this.mapper = null
  }

  /**
   * 运行所有测试
   * @returns {Promise<Object>} 测试结果
   */
  async runAllTests() {
    console.log('🧪 开始主题系统测试...')

    this.results = []

    try {
      // 初始化服务
      await this.initializeServices()

      // 运行各项测试
      await this.testThemeMapper()
      await this.testComplianceChecker()
      await this.testThemeService()
      await this.testThemePresets()
      await this.testCSSVariables()

      const summary = this.generateTestSummary()
      console.log('✅ 主题系统测试完成', summary)

      return summary
    } catch (error) {
      console.error('❌ 主题系统测试失败:', error)
      return {
        success: false,
        error: error.message,
        results: this.results,
      }
    }
  }

  /**
   * 初始化服务
   */
  async initializeServices() {
    this.addTest('服务初始化', '初始化主题管理服务')

    try {
      this.service = await getThemeManagementService()
      this.checker = createThemeChecker()
      this.mapper = getGlobalThemeMapper()

      this.passTest('服务初始化', '所有服务初始化成功')
    } catch (error) {
      this.failTest('服务初始化', error.message)
      throw error
    }
  }

  /**
   * 测试主题映射器
   */
  async testThemeMapper() {
    this.addTest('主题映射器', '测试主题变量映射功能')

    try {
      // 测试变量应用
      const appliedVariables = this.mapper.getAppliedVariables()
      if (appliedVariables.size === 0) {
        throw new Error('未找到已应用的CSS变量')
      }

      // 测试变量映射验证
      const validation = this.mapper.validateMapping()
      if (!validation.valid && validation.missing.length > 10) {
        console.warn('部分CSS变量未映射:', validation.missing.slice(0, 5))
      }

      // 测试主题预设应用
      const testPreset = 'violet'
      const success = this.mapper.applyThemePreset(testPreset)
      if (!success) {
        throw new Error(`无法应用测试主题预设: ${testPreset}`)
      }

      // 恢复默认主题
      this.mapper.applyThemePreset('default')

      this.passTest('主题映射器', `成功应用 ${appliedVariables.size} 个CSS变量`)
    } catch (error) {
      this.failTest('主题映射器', error.message)
    }
  }

  /**
   * 测试合规性检查器
   */
  async testComplianceChecker() {
    this.addTest('合规性检查器', '测试主题合规性检查功能')

    try {
      // 创建测试元素
      const testElement = this.createTestElement()
      document.body.appendChild(testElement)

      // 运行合规性检查
      const report = this.checker.checkPageCompliance(testElement)

      if (!report || typeof report !== 'object') {
        throw new Error('合规性检查未返回有效报告')
      }

      if (!report.timestamp || !report.status) {
        throw new Error('合规性报告格式不正确')
      }

      // 清理测试元素
      document.body.removeChild(testElement)

      this.passTest(
        '合规性检查器',
        `检查完成，状态: ${report.status}，违规: ${report.summary?.totalViolations || 0}`
      )
    } catch (error) {
      this.failTest('合规性检查器', error.message)
    }
  }

  /**
   * 测试主题管理服务
   */
  async testThemeService() {
    this.addTest('主题管理服务', '测试主题管理服务功能')

    try {
      // 测试配置获取
      const config = this.service.getThemeConfiguration()
      if (!config || !config.presets) {
        throw new Error('无法获取主题配置')
      }

      // 测试合规性检查
      const report = await this.service.checkCurrentPageCompliance()
      if (!report) {
        throw new Error('服务合规性检查失败')
      }

      // 测试摘要生成
      const summary = this.service.generateComplianceSummary()
      if (!summary) {
        throw new Error('无法生成合规性摘要')
      }

      this.passTest('主题管理服务', '所有服务功能正常')
    } catch (error) {
      this.failTest('主题管理服务', error.message)
    }
  }

  /**
   * 测试主题预设
   */
  async testThemePresets() {
    this.addTest('主题预设', '测试所有主题预设应用')

    try {
      let successCount = 0
      const totalPresets = THEME_PRESETS.length

      for (const preset of THEME_PRESETS) {
        try {
          const success = await this.service.applyThemePreset(preset.key)
          if (success) {
            successCount++
          }

          // 短暂延迟以避免过快切换
          await new Promise((resolve) => setTimeout(resolve, 100))
        } catch (error) {
          console.warn(`主题预设 ${preset.key} 应用失败:`, error.message)
        }
      }

      // 恢复默认主题
      await this.service.applyThemePreset('default')

      if (successCount === totalPresets) {
        this.passTest('主题预设', `所有 ${totalPresets} 个主题预设应用成功`)
      } else {
        this.failTest('主题预设', `仅 ${successCount}/${totalPresets} 个主题预设应用成功`)
      }
    } catch (error) {
      this.failTest('主题预设', error.message)
    }
  }

  /**
   * 测试CSS变量
   */
  async testCSSVariables() {
    this.addTest('CSS变量', '测试CSS变量定义和访问')

    try {
      const testVariables = [
        '--primary-color',
        '--text-color-primary',
        '--background-color-base',
        '--border-color-light',
        '--spacing-md',
        '--font-size-base',
      ]

      let validCount = 0
      const root = document.documentElement

      for (const variable of testVariables) {
        const value = getComputedStyle(root).getPropertyValue(variable)
        if (value && value.trim()) {
          validCount++
        } else {
          console.warn(`CSS变量 ${variable} 未定义或为空`)
        }
      }

      if (validCount === testVariables.length) {
        this.passTest('CSS变量', `所有 ${testVariables.length} 个测试变量定义正确`)
      } else {
        this.failTest('CSS变量', `仅 ${validCount}/${testVariables.length} 个变量定义正确`)
      }
    } catch (error) {
      this.failTest('CSS变量', error.message)
    }
  }

  /**
   * 创建测试元素
   * @returns {HTMLElement} 测试元素
   */
  createTestElement() {
    const element = document.createElement('div')
    element.className = 'theme-test-element'
    element.style.cssText = `
      position: fixed;
      top: -1000px;
      left: -1000px;
      width: 100px;
      height: 100px;
      background: var(--background-color-base);
      color: var(--text-color-primary);
      border: 1px solid var(--border-color-light);
      padding: var(--spacing-md);
    `

    // 添加一些子元素
    const button = document.createElement('button')
    button.className = 'standard-button'
    button.textContent = '测试按钮'
    element.appendChild(button)

    const table = document.createElement('div')
    table.className = 'standard-table'
    element.appendChild(table)

    return element
  }

  /**
   * 添加测试项
   * @param {string} name - 测试名称
   * @param {string} description - 测试描述
   */
  addTest(name, description) {
    this.results.push({
      name,
      description,
      status: 'running',
      startTime: Date.now(),
    })
  }

  /**
   * 标记测试通过
   * @param {string} name - 测试名称
   * @param {string} message - 成功消息
   */
  passTest(name, message) {
    const test = this.results.find((t) => t.name === name)
    if (test) {
      test.status = 'passed'
      test.message = message
      test.endTime = Date.now()
      test.duration = test.endTime - test.startTime
    }
  }

  /**
   * 标记测试失败
   * @param {string} name - 测试名称
   * @param {string} error - 错误消息
   */
  failTest(name, error) {
    const test = this.results.find((t) => t.name === name)
    if (test) {
      test.status = 'failed'
      test.error = error
      test.endTime = Date.now()
      test.duration = test.endTime - test.startTime
    }
  }

  /**
   * 生成测试摘要
   * @returns {Object} 测试摘要
   */
  generateTestSummary() {
    const passed = this.results.filter((r) => r.status === 'passed').length
    const failed = this.results.filter((r) => r.status === 'failed').length
    const total = this.results.length

    return {
      success: failed === 0,
      total,
      passed,
      failed,
      passRate: total > 0 ? ((passed / total) * 100).toFixed(2) : 0,
      totalDuration: this.results.reduce((sum, r) => sum + (r.duration || 0), 0),
      results: this.results,
      timestamp: new Date().toISOString(),
    }
  }
}

/**
 * 快速运行主题系统测试
 * @returns {Promise<Object>} 测试结果
 */
export async function runThemeSystemTest() {
  const test = new ThemeSystemTest()
  return await test.runAllTests()
}

/**
 * 在控制台运行测试
 */
export function runTestInConsole() {
  console.log('🚀 在控制台运行主题系统测试...')

  runThemeSystemTest()
    .then((result) => {
      console.log('📊 测试结果:', result)

      if (result.success) {
        console.log(`✅ 所有测试通过! (${result.passed}/${result.total})`)
      } else {
        console.log(`❌ 测试失败! (${result.passed}/${result.total} 通过)`)

        result.results
          .filter((r) => r.status === 'failed')
          .forEach((test) => {
            console.error(`  ❌ ${test.name}: ${test.error}`)
          })
      }
    })
    .catch((error) => {
      console.error('💥 测试执行失败:', error)
    })
}

// 在开发环境下自动暴露到全局
if (import.meta.env.DEV) {
  window.runThemeSystemTest = runThemeSystemTest
  window.runTestInConsole = runTestInConsole

  console.log('🔧 主题系统测试工具已加载')
  console.log('  - 运行 runThemeSystemTest() 获取详细结果')
  console.log('  - 运行 runTestInConsole() 在控制台查看结果')
}

export default {
  ThemeSystemTest,
  runThemeSystemTest,
  runTestInConsole,
}
