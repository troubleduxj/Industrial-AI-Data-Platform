<template>
  <div class="asset-layout">
    <!-- 面包屑导航 -->
    <DynamicBreadcrumb
      :category-code="categoryCode"
      :asset-name="assetName"
      class="asset-breadcrumb"
    />

    <!-- 页面内容 -->
    <div class="asset-content">
      <router-view v-slot="{ Component }">
        <keep-alive :include="keepAliveComponents">
          <component :is="Component" :key="route.fullPath" />
        </keep-alive>
      </router-view>
    </div>
  </div>
</template>

<script setup>
import { computed, provide } from 'vue'
import { useRoute } from 'vue-router'
import { DynamicBreadcrumb } from '@/components/platform'
import { useAssetCategoryStore } from '@/store/modules/assetCategory'

const route = useRoute()
const assetCategoryStore = useAssetCategoryStore()

// 当前类别编码
const categoryCode = computed(() => route.meta?.categoryCode || route.params?.categoryCode)

// 当前资产名称（用于详情页面包屑）
const assetName = computed(() => route.meta?.assetName || null)

// 当前类别
const currentCategory = computed(() => {
  if (categoryCode.value) {
    return assetCategoryStore.getCategoryByCode(categoryCode.value)
  }
  return null
})

// 需要缓存的组件
const keepAliveComponents = computed(() => {
  const components = []
  if (route.meta?.keepAlive) {
    components.push(route.name)
  }
  return components
})

// 提供类别信息给子组件
provide('currentCategory', currentCategory)
provide('categoryCode', categoryCode)
</script>

<style scoped>
.asset-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.asset-breadcrumb {
  padding: 12px 16px;
  background: var(--n-card-color);
  border-bottom: 1px solid var(--n-border-color);
}

.asset-content {
  flex: 1;
  overflow: auto;
  padding: 16px;
}
</style>
