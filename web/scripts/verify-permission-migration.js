#!/usr/bin/env node

/**
 * 权限迁移验证脚本
 * 验证已修改页面的权限控制实现
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const projectRoot = path.join(__dirname, '..')

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
}

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`)
}

// 已修改的页面列表
const modifiedPages = [
  {
    path: 'web/src/views/system/RoleManagementEnhanced.vue',
    expectedButtons: ['刷新', '保存', '新增角色'],
    expectedImport: true,
  },
  {
    path: 'web/src/views/ai-monitor/trend-prediction/index.vue',
    expectedButtons: ['开始预测', '刷新数据', '导出报告', '安排维护', '导出风险报告', '加入监控'],
    expectedImport: true,
  },
  {
    path: 'web/src/views/ai-monitor/data-annotation/index.vue',
    expectedButtons: ['新建项目', '导入数据', '刷新', '保存'],
    expectedImport: true,
  },
  {
    path: 'web/src/views/ai-monitor/smart-analysis/index.vue',
    expectedButtons: ['新建分析', '刷新'],
    expectedImport: true,
  },
  {
    path: 'web/src/views/ai-monitor/model-management/index.vue',
    expectedButtons: ['上传模型', '刷新'],
    expectedImport: true,
  },
  {
    path: 'web/src/views/ai-monitor/health-scoring/index.vue',
    expectedButtons: ['刷新数据', '导出报告', '评分配置'],
    expectedImport: true,
  },
  {
    path: 'web/src/views/alarm/alarm-info/index.vue',
    expectedButtons: ['查询', '重置'],
    expectedImport: true,
  },
  {
    path: 'web/src/views/dashboard/dashboard-weld/index.vue',
    expectedButtons: ['更多报警'],
    expectedImport: true,
  },
]

/**
 * 验证单个文件
 * @param {Object} pageInfo - 页面信息
 * @returns {Object} 验证结果
 */
function verifyPage(pageInfo) {
  const filePath = path.join(projectRoot, pageInfo.path.replace('web/', ''))

  if (!fs.existsSync(filePath)) {
    return {
      success: false,
      error: '文件不存在',
      details: {},
    }
  }

  const content = fs.readFileSync(filePath, 'utf8')
  const results = {
    success: true,
    details: {
      hasPermissionButtonImport: false,
      permissionButtonCount: 0,
      regularButtonCount: 0,
      foundButtons: [],
      missingButtons: [],
      issues: [],
    },
  }

  // 检查PermissionButton导入
  if (pageInfo.expectedImport) {
    const hasImport =
      content.includes('PermissionButton') &&
      content.includes('@/components/common/PermissionButton')
    results.details.hasPermissionButtonImport = hasImport

    if (!hasImport) {
      results.success = false
      results.details.issues.push('缺少PermissionButton导入')
    }
  }

  // 统计PermissionButton使用
  const permissionButtonMatches = content.match(/<PermissionButton/g)
  results.details.permissionButtonCount = permissionButtonMatches
    ? permissionButtonMatches.length
    : 0

  // 统计剩余的普通按钮
  const regularButtonMatches = content.match(/<n-button[^>]*@click/g)
  results.details.regularButtonCount = regularButtonMatches ? regularButtonMatches.length : 0

  // 检查预期的按钮是否都已转换
  for (const buttonText of pageInfo.expectedButtons) {
    const hasPermissionButton =
      content.includes(`>${buttonText}<`) && content.includes('<PermissionButton')

    if (hasPermissionButton) {
      results.details.foundButtons.push(buttonText)
    } else {
      results.details.missingButtons.push(buttonText)
      results.success = false
    }
  }

  // 检查是否还有未转换的业务按钮
  if (results.details.regularButtonCount > 0) {
    // 排除一些不需要权限控制的按钮（如取消、关闭等）
    const allowedRegularButtons = ['取消', '关闭', 'cancel', 'close']
    const hasBusinessButtons = regularButtonMatches?.some((match) => {
      return !allowedRegularButtons.some((allowed) =>
        content
          .substring(content.indexOf(match), content.indexOf(match) + 200)
          .toLowerCase()
          .includes(allowed.toLowerCase())
      )
    })

    if (hasBusinessButtons) {
      results.details.issues.push(`发现${results.details.regularButtonCount}个未转换的业务按钮`)
    }
  }

  return results
}

/**
 * 主验证函数
 */
function runVerification() {
  log('🔍 开始验证权限迁移结果', 'cyan')
  log('='.repeat(60), 'cyan')

  let totalPages = modifiedPages.length
  let successPages = 0
  let totalIssues = 0

  for (const pageInfo of modifiedPages) {
    const relativePath = pageInfo.path.replace('web/', '')
    log(`\n📄 验证: ${relativePath}`, 'blue')

    const result = verifyPage(pageInfo)

    if (result.success) {
      log(`✅ 验证通过`, 'green')
      successPages++
    } else {
      log(`❌ 验证失败`, 'red')
      if (result.error) {
        log(`   错误: ${result.error}`, 'red')
      }
    }

    // 显示详细信息
    const details = result.details
    if (details) {
      log(`   PermissionButton导入: ${details.hasPermissionButtonImport ? '✅' : '❌'}`)
      log(`   PermissionButton数量: ${details.permissionButtonCount}`)
      log(`   剩余普通按钮: ${details.regularButtonCount}`)

      if (details.foundButtons.length > 0) {
        log(`   已转换按钮: ${details.foundButtons.join(', ')}`, 'green')
      }

      if (details.missingButtons.length > 0) {
        log(`   未转换按钮: ${details.missingButtons.join(', ')}`, 'red')
        totalIssues += details.missingButtons.length
      }

      if (details.issues.length > 0) {
        details.issues.forEach((issue) => {
          log(`   ⚠️  ${issue}`, 'yellow')
          totalIssues++
        })
      }
    }
  }

  // 输出总结
  log('\n' + '='.repeat(60), 'cyan')
  log('📊 验证结果总结', 'cyan')
  log(`页面验证: ${successPages}/${totalPages}`, successPages === totalPages ? 'green' : 'yellow')
  log(`发现问题: ${totalIssues}`, totalIssues === 0 ? 'green' : 'red')

  if (successPages === totalPages && totalIssues === 0) {
    log('\n🎉 所有页面都已正确完成权限迁移！', 'green')
    log('✨ 权限控制系统已准备就绪', 'green')
  } else {
    log('\n⚠️  发现问题，建议检查并修复', 'yellow')

    if (totalIssues > 0) {
      log('\n🔧 修复建议:', 'blue')
      log('1. 确保所有业务按钮都使用PermissionButton组件', 'white')
      log('2. 检查PermissionButton的导入语句', 'white')
      log('3. 验证权限配置是否正确', 'white')
      log('4. 运行测试确保功能正常', 'white')
    }
  }

  return successPages === totalPages && totalIssues === 0
}

/**
 * 生成迁移状态报告
 */
function generateReport() {
  log('\n📋 生成详细报告...', 'blue')

  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalPages: modifiedPages.length,
      successPages: 0,
      totalButtons: 0,
      convertedButtons: 0,
      issues: [],
    },
    pages: [],
  }

  for (const pageInfo of modifiedPages) {
    const result = verifyPage(pageInfo)
    const pageReport = {
      path: pageInfo.path,
      success: result.success,
      details: result.details,
      error: result.error,
    }

    if (result.success) {
      report.summary.successPages++
    }

    if (result.details) {
      report.summary.totalButtons +=
        result.details.permissionButtonCount + result.details.regularButtonCount
      report.summary.convertedButtons += result.details.permissionButtonCount

      if (result.details.issues.length > 0) {
        report.summary.issues.push(
          ...result.details.issues.map((issue) => ({
            page: pageInfo.path,
            issue,
          }))
        )
      }
    }

    report.pages.push(pageReport)
  }

  // 保存报告
  const reportPath = path.join(projectRoot, 'permission-migration-verification.json')
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2))

  log(`📄 详细报告已保存到: ${reportPath}`, 'green')

  return report
}

// 处理命令行参数
const args = process.argv.slice(2)

if (args.includes('--help') || args.includes('-h')) {
  log('权限迁移验证脚本', 'cyan')
  log('用法: node verify-permission-migration.js [选项]', 'blue')
  log('\n选项:')
  log('  --report       生成详细的JSON报告')
  log('  --help, -h     显示帮助信息')
  process.exit(0)
}

// 运行验证
const success = runVerification()

if (args.includes('--report')) {
  generateReport()
}

process.exit(success ? 0 : 1)
