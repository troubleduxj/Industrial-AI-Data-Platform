<template>
  <CommonPage show-footer title="焊机日报">
    <template #action>
      <!-- 导出按钮 -->
      <PermissionButton
        permission="GET /api/v2/statistics/welding-report/export"
        type="primary"
        @click="handleExport"
      >
        <TheIcon icon="material-symbols:download" :size="16" class="mr-5" />
        导出报告
      </PermissionButton>
    </template>

    <!-- 查询条件 -->
    <NCard class="mb-15" rounded-10>
      <div class="query-container">
        <div
          class="query-items"
          style="display: flex; gap: 20px; flex-wrap: wrap; align-items: center"
        >
          <!-- 设备编码输入 -->
          <QueryBarItem label="设备编码" :label-width="70" style="flex: 1; min-width: 200px">
            <NInput
              v-model:value="deviceCode"
              placeholder="请输入设备编码"
              clearable
              style="width: 100%"
            />
          </QueryBarItem>

          <!-- 日期选择 -->
          <QueryBarItem label="报告日期" :label-width="70" style="flex: 1; min-width: 200px">
            <NDatePicker
              v-model:value="reportDate"
              type="date"
              clearable
              format="yyyy-MM-dd"
              :default-value="yesterdayStart.getTime()"
              style="width: 100%"
            />
          </QueryBarItem>

          <!-- 部门车间选择 -->
          <QueryBarItem label="部门车间" :label-width="70" style="flex: 1; min-width: 200px">
            <NSelect
              v-model:value="selectedGroup"
              :options="groupOptions"
              placeholder="全部部门车间"
              clearable
              style="width: 100%"
            />
          </QueryBarItem>

          <!-- 班次选择 -->
          <QueryBarItem label="班次" :label-width="50" style="flex: 1; min-width: 150px">
            <NSelect
              v-model:value="selectedShift"
              :options="shiftOptions"
              placeholder="全部班次"
              clearable
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

    <!-- 日报概览卡片 -->
    <div class="report-overview mb-20">
      <NCard class="overview-card">
        <div class="overview-content">
          <div class="overview-icon weld-time">
            <TheIcon icon="material-symbols:timer" :size="24" />
          </div>
          <div class="overview-info">
            <div class="overview-value">{{ reportStats.totalWeldTime }}h</div>
            <div class="overview-label">焊接时长</div>
          </div>
        </div>
      </NCard>

      <NCard class="overview-card">
        <div class="overview-content">
          <div class="overview-icon wire-consumption">
            <TheIcon icon="material-symbols:cable" :size="24" />
          </div>
          <div class="overview-info">
            <div class="overview-value">{{ reportStats.wireConsumption }}kg</div>
            <div class="overview-label">焊丝消耗</div>
          </div>
        </div>
      </NCard>

      <NCard class="overview-card">
        <div class="overview-content">
          <div class="overview-icon gas-consumption">
            <TheIcon icon="material-symbols:gas-meter" :size="24" />
          </div>
          <div class="overview-info">
            <div class="overview-value">{{ reportStats.gasConsumption }}L</div>
            <div class="overview-label">气体消耗</div>
          </div>
        </div>
      </NCard>

      <NCard class="overview-card">
        <div class="overview-content">
          <div class="overview-icon power-consumption">
            <TheIcon icon="material-symbols:electric-bolt" :size="24" />
          </div>
          <div class="overview-info">
            <div class="overview-value">{{ reportStats.powerConsumption }}kWh</div>
            <div class="overview-label">电能消耗</div>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 设备详细数据表格 -->
    <NCard title="设备详细数据" class="mb-20">
      <NDataTable
        v-permission="{ action: 'read', resource: 'welding_report' }"
        :columns="deviceColumns"
        :data="deviceData"
        :pagination="false"
        :loading="loading"
        striped
        size="medium"
      />

      <!-- 独立分页组件 -->
      <div v-if="deviceData.length > 0" class="mt-6 flex justify-center">
        <NPagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.itemCount"
          :page-sizes="pagination.pageSizes"
          :show-size-picker="pagination.showSizePicker"
          :show-quick-jumper="pagination.showQuickJumper"
          :prefix="(info) => `共 ${info.itemCount} 条`"
          :suffix="(info) => `显示 ${info.startIndex}-${info.endIndex} 条`"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </NCard>

    <!-- 部门车间统计图表 -->
    <NCard title="部门车间统计分析">
      <div ref="chartRef" class="chart" style="height: 400px"></div>
    </NCard>
  </CommonPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, reactive, h, type Ref } from 'vue'
import {
  NButton,
  NCard,
  NSelect,
  NDatePicker,
  NInput,
  NDataTable,
  NPagination,
  useMessage,
  type SelectOption,
  type DataTableColumns,
} from 'naive-ui'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import * as XLSX from 'xlsx'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { formatDate } from '@/utils'
import statisticsV2Api from '@/api/statistics-v2'

defineOptions({ name: '焊机日报' })

// ==================== 类型定义 ====================

interface ReportStats {
  totalWeldTime: number
  wireConsumption: number
  gasConsumption: number
  powerConsumption: number
}

interface DeviceReportData {
  prod_code: string
  device_name?: string
  weld_time?: number
  wire_consumption?: number
  gas_consumption?: number
  power_consumption?: number
  shift?: string
  group?: string
  [key: string]: any
}

interface PaginationInfo {
  page: number
  pageSize: number
  showSizePicker: boolean
  pageSizes: number[]
  showQuickJumper: boolean
  itemCount: number
}

const message = useMessage()

// 响应式数据
const loading = ref<boolean>(false)
const deviceCode = ref<string>('')
const selectedGroup = ref<string | null>(null)
const selectedShift = ref<string | null>(null)
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: ECharts | null = null

// 默认日期（昨天）
const today = new Date()
const yesterdayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1)
const reportDate = ref<Date>(yesterdayStart)

// 设备组选项
const groupOptions: SelectOption[] = [
  { label: '生产车间A', value: 'workshop_a' },
  { label: '生产车间B', value: 'workshop_b' },
  { label: '生产车间C', value: 'workshop_c' },
  { label: '测试区域', value: 'test_area' },
]

// 班次选项
const shiftOptions: SelectOption[] = [
  { label: '早班 (08:00-16:00)', value: 'morning' },
  { label: '中班 (16:00-24:00)', value: 'afternoon' },
  { label: '夜班 (00:00-08:00)', value: 'night' },
]

// 日报统计数据
const reportStats = ref<ReportStats>({
  totalWeldTime: 0,
  wireConsumption: 0,
  gasConsumption: 0,
  powerConsumption: 0,
})

// 设备数据（将通过API获取）
const deviceData = ref<DeviceReportData[]>([])

// 分页配置
const pagination = reactive<PaginationInfo>({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true,
  itemCount: 0,
})

// 设备数据表格列配置
const deviceColumns = [
  {
    title: '设备编码',
    key: 'prod_code',
    width: 120,
    render: (row) => row?.prod_code || '-',
  },
  {
    title: '报告日期',
    key: 'report_date',
    width: 100,
    render: (row) => row?.report_date || '-',
  },
  {
    title: '班次',
    key: 'shift',
    width: 80,
    render: (row) => row?.shift || '-',
  },
  {
    title: '部门车间',
    key: 'operator',
    width: 100,
    render: (row) => row?.operator || '-',
  },
  {
    title: '焊接时长（秒）',
    key: 'welding_duration_sec',
    width: 120,
    render: (row) => row?.welding_duration_sec || 0,
    sorter: (row1, row2) => (row1?.welding_duration_sec || 0) - (row2?.welding_duration_sec || 0),
  },
  {
    title: '焊丝消耗（kg）',
    key: 'wire_consumed_kg',
    width: 120,
    render: (row) => row?.wire_consumed_kg || 0,
    sorter: (row1, row2) => (row1?.wire_consumed_kg || 0) - (row2?.wire_consumed_kg || 0),
  },
  {
    title: '气体消耗（L）',
    key: 'gas_consumed_liter',
    width: 120,
    render: (row) => row?.gas_consumed_liter || 0,
    sorter: (row1, row2) => (row1?.gas_consumed_liter || 0) - (row2?.gas_consumed_liter || 0),
  },
  {
    title: '电能消耗（kWh）',
    key: 'energy_consumed_kwh',
    width: 130,
    render: (row) => row?.energy_consumed_kwh || 0,
    sorter: (row1, row2) => (row1?.energy_consumed_kwh || 0) - (row2?.energy_consumed_kwh || 0),
  },
]

/**
 * 获取图表数据
 */
async function getChartData() {
  try {
    // 构建查询参数，不包含分页参数以获取所有数据
    const params = {
      prod_code: deviceCode.value || null,
      report_date: reportDate.value ? formatDate(reportDate.value, 'YYYY-MM-DD') : null,
      device_group: selectedGroup.value,
      shift: selectedShift.value,
    }

    // 获取所有符合条件的数据用于图表统计
    const chartResponse = await statisticsV2Api.getWeldingDailyReportDetail(params)

    // 处理API v2响应格式
    if (chartResponse && chartResponse.success && chartResponse.data) {
      const responseData = chartResponse.data

      // 确保返回的是数组
      if (Array.isArray(responseData)) {
        return responseData
      } else {
        console.warn('图表API返回的data不是数组格式:', responseData)
        console.warn('数据类型:', typeof responseData)

        // 尝试从嵌套结构中提取数据
        if (responseData && typeof responseData === 'object') {
          if (responseData.data && Array.isArray(responseData.data)) {
            console.log('🔧 从嵌套结构中提取图表数据')
            return responseData.data
          } else {
            // 检查是否是类数组对象（有数字键的对象）
            const keys = Object.keys(responseData)
            const numericKeys = keys
              .filter((key) => /^\d+$/.test(key))
              .sort((a, b) => parseInt(a) - parseInt(b))

            if (numericKeys.length > 0) {
              console.log('🔧 检测到类数组对象，转换为真正的数组')
              const arrayData = numericKeys.map((key) => responseData[key])
              console.log('转换后的数组长度:', arrayData.length)
              return arrayData
            }

            // 检查是否是单个记录对象
            if (keys.includes('prod_code') || keys.includes('device_code') || keys.includes('id')) {
              console.log('🔧 将单个记录转换为数组用于图表')
              return [responseData]
            } else {
              // 尝试查找可能的数组字段
              const arrayField = keys.find((key) => Array.isArray(responseData[key]))
              if (arrayField) {
                console.log(`🔧 从字段 ${arrayField} 中提取图表数组数据`)
                return responseData[arrayField]
              }
            }
          }
        }
        return []
      }
    } else {
      console.warn('图表API响应格式异常:', chartResponse)
      return []
    }
  } catch (error) {
    console.error('获取图表数据失败:', error)
    return []
  }
}

/**
 * 初始化图表
 */
async function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  // 获取所有符合筛选条件的数据
  const allData = await getChartData()

  // 根据筛选条件决定聚合逻辑
  let chartData = []
  let xAxisData = []

  if (selectedGroup.value && selectedShift.value) {
    // 情况4：选择了日期、部门车间和班次，只展示该部门该班次的数据
    const filteredData = allData.filter(
      (device) => device.operator === selectedGroup.value && device.shift === selectedShift.value
    )

    if (filteredData.length > 0) {
      const stats = {
        weldTime: filteredData.reduce((sum, device) => sum + (device.welding_duration_sec || 0), 0),
        wireConsumption: filteredData.reduce(
          (sum, device) => sum + (device.wire_consumed_kg || 0),
          0
        ),
        gasConsumption: filteredData.reduce(
          (sum, device) => sum + (device.gas_consumed_liter || 0),
          0
        ),
        powerConsumption: filteredData.reduce(
          (sum, device) => sum + (device.energy_consumed_kwh || 0),
          0
        ),
      }

      xAxisData = [`${selectedGroup.value}-${selectedShift.value}`]
      chartData = {
        weldTimeData: [stats.weldTime],
        wireData: [stats.wireConsumption],
        gasData: [stats.gasConsumption],
        powerData: [stats.powerConsumption],
      }
    }
  } else if (selectedGroup.value) {
    // 情况2：选择了日期和部门车间，只展示本车间4个指标的统计
    const filteredData = allData.filter((device) => device.operator === selectedGroup.value)

    if (filteredData.length > 0) {
      const stats = {
        weldTime:
          filteredData.reduce((sum, device) => sum + (device.welding_duration_sec || 0), 0) / 3600,
        wireConsumption: filteredData.reduce(
          (sum, device) => sum + (device.wire_consumed_kg || 0),
          0
        ),
        gasConsumption: filteredData.reduce(
          (sum, device) => sum + (device.gas_consumed_liter || 0),
          0
        ),
        powerConsumption: filteredData.reduce(
          (sum, device) => sum + (device.energy_consumed_kwh || 0),
          0
        ),
      }

      xAxisData = [selectedGroup.value]
      chartData = {
        weldTimeData: [stats.weldTime],
        wireData: [stats.wireConsumption],
        gasData: [stats.gasConsumption],
        powerData: [stats.powerConsumption],
      }
    }
  } else if (selectedShift.value) {
    // 情况3：选择了日期和班次，展示本班次各部门车间的数据聚合
    const filteredData = allData.filter((device) => device.shift === selectedShift.value)
    const departmentStats = {}

    filteredData.forEach((device) => {
      const department = device.operator || '未知部门'
      if (!departmentStats[department]) {
        departmentStats[department] = {
          weldTime: 0,
          wireConsumption: 0,
          gasConsumption: 0,
          powerConsumption: 0,
        }
      }
      departmentStats[department].weldTime += device.welding_duration_sec || 0
      departmentStats[department].wireConsumption += device.wire_consumed_kg || 0
      departmentStats[department].gasConsumption += device.gas_consumed_liter || 0
      departmentStats[department].powerConsumption += device.energy_consumed_kwh || 0
    })

    const departments = Object.keys(departmentStats)
    xAxisData = departments
    chartData = {
      weldTimeData: departments.map((dept) => departmentStats[dept].weldTime),
      wireData: departments.map((dept) => departmentStats[dept].wireConsumption),
      gasData: departments.map((dept) => departmentStats[dept].gasConsumption),
      powerData: departments.map((dept) => departmentStats[dept].powerConsumption),
    }
  } else {
    // 情况1：只选择了日期，把该日期返回的所有结果集按部门车间进行数据聚合展示
    const departmentStats = {}

    allData.forEach((device) => {
      const department = device.operator || '未知部门'
      if (!departmentStats[department]) {
        departmentStats[department] = {
          weldTime: 0,
          wireConsumption: 0,
          gasConsumption: 0,
          powerConsumption: 0,
        }
      }
      departmentStats[department].weldTime += device.welding_duration_sec || 0
      departmentStats[department].wireConsumption += device.wire_consumed_kg || 0
      departmentStats[department].gasConsumption += device.gas_consumed_liter || 0
      departmentStats[department].powerConsumption += device.energy_consumed_kwh || 0
    })

    const departments = Object.keys(departmentStats)
    xAxisData = departments
    chartData = {
      weldTimeData: departments.map((dept) => departmentStats[dept].weldTime),
      wireData: departments.map((dept) => departmentStats[dept].wireConsumption),
      gasData: departments.map((dept) => departmentStats[dept].gasConsumption),
      powerData: departments.map((dept) => departmentStats[dept].powerConsumption),
    }
  }

  // 如果没有数据，使用默认值
  if (xAxisData.length === 0) {
    xAxisData = ['生产车间A', '生产车间B', '生产车间C']
    chartData = {
      weldTimeData: [0, 0, 0],
      wireData: [0, 0, 0],
      gasData: [0, 0, 0],
      powerData: [0, 0, 0],
    }
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['焊接时长', '焊丝消耗', '气体消耗', '电能消耗'],
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
      type: 'category',
      data: xAxisData,
    },
    yAxis: [
      {
        type: 'value',
        name: '时长/消耗 (s)',
        position: 'left',
      },
    ],
    series: [
      {
        name: '焊接时长',
        type: 'bar',
        yAxisIndex: 0,
        tooltip: {
          valueFormatter: function (value) {
            return value + ' s'
          },
        },
        data: chartData.weldTimeData,
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
        name: '焊丝消耗',
        type: 'bar',
        yAxisIndex: 0,
        data: chartData.wireData,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#4834d4' },
              { offset: 1, color: '#686de0' },
            ],
          },
        },
      },
      {
        name: '气体消耗',
        type: 'bar',
        yAxisIndex: 0,
        data: chartData.gasData,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#fac858' },
              { offset: 1, color: '#faad14' },
            ],
          },
        },
      },
      {
        name: '电能消耗',
        type: 'bar',
        yAxisIndex: 0,
        data: chartData.powerData,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#ee6666' },
              { offset: 1, color: '#ff4d4f' },
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
    // 确保有报告日期
    if (!reportDate.value) {
      message.error('请选择报告日期')
      return
    }

    // 构建查询参数
    const params = {
      prod_code: deviceCode.value || undefined,
      report_date: formatDate(reportDate.value, 'YYYY-MM-DD'),
      device_type: 'welding',
      device_group: selectedGroup.value,
      shift: selectedShift.value,
    }

    console.log('查询参数:', params)

    // 调用汇总数据API
    const summaryResponse = await statisticsV2Api.getWeldingDailyReportSummary(params)
    console.log('汇总数据响应:', summaryResponse)
    if (summaryResponse && summaryResponse.data) {
      // 根据API实际返回的字段名进行映射
      reportStats.value = {
        totalWeldTime: summaryResponse.data.total_duration || 0,
        wireConsumption: summaryResponse.data.total_wire || 0,
        gasConsumption: summaryResponse.data.total_gas || 0,
        powerConsumption: summaryResponse.data.total_energy || 0,
      }
    }

    // 调用详细数据API
    const detailResponse = await statisticsV2Api.getWeldingDailyReportDetail({
      ...params,
      page: pagination.page,
      page_size: pagination.pageSize,
    })

    console.log('详细数据响应:', detailResponse)
    console.log('响应数据类型:', typeof detailResponse?.data)
    console.log('响应数据内容:', detailResponse?.data)

    // 详细分析响应结构
    if (detailResponse?.data && typeof detailResponse.data === 'object') {
      console.log('🔍 详细分析响应数据结构:')
      console.log('- 数据键:', Object.keys(detailResponse.data))
      console.log('- 完整响应结构:', JSON.stringify(detailResponse, null, 2))

      // 检查每个键的值
      Object.keys(detailResponse.data).forEach((key) => {
        const value = detailResponse.data[key]
        console.log(
          `- ${key}: ${typeof value} = ${Array.isArray(value) ? `Array(${value.length})` : value}`
        )
      })
    }

    if (detailResponse && detailResponse.success && detailResponse.data) {
      // API v2标准响应格式：data直接是数组，分页信息在meta中
      const responseData = detailResponse.data

      // 确保数据是数组格式
      if (Array.isArray(responseData)) {
        deviceData.value = responseData
        console.log('✅ 数据是数组格式，长度:', responseData.length)
      } else {
        console.warn('❌ API返回的data不是数组格式:', responseData)
        console.warn('数据类型:', typeof responseData)
        console.warn('数据键:', Object.keys(responseData))

        // 尝试从嵌套结构中提取数据
        if (responseData && typeof responseData === 'object') {
          if (responseData.data && Array.isArray(responseData.data)) {
            console.log('🔧 从嵌套结构中提取数据')
            deviceData.value = responseData.data
            pagination.itemCount = responseData.total || 0
          } else {
            // 检查是否是类数组对象或单个记录对象
            const keys = Object.keys(responseData)
            console.log('🔍 检查对象键:', keys)

            // 检查是否是类数组对象（有数字键的对象）
            const numericKeys = keys
              .filter((key) => /^\d+$/.test(key))
              .sort((a, b) => parseInt(a) - parseInt(b))

            if (numericKeys.length > 0) {
              console.log('🔧 检测到类数组对象，转换为真正的数组')
              const arrayData = numericKeys.map((key) => responseData[key])
              console.log('转换后的数组长度:', arrayData.length)
              deviceData.value = arrayData
              pagination.itemCount =
                detailResponse.meta?.pagination?.total ||
                detailResponse.meta?.total ||
                arrayData.length
            } else if (
              keys.includes('prod_code') ||
              keys.includes('device_code') ||
              keys.includes('id')
            ) {
              // 如果对象包含典型的记录字段，将其转换为数组
              console.log('🔧 将单个记录转换为数组')
              deviceData.value = [responseData]
              pagination.itemCount = 1
            } else {
              // 尝试查找可能的数组字段
              const arrayField = keys.find((key) => Array.isArray(responseData[key]))
              if (arrayField) {
                console.log(`🔧 从字段 ${arrayField} 中提取数组数据`)
                deviceData.value = responseData[arrayField]
                pagination.itemCount = responseData.total || responseData[arrayField].length
              } else {
                console.warn('⚠️ 无法从响应中提取数组数据')
                deviceData.value = []
              }
            }
          }
        } else {
          deviceData.value = []
        }
      }

      // 从meta获取分页信息
      if (Array.isArray(responseData)) {
        pagination.itemCount =
          detailResponse.meta?.pagination?.total || detailResponse.meta?.total || 0
      }
    } else {
      console.warn('API响应格式异常:', detailResponse)
      deviceData.value = []
      pagination.itemCount = 0
    }

    await nextTick()
    await initChart()

    message.success('查询完成')
  } catch (error) {
    console.error('查询焊机日报数据失败:', error)
    const errorMsg = error?.response?.data?.detail || error?.message || '查询失败'
    message.error(`查询失败: ${errorMsg}`)

    // 出错时重置数据
    reportStats.value = {
      totalWeldTime: 0,
      wireConsumption: 0,
      gasConsumption: 0,
      powerConsumption: 0,
    }
    deviceData.value = []
    pagination.itemCount = 0
  } finally {
    loading.value = false
  }
}

/**
 * 处理重置
 */
function handleReset() {
  // 重置设备编码
  deviceCode.value = ''

  // 重置日期为默认值（昨天）
  reportDate.value = yesterdayStart.getTime()

  // 重置设备组选择
  selectedGroup.value = null

  // 重置班次选择
  selectedShift.value = null

  // 重置分页
  pagination.page = 1

  // 重新查询数据
  handleQuery()

  message.success('重置完成')
}

/**
 * 处理分页变化
 */
function handlePageChange(page) {
  pagination.page = page
  handleQuery()
}

/**
 * 处理每页大小变化
 */
function handlePageSizeChange(pageSize) {
  pagination.pageSize = pageSize
  pagination.page = 1
  handleQuery()
}

/**
 * 处理导出
 */
async function handleExport() {
  try {
    message.loading('正在导出数据...', { duration: 0 })

    // 构建查询参数（不包含分页参数，获取所有数据）
    const params = {
      prod_code: deviceCode.value || null,
      report_date: reportDate.value ? formatDate(reportDate.value, 'YYYY-MM-DD') : null,
      device_group: selectedGroup.value,
      shift: selectedShift.value,
    }

    // 调用详细数据API获取所有筛选结果
    const detailResponse = await statisticsV2Api.getWeldingDailyReportDetail(params)

    let allData = []
    if (detailResponse && detailResponse.data) {
      allData = detailResponse.data || []
    }

    if (!allData || allData.length === 0) {
      message.destroyAll()
      message.warning('暂无数据可导出')
      return
    }

    // 准备导出数据
    const exportData = allData.map((item) => ({
      设备编码: item.prod_code || '',
      报告日期: item.report_date || '',
      班次: item.shift || '',
      部门车间: item.operator || '',
      '焊接时长（秒）': item.welding_duration_sec || 0,
      '焊丝消耗（kg）': item.wire_consumed_kg || 0,
      '气体消耗（L）': item.gas_consumed_liter || 0,
      '电能消耗（kWh）': item.energy_consumed_kwh || 0,
    }))

    // 创建工作表
    const worksheet = XLSX.utils.json_to_sheet(exportData)

    // 设置列宽
    const colWidths = [
      { wch: 15 }, // 设备编码
      { wch: 12 }, // 报告日期
      { wch: 8 }, // 班次
      { wch: 12 }, // 部门车间
      { wch: 15 }, // 焊接时长
      { wch: 15 }, // 焊丝消耗
      { wch: 15 }, // 气体消耗
      { wch: 15 }, // 电能消耗
    ]
    worksheet['!cols'] = colWidths

    // 创建工作簿
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, '焊机日报明细')

    // 生成文件名
    const dateStr = reportDate.value
      ? formatDate(reportDate.value, 'YYYY-MM-DD')
      : formatDate(new Date(), 'YYYY-MM-DD')
    const fileName = `焊机日报明细_${dateStr}.xlsx`

    // 导出文件
    XLSX.writeFile(workbook, fileName)

    message.destroyAll()
    message.success(`导出成功，共导出 ${allData.length} 条数据`)
  } catch (error) {
    console.error('导出失败:', error)
    message.destroyAll()
    const errorMsg = error?.response?.data?.detail || error?.message || '导出失败'
    message.error(`导出失败: ${errorMsg}`)
  }
}

// 窗口大小变化时重新调整图表大小
function handleResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 组件挂载时初始化
onMounted(() => {
  // 设置默认日期
  reportDate.value = yesterdayStart.getTime()

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

/* 日报概览卡片样式 */
.report-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.overview-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.overview-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.overview-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.overview-icon.production {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.overview-icon.weld-time {
  background: linear-gradient(135deg, #4834d4 0%, #686de0 100%);
}

.overview-icon.wire-consumption {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
}

.overview-icon.gas-consumption {
  background: linear-gradient(135deg, #00d2d3 0%, #54a0ff 100%);
}

.overview-icon.power-consumption {
  background: linear-gradient(135deg, #ffa726 0%, #ff9800 100%);
}

.overview-icon.efficiency {
  background: linear-gradient(135deg, #00d2d3 0%, #54a0ff 100%);
}

.overview-icon.devices {
  background: linear-gradient(135deg, #5f27cd 0%, #a55eea 100%);
}

.overview-info {
  flex: 1;
}

.overview-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.overview-label {
  font-size: 14px;
  color: #666;
}

/* 图表容器 */
.chart {
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .report-overview {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .report-overview {
    grid-template-columns: 1fr;
  }
}
</style>
