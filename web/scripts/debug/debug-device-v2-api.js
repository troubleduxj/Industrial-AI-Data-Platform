// 调试脚本：检查 device-v2 API 结构
// 在浏览器控制台运行此脚本

console.log('=== 调试 device-v2 API ===')

// 动态导入模块
import('/src/api/device-v2.ts').then(module => {
  console.log('✅ device-v2 模块加载成功')
  console.log('默认导出:', module.default)
  console.log('命名导出 deviceV2Api:', module.deviceV2Api)
  
  const api = module.default || module.deviceV2Api
  console.log('API 对象:', api)
  console.log('API.deviceTypes:', api?.deviceTypes)
  console.log('API.deviceFields:', api?.deviceFields)
  
  if (api?.deviceFields) {
    console.log('deviceFields 方法:')
    console.log('  - getMonitoringKeys:', typeof api.deviceFields.getMonitoringKeys)
    console.log('  - create:', typeof api.deviceFields.create)
    console.log('  - update:', typeof api.deviceFields.update)
    console.log('  - delete:', typeof api.deviceFields.delete)
  } else {
    console.error('❌ deviceFields 未定义!')
  }
}).catch(err => {
  console.error('❌ 加载失败:', err)
})

// 检查 device-field API
import('/src/api/device-field.ts').then(module => {
  console.log('\n=== device-field 模块 ===')
  console.log('默认导出:', module.default)
  console.log('命名导出 deviceFieldApi:', module.deviceFieldApi)
  
  const api = module.default || module.deviceFieldApi
  console.log('API 方法:')
  console.log('  - getMonitoringKeys:', typeof api?.getMonitoringKeys)
  console.log('  - create:', typeof api?.create)
  console.log('  - update:', typeof api?.update)
  console.log('  - delete:', typeof api?.delete)
}).catch(err => {
  console.error('❌ 加载失败:', err)
})
