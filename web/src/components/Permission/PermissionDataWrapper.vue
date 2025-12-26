<template>
  <div class="permission-data-wrapper">
    <!-- 有数据时显示内容 -->
    <div v-if="hasData" class="data-content">
      <slot :data="data" :loading="loading" />
    </div>

    <!-- 无数据时的处理 -->
    <div v-else class="empty-content">
      <!-- 权限不足 - 优先检查权限 -->
      <PermissionEmpty
        v-if="isPermissionIssue"
        :type="permissionType"
        :description="permissionDescription"
        :permission-name="permissionName"
        :show-actions="showPermissionActions"
        :show-refresh="showRefresh"
        :show-contact="showContact"
        :show-apply="showApply"
        @refresh="handleRefresh"
        @contact="handleContact"
        @apply="handleApply"
      />

      <!-- 加载中 - 只有在有权限时才显示加载状态 -->
      <div v-else-if="loading" class="loading-content">
        <n-spin size="large">
          <template #description>
            {{ loadingText }}
          </template>
        </n-spin>
      </div>

      <!-- 普通无数据 -->
      <n-empty v-else :description="emptyDescription" :size="emptySize">
        <template v-if="showEmptyActions" #extra>
          <n-space>
            <n-button v-if="showRefresh" :loading="refreshing" secondary @click="handleRefresh">
              刷新数据
            </n-button>

            <n-button v-if="showCreate && hasCreatePermission" type="primary" @click="handleCreate">
              {{ createText }}
            </n-button>
          </n-space>
        </template>
      </n-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { NSpin, NEmpty, NButton, NSpace } from 'naive-ui'
import { usePermission } from '@/composables/usePermission'
import PermissionEmpty from './PermissionEmpty.vue'

const props = defineProps({
  // 数据
  data: {
    type: Array,
    default: () => [],
  },

  // 加载状态
  loading: {
    type: Boolean,
    default: false,
  },

  // 权限检查
  permission: {
    type: [String, Array],
    default: '',
  },

  // 创建权限
  createPermission: {
    type: String,
    default: '',
  },

  // 权限类型
  permissionType: {
    type: String,
    default: 'data',
  },

  // 权限名称
  permissionName: {
    type: String,
    default: '',
  },

  // 自定义权限描述
  permissionDescription: {
    type: String,
    default: '',
  },

  // 自定义空数据描述
  emptyDescription: {
    type: String,
    default: '暂无数据',
  },

  // 加载文本
  loadingText: {
    type: String,
    default: '加载中...',
  },

  // 创建按钮文本
  createText: {
    type: String,
    default: '新建',
  },

  // 空数据大小
  emptySize: {
    type: String,
    default: 'medium',
  },

  // 显示权限操作按钮
  showPermissionActions: {
    type: Boolean,
    default: true,
  },

  // 显示空数据操作按钮
  showEmptyActions: {
    type: Boolean,
    default: true,
  },

  // 显示刷新按钮
  showRefresh: {
    type: Boolean,
    default: true,
  },

  // 显示联系管理员按钮
  showContact: {
    type: Boolean,
    default: true,
  },

  // 显示申请权限按钮
  showApply: {
    type: Boolean,
    default: false,
  },

  // 显示创建按钮
  showCreate: {
    type: Boolean,
    default: true,
  },

  // 强制显示权限问题（即使有数据权限）
  forcePermissionCheck: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['refresh', 'contact', 'apply', 'create'])

// 权限检查
const { hasPermission } = usePermission()

// 响应式数据
const refreshing = ref(false)
const permissionChecked = ref(false)
const hasDataPermission = ref(true)

// 立即进行权限检查（同步）
const immediatePermissionCheck = computed(() => {
  if (!props.permission) {
    return true // 没有指定权限，默认有权限
  }

  try {
    return hasPermission(props.permission)
  } catch (error) {
    console.warn('权限检查失败:', error)
    return false // 权限检查失败，默认无权限
  }
})

// 计算属性
const hasData = computed(() => {
  return Array.isArray(props.data) && props.data.length > 0
})

const hasCreatePermission = computed(() => {
  if (!props.createPermission) return true
  return hasPermission(props.createPermission)
})

const isPermissionIssue = computed(() => {
  // 如果强制检查权限问题
  if (props.forcePermissionCheck) {
    return !hasDataPermission.value
  }

  // 如果没有指定权限，不是权限问题
  if (!props.permission) {
    return false
  }

  // 使用立即权限检查结果
  // 这样可以在页面加载时立即显示权限提示，而不需要等待数据加载
  return !immediatePermissionCheck.value
})

// 方法（必须在 watch 之前定义，避免 TDZ 错误）
const checkPermission = () => {
  if (!props.permission) {
    hasDataPermission.value = true
    permissionChecked.value = true
    return
  }

  hasDataPermission.value = hasPermission(props.permission)
  permissionChecked.value = true
}

// 监听权限变化
watch(
  () => props.permission,
  (newPermission) => {
    if (newPermission) {
      checkPermission()
    }
  },
  { immediate: true }
)

// 监听数据变化
watch(
  () => props.data,
  (newData) => {
    // 如果数据从无到有，可能是权限问题解决了
    if (Array.isArray(newData) && newData.length > 0) {
      hasDataPermission.value = true
    }
  },
  { immediate: true }
)

const handleRefresh = async () => {
  refreshing.value = true
  try {
    // 重新检查权限
    checkPermission()

    // 触发刷新事件
    emit('refresh')
  } finally {
    refreshing.value = false
  }
}

const handleContact = () => {
  emit('contact')
}

const handleApply = (permissionName) => {
  emit('apply', permissionName)
}

const handleCreate = () => {
  emit('create')
}

// 暴露方法给父组件
defineExpose({
  checkPermission,
  refresh: handleRefresh,
})
</script>

<style scoped>
.permission-data-wrapper {
  width: 100%;
}

.data-content {
  width: 100%;
}

.empty-content {
  width: 100%;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-content {
  width: 100%;
  padding: 60px 20px;
  text-align: center;
}

.loading-content :deep(.n-spin) {
  width: 100%;
}

.loading-content :deep(.n-spin__description) {
  margin-top: 12px;
  color: #666;
}
</style>
