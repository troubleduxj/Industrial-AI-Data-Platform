<template>
  <CommonPage show-footer>
    <!-- 页面标题和操作区 -->
    <template #action>
      <div class="flex items-center gap-3">
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
      <div class="query-form">
        <div class="form-row flex items-center gap-15">
          <QueryBarItem label="设备编号" :label-width="70">
            <NInput
              v-model:value="queryForm.device_code"
              style="width: 200px"
              placeholder="请输入设备编号"
              clearable
            />
          </QueryBarItem>
          <QueryBarItem label="设备名称" :label-width="70">
            <NInput
              v-model:value="queryForm.device_name"
              style="width: 180px"
              placeholder="请输入设备名称"
              clearable
            />
          </QueryBarItem>
          <QueryBarItem label="开始时间" :label-width="70">
            <NDatePicker
              v-model:value="queryForm.start_time"
              type="datetime"
              style="width: 200px"
              placeholder="请选择开始时间"
              clearable
            />
          </QueryBarItem>
          <QueryBarItem label="结束时间" :label-width="70">
            <NDatePicker
              v-model:value="queryForm.end_time"
              type="datetime"
              style="width: 200px"
              placeholder="请选择结束时间"
              clearable
            />
          </QueryBarItem>
          <NButton type="primary" @click="handleQuery">
            <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />查询
          </NButton>
          <NButton class="ml-10" @click="handleReset">
            <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />重置
          </NButton>
        </div>
      </div>
    </NCard>

    <!-- 设备历史参数 -->
    <NCard class="mb-15" rounded-10>
      <template #header>
        <span>{{ queryForm.device_name }}（{{ queryForm.device_code }}）</span>
      </template>

      <!-- 图表展示 -->
      <div v-if="viewMode === 'chart'" class="chart-container">
        <div ref="chartRef" style="width: 100%; height: 400px"></div>
      </div>

      <!-- 表格展示 -->
      <div v-else>
        <NDataTable :columns="historyColumns" :data="historyData" :loading="loading" striped />

        <!-- 独立分页组件 -->
        <div v-if="historyData.length > 0" class="mt-6 flex justify-center">
          <NPagination
            v-model:page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :item-count="pagination.itemCount"
            :page-sizes="pagination.pageSizes"
            :show-size-picker="pagination.showSizePicker"
            :show-quick-jumper="pagination.showQuickJumper"
            :prefix="pagination.prefix"
            :suffix="pagination.suffix"
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </div>
      </div>
    </NCard>
  </CommonPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NCard, NInput, NDatePicker, NDataTable, NPagination, useMessage, NSelect } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import ViewToggle from '@/components/common/ViewToggle.vue'
import { formatDate, formatDateTime } from '@/utils'
import * as echarts from 'echarts'
import { compatibilityApi as deviceDataApi } from '@/api/device-v2'
import { systemV2Api } from '@/api/system-v2'
import { deviceFieldApi } from '@/api/device-field'
import { alarmRulesApi } from '@/api/alarm-rules'
import type { DeviceField } from '@/api/device-field'
import { useDeviceFieldStore } from '@/store/modules/device-field'

// 页面名称
defineOptions({ name: '历史数据查询' })

// 消息提示
const message = useMessage()

// 设备字段 Store
const deviceFieldStore = useDeviceFieldStore()

// 视图模式
const viewMode = ref('chart')
const chartRef = ref(null)
let chartInstance = null

// 报警规则缓存
const alarmRules = ref([])

// 视图切换选项
const viewOptions = [
  {
    value: 'chart',
    label: '图表视图',
    icon: 'material-symbols:bar-chart',
  },
  {
    value: 'table',
    label: '表格视图',
    icon: 'material-symbols:table-rows',
  },
]

// 路由
const route = useRoute()

// 查询表单
const queryForm = reactive({
  device_code: route.query.device_code || '14323A0041',
  device_name: route.query.device_name || '',
  device_type_code: route.query.device_type_code || '', // 设备类型代码
  start_time: route.query.start_time
    ? new Date(route.query.start_time).getTime()
    : new Date(Date.now() - 24 * 60 * 60 * 1000).getTime(), // 默认查询最近24小时
  end_time: route.query.end_time ? new Date(route.query.end_time).getTime() : new Date().getTime(),
})

// 选中的设备ID
const selectedDeviceId = ref('14324G0216')

// 加载状态
const loading = ref(false)

// 设备类型字段配置
const deviceFields = ref<DeviceField[]>([])

// 默认查询间隔（秒），默认为1小时
const defaultInterval = ref(3600)

// 获取系统默认配置
async function fetchDefaultConfig() {
  try {
    const res = await systemV2Api.getSystemConfigByKey('HISTORY_DATA_DEFAULT_INTERVAL', { _t: Date.now() })
    // 增加更多调试信息
    console.log('Fetching system config response:', res)
    
    // 检查响应格式
    let paramValue = null
    if (res && res.data) {
       // 直接返回了对象 {param_key: "...", param_value: "..."}
       if (res.data.param_value !== undefined) {
         paramValue = res.data.param_value
       } 
       // 或者包裹在 data 中 {data: {param_key: "...", param_value: "..."}}
       else if (res.data.data && res.data.data.param_value !== undefined) {
         paramValue = res.data.data.param_value
       }
    }

    if (paramValue !== null) {
       const interval = parseInt(paramValue)
       if (!isNaN(interval) && interval > 0) {
         defaultInterval.value = interval
         console.log('✅ 获取到默认查询间隔:', interval, '秒')
       }
    } else {
       console.warn('⚠️ 未找到 param_value，响应数据:', res)
    }
  } catch (e) {
    console.warn('获取默认查询间隔失败，使用默认值:', e)
  }
}

// 动态生成表格列
const historyColumns = computed(() => {
  const columns = [
    {
      title: '时间',
      key: 'ts',
      width: 180,
      fixed: 'left' as const,
      render: (row: any) => {
        return formatDateTime(row.ts, 'YYYY-MM-DD HH:mm:ss')
      },
    },
  ]

  // 根据设备字段配置动态添加列
  if (deviceFields.value && deviceFields.value.length > 0) {
    deviceFields.value.forEach((field) => {
      columns.push({
        title: field.field_name,
        key: field.field_code,
        width: 120,
        render: (row: any) => {
          const val = row[field.field_code]
          if (val === null || val === undefined) return '-'
          // 如果是数字，保留3位小数
          if (typeof val === 'number') {
            return val.toFixed(3) + (field.unit ? field.unit : '')
          }
          return val + (field.unit ? field.unit : '')
        },
      })
    })
  } else {
    // 如果没有字段配置，使用默认列（兼容旧数据）
    columns.push(
      {
        title: '预设电流',
        key: 'preset_current',
        width: 100,
        render: (row: any) => {
          return row.preset_current ? `${Number(row.preset_current).toFixed(3)}A` : '-'
        },
      },
      {
        title: '预设电压',
        key: 'preset_voltage',
        width: 100,
        render: (row: any) => {
          return row.preset_voltage ? `${Number(row.preset_voltage).toFixed(3)}V` : '-'
        },
      },
      {
        title: '焊接电流',
        key: 'weld_current',
        width: 100,
        render: (row: any) => {
          return row.weld_current ? `${Number(row.weld_current).toFixed(3)}A` : '-'
        },
      },
      {
        title: '焊接电压',
        key: 'weld_voltage',
        width: 100,
        render: (row: any) => {
          return row.weld_voltage ? `${Number(row.weld_voltage).toFixed(3)}V` : '-'
        },
      }
    )
  }

  return columns
})

// 模拟历史数据
const historyData = ref([])

// 分页状态
const pagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true,
  itemCount: 0,
  prefix: ({ itemCount }) => `共 ${itemCount} 条`,
  suffix: ({ startIndex, endIndex }) => `显示 ${startIndex}-${endIndex} 条`,
})

// 分页事件处理函数
function handlePageChange(page) {
  isViewModeChanging.value = true
  pagination.page = page
  queryHistoryData().finally(() => {
    isViewModeChanging.value = false
  })
}

function handlePageSizeChange(pageSize) {
  isViewModeChanging.value = true
  pagination.pageSize = pageSize
  pagination.page = 1
  queryHistoryData().finally(() => {
    isViewModeChanging.value = false
  })
}

/**
 * 加载报警规则
 */
async function loadAlarmRules() {
  try {
    const params = {}
    if (queryForm.device_type_code) params.device_type_code = queryForm.device_type_code
    if (queryForm.device_code) params.device_code = queryForm.device_code
    params.is_enabled = true
    
    // console.log('Fetching alarm rules with params:', params)
    
    const res = await alarmRulesApi.list(params)
    if (res.success) {
      alarmRules.value = res.data.items || res.data || []
      console.log(`✅ 加载到 ${alarmRules.value.length} 条报警规则`)
    }
  } catch (error) {
    console.warn('加载报警规则失败:', error)
    alarmRules.value = []
  }
}

/**
 * 获取字段的MarkLine配置
 */
function getMarkLine(fieldCode: string) {
  if (!alarmRules.value || alarmRules.value.length === 0) return null

  // 查找适用于该字段的规则
  // 优先使用特定设备的规则，然后是通用规则
  // 注意：alarmRules.value 应该已经包含了过滤后的规则，这里我们找最匹配的
  const rules = alarmRules.value.filter(r => r.field_code === fieldCode)
  if (rules.length === 0) return null

  // 排序：有device_code的优先
  rules.sort((a, b) => {
    if (a.device_code && !b.device_code) return -1
    if (!a.device_code && b.device_code) return 1
    return 0
  })

  const rule = rules[0] // 使用优先级最高的规则
  const config = rule.threshold_config || {}
  const data = []

  // 解析阈值配置
  // Warning
  if (config.warning) {
    if (config.warning.max !== undefined) {
      data.push({ 
        yAxis: config.warning.max, 
        name: 'Warning Max',
        lineStyle: { color: '#e6a23c', type: 'dashed' },
        label: { formatter: 'Warn: {c}' }
      })
    }
    if (config.warning.min !== undefined) {
      data.push({ 
        yAxis: config.warning.min, 
        name: 'Warning Min',
        lineStyle: { color: '#e6a23c', type: 'dashed' },
        label: { formatter: 'Warn: {c}' }
      })
    }
  }

  // Critical
  if (config.critical) {
    if (config.critical.max !== undefined) {
      data.push({ 
        yAxis: config.critical.max, 
        name: 'Critical Max',
        lineStyle: { color: '#f56c6c', type: 'solid' },
        label: { formatter: 'Crit: {c}' }
      })
    }
    if (config.critical.min !== undefined) {
      data.push({ 
        yAxis: config.critical.min, 
        name: 'Critical Min',
        lineStyle: { color: '#f56c6c', type: 'solid' },
        label: { formatter: 'Crit: {c}' }
      })
    }
  }

  if (data.length === 0) return null

  return {
    symbol: 'none',
    data: data
  }
}

/**
 * 渲染图表（整合初始化和更新逻辑）
 */
function renderChart(data: any[]) {
  if (!chartRef.value) return
  
  // 确保数据是数组
  const chartData = Array.isArray(data) ? data : []

  // 如果实例不存在，初始化
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  // 根据设备字段配置动态生成图表
  const legendData: string[] = []
  const series: any[] = []
  const yAxisConfig: any[] = []

  if (deviceFields.value && deviceFields.value.length > 0) {
    // 按字段类型分组（用于多Y轴）
    const fieldsByUnit = new Map<string, DeviceField[]>()
    deviceFields.value.forEach((field) => {
      const unit = field.unit || '无单位'
      if (!fieldsByUnit.has(unit)) {
        fieldsByUnit.set(unit, [])
      }
      fieldsByUnit.get(unit)!.push(field)
    })

    // 为每个单位创建一个Y轴
    let yAxisIndex = 0
    const colors = ['#ff4d4f', '#1890ff', '#52c41a', '#faad14', '#722ed1', '#eb2f96']
    let colorIndex = 0

    fieldsByUnit.forEach((fields, unit) => {
      // 创建Y轴
      yAxisConfig.push({
        type: 'value',
        name: unit !== '无单位' ? unit : '',
        position: yAxisIndex % 2 === 0 ? 'left' : 'right',
        offset: Math.floor(yAxisIndex / 2) * 60,
        axisLabel: {
          formatter: unit !== '无单位' ? `{value}${unit}` : '{value}',
        },
        splitLine: {
          show: yAxisIndex === 0 // 只显示第一个轴的网格线，避免杂乱
        }
      })

      // 为该单位的每个字段创建一条线
      fields.forEach((field) => {
        legendData.push(field.field_name)
        series.push({
          name: field.field_name,
          type: 'line',
          yAxisIndex: yAxisIndex,
          data: chartData.map((item: any) => {
            const val = item[field.field_code]
            return [item.ts, typeof val === 'number' ? Number(val.toFixed(3)) : val]
          }),
          smooth: true,
          showSymbol: false, // 数据量大时不显示点
          lineStyle: {
            color: colors[colorIndex % colors.length],
            width: 2
          },
          markLine: getMarkLine(field.field_code) // 添加阈值线
        })
        colorIndex++
      })

      yAxisIndex++
    })
  } else {
    // 默认配置（兼容旧数据）
    legendData.push('预设电流', '预设电压', '焊接电流', '焊接电压')
    yAxisConfig.push(
      {
        type: 'value',
        name: '电流(A)',
        position: 'left',
        axisLabel: {
          formatter: '{value}A',
        },
      },
      {
        type: 'value',
        name: '电压(V)',
        position: 'right',
        axisLabel: {
          formatter: '{value}V',
        },
      }
    )
    series.push(
      {
        name: '预设电流',
        type: 'line',
        yAxisIndex: 0,
        data: chartData.map((item: any) => [item.ts, typeof item.preset_current === 'number' ? Number(item.preset_current.toFixed(3)) : item.preset_current]),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          color: '#ff4d4f',
        },
      },
      {
        name: '焊接电流',
        type: 'line',
        yAxisIndex: 0,
        data: chartData.map((item: any) => [item.ts, typeof item.weld_current === 'number' ? Number(item.weld_current.toFixed(3)) : item.weld_current]),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          color: '#ff7a45',
        },
      },
      {
        name: '预设电压',
        type: 'line',
        yAxisIndex: 1,
        data: chartData.map((item: any) => [item.ts, typeof item.preset_voltage === 'number' ? Number(item.preset_voltage.toFixed(3)) : item.preset_voltage]),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          color: '#1890ff',
        },
      },
      {
        name: '焊接电压',
        type: 'line',
        yAxisIndex: 1,
        data: chartData.map((item: any) => [item.ts, typeof item.weld_voltage === 'number' ? Number(item.weld_voltage.toFixed(3)) : item.weld_voltage]),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          color: '#40a9ff',
        },
      }
    )
  }

  const option = {
    title: {
      text: '设备历史参数',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: legendData,
      top: 30,
      type: 'scroll',
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
    },
    yAxis: yAxisConfig,
    series: series,
  }

  // 使用 notMerge: true 确保完全重绘，避免旧配置残留
  chartInstance.setOption(option, true)
}

/**
 * 处理查询
 */
/**
 * 加载设备字段配置
 */
async function loadDeviceFields() {
  if (!queryForm.device_type_code) {
    console.warn('⚠️ 未指定设备类型代码，无法加载字段配置')
    return
  }

  try {
    console.log(`📋 加载设备类型字段配置: ${queryForm.device_type_code}`)
    const fields = await deviceFieldStore.getMonitoringFields(queryForm.device_type_code)
    
    // 只显示监测关键字段
    deviceFields.value = fields.filter((f) => f.is_monitoring_key && f.is_active)
    
    console.log(`✅ 加载到 ${deviceFields.value.length} 个监测字段`)
  } catch (error) {
    console.error('❌ 加载设备字段配置失败:', error)
    // 失败时使用空数组，会回退到默认列
    deviceFields.value = []
  }
}

// 查询历史数据
async function queryHistoryData() {
  loading.value = true
  try {
    // 先加载字段配置和报警规则
    await Promise.all([
      loadDeviceFields(),
      loadAlarmRules()
    ])

    // 根据视图模式决定查询参数
    const queryParams: any = {
      device_code: queryForm.device_code,
      start_time: queryForm.start_time,
      end_time: queryForm.end_time,
    }

    if (viewMode.value === 'chart') {
      // 图表模式：使用大的page_size获取所有数据点
      queryParams.page = 1
      queryParams.page_size = 10000

      const response = await deviceDataApi.getDeviceHistoryData(queryParams)
      
      // 如果在请求过程中切换了视图，则不再处理
      if (viewMode.value !== 'chart') return

      console.log('📊 图表模式 - API响应:', response)
      console.log('📊 图表模式 - 响应数据类型:', typeof response)
      console.log('📊 图表模式 - 响应数据结构:', Object.keys(response))
      
      // 处理响应数据 - 兼容不同的响应格式
      let dataArray = []
      if (Array.isArray(response)) {
        dataArray = response
      } else if (response.items && Array.isArray(response.items)) {
         // 处理 items 格式
         dataArray = response.items
      } else if (response.data && Array.isArray(response.data)) {
        dataArray = response.data
      } else if (response.data && response.data.items && Array.isArray(response.data.items)) {
         // 处理 data.items 格式
         dataArray = response.data.items
      } else if (response.data && response.data.data && Array.isArray(response.data.data)) {
        dataArray = response.data.data
      }
      
      console.log('📊 图表模式 - 提取的数据数组:', dataArray)
      console.log('📊 图表模式 - 数据数量:', dataArray.length)
      
      historyData.value = dataArray
      // 图表模式下不重置itemCount，保持表格模式的分页状态

      nextTick(() => {
        // 渲染图表
        if (viewMode.value === 'chart') {
           renderChart(dataArray)
        }
      })
    } else {
      // 表格模式：使用正常分页
      queryParams.page = pagination.page
      queryParams.page_size = pagination.pageSize

      const response = await deviceDataApi.getDeviceHistoryData(queryParams)
      console.log('📋 表格模式 - API响应:', response)
      console.log('📋 表格模式 - 响应数据类型:', typeof response)
      console.log('📋 表格模式 - 响应数据结构:', Object.keys(response))
      
      // 处理响应数据 - 兼容不同的响应格式
      let dataArray = []
      let total = 0
      
      if (Array.isArray(response)) {
        dataArray = response
        // 数组直接返回，无法获取 total，只能认为是全部数据
        total = response.length
      } else if (response.items && Array.isArray(response.items)) {
         dataArray = response.items
         // 这里移除了 total 的赋值，统一在后面处理
      } else if (response.data && Array.isArray(response.data)) {
        dataArray = response.data
        // 这里移除了 total 的赋值，统一在后面处理
      } else if (response.data && response.data.items && Array.isArray(response.data.items)) {
         dataArray = response.data.items
         // 这里移除了 total 的赋值，统一在后面处理
      } else if (response.data && response.data.data && Array.isArray(response.data.data)) {
        dataArray = response.data.data
        // 这里移除了 total 的赋值，统一在后面处理
      }
      
      // 提取 total
      if (response.total !== undefined) {
        total = response.total
      } else if (response.data && response.data.total !== undefined) {
        total = response.data.total
      } else if (response._metadata && response._metadata.total !== undefined) {
        total = response._metadata.total
      } else if (response.data && typeof response.data === 'object' && response.data.total !== undefined) {
        // 尝试从 data 对象中获取 total
        total = response.data.total
      } else if (response.meta && response.meta.total !== undefined) {
        // API v2 标准格式，total 在 meta 字段中
        total = response.meta.total
      } else {
        // 回退逻辑：如果没有找到total，使用当前页长度
        total = dataArray.length
      }

      console.log('📋 表格模式 - 提取的数据数组:', dataArray)
      console.log('📋 表格模式 - 数据数量:', dataArray.length)
      console.log('📋 表格模式 - 总数 (Total):', total)
      
      historyData.value = dataArray
      pagination.itemCount = total
    }
  } catch (error) {
    console.error('❌ 查询历史数据失败:', error)
    message.error(`查询失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

// 处理查询
function handleQuery() {
  pagination.page = 1
  queryHistoryData()
}

// 处理重置
function handleReset() {
  queryForm.device_code = '14324G0216'
  queryForm.device_name = ''
  queryForm.end_time = new Date().getTime()
  queryForm.start_time = queryForm.end_time - defaultInterval.value * 1000
  pagination.page = 1
  queryHistoryData()
}

// 标记是否正在切换视图模式，避免重复查询
const isViewModeChanging = ref(false)

// 监听分页变化
watch(
  () => pagination.page,
  () => {
    if (!isViewModeChanging.value) {
      queryHistoryData()
    }
  }
)

// 监听每页显示数量变化
watch(
  () => pagination.pageSize,
  () => {
    if (!isViewModeChanging.value) {
      pagination.page = 1
      queryHistoryData()
    }
  }
)

// 监听视图模式变化
watch(
  () => viewMode.value,
  (newVal) => {
    isViewModeChanging.value = true

    if (newVal === 'chart') {
      // 切换到图表模式时重新查询数据以获取所有数据点
      queryHistoryData().finally(() => {
        isViewModeChanging.value = false
      })
    } else {
      // 切换到表格模式时，如果itemCount为0，先重置分页再查询
      if (pagination.itemCount === 0) {
        pagination.page = 1
      }
      queryHistoryData().finally(() => {
        isViewModeChanging.value = false
      })
    }
  }
)

// 监听路由参数变化，自动更新查询条件
watch(
  () => route.query,
  (newQuery) => {
    // 检查是否有新的设备编码参数
    if (newQuery.device_code && newQuery.device_code !== queryForm.device_code) {
      console.log('路由参数变化，更新查询条件:', newQuery)
      queryForm.device_code = newQuery.device_code as string
      if (newQuery.device_name) queryForm.device_name = newQuery.device_name as string
      if (newQuery.device_type_code) queryForm.device_type_code = newQuery.device_type_code as string
      
      // 更新时间范围（如果有）
      if (newQuery.start_time) queryForm.start_time = new Date(newQuery.start_time as string).getTime()
      if (newQuery.end_time) queryForm.end_time = new Date(newQuery.end_time as string).getTime()
      
      // 重置分页并查询
      pagination.page = 1
      queryHistoryData()
    }
  },
  { deep: true }
)

// 初始化数据
onMounted(async () => {
  window.addEventListener('resize', handleResize)

  // 先获取系统配置
  await fetchDefaultConfig()
  
  // 首次加载时，确保使用路由参数（解决从其他页面跳转过来参数未生效的问题）
  const query = route.query
  let hasUpdate = false
  
  if (query.device_code && query.device_code !== queryForm.device_code) {
    queryForm.device_code = query.device_code as string
    hasUpdate = true
  }
  if (query.device_name && query.device_name !== queryForm.device_name) {
    queryForm.device_name = query.device_name as string
    hasUpdate = true
  }
  if (query.device_type_code && query.device_type_code !== queryForm.device_type_code) {
    queryForm.device_type_code = query.device_type_code as string
    hasUpdate = true
  }

  // 如果路由中没有指定时间，则使用获取到的默认间隔更新时间
  if (!query.start_time) {
    if (!query.end_time) {
      queryForm.end_time = new Date().getTime()
    }
    queryForm.start_time = queryForm.end_time - defaultInterval.value * 1000
    hasUpdate = true
  }
  
  if (hasUpdate) {
    console.log('初始化时同步路由参数/默认配置:', query)
  }
  
  queryHistoryData()
})

// 窗口大小改变时重绘图表
const handleResize = () => {
  if (chartInstance && !chartInstance.isDisposed()) {
    chartInstance.resize()
  }
}

// 销毁图表实例
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    if (!chartInstance.isDisposed()) {
      chartInstance.dispose()
    }
    chartInstance = null
  }
})

// 更新图表数据
// function updateChart(data: any[]) {
//   if (!chartInstance || chartInstance.isDisposed() || !data || !Array.isArray(data)) return
//
//   const series: any[] = []
//   const colors = ['#ff4d4f', '#1890ff', '#52c41a', '#faad14', '#722ed1', '#eb2f96']
//   let colorIndex = 0
//
//   if (deviceFields.value && deviceFields.value.length > 0) {
//     // 按字段类型分组（用于多Y轴）
//     const fieldsByUnit = new Map<string, DeviceField[]>()
//     deviceFields.value.forEach((field) => {
//       const unit = field.unit || '无单位'
//       if (!fieldsByUnit.has(unit)) {
//         fieldsByUnit.set(unit, [])
//       }
//       fieldsByUnit.get(unit)!.push(field)
//     })
//
//     let yAxisIndex = 0
//     fieldsByUnit.forEach((fields) => {
//       fields.forEach((field) => {
//         series.push({
//           name: field.field_name,
//           type: 'line',
//           yAxisIndex: yAxisIndex,
//           data: data.map((item) => [item.ts, item[field.field_code]]),
//           smooth: true,
//           lineStyle: {
//             color: colors[colorIndex % colors.length],
//           },
//         })
//         colorIndex++
//       })
//       yAxisIndex++
//     })
//   } else {
//     // 默认配置（兼容旧数据）
//     series.push(
//       {
//         name: '预设电流',
//         type: 'line',
//         yAxisIndex: 0,
//         data: data.map((item) => [item.ts, item.preset_current]),
//         smooth: true,
//         lineStyle: {
//           color: '#ff4d4f',
//         },
//       },
//       {
//         name: '焊接电流',
//         type: 'line',
//         yAxisIndex: 0,
//         data: data.map((item) => [item.ts, item.weld_current]),
//         smooth: true,
//         lineStyle: {
//           color: '#ff7a45',
//         },
//       },
//       {
//         name: '预设电压',
//         type: 'line',
//         yAxisIndex: 1,
//         data: data.map((item) => [item.ts, item.preset_voltage]),
//         smooth: true,
//         lineStyle: {
//           color: '#1890ff',
//         },
//       },
//       {
//         name: '焊接电压',
//         type: 'line',
//         yAxisIndex: 1,
//         data: data.map((item) => [item.ts, item.weld_voltage]),
//         smooth: true,
//         lineStyle: {
//           color: '#40a9ff',
//         },
//       }
//     )
//   }
//
//   const option = {
//     series: series,
//   }
//   chartInstance.setOption(option)
// }

// 导出
// export default {
//   name: '历史数据查询',
// }
</script>

<style scoped>
.query-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.chart-container {
  width: 100%;
  height: 400px;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
