/**
 * 浏览器端Vue文件检查工具
 * 通过动态导入检查Vue组件是否能正常加载
 */

// 系统管理页面路由列表
const systemRoutes = [
  '/system/user',
  '/system/role', 
  '/system/menu',
  '/system/dept',
  '/system/api',
  '/system/api/groups',
  '/system/dict',
  '/system/dict/data',
  '/system/config',
  '/system/param',
  '/system/auditlog',
  '/system/components'
]

// 对应的组件导入路径
const componentPaths = {
  '/system/user': () => import('../src/views/system/user/index.vue'),
  '/system/role': () => import('../src/views/system/roleV2/index.vue'),
  '/system/menu': () => import('../src/views/system/menu/index.vue'),
  '/system/dept': () => import('../src/views/system/dept/index.vue'),
  '/system/api': () => import('../src/views/system/api/index.vue'),
  '/system/api/groups': () => import('../src/views/system/api/groups/index.vue'),
  '/system/dict': () => import('../src/views/system/dict/DictType/index.vue'),
  '/system/dict/data': () => import('../src/views/system/dict/DictData/index.vue'),
  '/system/config': () => import('../src/views/system/config/SystemConfig/index.vue'),
  '/system/param': () => import('../src/views/system/param/index.vue'),
  '/system/auditlog': () => import('../src/views/system/auditlog/index.vue'),
  '/system/components': () => import('../src/views/system/components/index.vue')
}

// 检查单个组件
async function checkComponent(route) {
  try {
    console.log(`检查组件: ${route}`)
    const importFn = componentPaths[route]
    
    if (!importFn) {
      return { route, status: 'error', error: '未找到对应的导入函数' }
    }
    
    const component = await importFn()
    
    if (!component || !component.default) {
      return { route, status: 'error', error: '组件导入失败或没有默认导出' }
    }
    
    return { route, status: 'success', component: component.default }
  } catch (error) {
    return { 
      route, 
      status: 'error', 
      error: error.message,
      stack: error.stack
    }
  }
}

// 检查所有组件
async function checkAllComponents() {
  console.log('开始检查所有系统管理组件...')
  
  const results = []
  
  for (const route of systemRoutes) {
    const result = await checkComponent(route)
    results.push(result)
    
    if (result.status === 'success') {
      console.log(`✅ ${route} - 组件加载成功`)
    } else {
      console.error(`❌ ${route} - 组件加载失败:`, result.error)
    }
  }
  
  // 汇总结果
  const successCount = results.filter(r => r.status === 'success').length
  const errorCount = results.filter(r => r.status === 'error').length
  
  console.log('\n=== 检查结果汇总 ===')
  console.log(`总计: ${results.length} 个组件`)
  console.log(`成功: ${successCount} 个`)
  console.log(`失败: ${errorCount} 个`)
  
  if (errorCount > 0) {
    console.log('\n失败的组件:')
    results.filter(r => r.status === 'error').forEach(r => {
      console.log(`- ${r.route}: ${r.error}`)
    })
  }
  
  return results
}

// 导出函数供外部调用
window.checkVueComponents = checkAllComponents
window.checkSingleComponent = checkComponent

// 自动执行检查
console.log('Vue组件检查工具已加载，调用 checkVueComponents() 开始检查')