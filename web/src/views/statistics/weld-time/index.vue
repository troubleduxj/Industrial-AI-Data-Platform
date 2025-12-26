<template>
  <CommonPage
    v-permission="{ action: 'read', resource: 'weld_time' }"
    show-footer
    title="焊接时长统计"
  >
    <template #action>
      <!-- 视图切换 -->
      <ViewToggle
        v-model="viewMode"
        :options="viewOptions"
        size="small"
        :show-label="false"
        :icon-size="16"
        align="right"
      />
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
              :default-value="[yesterdayStart.getTime(), yesterdayEnd.getTime()]"
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
          <div class="stat-icon total-time">
            <TheIcon icon="material-symbols:timer" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overallStats.totalWeldTime }}h</div>
            <div class="stat-label">总焊接时长</div>
          </div>
          <NTooltip trigger="hover">
            <template #trigger>
              <n-icon size="18" class="info-icon" cursor-pointer>
                <icon-mdi:information-outline />
              </n-icon>
            </template>
            总焊接时长 = 各设备焊接时长之和
          </NTooltip>
        </div>
      </NCard>

      <NCard class="stat-card">
        <div class="stat-content">
          <div class="stat-icon avg-time">
            <TheIcon icon="material-symbols:hourglass-top" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overallStats.avgWeldTime }}h</div>
            <div class="stat-label">平均焊接时长</div>
          </div>
          <NTooltip trigger="hover">
            <template #trigger>
              <n-icon size="18" class="info-icon" cursor-pointer>
                <icon-mdi:information-outline />
              </n-icon>
            </template>
            平均焊接时长 = 总焊接时长 / 设备数
          </NTooltip>
        </div>
      </NCard>

      <NCard class="stat-card">
        <div class="stat-content">
          <div class="stat-icon efficiency">
            <TheIcon icon="material-symbols:trending-up" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overallStats.weldingEfficiency }}%</div>
            <div class="stat-label">焊接效率</div>
          </div>
          <NTooltip trigger="hover">
            <template #trigger>
              <n-icon size="18" class="info-icon" cursor-pointer>
                <icon-mdi:information-outline />
              </n-icon>
            </template>
            焊接效率 = 焊接时间 / 总统计时间
          </NTooltip>
        </div>
      </NCard>

      <NCard class="stat-card">
        <div class="stat-content">
          <div class="stat-icon devices">
            <TheIcon icon="material-symbols:developer-board" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overallStats.activeDevices }}</div>
            <div class="stat-label">活跃设备数</div>
          </div>
          <NTooltip trigger="hover">
            <template #trigger>
              <n-icon size="18" class="info-icon" cursor-pointer>
                <icon-mdi:information-outline />
              </n-icon>
            </template>
            活跃设备数 = 焊接时长>0的设备数
          </NTooltip>
        </div>
      </NCard>
    </div>

    <!-- 图表视图 -->
    <div v-if="viewMode === 'chart'" class="chart-container">
      <NCard title="焊接时长历史统计">
        <div ref="chartRef" class="chart" style="height: 400px"></div>
      </NCard>
    </div>

    <!-- 表格视图 -->
    <div v-else-if="viewMode === 'table'">
      <NCard title="焊接时长统计数据">
        <NDataTable
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick, reactive } from 'vue'
import {
  NButton,
  NCard,
  NSelect,
  NDatePicker,
  NDataTable,
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
import { deviceDataApi } from '@/api/device-v2'

defineOptions({ name: '焊接时长统计' })

// ==================== 类型定义 ====================

interface WeldTimeData {
  device_code: string
  device_name?: string
  total_time: number
  date?: string
  [key: string]: any
}

type ViewMode = 'chart' | 'table'

const message = useMessage()

// 响应式数据
const loading = ref<boolean>(false)
const viewMode = ref<ViewMode>('chart')
const filterType = ref<string>('welding') // 默认选择焊机类型

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
// 时间范围设置（默认昨天）
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
const deviceTypeOptions = [
  { label: '焊机', value: 'welding' },
  { label: '切割设备', value: 'cutting' },
  { label: '装配设备', value: 'assembly' },
  { label: '检测设备', value: 'testing' },
  { label: '搬运设备', value: 'transport' },
]

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
      totalWeldTime: 0,
      avgWeldTime: 0,
      weldingEfficiency: 0,
      activeDevices: 0,
    }
  }

  const totalWeldTime = statisticsData.value.reduce((sum, item) => sum + item.totalWeldTime, 0)
  const avgWeldTime = (totalWeldTime / statisticsData.value.length).toFixed(1)
  const totalEfficiency = statisticsData.value.reduce(
    (sum, item) => sum + item.weldingEfficiency,
    0
  )
  const avgEfficiency = (totalEfficiency / statisticsData.value.length).toFixed(1)

  return {
    totalWeldTime: totalWeldTime.toFixed(1),
    avgWeldTime,
    weldingEfficiency: avgEfficiency,
    activeDevices: 23,
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
    title: '总焊接时长',
    key: 'totalWeldTime',
    width: 120,
    render: (row) => `${row.totalWeldTime}小时`,
  },
  {
    title: '平均焊接时长',
    key: 'avgWeldTime',
    width: 140,
    render: (row) => `${row.avgWeldTime}小时`,
  },
  {
    title: '焊接效率',
    key: 'weldingEfficiency',
    width: 100,
    render: (row) => `${row.weldingEfficiency}%`,
  },
  {
    title: '活跃设备数',
    key: 'activeDevices',
    width: 120,
  },
  {
    title: '最长焊接时长',
    key: 'maxWeldTime',
    width: 140,
    render: (row) => `${row.maxWeldTime}小时`,
  },
  {
    title: '最短焊接时长',
    key: 'minWeldTime',
    width: 140,
    render: (row) => `${row.minWeldTime}小时`,
  },
  {
    title: '焊接次数',
    key: 'weldCount',
    width: 100,
  },
]

/**
 * 生成模拟数据
 */
function generateMockData() {
  const data = []

  if (!dateRange.value || dateRange.value.length !== 2) {
    return data
  }

  const startDate = new Date(dateRange.value[0])
  const endDate = new Date(dateRange.value[1])
  const daysDiff = Math.floor((endDate - startDate) / (24 * 60 * 60 * 1000)) + 1
  const isHourlyView = daysDiff <= 3

  if (isHourlyView) {
    // 小于等于3天：生成按小时的数据
    const totalHours = daysDiff * 24

    for (let hour = 0; hour < totalHours; hour++) {
      const hourDate = new Date(startDate.getTime() + hour * 60 * 60 * 1000)
      const totalWeldTime = parseFloat((1.5 + Math.random() * 2).toFixed(1)) // 1.5-3.5小时
      const avgWeldTime = parseFloat((0.3 + Math.random() * 0.4).toFixed(1)) // 0.3-0.7小时
      const weldingEfficiency = parseFloat((70 + Math.random() * 25).toFixed(1)) // 70-95%
      const activeDevices = 15 + Math.floor(Math.random() * 10) // 15-24台
      const maxWeldTime = parseFloat((avgWeldTime + 0.2 + Math.random() * 0.3).toFixed(1))
      const minWeldTime = parseFloat(
        Math.max(0.1, avgWeldTime - 0.1 - Math.random() * 0.2).toFixed(1)
      )
      const weldCount = 5 + Math.floor(Math.random() * 15) // 5-20次

      data.push({
        date: hourDate.getTime(),
        totalWeldTime,
        avgWeldTime,
        weldingEfficiency,
        activeDevices,
        maxWeldTime,
        minWeldTime,
        weldCount,
      })
    }
  } else {
    // 大于3天：生成按天的数据
    for (let i = 0; i < daysDiff; i++) {
      const date = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000)
      const totalWeldTime = parseFloat((40 + Math.random() * 20).toFixed(1)) // 40-60小时
      const avgWeldTime = parseFloat((1.5 + Math.random() * 1.5).toFixed(1)) // 1.5-3小时
      const weldingEfficiency = parseFloat((75 + Math.random() * 20).toFixed(1)) // 75-95%
      const activeDevices = 20 + Math.floor(Math.random() * 5) // 20-24台
      const maxWeldTime = parseFloat((avgWeldTime + 1 + Math.random() * 2).toFixed(1))
      const minWeldTime = parseFloat(Math.max(0.5, avgWeldTime - 1 - Math.random()).toFixed(1))
      const weldCount = 150 + Math.floor(Math.random() * 100) // 150-250次

      data.push({
        date: date.getTime(),
        totalWeldTime,
        avgWeldTime,
        weldingEfficiency,
        activeDevices,
        maxWeldTime,
        minWeldTime,
        weldCount,
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
          const unit = param.seriesName.includes('效率') ? '%' : '小时'
          result += `${param.seriesName}: ${param.data[1]}${unit}<br/>`
        })
        return result
      },
    },
    legend: {
      data: ['总焊接时长', '平均焊接时长', '焊接效率'],
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
      boundaryGap: isHourlyView ? false : true,
      axisLabel: {
        formatter: function (value) {
          return formatDate(value, isHourlyView ? 'HH:mm' : 'MM-DD')
        },
      },
    },
    yAxis: [
      {
        type: 'value',
        name: '时长(小时)',
        position: 'left',
        axisLabel: {
          formatter: '{value}h',
        },
      },
      {
        type: 'value',
        name: '效率(%)',
        position: 'right',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%',
        },
      },
    ],
    series: [
      {
        name: '总焊接时长',
        type: 'bar',
        yAxisIndex: 0,
        data: statisticsData.value.map((item) => [item.date, item.totalWeldTime]),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#52c41a' },
              { offset: 1, color: '#389e0d' },
            ],
          },
        },
      },
      {
        name: '平均焊接时长',
        type: 'line',
        yAxisIndex: 0,
        data: statisticsData.value.map((item) => [item.date, item.avgWeldTime]),
        smooth: true,
        lineStyle: {
          color: '#4834d4',
          width: 3,
        },
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(72, 52, 212, 0.3)' },
              { offset: 1, color: 'rgba(104, 109, 224, 0.1)' },
            ],
          },
        },
      },
      {
        name: '焊接效率',
        type: 'line',
        yAxisIndex: 1,
        data: statisticsData.value.map((item) => [item.date, item.weldingEfficiency]),
        smooth: true,
        lineStyle: {
          color: '#00d2d3',
          width: 3,
        },
        symbol: 'diamond',
        symbolSize: 6,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0, 210, 211, 0.3)' },
              { offset: 1, color: 'rgba(84, 160, 255, 0.1)' },
            ],
          },
        },
      },
    ],
  }

  chartInstance.setOption(option)
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

    console.log('查询参数:', params)

    // 调用真实API
    const response = await deviceDataApi.getWeldTimeStatistics(params)

    if (response && Array.isArray(response)) {
      statisticsData.value = response
      pagination.itemCount = response.length
    } else {
      statisticsData.value = []
      pagination.itemCount = 0
    }

    if (viewMode.value === 'chart') {
      nextTick(() => {
        initChart()
      })
    }

    message.success(
      `查询完成 - 设备类型: ${
        deviceTypeOptions.find((opt) => opt.value === filterType.value)?.label || '全部'
      }`
    )
  } catch (error) {
    console.error('查询焊接时长统计数据失败:', error)
    statisticsData.value = []
    pagination.itemCount = 0

    const errorMsg = error?.response?.data?.detail || error?.message || '查询失败'
    message.error(`查询失败: ${errorMsg}`)
  } finally {
    loading.value = false
  }
}

/**
 * 处理重置
 */
function handleReset() {
  // 重置设备类型为默认值（焊机）
  filterType.value = 'welding'

  // 重置时间范围为默认值（昨天）
  dateRange.value = [yesterdayStart.getTime(), yesterdayEnd.getTime()]

  // 重置设备组选择
  selectedGroup.value = null

  // 重新查询数据
  handleQuery()

  message.success('重置完成')
}

// 窗口大小变化时重新调整图表大小
function handleResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 组件挂载时初始化
onMounted(() => {
  // 初始化查询数据
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
/* 查询区域样式 */
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
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
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

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.total-time {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.stat-icon.avg-time {
  background: linear-gradient(135deg, #4834d4 0%, #686de0 100%);
}

.stat-icon.efficiency {
  background: linear-gradient(135deg, #00d2d3 0%, #54a0ff 100%);
}

.stat-icon.devices {
  background: linear-gradient(135deg, #5f27cd 0%, #a55eea 100%);
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
