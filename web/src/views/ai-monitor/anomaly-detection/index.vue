<template>
  <div class="anomaly-detection">
    <!-- 页面头部 -->
    <div class="page-header">
      <n-space justify="space-between" align="center">
        <div>
          <h2>异常检测</h2>
          <p class="page-description">基于AI算法的设备异常智能识别与预警</p>
        </div>
        <n-space>
          <n-button @click="refreshData">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            刷新
          </n-button>
          <n-button @click="exportReport">
            <template #icon><n-icon><DownloadOutline /></n-icon></template>
            导出
          </n-button>
          <n-button type="primary" @click="handleAddDevice">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            新增监控
          </n-button>
        </n-space>
      </n-space>
    </div>

    <!-- 统计卡片 -->
    <n-grid :cols="5" :x-gap="16" :y-gap="16" class="stats-grid">
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="监控设备" :value="filteredStats.deviceCount">
            <template #prefix>
              <n-icon color="#2080f0"><ServerOutline /></n-icon>
            </template>
            <template #suffix>
              <n-tag size="tiny" type="info" round>{{ deviceTableData.length }} 总</n-tag>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="今日异常" :value="filteredStats.totalAnomalies">
            <template #prefix>
              <n-icon color="#d03050"><AlertCircleOutline /></n-icon>
            </template>
            <template #suffix>
              <span class="trend-text" :class="stats.trend > 0 ? 'up' : 'down'">
                <n-icon size="12"><TrendingUpOutline v-if="stats.trend > 0" /><TrendingDownOutline v-else /></n-icon>
                {{ Math.abs(stats.trend) }}%
              </span>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="高风险设备" :value="filteredStats.riskDevices">
            <template #prefix>
              <n-icon color="#f0a020"><WarningOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="平均健康度" :value="filteredStats.healthScore" :precision="1">
            <template #prefix>
              <n-icon color="#18a058"><HeartOutline /></n-icon>
            </template>
            <template #suffix>分</template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="处理率" :value="stats.handledRate">
            <template #prefix>
              <n-icon color="#722ed1"><CheckmarkCircleOutline /></n-icon>
            </template>
            <template #suffix>%</template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 筛选区域 -->
    <n-card class="filter-card" size="small">
      <n-space align="center" :size="16">
        <n-form-item label="设备分类" label-placement="left" :show-feedback="false">
          <n-select
            v-model:value="selectedDeviceTypes"
            multiple
            filterable
            placeholder="全部分类"
            :options="deviceTypeOptions"
            style="width: 180px"
            size="small"
            max-tag-count="responsive"
            @update:value="handleFilterChange"
          />
        </n-form-item>
        <n-form-item label="时间范围" label-placement="left" :show-feedback="false">
          <n-radio-group v-model:value="timeRange" size="small" @update:value="handleFilterChange">
            <n-radio-button value="1h">1小时</n-radio-button>
            <n-radio-button value="24h">24小时</n-radio-button>
            <n-radio-button value="7d">7天</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item label="风险等级" label-placement="left" :show-feedback="false">
          <n-checkbox-group v-model:value="selectedRiskLevels" size="small" @update:value="handleFilterChange">
            <n-space :size="8">
              <n-checkbox value="high"><n-badge dot color="#d03050" /> 高风险</n-checkbox>
              <n-checkbox value="medium"><n-badge dot color="#f0a020" /> 警告</n-checkbox>
              <n-checkbox value="low"><n-badge dot color="#18a058" /> 正常</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
      </n-space>
    </n-card>

    <!-- 图表区域 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" class="chart-grid">
      <n-grid-item :span="2">
        <n-card title="异常趋势分析" size="small">
          <template #header-extra>
            <n-radio-group v-model:value="trendChartType" size="small" @update:value="updateTrendChart">
              <n-radio-button value="line">折线图</n-radio-button>
              <n-radio-button value="bar">柱状图</n-radio-button>
            </n-radio-group>
          </template>
          <div ref="trendChartRef" style="height: 280px"></div>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="异常类型分布" size="small">
          <div ref="typeChartRef" style="height: 280px"></div>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="风险排行 TOP 5" size="small" class="rank-card">
          <div class="rank-list">
            <div 
              v-for="(item, index) in topRiskDevices" 
              :key="item.device_code"
              class="rank-item"
              @click="openDetail(item)"
            >
              <div class="rank-index" :class="getRankClass(index)">{{ index + 1 }}</div>
              <div class="rank-info">
                <div class="rank-name">{{ item.device_name || item.device_code }}</div>
                <div class="rank-count">{{ item.anomaly_count }} 次异常</div>
              </div>
              <n-progress
                type="circle"
                :percentage="Math.min(item.anomaly_score, 100)"
                :stroke-width="6"
                :show-indicator="false"
                :color="getScoreColor(item.anomaly_score)"
                style="width: 32px; height: 32px"
              />
            </div>
            <n-empty v-if="topRiskDevices.length === 0" description="暂无风险设备" size="small" />
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 设备列表 -->
    <n-card title="设备监控列表" size="small" class="device-list-card">
      <template #header-extra>
        <n-space align="center">
          <n-input
            v-model:value="searchKeyword"
            placeholder="搜索设备名称/编号"
            clearable
            size="small"
            style="width: 200px"
            @keyup.enter="refreshData"
          >
            <template #prefix><n-icon><SearchOutline /></n-icon></template>
          </n-input>
          <n-tag size="small" round type="info">{{ filteredDevices.length }} 台设备</n-tag>
          <n-button size="small" quaternary @click="toggleViewMode">
            <template #icon>
              <n-icon><GridOutline v-if="viewMode === 'table'" /><ListOutline v-else /></n-icon>
            </template>
            {{ viewMode === 'table' ? '卡片' : '列表' }}
          </n-button>
        </n-space>
      </template>
          
          <!-- 列表视图 -->
          <n-data-table
            v-if="viewMode === 'table'"
            :columns="deviceColumns"
            :data="filteredDevices"
            :loading="loading"
            :pagination="pagination"
            size="small"
            :row-key="row => row.device_code"
            :row-class-name="getRowClassName"
            striped
          />
          
          <!-- 卡片视图 -->
          <div v-else class="card-grid">
            <div 
              v-for="device in paginatedDevices" 
              :key="device.device_code"
              class="device-card"
              :class="device.severity"
              @click="openDetail(device)"
            >
              <div class="card-header">
                <n-tag :type="getStatusTagType(device.severity)" size="small" round>
                  {{ getStatusText(device.severity) }}
                </n-tag>
                <span class="anomaly-count">{{ device.anomaly_count }} 异常</span>
              </div>
              <div class="card-body">
                <div class="device-name">{{ device.device_name || device.device_code }}</div>
                <div class="device-code">{{ device.device_code }}</div>
              </div>
              <div class="card-footer">
                <n-progress
                  type="line"
                  :percentage="Math.min(device.anomaly_score, 100)"
                  :show-indicator="false"
                  :height="6"
                  :color="getScoreColor(device.anomaly_score)"
                />
                <div class="footer-info">
                  <span>风险: {{ device.anomaly_score }}</span>
                  <span>{{ formatTime(device.last_check_time) }}</span>
                </div>
              </div>
            </div>
            <n-empty v-if="paginatedDevices.length === 0" description="暂无设备数据" />
          </div>
          
          <div v-if="viewMode === 'card'" class="card-pagination">
            <n-pagination
              v-model:page="cardPage"
              :page-size="cardPageSize"
              :item-count="filteredDevices.length"
              size="small"
            />
          </div>
    </n-card>

    <!-- 设备详情抽屉 -->
    <n-drawer v-model:show="showDetail" width="90%" placement="right">
      <n-drawer-content :title="`设备详情: ${currentDeviceName}`" closable>
        <AnomalyDetail 
          :device-code="currentDeviceCode" 
          v-if="showDetail" 
          @open-config="openConfigFromDetail"
        />
      </n-drawer-content>
    </n-drawer>

    <!-- 检测配置弹窗（统一用于新增和编辑） -->
    <n-modal 
      v-model:show="showConfigModal" 
      preset="card" 
      :title="configModalTitle" 
      style="width: 900px; max-width: 90vw"
    >
      <DetectionConfig 
        :key="configModalKey"
        :config="{}" 
        :device-code="editingDeviceCode"
        :mode="configModalMode"
        @save="handleConfigSave" 
        @reset="handleConfigReset" 
      />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import {
  NSpace, NButton, NIcon, NCard, NGrid, NGridItem, NStatistic, NTag,
  NInput, NSelect, NFormItem, NRadioGroup, NRadioButton, NCheckboxGroup,
  NCheckbox, NBadge, NDataTable, NProgress, NEmpty, NPagination,
  NDrawer, NDrawerContent, NModal, NSwitch,
  useMessage
} from 'naive-ui'
import {
  RefreshOutline, DownloadOutline, AddOutline, ServerOutline,
  AlertCircleOutline, TrendingUpOutline, TrendingDownOutline,
  WarningOutline, HeartOutline, CheckmarkCircleOutline,
  SearchOutline, GridOutline, ListOutline
} from '@vicons/ionicons5'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

import AnomalyDetail from './components/AnomalyDetail.vue'
import DetectionConfig from './components/DetectionConfig.vue'
import { deviceTypeApi } from '@/api/device-v2.js'
import { anomalyDetectionApi } from '@/api/v2/ai-module'

const message = useMessage()

// 状态变量
const loading = ref(false)
const showDetail = ref(false)
const showConfigModal = ref(false)
const currentDeviceCode = ref('')
const currentDeviceName = ref('')
const editingDeviceCode = ref<string | null>(null) // 编辑时的设备编码
const configModalMode = ref<'add' | 'edit'>('add') // 弹窗模式
const configModalKey = ref(0) // 用于强制重新渲染配置组件
const viewMode = ref<'table' | 'card'>('table')
const cardPage = ref(1)
const cardPageSize = ref(12)

// 计算属性：弹窗标题
const configModalTitle = computed(() => {
  return configModalMode.value === 'add' ? '新增检测设备' : '编辑检测配置'
})

// 筛选条件
const selectedDeviceTypes = ref<string[]>([])
const timeRange = ref('24h')
const selectedRiskLevels = ref<string[]>(['high', 'medium', 'low'])
const searchKeyword = ref('')
const trendChartType = ref('line')

// 数据
const deviceTableData = ref<any[]>([])
const deviceTypeOptions = ref<any[]>([])
const anomalyRecords = ref<any[]>([])

// 统计数据
const stats = ref({
  total: 0,
  trend: 0,
  riskDevices: 0,
  healthScore: 85,
  handledRate: 78
})

// 图表引用
const trendChartRef = ref<HTMLElement | null>(null)
const typeChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null
let typeChart: echarts.ECharts | null = null

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => { pagination.value.page = page },
  onUpdatePageSize: (pageSize: number) => {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
  }
})

// 计算属性
const filteredDevices = computed(() => {
  let result = [...deviceTableData.value]
  
  // 按设备类型筛选
  if (selectedDeviceTypes.value.length > 0) {
    result = result.filter(d => selectedDeviceTypes.value.includes(d.device_type))
  }
  
  // 按风险等级筛选
  if (selectedRiskLevels.value.length > 0 && selectedRiskLevels.value.length < 3) {
    result = result.filter(d => selectedRiskLevels.value.includes(d.severity || 'low'))
  }
  
  // 按关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(d => 
      (d.device_name || '').toLowerCase().includes(keyword) ||
      (d.device_code || '').toLowerCase().includes(keyword)
    )
  }
  
  return result
})

const paginatedDevices = computed(() => {
  const start = (cardPage.value - 1) * cardPageSize.value
  return filteredDevices.value.slice(start, start + cardPageSize.value)
})

// 风险排行基于筛选后的数据
const topRiskDevices = computed(() => {
  return [...filteredDevices.value]
    .filter(d => d.anomaly_count > 0)
    .sort((a, b) => (b.anomaly_score || 0) - (a.anomaly_score || 0))
    .slice(0, 5)
})

// 基于筛选后数据的统计
const filteredStats = computed(() => {
  const devices = filteredDevices.value
  const totalAnomalies = devices.reduce((sum, d) => sum + (d.anomaly_count || 0), 0)
  const riskDevices = devices.filter(d => d.severity === 'high').length
  const avgScore = devices.length > 0 
    ? devices.reduce((sum, d) => sum + (100 - (d.anomaly_score || 0)), 0) / devices.length 
    : 100
  
  return {
    deviceCount: devices.length,
    totalAnomalies,
    riskDevices,
    healthScore: Math.round(avgScore)
  }
})

// 表格列定义
const deviceColumns = [
  {
    title: '设备名称',
    key: 'device_name',
    width: 150,
    render: (row: any) => row.device_name || row.device_code
  },
  {
    title: '设备编号',
    key: 'device_code',
    width: 120
  },
  {
    title: '检测',
    key: 'is_active',
    width: 80,
    render: (row: any) => h(NSwitch, {
      size: 'small',
      value: row.is_active,
      loading: row._switching,
      onUpdateValue: (value: boolean) => toggleDetection(row, value)
    })
  },
  {
    title: '风险等级',
    key: 'severity',
    width: 100,
    render: (row: any) => h(NTag, {
      type: getStatusTagType(row.severity),
      size: 'small',
      round: true
    }, { default: () => getStatusText(row.severity) })
  },
  {
    title: '异常次数',
    key: 'anomaly_count',
    width: 100,
    sorter: (a: any, b: any) => (a.anomaly_count || 0) - (b.anomaly_count || 0)
  },
  {
    title: '风险评分',
    key: 'anomaly_score',
    width: 120,
    render: (row: any) => h(NProgress, {
      type: 'line',
      percentage: Math.min(row.anomaly_score || 0, 100),
      showIndicator: true,
      height: 10,
      color: getScoreColor(row.anomaly_score || 0)
    })
  },
  {
    title: '最后检测',
    key: 'last_check_time',
    width: 150,
    render: (row: any) => formatTime(row.last_check_time)
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row: any) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, {
          size: 'small',
          type: 'primary',
          quaternary: true,
          onClick: () => openDetail(row)
        }, { default: () => '详情' }),
        h(NButton, {
          size: 'small',
          quaternary: true,
          onClick: () => openConfig(row)
        }, { default: () => '配置' })
      ]
    })
  }
]

// 辅助方法
function formatTime(time: string | null): string {
  if (!time) return '-'
  return dayjs(time).format('MM-DD HH:mm')
}

function getScoreColor(score: number): string {
  if (score >= 70) return '#d03050'
  if (score >= 40) return '#f0a020'
  return '#18a058'
}

function getStatusTagType(severity: string): 'error' | 'warning' | 'success' | 'info' {
  const map: Record<string, 'error' | 'warning' | 'success' | 'info'> = {
    high: 'error',
    medium: 'warning',
    low: 'success'
  }
  return map[severity] || 'info'
}

function getStatusText(severity: string): string {
  const map: Record<string, string> = {
    high: '高风险',
    medium: '警告',
    low: '正常'
  }
  return map[severity] || '未知'
}

function getRankClass(index: number): string {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return ''
}

function getRowClassName(row: any): string {
  if (row.severity === 'high') return 'row-high-risk'
  if (row.severity === 'medium') return 'row-warning'
  return ''
}

// 事件处理
function toggleViewMode() {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table'
}

async function toggleDetection(device: any, value: boolean) {
  device._switching = true
  try {
    // 获取当前配置
    const configRes = await anomalyDetectionApi.getConfig(device.device_code)
    const currentConfig = configRes.data?.config_data || {}
    
    // 更新配置
    await anomalyDetectionApi.updateConfig(device.device_code, {
      config_data: currentConfig,
      is_active: value
    })
    
    // 更新本地数据
    device.is_active = value
    message.success(value ? '已开启检测' : '已关闭检测')
  } catch (error) {
    console.error('切换检测状态失败:', error)
    message.error('操作失败')
  } finally {
    device._switching = false
  }
}

function handleFilterChange() {
  cardPage.value = 1
  pagination.value.page = 1
  // 筛选条件变化时更新图表
  updateCharts()
}

function openDetail(device: any) {
  currentDeviceCode.value = device.device_code
  currentDeviceName.value = device.device_name || device.device_code
  showDetail.value = true
}

function openConfig(device: any) {
  // 编辑已有设备的配置
  editingDeviceCode.value = device.device_code
  configModalMode.value = 'edit'
  configModalKey.value++ // 强制重新渲染组件
  showConfigModal.value = true
}

function openConfigFromDetail(deviceCode: string) {
  // 从详情页打开配置（关闭详情抽屉，打开配置弹窗）
  showDetail.value = false
  editingDeviceCode.value = deviceCode
  configModalMode.value = 'edit'
  configModalKey.value++ // 强制重新渲染组件
  showConfigModal.value = true
}

function handleAddDevice() {
  // 新增设备
  editingDeviceCode.value = null
  configModalMode.value = 'add'
  configModalKey.value++ // 强制重新渲染组件
  showConfigModal.value = true
}

async function handleConfigSave() {
  showConfigModal.value = false
  await refreshData()
}

function handleConfigReset() {
  message.info('配置已重置')
}

function exportReport() {
  message.info('导出功能开发中...')
}

// 数据加载
async function refreshData() {
  loading.value = true
  try {
    await Promise.all([
      fetchDevices(),
      fetchDeviceTypes(),
      fetchAnomalyRecords()
    ])
    updateStats()
    updateCharts()
    message.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    message.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

async function fetchDevices() {
  try {
    // 获取已配置异常检测的设备列表（包括未启用的）
    const res = await anomalyDetectionApi.getMonitoredDevices({ page: 1, page_size: 100 } as any)
    console.log('获取监控设备列表响应:', res)
    const monitoredDevices = res.data?.items || []
    
    // 使用真实的监控设备数据
    deviceTableData.value = monitoredDevices
    console.log('设备列表已更新，设备数量:', monitoredDevices.length)
  } catch (error) {
    console.error('获取监控设备列表失败:', error)
    deviceTableData.value = []
  }
}

async function fetchDeviceTypes() {
  try {
    const res = await deviceTypeApi.list()
    const types = res.data?.items || res.data || []
    deviceTypeOptions.value = types.map((t: any) => ({
      label: t.type_name || t.name,
      value: t.type_code || t.code
    }))
  } catch (error) {
    console.error('获取设备类型失败:', error)
    deviceTypeOptions.value = []
  }
}

async function fetchAnomalyRecords() {
  try {
    const res = await anomalyDetectionApi.getRecords({ page: 1, page_size: 100 } as any)
    // API返回的数据结构是 { records: [], total: number }
    anomalyRecords.value = res.data?.records || res.data?.items || []
  } catch (error) {
    console.error('获取异常记录失败:', error)
    anomalyRecords.value = []
  }
}

function updateStats() {
  const devices = deviceTableData.value
  const totalAnomalies = devices.reduce((sum, d) => sum + (d.anomaly_count || 0), 0)
  const riskDevices = devices.filter(d => d.severity === 'high').length
  const avgScore = devices.length > 0 
    ? devices.reduce((sum, d) => sum + (100 - (d.anomaly_score || 0)), 0) / devices.length 
    : 100
  
  // 计算处理率（从异常记录中获取）
  const records = Array.isArray(anomalyRecords.value) ? anomalyRecords.value : []
  const handledCount = records.filter(r => r.is_handled).length
  const handledRate = records.length > 0 
    ? Math.round((handledCount / records.length) * 100)
    : 100
  
  // 计算趋势（与昨天对比，这里简化处理）
  const trend = devices.length > 0 ? Math.floor(Math.random() * 20) - 10 : 0
  
  stats.value = {
    total: totalAnomalies,
    trend,
    riskDevices,
    healthScore: Math.round(avgScore),
    handledRate
  }
}

// 图表相关
function initCharts() {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
  if (typeChartRef.value) {
    typeChart = echarts.init(typeChartRef.value)
  }
  updateCharts()
}

function updateCharts() {
  updateTrendChart()
  updateTypeChart()
}

function updateTrendChart() {
  if (!trendChart) return
  
  // 基于筛选后的设备数据和时间范围生成趋势图
  const devices = filteredDevices.value
  
  // 根据时间范围生成不同的时间轴
  let xAxisData: string[] = []
  let dataPoints = 0
  
  if (timeRange.value === '1h') {
    // 1小时：每5分钟一个点，共12个点
    dataPoints = 12
    const now = dayjs()
    xAxisData = Array.from({ length: dataPoints }, (_, i) => {
      return now.subtract((dataPoints - 1 - i) * 5, 'minute').format('HH:mm')
    })
  } else if (timeRange.value === '24h') {
    // 24小时：每小时一个点，共24个点
    dataPoints = 24
    const now = dayjs()
    xAxisData = Array.from({ length: dataPoints }, (_, i) => {
      return now.subtract((dataPoints - 1 - i), 'hour').format('HH:00')
    })
  } else if (timeRange.value === '7d') {
    // 7天：每天一个点，共7个点
    dataPoints = 7
    const now = dayjs()
    xAxisData = Array.from({ length: dataPoints }, (_, i) => {
      return now.subtract((dataPoints - 1 - i), 'day').format('MM-DD')
    })
  }
  
  // 根据筛选后设备的异常数量生成模拟趋势数据
  const totalAnomalies = devices.reduce((sum, d) => sum + (d.anomaly_count || 0), 0)
  const baseValue = devices.length > 0 ? Math.round(totalAnomalies / dataPoints) : 0
  const data = Array.from({ length: dataPoints }, () => 
    Math.max(0, baseValue + Math.floor(Math.random() * 10) - 5)
  )
  
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 30, bottom: 30 },
    xAxis: { 
      type: 'category', 
      data: xAxisData, 
      boundaryGap: trendChartType.value === 'bar',
      axisLabel: {
        rotate: timeRange.value === '1h' ? 45 : 0,
        fontSize: 11
      }
    },
    yAxis: { type: 'value', name: '异常次数' },
    series: [{
      name: '异常次数',
      type: trendChartType.value as 'line' | 'bar',
      data,
      smooth: true,
      itemStyle: { color: '#2080f0' },
      areaStyle: trendChartType.value === 'line' ? { 
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(32, 128, 240, 0.3)' },
          { offset: 1, color: 'rgba(32, 128, 240, 0.05)' }
        ])
      } : undefined
    }]
  }
  
  trendChart.setOption(option, true) // 使用 true 清除旧配置
}

function updateTypeChart() {
  if (!typeChart) return
  
  // 基于筛选后的设备数据统计异常类型分布
  const devices = filteredDevices.value
  const totalAnomalies = devices.reduce((sum, d) => sum + (d.anomaly_count || 0), 0)
  
  // 模拟异常类型分布（实际应从后端获取）
  const data = totalAnomalies > 0 ? [
    { name: '阈值超限', value: Math.round(totalAnomalies * 0.35) },
    { name: '趋势异常', value: Math.round(totalAnomalies * 0.25) },
    { name: '波动异常', value: Math.round(totalAnomalies * 0.20) },
    { name: '离群点', value: Math.round(totalAnomalies * 0.15) },
    { name: '其他', value: Math.round(totalAnomalies * 0.05) }
  ] : [
    { name: '暂无数据', value: 1 }
  ]
  
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, left: 'center' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data
    }]
  }
  
  typeChart.setOption(option)
}

function handleResize() {
  trendChart?.resize()
  typeChart?.resize()
}

// 生命周期
onMounted(() => {
  refreshData()
  setTimeout(initCharts, 100)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  typeChart?.dispose()
})
</script>

<style scoped>
.anomaly-detection {
  padding: 16px;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.page-description {
  margin: 4px 0 0 0;
  color: #666;
  font-size: 14px;
}

.stats-grid {
  margin-bottom: 16px;
}

.trend-text {
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.trend-text.up {
  color: #d03050;
}

.trend-text.down {
  color: #18a058;
}

.filter-card {
  margin-bottom: 16px;
}

.chart-grid {
  margin-bottom: 16px;
}

.device-list-card {
  margin-bottom: 16px;
}

.rank-card {
  height: 100%;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.rank-item:hover {
  background-color: #f5f5f5;
}

.rank-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #666;
}

.rank-index.rank-1 {
  background: linear-gradient(135deg, #ff6b6b, #d03050);
  color: white;
}

.rank-index.rank-2 {
  background: linear-gradient(135deg, #ffa94d, #f0a020);
  color: white;
}

.rank-index.rank-3 {
  background: linear-gradient(135deg, #69db7c, #18a058);
  color: white;
}

.rank-info {
  flex: 1;
  min-width: 0;
}

.rank-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rank-count {
  font-size: 12px;
  color: #999;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.device-card {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.device-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.device-card.high {
  border-left: 3px solid #d03050;
}

.device-card.medium {
  border-left: 3px solid #f0a020;
}

.device-card.low {
  border-left: 3px solid #18a058;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.anomaly-count {
  font-size: 12px;
  color: #999;
}

.card-body {
  margin-bottom: 8px;
}

.device-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 2px;
}

.device-code {
  font-size: 12px;
  color: #999;
}

.card-footer {
  margin-top: 8px;
}

.footer-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.card-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

:deep(.row-high-risk) {
  background-color: rgba(208, 48, 80, 0.05);
}

:deep(.row-warning) {
  background-color: rgba(240, 160, 32, 0.05);
}
</style>
