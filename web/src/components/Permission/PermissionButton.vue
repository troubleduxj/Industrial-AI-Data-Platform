<template>
  <n-button
    v-if="showButton"
    v-bind="buttonProps"
    :disabled="buttonDisabled"
    :loading="loading"
    @click="handleClick"
  >
    <template v-if="icon" #icon>
      <component :is="icon" />
    </template>
    <slot />
  </n-button>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { NButton } from 'naive-ui'
import { useEnhancedPermissionStore } from '@/store/modules/permission'
import { usePermissionButtonMode } from '@/composables/usePermissionButtonMode'

// 直接定义权限模式，避免循环导入
const PermissionMode = {
  ALL: 'all',
  ANY: 'any',
  EXACT: 'exact',
}

/**
 * 权限按钮组件
 * 根据用户权限自动控制按钮的显示、禁用状态
 */

const props = defineProps({
  // 权限相关
  permission: {
    type: [String, Array],
    default: null,
  },
  permissionMode: {
    type: String,
    default: 'any',
    validator: (value) => ['all', 'any', 'exact'].includes(value),
  },

  // 显示控制（如果不指定，则使用系统配置）
  hideWhenNoPermission: {
    type: Boolean,
    default: undefined, // undefined表示使用系统配置
  },
  disableWhenNoPermission: {
    type: Boolean,
    default: undefined, // undefined表示使用系统配置
  },
  showTooltipWhenNoPermission: {
    type: Boolean,
    default: true,
  },

  // 按钮属性
  type: {
    type: String,
    default: 'default',
  },
  size: {
    type: String,
    default: 'medium',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  icon: {
    type: [String, Object],
    default: null,
  },

  // 其他属性
  ghost: {
    type: Boolean,
    default: false,
  },
  dashed: {
    type: Boolean,
    default: false,
  },
  round: {
    type: Boolean,
    default: false,
  },
  circle: {
    type: Boolean,
    default: false,
  },
  block: {
    type: Boolean,
    default: false,
  },

  // 确认相关
  needConfirm: {
    type: Boolean,
    default: false,
  },
  confirmTitle: {
    type: String,
    default: '确认操作',
  },
  confirmContent: {
    type: String,
    default: '确定要执行此操作吗？',
  },

  // 权限不足时的提示
  noPermissionText: {
    type: String,
    default: '权限不足，无法执行此操作',
  },
})

const emit = defineEmits(['click', 'confirm', 'cancel'])

// 使用权限Store
let permissionStore = null
try {
  permissionStore = useEnhancedPermissionStore()
} catch (error) {
  console.warn('PermissionButton: useEnhancedPermissionStore failed:', error)
}

// 使用权限按钮显示模式配置
const { hideWhenNoPermission: globalHideMode, disableWhenNoPermission: globalDisableMode, loadConfig } = usePermissionButtonMode()

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
})

// 权限检查 - 添加缓存和错误处理
const hasAuth = computed(() => {
  try {
    if (!props.permission) {
      return true
    }

    // 如果权限Store不存在，尝试重新获取
    if (!permissionStore) {
      try {
        permissionStore = useEnhancedPermissionStore()
      } catch (error) {
        console.error('PermissionButton: Cannot get permission store, denying access for security')
        return false // 🔒 默认拒绝，确保安全
      }
    }

    // 如果权限检查方法不存在，返回默认值
    if (!permissionStore || !permissionStore.hasPermission) {
      console.error('PermissionButton: hasPermission method not available, denying access for security')
      return false // 🔒 默认拒绝，确保安全
    }

    const result = permissionStore.hasPermission(props.permission, props.permissionMode)

    // 详细的权限检查日志
    console.group(`🔍 PermissionButton: 权限检查详情 - "${props.permission}"`)
    console.log(`📊 检查结果: ${result ? '✅ 有权限' : '❌ 无权限'}`)
    console.log(`🔧 检查模式: ${props.permissionMode}`)

    // 显示Store中的所有权限数据
    if (permissionStore.accessApis) {
      console.log(`📋 Store中API权限总数: ${permissionStore.accessApis.length}`)
      console.log(
        `📋 Store中API权限数据类型: ${
          Array.isArray(permissionStore.accessApis) ? 'Array' : typeof permissionStore.accessApis
        }`
      )

      if (permissionStore.accessApis.length > 0) {
        console.log(`📋 前10个API权限:`, permissionStore.accessApis.slice(0, 10))

        // 查找维修记录相关权限
        const repairPermissions = permissionStore.accessApis.filter(
          (api) =>
            (typeof api === 'string' &&
              (api.includes('repair-records') || api.includes('maintenance'))) ||
            (api &&
              api.path &&
              (api.path.includes('repair-records') || api.path.includes('maintenance')))
        )
        console.log(`🔧 维修记录相关权限 (${repairPermissions.length}个):`, repairPermissions)

        // 检查是否包含当前权限
        const directMatch = permissionStore.accessApis.includes(props.permission)
        console.log(`🎯 直接匹配 "${props.permission}": ${directMatch}`)

        // 检查路径参数匹配
        if (props.permission.includes('{id}')) {
          const normalizedPermission = props.permission.replace(/\/\{[^}]+\}/g, '/*')
          const paramMatch = permissionStore.accessApis.includes(normalizedPermission)
          console.log(`🎯 路径参数匹配 "${normalizedPermission}": ${paramMatch}`)
        }
      }
    } else {
      console.log(`❌ Store中没有accessApis数据`)
    }

    // 显示allPermissions
    if (permissionStore.allPermissions) {
      console.log(`📋 allPermissions总数: ${permissionStore.allPermissions.length}`)
      const allRepairPermissions = permissionStore.allPermissions.filter(
        (perm) => perm.includes('repair-records') || perm.includes('maintenance')
      )
      console.log(`🔧 allPermissions中维修相关权限:`, allRepairPermissions)

      const inAllPermissions = permissionStore.allPermissions.includes(props.permission)
      console.log(`🎯 在allPermissions中: ${inAllPermissions}`)
    }

    // 显示用户信息
    try {
      const userStore =
        permissionStore._userStore ||
        window.__VUE_APP__?.config?.globalProperties?.$pinia?._s?.get('user')
      if (userStore) {
        console.log(`👤 用户信息:`)
        console.log(`  用户名: ${userStore.userInfo?.username || userStore.username || '未知'}`)
        console.log(`  超级用户: ${userStore.isSuperUser || userStore.is_superuser || false}`)
        console.log(`  Token存在: ${!!userStore.token}`)
      }
    } catch (error) {
      console.log(`👤 无法获取用户信息: ${error.message}`)
    }

    console.groupEnd()

    return result
  } catch (error) {
    console.error('PermissionButton: Error checking permission:', error)
    return true // 出错时默认允许
  }
})

// 按钮显示控制（优先使用props，否则使用全局配置）
const showButton = computed(() => {
  if (!hasAuth.value) {
    // 如果props明确指定了hideWhenNoPermission，使用props的值
    if (props.hideWhenNoPermission !== undefined) {
      return !props.hideWhenNoPermission
    }
    // 否则使用全局配置
    return !globalHideMode.value
  }
  return true
})

// 按钮禁用控制（优先使用props，否则使用全局配置）
const buttonDisabled = computed(() => {
  if (props.disabled) {
    return true
  }
  if (!hasAuth.value) {
    // 如果props明确指定了disableWhenNoPermission，使用props的值
    if (props.disableWhenNoPermission !== undefined) {
      return props.disableWhenNoPermission
    }
    // 否则使用全局配置
    return globalDisableMode.value
  }
  return false
})

// 按钮属性
const buttonProps = computed(() => ({
  type: props.type,
  size: props.size,
  ghost: props.ghost,
  dashed: props.dashed,
  round: props.round,
  circle: props.circle,
  block: props.block,
  title: !hasAuth.value && props.showTooltipWhenNoPermission ? props.noPermissionText : undefined,
}))

// 点击处理
const handleClick = (event) => {
  if (!hasAuth.value) {
    if (props.showTooltipWhenNoPermission) {
      // 显示权限不足提示
      window.$message?.warning(props.noPermissionText)
    }
    return
  }

  if (props.needConfirm) {
    // 显示确认对话框
    showConfirmDialog()
  } else {
    emit('click', event)
  }
}

// 确认对话框
const showConfirmDialog = () => {
  window.$dialog?.warning({
    title: props.confirmTitle,
    content: props.confirmContent,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      emit('confirm')
    },
    onNegativeClick: () => {
      emit('cancel')
    },
  })
}
</script>

<style scoped>
/* 权限不足时的样式 */
.n-button[disabled] {
  cursor: not-allowed;
}
</style>
