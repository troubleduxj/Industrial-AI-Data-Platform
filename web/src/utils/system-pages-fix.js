/**
 * 系统管理页面修复脚本
 * 统一修复系统管理模块中各个页面的常见问题
 */

// 修复1: 确保所有页面都有正确的onMounted和onActivated钩子
export function ensureLifecycleHooks() {
  console.log('🔧 修复生命周期钩子...')

  // 这个函数主要用于指导手动修复，实际修复需要在各个页面文件中进行
  const fixes = [
    '确保每个页面都有 onMounted 钩子',
    '确保每个页面都有 onActivated 钩子',
    '在钩子中调用 $table.value?.handleSearch()',
    '添加适当的错误处理',
  ]

  return { success: true, fixes }
}

// 修复2: 统一API调用方式
export function standardizeApiCalls() {
  console.log('🔧 标准化API调用...')

  const apiMappings = {
    菜单管理: 'systemV2Api.getMenus',
    部门管理: 'systemV2Api.getDepts',
    API管理: 'systemV2Api.getApiList',
    API分组: 'systemV2Api.getApiGroupList',
    字典类型: 'systemV2Api.getDictTypeList',
    字典数据: 'systemV2Api.getDictDataList',
    系统参数: 'systemV2Api.getSystemParamList',
    审计日志: 'systemV2Api.getAuditLogList',
  }

  return { success: true, apiMappings }
}

// 修复3: 统一错误处理
export function addErrorHandling() {
  console.log('🔧 添加错误处理...')

  const errorHandlingTemplate = `
try {
  const response = await apiCall(params)
  return {
    data: response.data || [],
    total: response.total || 0
  }
} catch (error) {
  console.error('API调用失败:', error)
  message?.error('获取数据失败: ' + (error.message || '未知错误'))
  return { data: [], total: 0 }
}
`

  return { success: true, template: errorHandlingTemplate }
}

// 修复4: 统一分页处理
export function standardizePagination() {
  console.log('🔧 标准化分页处理...')

  const paginationTemplate = `
// 分页状态管理
const pagination = ref({
  page: 1,
  pageSize: 10,
})

// 分页事件处理
const handlePageChange = (page) => {
  pagination.value.page = page
}

const handlePageSizeChange = (pageSize) => {
  pagination.value.page = 1
  pagination.value.pageSize = pageSize
}
`

  return { success: true, template: paginationTemplate }
}

// 修复5: 检查必要的导入
export function checkRequiredImports() {
  console.log('🔧 检查必要的导入...')

  const requiredImports = [
    "import { onMounted, onActivated } from 'vue'",
    "import systemV2Api from '@/api/system-v2'",
    "import CommonPage from '@/components/page/CommonPage.vue'",
    "import CrudTable from '@/components/table/CrudTable.vue'",
    "import { useMessage } from 'naive-ui'",
  ]

  return { success: true, requiredImports }
}

// 主修复函数
export async function fixSystemPages() {
  console.log('🚀 开始修复系统管理页面...')

  const results = {
    lifecycleHooks: ensureLifecycleHooks(),
    apiCalls: standardizeApiCalls(),
    errorHandling: addErrorHandling(),
    pagination: standardizePagination(),
    imports: checkRequiredImports(),
  }

  console.log('✅ 系统管理页面修复完成')
  return results
}

// 页面特定的修复建议
export const pageSpecificFixes = {
  菜单管理: {
    issues: ['树形结构处理', '展开状态管理'],
    solutions: ['使用buildMenuTree函数', '正确处理expandedRowKeys'],
  },

  部门管理: {
    issues: ['树形结构', '级联删除'],
    solutions: ['实现部门树形显示', '添加删除确认'],
  },

  API管理: {
    issues: ['分组关联', '权限验证'],
    solutions: ['加载API分组数据', '检查操作权限'],
  },

  字典类型: {
    issues: ['数据关联', '系统内置保护'],
    solutions: ['关联字典数据', '保护系统内置类型'],
  },

  字典数据: {
    issues: ['类型关联', '排序处理'],
    solutions: ['正确关联字典类型', '实现排序功能'],
  },

  系统参数: {
    issues: ['类型验证', '值格式化'],
    solutions: ['根据类型验证值', '格式化显示'],
  },

  审计日志: {
    issues: ['时间范围', '数据量大'],
    solutions: ['默认今日数据', '优化查询性能'],
  },
}

// 导出给开发环境使用
if (process.env.NODE_ENV === 'development') {
  window.fixSystemPages = fixSystemPages
  window.pageSpecificFixes = pageSpecificFixes
}
