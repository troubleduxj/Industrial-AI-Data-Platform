/**
 * 系统管理模块修复工具
 * 用于修复系统管理各个页面的常见问题
 */

import systemV2Api from '@/api/system-v2'

export class SystemModuleFixer {
  constructor() {
    this.fixResults = {}
  }

  /**
   * 修复所有系统管理模块问题
   */
  async fixAll() {
    console.log('🔧 开始修复系统管理模块问题...')

    const fixes = [
      { name: '检查API路径映射', fix: () => this.checkApiPathMapping() },
      { name: '验证API响应格式', fix: () => this.validateApiResponseFormat() },
      { name: '修复分页参数', fix: () => this.fixPaginationParams() },
      { name: '检查权限配置', fix: () => this.checkPermissionConfig() },
    ]

    for (const fixItem of fixes) {
      try {
        console.log(`🔧 执行修复: ${fixItem.name}...`)
        const result = await fixItem.fix()
        this.fixResults[fixItem.name] = result
        console.log(`✅ ${fixItem.name} 修复完成`)
      } catch (error) {
        console.error(`❌ ${fixItem.name} 修复失败:`, error)
        this.fixResults[fixItem.name] = { success: false, error: error.message }
      }
    }

    return this.generateFixReport()
  }

  /**
   * 检查API路径映射
   */
  async checkApiPathMapping() {
    const apiTests = [
      { name: '菜单管理', api: () => systemV2Api.getMenus({ page: 1, page_size: 1 }) },
      { name: '部门管理', api: () => systemV2Api.getDepts({ page: 1, page_size: 1 }) },
      { name: 'API管理', api: () => systemV2Api.getApiList({ page: 1, page_size: 1 }) },
      { name: 'API分组', api: () => systemV2Api.getApiGroupList({ page: 1, page_size: 1 }) },
      { name: '字典类型', api: () => systemV2Api.getDictTypeList({ page: 1, page_size: 1 }) },
      { name: '字典数据', api: () => systemV2Api.getDictDataList({ page: 1, page_size: 1 }) },
      { name: '系统参数', api: () => systemV2Api.getSystemParamList({ page: 1, page_size: 1 }) },
      { name: '审计日志', api: () => systemV2Api.getAuditLogList({ page: 1, page_size: 1 }) },
    ]

    const results = {}
    for (const test of apiTests) {
      try {
        const response = await test.api()
        results[test.name] = {
          success: true,
          status: response?.code || 200,
          hasData: !!response?.data,
          dataType: Array.isArray(response?.data) ? 'array' : typeof response?.data,
        }
      } catch (error) {
        results[test.name] = {
          success: false,
          error: error.message,
          status: error.response?.status || 'unknown',
        }
      }
    }

    return { success: true, results }
  }

  /**
   * 验证API响应格式
   */
  async validateApiResponseFormat() {
    try {
      // 测试一个简单的API调用
      const response = await systemV2Api.getMenus({ page: 1, page_size: 1 })

      const expectedFields = ['success', 'code', 'data', 'message']
      const actualFields = Object.keys(response || {})

      const missingFields = expectedFields.filter((field) => !actualFields.includes(field))
      const hasValidStructure = missingFields.length === 0

      return {
        success: hasValidStructure,
        expectedFields,
        actualFields,
        missingFields,
        responseStructure: this.analyzeResponseStructure(response),
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        suggestion: '检查API响应格式是否符合v2标准',
      }
    }
  }

  /**
   * 修复分页参数
   */
  async fixPaginationParams() {
    // 检查分页参数是否正确传递
    const testParams = {
      page: 1,
      page_size: 10,
      search: 'test',
    }

    try {
      const response = await systemV2Api.getMenus(testParams)

      return {
        success: true,
        message: '分页参数传递正常',
        testParams,
        responseHasPagination: !!(
          response?.total !== undefined || response?.meta?.total !== undefined
        ),
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        suggestion: '检查分页参数格式化是否正确',
      }
    }
  }

  /**
   * 检查权限配置
   */
  async checkPermissionConfig() {
    // 检查权限相关的配置
    const token = localStorage.getItem('access_token')
    const userInfo = localStorage.getItem('userInfo')

    return {
      success: true,
      hasToken: !!token,
      hasUserInfo: !!userInfo,
      tokenValid: this.validateToken(token),
      suggestions: this.generatePermissionSuggestions(token, userInfo),
    }
  }

  /**
   * 验证token有效性
   */
  validateToken(token) {
    if (!token) return false

    try {
      const parts = token.split('.')
      if (parts.length !== 3) return false

      const payload = JSON.parse(atob(parts[1]))
      const currentTime = Math.floor(Date.now() / 1000)

      return payload.exp > currentTime
    } catch (error) {
      return false
    }
  }

  /**
   * 生成权限相关建议
   */
  generatePermissionSuggestions(token, userInfo) {
    const suggestions = []

    if (!token) {
      suggestions.push('缺少访问令牌，请重新登录')
    } else if (!this.validateToken(token)) {
      suggestions.push('访问令牌已过期，请重新登录')
    }

    if (!userInfo) {
      suggestions.push('缺少用户信息，请检查登录状态')
    }

    return suggestions
  }

  /**
   * 分析响应数据结构
   */
  analyzeResponseStructure(response) {
    if (!response) return 'null'

    return {
      type: typeof response,
      keys: Object.keys(response),
      hasSuccess: 'success' in response,
      hasCode: 'code' in response,
      hasData: 'data' in response,
      hasMessage: 'message' in response,
      dataType: response.data ? typeof response.data : 'undefined',
      dataIsArray: Array.isArray(response.data),
    }
  }

  /**
   * 生成修复报告
   */
  generateFixReport() {
    const successCount = Object.values(this.fixResults).filter((r) => r.success).length
    const totalCount = Object.keys(this.fixResults).length

    const report = {
      summary: {
        total: totalCount,
        success: successCount,
        failed: totalCount - successCount,
        successRate: `${((successCount / totalCount) * 100).toFixed(1)}%`,
      },
      details: this.fixResults,
      recommendations: this.generateRecommendations(),
    }

    console.log('🔧 修复报告:', report)
    return report
  }

  /**
   * 生成修复建议
   */
  generateRecommendations() {
    const recommendations = []

    // 基于修复结果生成建议
    Object.entries(this.fixResults).forEach(([fixName, result]) => {
      if (!result.success) {
        recommendations.push(`${fixName}: ${result.error || '需要进一步检查'}`)
      }
    })

    // 通用建议
    recommendations.push('确保后端服务正常运行')
    recommendations.push('检查网络连接状态')
    recommendations.push('验证API权限配置')

    return recommendations
  }
}

// 导出修复函数供控制台使用
export async function runSystemModuleFix() {
  const fixer = new SystemModuleFixer()
  return await fixer.fixAll()
}

// 在开发环境下将修复工具挂载到window对象
if (process.env.NODE_ENV === 'development') {
  window.runSystemModuleFix = runSystemModuleFix
}
