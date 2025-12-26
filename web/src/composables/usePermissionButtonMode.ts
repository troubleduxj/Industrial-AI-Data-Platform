/**
 * 权限按钮显示模式管理
 * 从系统参数中读取配置，决定无权限按钮是隐藏还是禁用
 */
import { ref, computed } from 'vue'
import { systemV2Api } from '@/api'

// 全局状态
const buttonMode = ref<'hide' | 'disable'>('disable') // 默认禁用模式
const isLoading = ref(false)
const isLoaded = ref(false)

/**
 * 权限按钮显示模式
 */
export function usePermissionButtonMode() {
  /**
   * 加载配置
   */
  const loadConfig = async () => {
    if (isLoaded.value || isLoading.value) {
      return
    }

    try {
      isLoading.value = true
      
      // 从系统参数API获取配置
      const response = await systemV2Api.getSystemParamByKey('PERMISSION_BUTTON_MODE')
      
      if (response && response.data && response.data.param_value) {
        const value = response.data.param_value.toLowerCase()
        if (value === 'hide' || value === 'disable') {
          buttonMode.value = value
          console.log(`✅ 权限按钮显示模式: ${value}`)
        }
      }
      
      isLoaded.value = true
    } catch (error) {
      console.warn('无法加载权限按钮显示模式配置，使用默认值（disable）:', error)
      // 使用默认值
      buttonMode.value = 'disable'
      isLoaded.value = true
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 计算属性：是否隐藏无权限按钮
   */
  const hideWhenNoPermission = computed(() => buttonMode.value === 'hide')

  /**
   * 计算属性：是否禁用无权限按钮
   */
  const disableWhenNoPermission = computed(() => buttonMode.value === 'disable')

  /**
   * 重新加载配置
   */
  const reloadConfig = async () => {
    isLoaded.value = false
    await loadConfig()
  }

  return {
    buttonMode,
    hideWhenNoPermission,
    disableWhenNoPermission,
    loadConfig,
    reloadConfig,
    isLoading,
    isLoaded,
  }
}
