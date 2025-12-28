<template>
  <n-breadcrumb class="dynamic-breadcrumb" :separator="separator">
    <n-breadcrumb-item
      v-for="(item, index) in breadcrumbItems"
      :key="index"
      :clickable="item.path !== null && index < breadcrumbItems.length - 1"
      @click="handleClick(item, index)"
    >
      <template v-if="item.icon" #default>
        <div class="breadcrumb-item-content">
          <n-icon :component="item.icon" :size="16" />
          <span>{{ item.title }}</span>
        </div>
      </template>
      <template v-else>
        {{ item.title }}
      </template>
    </n-breadcrumb-item>
  </n-breadcrumb>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NBreadcrumb, NBreadcrumbItem, NIcon } from 'naive-ui'
import { 
  HomeOutline, 
  CubeOutline, 
  ServerOutline,
  SettingsOutline
} from '@vicons/ionicons5'
import { useAssetCategories } from '../composables/useAssetCategories'

// Props
const props = defineProps({
  // 自定义面包屑项
  items: {
    type: Array,
    default: null
  },
  // 是否显示首页
  showHome: {
    type: Boolean,
    default: true
  },
  // 首页路径
  homePath: {
    type: String,
    default: '/'
  },
  // 首页标题
  homeTitle: {
    type: String,
    default: '首页'
  },
  // 分隔符
  separator: {
    type: String,
    default: '/'
  },
  // 资产类别编码（用于自动生成）
  categoryCode: {
    type: String,
    default: null
  },
  // 资产名称
  assetName: {
    type: String,
    default: null
  }
})

// Emits
const emit = defineEmits(['click'])

const router = useRouter()
const route = useRoute()

// 使用资产类别组合式函数
const { categories, generateBreadcrumb, loadCategories } = useAssetCategories()

// 面包屑项
const breadcrumbItems = computed(() => {
  // 如果提供了自定义项，直接使用
  if (props.items) {
    return addHomeItem(props.items)
  }

  // 如果提供了类别编码，自动生成
  if (props.categoryCode) {
    const items = generateBreadcrumb(props.categoryCode, props.assetName)
    return addHomeItem(items)
  }

  // 根据路由自动生成
  return generateFromRoute()
})

// 添加首页项
function addHomeItem(items) {
  if (!props.showHome) return items

  const homeItem = {
    title: props.homeTitle,
    path: props.homePath,
    icon: HomeOutline
  }

  return [homeItem, ...items]
}

// 根据路由生成面包屑
function generateFromRoute() {
  const items = []

  // 添加首页
  if (props.showHome) {
    items.push({
      title: props.homeTitle,
      path: props.homePath,
      icon: HomeOutline
    })
  }

  // 解析路由
  const matched = route.matched
  matched.forEach((record, index) => {
    // 跳过根路由
    if (record.path === '/') return

    const meta = record.meta || {}
    
    // 检查是否是资产类别路由
    if (meta.categoryCode) {
      const category = categories.value.find(c => c.code === meta.categoryCode)
      if (category) {
        items.push({
          title: category.name,
          path: record.path,
          icon: CubeOutline
        })
      }
    } else if (meta.title) {
      items.push({
        title: meta.title,
        path: index < matched.length - 1 ? record.path : null,
        icon: getRouteIcon(meta)
      })
    }
  })

  // 添加资产名称（如果有）
  if (props.assetName) {
    items.push({
      title: props.assetName,
      path: null,
      icon: ServerOutline
    })
  }

  return items
}

// 获取路由图标
function getRouteIcon(meta) {
  if (meta.icon) {
    // 这里可以扩展图标映射
    const iconMap = {
      'home': HomeOutline,
      'cube': CubeOutline,
      'server': ServerOutline,
      'settings': SettingsOutline
    }
    return iconMap[meta.icon] || null
  }
  return null
}

// 处理点击
function handleClick(item, index) {
  if (item.path && index < breadcrumbItems.value.length - 1) {
    emit('click', item)
    router.push(item.path)
  }
}

// 加载类别数据
watch(() => props.categoryCode, () => {
  if (props.categoryCode && categories.value.length === 0) {
    loadCategories()
  }
}, { immediate: true })
</script>

<style scoped>
.dynamic-breadcrumb {
  padding: 8px 0;
}

.breadcrumb-item-content {
  display: flex;
  align-items: center;
  gap: 4px;
}

:deep(.n-breadcrumb-item:last-child) {
  font-weight: 600;
  color: var(--n-text-color);
}

:deep(.n-breadcrumb-item:not(:last-child)) {
  cursor: pointer;
}

:deep(.n-breadcrumb-item:not(:last-child):hover) {
  color: var(--primary-color);
}
</style>
