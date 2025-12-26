/**
 * 导入测试文件
 * 用于测试批量删除相关文件的导入是否正常
 */

console.log('🧪 开始测试导入...')

// 测试基础导入
try {
  console.log('1. 测试 batch-delete-error-handler 导入...')
  import('./batch-delete-error-handler.js')
    .then((module) => {
      console.log('✅ batch-delete-error-handler 导入成功:', Object.keys(module))
    })
    .catch((error) => {
      console.error('❌ batch-delete-error-handler 导入失败:', error)
    })
} catch (error) {
  console.error('❌ batch-delete-error-handler 同步导入失败:', error)
}

try {
  console.log('2. 测试 batch-delete-fix 导入...')
  import('./batch-delete-fix.js')
    .then((module) => {
      console.log('✅ batch-delete-fix 导入成功:', Object.keys(module))
    })
    .catch((error) => {
      console.error('❌ batch-delete-fix 导入失败:', error)
    })
} catch (error) {
  console.error('❌ batch-delete-fix 同步导入失败:', error)
}

// 测试组合式函数导入
try {
  console.log('3. 测试 useBatchDelete 导入...')
  import('../composables/useBatchDelete.js')
    .then((module) => {
      console.log('✅ useBatchDelete 导入成功:', Object.keys(module))
    })
    .catch((error) => {
      console.error('❌ useBatchDelete 导入失败:', error)
    })
} catch (error) {
  console.error('❌ useBatchDelete 同步导入失败:', error)
}

export default {
  test: () => console.log('导入测试完成'),
}
