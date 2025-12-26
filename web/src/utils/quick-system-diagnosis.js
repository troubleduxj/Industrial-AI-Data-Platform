/**
 * 快速系统诊断工具
 * 可以在任何系统管理页面的浏览器控制台中运行
 */

// 导入系统API
import systemV2Api from '@/api/system-v2'

/**
 * 快速诊断所有系统管理API
 */
export async function quickSystemDiagnosis() {
  console.log('🔍 开始快速系统诊断...')
  console.log('=====================================')

  // 检查基础环境
  const token = localStorage.getItem('access_token')
  const userInfo = localStorage.getItem('userInfo')

  console.log('📋 基础环境检查:')
  console.log('- Token存在:', !!token)
  console.log('- 用户信息存在:', !!userInfo)

  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const isExpired = payload.exp < Date.now() / 1000
      console.log('- Token有效:', !isExpired)
      if (isExpired) {
        console.warn('⚠️ Token已过期，请重新登录')
        return
      }
    } catch (e) {
      console.error('❌ Token格式无效')
      return
    }
  } else {
    console.error('❌ 缺少访问令牌，请先登录')
    return
  }

  console.log('=====================================')

  // 测试所有API
  const apiTests = [
    { name: '菜单管理', api: () => systemV2Api.getMenus({ page: 1, page_size: 5 }) },
    { name: '部门管理', api: () => systemV2Api.getDepts({ page: 1, page_size: 5 }) },
    { name: 'API管理', api: () => systemV2Api.getApiList({ page: 1, page_size: 5 }) },
    { name: 'API分组', api: () => systemV2Api.getApiGroupList({ page: 1, page_size: 5 }) },
    { name: '字典类型', api: () => systemV2Api.getDictTypeList({ page: 1, page_size: 5 }) },
    { name: '字典数据', api: () => systemV2Api.getDictDataList({ page: 1, page_size: 5 }) },
    { name: '系统参数', api: () => systemV2Api.getSystemParamList({ page: 1, page_size: 5 }) },
    { name: '审计日志', api: () => systemV2Api.getAuditLogList({ page: 1, page_size: 5 }) },
  ]

  console.log('🌐 API测试结果:')
  const results = {}

  for (const test of apiTests) {
    const startTime = Date.now()
    try {
      const response = await test.api()
      const endTime = Date.now()

      const result = {
        success: true,
        responseTime: endTime - startTime,
        status: response?.code || response?.status || 200,
        hasData: !!response?.data,
        dataCount: Array.isArray(response?.data) ? response.data.length : response?.data ? 1 : 0,
        dataType: Array.isArray(response?.data) ? 'array' : typeof response?.data,
      }

      results[test.name] = result
      console.log(`✅ ${test.name}: 成功 (${result.responseTime}ms, ${result.dataCount}条数据)`)
    } catch (error) {
      const endTime = Date.now()
      const result = {
        success: false,
        responseTime: endTime - startTime,
        error: error.message,
        status: error.response?.status || 'unknown',
      }

      results[test.name] = result
      console.log(`❌ ${test.name}: 失败 - ${error.message} (状态码: ${result.status})`)
    }

    // 添加小延迟避免请求过于频繁
    await new Promise((resolve) => setTimeout(resolve, 100))
  }

  console.log('=====================================')

  // 生成总结
  const totalTests = Object.keys(results).length
  const successCount = Object.values(results).filter((r) => r.success).length
  const failedCount = totalTests - successCount
  const successRate = Math.round((successCount / totalTests) * 100)

  console.log('📊 测试总结:')
  console.log(`- 总测试数: ${totalTests}`)
  console.log(`- 成功: ${successCount}`)
  console.log(`- 失败: ${failedCount}`)
  console.log(`- 成功率: ${successRate}%`)

  // 生成建议
  console.log('=====================================')
  console.log('💡 修复建议:')

  const failedApis = Object.entries(results).filter(([name, result]) => !result.success)

  if (failedApis.length === 0) {
    console.log('✅ 所有API测试通过！系统管理模块应该可以正常工作。')
  } else {
    failedApis.forEach(([name, result]) => {
      if (result.status === 404) {
        console.log(`🔧 ${name}: API端点不存在，请检查后端路由配置`)
      } else if (result.status === 401) {
        console.log(`🔐 ${name}: 权限不足，请检查用户权限配置`)
      } else if (result.status === 500) {
        console.log(`🛠️ ${name}: 服务器内部错误，请检查后端实现`)
      } else {
        console.log(`❓ ${name}: ${result.error}`)
      }
    })
  }

  console.log('=====================================')
  console.log('🔍 诊断完成！')

  return {
    summary: { totalTests, successCount, failedCount, successRate },
    results,
    timestamp: new Date().toISOString(),
  }
}

/**
 * 测试特定的API
 */
export async function testSpecificApi(apiName) {
  const apiMap = {
    菜单: () => systemV2Api.getMenus({ page: 1, page_size: 5 }),
    部门: () => systemV2Api.getDepts({ page: 1, page_size: 5 }),
    API: () => systemV2Api.getApiList({ page: 1, page_size: 5 }),
    API分组: () => systemV2Api.getApiGroupList({ page: 1, page_size: 5 }),
    字典类型: () => systemV2Api.getDictTypeList({ page: 1, page_size: 5 }),
    字典数据: () => systemV2Api.getDictDataList({ page: 1, page_size: 5 }),
    系统参数: () => systemV2Api.getSystemParamList({ page: 1, page_size: 5 }),
    审计日志: () => systemV2Api.getAuditLogList({ page: 1, page_size: 5 }),
  }

  const apiCall = apiMap[apiName]
  if (!apiCall) {
    console.error(`❌ 未找到API: ${apiName}`)
    console.log('可用的API:', Object.keys(apiMap))
    return
  }

  console.log(`🧪 测试 ${apiName} API...`)

  try {
    const startTime = Date.now()
    const response = await apiCall()
    const endTime = Date.now()

    console.log(`✅ ${apiName} API 测试成功:`)
    console.log('- 响应时间:', endTime - startTime, 'ms')
    console.log('- 状态码:', response?.code || response?.status || 200)
    console.log('- 数据类型:', Array.isArray(response?.data) ? 'array' : typeof response?.data)
    console.log(
      '- 数据数量:',
      Array.isArray(response?.data) ? response.data.length : response?.data ? 1 : 0
    )
    console.log('- 响应数据:', response)

    return response
  } catch (error) {
    console.error(`❌ ${apiName} API 测试失败:`)
    console.error('- 错误信息:', error.message)
    console.error('- 状态码:', error.response?.status || 'unknown')
    console.error('- 完整错误:', error)

    throw error
  }
}

/**
 * 检查页面状态
 */
export function checkPageStatus() {
  console.log('📄 当前页面状态检查:')
  console.log('- 当前路径:', window.location.pathname)
  console.log('- Vue应用:', !!window.__VUE__)
  console.log('- 路由器:', !!window.$router)

  // 检查是否在系统管理页面
  const isSystemPage = window.location.pathname.startsWith('/system')
  console.log('- 系统管理页面:', isSystemPage)

  if (isSystemPage) {
    console.log('✅ 当前在系统管理页面，可以直接测试相关功能')
  } else {
    console.log('💡 建议导航到系统管理页面进行测试')
  }
}

// 在开发环境下挂载到window对象
if (typeof window !== 'undefined') {
  window.quickSystemDiagnosis = quickSystemDiagnosis
  window.testSpecificApi = testSpecificApi
  window.checkPageStatus = checkPageStatus
}

// 自动执行检查（如果在浏览器环境中）
if (typeof window !== 'undefined' && window.location) {
  console.log('🔧 系统诊断工具已加载！')
  console.log('💡 使用方法:')
  console.log('  - 完整诊断: await quickSystemDiagnosis()')
  console.log('  - 测试特定API: await testSpecificApi("菜单")')
  console.log('  - 检查页面状态: checkPageStatus()')
}
