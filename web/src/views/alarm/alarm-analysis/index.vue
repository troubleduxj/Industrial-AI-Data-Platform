<template>
  <CommonPage show-footer>
    <!-- 时间范围选择 -->
    <NCard class="mb-15" rounded-10>
      <div class="flex flex-wrap items-center gap-15">
        <QueryBarItem label="时间范围" :label-width="70">
          <NDatePicker
            v-model:value="dateRange"
            type="datetimerange"
            clearable
            format="yyyy-MM-dd HH:mm:ss"
            value-format="timestamp"
            placeholder="请选择时间范围"
            style="width: 300px"
          />
        </QueryBarItem>
        <QueryBarItem label="设备类型" :label-width="70">
          <NSelect
            v-model:value="deviceType"
            :options="deviceTypeOptions"
            placeholder="请选择设备类型"
            clearable
            style="width: 150px"
          />
        </QueryBarItem>
        <div class="ml-20 flex items-center gap-10">
          <NButton type="primary" :loading="loading" @click="handleQuery">
            <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />查询
          </NButton>
          <NButton @click="handleReset">
            <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />重置
          </NButton>
        </div>
      </div>
    </NCard>

    <!-- 统计卡片 -->
    <NCard class="mb-15" rounded-10>
      <template #header>
        <span>报警统计概览</span>
      </template>
      <NSpin :show="loading">
        <div class="grid grid-cols-4 gap-4">
          <div class="stat-card">
            <div class="stat-icon today">
              <TheIcon icon="material-symbols:analytics" :size="32" />
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ statistics.todayAlarms }}</div>
              <div class="stat-label">今日报警</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" :class="statistics.growthRate >= 0 ? 'up' : 'down'">
              <TheIcon
                :icon="statistics.growthRate >= 0 ? 'material-symbols:trending-up' : 'material-symbols:trending-down'"
                :size="32"
              />
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ statistics.growthRate }}%</div>
              <div class="stat-label">环比{{ statistics.growthRate >= 0 ? '增长' : '下降' }}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon device">
              <TheIcon icon="material-symbols:device-hub" :size="32" />
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ statistics.abnormalDevices }}</div>
              <div class="stat-label">异常设备</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon time">
              <TheIcon icon="material-symbols:schedule" :size="32" />
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ statistics.avgResponseTime }}</div>
              <div class="stat-label">平均响应时间</div>
            </div>
          </div>
        </div>
      </NSpin>
    </NCard>

    <!-- 图表分析区域 -->
    <div class="grid grid-cols-2 gap-4 mb-15">
      <!-- 报警趋势图 -->
      <NCard rounded-10>
        <template #header>
          <span>报警趋势（近7天）</span>
        </template>
        <NSpin :show="loading">
          <div ref="trendChartRef" class="chart-container"></div>
        </NSpin>
      </NCard>

      <!-- 报警类型分布 -->
      <NCard rounded-10>
        <template #header>
          <span>报警类型分布</span>
        </template>
        <NSpin :show="loading">
          <div ref="typeChartRef" class="chart-container"></div>
        </NSpin>
      </NCard>
    </div>

    <!-- 设备报警排行 -->
    <NCard rounded-10>
      <template #header>
        <span>设备报警排行 TOP 10</span>
      </template>
      <NSpin :show="loading">
        <NDataTable
          :columns="deviceRankColumns"
          :data="deviceRankData"
          :bordered="false"
          :single-line="false"
          size="small"
        />
      </NSpin>
    </NCard>
  </CommonPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, h, computed } from 'vue'
import { NCard, NDatePicker, NSelect, NButton, NSpin, NDataTable, NProgress } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import * as echarts from 'echarts'
import { alarmApi } from '@/api/alarm-shared'
import { deviceTypeApi } from '@/api/device-v2'

// 查询参数
const dateRange = ref(null)
const deviceType = ref(null)
const loading = ref(false)

// 统计数据
const statistics = reactive({
  todayAlarms: 0,
  growthRate: 0,
  abnormalDevices: 0,
  avgResponseTime: 'N/A',
  totalAlarms: 0,
  trendData: [],
  byType: {},
  bySource: {},
})

// 图表引用
const trendChartRef = ref(null)
const typeChartRef = ref(null)
let trendChart = null
let typeChart = null

// 设备类型数据
const deviceTypes = ref([])

// 加载设备类型数据
const loadDeviceTypes = async () => {
  try {
    const response = await deviceTypeApi.list({ page_size: 100 })
    if (response.data) {
      deviceTypes.value = response.data
    }
  } catch (error) {
    console.error('Failed to load device types', error)
  }
}

// 设备类型选项
const deviceTypeOptions = computed(() => {
  const baseOptions = [{ label: '全部', value: null }]
  
  if (deviceTypes.value && deviceTypes.value.length > 0) {
    return [
      ...baseOptions,
      ...deviceTypes.value.map(type => ({
        label: type.type_name,
        value: type.type_code
      }))
    ]
  }
  
  // 降级选项
  return [
    { label: '全部', value: null },
    { label: '焊接设备', value: 'welding' },
    { label: '传感器', value: 'sensor' },
    { label: '控制器', value: 'controller' },
  ]
})

// 设备排行表格列

// 设备排行表格列
const deviceRankColumns = [
  {
    title: '排名',
    key: 'rank',
    width: 60,
    render: (_, index) => index + 1,
  },
  {
    title: '设备编号',
    key: 'deviceCode',
  },
  {
    title: '报警次数',
    key: 'alarmCount',
    width: 120,
  },
  {
    title: '占比',
    key: 'percentage',
    width: 200,
    render: (row) =>
      h(NProgress, {
        type: 'line',
        percentage: row.percentage,
        indicatorPlacement: 'inside',
        status: row.percentage > 20 ? 'error' : row.percentage > 10 ? 'warning' : 'success',
      }),
  },
]

// 设备排行数据
const deviceRankData = ref([])

// 加载统计数据
const loadStatistics = async () => {
  loading.value = true
  try {
    // 构建查询参数
    const params: { start_date?: string; end_date?: string; device_type?: string } = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = new Date(dateRange.value[0]).toISOString()
      params.end_date = new Date(dateRange.value[1]).toISOString()
    }

    if (deviceType.value) {
      params.device_type = deviceType.value
    }

    // 调用API获取统计数据
    const response = await alarmApi.getStats(params)

    if (response && response.data) {
      const data = response.data

      // 更新统计数据
      statistics.todayAlarms = data.today_alarms || data.active_alarms || 0
      statistics.growthRate = data.growth_rate || 0
      statistics.abnormalDevices = data.abnormal_devices || 0
      statistics.avgResponseTime = data.avg_response_time || 'N/A'
      statistics.totalAlarms = data.total_alarms || 0
      statistics.trendData = data.trend_data || []
      statistics.byType = data.by_type || {}
      statistics.bySource = data.by_source || {}

      // 更新图表
      await nextTick()
      updateTrendChart()
      updateTypeChart()
      updateDeviceRank()
    }
  } catch (error) {
    console.error('加载报警统计失败:', error)
  } finally {
    loading.value = false
  }
}

// 更新趋势图
const updateTrendChart = () => {
  if (!trendChartRef.value) return

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const dates = statistics.trendData.map((item) => item.date)
  const counts = statistics.trendData.map((item) => item.count)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: (value) => value.slice(5), // 只显示月-日
      },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
    },
    series: [
      {
        name: '报警次数',
        type: 'bar',
        data: counts,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#18a058' },
            { offset: 1, color: '#36ad6a' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#0c7a43' },
              { offset: 1, color: '#18a058' },
            ]),
          },
        },
      },
    ],
  }

  trendChart.setOption(option)
}

// 更新类型分布图
const updateTypeChart = () => {
  if (!typeChartRef.value) return

  if (!typeChart) {
    typeChart = echarts.init(typeChartRef.value)
  }

  const typeData = Object.entries(statistics.byType).map(([name, value]) => ({
    name: name || '未知',
    value: value,
  }))

  // 如果没有数据，显示空状态
  if (typeData.length === 0) {
    typeData.push({ name: '暂无数据', value: 1 })
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
    },
    series: [
      {
        name: '报警类型',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data: typeData,
      },
    ],
  }

  typeChart.setOption(option)
}

// 更新设备排行
const updateDeviceRank = () => {
  const sourceData = Object.entries(statistics.bySource)
    .map(([deviceCode, alarmCount]) => ({
      deviceCode,
      alarmCount: Number(alarmCount),
    }))
    .sort((a, b) => b.alarmCount - a.alarmCount)
    .slice(0, 10)

  const maxCount = sourceData.length > 0 ? sourceData[0].alarmCount : 1

  deviceRankData.value = sourceData.map((item) => ({
    ...item,
    percentage: Math.round((item.alarmCount / maxCount) * 100),
  }))
}

// 查询处理
const handleQuery = () => {
  loadStatistics()
}

// 重置处理
const handleReset = () => {
  dateRange.value = null
  deviceType.value = null
  loadStatistics()
}

// 窗口大小变化时重绘图表
const handleResize = () => {
  trendChart?.resize()
  typeChart?.resize()
}

// 生命周期
onMounted(() => {
  loadDeviceTypes()
  loadStatistics()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  typeChart?.dispose()
})
</script>

<style scoped>
/* 统计卡片样式 */
.stat-card {
  @apply p-20 bg-white rounded-8 border border-gray-200 hover:shadow-md transition-all duration-300;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  @apply w-48 h-48 rounded-8 flex items-center justify-center text-white;
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%);
}

.stat-icon.today {
  background: linear-gradient(135deg, #2080f0 0%, #409eff 100%);
}

.stat-icon.up {
  background: linear-gradient(135deg, #d03050 0%, #e88080 100%);
}

.stat-icon.down {
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%);
}

.stat-icon.device {
  background: linear-gradient(135deg, #f0a020 0%, #fcb040 100%);
}

.stat-icon.time {
  background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  @apply text-24 font-600 text-gray-800 mb-4;
}

.stat-label {
  @apply text-14 text-gray-600;
}

/* 图表容器样式 */
.chart-container {
  height: 300px;
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .grid-cols-4 {
    @apply grid-cols-2;
  }

  .grid-cols-2 {
    @apply grid-cols-1;
  }
}

@media (max-width: 640px) {
  .grid-cols-4 {
    @apply grid-cols-1;
  }

  .flex-wrap {
    @apply flex-col items-start;
  }

  .ml-20 {
    @apply ml-0 mt-15;
  }
}
</style>
