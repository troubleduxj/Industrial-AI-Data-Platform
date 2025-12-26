/**
 * Token问题诊断脚本
 * 在浏览器控制台运行此脚本来诊断token问题
 */

export function diagnoseToken() {
  console.log('=' .repeat(80))
  console.log('Token问题诊断')
  console.log('=' .repeat(80))
  
  // 1. 检查localStorage中的所有数据
  console.log('\n1. localStorage中的所有数据:')
  const allStorage = {}
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    allStorage[key] = localStorage.getItem(key)
  }
  console.table(allStorage)
  
  // 2. 检查可能的token keys
  console.log('\n2. 检查可能的token keys:')
  const possibleKeys = ['access_token', 'token', 'accessToken', 'Authorization', 'auth_token']
  possibleKeys.forEach(key => {
    const value = localStorage.getItem(key)
    console.log(`  ${key}:`, value ? `${value.substring(0, 30)}...` : 'null')
  })
  
  // 3. 检查userStore
  console.log('\n3. 检查userStore:')
  try {
    const { useUserStore } = await import('@/store')
    const userStore = useUserStore()
    console.log('  用户信息:', {
      username: userStore.name,
      userId: userStore.userId,
      isSuperUser: userStore.isSuperUser,
      token: userStore.token ? `${userStore.token.substring(0, 30)}...` : 'null',
      isLoggingOut: userStore.isLoggingOut
    })
  } catch (error) {
    console.error('  无法获取userStore:', error)
  }
  
  // 4. 检查permissionStore
  console.log('\n4. 检查permissionStore:')
  try {
    const { useEnhancedPermissionStore } = await import('@/store/modules/permission')
    const permissionStore = useEnhancedPermissionStore()
    console.log('  API权限数量:', permissionStore.accessApis?.length || 0)
    console.log('  前5个权限:', permissionStore.accessApis?.slice(0, 5) || [])
  } catch (error) {
    console.error('  无法获取permissionStore:', error)
  }
  
  // 5. 测试API调用
  console.log('\n5. 测试API调用:')
  try {
    const { authApi } = await import('@/api/system-v2')
    console.log('  尝试获取用户API权限...')
    const res = await authApi.getUserApis()
    console.log('  API响应:', res)
    console.log('  API权限数量:', res.data?.length || 0)
  } catch (error) {
    console.error('  API调用失败:', error)
    console.error('  错误详情:', {
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    })
  }
  
  console.log('\n' + '='.repeat(80))
  console.log('诊断完成')
  console.log('='.repeat(80))
}

// 自动执行
if (typeof window !== 'undefined') {
  window.diagnoseToken = diagnoseToken
  console.log('✅ Token诊断脚本已加载')
  console.log('💡 在控制台执行 diagnoseToken() 来运行诊断')
}
