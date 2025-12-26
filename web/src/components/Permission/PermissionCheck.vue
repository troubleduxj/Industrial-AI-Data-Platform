<template>
  <div v-if="hasAuth" class="permission-check">
    <slot />
  </div>
  <div v-else-if="showFallback" class="permission-fallback">
    <slot name="fallback">
      <div v-if="showNoPermissionMessage" class="no-permission-message">
        <n-empty :description="noPermissionText" size="small">
          <template #icon>
            <n-icon size="48" color="#d9d9d9">
              <LockClosedOutline />
            </n-icon>
          </template>
        </n-empty>
      </div>
    </slot>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { NEmpty, NIcon } from 'naive-ui'
import { LockClosedOutline } from '@vicons/ionicons5'
import { useEnhancedPermissionStore } from '@/store/modules/permission'

// 直接定义权限模式，避免循环导入
const PermissionMode = {
  ALL: 'all',
  ANY: 'any',
  EXACT: 'exact',
}

/**
 * 权限检查组件
 * 根据权限控制内容的显示
 */

const props = defineProps({
  // 权限相关
  permission: {
    type: [String, Array],
    required: true,
  },
  permissionMode: {
    type: String,
    default: 'any',
    validator: (value) => ['all', 'any', 'exact'].includes(value),
  },

  // 显示控制
  showFallback: {
    type: Boolean,
    default: true,
  },
  showNoPermissionMessage: {
    type: Boolean,
    default: true,
  },
  noPermissionText: {
    type: String,
    default: '权限不足，无法访问此内容',
  },

  // 调试模式
  debug: {
    type: Boolean,
    default: false,
  },
})

// 直接使用Store，避免Composable循环导入
const permissionStore = useEnhancedPermissionStore()

// 权限检查
const hasAuth = computed(() => {
  const result = permissionStore.hasPermission(props.permission, props.permissionMode)

  if (props.debug) {
    console.log('PermissionCheck:', {
      permission: props.permission,
      mode: props.permissionMode,
      hasAuth: result,
    })
  }

  return result
})
</script>

<style scoped>
.permission-check {
  /* 有权限时的样式 */
}

.permission-fallback {
  /* 无权限时的样式 */
}

.no-permission-message {
  padding: 20px;
  text-align: center;
  color: #999;
}
</style>
