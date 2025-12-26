/** 重置样式 */
import '@/styles/reset.css'
import '@/styles/theme.scss'
import '@/styles/theme-standardized.scss'
import 'uno.css'
import '@/styles/global.scss'

import { createApp } from 'vue'
import { setupRouter } from '@/router'
import { setupStore } from '@/store'
import App from './App.vue'
import { setupDirectives } from './directives'
import { useResize } from '@/utils'
import i18n from '~/i18n'
import PermissionComponents from '@/components/Permission'
import PermissionRealtimePlugin from '@/plugins/permission-realtime'
import { setupGlobalErrorHandler } from '@/utils/vue-error-handler'
import '@/utils/fix-vue-errors'
import { autoFixAuthState, watchAuthState } from '@/utils/auth-state-fix'
import { initMockInterceptor } from '@/utils/mock-interceptor'

// 开发环境检查和工具加载
if (import.meta.env.DEV) {
  console.log('✅ 开发环境已启用')

  // 加载主题系统测试工具
  import('@/utils/theme-system-test.js')
    .then((module) => {
      console.log('🔧 主题系统测试工具已加载')
    })
    .catch((error) => {
      console.warn('主题测试工具加载失败:', error)
    })

  // 加载认证诊断工具
  import('@/utils/auth-diagnosis.js')
    .then((module) => {
      console.log('🔧 认证诊断工具已加载')
      console.log('💡 可用命令: runAuthDiagnosis(), autoFixAuth(), clearAllAuthData()')
    })
    .catch((error) => {
      console.warn('认证诊断工具加载失败:', error)
    })
}

async function setupApp() {
  console.log('🚀 开始应用初始化...')

  try {
    console.log('📱 创建Vue应用实例...')
    const app = createApp(App)
    console.log('✅ Vue应用实例创建成功')

    console.log('🛡️ 设置全局错误处理器...')
    setupGlobalErrorHandler(app)
    console.log('✅ 全局错误处理器设置完成')

    console.log('🏪 初始化状态管理...')
    await setupStore(app)
    console.log('✅ 状态管理初始化完成')

    console.log('🧠 初始化AI模块...')
    try {
      const { useAIModuleStore } = await import('@/store/modules/ai')
      const aiModuleStore = useAIModuleStore()
      await aiModuleStore.initialize()
      console.log('✅ AI模块初始化完成:', {
        enabled: aiModuleStore.isEnabled,
        loaded: aiModuleStore.isLoaded,
        features: aiModuleStore.enabledFeatures,
      })
    } catch (error) {
      console.warn('⚠️ AI模块初始化失败（非关键错误）:', error)
    }

    console.log('🎭 初始化Mock拦截器...')
    try {
      await initMockInterceptor()
      console.log('✅ Mock拦截器初始化完成')
    } catch (error) {
      console.warn('⚠️ Mock拦截器初始化失败:', error)
    }

    console.log('👀 启动认证状态监听...')
    watchAuthState()
    console.log('✅ 认证状态监听启动完成')

    console.log('🔐 自动修复认证状态...')
    try {
      const authResult = await autoFixAuthState()
      console.log('✅ 认证状态检查完成:', authResult)
    } catch (error) {
      console.warn('⚠️ 认证状态自动修复失败:', error)
    }

    console.log('🛣️ 设置路由系统...')
    await setupRouter(app)
    console.log('✅ 路由系统设置完成')

    console.log('📋 设置指令系统...')
    setupDirectives(app)
    console.log('✅ 指令系统设置完成')

    console.log('🔒 注册权限组件...')
    app.use(PermissionComponents)
    console.log('✅ 权限组件注册完成')

    console.log('⚡ 注册权限实时更新插件...')
    app.use(PermissionRealtimePlugin, {
      autoRefresh: true,
      refreshInterval: 30000,
      enableApiInterception: true,
      enableStorageWatch: true,
      debugMode: import.meta.env.DEV,
    })
    console.log('✅ 权限实时更新插件注册完成')

    console.log('📐 注册工具插件...')
    app.use(useResize)
    console.log('✅ useResize插件注册完成')

    console.log('🌍 注册国际化...')
    app.use(i18n)
    console.log('✅ 国际化注册完成')

    console.log('🎯 挂载应用到DOM...')
    app.mount('#app')
    console.log('🎉 应用挂载完成！')

    if (import.meta.env.DEV) {
      console.log('✅ 应用已准备就绪')
    }
  } catch (error) {
    console.error('❌ 应用初始化失败:', error)
    console.error('错误堆栈:', error.stack)
    throw error
  }
}

setupApp()
