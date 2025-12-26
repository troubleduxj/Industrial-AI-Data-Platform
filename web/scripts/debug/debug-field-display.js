/**
 * 前端字段显示问题诊断脚本
 * 在浏览器控制台运行此脚本
 */

console.log('='.repeat(80))
console.log('开始诊断前端字段显示问题')
console.log('='.repeat(80))

// 1. 检查当前页面状态
console.log('\n【步骤1】检查当前页面状态')
console.log('-'.repeat(80))

// 检查当前URL
console.log('当前URL:', window.location.href)

// 检查Vue实例
if (window.__VUE_DEVTOOLS_GLOBAL_HOOK__) {
  console.log('✓ Vue DevTools 已安装')
} else {
  console.log('⚠️  Vue DevTools 未安装')
}

// 2. 检查设备类型筛选
console.log('\n【步骤2】检查设备类型筛选')
console.log('-'.repeat(80))

// 尝试从页面获取当前选择的设备类型
const deviceTypeSelect = document.querySelector('input[placeholder="全部类型"]')
if (deviceTypeSelect) {
  console.log('设备类型选择器:', deviceTypeSelect.value || '未选择')
} else {
  console.log('⚠️  未找到设备类型选择器')
}

// 3. 检查API调用
console.log('\n【步骤3】检查API调用')
console.log('-'.repeat(80))

// 拦截fetch请求
const originalFetch = window.fetch
const apiCalls = []

window.fetch = function(...args) {
  const url = args[0]
  if (typeof url === 'string' && url.includes('device-fields')) {
    console.log('📡 API调用:', url)
    apiCalls.push({ url, timestamp: new Date() })
  }
  return originalFetch.apply(this, args)
}

console.log('已设置API拦截器，监控 device-fields 相关请求')

// 4. 检查localStorage缓存
console.log('\n【步骤4】检查localStorage缓存')
console.log('-'.repeat(80))

const cacheKeys = []
for (let i = 0; i < localStorage.length; i++) {
  const key = localStorage.key(i)
  if (key && (key.includes('device') || key.includes('field'))) {
    cacheKeys.push(key)
  }
}

if (cacheKeys.length > 0) {
  console.log('找到相关缓存键:', cacheKeys)
  cacheKeys.forEach(key => {
    const value = localStorage.getItem(key)
    console.log(`  ${key}:`, value ? value.substring(0, 100) + '...' : 'null')
  })
} else {
  console.log('未找到相关缓存')
}

// 5. 测试API调用
console.log('\n【步骤5】测试API调用')
console.log('-'.repeat(80))

async function testDeviceFieldsAPI() {
  const deviceTypes = ['welding', 'PRESSURE_SENSOR_V1', 'cutting', 'test', 'test2']
  
  for (const deviceType of deviceTypes) {
    try {
      console.log(`\n测试设备类型: ${deviceType}`)
      const response = await fetch(`/api/v2/device-fields/monitoring-keys/${deviceType}`, {
        headers: {
          'Authorization': localStorage.getItem('token') || ''
        }
      })
      
      const data = await response.json()
      
      if (response.ok) {
        console.log(`  ✓ API调用成功`)
        console.log(`  返回字段数量: ${data.data ? data.data.length : 0}`)
        if (data.data && data.data.length > 0) {
          console.log(`  字段列表:`)
          data.data.forEach(field => {
            console.log(`    - ${field.field_name} (${field.field_code})`)
          })
        } else {
          console.log(`  ⚠️  该设备类型没有监测关键字段`)
        }
      } else {
        console.log(`  ❌ API调用失败: ${response.status} ${response.statusText}`)
        console.log(`  错误信息:`, data)
      }
    } catch (error) {
      console.log(`  ❌ API调用异常:`, error.message)
    }
  }
}

// 执行测试
testDeviceFieldsAPI().then(() => {
  console.log('\n' + '='.repeat(80))
  console.log('诊断完成')
  console.log('='.repeat(80))
  console.log('\n如果发现问题，请检查:')
  console.log('1. 设备类型代码是否正确 (device_type_code)')
  console.log('2. 数据库中是否配置了监测关键字段 (is_monitoring_key=true)')
  console.log('3. 字段是否被激活 (is_active=true)')
  console.log('4. 前端是否正确传递了 device_type_code')
  console.log('5. 清除浏览器缓存后重试')
})

// 6. 提供清除缓存的函数
window.clearDeviceFieldCache = function() {
  console.log('清除设备字段相关缓存...')
  const keysToRemove = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && (key.includes('device') || key.includes('field'))) {
      keysToRemove.push(key)
    }
  }
  keysToRemove.forEach(key => localStorage.removeItem(key))
  console.log(`已清除 ${keysToRemove.length} 个缓存项`)
  console.log('请刷新页面')
}

console.log('\n提示: 可以运行 clearDeviceFieldCache() 清除缓存')
