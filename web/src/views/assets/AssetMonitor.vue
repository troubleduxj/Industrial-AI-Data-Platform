<template>
  <div class="asset-monitor-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>{{ categoryName }}监控</h2>
        <n-tag type="info" size="small">
          {{ onlineCount }}/{{ totalCount }} 在线
        </n-tag>
      </div>
      <div class="header-right">
        <n-space>
          <n-select
            v-model:value="selectedAssets"
            :options="assetOptions"
            multiple
            placeholder="选择资产"
            clearable
            style="width: 300px"
            max-tag-count="responsive"
          />
          <n-button :loading="refreshing" @click="refreshAllData">
            <template #icon>
              <n-icon :component="RefreshOutline" />
            </template>
            刷新
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 监控网格 -->
    <n-spin :show="loading">
      <div class="monitor-grid">
        <n-card
          v-for="asset in displayAssets"
          :key="asset.id"
          class="asset-monitor-card"
          :class="{ 'asset-offline': asset.status === 'offline', 'asset-error': asset.status === 'error' }"
          hoverable
          @click="handleAssetClick(asset)"
        >
          <template #header>
            <div class="asset-header">
              <span class="asset-name">{{ asset.name }}</span>
              <n-tag :type="getStatusType(asset.status)" size="small">
                {{ getStatusText(asset.status) }}
              </n-tag>
            </div>
          </template>

          <div class="asset-signals">
            <div
              v-for="signal in getAssetSignals(asset)"
              :key="signal.code"
              class="signal-item"
              :class="getSignalClass(signal, asset)"
            >
              <span class="signal-label">{{ signal.name }}</span>
              <span class="signal-value">
                {{ formatSignalValue(signal, asset) }}
                <span v-if="signal.unit" class="signal-unit">{{ signal.unit }}</span>
              </span>
            </div>
          </div>

          <template #footer>
            <div class="asset-footer">
              <span class="asset-location">{{ asset.location || '-' }}</span>
              <span class="update-time">{{ formatUpdateTime(asset.last_update) }}</span>
            </div>
          </template>
        </n-card>
      </div>

      <!-- 空状态 -->
      <n-empty
        v-if="!loading && displayAssets.length === 0"
        description="暂无监控数据"
        class="empty-state"
      />
    </n-spin>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NTag, NButton, NSpace, NSelect, NIcon, NSpin, NEmpty, useMessage } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import { assetApi } from '@/api/v4'
import { useSignalDefinitions } from '@/components/platform/composables/useSignalDefinitions'

const router = useRouter()
const message = useMessage()

// 注入类别信息
const currentCategory = inject('currentCategory')
const categoryCode = inject('categoryCode')

// 类别名称
const categoryName = computed(() => currentCategory.value?.name || '资产')

// 使用信号定义
const { signals, realtimeSignals, formatSignalValue: formatValue } = useSignalDefinitions(currentCategory.value?.id)

// 状态
const loading = ref(false)
const refreshing = ref(false)
const assets = ref([])
const realtimeDataMap = ref({})
const selectedAssets = ref([])

// 自动刷新定时器
let refreshTimer = null

// 资产选项
const assetOptions = computed(() => {
  return assets.value.map(asset => ({
    label: asset.name,
    value: asset.id
  }))
})

// 显示的资产
const displayAssets = computed(() => {
  if (selectedAssets.value.length === 0) {
    return assets.value
  }
  return assets.value.filter(asset => selectedAssets.value.includes(asset.id))
})

// 统计
const totalCount = computed(() => assets.value.length)
const onlineCount = computed(() => assets.value.filter(a => a.status === 'online').length)

// 状态映射
const statusMap = {
  online: { type: 'success', text: '在线' },
  offline: { type: 'default', text: '离线' },
  error: { type: 'error', text: '故障' },
  maintenance: { type: 'warning', text: '维护中' }
}

function getStatusType(status) {
  return statusMap[status]?.type || 'default'
}

function getStatusText(status) {
  return statusMap[status]?.text || '未知'
}

// 获取资产的信号数据
function getAssetSignals(asset) {
  // 只显示实时监控信号，最多5个
  return realtimeSignals.value.slice(0, 5)
}

// 格式化信号值
function formatSignalValue(signal, asset) {
  const data = realtimeDataMap.value[asset.id]
  if (!data) return '-'
  
  const value = data[signal.code]
  if (value === null || value === undefined) return '-'

  switch (signal.data_type) {
    case 'float':
    case 'double':
      return typeof value === 'number' ? value.toFixed(2) : String(value)
    case 'int':
    case 'bigint':
      return String(Math.round(Number(value)))
    case 'bool':
    case 'boolean':
      return value ? '开启' : '关闭'
    default:
      return String(value)
  }
}

// 获取信号样式类
function getSignalClass(signal, asset) {
  const data = realtimeDataMap.value[asset.id]
  if (!data || !signal.value_range) return ''

  const value = data[signal.code]
  if (value === null || value === undefined) return ''

  const { min, max } = signal.value_range
  if ((min !== undefined && value < min) || (max !== undefined && value > max)) {
    return 'signal-error'
  }

  if (min !== undefined && max !== undefined) {
    const range = max - min
    const warningLow = min + range * 0.1
    const warningHigh = max - range * 0.1
    if (value <= warningLow || value >= warningHigh) {
      return 'signal-warning'
    }
  }

  return 'signal-normal'
}

// 格式化更新时间
function formatUpdateTime(time) {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// 加载资产列表
async function loadAssets() {
  if (!currentCategory.value?.id) return

  loading.value = true
  try {
    const response = await assetApi.getList({
      category_id: currentCategory.value.id,
      page_size: 100
    })

    const data = response.data || response
    assets.value = data.items || data.assets || []
  } catch (error) {
    message.error('加载资产列表失败')
    console.error('加载资产列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载实时数据
async function loadRealtimeData() {
  if (assets.value.length === 0) return

  try {
    const assetIds = assets.value.map(a => a.id)
    const response = await assetApi.getBatchRealtimeData(assetIds)
    const data = response.data || response

    // 更新实时数据映射
    if (Array.isArray(data)) {
      data.forEach(item => {
        realtimeDataMap.value[item.asset_id] = item.data
      })
    } else if (typeof data === 'object') {
      realtimeDataMap.value = data
    }
  } catch (error) {
    console.error('加载实时数据失败:', error)
  }
}

// 刷新所有数据
async function refreshAllData() {
  refreshing.value = true
  try {
    await loadRealtimeData()
  } finally {
    refreshing.value = false
  }
}

// 点击资产卡片
function handleAssetClick(asset) {
  router.push(`/assets/${categoryCode.value}/${asset.id}`)
}

// 开始自动刷新
function startAutoRefresh() {
  refreshTimer = setInterval(() => {
    loadRealtimeData()
  }, 5000)
}

// 停止自动刷新
function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 生命周期
onMounted(async () => {
  await loadAssets()
  await loadRealtimeData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.asset-monitor-page {
  height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.monitor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.asset-monitor-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.asset-monitor-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.asset-offline {
  opacity: 0.7;
}

.asset-error {
  border-color: #d03050;
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-name {
  font-weight: 600;
  font-size: 14px;
}

.asset-signals {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.signal-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  background: var(--n-color-embedded);
}

.signal-normal {
  border-left: 3px solid #18a058;
}

.signal-warning {
  border-left: 3px solid #f0a020;
  background: rgba(240, 160, 32, 0.1);
}

.signal-error {
  border-left: 3px solid #d03050;
  background: rgba(208, 48, 80, 0.1);
}

.signal-label {
  font-size: 12px;
  color: var(--n-text-color-3);
}

.signal-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color);
}

.signal-unit {
  font-size: 11px;
  color: var(--n-text-color-3);
  font-weight: normal;
  margin-left: 2px;
}

.asset-footer {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--n-text-color-3);
}

.empty-state {
  margin-top: 100px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .monitor-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>
