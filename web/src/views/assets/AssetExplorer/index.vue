<template>
  <div class="asset-explorer-page">
    <div class="explorer-container">
      <!-- Left Sidebar: Asset Tree -->
      <div class="explorer-sidebar">
        <div class="sidebar-header mb-4">
          <h3 class="font-bold m-0" style="font-size: 24px; color: #333; line-height: 1.2;">资产导航</h3>
        </div>
        <AssetTree 
          :assets="allAssets" 
          :loading="loading"
          @select="handleTreeSelect"
        />
      </div>

      <!-- Main Content -->
      <div class="explorer-content">
        <!-- Top Search Bar -->
        <n-card :bordered="false" class="mb-4 search-card">
          <n-form inline :model="searchForm" label-placement="left">
            <n-form-item label="资产名称">
              <n-input v-model:value="searchForm.keyword" placeholder="输入名称或编码搜索" clearable @keyup.enter="handleSearch" />
            </n-form-item>
            <n-form-item label="状态">
              <n-select 
                v-model:value="searchForm.status" 
                :options="statusOptions" 
                placeholder="全部状态" 
                clearable 
                style="width: 120px"
              />
            </n-form-item>
            <n-form-item>
              <n-button type="primary" @click="handleSearch">
                <template #icon><n-icon :component="SearchOutline" /></template>
                搜索
              </n-button>
              <n-button class="ml-2" @click="handleReset">重置</n-button>
            </n-form-item>
          </n-form>
        </n-card>

        <!-- Asset Cards -->
        <div class="flex-1 overflow-auto">
          <n-spin :show="loading">
             <div class="mb-2 flex justify-between items-center">
                <div class="font-bold" style="font-size: 24px;">
                  {{ currentBreadcrumb }} 
                  <n-tag size="small" type="info" round class="ml-2">{{ filteredAssets.length }} 个资产</n-tag>
                </div>
                <n-space>
                   <n-button size="small" @click="refreshData">
                     <template #icon><n-icon :component="RefreshOutline" /></template>
                     刷新
                   </n-button>
                </n-space>
             </div>
             
             <AssetCards 
               :assets="filteredAssets" 
               @view="handleViewAsset"
               @monitor="handleMonitorAsset"
             />
          </n-spin>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NCard, NForm, NFormItem, 
  NInput, NSelect, NButton, NIcon, NSpin, NTag, NSpace, useMessage 
} from 'naive-ui'
import { SearchOutline, RefreshOutline } from '@vicons/ionicons5'
import { assetApi } from '@/api/v4/assets'
import AssetTree from './components/AssetTree.vue'
import AssetCards from './components/AssetCards.vue'

const router = useRouter()
const message = useMessage()

// State
const loading = ref(false)
const allAssets = ref([])
const searchForm = reactive({
  keyword: '',
  status: null
})
const selectedLocation = ref(null)

// Options
const statusOptions = [
  { label: '在线', value: 'online' },
  { label: '离线', value: 'offline' },
  { label: '故障', value: 'error' },
  { label: '维护中', value: 'maintenance' }
]

// Computed
const filteredAssets = computed(() => {
  return allAssets.value.filter(asset => {
    // 1. Filter by Tree Selection (Location)
    if (selectedLocation.value) {
      if (!asset.location || !asset.location.startsWith(selectedLocation.value)) {
        return false
      }
    }
    
    // 2. Filter by Keyword
    if (searchForm.keyword) {
      const kw = searchForm.keyword.toLowerCase()
      const nameMatch = asset.name && asset.name.toLowerCase().includes(kw)
      const codeMatch = asset.code && asset.code.toLowerCase().includes(kw)
      if (!nameMatch && !codeMatch) return false
    }
    
    // 3. Filter by Status
    if (searchForm.status && asset.status !== searchForm.status) {
      return false
    }
    
    return true
  })
})

const currentBreadcrumb = computed(() => {
    if (!selectedLocation.value) return '全部资产'
    return selectedLocation.value.split('/').join(' > ')
})

// Methods
async function loadAssets() {
  loading.value = true
  try {
    // Fetch all assets (pagination limit set high or loop if needed, assuming < 1000 for now or paging handled elsewhere)
    // For Explorer view, fetching all summary is often better for tree building
    const res = await assetApi.getList({ page: 1, page_size: 1000 })
    if (res.data) {
        // Adapt to different response structures
        if (Array.isArray(res.data)) {
            allAssets.value = res.data
        } else if (res.data.items) {
            allAssets.value = res.data.items
        } else if (res.data.data) {
            allAssets.value = res.data.data
        } else {
            allAssets.value = []
        }
    }
  } catch (error) {
    console.error('Failed to load assets:', error)
    message.error('加载资产数据失败')
  } finally {
    loading.value = false
  }
}

function handleTreeSelect(key) {
  selectedLocation.value = key
}

function handleSearch() {
  // Computed property handles filtering automatically
}

function handleReset() {
  searchForm.keyword = ''
  searchForm.status = null
  selectedLocation.value = null
}

function refreshData() {
  loadAssets()
}

function handleViewAsset(asset) {
  router.push(`/assets/${asset.category?.code || 'default'}/${asset.id}`)
}

function handleMonitorAsset(asset) {
  router.push(`/assets/${asset.category?.code || 'default'}/${asset.id}/monitor`)
}

onMounted(() => {
  loadAssets()
})
</script>

<style scoped>
.asset-explorer-page {
  height: 100%;
  width: 100%;
  background-color: #f5f7f9;
}

.explorer-container {
  display: flex;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.explorer-sidebar {
  width: 280px;
  flex-shrink: 0;
  background-color: #fff;
  border-right: 1px solid #eee;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.explorer-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
}

.search-card {
  border-radius: 4px;
}

.text-lg { font-size: 1.125rem; }
.font-bold { font-weight: 700; }
.font-medium { font-weight: 500; }
.text-base { font-size: 1rem; }
.m-0 { margin: 0; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
.ml-2 { margin-left: 0.5rem; }
.flex { display: flex; }
.flex-col { flex-direction: column; }
.flex-1 { flex: 1; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.overflow-auto { overflow: auto; }
</style>
