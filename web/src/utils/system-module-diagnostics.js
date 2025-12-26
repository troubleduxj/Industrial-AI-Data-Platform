/**
 * 系统管理模块诊断工具
 * 用于检测系统管理各个页面的API调用和数据加载问题
 */

import systemV2Api from '@/api/system-v2'

export class SystemModuleDiagnostics {
  constructor() {
    this.results = {}
    this.errors = []
  }

  /**
   * 诊断所有系统管理模块的API
   */
  async diagnoseAll() {
    console.log('🔍 开始系统管理模块诊断...')

    const modules = [
      { name: '菜单管理', test: () => this.testMenuApi() },
      { name: '部门管理', test: () => this.testDeptApi() },
      { name: 'API管理', test: () => this.testApiManagement() },
      { name: 'API分组管理', test: () => this.testApiGroupsApi() },
      { name: '字典类型管理', test: () => this.testDictTypeApi() },
      { name: '字典数据管理', test: () => this.testDictDataApi() },
      { name: '系统参数管理', test: () => this.testSystemParamApi() },
      { name: '审计日志', test: () => this.testAuditLogApi() },
    ]

    for (const module of modules) {
      try {
        console.log(`📋 测试 ${module.name}...`)
        const result = await module.test()
        this.results[module.name] = result
        console.log(`✅ ${module.name} 测试完成:`, result.success ? '成功' : '失败')
      } catch (error) {
        console.error(`❌ ${module.name} 测试失败:`, error)
        this.results[module.name] = { success: false, error: error.message }
        this.errors.push({ module: module.name, error })
      }
    }

    return this.generateReport()
  }

  /**
   * 测试菜单管理API
   */
  async testMenuApi() {
    try {
      const response = await systemV2Api.getMenus({ page: 1, page_size: 10 })
      return {
        success: true,
        apiPath: '/api/v2/menus',
        responseStructure: this.analyzeResponseStructure(response),
        dataCount: Array.isArray(response?.data) ? response.data.length : 0,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        apiPath: '/api/v2/menus',
      }
    }
  }

  /**
   * 测试部门管理API
   */
  async testDeptApi() {
    try {
      const response = await systemV2Api.getDepts({ page: 1, page_size: 10 })
      return {
        success: true,
        apiPath: '/api/v2/departments',
        responseStructure: this.analyzeResponseStructure(response),
        dataCount: Array.isArray(response?.data) ? response.data.length : 0,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        apiPath: '/api/v2/departments',
      }
    }
  }

  /**
   * 测试API管理
   */
  async testApiManagement() {
    try {
      const response = await systemV2Api.getApiList({ page: 1, page_size: 10 })
      return {
        success: true,
        apiPath: '/api/v2/apis',
        responseStructure: this.analyzeResponseStructure(response),
        dataCount: Array.isArray(response?.data) ? response.data.length : 0,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        apiPath: '/api/v2/apis',
      }
    }
  }

  /**
   * 测试API分组管理
   */
  async testApiGroupsApi() {
    try {
      const response = await systemV2Api.getApiGroupList({ page: 1, page_size: 10 })
      return {
        success: true,
        apiPath: '/api/v2/api-groups',
        responseStructure: this.analyzeResponseStructure(response),
        dataCount: Array.isArray(response?.data) ? response.data.length : 0,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        apiPath: '/api/v2/api-groups',
      }
    }
  }

  /**
   * 测试字典类型管理API
   */
  async testDictTypeApi() {
    try {
      const response = await systemV2Api.getDictTypeList({ page: 1, page_size: 10 })
      return {
        success: true,
        apiPath: '/api/v2/dict-types',
        responseStructure: this.analyzeResponseStructure(response),
        dataCount: Array.isArray(response?.data) ? response.data.length : 0,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        apiPath: '/api/v2/dict-types',
      }
    }
  }

  /**
   * 测试字典数据管理API
   */
  async testDictDataApi() {
    try {
      const response = await systemV2Api.getDictDataList({ page: 1, page_size: 10 })
      return {
        success: true,
        apiPath: '/api/v2/dict-data',
        responseStructure: this.analyzeResponseStructure(response),
        dataCount: Array.isArray(response?.data) ? response.data.length : 0,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        apiPath: '/api/v2/dict-data',
      }
    }
  }

  /**
   * 测试系统参数管理API
   */
  async testSystemParamApi() {
    try {
      const response = await systemV2Api.getSystemParamList({ page: 1, page_size: 10 })
      return {
        success: true,
        apiPath: '/api/v2/system-params',
        responseStructure: this.analyzeResponseStructure(response),
        dataCount: Array.isArray(response?.data) ? response.data.length : 0,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        apiPath: '/api/v2/system-params',
      }
    }
  }

  /**
   * 测试审计日志API
   */
  async testAuditLogApi() {
    try {
      const response = await systemV2Api.getAuditLogList({ page: 1, page_size: 10 })
      return {
        success: true,
        apiPath: '/api/v2/audit-logs',
        responseStructure: this.analyzeResponseStructure(response),
        dataCount: Array.isArray(response?.data) ? response.data.length : 0,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        apiPath: '/api/v2/audit-logs',
      }
    }
  }

  /**
   * 分析响应数据结构
   */
  analyzeResponseStructure(response) {
    if (!response) return 'null'

    const structure = {
      type: typeof response,
      hasSuccess: 'success' in response,
      hasCode: 'code' in response,
      hasData: 'data' in response,
      hasMessage: 'message' in response,
      hasMeta: 'meta' in response,
      dataType: response.data ? typeof response.data : 'undefined',
      dataIsArray: Array.isArray(response.data),
      keys: Object.keys(response),
    }

    return structure
  }

  /**
   * 生成诊断报告
   */
  generateReport() {
    const successCount = Object.values(this.results).filter((r) => r.success).length
    const totalCount = Object.keys(this.results).length

    const report = {
      summary: {
        total: totalCount,
        success: successCount,
        failed: totalCount - successCount,
        successRate: `${((successCount / totalCount) * 100).toFixed(1)}%`,
      },
      details: this.results,
      errors: this.errors,
      recommendations: this.generateRecommendations(),
    }

    console.log('📊 诊断报告:', report)
    return report
  }

  /**
   * 生成修复建议
   */
  generateRecommendations() {
    const recommendations = []

    // 检查失败的模块
    Object.entries(this.results).forEach(([module, result]) => {
      if (!result.success) {
        if (result.status === 404) {
          recommendations.push(`${module}: API端点不存在，需要检查后端路由配置`)
        } else if (result.status === 401) {
          recommendations.push(`${module}: 认证失败，需要检查token或权限配置`)
        } else if (result.status === 500) {
          recommendations.push(`${module}: 服务器内部错误，需要检查后端实现`)
        } else {
          recommendations.push(`${module}: ${result.error}`)
        }
      }
    })

    // 检查数据结构一致性
    const structures = Object.values(this.results)
      .filter((r) => r.success)
      .map((r) => r.responseStructure)

    if (structures.length > 1) {
      const inconsistent = structures.some(
        (s) =>
          s.hasSuccess !== structures[0].hasSuccess ||
          s.hasCode !== structures[0].hasCode ||
          s.dataIsArray !== structures[0].dataIsArray
      )

      if (inconsistent) {
        recommendations.push('检测到API响应格式不一致，建议统一响应格式')
      }
    }

    return recommendations
  }
}

// 导出诊断函数供控制台使用
export async function runSystemDiagnostics() {
  const diagnostics = new SystemModuleDiagnostics()
  return await diagnostics.diagnoseAll()
}

// 在开发环境下将诊断工具挂载到window对象
if (process.env.NODE_ENV === 'development') {
  window.runSystemDiagnostics = runSystemDiagnostics
}
