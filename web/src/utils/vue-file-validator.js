/**
 * Vue文件完整性检查工具
 * 检查Vue单文件组件是否包含必需的template或script标签
 */

/**
 * 检查Vue文件内容是否有效
 * @param {string} content - Vue文件内容
 * @param {string} filePath - 文件路径（用于错误报告）
 * @returns {Object} 验证结果
 */
export function validateVueFileContent(content, filePath = '') {
  try {
    // 检查是否包含template或script标签
    const hasTemplate = /<template[^>]*>/.test(content)
    const hasScript = /<script[^>]*>/.test(content)

    if (!hasTemplate && !hasScript) {
      return {
        valid: false,
        error: 'Missing both <template> and <script> tags',
        filePath,
      }
    }

    // 检查标签是否正确闭合
    if (hasTemplate) {
      const templateMatches = content.match(/<template[^>]*>/g)
      const templateCloseMatches = content.match(/<\/template>/g)
      if (!templateCloseMatches || templateMatches.length !== templateCloseMatches.length) {
        return {
          valid: false,
          error: 'Unclosed <template> tag',
          filePath,
        }
      }
    }

    if (hasScript) {
      const scriptMatches = content.match(/<script[^>]*>/g)
      const scriptCloseMatches = content.match(/<\/script>/g)
      if (!scriptCloseMatches || scriptMatches.length !== scriptCloseMatches.length) {
        return {
          valid: false,
          error: 'Unclosed <script> tag',
          filePath,
        }
      }
    }

    // 检查是否有语法错误的标签
    const malformedTags = content.match(/<[^>]*[^\/]>(?![^<]*<\/)/g)
    if (malformedTags) {
      // 进一步检查是否是真正的语法错误
      const suspiciousTags = malformedTags.filter(
        (tag) =>
          !tag.includes('/>') &&
          !['<br>', '<hr>', '<img', '<input', '<meta', '<link'].some((selfClosing) =>
            tag.startsWith(selfClosing)
          )
      )

      if (suspiciousTags.length > 0) {
        return {
          valid: false,
          error: `Potentially malformed tags found: ${suspiciousTags.slice(0, 3).join(', ')}`,
          filePath,
        }
      }
    }

    return {
      valid: true,
      filePath,
      hasTemplate,
      hasScript,
      hasStyle: /<style[^>]*>/.test(content),
    }
  } catch (error) {
    return {
      valid: false,
      error: `Validation error: ${error.message}`,
      filePath,
    }
  }
}

/**
 * 批量验证Vue文件内容
 * @param {Array} files - 文件对象数组 [{path: string, content: string}]
 * @returns {Object} 验证结果汇总
 */
export function validateMultipleVueFiles(files) {
  const results = files.map((file) => validateVueFileContent(file.content, file.path))

  const invalidFiles = results.filter((r) => !r.valid)

  return {
    total: results.length,
    valid: results.filter((r) => r.valid).length,
    invalid: invalidFiles.length,
    invalidFiles,
    results,
  }
}

/**
 * 生成Vue文件验证报告
 * @param {Object} validationResult - 验证结果
 * @returns {string} 格式化的报告
 */
export function generateValidationReport(validationResult) {
  const { total, valid, invalid, invalidFiles } = validationResult

  let report = `Vue文件验证报告\n`
  report += `==================\n`
  report += `总文件数: ${total}\n`
  report += `有效文件: ${valid}\n`
  report += `无效文件: ${invalid}\n`
  report += `成功率: ${((valid / total) * 100).toFixed(1)}%\n\n`

  if (invalid > 0) {
    report += `无效文件详情:\n`
    invalidFiles.forEach((file, index) => {
      report += `${index + 1}. ${file.filePath}\n`
      report += `   错误: ${file.error}\n\n`
    })
  } else {
    report += `✅ 所有Vue文件都是有效的！\n`
  }

  return report
}

/**
 * 检查Vue组件的基本结构
 * @param {string} content - Vue文件内容
 * @returns {Object} 结构分析结果
 */
export function analyzeVueStructure(content) {
  const structure = {
    hasTemplate: /<template[^>]*>/.test(content),
    hasScript: /<script[^>]*>/.test(content),
    hasStyle: /<style[^>]*>/.test(content),
    scriptSetup: /<script[^>]*setup[^>]*>/.test(content),
    typescript: /<script[^>]*lang=[\"']ts[\"'][^>]*>/.test(content),
    scoped: /<style[^>]*scoped[^>]*>/.test(content),
    preprocessor: null,
  }

  // 检查CSS预处理器
  const styleMatch = content.match(/<style[^>]*lang=[\"']([^\"']+)[\"'][^>]*>/)
  if (styleMatch) {
    structure.preprocessor = styleMatch[1]
  }

  // 检查组件名称
  const nameMatch = content.match(/name:\s*[\"']([^\"']+)[\"']/)
  if (nameMatch) {
    structure.componentName = nameMatch[1]
  }

  return structure
}

/**
 * 修复常见的Vue文件问题
 * @param {string} content - Vue文件内容
 * @returns {Object} 修复结果
 */
export function fixCommonVueIssues(content) {
  let fixedContent = content
  const fixes = []

  // 修复未闭合的自闭合标签
  const selfClosingTags = ['br', 'hr', 'img', 'input', 'meta', 'link']
  selfClosingTags.forEach((tag) => {
    const regex = new RegExp(`<${tag}([^>]*[^/])>`, 'gi')
    if (regex.test(fixedContent)) {
      fixedContent = fixedContent.replace(regex, `<${tag}$1 />`)
      fixes.push(`Fixed self-closing <${tag}> tags`)
    }
  })

  // 修复多余的空白行
  const originalLines = fixedContent.split('\n').length
  fixedContent = fixedContent.replace(/\n\s*\n\s*\n/g, '\n\n')
  const newLines = fixedContent.split('\n').length
  if (originalLines !== newLines) {
    fixes.push(`Removed ${originalLines - newLines} excessive blank lines`)
  }

  return {
    content: fixedContent,
    fixes,
    hasChanges: fixes.length > 0,
  }
}

export default {
  validateVueFileContent,
  validateMultipleVueFiles,
  generateValidationReport,
  analyzeVueStructure,
  fixCommonVueIssues,
}
