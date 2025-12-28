<template>
  <div class="asset-monitor-page">
    <!-- 顶部工具栏 -->
    <div class="monitor-toolbar">
      <div class="toolbar-left">
        <ConnectionStatus 
          :state="connectionState" 
          :reconnect-attempts="reconnectAttempts"
          :subscribed-count="subscribedAssets.length"
          :last-connected-time="lastConnectedTime"
          :last-message-time="lastMessageTime"
          mode="compact"
          @connect="handleConnect"
          @disconnect="handleDisconnect"
        />
      </div>
      <div class="toolbar-right">
        <AlertNotification 
          ref="alertNotificationRef"
          :alerts="alerts"
          @alert-click="handleAlertClick"
        />
        <n-divider vertical />
        <n-popover trigger="click" placement="bottom-end">
          <template #trigger>
            <n-button size="small">
              <template #icon><n-icon><SettingsOutline /></n-icon></template>
              设置
            </n-button>
          </template>
          <div class="settings-panel">
            <div class="setting-item">
              <span class="setting-label">刷新频率</span>
              <n-select
                v-model:value="refreshIntervalValue"
                :options="refreshIntervalOptions"
                size="small"
                style="width: 120px"
                @update:value="handleRefreshIntervalChange"
              />
            </div>
            <div class="setting-item">
              <span class="setting-label">显示精度</span>
              <n-input-number
                v-model:value="displayPrecisionValue"
                :min="0"
                :max="6"
                size="small"
                style="width: 120px"
                @update:value="handleDisplayPrecisionChange"
              />
            </div>
            <div class="setting-item">
              <span class="setting-label">自动滚动</span>
              <n-switch v-model:value="autoScroll" size="small" />
            </div>
          </div>
        </n-popover>
      </div>
    </div>

    <n-grid :cols="24" :x-gap="16" :y-gap="16">
      <!-- 左侧资产树 -->
      <n-gi :span="6">
        <n-card title="资产列表" size="small">
          <n-input v-model:value="searchKeyword" placeholder="搜索资产" clearable style="margin-bottom: 12px;">
            <template #prefix><n-icon><SearchOutline /></n-icon></template>
          </n-input>
          <n-tree
            :data="assetTree"
            :pattern="searchKeyword"
            :show-irrelevant-nodes="false"
            selectable
            @update:selected-keys="handleSelectAsset"
          />
        </n-card>
      </n-gi>

      <!-- 右侧监控面板 -->
      <n-gi :span="18">
        <n-card v-if="selectedAsset" :title="selectedAsset.name + ' - 实时监控'" size="small">
          <template #header-extra>
            <n-space>
              <n-tag :type="statusType">{{ statusText }}</n-tag>
              <n-button size="small" @click="refreshData">
                <template #icon><n-icon><RefreshOutline /></n-icon></template>
                刷新
              </n-button>
            </n-space>
          </template>

          <!-- 信号卡片 -->
          <n-grid :cols="4" :x-gap="12" :y-gap="12">
            <n-gi v-for="signal in signals" :key="signal.id">
              <n-card size="small" :class="['signal-card', signal.alarm ? 'alarm' : '']">
                <n-statistic :label="signal.name" :value="formatSignalValue(signal.value)">
                  <template #suffix>{{ signal.unit }}</template>
                </n-statistic>
                <div class="signal-meta">
                  <span>{{ signal.updated_at }}</span>
                </div>
              </n-card>
            </n-gi>
          </n-grid>

          <!-- 实时趋势图 -->
          <RealtimeChart
            v-if="signals.length > 0"
            title="数据趋势"
            :signals="signals"
            :data="chartData"
            :is-connected="isConnected"
            :display-precision="displayPrecisionValue"
            :height="300"
            style="margin-top: 16px;"
          />

          <!-- 预测结果 -->
          <PredictionDisplay
            v-if="latestPrediction"
            title="AI预测"
            :prediction="latestPrediction"
            :prediction-history="predictionHistory"
            :is-realtime="isConnected"
            :display-precision="displayPrecisionValue"
            style="margin-top: 16px;"
            @refresh="loadPredictions"
          />
        </n-card>

        <n-empty v-else description="请选择要监控的资产" style="margin-top: 100px;" />
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
/**
 * 资产监控页面
 * 
 * 需求: 7.1 - 当打开监控页面时，前端应自动建立WebSocket连接
 * 需求: 7.2 - 当收到实时数据时，前端应更新图表和数值显示而无需刷新页面
 * 需求: 7.3 - 当预测结果产生时，前端应在监控面板中显示预测值和置信度
 * 需求: 7.4 - 当告警触发时，前端应实时显示告警通知
 * 需求: 7.5 - 前端应支持配置数据刷新频率和显示精度
 * 需求: 7.6 - 当网络断开时，前端应显示连接状态并自动重连
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { SearchOutline, RefreshOutline, SettingsOutline } from '@vicons/ionicons5'
import { platformApi } from '@/api/v3/platform'
import { useWebSocket, ConnectionState } from '@/utils/websocket'
import { RealtimeChart, AlertNotification, PredictionDisplay, ConnectionStatus } from '@/components/realtime'

const message = useMessage()

// WebSocket配置
const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v3/ws`
const {
  state: connectionState,
  isConnected,
  subscribedAssets,
  lastAssetData,
  lastAlert,
  lastPrediction,
  connect,
  disconnect,
  subscribe,
  unsubscribe,
  setRefreshInterval,
  setDisplayPrecision,
  dataHistory,
  on
} = useWebSocket(wsUrl, { debug: true })

// 状态
const searchKeyword = ref('')
const assetTree = ref([])
const selectedAsset = ref(null)
const signals = ref([])
const alerts = ref([])
const latestPrediction = ref(null)
const predictionHistory = ref([])
const chartData = ref([])
const alertNotificationRef = ref(null)

// 连接状态追踪
const reconnectAttempts = ref(0)
const lastConnectedTime = ref(null)
const lastMessageTime = ref(null)

// 设置
const refreshIntervalValue = ref(1000)
const displayPrecisionValue = ref(2)
const autoScroll = ref(true)

const refreshIntervalOptions = [
  { label: '100ms', value: 100 },
  { label: '500ms', value: 500 },
  { label: '1秒', value: 1000 },
  { label: '2秒', value: 2000 },
  { label: '5秒', value: 5000 },
  { label: '10秒', value: 10000 }
]

const statusMap = {
  normal: { text: '正常', type: 'success' },
  warning: { text: '警告', type: 'warning' },
  error: { text: '故障', type: 'error' },
  offline: { text: '离线', type: 'default' }
}

const statusType = computed(() => statusMap[selectedAsset.value?.status]?.type || 'default')
const statusText = computed(() => statusMap[selectedAsset.value?.status]?.text || '未知')

// 格式化信号值
function formatSignalValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') {
    return value.toFixed(displayPrecisionValue.value)
  }
  return String(value)
}

// 加载资产树
const loadAssetTree = async () => {
  try {
    const res = await platformApi.getAssetCategories()
    const categories = res.data || []
    
    assetTree.value = await Promise.all(categories.map(async (cat) => {
      const assetsRes = await platformApi.getAssets({ category_id: cat.id })
      return {
        key: `cat-${cat.id}`,
        label: cat.name,
        children: (assetsRes.data?.items || []).map(asset => ({
          key: `asset-${asset.id}`,
          label: asset.name,
          isLeaf: true,
          asset: asset
        }))
      }
    }))
  } catch (error) {
    message.error('加载资产树失败')
  }
}

// 选择资产
const handleSelectAsset = (keys) => {
  if (keys.length === 0) return
  const key = keys[0]
  if (key.startsWith('asset-')) {
    const findAsset = (nodes) => {
      for (const node of nodes) {
        if (node.key === key) return node.asset
        if (node.children) {
          const found = findAsset(node.children)
          if (found) return found
        }
      }
      return null
    }
    
    // 取消之前的订阅
    if (selectedAsset.value && isConnected.value) {
      unsubscribe(selectedAsset.value.id)
    }
    
    selectedAsset.value = findAsset(assetTree.value)
    
    if (selectedAsset.value) {
      loadSignals()
      loadPredictions()
      
      // 订阅新资产的实时数据
      if (isConnected.value) {
        subscribe(selectedAsset.value.id, 'all')
      }
    }
  }
}

// 加载信号数据
const loadSignals = async () => {
  if (!selectedAsset.value) return
  try {
    const res = await platformApi.getAssetRealtimeData(selectedAsset.value.id)
    signals.value = res.data || []
    updateChartData()
  } catch (error) {
    console.error('加载信号数据失败:', error)
  }
}

// 加载预测数据
const loadPredictions = async () => {
  if (!selectedAsset.value) return
  try {
    // 这里假设有预测API
    // const res = await platformApi.getAssetPredictions(selectedAsset.value.id)
    // latestPrediction.value = res.data?.latest
    // predictionHistory.value = res.data?.history || []
  } catch (error) {
    console.error('加载预测数据失败:', error)
  }
}

// 更新图表数据
const updateChartData = () => {
  if (!selectedAsset.value) return
  
  const history = dataHistory[selectedAsset.value.id] || []
  chartData.value = history.map(item => ({
    timestamp: item.timestamp,
    signals: item.data
  }))
}

// 刷新数据
const refreshData = () => {
  loadSignals()
  loadPredictions()
}

// 处理连接
const handleConnect = () => {
  const token = localStorage.getItem('token')
  connect(token)
}

// 处理断开
const handleDisconnect = () => {
  disconnect()
}

// 处理刷新频率变化
const handleRefreshIntervalChange = (value) => {
  setRefreshInterval(value)
}

// 处理显示精度变化
const handleDisplayPrecisionChange = (value) => {
  setDisplayPrecision(value)
}

// 处理告警点击
const handleAlertClick = (alert) => {
  // 可以跳转到告警详情或相关资产
  if (alert.asset_id) {
    // 选择对应资产
    handleSelectAsset([`asset-${alert.asset_id}`])
  }
}

// 监听实时数据更新
watch(lastAssetData, (newData) => {
  if (!newData || !selectedAsset.value) return
  
  if (newData.asset_id === selectedAsset.value.id) {
    lastMessageTime.value = new Date()
    
    // 更新信号值
    if (newData.data) {
      signals.value = signals.value.map(signal => {
        const newValue = newData.data[signal.code]
        if (newValue !== undefined) {
          return { ...signal, value: newValue, updated_at: newData.timestamp }
        }
        return signal
      })
    }
    
    // 更新图表数据
    updateChartData()
  }
})

// 监听告警
watch(lastAlert, (newAlert) => {
  if (newAlert && alertNotificationRef.value) {
    alertNotificationRef.value.addAlert(newAlert)
    alerts.value.push(newAlert)
  }
})

// 监听预测结果
watch(lastPrediction, (newPrediction) => {
  if (newPrediction && selectedAsset.value && newPrediction.asset_id === selectedAsset.value.id) {
    latestPrediction.value = newPrediction
    predictionHistory.value.push(newPrediction)
    
    // 限制历史长度
    if (predictionHistory.value.length > 50) {
      predictionHistory.value.shift()
    }
  }
})

// 监听连接状态变化
on('stateChange', ({ oldState, newState }) => {
  if (newState === ConnectionState.CONNECTED) {
    lastConnectedTime.value = new Date()
    reconnectAttempts.value = 0
    
    // 重新订阅当前资产
    if (selectedAsset.value) {
      subscribe(selectedAsset.value.id, 'all')
    }
  } else if (newState === ConnectionState.RECONNECTING) {
    reconnectAttempts.value++
  }
})

// 生命周期
onMounted(() => {
  loadAssetTree()
  
  // 自动连接WebSocket (需求 7.1)
  const token = localStorage.getItem('token')
  if (token) {
    connect(token)
  }
})

onUnmounted(() => {
  // 断开连接
  disconnect()
})
</script>

<style scoped>
.asset-monitor-page {
  padding: 16px;
}

.monitor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 8px 16px;
  background: var(--n-card-color);
  border-radius: 8px;
  border: 1px solid var(--n-border-color);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.settings-panel {
  padding: 8px;
  min-width: 200px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.setting-item:not(:last-child) {
  border-bottom: 1px solid var(--n-border-color);
}

.setting-label {
  font-size: 13px;
  color: var(--n-text-color-2);
}

.signal-card {
  transition: all 0.3s;
}

.signal-card.alarm {
  border-color: #f5222d;
  background: #fff1f0;
}

.signal-meta {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
</style>
