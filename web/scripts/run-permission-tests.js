#!/usr/bin/env node

/**
 * 权限测试执行脚本
 * 按阶段执行权限相关的测试
 */

import { spawn } from 'child_process'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = join(__dirname, '..')

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
}

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`)
}

function runCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    log(`\n${colors.bright}执行命令: ${command} ${args.join(' ')}${colors.reset}`, 'cyan')

    const child = spawn(command, args, {
      cwd: projectRoot,
      stdio: 'inherit',
      shell: true,
      ...options,
    })

    child.on('close', (code) => {
      if (code === 0) {
        resolve(code)
      } else {
        reject(new Error(`命令执行失败，退出码: ${code}`))
      }
    })

    child.on('error', (error) => {
      reject(error)
    })
  })
}

// 测试阶段配置
const testPhases = {
  unit: {
    name: '单元测试阶段',
    description: '测试权限组件和工具函数',
    tests: [
      {
        name: 'PermissionButton组件测试',
        command: 'npx',
        args: ['vitest', 'run', 'tests/components/PermissionButton.test.js'],
      },
      {
        name: 'usePermission组合函数测试',
        command: 'npx',
        args: ['vitest', 'run', 'tests/composables/usePermission.test.js'],
      },
    ],
  },

  integration: {
    name: '集成测试阶段',
    description: '测试权限系统的集成功能',
    tests: [
      {
        name: '权限系统集成测试',
        command: 'npx',
        args: ['vitest', 'run', 'tests/integration/permission-system.test.js'],
      },
    ],
  },

  e2e: {
    name: '端到端测试阶段',
    description: '测试完整的用户权限流程',
    tests: [
      {
        name: '权限按钮端到端测试',
        command: 'npx',
        args: ['playwright', 'test', 'tests/e2e/permission-button.spec.js'],
      },
      {
        name: '权限系统完整测试',
        command: 'npx',
        args: ['playwright', 'test', 'tests/e2e/permission-system-complete.spec.js'],
      },
    ],
  },

  manual: {
    name: '手动测试阶段',
    description: '需要手动执行的测试项目',
    tests: [
      {
        name: '用户权限验证',
        type: 'manual',
        steps: [
          '1. 使用不同权限的用户登录系统',
          '2. 验证各页面按钮的显示/隐藏状态',
          '3. 测试按钮点击后的权限验证',
          '4. 验证权限不足时的错误提示',
        ],
      },
      {
        name: '权限动态更新测试',
        type: 'manual',
        steps: [
          '1. 登录普通用户账号',
          '2. 在后台修改用户权限',
          '3. 验证前端权限状态是否实时更新',
          '4. 测试新权限是否立即生效',
        ],
      },
      {
        name: '性能测试',
        type: 'manual',
        steps: [
          '1. 使用浏览器开发者工具监控性能',
          '2. 测试权限检查对页面加载时间的影响',
          '3. 验证大量权限按钮的渲染性能',
          '4. 检查内存使用情况',
        ],
      },
    ],
  },
}

async function runTestPhase(phaseName) {
  const phase = testPhases[phaseName]
  if (!phase) {
    log(`未找到测试阶段: ${phaseName}`, 'red')
    return false
  }

  log(`\n🚀 开始执行: ${phase.name}`, 'cyan')
  log(`📝 ${phase.description}`, 'blue')
  log('='.repeat(60), 'cyan')

  let passedTests = 0
  let totalTests = phase.tests.length

  for (const test of phase.tests) {
    try {
      log(`\n📋 ${test.name}`, 'yellow')

      if (test.type === 'manual') {
        log('📖 手动测试步骤:', 'blue')
        test.steps.forEach((step) => {
          log(`   ${step}`, 'white')
        })
        log('⚠️  请手动执行上述步骤并验证结果', 'yellow')
        passedTests++
      } else {
        await runCommand(test.command, test.args)
        log(`✅ ${test.name} 通过`, 'green')
        passedTests++
      }
    } catch (error) {
      log(`❌ ${test.name} 失败: ${error.message}`, 'red')
    }
  }

  // 输出阶段结果
  log('\n' + '-'.repeat(60), 'cyan')
  log(
    `📊 ${phase.name} 结果: ${passedTests}/${totalTests}`,
    passedTests === totalTests ? 'green' : 'yellow'
  )

  return passedTests === totalTests
}

async function runAllTests() {
  log('🎯 权限测试执行计划', 'bright')
  log('='.repeat(60), 'cyan')

  const phases = ['unit', 'integration', 'e2e', 'manual']
  let totalPassed = 0
  let totalPhases = phases.length

  for (const phase of phases) {
    const success = await runTestPhase(phase)
    if (success) totalPassed++
  }

  // 最终结果
  log('\n' + '='.repeat(60), 'cyan')
  log('🏁 测试执行完成', 'bright')
  log(
    `总体结果: ${totalPassed}/${totalPhases} 个阶段通过`,
    totalPassed === totalPhases ? 'green' : 'yellow'
  )

  if (totalPassed === totalPhases) {
    log('🎉 所有测试阶段都通过了！', 'green')
    log('✨ 权限系统已准备就绪', 'green')
  } else {
    log('⚠️  部分测试阶段失败，请检查上面的错误信息', 'red')
    log('🔧 建议修复问题后重新运行测试', 'yellow')
  }
}

// 处理命令行参数
const args = process.argv.slice(2)

if (args.includes('--help') || args.includes('-h')) {
  log('权限测试执行脚本', 'bright')
  log('用法: node run-permission-tests.js [选项]', 'cyan')
  log('\n选项:')
  log('  --unit         只运行单元测试')
  log('  --integration  只运行集成测试')
  log('  --e2e          只运行端到端测试')
  log('  --manual       显示手动测试步骤')
  log('  --all          运行所有测试阶段（默认）')
  log('  --help, -h     显示帮助信息')
  log('\n测试阶段说明:')
  Object.entries(testPhases).forEach(([key, phase]) => {
    log(`  ${key.padEnd(12)} ${phase.description}`, 'blue')
  })
  process.exit(0)
}

// 执行指定的测试阶段
if (args.includes('--unit')) {
  runTestPhase('unit')
} else if (args.includes('--integration')) {
  runTestPhase('integration')
} else if (args.includes('--e2e')) {
  runTestPhase('e2e')
} else if (args.includes('--manual')) {
  runTestPhase('manual')
} else {
  runAllTests()
}
