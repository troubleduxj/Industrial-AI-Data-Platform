<template>
  <CommonPage show-footer title="在线率统计">
    <template #action>
      <div class="flex items-center justify-end">
        <!-- 视图切换 -->
        <ViewToggle
          v-model="viewMode"
          :options="viewOptions"
          size="small"
          :show-label="false"
          :icon-size="16"
          align="right"
        />
      </div>
    </template>

    <!-- 查询条件 -->
    <NCard class="mb-15" rounded-10>
      <div class="query-container">
        <div
          class="query-items"
          style="display: flex; gap: 20px; flex-wrap: wrap; align-items: center"
        >
          <!-- 设备类型选择 -->
          <QueryBarItem label="设备类型" :label-width="70" style="flex: 1; min-width: 200px">
            <NSelect
              v-model:value="filterType"
              :options="deviceTypeOptions"
              placeholder="全部类型"
              clearable
              style="width: 100%"
            />
          </QueryBarItem>

          <!-- 设备组选择 -->
          <QueryBarItem label="设备组" :label-width="60" style="flex: 1; min-width: 200px">
            <NSelect
              v-model:value="selectedGroup"
              :options="groupOptions"
              placeholder="全部设备组"
              clearable
              style="width: 100%"
            />
          </QueryBarItem>

          <!-- 时间范围选择 -->
          <QueryBarItem label="时间范围" :label-width="80" style="flex: 1; min-width: 280px">
            <NDatePicker
              v-model:value="dateRange"
              type="daterange"
              clearable
              format="yyyy-MM-dd"
              :default-value="[new Date(Date.now() - 6 * 24 * 60 * 60 * 1000), new Date()]"
              style="width: 100%"
            />
          </QueryBarItem>
        </div>

        <div class="query-actions">
          <!-- 查询按钮 -->
          <NButton type="primary" @click="handleQuery">
            <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />
            查询
          </NButton>

          <!-- 重置按钮 -->
          <NButton @click="handleReset">
            <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />
            重置
          </NButton>
        </div>
      </div>
    </NCard>

    <!-- 统计卡片 -->
    <div class="statistics-cards mb-20">
      <NCard class="stat-card">
        <div class="stat-content">
          <div class="stat-icon online">
            <TheIcon icon="material-symbols:schedule" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overallStats.totalOnlineTime }}h</div>
            <div class="stat-label">在线总时长</div>
          </div>
          <NTooltip trigger="hover">
            <template #trigger>
              <n-icon size="18" class="info-icon" cursor-pointer>
                <icon-mdi:information-outline />
              </n-icon>
            </template>
            在线总时长 = 焊接时间 + 待机时间 + 报警时间
          </NTooltip>
        </div>
      </NCard>

      <NCard class="stat-card">
        <div class="stat-content">
          <div class="stat-icon welding">
            <TheIcon icon="material-symbols:signal-wifi-4-bar" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overallStats.avgOnlineRate }}%</div>
            <div class="stat-label">平均在线率</div>
          </div>
          <NTooltip trigger="hover">
            <template #trigger>
              <n-icon size="18" class="info-icon" cursor-pointer>
                <icon-mdi:information-outline />
              </n-icon>
            </template>
            平均在线率 = (在线时间 / 总时间) × 100%
          </NTooltip>
        </div>
      </NCard>

      <NCard class="stat-card">
        <div class="stat-content">
          <div class="stat-icon devices">
            <TheIcon icon="material-symbols:developer-board" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overallStats.totalDevices }}</div>
            <div class="stat-label">设备总数</div>
          </div>
          <NTooltip trigger="hover">
            <template #trigger>
              <n-icon size="18" class="info-icon" cursor-pointer>
                <icon-mdi:information-outline />
              </n-icon>
            </template>
            设备总数 = 焊接设备数 + 待机设备数 + 报警设备数 + 关机设备数
          </NTooltip>
        </div>
      </NCard>

      <NCard class="stat-card">
        <div class="stat-content">
          <div class="stat-icon efficiency">
            <TheIcon icon="material-symbols:speed" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overallStats.efficiency }}%</div>
            <div class="stat-label">设备利用率</div>
          </div>
          <NTooltip trigger="hover">
            <template #trigger>
              <n-icon size="18" class="info-icon" cursor-pointer>
                <icon-mdi:information-outline />
              </n-icon>
            </template>
            设备利用率 = (焊接时间 + 待机时间) / 总时间 × 100%
          </NTooltip>
        </div>
      </NCard>
    </div>

    <!-- 图表视图 -->
    <div v-if="viewMode === 'chart'" class="chart-container">
      <NCard title="在线率与焊接率趋势">
        <div ref="chartRef" class="chart" style="height: 400px"></div>
      </NCard>
    </div>

    <!-- 表格视图 -->
    <div v-else-if="viewMode === 'table'">
      <NCard title="在线率统计数据">
        <NDataTable
          v-permission="{ action: 'read', resource: 'online_rate_statistics' }"
          :columns="tableColumns"
          :data="statisticsData"
          :pagination="pagination"
          :loading="loading"
          striped
          size="medium"
        />
      </NCard>
    </div>
  </CommonPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, reactive, type Ref } from 'vue'
import {
  NButton,
  NCard,
  NSelect,
  NDatePicker,
  NDataTable,
  NTooltip,
  NIcon,
  useMessage,
  type SelectOption,
  type DataTableColumns,
} from 'naive-ui'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import ViewToggle from '@/components/common/ViewToggle.vue'

import { formatDate } from '@/utils'
import statisticsV2Api from '@/api/statistics-v2'
import deviceV2Api from '@/api/device-v2'

defineOptions({ name: '在线率统计' })

// ==================== 类型定义 ====================

interface DeviceType {
  type_code: string
  type_name: string
}

interface OnlineRateData {
  date: string
  online_rate: number
  total_devices: number
  online_devices: number
  [key: string]: any
}

interface StatisticsCard {
  avgOnlineRate: number
  maxOnlineRate: number
  minOnlineRate: number
  avgDevices: number
}

type ViewMode = 'chart' | 'table'

// 消息提示
const message = useMessage()

// 响应式数据
const loading = ref<boolean>(false)
const viewMode = ref<ViewMode>('chart')
const filterType = ref<string>('welding') // 设备类型筛选，默认选择焊接设备
const deviceTypes = ref<DeviceType[]>([]) // 设备类型列表

// 视图切换选项
const viewOptions: SelectOption[] = [
  {
    value: 'chart',
    label: '图表视图',
    icon: 'material-symbols:analytics',
  },
  {
    value: 'table',
    label: '表格视图',
    icon: 'material-symbols:table-chart',
  },
]
const today = new Date()
const yesterdayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1, 0, 0, 0)
const yesterdayEnd = new Date(
  today.getFullYear(),
  today.getMonth(),
  today.getDate() - 1,
  23,
  59,
  59
)
const dateRange = ref<[number, number]>([yesterdayStart.getTime(), yesterdayEnd.getTime()])
const selectedGroup = ref<string | null>(null)
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: ECharts | null = null

// 设备类型选项
const deviceTypeOptions = computed(() => {
  const options = [{ label: '全部设备', value: null }]

  if (deviceTypes.value.length === 0) {
    // 降级处理：使用默认选项
    options.push(
      { label: '焊机', value: 'welding' },
      { label: '切割设备', value: 'cutting' },
      { label: '装配设备', value: 'assembly' }
    )
  } else {
    // 使用API获取的数据
    deviceTypes.value.forEach((type) => {
      options.push({
        label: type.type_name,
        value: type.type_code,
      })
    })
  }

  return options
})

// 设备组选项
const groupOptions = [
  { label: '生产车间A', value: 'workshop_a' },
  { label: '生产车间B', value: 'workshop_b' },
  { label: '生产车间C', value: 'workshop_c' },
  { label: '测试区域', value: 'test_area' },
]

// 模拟统计数据
const statisticsData = ref([])

// 总体统计
const overallStats = computed(() => {
  if (statisticsData.value.length === 0) {
    return {
      totalOnlineTime: 0,
      avgOnlineRate: 0,
      totalDevices: 0,
      efficiency: 0,
    }
  }

  // 计算平均在线率
  const totalOnlineRate = statisticsData.value.reduce(
    (sum, item) => sum + (item.onlineRate || 0),
    0
  )
  const avgOnlineRate = (totalOnlineRate / statisticsData.value.length).toFixed(1)

  // 计算在线总时长（基于在线设备数和天数）
  const totalOnlineTime = statisticsData.value.reduce((sum, item) => {
    // 每个在线设备每天按24小时计算
    return sum + (item.onlineDevices || 0) * 24
  }, 0)

  // 获取设备总数（从统计数据中取最大值或从设备类型API获取）
  let totalDevices = 0
  if (statisticsData.value.length > 0) {
    // 从统计数据中获取设备总数（取最大值）
    totalDevices = Math.max(...statisticsData.value.map((item) => item.totalDevices || 0))
  }

  // 如果统计数据中没有设备总数，从设备类型API获取
  if (totalDevices === 0) {
    if (filterType.value && deviceTypes.value.length > 0) {
      // 从设备类型API数据中获取device_count
      const selectedDeviceType = deviceTypes.value.find(
        (type) => type.type_code === filterType.value
      )
      totalDevices = selectedDeviceType?.device_count || 0
    } else if (deviceTypes.value.length > 0) {
      // 如果没有选择特定类型，计算所有设备类型的总数
      totalDevices = deviceTypes.value.reduce((sum, type) => sum + (type.device_count || 0), 0)
    }
  }

  // 设备利用率 = 平均在线率（已经是百分比）
  const efficiency = parseFloat(avgOnlineRate)

  return {
    totalOnlineTime: Math.round(totalOnlineTime),
    avgOnlineRate: parseFloat(avgOnlineRate),
    totalDevices,
    efficiency: efficiency.toFixed(1),
  }
})

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true,
  itemCount: 0,
})

// 表格列配置
const tableColumns = [
  {
    title: '日期',
    key: 'date',
    width: 120,
    render: (row) => {
      const daysDiff = dateRange.value
        ? Math.floor((dateRange.value[1] - dateRange.value[0]) / (24 * 60 * 60 * 1000)) + 1
        : 1
      const isHourlyView = daysDiff <= 3
      return formatDate(row.date, isHourlyView ? 'MM-DD HH:mm' : 'YYYY-MM-DD')
    },
  },
  {
    title: '焊接时长',
    key: 'weldingDuration',
    width: 100,
    render: (row) => `${row.weldingDuration}h`,
  },
  {
    title: '待机时长',
    key: 'standbyDuration',
    width: 100,
    render: (row) => `${row.standbyDuration}h`,
  },
  {
    title: '报警时长',
    key: 'alarmDuration',
    width: 100,
    render: (row) => `${row.alarmDuration}h`,
  },
  {
    title: '关机时长',
    key: 'offlineDuration',
    width: 100,
    render: (row) => `${row.offlineDuration}h`,
  },
  {
    title: '在线时长',
    key: 'onlineDuration',
    width: 100,
    render: (row) => `${row.onlineDuration}h`,
  },
  {
    title: '在线率',
    key: 'onlineRate',
    width: 100,
    render: (row) => `${row.onlineRate}%`,
  },
  {
    title: '利用率',
    key: 'utilizationRate',
    width: 100,
    render: (row) => `${row.utilizationRate}%`,
  },
]

/**
 * 生成模拟数据
 */
function generateMockData() {
  const data = []

  // 根据设备类型调整设备总数
  let totalDevices = 25
  if (filterType.value && deviceTypes.value.length > 0) {
    // 从设备类型API数据中获取device_count
    const selectedDeviceType = deviceTypes.value.find((type) => type.type_code === filterType.value)
    totalDevices = selectedDeviceType?.device_count || 25
  } else if (deviceTypes.value.length > 0) {
    // 如果没有选择特定类型，使用所有设备类型的总数
    totalDevices = deviceTypes.value.reduce((sum, type) => sum + (type.device_count || 0), 0) || 25
  }

  // 判断时间范围：小于等于3天显示按小时数据，大于3天显示按天数据
  const startDate = new Date(dateRange.value[0])
  const endDate = new Date(dateRange.value[1])
  // 计算实际天数差（包含结束日期）
  const daysDiff = Math.floor((endDate - startDate) / (24 * 60 * 60 * 1000)) + 1
  const isHourlyView = daysDiff <= 3

  if (isHourlyView) {
    // 小于等于3天：生成按小时的数据
    const totalHours = daysDiff * 24

    for (let hour = 0; hour < totalHours; hour++) {
      const hourDate = new Date(startDate.getTime() + hour * 60 * 60 * 1000)

      // 生成各种时长数据（小时为单位）
      const weldingDuration = parseFloat((0.3 + Math.random() * 0.4).toFixed(1)) // 0.3-0.7小时
      const standbyDuration = parseFloat((0.2 + Math.random() * 0.3).toFixed(1)) // 0.2-0.5小时
      const alarmDuration = parseFloat((Math.random() * 0.1).toFixed(1)) // 0-0.1小时
      const offlineDuration = parseFloat((Math.random() * 0.2).toFixed(1)) // 0-0.2小时
      const onlineDuration = parseFloat(
        (weldingDuration + standbyDuration + alarmDuration).toFixed(1)
      )

      // 计算比率
      const onlineRate = parseFloat(((onlineDuration / 1.0) * 100).toFixed(1)) // 基于1小时计算
      const utilizationRate = parseFloat(((weldingDuration / onlineDuration) * 100).toFixed(1))

      data.push({
        date: hourDate.getTime(),
        weldingDuration,
        standbyDuration,
        alarmDuration,
        offlineDuration,
        onlineDuration,
        onlineRate: Math.min(onlineRate, 100), // 确保不超过100%
        utilizationRate: isNaN(utilizationRate) ? 0 : Math.min(utilizationRate, 100),
        weldingRate: utilizationRate, // 保留用于图表显示
      })
    }
  } else {
    // 大于3天：生成按天的数据
    for (let i = 0; i < daysDiff; i++) {
      const date = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000)

      // 生成各种时长数据（小时为单位，按天计算）
      const weldingDuration = parseFloat((6 + Math.random() * 4).toFixed(1)) // 6-10小时
      const standbyDuration = parseFloat((4 + Math.random() * 3).toFixed(1)) // 4-7小时
      const alarmDuration = parseFloat((Math.random() * 2).toFixed(1)) // 0-2小时
      const offlineDuration = parseFloat((Math.random() * 4).toFixed(1)) // 0-4小时
      const onlineDuration = parseFloat(
        (weldingDuration + standbyDuration + alarmDuration).toFixed(1)
      )

      // 计算比率
      const onlineRate = parseFloat(((onlineDuration / 24.0) * 100).toFixed(1)) // 基于24小时计算
      const utilizationRate = parseFloat(((weldingDuration / onlineDuration) * 100).toFixed(1))

      data.push({
        date: date.getTime(),
        weldingDuration,
        standbyDuration,
        alarmDuration,
        offlineDuration,
        onlineDuration,
        onlineRate: Math.min(onlineRate, 100), // 确保不超过100%
        utilizationRate: isNaN(utilizationRate) ? 0 : Math.min(utilizationRate, 100),
        weldingRate: utilizationRate, // 保留用于图表显示
      })
    }
  }

  return data
}

/**
 * 初始化图表
 */
function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  // 判断时间范围：小于等于3天显示按小时数据，大于3天显示按天数据
  const daysDiff = dateRange.value
    ? Math.floor((dateRange.value[1] - dateRange.value[0]) / (24 * 60 * 60 * 1000)) + 1
    : 1
  const isHourlyView = daysDiff <= 3

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
      formatter: function (params) {
        const timeFormat = isHourlyView ? 'HH:mm' : 'MM-DD'
        let result = `${formatDate(params[0].data[0], timeFormat)}<br/>`
        params.forEach((param) => {
          result += `${param.seriesName}: ${param.data[1]}%<br/>`
        })
        return result
      },
    },
    legend: {
      data: isHourlyView ? ['在线率', '设备利用率'] : ['在线率', '焊接率'],
      top: 10,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
      axisLabel: {
        formatter: function (value) {
          return formatDate(value, isHourlyView ? 'HH:mm' : 'MM-DD')
        },
      },
    },
    yAxis: {
      type: 'value',
      name: '百分比(%)',
      min: 0,
      max: 100,
      axisLabel: {
        formatter: '{value}%',
      },
    },
    series: [
      {
        name: '在线率',
        type: 'line',
        data: statisticsData.value.map((item) => [item.date, item.onlineRate]),
        smooth: true,
        lineStyle: {
          color: '#1890ff',
          width: 3,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.1)' },
            ],
          },
        },
      },
      {
        name: isHourlyView ? '设备利用率' : '焊接率',
        type: 'line',
        data: statisticsData.value.map((item) => [item.date, item.weldingRate]),
        smooth: true,
        lineStyle: {
          color: '#52c41a',
          width: 3,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
              { offset: 1, color: 'rgba(82, 196, 26, 0.1)' },
            ],
          },
        },
      },
    ],
  }

  chartInstance.setOption(option)
}

/**
 * 加载设备类型列表
 */
async function loadDeviceTypes() {
  try {
    const response = await deviceV2Api.deviceTypes.list()
    if (response.data) {
      deviceTypes.value = response.data
    }
  } catch (err) {
    console.error('获取设备类型失败:', err)

    // 提供更详细的错误信息
    let errorMsg = '获取设备类型失败'
    if (err.code === 'ECONNABORTED') {
      errorMsg = '连接超时，请检查网络连接或联系管理员'
    } else if (err.message) {
      errorMsg = `获取设备类型失败: ${err.message}`
    }

    message.warning(errorMsg)

    // 使用默认类型选项作为降级处理
    deviceTypes.value = [
      { type_code: 'welding', type_name: '焊机' },
      { type_code: 'cutting', type_name: '切割设备' },
      { type_code: 'assembly', type_name: '装配设备' },
    ]
  }
}

/**
 * 处理查询
 */
async function handleQuery() {
  loading.value = true

  try {
    // 构建查询参数
    const params = {
      device_type: filterType.value,
      device_group: selectedGroup.value,
      start_date: dateRange.value ? formatDate(dateRange.value[0], 'YYYY-MM-DD') : null,
      end_date: dateRange.value ? formatDate(dateRange.value[1], 'YYYY-MM-DD') : null,
    }

    // 调用真实API
    const response = await statisticsV2Api.getOnlineRateStatistics(params)

    if (response.data && Array.isArray(response.data)) {
      statisticsData.value = response.data
      pagination.itemCount = statisticsData.value.length

      if (viewMode.value === 'chart') {
        nextTick(() => {
          initChart()
        })
      }

      message.success('查询完成')
    } else {
      message.warning('未获取到数据')
      // 如果没有数据，清空统计数据
      statisticsData.value = []
      pagination.itemCount = 0
    }
  } catch (err) {
    console.error('查询在线率统计失败:', err)

    // 提供详细的错误信息
    let errorMsg = '查询失败'
    if (err.code === 'ECONNABORTED') {
      errorMsg = '连接超时，请检查网络连接或联系管理员'
    } else if (err.response && err.response.data && err.response.data.detail) {
      errorMsg = `查询失败: ${err.response.data.detail.message || err.response.data.detail}`
    } else if (err.message) {
      errorMsg = `查询失败: ${err.message}`
    }

    message.error(errorMsg)

    // 清空数据
    statisticsData.value = []
    pagination.itemCount = 0
  } finally {
    loading.value = false
  }
}

/**
 * 处理重置
 */
function handleReset() {
  // 重置时间范围为默认值（昨天）
  dateRange.value = [yesterdayStart.getTime(), yesterdayEnd.getTime()]

  // 重置设备类型选择
  filterType.value = 'welding'

  // 重置设备组选择
  selectedGroup.value = null

  // 重新查询数据
  handleQuery()

  message.success('重置成功')
}

// 窗口大小变化时重新调整图表大小
function handleResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 组件挂载时初始化
onMounted(() => {
  // 加载设备类型
  loadDeviceTypes()

  // 初始化数据 - 调用真实API
  handleQuery()

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

// 组件销毁前清理
onBeforeUnmount(() => {
  // 移除窗口大小变化监听
  window.removeEventListener('resize', handleResize)

  // 销毁图表实例
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
/* 查询容器样式 */
.query-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.query-items {
  display: flex;
  align-items: center;
  gap: 32px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.query-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  min-width: fit-content;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .query-container {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .query-items {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .query-actions {
    justify-content: flex-end;
  }
}

@media (max-width: 600px) {
  .query-items {
    flex-direction: column;
    align-items: stretch;
  }
}

/* 统计卡片样式 */
.statistics-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
}

.info-icon {
  position: absolute;
  top: -8px;
  right: -8px;
  color: #999;
  cursor: pointer;
  transition: color 0.3s ease;
}

.info-icon:hover {
  color: #1890ff;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.online {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.stat-icon.welding {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.stat-icon.devices {
  background: linear-gradient(135deg, #722ed1 0%, #531dab 100%);
}

.stat-icon.efficiency {
  background: linear-gradient(135deg, #fa541c 0%, #d4380d 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 图表容器 */
.chart {
  width: 100%;
}

/* 设备组选择器样式 */
.device-group-select {
  width: 140px;
  min-width: 120px;
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .statistics-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .statistics-cards {
    grid-template-columns: 1fr;
  }
}
</style>
