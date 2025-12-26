#!/usr/bin/env node

/**
 * 权限迁移脚本
 * 自动将现有组件中的普通按钮替换为权限按钮
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import {
  analyzeButtonsForPermission,
  generatePermissionButton,
} from '../src/utils/permission-migration.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// 配置
const CONFIG = {
  srcDir: path.join(__dirname, '../src'),
  backupDir: path.join(__dirname, '../backup'),
  dryRun: process.argv.includes('--dry-run'),
  verbose: process.argv.includes('--verbose'),
  force: process.argv.includes('--force'),
}

// 颜色输出
const colors = {
  reset: '\x1b[0m',
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

/**
 * 递归获取所有Vue文件
 * @param {string} dir - 目录路径
 * @returns {Array} Vue文件路径列表
 */
function getVueFiles(dir) {
  const files = []

  function traverse(currentDir) {
    const items = fs.readdirSync(currentDir)

    for (const item of items) {
      const fullPath = path.join(currentDir, item)
      const stat = fs.statSync(fullPath)

      if (stat.isDirectory()) {
        // 跳过node_modules等目录
        if (!['node_modules', '.git', 'dist', 'build'].includes(item)) {
          traverse(fullPath)
        }
      } else if (item.endsWith('.vue')) {
        files.push(fullPath)
      }
    }
  }

  traverse(dir)
  return files
}

/**
 * 创建备份
 * @param {string} filePath - 文件路径
 */
function createBackup(filePath) {
  if (CONFIG.dryRun) return

  const relativePath = path.relative(CONFIG.srcDir, filePath)
  const backupPath = path.join(CONFIG.backupDir, relativePath)
  const backupDir = path.dirname(backupPath)

  // 确保备份目录存在
  if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir, { recursive: true })
  }

  // 复制文件
  fs.copyFileSync(filePath, backupPath)

  if (CONFIG.verbose) {
    log(`备份文件: ${relativePath}`, 'blue')
  }
}

/**
 * 检查文件是否已经导入了PermissionButton
 * @param {string} content - 文件内容
 * @returns {boolean} 是否已导入
 */
function hasPermissionButtonImport(content) {
  return (
    content.includes('PermissionButton') || content.includes('@/components/common/PermissionButton')
  )
}

/**
 * 添加PermissionButton导入
 * @param {string} content - 文件内容
 * @returns {string} 修改后的内容
 */
function addPermissionButtonImport(content) {
  // 查找script标签
  const scriptMatch = content.match(/<script[^>]*>([\s\S]*?)<\/script>/)
  if (!scriptMatch) {
    log('警告: 未找到script标签', 'yellow')
    return content
  }

  const scriptContent = scriptMatch[1]

  // 查找import语句的位置
  const importRegex = /import\s+.*?from\s+['"][^'"]*['"]/g
  const imports = []
  let match

  while ((match = importRegex.exec(scriptContent)) !== null) {
    imports.push({
      statement: match[0],
      index: match.index,
    })
  }

  if (imports.length === 0) {
    // 没有import语句，在script开头添加
    const newImport = "import PermissionButton from '@/components/common/PermissionButton.vue'\n"
    return content.replace(
      scriptMatch[0],
      `<script${
        scriptMatch[0].match(/<script([^>]*?)>/)[1]
      }>\n${newImport}${scriptContent}</script>`
    )
  } else {
    // 在最后一个import语句后添加
    const lastImport = imports[imports.length - 1]
    const insertPosition = lastImport.index + lastImport.statement.length

    const newImport = "\nimport PermissionButton from '@/components/common/PermissionButton.vue'"
    const newScriptContent =
      scriptContent.slice(0, insertPosition) + newImport + scriptContent.slice(insertPosition)

    return content.replace(
      scriptMatch[0],
      `<script${scriptMatch[0].match(/<script([^>]*?)>/)[1]}>${newScriptContent}</script>`
    )
  }
}

/**
 * 处理单个Vue文件
 * @param {string} filePath - 文件路径
 * @returns {Object} 处理结果
 */
function processVueFile(filePath) {
  const relativePath = path.relative(CONFIG.srcDir, filePath)

  try {
    const content = fs.readFileSync(filePath, 'utf8')
    const buttons = analyzeButtonsForPermission(content, filePath)

    if (buttons.length === 0) {
      if (CONFIG.verbose) {
        log(`跳过: ${relativePath} (无需要权限控制的按钮)`, 'blue')
      }
      return { processed: false, buttonCount: 0 }
    }

    log(`处理: ${relativePath} (${buttons.length}个按钮)`, 'cyan')

    // 创建备份
    createBackup(filePath)

    let newContent = content
    let needsImport = !hasPermissionButtonImport(content)
    let offset = 0

    // 从后往前替换，避免位置偏移问题
    for (let i = buttons.length - 1; i >= 0; i--) {
      const button = buttons[i]
      const newButton = generatePermissionButton(
        button.permissionConfig,
        button.props,
        button.content
      )

      if (CONFIG.verbose) {
        log(`  替换按钮: "${button.text}" -> ${button.permissionConfig.type}权限`, 'green')
      }

      newContent =
        newContent.slice(0, button.startIndex) + newButton + newContent.slice(button.endIndex)
    }

    // 添加导入语句
    if (needsImport) {
      newContent = addPermissionButtonImport(newContent)
      if (CONFIG.verbose) {
        log(`  添加PermissionButton导入`, 'green')
      }
    }

    // 写入文件
    if (!CONFIG.dryRun) {
      fs.writeFileSync(filePath, newContent, 'utf8')
    }

    return {
      processed: true,
      buttonCount: buttons.length,
      addedImport: needsImport,
    }
  } catch (error) {
    log(`错误处理文件 ${relativePath}: ${error.message}`, 'red')
    return { processed: false, buttonCount: 0, error: error.message }
  }
}

/**
 * 主函数
 */
async function main() {
  log('🚀 开始权限迁移', 'cyan')
  log('='.repeat(50), 'cyan')

  if (CONFIG.dryRun) {
    log('⚠️  运行在预览模式，不会修改文件', 'yellow')
  }

  // 获取所有Vue文件
  const vueFiles = getVueFiles(CONFIG.srcDir)
  log(`找到 ${vueFiles.length} 个Vue文件`, 'blue')

  // 统计信息
  let processedFiles = 0
  let totalButtons = 0
  let addedImports = 0
  let errors = 0

  // 处理每个文件
  for (const filePath of vueFiles) {
    const result = processVueFile(filePath)

    if (result.processed) {
      processedFiles++
      totalButtons += result.buttonCount
      if (result.addedImport) addedImports++
    }

    if (result.error) {
      errors++
    }
  }

  // 输出统计结果
  log('\n' + '='.repeat(50), 'cyan')
  log('📊 迁移完成统计', 'cyan')
  log(`处理文件: ${processedFiles}/${vueFiles.length}`, 'green')
  log(`替换按钮: ${totalButtons}`, 'green')
  log(`添加导入: ${addedImports}`, 'green')

  if (errors > 0) {
    log(`错误数量: ${errors}`, 'red')
  }

  if (CONFIG.dryRun) {
    log('\n💡 使用 --force 参数执行实际修改', 'yellow')
  } else {
    log(`\n✅ 迁移完成！备份文件保存在: ${CONFIG.backupDir}`, 'green')
  }
}

// 显示帮助信息
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  log('权限迁移脚本', 'cyan')
  log('用法: node migrate-permissions.js [选项]', 'blue')
  log('\n选项:')
  log('  --dry-run    预览模式，不修改文件')
  log('  --verbose    显示详细信息')
  log('  --force      强制执行修改')
  log('  --help, -h   显示帮助信息')
  process.exit(0)
}

// 运行主函数
main().catch((error) => {
  log(`脚本执行失败: ${error.message}`, 'red')
  process.exit(1)
})
