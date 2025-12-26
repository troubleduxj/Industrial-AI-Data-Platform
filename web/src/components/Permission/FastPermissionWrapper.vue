<template>
  <div class="fast-permission-wrapper">
    <!-- 权限检查优先 - 立即显示权限提示 -->
    <PermissionEmpty
      v-if="!hasPermissionSync"
      :type="permissionType"
      :description="permissionDescription || defaultPermissionDescription"
      :permission-name="permissionName"
      :show-actions="showPermissionActions"
      :show-refresh="showRefresh"
      :show-contact="showContact"
      :show-apply="showApply"
      @refresh="handleRefresh"
      @contact="handleContact"
      @apply="handleApply"
    />

    <!-- 有权限时的内容 -->
    <div v-else class="permission-content">
      <!-- 有数据时显示内容 -->
      <div v-if="hasData" class="data-content">
        <slot :data="data" :loading="loading" />
      </div>

      <!-- 无数据时的处理 -->
      <div v-else class="empty-content">
        <!-- 加载中 -->
        <div v-if="loading" class="loading-content">
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

              <n-button v-if="showCreate" type="primary" @click="handleCreate">
                {{ createText }}
              </n-button>
            </n-space>
          </template>
        </n-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { NSpin, NEmpty, NButton, NSpace } from 'naive-ui'
import { usePermission } from '@/composables/usePermission'
import { useUserStore } from '@/store'
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
    required: true,
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
})

const emit = defineEmits(['refresh', 'contact', 'apply', 'create'])

// 权限检查和用户信息
const { hasPermission } = usePermission()
const userStore = useUserStore()

// 响应式数据
const refreshing = ref(false)

// 立即同步权限检查 - 这是关键改进
const hasPermissionSync = computed(() => {
  // 超级用户拥有所有权限
  if (userStore.isSuperUser) {
    return true
  }

  // 如果没有指定权限，默认有权限
  if (!props.permission) {
    return true
  }

  // 立即同步检查权限
  try {
    return hasPermission(props.permission)
  } catch (error) {
    console.warn('FastPermissionWrapper: 权限检查失败:', error)
    return false
  }
})

// 计算属性
const hasData = computed(() => {
  return Array.isArray(props.data) && props.data.length > 0
})

const defaultPermissionDescription = computed(() => {
  return `您没有权限查看${props.permissionName || '此内容'}`
})

// 方法
const handleRefresh = async () => {
  refreshing.value = true
  try {
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
</script>

<style scoped>
.fast-permission-wrapper {
  width: 100%;
}

.permission-content {
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
