<template>
  <div class="asset-detail-page">
    <n-spin :show="loading">
      <!-- 资产信息卡片 -->
      <n-card class="info-card">
        <template #header>
          <div class="card-header">
            <div class="asset-title">
              <h2>{{ asset?.name || '资产详情' }}</h2>
              <n-tag :type="statusType" size="small">{{ statusText }}</n-tag>
            </div>
            <n-space>
              <n-button @click="handleEdit">
                <template #icon>
                  <n-icon :component="CreateOutline" />
                </template>
                编辑
              </n-button>
              <n-button @click="handleBack">返回列表</n-button>
            </n-space>
          </div>
        </template>

        <n-descriptions :column="3" label-placement="left" bordered>
          <n-descriptions-item label="资产编码">{{ asset?.code }}</n-descriptions-item>
          <n-descriptions-item label="资产名称">{{ asset?.name }}</n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="statusType" size="small">{{ statusText }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="位置">{{ asset?.location || '-' }}</n-descriptions-item>
          <n-descriptions-item label="制造商">{{ asset?.manufacturer || '-' }}</n-descriptions-item>
          <n-descriptions-item label="型号">{{ asset?.model || '-' }}</n-descriptions-item>
          <n-descriptions-item label="序列号">{{ asset?.serial_number || '-' }}</n-descriptions-item>
          <n-descriptions-item label="安装日期">{{ asset?.install_date || '-' }}</n-descriptions-item>
          <n-descriptions-item label="所属部门">{{ asset?.department || '-' }}</n-descriptions-item>
        </n-descriptions>
      </n-card>

      <!-- 实时数据卡片 -->
      <n-card class="data-card" title="实时数据">
        <template #header-extra>
          <n-button size="small" :loading="refreshing" @click="refreshRealtimeData">
            <template #icon>
              <n-icon :component="RefreshOutline" />
            </template>
            刷新
          </n-button>
        </template>

        <DynamicDataDisplay
          v-if="currentCategory?.id"
          :category-id="currentCategory.id"
          :signal-data="realtimeData"
          :history-data="historyData"
          :previous-data="previousData"
          default-view="cards"
          :show-mini-chart="true"
          :loading="dataLoading"
          @refresh="refreshRealtimeData"
        />
      </n-card>

      <!-- 历史数据图表 -->
      <n-card class="chart-card" title="历史趋势">
        <template #header-extra>
          <n-select
            v-model:value="timeRange"
            :options="timeRangeOptions"
            size="small"
            style="width: 120px"
            @update:value="loadHistoryData"
          />
        </template>

        <DynamicDataDisplay
          v-if="currentCategory?.id"
          :category-id="currentCategory.id"
          :signal-data="realtimeData"
          :history-data="historyData"
          default-view="charts"
          :show-view-toggle="false"
          :chart-height="250"
        />
      </n-card>
    </n-spin>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  NCard, NDescriptions, NDescriptionsItem, NButton, NSpace, NTag, 
  NIcon, NSpin, NSelect, useMessage
} from 'naive-ui'
import { CreateOutline, RefreshOutline } from '@vicons/ionicons5'
import { assetApi } from '@/api/v3/platform'
import { DynamicDataDisplay } from '@/components/platform'

const router = useRouter()
const route = useRoute()
const message = useMessage()

// 注入类别信息
const currentCategory = inject('currentCategory')
const categoryCode = inject('categoryCode')

// 状态
const loading = ref(false)
const dataLoading = ref(false)
const refreshing = ref(false)
const asset = ref(null)
const realtimeData = ref({})
const previousData = ref({})
const historyData = ref({})
const timeRange = ref('1h')

// 时间范围选项
const timeRangeOptions = [
  { label: '1小时', value: '1h' },
  { label: '6小时', value: '6h' },
  { label: '24小时', value: '24h' },
  { label: '7天', value: '7d' }
]

// 状态映射
const statusMap = {
  online: { type: 'success', text: '在线' },
  offline: { type: 'default', text: '离线' },
  error: { type: 'error', text: '故障' },
  maintenance: { type: 'warning', text: '维护中' }
}

const statusType = computed(() => statusMap[asset.value?.status]?.type || 'default')
const statusText = computed(() => statusMap[asset.value?.status]?.text || '未知')

// 自动刷新定时器
let refreshTimer = null

// 加载资产详情
async function loadAsset() {
  const assetId = route.params.id
  if (!assetId) return

  loading.value = true
  try {
    const response = await assetApi.getById(assetId)
    asset.value = response.data || response
  } catch (error) {
    message.error('加载资产详情失败')
    console.error('加载资产详情失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载实时数据
async function loadRealtimeData() {
  const assetId = route.params.id
  if (!assetId) return

  dataLoading.value = true
  try {
    const response = await assetApi.getRealtimeData(assetId)
    const data = response.data || response

    // 保存上一次数据用于趋势显示
    previousData.value = { ...realtimeData.value }
    realtimeData.value = data
  } catch (error) {
    console.error('加载实时数据失败:', error)
  } finally {
    dataLoading.value = false
  }
}

// 加载历史数据
async function loadHistoryData() {
  const assetId = route.params.id
  if (!assetId) return

  try {
    const response = await assetApi.getHistoricalData(assetId, {
      time_range: timeRange.value
    })
    const data = response.data || response

    // 按信号组织历史数据
    historyData.value = data.signals || data
  } catch (error) {
    console.error('加载历史数据失败:', error)
  }
}

// 刷新实时数据
async function refreshRealtimeData() {
  refreshing.value = true
  try {
    await loadRealtimeData()
  } finally {
    refreshing.value = false
  }
}

// 编辑资产
function handleEdit() {
  router.push(`/assets/${categoryCode.value}/${route.params.id}/edit`)
}

// 返回列表
function handleBack() {
  router.push(`/assets/${categoryCode.value}/list`)
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
  await loadAsset()
  await loadRealtimeData()
  await loadHistoryData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.asset-detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card,
.data-card,
.chart-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.asset-title h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}
</style>
