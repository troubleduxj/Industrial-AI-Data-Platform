<template>
  <div class="permission-empty">
    <n-empty :description="description" :size="size">
      <template #icon>
        <n-icon :size="iconSize" :color="iconColor">
          <component :is="iconComponent" />
        </n-icon>
      </template>

      <template v-if="showActions" #extra>
        <n-space>
          <n-button v-if="showRefresh" :loading="refreshing" secondary @click="handleRefresh">
            刷新数据
          </n-button>

          <n-button v-if="showContact" type="primary" ghost @click="handleContact">
            联系管理员
          </n-button>

          <n-button v-if="showApply" type="primary" @click="handleApply"> 申请权限 </n-button>
        </n-space>
      </template>
    </n-empty>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { NEmpty, NIcon, NButton, NSpace } from 'naive-ui'
import {
  ShieldOutline,
  LockClosedOutline,
  WarningOutline,
  InformationCircleOutline,
} from '@vicons/ionicons5'

const props = defineProps({
  // 权限类型
  type: {
    type: String,
    default: 'permission', // permission, data, access, system
    validator: (value) => ['permission', 'data', 'access', 'system'].includes(value),
  },

  // 自定义描述
  description: {
    type: String,
    default: '',
  },

  // 大小
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large', 'huge'].includes(value),
  },

  // 显示操作按钮
  showActions: {
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

  // 权限名称（用于申请权限）
  permissionName: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['refresh', 'contact', 'apply'])

// 响应式数据
const refreshing = ref(false)

// 计算属性
const defaultDescriptions = {
  permission: '您没有权限查看此内容',
  data: '暂无数据或您没有权限查看相关数据',
  access: '访问受限，请联系管理员获取权限',
  system: '系统功能暂不可用',
}

const finalDescription = computed(() => {
  if (props.description) {
    return props.description
  }

  const baseDesc = defaultDescriptions[props.type] || defaultDescriptions.permission

  if (props.permissionName) {
    return `${baseDesc}（${props.permissionName}）`
  }

  return baseDesc
})

const iconComponent = computed(() => {
  const iconMap = {
    permission: ShieldOutline,
    data: InformationCircleOutline,
    access: LockClosedOutline,
    system: WarningOutline,
  }
  return iconMap[props.type] || ShieldOutline
})

const iconSize = computed(() => {
  const sizeMap = {
    small: 32,
    medium: 48,
    large: 64,
    huge: 80,
  }
  return sizeMap[props.size] || 48
})

const iconColor = computed(() => {
  const colorMap = {
    permission: '#f0a020',
    data: '#2080f0',
    access: '#d03050',
    system: '#f0a020',
  }
  return colorMap[props.type] || '#f0a020'
})

// 事件处理
const handleRefresh = async () => {
  refreshing.value = true
  try {
    await new Promise((resolve) => setTimeout(resolve, 1000)) // 模拟刷新延迟
    emit('refresh')
  } finally {
    refreshing.value = false
  }
}

const handleContact = () => {
  emit('contact')
  // 默认行为：显示联系方式
  window.$message?.info('请联系系统管理员获取相关权限')
}

const handleApply = () => {
  emit('apply', props.permissionName)
  // 默认行为：显示申请提示
  window.$message?.info(`已提交权限申请：${props.permissionName || '相关权限'}`)
}
</script>

<style scoped>
.permission-empty {
  padding: 40px 20px;
  text-align: center;
}

.permission-empty :deep(.n-empty) {
  justify-content: center;
}

.permission-empty :deep(.n-empty__description) {
  color: #666;
  font-size: 14px;
  margin-top: 16px;
}

.permission-empty :deep(.n-empty__extra) {
  margin-top: 20px;
}
</style>
