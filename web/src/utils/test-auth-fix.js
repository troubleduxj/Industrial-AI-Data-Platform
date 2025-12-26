/**
 * 认证修复方案验证测试脚本
 *
 * 用于验证增强版认证管理工具的有效性
 *
 * @author DeviceMonitorV2 Team
 * @date 2025-01-11
 */

import {
  setTokenEnhanced,
  getTokenEnhanced,
  diagnoseAuthState,
  checkTokenExpiration,
  clearAuthStateEnhanced,
  exportDiagnosticReport,
} from './auth-enhanced'

/**
 * 测试用的模拟JWT Token
 */
const MOCK_TOKEN =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InRlc3RfdXNlciIsInVzZXJfaWQiOjEsImV4cCI6MTc1NzU4NjAwMCwiaWF0IjoxNzU3NTgyNDAwfQ.test_signature'

const MOCK_USER_INFO = {
  id: 1,
  username: 'test_user',
  email: 'test@example.com',
  roles: ['admin'],
}

/**
 * 测试结果收集器
 */
class TestCollector {
  constructor() {
    this.tests = []
    this.passed = 0
    this.failed = 0
  }

  /**
   * 添加测试结果
   */
  addTest(name, passed, message = '', details = null) {
    const test = {
      name,
      passed,
      message,
      details,
      timestamp: new Date().toISOString(),
    }
    this.tests.push(test)

    if (passed) {
      this.passed++
      console.log(`✅ ${name}: ${message}`)
    } else {
      this.failed++
      console.error(`❌ ${name}: ${message}`, details)
    }
  }

  /**
   * 生成测试报告
   */
  generateReport() {
    const report = {
      summary: {
        total: this.tests.length,
        passed: this.passed,
        failed: this.failed,
        successRate:
          this.tests.length > 0 ? ((this.passed / this.tests.length) * 100).toFixed(2) + '%' : '0%',
      },
      tests: this.tests,
      timestamp: new Date().toISOString(),
    }

    console.log('📊 测试报告', report)
    return report
  }
}

/**
 * 测试Token设置功能
 */
function testTokenSetting(collector) {
  console.log('\n🧪 测试Token设置功能...')

  try {
    // 清除现有状态
    clearAuthStateEnhanced()

    // 测试设置Token
    const result = setTokenEnhanced(MOCK_TOKEN, MOCK_USER_INFO)
    collector.addTest('Token设置', result === true, result ? '成功设置Token' : '设置Token失败')

    // 验证Token是否正确保存
    const savedToken = localStorage.getItem('access_token')
    collector.addTest(
      'Token保存验证',
      savedToken === MOCK_TOKEN,
      savedToken === MOCK_TOKEN
        ? 'Token正确保存到localStorage'
        : `保存的Token不匹配: ${savedToken?.substring(0, 20)}...`
    )

    // 验证用户信息是否正确保存
    const savedUserInfo = localStorage.getItem('userInfo')
    const parsedUserInfo = savedUserInfo ? JSON.parse(savedUserInfo) : null
    collector.addTest(
      '用户信息保存验证',
      parsedUserInfo && parsedUserInfo.username === MOCK_USER_INFO.username,
      parsedUserInfo ? '用户信息正确保存' : '用户信息保存失败'
    )

    // 验证调试信息是否正确保存
    const debugInfo = localStorage.getItem('auth_debug')
    collector.addTest(
      '调试信息保存验证',
      !!debugInfo,
      debugInfo ? '调试信息已保存' : '调试信息保存失败'
    )
  } catch (error) {
    collector.addTest('Token设置异常处理', false, '设置过程中发生异常', error)
  }
}

/**
 * 测试Token获取功能
 */
function testTokenGetting(collector) {
  console.log('\n🧪 测试Token获取功能...')

  try {
    // 测试获取Token
    const token = getTokenEnhanced()
    collector.addTest(
      'Token获取',
      token === MOCK_TOKEN,
      token === MOCK_TOKEN ? '成功获取Token' : `获取的Token不匹配: ${token?.substring(0, 20)}...`
    )

    // 测试空Token情况
    localStorage.removeItem('access_token')
    const emptyToken = getTokenEnhanced()
    collector.addTest(
      '空Token处理',
      emptyToken === null,
      emptyToken === null ? '正确处理空Token情况' : '空Token处理异常'
    )

    // 恢复Token用于后续测试
    localStorage.setItem('access_token', MOCK_TOKEN)
  } catch (error) {
    collector.addTest('Token获取异常处理', false, '获取过程中发生异常', error)
  }
}

/**
 * 测试诊断功能
 */
function testDiagnostics(collector) {
  console.log('\n🧪 测试诊断功能...')

  try {
    // 测试认证状态诊断
    const diagnosis = diagnoseAuthState()

    collector.addTest(
      '诊断功能基本运行',
      typeof diagnosis === 'object' && diagnosis !== null,
      '诊断功能正常运行'
    )

    collector.addTest(
      '诊断Token检测',
      diagnosis.hasToken === true,
      diagnosis.hasToken ? '正确检测到Token存在' : '未能检测到Token'
    )

    collector.addTest(
      '诊断Token格式验证',
      diagnosis.tokenValid === true,
      diagnosis.tokenValid ? 'Token格式验证通过' : 'Token格式验证失败'
    )

    // 测试过期检查
    const expiration = checkTokenExpiration()
    collector.addTest(
      '过期检查功能',
      typeof expiration === 'object' && expiration.hasToken === true,
      '过期检查功能正常运行'
    )

    // 测试诊断报告导出
    const report = exportDiagnosticReport()
    collector.addTest(
      '诊断报告导出',
      typeof report === 'string' && report.length > 0,
      '诊断报告导出成功'
    )
  } catch (error) {
    collector.addTest('诊断功能异常处理', false, '诊断过程中发生异常', error)
  }
}

/**
 * 测试清除功能
 */
function testClearFunction(collector) {
  console.log('\n🧪 测试清除功能...')

  try {
    // 确保有数据可清除
    setTokenEnhanced(MOCK_TOKEN, MOCK_USER_INFO)

    // 测试清除功能
    const beforeState = clearAuthStateEnhanced()

    collector.addTest(
      '清除功能返回状态',
      typeof beforeState === 'object' && beforeState.hasToken === true,
      '清除功能正确返回清除前状态'
    )

    // 验证数据是否被清除
    const afterToken = localStorage.getItem('access_token')
    const afterUserInfo = localStorage.getItem('userInfo')
    const afterDebugInfo = localStorage.getItem('auth_debug')

    collector.addTest(
      'Token清除验证',
      afterToken === null,
      afterToken === null ? 'Token已成功清除' : 'Token清除失败'
    )

    collector.addTest(
      '用户信息清除验证',
      afterUserInfo === null,
      afterUserInfo === null ? '用户信息已成功清除' : '用户信息清除失败'
    )

    collector.addTest(
      '调试信息清除验证',
      afterDebugInfo === null,
      afterDebugInfo === null ? '调试信息已成功清除' : '调试信息清除失败'
    )
  } catch (error) {
    collector.addTest('清除功能异常处理', false, '清除过程中发生异常', error)
  }
}

/**
 * 运行完整的测试套件
 */
export function runAuthFixTests() {
  console.log('🚀 开始运行认证修复方案验证测试...')
  console.log('测试时间:', new Date().toISOString())

  const collector = new TestCollector()

  // 运行各项测试
  testTokenSetting(collector)
  testTokenGetting(collector)
  testDiagnostics(collector)
  testClearFunction(collector)

  // 生成最终报告
  console.log('\n📊 测试完成，生成报告...')
  const report = collector.generateReport()

  // 输出总结
  console.log(`\n🎯 测试总结:`)
  console.log(`   总计: ${report.summary.total} 项测试`)
  console.log(`   通过: ${report.summary.passed} 项`)
  console.log(`   失败: ${report.summary.failed} 项`)
  console.log(`   成功率: ${report.summary.successRate}`)

  if (report.summary.failed === 0) {
    console.log('\n🎉 所有测试通过！认证修复方案验证成功！')
  } else {
    console.log('\n⚠️ 部分测试失败，请检查失败的测试项目。')
  }

  return report
}

/**
 * 在开发环境下自动挂载测试函数
 */
if (process.env.NODE_ENV === 'development') {
  window.runAuthFixTests = runAuthFixTests
  console.log('🔧 开发模式：认证测试工具已挂载到window.runAuthFixTests()')
}

export default {
  runAuthFixTests,
  testTokenSetting,
  testTokenGetting,
  testDiagnostics,
  testClearFunction,
}
