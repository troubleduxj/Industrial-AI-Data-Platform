<template>
  <div class="asset-category-menu">
    <!-- 加载状态 -->
    <n-spin :show="loading" size="small">
      <!-- 按行业分组显示 -->
      <template v-if="groupByIndustry">
        <n-menu
          :value="activeKey"
          :options="groupedMenuOptions"
          :collapsed="collapsed"
          :collapsed-width="collapsedWidth"
          :indent="indent"
          accordion
          @update:value="handleMenuSelect"
        />
      </template>

      <!-- 平铺显示 -->
      <template v-else>
        <n-menu
          :value="activeKey"
          :options="flatMenuOptions"
          :collapsed="collapsed"
          :collapsed-width="collapsedWidth"
          :indent="indent"
          @update:value="handleMenuSelect"
        />
      </template>
    </n-spin>

    <!-- 空状态 -->
    <n-empty
      v-if="!loading && categories.length === 0"
      description="暂无资产类别"
      size="small"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NMenu, NSpin, NEmpty, NIcon, NBadge } from 'naive-ui'
import { 
  CubeOutline,
  ServerOutline,
  HardwareChipOutline,
  CarOutline,
  FlashOutline,
  ConstructOutline,
  SettingsOutline
} from '@vicons/ionicons5'
import { useAssetCategories } from '../composables/useAssetCategories'

// Props
const props = defineProps({
  // 基础路径
  basePath: {
    type: String,
    default: '/assets'
  },
  // 是否按行业分组
  groupByIndustry: {
    type: Boolean,
    default: false
  },
  // 是否显示资产数量
  showCount: {
    type: Boolean,
    default: true
  },
  // 是否折叠
  collapsed: {
    type: Boolean,
    default: false
  },
  // 折叠宽度
  collapsedWidth: {
    type: Number,
    default: 64
  },
  // 缩进
  indent: {
    type: Number,
    default: 24
  }
})

// Emits
const emit = defineEmits(['select'])

const router = useRouter()
const route = useRoute()

// 使用资产类别组合式函数
const { 
  categories, 
  loading, 
  categoriesByIndustry,
  activeCategories,
  loadCategories 
} = useAssetCategories()

// 当前激活的菜单项
const activeKey = computed(() => {
  const path = route.path
  const category = activeCategories.value.find(c => 
    path.includes(`${props.basePath}/${c.code}`)
  )
  return category?.code || null
})

// 图标映射
const iconMap = {
  // 行业图标
  '制造业': ConstructOutline,
  '能源': FlashOutline,
  '交通': CarOutline,
  '电子': HardwareChipOutline,
  '通用': CubeOutline,
  // 默认图标
  default: ServerOutline
}

// 获取图标组件
function getIconComponent(category) {
  // 优先使用类别配置的图标
  if (category.icon) {
    return resolveIcon(category.icon)
  }
  // 其次使用行业图标
  if (category.industry && iconMap[category.industry]) {
    return iconMap[category.industry]
  }
  return iconMap.default
}

// 解析图标
function resolveIcon(iconName) {
  // 这里可以扩展支持更多图标库
  const iconMapping = {
    'cube': CubeOutline,
    'server': ServerOutline,
    'chip': HardwareChipOutline,
    'car': CarOutline,
    'flash': FlashOutline,
    'construct': ConstructOutline,
    'settings': SettingsOutline
  }
  return iconMapping[iconName] || CubeOutline
}

// 渲染图标
function renderIcon(icon) {
  return () => h(NIcon, { component: icon })
}

// 渲染带数量的标签
function renderLabel(category) {
  if (props.showCount && category.asset_count > 0) {
    return () => h('div', { style: { display: 'flex', alignItems: 'center', gap: '8px' } }, [
      h('span', category.name),
      h(NBadge, { 
        value: category.asset_count, 
        max: 99,
        type: 'info',
        size: 'small'
      })
    ])
  }
  return category.name
}

// 平铺菜单选项
const flatMenuOptions = computed(() => {
  return activeCategories.value.map(category => ({
    label: renderLabel(category),
    key: category.code,
    icon: renderIcon(getIconComponent(category)),
    path: `${props.basePath}/${category.code}`,
    meta: {
      categoryId: category.id,
      categoryCode: category.code,
      industry: category.industry,
      assetCount: category.asset_count
    }
  }))
})

// 分组菜单选项
const groupedMenuOptions = computed(() => {
  return categoriesByIndustry.value.map(group => ({
    label: group.name,
    key: `industry_${group.name}`,
    type: 'group',
    children: group.categories.map(category => ({
      label: renderLabel(category),
      key: category.code,
      icon: renderIcon(getIconComponent(category)),
      path: `${props.basePath}/${category.code}`,
      meta: {
        categoryId: category.id,
        categoryCode: category.code,
        industry: category.industry,
        assetCount: category.asset_count
      }
    }))
  }))
})

// 处理菜单选择
function handleMenuSelect(key, item) {
  const path = item.path || `${props.basePath}/${key}`
  
  emit('select', {
    key,
    path,
    meta: item.meta
  })

  router.push(path)
}

// 加载数据
onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.asset-category-menu {
  width: 100%;
}

:deep(.n-menu-item-content) {
  padding-right: 12px;
}

:deep(.n-badge) {
  margin-left: auto;
}
</style>
