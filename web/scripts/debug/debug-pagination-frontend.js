/**
 * 前端分页调试脚本
 * 在浏览器控制台运行此脚本来检查分页状态
 */

console.log('='.repeat(80))
console.log('前端分页状态调试')
console.log('='.repeat(80))

// 检查Vue实例
const app = document.querySelector('#app').__vue_app__
if (app) {
  console.log('✅ Vue应用实例找到')
  
  // 尝试获取pagination状态
  const instances = app._instance.ctx.$children || []
  console.log('Vue组件实例数:', instances.length)
  
  // 查找包含pagination的组件
  function findPaginationData(component, depth = 0) {
    if (depth > 5) return null
    
    if (component && component.setupState) {
      const state = component.setupState
      if (state.pagination) {
        return state.pagination
      }
    }
    
    if (component && component.subTree && component.subTree.component) {
      return findPaginationData(component.subTree.component, depth + 1)
    }
    
    return null
  }
  
  const pagination = findPaginationData(app._instance)
  if (pagination) {
    console.log('\n📊 分页状态:')
    console.log('  - page:', pagination.page)
    console.log('  - pageSize:', pagination.pageSize)
    console.log('  - itemCount:', pagination.itemCount)
    console.log('  - 总页数:', Math.ceil(pagination.itemCount / pagination.pageSize))
    
    if (pagination.itemCount === 0) {
      console.error('❌ itemCount为0，这是问题所在！')
    } else if (pagination.itemCount === 20) {
      console.error('❌ itemCount为20，应该是7203！')
    } else {
      console.log('✅ itemCount正确:', pagination.itemCount)
    }
  } else {
    console.warn('⚠️  未找到pagination状态')
  }
} else {
  console.error('❌ 未找到Vue应用实例')
}

console.log('\n' + '='.repeat(80))
console.log('请检查以下内容:')
console.log('1. 查看上面的itemCount值')
console.log('2. 查看Network标签中的WebSocket消息')
console.log('3. 查看Console中是否有"✅ 检测到服务端分页格式"的日志')
console.log('='.repeat(80))
