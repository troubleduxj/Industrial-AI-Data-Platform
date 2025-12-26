import setupPermissionDirective from './permission'
import enhancedPermissionDirectives from './enhanced-permission'

/** setup custom vue directives. - [安装自定义的vue指令] */
export function setupDirectives(app) {
  console.log('📋 开始设置指令系统...')

  try {
    console.log('🔒 设置基础权限指令...')
    setupPermissionDirective(app)
    console.log('✅ 基础权限指令设置完成')

    console.log('🔒+ 设置增强版权限指令...')
    app.use(enhancedPermissionDirectives)
    console.log('✅ 增强版权限指令设置完成')
  } catch (error) {
    console.error('❌ 指令系统设置失败:', error)
    console.error('错误堆栈:', error.stack)
    throw error
  }
}
