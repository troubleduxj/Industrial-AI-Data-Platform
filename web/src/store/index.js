import { createPinia } from 'pinia'
import * as modules from './modules'
import { unifiedStateManager } from './unified-state'
import { useThemeStore } from './theme'
import { useChatWidgetStore } from './modules/chatWidget'

const pinia = createPinia()

export const setupStore = async (app) => {
  app.use(pinia)

  // 在开发环境中将Pinia实例挂载到window对象上，便于调试
  if (import.meta.env.DEV) {
    window.$pinia = pinia
  }

  // 初始化统一状态管理
  try {
    await unifiedStateManager.initialize()
    console.log('统一状态管理初始化成功')
  } catch (error) {
    console.error('统一状态管理初始化失败:', error)
    // 不阻止应用启动，但记录错误
  }

  // 初始化主题设置
  try {
    const themeStore = useThemeStore()
    themeStore.loadThemeFromStorage()
    console.log('主题设置初始化成功')
  } catch (error) {
    console.error('主题设置初始化失败:', error)
  }

  // 初始化聊天组件设置
  try {
    const chatWidgetStore = useChatWidgetStore()
    await chatWidgetStore.initStore()
    console.log('聊天组件设置初始化成功')
  } catch (error) {
    console.error('聊天组件设置初始化失败:', error)
  }
}

export { modules, unifiedStateManager, useThemeStore }
export * from './unified-state'
export * from './theme'
export default pinia
